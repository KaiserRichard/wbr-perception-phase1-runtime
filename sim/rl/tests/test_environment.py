"""Behavioral checks for the shared information boundary and Gym semantics."""

from dataclasses import replace
import tempfile
from pathlib import Path
import unittest

import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv

from sim.augmented import AugmentedRuntime
from sim.rl.environment import WbrEnv, NumericalFailure, encode_observation, decode_native
from sim.rl.trace import TraceRecorder
from sim.rl.metrics import compute_metrics, trace_arrays


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.env = WbrEnv(policy_seed=3)
        self.addCleanup(self.env.close)

    def fixed(self, delay=.003, scenario='balance', seed=1000):
        return self.env.reset(options={'delay_s': delay, 'scenario': scenario, 'noise_seed': seed})[0]

    def test_exact_condition_rng_and_disjoint_noise_mapping(self):
        rng = np.random.default_rng(np.random.SeedSequence([2, 3]))
        expected = []
        for episode in range(12):
            delay, scenario = [.002, .003, .004, .005][rng.integers(4)], ['balance', 'push'][rng.integers(2)]
            _, info = self.env.reset(seed=3 if episode == 0 else None)
            self.assertEqual((info['delay_s'], info['scenario'], info['noise_seed']),
                             (delay, scenario, 1000000 + 150000 * 3 + episode))
            expected.append(self.env.runtime.sensor_noise())
        self.env.reset(seed=3)
        np.testing.assert_array_equal(self.env.runtime.sensor_noise(), expected[0])

    def test_noise_pairing_survives_other_actions_and_extra_reads(self):
        other = WbrEnv()
        self.addCleanup(other.close)
        self.fixed()
        other.reset(options={'delay_s': .005, 'scenario': 'push', 'noise_seed': 1000})
        for _ in range(12):
            for _ in range(7):
                self.env.runtime.observation()
            np.testing.assert_array_equal(self.env.runtime.sensor_noise(), other.runtime.sensor_noise())
            self.env.step([.1, -.2])
            other.step([-.1, .2])

    def test_only_observation_fields_enter_shared_vector_all_delays(self):
        for delay in [.002, .003, .004, .005]:
            self.fixed(delay=delay)
            for _ in range(10):
                encoded, *_ = self.env.step([.2, -.1])
                native = self.env.runtime.observation()
                np.testing.assert_allclose(decode_native(encoded, self.env.protocol), native.vector(), atol=1e-15)
                n = len(native.command_history)
                np.testing.assert_array_equal(encoded[8+2*n:14], 0)
                self.assertEqual(encoded.shape, (15,))
                # Encoding receives no runtime, truth, noise, future push or time.
                changed = replace(native, time_s=100000., command_times_s=np.full(n, -999.))
                np.testing.assert_array_equal(encode_observation(changed, self.env.protocol), encoded)

    def test_causal_estimate_does_not_read_physical_torque(self):
        self.fixed()
        self.env.step([.5, -.5])
        before = self.env.runtime.observation()
        self.env.runtime._tau[:] = [1., 2.]
        after = self.env.runtime.observation()
        np.testing.assert_array_equal(before.torque_estimate, after.torque_estimate)
        np.testing.assert_array_equal(before.vector(), after.vector())

    def test_action_clipping_poststep_reward_and_odd_delay(self):
        self.fixed()
        _, reward, terminated, truncated, info = self.env.step([2., -3.])
        t = self.env.last_transition
        np.testing.assert_array_equal(t['bounded_command_Nm'], [2., -4.])
        np.testing.assert_array_equal(self.env.runtime.observation().command_history[0], [2., -4.])
        state = self.env.runtime.truth()
        expected = -.002 * (np.dot(state**2, [40, 200, 200, 8, 8, 8]) + np.dot([4, 16], [.8, .6]))
        self.assertAlmostEqual(reward, expected, places=15)
        self.assertFalse(terminated or truncated)
        self.assertEqual(info, {})
        self.env.step([0., 0.])
        seg = self.env.last_transition['result'].intervals
        self.assertTrue(any(abs(s.time_s - .003) < 1e-12 for s in seg))
        for s in seg:
            np.testing.assert_array_equal(s.delayed_command, [0, 0] if s.time_s < .003-1e-12 else [2, -4])

    def test_physical_failure_terminal_penalty_and_no_step_after_end(self):
        self.fixed()
        for _ in range(500):
            _, reward, done, truncated, _ = self.env.step([0., 0.])
            if done:
                break
        self.assertTrue(done)
        self.assertFalse(truncated)
        state = self.env.runtime.truth()
        self.assertGreaterEqual(np.rad2deg(max(abs(state[1:3]))), 45.)
        self.assertAlmostEqual(reward, -.002 * np.dot(state**2, [40, 200, 200, 8, 8, 8]) - 100.)
        with self.assertRaises(RuntimeError):
            self.env.step([0., 0.])

    def test_numerical_invalid_action_aborts_never_nan_reward(self):
        self.fixed()
        for action in ([np.nan, 0.], [np.inf, 0.], [1.]):
            with self.assertRaises(NumericalFailure):
                self.env.step(action)
        self.assertEqual(self.env.total_steps, 0)

    def test_time_limit_terminal_observation_bootstrap_contract(self):
        # Short fixture exercises Gym/SB3 semantics, not experiment acceptance.
        self.env.max_ticks = 2
        vec = DummyVecEnv([lambda: self.env])
        obs = vec.reset()
        for _ in range(2):
            next_obs, reward, done, infos = vec.step(np.zeros((1, 2)))
        self.assertTrue(done[0])
        self.assertTrue(infos[0]['TimeLimit.truncated'])
        self.assertIn('terminal_observation', infos[0])
        self.assertFalse(np.array_equal(next_obs[0], infos[0]['terminal_observation']))
        self.assertEqual(infos[0]['terminal_observation'].shape, (15,))

    def test_lossless_chunks_raw_alignment_and_recomputed_reward(self):
        out = Path(tempfile.mkdtemp(prefix='wbr-rl-trace-test-'))
        recorder = TraceRecorder(out / 'trace', self.env.protocol, chunk_size=3)
        self.env.recorder = recorder
        self.fixed()
        for _ in range(11):
            self.env.step([1., -.1])
            recorder.attach_raw([2., -.1])
        recorder.close()
        rows, seg = trace_arrays(out / 'trace')
        self.assertEqual(len(rows['reward']), 11)
        self.assertTrue(np.all(rows['raw_action_available']))
        np.testing.assert_allclose(rows['policy_action_raw'][:, 0], 2.)
        expected = -.002 * (np.sum(rows['truth_after']**2 * [40, 200, 200, 8, 8, 8], axis=1) +
                            np.sum(rows['bounded_command_Nm']**2 * [.8, .6], axis=1))
        np.testing.assert_array_equal(rows['reward'], expected)
        self.assertAlmostEqual(seg[:, 1].sum(), .022)
        metrics = compute_metrics(out / 'trace', 'balance')
        self.assertEqual(metrics['command_saturation_duration_s'][0], metrics['duration_s'])
        self.assertEqual(metrics['penalized_recovery_s'], 10.)
        self.assertIsNone(metrics['recovery_time_after_event_s'])
