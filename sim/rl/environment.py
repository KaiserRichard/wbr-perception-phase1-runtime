"""Gymnasium adapter for the frozen shared plant; no controller is embedded.

The policy sees only encoded Observation. Diagnostics and truth are confined to
reward/recording; PPO receives no privileged critic observation or push phase.
"""

from dataclasses import replace
import json
from pathlib import Path

import gymnasium as gym
import numpy as np

from sim.augmented import AugmentedRuntime, load_experiment


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = ROOT / "sim/rl/protocol.json"


def load_protocol(path=PROTOCOL_PATH):
    return json.loads(Path(path).read_text())


def encode_observation(observation, protocol):
    """Normalize common measurements/causal history only; never read runtime."""
    scale = protocol["policy_input"]
    history = np.zeros((protocol["observations"]["history_steps"], 2))
    source = observation.command_history
    if source.ndim != 2 or source.shape[1] != 2 or len(source) > len(history):
        raise ValueError("Unexpected causal history shape")
    history[:len(source)] = source
    value = np.r_[observation.measurement / scale["sensor_divisors"],
                  observation.torque_estimate / scale["torque_estimate_divisors"],
                  (history / scale["history_divisors"]).ravel(),
                  observation.delay_s / scale["delay_divisor_s"]]
    if value.shape != (scale["dimension"],) or not np.all(np.isfinite(value)):
        raise ValueError("Nonfinite or incorrectly shaped policy observation")
    return value


def decode_native(encoded, protocol):
    """Undo fixed normalization into the delay-specific LQR state ordering."""
    encoded = np.asarray(encoded, dtype=float)
    scale = protocol["policy_input"]
    if encoded.shape != (scale["dimension"],):
        raise ValueError("Expected a single shared 15-dimensional observation")
    delay = encoded[-1] * scale["delay_divisor_s"]
    matches = [d for d in protocol["plant"]["fixed_delays_s"]
               if abs(delay-d) < 1e-9]
    if len(matches) != 1:
        raise ValueError("Observation has an unknown fixed delay")
    n = max(1, int(np.ceil(matches[0] / protocol["plant"]["control_period_s"] - 1e-12)))
    return np.r_[encoded[:6] * scale["sensor_divisors"],
                 encoded[6:8] * scale["torque_estimate_divisors"],
                 (encoded[8:14].reshape(3, 2)[:n] * scale["history_divisors"]).ravel()]


class NumericalFailure(RuntimeError):
    """An invalid run must abort rather than becoming an ordinary RL terminal."""


class WbrEnv(gym.Env):
    """One CPU environment with independent condition and runtime noise RNGs.

    `policy_seed` selects predeclared training streams. Fixed evaluation resets
    require options={delay_s, scenario, noise_seed}, never a training RNG draw.
    Renderless by design. A recorder consumes evaluator-only step diagnostics.
    """

    metadata = {"render_modes": []}

    def __init__(self, policy_seed=0, config=None, protocol=None, recorder=None):
        self.protocol = load_protocol() if protocol is None else protocol
        config = ROOT / self.protocol["plant_contract"]["config"] if config is None else config
        self.base, self.experiment, self.effects = load_experiment(config)
        self.policy_seed = int(policy_seed)
        self.recorder = recorder
        self.dt = self.base["simulation"]["dt_s"]
        self.limits = np.asarray(self.protocol["plant"]["torque_limits_Nm"])
        self.duration = self.protocol["scenarios"][0]["duration_s"]
        self.max_ticks = round(self.duration / self.dt)
        self._runtimes = {}
        self._episode_index = 0
        self.total_steps = 0
        self._conditions = np.random.default_rng(np.random.SeedSequence([2, self.policy_seed]))
        self.action_space = gym.spaces.Box(-1., 1., shape=(2,), dtype=np.float32)
        # Fixed arithmetic is kept in float64. SB3 converts its own neural input
        # to float32; the LQR adapter can recover the original native vector.
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, shape=(15,), dtype=np.float64)
        self._ended = True

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self.policy_seed = int(seed)
            self._episode_index = 0
            self._conditions = np.random.default_rng(np.random.SeedSequence([2, self.policy_seed]))
        if options is None or options == {}:
            delays = self.protocol["plant"]["fixed_delays_s"]
            self.delay_s = delays[int(self._conditions.integers(len(delays)))]
            self.scenario = self.protocol["scenarios"][int(self._conditions.integers(2))]["name"]
            if self._episode_index >= self.protocol["rng"]["training_noise_seed_stride"]:
                raise ValueError("Exhausted reserved training noise seed range")
            self.noise_seed = (self.protocol["rng"]["training_noise_seed_base"] +
                               self.protocol["rng"]["training_noise_seed_stride"] * self.policy_seed +
                               self._episode_index)
        else:
            if set(options) != {"delay_s", "scenario", "noise_seed"}:
                raise ValueError("Fixed reset needs delay_s, scenario and noise_seed")
            self.delay_s, self.scenario = options["delay_s"], options["scenario"]
            self.noise_seed = int(options["noise_seed"])
        if self.delay_s not in self.protocol["plant"]["fixed_delays_s"]:
            raise ValueError("Delay outside the frozen protocol")
        if self.scenario not in ("balance", "push"):
            raise ValueError("Unknown scenario")
        if self.delay_s not in self._runtimes:
            self._runtimes[self.delay_s] = AugmentedRuntime(
                self.base, replace(self.effects, delay_s=self.delay_s))
        self.runtime = self._runtimes[self.delay_s]
        obs = self.runtime.reset(seed=self.noise_seed)
        self._tick, self._ended = 0, False
        self.last_transition = None
        info = {"delay_s": self.delay_s, "scenario": self.scenario,
                "noise_seed": self.noise_seed, "episode_index": self._episode_index}
        self._episode_index += 1
        if self.recorder is not None:
            self.recorder.start_episode(info, self.runtime)
        return encode_observation(obs, self.protocol), info

    def step(self, action):
        if self._ended:
            raise RuntimeError("Call reset before stepping a finished episode")
        action = np.asarray(action, dtype=float)
        self.attempted_action = action.copy()
        if action.shape != (2,) or not np.all(np.isfinite(action)):
            raise NumericalFailure("Policy emitted nonfinite or invalid action")
        raw_Nm = action * self.limits
        bounded_Nm = np.clip(action, -1., 1.) * self.limits
        p = self.base["protocol"]
        push_start = round(p["push_start_s"] / self.dt)
        push_end = push_start + round(p["push_duration_s"] / self.dt)
        force = p["push_force_N"] if self.scenario == "push" and push_start <= self._tick < push_end else 0.
        truth_before, noise_before = self.runtime.truth(), self.runtime.sensor_noise()
        observation_before = self.runtime.observation()
        time_before = self.runtime.time
        result = self.runtime.step(bounded_Nm, push_N=force)
        self._tick += 1
        self.total_steps += 1
        state = self.runtime.truth()
        if (not np.all(np.isfinite(state)) or any(self.runtime.warning_counts) or
                abs(self.runtime.time - self._tick * self.dt) > 1e-9):
            raise NumericalFailure("Nonfinite state, MuJoCo warning/reset or invalid elapsed time")
        physical_failure = bool(np.rad2deg(max(abs(state[1:3]))) >= p["fall_angle_deg"] or
                                abs(state[0]) > p["max_displacement_m"])
        reward_cfg = self.protocol["reward"]
        reward = -self.dt * (np.dot(state**2, reward_cfg["Q_diagonal"]) +
                             np.dot(bounded_Nm**2, reward_cfg["R_diagonal"]))
        reward -= 100. if physical_failure else 0.
        if not np.isfinite(reward):
            raise NumericalFailure("Nonfinite reward")
        terminated = physical_failure
        truncated = bool(self._tick >= self.max_ticks and not terminated)
        self._ended = terminated or truncated
        # This object is evaluator-only and never part of observation/info.
        self.last_transition = {
            "time_s": time_before, "truth_before": truth_before, "truth_after": state,
            "observation_before": observation_before, "observation_after": result.observation,
            "noise_before": noise_before, "noise_after": self.runtime.sensor_noise(),
            "raw_command_Nm": raw_Nm, "bounded_command_Nm": bounded_Nm,
            "result": result, "push_N": force, "reward": float(reward),
            "terminated": terminated, "truncated": truncated,
        }
        if self.recorder is not None:
            self.recorder.record(self.last_transition, self.runtime)
        return encode_observation(result.observation, self.protocol), float(reward), terminated, truncated, {}

    def close(self):
        if self.recorder is not None:
            self.recorder.close()
