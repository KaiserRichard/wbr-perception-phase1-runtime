"""100 Hz bounded governor above the unchanged 500 Hz LQR/planar runtime."""
from collections import deque
import math
import time
import gymnasium as gym
import numpy as np
from sim.augmented import AugmentedRuntime, RuntimeConfig
from .control import Predictor
from .protocol import DT, POLICY_DT, TOL, errors, model_config, reference


class G1Env(gym.Env):
    metadata = {'render_modes': []}

    def __init__(self, seed=0, rank=0, baseline=False, record=False):
        self.base_seed, self.rank = seed, rank
        self.baseline, self.record = baseline, record
        self.action_space = gym.spaces.Box(-1., 1., (1,), np.float32)
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (25,), np.float32)
        self.streams = None
        self.cpu_started = time.process_time()
        self.runtime = None

    def cpu_seconds(self):
        return time.process_time()-self.cpu_started

    def sampler_state(self):
        return [r.bit_generator.state for r in self.streams]

    def restore_sampler(self, states):
        self._seed(self.base_seed)
        for rng, state in zip(self.streams, states):
            rng.bit_generator.state = state

    def _seed(self, seed):
        # Command, pitch, push, delay and episode IMU seed are independent streams.
        self.streams = [np.random.default_rng(s) for s in
                        np.random.SeedSequence([seed, self.rank]).spawn(5)]

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None or self.streams is None:
            self._seed(self.base_seed if seed is None else seed)
        r = self.streams
        case = dict(command=float(r[0].choice([0., -.1, .1, -.2, .2])),
                    pitch_deg=float(r[1].uniform(-10, 10)), push_N=float(r[2].uniform(-6, 6)),
                    delay_s=float(r[3].uniform(.002, .005)), variant=0,
                    noise_seed=int(r[4].integers(0, 2**32))) if options is None else dict(options)
        self.case = case
        scale = 2 if case['variant'] else 1
        lag = .008 if case['variant'] else .005
        rc = RuntimeConfig(delay_s=case['delay_s'], motor_time_constant_s=(lag, lag),
                           body_angle_std_deg=.1*scale, body_gyro_std_rad_s=.01*scale)
        # Reuse only identical episode mechanics; a new delay changes timestamps/history.
        key = (case['delay_s'], case['variant'])
        if getattr(self, '_runtime_key', None) != key:
            self.runtime = AugmentedRuntime(model_config(case['variant']), rc)
            self.predictor = Predictor(case['delay_s'])
            self._runtime_key = key
        state = np.zeros(6); state[2] = np.deg2rad(case['pitch_deg'])
        self.runtime.reset(state, seed=case['noise_seed'])
        self.delta = self.prev_a = 0.
        self.deltas = deque([0.]*5, maxlen=5)
        self.commands = deque([np.zeros(2) for _ in range(5)], maxlen=5)
        self.samples, self.actions, self.trace = [], [], []
        self.reward_sums, self.total_return = {}, 0.
        self.failed = self.numerical = self.collision = False
        self.clips = self.rejects = self.actuator_clips = 0
        self._sample(np.zeros(2), np.zeros(2), 0., 0.)
        return self.observation(), {'case': case}

    def observation(self):
        rt = self.runtime
        e = errors(rt.measurement(), rt.time, self.case['command'])/TOL
        return np.r_[e, reference(rt.time, self.case['command'])[1]/.2,
                     np.array(self.deltas)/.03, np.array(self.commands).ravel()/np.tile(rt.limits, 5),
                     rt.observation().torque_estimate/rt.limits, self.case['delay_s']/.01].astype(np.float32)

    def _sample(self, requested, applied, effort, saturation):
        rt = self.runtime
        e = errors(rt.truth(), rt.time, self.case['command'])
        self.samples.append((rt.time, e.copy(), np.asarray(requested).copy(),
                             np.asarray(applied).copy(), effort, saturation))

    def step(self, action):
        a = np.asarray(action, dtype=float)
        if a.shape != (1,):
            raise ValueError('G1 requires one scalar action in a (1,) array')
        if not np.isfinite(a).all():
            self.rejects += 1; a = 0.
        else:
            a = float(a[0])
        self.clips += int(abs(a) > 1)
        a = 0. if self.baseline else float(np.clip(a, -1, 1))
        proposed = .03*a
        accepted = float(np.clip(proposed, self.delta-.001, self.delta+.001))
        v = reference(self.runtime.time, self.case['command'])[1]
        # During the fixed ramp, retain enough slew authority to meet the final speed cap.
        remaining = max(0., 1.-self.runtime.time)
        upper = min(.2-v, .2-self.case['command']+.1*remaining)
        lower = max(-.2-v, -.2-self.case['command']-.1*remaining)
        accepted = float(np.clip(accepted, lower, upper))
        self.clips += int(abs(accepted-proposed) > 1e-12)
        self.delta = accepted
        self.deltas.appendleft(accepted)
        ticks = 0
        for _ in range(5):
            rt = self.runtime
            request = self.predictor.command(rt, reference(rt.time, self.case['command']), self.delta)
            push = self.case['push_N'] if 3.-1e-12 <= rt.time < 3.15-1e-12 else 0.
            result = rt.step(request, push)
            ticks += 1
            self.commands.appendleft(result.clipped.copy())
            effort = float(sum(np.sum(i.torque_squared_integral) for i in result.intervals))
            sat = float(np.sum(abs(result.clipped) >= rt.limits-1e-12)*DT)
            self.actuator_clips += int(np.any(abs(result.requested-result.clipped)>1e-12))
            self._sample(result.clipped, rt.torque(), effort, sat)
            if self.record:
                self.trace.extend((i.time_s, i.dt_s, i.source_submitted_s,
                                   i.delayed_command.tolist()) for i in result.intervals)
            truth = rt.truth()
            self.numerical = bool(not np.isfinite(truth).all() or any(rt.warning_counts))
            # Lowest body-box corner against the floor, evaluated geometrically.
            p = rt.plant.cfg['physics']
            center_z = p['wheel_radius']['value'] + p['leg_length']['value']*np.cos(truth[1]) + p['body_com']['value']*np.cos(truth[2])
            self.collision = bool(center_z-.06*abs(np.cos(truth[2]))-.06*abs(np.sin(truth[2])) <= 0)
            e = errors(truth, rt.time, self.case['command'])
            self.failed = bool(self.numerical or self.collision or np.any(abs(truth[1:3]) > np.deg2rad(30)) or abs(e[0]) > 1.5)
            if self.failed:
                break
        q = errors(self.runtime.truth(), self.runtime.time, self.case['command'])/TOL
        terms = dict(alive=1., x=-q[0]**2, v=-q[1]**2,
                     angles=-.5*float(q[2:4]@q[2:4]), rates=-.25*float(q[4:]@q[4:]),
                     torque=-.01*float(np.sum((self.runtime.torque()/self.runtime.limits)**2)),
                     action_slew=-.05*((a-self.prev_a)/.1)**2, action=-.1*a*a,
                     fall=-math.ceil(max(0., 10-self.runtime.time)/.01) if self.failed else 0.)
        self.prev_a = a
        reward = float(sum(terms.values()))
        if not np.isfinite(reward):
            raise FloatingPointError('Nonfinite G1 reward: invalid run')
        for k, value in terms.items():
            self.reward_sums[k] = self.reward_sums.get(k, 0.)+float(value)
        self.total_return += reward
        self.actions.append((a, accepted, v+accepted))
        done = self.runtime.time >= 10.-1e-10
        info = dict(plant_ticks=ticks, reward_terms=terms, numerical_failure=self.numerical)
        if self.failed or done:
            from .metrics import episode_metrics
            info['episode_metrics'] = episode_metrics(self)
            info['episode'] = dict(r=self.total_return, l=len(self.actions), t=self.runtime.time)
            info['reward_sums'] = self.reward_sums.copy()
            info['case'] = self.case
        return self.observation(), reward, self.failed, bool(done and not self.failed), info
