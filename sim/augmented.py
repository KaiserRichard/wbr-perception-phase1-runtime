"""Reusable causal actuator/sensor runtime; see augmented.md for the contract.

No controller or reward is embedded here. Only measurement(), observation(), and
the causal command/filter state belong in feedback; truth() is evaluation-only.
"""

from collections import deque
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path

import mujoco
import numpy as np

from sim.planar import Plant, load_config


TIME_EPS = 1e-12


def gain_hash(gain):
    """Portable, shape-checked elsewhere: row-major little-endian float64 bytes."""
    return hashlib.sha256(np.asarray(gain, dtype="<f8").tobytes()).hexdigest()


@dataclass(frozen=True)
class RuntimeConfig:
    delay_s: float = 0.002
    motor_time_constant_s: tuple = (0.005, 0.005)
    integration_max_step_s: float = 0.00025
    body_angle_std_deg: float = 0.1
    body_gyro_std_rad_s: float = 0.01

    def __post_init__(self):
        tau = tuple(float(v) for v in self.motor_time_constant_s)
        object.__setattr__(self, "motor_time_constant_s", tau)
        values = [self.delay_s, *tau, self.body_angle_std_deg, self.body_gyro_std_rad_s]
        if len(tau) != 2 or not all(math.isfinite(v) and v >= 0 for v in values):
            raise ValueError("Delay, two motor constants, and noise must be finite and nonnegative")
        if not math.isfinite(self.integration_max_step_s) or self.integration_max_step_s <= 0:
            raise ValueError("integration_max_step_s must be positive and finite")


def load_experiment(path):
    """Return (unaltered nominal config, augmented JSON, runtime config)."""
    path = Path(path)
    cfg = json.loads(path.read_text())
    if cfg["schema_version"] != 1:
        raise ValueError("Unsupported augmented config schema")
    base_path = path.parent / cfg["base_config"]
    if hashlib.sha256(base_path.read_bytes()).hexdigest() != cfg["base_sha256"]:
        raise ValueError("Frozen nominal config hash mismatch")
    base = load_config(base_path)
    if base["simulation"]["dt_s"] != 0.002:
        raise ValueError("This experiment freezes the control period at 2 ms")
    frozen = np.asarray(cfg["frozen_nominal"]["K"], float)
    if frozen.shape != (2, 6) or not np.all(np.isfinite(frozen)):
        raise ValueError("Expected a finite frozen 2x6 gain")
    if gain_hash(frozen) != cfg["frozen_nominal"]["sha256_float64_le"]:
        raise ValueError("Frozen gain hash mismatch")
    e = cfg["experiment"]
    if e["delays_s"] != [0.002, 0.003, 0.004, 0.005] or e["seeds"] != list(range(5)):
        raise ValueError("Declared experiment requires exact 2/3/4/5 ms delays and seeds 0..4")
    if e["scenarios"] != ["balance", "push", "open_loop"]:
        raise ValueError("Declared experiment requires the three nominal scenarios")
    return base, cfg, RuntimeConfig(**cfg["runtime"])


def lag_interval(torque, command, constants, dt):
    """Exact endpoint, mean, and integral(torque**2 dt) for constant command.

    tau(t+h) = u + (tau(t)-u)*exp(-h/T). Zero T is instantaneous.
    MuJoCo holds the exact mean over each short mechanical substep. Thus the
    filter/impulse are exact; coupled mechanical integration is an approximation.
    """
    torque, command, constants = (np.asarray(value, dtype=float)
                                  for value in (torque, command, constants))
    endpoint, mean, squared_integral = command.copy(), command.copy(), command**2 * dt
    active = constants > 0
    if np.any(active):
        T, u = constants[active], command[active]
        delta = torque[active] - u
        one_minus = -np.expm1(-dt / T)
        endpoint[active] = u + delta * (1 - one_minus)
        mean[active] = u + delta * (T / dt) * one_minus
        squared_integral[active] = (u*u*dt + 2*u*delta*T*one_minus +
                                    delta*delta*T/2 * (-np.expm1(-2*dt/T)))
    return endpoint, mean, np.maximum(squared_integral, 0.)


@dataclass(frozen=True)
class Command:
    submitted_s: float
    arrives_s: float
    value: np.ndarray


@dataclass(frozen=True)
class Observation:
    time_s: float
    measurement: np.ndarray
    torque_estimate: np.ndarray
    command_history: np.ndarray
    command_times_s: np.ndarray
    delay_s: float

    def vector(self):
        """[six measured coordinates, two reconstructed torques, newest commands]."""
        return np.r_[self.measurement, self.torque_estimate, self.command_history.ravel()]


@dataclass(frozen=True)
class Interval:
    time_s: float
    dt_s: float
    truth_start: np.ndarray
    torque_start: np.ndarray
    torque_end: np.ndarray
    applied_mean: np.ndarray
    torque_squared_integral: np.ndarray
    delayed_command: np.ndarray
    source_submitted_s: float | None
    push_N: float


@dataclass(frozen=True)
class StepResult:
    observation: Observation
    requested: np.ndarray
    clipped: np.ndarray
    intervals: tuple


class AugmentedRuntime:
    """One isolated MuJoCo model per runtime; no global callbacks or global RNG.

    reset(state=None, seed=0) starts zero torque and zero command prehistory.
    step(action_Nm, push_N=0) advances exactly ONE nominal control period.
    Repeated measurement/observation reads at a tick reuse the same noise.
    All exposed arrays are copies. Torque estimation uses commands/known T only.
    """

    def __init__(self, base_cfg, config=RuntimeConfig()):
        self.config = config
        self.plant = Plant(base_cfg)
        self.dt = float(base_cfg["simulation"]["dt_s"])
        self.history_steps = max(1, math.ceil(config.delay_s / self.dt - TIME_EPS))
        self.state_size = 8 + 2 * self.history_steps
        self._constants = np.asarray(config.motor_time_constant_s, float)
        # Preserve bitwise nominal mechanics when transport and lag are disabled.
        self._nominal_mechanics = config.delay_s == 0 and not np.any(self._constants)
        self.reset()

    @property
    def time(self):
        return float(self._data.time)

    @property
    def limits(self):
        return self.plant.limits.copy()

    @property
    def warning_counts(self):
        return [int(w.number) for w in self._data.warning]

    def reset(self, state=None, seed=0):
        if state is None:
            state = self.plant.cfg["protocol"]["initial_state"]
        state = np.asarray(state, float)
        if state.shape != (6,) or not np.all(np.isfinite(state)):
            raise ValueError("reset requires a finite six-state vector")
        self._data = self.plant.data(state)
        self._tick = 0
        self._tau = np.zeros(2)
        self._estimated_tau = np.zeros(2)
        self._delayed = np.zeros(2)
        self._source_time = None
        self._pending = deque()
        self._history = deque((Command(-i*self.dt, -i*self.dt+self.config.delay_s,
                                       np.zeros(2)) for i in range(1, self.history_steps+1)),
                              maxlen=self.history_steps)
        # Independent streams for angle and gyro; one draw per control tick.
        self._rngs = [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(2)]
        self._measurement = None
        return self.observation()

    def truth(self):
        """Evaluation/reward only; never part of controller-facing Observation."""
        return self.plant.state(self._data).copy()

    def torque(self):
        """Physical filter endpoint (evaluation only)."""
        return self._tau.copy()

    def command_history(self):
        """Newest first; commands already clipped BEFORE transport."""
        return tuple(Command(c.submitted_s, c.arrives_s, c.value.copy()) for c in self._history)

    def measurement(self):
        if self._measurement is None:
            self._measurement = self.truth()
            self._noise = np.array([
                self._rngs[0].normal() * np.deg2rad(self.config.body_angle_std_deg),
                self._rngs[1].normal() * self.config.body_gyro_std_rad_s,
            ])
            self._measurement[[2, 5]] += self._noise
        return self._measurement.copy()

    def sensor_noise(self):
        """Evaluation-only realized [body angle, body gyro] noise; NOT feedback."""
        self.measurement()
        return self._noise.copy()

    def observation(self):
        return Observation(self.time, self.measurement(), self._estimated_tau.copy(),
                           np.array([c.value for c in self._history]),
                           np.array([c.submitted_s for c in self._history]), self.config.delay_s)

    def _deliver(self):
        while self._pending and self._pending[0].arrives_s <= self.time + TIME_EPS:
            command = self._pending.popleft()
            self._delayed = command.value.copy()
            self._source_time = command.submitted_s
        instantaneous = self._constants == 0
        self._tau[instantaneous] = self._delayed[instantaneous]
        self._estimated_tau[instantaneous] = self._delayed[instantaneous]

    def step(self, action_Nm, push_N=0.):
        raw = np.asarray(action_Nm, float)
        if raw.shape != (2,) or not np.all(np.isfinite(raw)) or not np.isfinite(push_N):
            raise ValueError("Finite two-torque action and finite push required")
        clipped = np.clip(raw, -self.limits, self.limits)
        sent = self._tick * self.dt
        command = Command(sent, sent + self.config.delay_s, clipped.copy())
        self._pending.append(command)
        self._history.appendleft(command)
        end = (self._tick + 1) * self.dt
        intervals = []
        while self.time < end - TIME_EPS:
            self._deliver()
            if self._nominal_mechanics:
                h = self.dt
            else:
                h = min(self.config.integration_max_step_s, end-self.time)
                if self._pending:
                    h = min(h, self._pending[0].arrives_s-self.time)
            start, truth, tau0 = self.time, self.truth(), self._tau.copy()
            tau1, mean, squared = lag_interval(tau0, self._delayed, self._constants, h)
            # Independent causal filter reconstruction: no truth/physical tau read.
            estimate, _, _ = lag_interval(self._estimated_tau, self._delayed, self._constants, h)
            self.plant.model.opt.timestep = h
            self.plant.forward(self._data, mean, push_N)
            applied = self._data.actuator_force.copy()
            mujoco.mj_step(self.plant.model, self._data)
            if abs(self.time - start - h) > TIME_EPS or self.time <= start:
                raise FloatingPointError("MuJoCo time reset/non-advancement during actuator substep")
            self._tau, self._estimated_tau = tau1, estimate
            intervals.append(Interval(start, self.time-start, truth, tau0, tau1.copy(),
                                      applied, squared, self._delayed.copy(), self._source_time,
                                      float(push_N)))
        self._deliver()  # Arrival at end affects the NEXT interval, never the previous one.
        self._tick += 1
        self._measurement = None
        return StepResult(self.observation(), raw.copy(), clipped.copy(), tuple(intervals))

    def evaluation_state(self):
        """Linearization/evaluation only: truth plus causal filter/history."""
        return np.r_[self.truth(), self._tau, np.array([c.value for c in self._history]).ravel()]

    def transition_for_linearization(self, state, action):
        """Actual noiseless one-tick map, with consistent command timestamps.

        Restores a local linearization state at t=0; do not call during a rollout.
        The extra states are two filter torques and ceil(delay/dt) prior commands
        (at least one). They are causally reconstructible by either controller.
        """
        z = np.asarray(state, float)
        if z.shape != (self.state_size,):
            raise ValueError("Wrong augmented state size")
        self.reset(z[:6])
        self._tau = z[6:8].copy()
        self._estimated_tau = z[6:8].copy()
        self._history = deque((Command(-i*self.dt, -i*self.dt+self.config.delay_s, u.copy())
                               for i, u in enumerate(z[8:].reshape(-1, 2), 1)),
                              maxlen=self.history_steps)
        for command in reversed(self._history):
            if command.arrives_s <= TIME_EPS:
                self._delayed = command.value.copy()
                self._source_time = command.submitted_s
            else:
                self._pending.append(command)
        self.step(action)
        return self.evaluation_state()
