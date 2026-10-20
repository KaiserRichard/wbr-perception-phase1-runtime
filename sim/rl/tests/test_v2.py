"""Timing, information, metric and durability contracts of the lean v2 runner."""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from gymnasium.utils.env_checker import check_env
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from sim.augmented import AugmentedRuntime
from sim.rl.environment import NumericalFailure, load_protocol
from sim.rl.metrics import compute_metrics
from sim.rl.trace import TraceRecorder
from sim.rl.v2 import (V2Env, Progress, ReportWorkerFailure, compact_metrics, evaluation_panel,
                       evaluate_seed, experiment, load_config, load_frozen, lqr_gains,
                       should_extend, single_thread, train_seed, write_json)


def fixed(delay=.003, scenario="balance", noise=1000):
    return {"delay_s": delay, "scenario": scenario, "noise_seed": noise}


class V2EnvironmentTests(unittest.TestCase):
    def env(self, arm="direct", **kwargs):
        env = V2Env(arm, **kwargs)
        self.addCleanup(env.close)
        return env

    def test_gym_api(self):
        check_env(self.env(), skip_render_check=True)

    def test_five_tick_hold_clipping_reward_and_noise_reads(self):
        env = self.env(record=True)
        env.reset(options=fixed())
        twin = AugmentedRuntime(env.base, replace(env.effects, delay_s=.003))
        twin.reset(seed=1000)
        expected_costs = []
        for _ in range(5):
            for _ in range(7):
                twin.observation()
            result = twin.step([2., -4.])
            expected_costs.append(twin.truth()**2 @ env.q + result.clipped**2 @ env.r)
        _, reward, terminated, truncated, info = env.step([2., -3.])
        a = env.capture.arrays()
        self.assertEqual(info["plant_ticks"], 5)
        self.assertAlmostEqual(env.runtime.time, .01)
        self.assertFalse(terminated or truncated)
        np.testing.assert_array_equal(a["command_Nm"], np.tile([2., -4.], (5, 1)))
        np.testing.assert_array_equal(env.runtime.truth(), twin.truth())
        np.testing.assert_array_equal(env.runtime.sensor_noise(), twin.sensor_noise())
        self.assertEqual(len(a["noise"]), 6)
        self.assertAlmostEqual(reward, 1. - .1*np.mean(expected_costs), places=14)
        self.assertIsNone(self.env().capture)  # training retains no trajectory

    def test_early_fall_averages_only_completed_ticks_and_stops_immediately(self):
        env = self.env(record=True)
        env.reset(options=fixed())
        # A fall occurs within a hold, not exactly on a policy boundary.
        original = env.runtime.step
        ticks = 0

        def fall_on_third(action, push_N=0):
            nonlocal ticks
            ticks += 1
            if ticks == 3:
                env.runtime._data.qpos[1] = np.deg2rad(46.)
            return original(action, push_N)

        with patch.object(env.runtime, "step", side_effect=fall_on_third):
            _, reward, done, truncated, info = env.step([.1, -.2])
        self.assertTrue(done)
        self.assertFalse(truncated)
        self.assertEqual(info["plant_ticks"], 3)
        self.assertEqual(ticks, 3)
        a = env.capture.arrays()
        costs = a["truth"][1:]**2 @ env.q + a["command_Nm"]**2 @ env.r
        self.assertAlmostEqual(reward, -.1*np.mean(costs), places=12)
        with self.assertRaises(RuntimeError):
            env.step([0., 0.])

    def test_timeout_is_truncation_with_bootstrap_observation(self):
        env = self.env()
        env.max_ticks = 3
        vec = DummyVecEnv([lambda: env])
        self.addCleanup(vec.close)
        vec.reset()
        _, _, done, infos = vec.step(np.zeros((1, 2)))
        self.assertTrue(done[0])
        self.assertTrue(infos[0]["TimeLimit.truncated"])
        self.assertEqual(infos[0]["plant_ticks"], 3)
        self.assertEqual(infos[0]["terminal_observation"].shape, (15,))
        self.assertEqual(env.total_plant_ticks, 3)

    def test_displacement_and_numerics_are_not_timeout(self):
        env = self.env()
        env.reset(options=fixed())
        env.runtime.reset(state=[1.501, 0, 0, 0, 0, 0], seed=1000)
        _, _, done, truncated, info = env.step([0., 0.])
        self.assertTrue(done)
        self.assertFalse(truncated)
        self.assertEqual(info["plant_ticks"], 1)
        env.reset(options=fixed())
        with patch.object(type(env.runtime), "warning_counts", property(lambda _: [1])):
            with self.assertRaises(NumericalFailure):
                env.step([0., 0.])
        env.reset(options=fixed())
        for action in ([float("nan"), 0], [1]):
            with self.assertRaises(NumericalFailure):
                env.step(action)

    def test_zero_residual_matches_original_500hz_lqr_all_delays(self):
        for delay, gain in lqr_gains().items():
            env = self.env("residual", record=True)
            env.reset(options=fixed(delay))
            twin = AugmentedRuntime(env.base, replace(env.effects, delay_s=delay))
            obs = twin.reset(seed=1000)
            commands, states = [], []
            for _ in range(20):
                for _ in range(5):
                    command = np.clip(-gain @ obs.vector(), -env.limits, env.limits)
                    obs = twin.step(command).observation
                    commands.append(command)
                    states.append(twin.truth())
                env.step([0., 0.])
                np.testing.assert_array_equal(env.runtime.truth(), twin.truth())
            a = env.capture.arrays()
            np.testing.assert_array_equal(a["truth"][1:], states)
            np.testing.assert_array_equal(a["command_Nm"], commands)

    def test_residual_recomputes_causal_lqr_each_tick_and_caps_total(self):
        env = self.env("residual", record=True)
        env.reset(options=fixed())
        twin = AugmentedRuntime(env.base, replace(env.effects, delay_s=.003))
        obs = twin.reset(seed=1000)
        expected = []
        for _ in range(5):
            command = np.clip(-env.gains[.003] @ obs.vector() + [.4, -.8],
                              -env.limits, env.limits)
            expected.append(command)
            obs = twin.step(command).observation
        _, reward, *_ = env.step([20, -20])
        a = env.capture.arrays()
        np.testing.assert_array_equal(a["command_Nm"], expected)
        self.assertGreater(np.ptp(a["command_Nm"][:, 0]), 0.)
        self.assertTrue(np.all(abs(a["command_Nm"]) <= env.limits))
        costs = a["truth"][1:]**2 @ env.q + a["command_Nm"]**2 @ env.r
        self.assertAlmostEqual(reward, 1. - .1*np.mean(costs), places=12)
        # Changing the cached measurement changes feedback, not a truth shortcut.
        env.reset(options=fixed())
        env._observation = replace(env._observation, measurement=np.zeros(6))
        env.step([0, 0])
        np.testing.assert_array_equal(env.capture.arrays()["command_Nm"][0], [0, 0])

    def test_randomization_and_noise_domains_are_reproducible_and_independent(self):
        env, twin = self.env(policy_seed=2, rank=4), self.env(policy_seed=2, rank=4)
        conditions, signs, delays, seeds = [], set(), set(), set()
        for i in range(100):
            _, info = env.reset(seed=9 if i == 0 else None)
            _, other = twin.reset(seed=9 if i == 0 else None)
            self.assertEqual(info, other)
            state = np.asarray(info["initial_state"])
            self.assertTrue(np.all(abs(state[1:3]) <= np.deg2rad(10.)))
            np.testing.assert_array_equal(state[[0, 3, 4, 5]], 0.)
            self.assertGreaterEqual(info["push_start_tick"], 500)
            self.assertLessEqual(info["push_start_tick"], 3500)
            self.assertEqual(info["push_duration_ticks"], 75)
            self.assertLessEqual(abs(info["push_force_N"]), 10.)
            signs.add(np.sign(info["push_force_N"]))
            delays.add(info["delay_s"])
            seeds.add(info["noise_seed"])
            conditions.append(state[1:3])
            env.step([.1, .2])  # sensor draws must not perturb condition RNG
        self.assertEqual(delays, {.002, .003, .004, .005})
        self.assertEqual(signs, {-1, 1})
        self.assertEqual(len(seeds), 100)
        self.assertTrue(seeds.isdisjoint(range(1000, 1020)))
        self.assertTrue(np.all(np.std(conditions, axis=0) > .05))
        other = self.env(policy_seed=2, rank=5)
        _, info = other.reset(seed=9)
        self.assertNotIn(info["noise_seed"], seeds)

    def test_exact_fixed_evaluation_panel_and_pulse(self):
        panel, protocol = evaluation_panel(), load_protocol()
        self.assertEqual(len(panel), 160)
        self.assertEqual({r["noise_seed"] for r in panel}, set(range(1000, 1020)))
        env = self.env()
        for case in panel:
            _, info = env.reset(options=case)
            np.testing.assert_array_equal(env.runtime.truth(), protocol["scenarios"][0]["initial_state"])
            self.assertEqual(info["delay_s"], case["delay_s"])
            self.assertEqual(info["noise_seed"], case["noise_seed"])
            if case["scenario"] == "push":
                self.assertEqual((env.push_force, env.push_start, env.push_end), (6., 1500, 1575))
            else:
                self.assertEqual(env.push_force, 0.)

    def test_compact_metrics_equal_old_raw_metrics_full_push_and_failed_balance(self):
        # Full LQR push exercises recovery, final held window and full pulse.
        # Direct zero torque exercises the early failure path on the same reducer.
        for arm, scenario in (("residual", "push"), ("direct", "balance")):
            with self.subTest(arm=arm), tempfile.TemporaryDirectory() as directory:
                env = self.env(arm, record=True)
                env.reset(options=fixed(.003, scenario))
                trace = TraceRecorder(Path(directory) / "trace", env.protocol)
                trace.start_episode({}, env.runtime)
                original = env.runtime.step

                def record(action, push_N=0):
                    before, noise = env.runtime.truth(), env.runtime.sensor_noise()
                    observation, time_s = env.runtime.observation(), env.runtime.time
                    result = original(action, push_N)
                    trace.record({
                        "time_s": time_s, "truth_before": before, "truth_after": env.runtime.truth(),
                        "noise_before": noise, "noise_after": env.runtime.sensor_noise(),
                        "observation_before": observation, "observation_after": result.observation,
                        "raw_command_Nm": action, "bounded_command_Nm": result.clipped,
                        "result": result, "push_N": push_N, "reward": 0.,
                        "terminated": False, "truncated": False,
                    }, env.runtime)
                    return result

                with patch.object(env.runtime, "step", side_effect=record):
                    while True:
                        _, _, terminated, truncated, _ = env.step([0., 0.])
                        if terminated or truncated:
                            break
                trace.close()
                old = compute_metrics(Path(directory) / "trace", scenario)
                new = compact_metrics(env.capture.arrays(), scenario)
                self.assertEqual(new["checks"], old["checks"])
                self.assertEqual(new["success"], arm == "residual")
                self.assertEqual(new["survived"], arm == "residual")
                for k, value in old.items():
                    if k == "noise_stream_sha256_float64_le":
                        continue
                    if value is None or isinstance(value, (str, dict, bool)):
                        self.assertEqual(new[k], value, k)
                    elif isinstance(value, list) and (not value or isinstance(value[0], str)):
                        self.assertEqual(new[k], value, k)
                    else:
                        np.testing.assert_allclose(new[k], value, rtol=2e-12, atol=2e-12, err_msg=k)
                a = env.capture.arrays()
                for key, value in a.items():
                    self.assertIn(len(value), (len(a["truth"]), len(a["truth"])-1), key)
                if arm == "residual":
                    mutations = [
                        ("caps", "peak_applied", lambda x: x*0 + [3, 0]),
                        ("full_pulse", "push_impulse", lambda x: x*0),
                        ("numerics", None, None),
                        ("held_final_window", "truth", lambda x: np.vstack([x[:-1], [0, .1, 0, 0, 0, 0]])),
                    ]
                    for check, key, change in mutations:
                        altered = dict(a)
                        if key:
                            altered[key] = change(a[key])
                        result = compact_metrics(altered, scenario, "warning" if key is None else None)
                        self.assertFalse(result["checks"][check], check)
                        self.assertFalse(result["success"])
                    late = dict(a)
                    late["truth"] = a["truth"].copy()
                    late["truth"][np.flatnonzero(a["times_s"] >= 8.5)[0], 2] = .03
                    result = compact_metrics(late, scenario)
                    self.assertTrue(result["checks"]["held_final_window"])
                    self.assertFalse(result["checks"]["recovery_deadline"])
                    self.assertFalse(result["success"])


class V2RunnerTests(unittest.TestCase):
    def test_exact_budget_and_preserved_ppo_choices(self):
        c, p = load_config(), load_protocol()
        hyper = {**p["ppo_hyperparameters"], **c["ppo_overrides"]}
        self.assertEqual(c["training"]["n_envs"], 8)
        self.assertEqual(hyper["n_steps"], 250)
        self.assertEqual(hyper["batch_size"], 250)
        self.assertEqual(hyper["gamma"], .99)
        self.assertEqual(1500*hyper["n_steps"]*8, c["training"]["policy_transitions_per_seed"])
        self.assertEqual(c["training"]["policy_transitions_per_seed"]*c["policy_hold_ticks"], 15000000)
        self.assertFalse(c["vecnormalize"]["norm_reward"])
        self.assertEqual(hyper["learning_rate"], .0003)
        self.assertEqual(hyper["n_epochs"], 10)

    def test_frozen_norm_and_policy_reload_is_identical_and_never_updates(self):
        single_thread()
        with tempfile.TemporaryDirectory() as folder:
            c = load_config()
            vec = VecNormalize(DummyVecEnv([lambda: V2Env()]), **c["vecnormalize"])
            self.addCleanup(vec.close)
            obs = vec.reset()
            for _ in range(8):
                obs, *_ = vec.step(np.array([[.3, -.2]]))
            model = PPO("MlpPolicy", vec, seed=7, n_steps=8, batch_size=8, device="cpu")
            model.save(Path(folder) / "final.zip")
            vec.save(Path(folder) / "vecnormalize.pkl")
            loaded, norm = load_frozen(folder, "direct", c)
            self.addCleanup(norm.close)
            before = deepcopy(norm.obs_rms)
            probe = vec.get_original_obs()
            np.testing.assert_array_equal(vec.normalize_obs(probe), norm.normalize_obs(probe))
            np.testing.assert_array_equal(model.predict(obs, deterministic=True)[0],
                                          loaded.predict(norm.normalize_obs(probe), deterministic=True)[0])
            norm.reset()
            for _ in range(4):
                norm.step(np.zeros((1, 2)))
            np.testing.assert_array_equal(norm.obs_rms.mean, before.mean)
            np.testing.assert_array_equal(norm.obs_rms.var, before.var)
            self.assertEqual(norm.obs_rms.count, before.count)
            self.assertFalse(norm.training)
            self.assertFalse(norm.norm_reward)

    def test_worker_numerical_error_aborts_before_learning(self):
        env = V2Env()
        self.addCleanup(env.close)
        wrapper = ReportWorkerFailure(env)
        wrapper.reset()
        _, reward, done, _, info = wrapper.step([float("nan"), 0])
        self.assertTrue(done)
        self.assertIn("Nonfinite", info["worker_error"])
        callback = Progress(Path("/unused"), 2000)
        callback.locals = {"infos": [info]}
        with self.assertRaisesRegex(NumericalFailure, "Nonfinite"):
            callback._on_step()
        self.assertEqual(callback.plant_ticks, 0)

    def test_extension_uses_strict_balance_pass_only(self):
        row = {"scenario": "balance", "status": "FAIL", "success": False,
               "survived": True, "policy_seed": 0}
        self.assertFalse(should_extend([row]))
        self.assertFalse(should_extend([{**row, "scenario": "push", "status": "PASS", "success": True}]))
        self.assertTrue(should_extend([{**row, "status": "PASS", "success": True}]))
        self.assertFalse(should_extend([{**row, "policy_seed": 3, "status": "PASS", "success": True}]))

    def test_failed_existing_attempt_never_overwritten_and_all_missing_slots_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "seed-1"
            out.mkdir()
            write_json(out / "status.json", {"status": "FAILED", "reason": "retained"})
            before = (out / "status.json").read_bytes()
            with self.assertRaises(FileExistsError):
                train_seed("direct", 1, out, load_config())
            self.assertEqual((out / "status.json").read_bytes(), before)
            rows = evaluate_seed("direct", 1, out, load_config(), missing="retained failure")
            self.assertEqual(len(rows), 160)
            self.assertTrue(all(r["status"] == "MISSING_POLICY" and not r["success"] for r in rows))
            self.assertTrue(all(r["training_failure_count"] == 1 for r in rows))
            self.assertEqual(len(list((out / "evaluation").glob("*.npz"))), 0)

    def test_failed_reset_cannot_relabel_previous_episode_trajectory(self):
        with tempfile.TemporaryDirectory() as folder:
            env = V2Env(record=True)
            env.reset(options=fixed())
            env.step([0, 0])
            with patch("sim.rl.v2.load_frozen", return_value=(None, DummyVecEnv([lambda: V2Env()]))), \
                    patch("sim.rl.v2.V2Env", return_value=env), \
                    patch.object(env, "reset", side_effect=RuntimeError("reset failed")):
                rows = evaluate_seed("direct", 0, folder, load_config(), smoke=True)
            self.assertEqual(rows[0]["status"], "EVALUATION_FAILED")
            self.assertEqual(rows[0]["control_steps"], 0)
            self.assertFalse(list((Path(folder) / "evaluation").glob("*.npz")))

    def test_orchestration_is_sequential_and_extensions_independent(self):
        with tempfile.TemporaryDirectory() as folder:
            calls = []

            def train(arm, seed, out, *args):
                calls.append((arm, seed))
                Path(out).mkdir(parents=True)
                return {"status": "FAILED" if (arm, seed) == ("direct", 1) else "COMPLETE",
                        "failure_reasons": ["test failure"] if (arm, seed) == ("direct", 1) else []}

            def evaluate(arm, seed, *args):
                return [{"controller": arm, "policy_seed": seed, "scenario": "balance",
                         "status": "PASS" if arm == "residual" and seed == 2 else "FAIL",
                         "success": arm == "residual" and seed == 2, "survived": True,
                         "fall_count": 0, "training_failure_count": int((arm, seed) == ("direct", 1)),
                         "numerical_failure_count": 0, "other_failure_count": 0}]

            with patch("sim.rl.v2.train_seed", side_effect=train), \
                    patch("sim.rl.v2.evaluate_seed", side_effect=evaluate):
                result = experiment(Path(folder) / "run")
            self.assertEqual(result, 1)
            self.assertEqual(calls, [("direct", 0), ("residual", 0), ("direct", 1), ("residual", 1),
                                     ("direct", 2), ("residual", 2), ("residual", 3), ("residual", 4)])
            status = json.loads((Path(folder) / "run/status.json").read_text())
            self.assertEqual(status["extensions"], {"direct": False, "residual": True})


if __name__ == "__main__":
    unittest.main()
