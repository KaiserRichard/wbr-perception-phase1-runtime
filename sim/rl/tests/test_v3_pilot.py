"""Residual pilot contracts: arithmetic, real plant parity, logs and screens."""

from copy import deepcopy
from dataclasses import replace
import json
import os
import tempfile
import threading
import time
from pathlib import Path
import random
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sim.rl import v2  # Apply inherited thread limits before numerical imports.
import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecNormalize

from sim.rl.environment import NumericalFailure, load_protocol
from sim.rl.v2 import V2Env, lqr_gains, single_thread
from sim.rl.v3_pilot import (PilotEnv, PreciseVecMonitor, Telemetry, beta_for_tolerances, bounded_reward,
                             development_panel, physical_upright, pilot_screens,
                             save_snapshot, settings, stop_boundary, summarize_panel,
                             zero_actor_mean, close_vector, verify_zero_initialization, evaluate_snapshot)


CASE = {"delay_s": .003, "scenario": "balance", "noise_seed": 2000}


def setUpModule():
    # A regression must fail before it can perform any optimization.
    global no_learning
    no_learning = patch.object(PPO, "learn", side_effect=AssertionError("No training authorized"))
    no_learning.start()


def tearDownModule():
    no_learning.stop()


class CheapWorker(gym.Env):
    """No plant: exercise subprocess death and long monitor accumulation."""
    observation_space = gym.spaces.Box(-1., 1., (1,), dtype=np.float32)
    action_space = gym.spaces.Box(-1., 1., (1,), dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        return np.zeros(1, np.float32), {}

    def step(self, action):
        if action[0] > .5:
            os._exit(17)  # Only the test-owned subprocess receives this action.
        return np.zeros(1, np.float32), .1234567, False, False, {}


class SyntheticRuntime:
    """Known post-tick truths; no integration, training or altered real plant."""

    def __init__(self, observation, states, initial_tick=0):
        self.observation = observation
        self.states = iter(states)
        self.state = np.zeros(6)
        self.tick = initial_tick
        self.time = initial_tick * .002
        self.warning_counts = [0]
        self.commands = []

    def step(self, command, push_N=0):
        self.commands.append(np.asarray(command).copy())
        self.state = np.asarray(next(self.states), float)
        self.tick += 1
        self.time = self.tick * .002
        return SimpleNamespace(observation=self.observation, clipped=np.asarray(command))

    def truth(self):
        return self.state.copy()


class RewardTests(unittest.TestCase):
    def synthetic_env(self, states, initial_tick=0):
        env = PilotEnv()
        self.addCleanup(env.close)
        env.reset(options=CASE)
        env._observation = replace(env._observation, measurement=np.zeros(6))
        env._tick = initial_tick
        env.runtime = SyntheticRuntime(env._observation, states, initial_tick)
        return env

    def test_exact_physical_boundaries_and_timeout_precedence(self):
        for axis in (1, 2):
            for sign in (-1., 1.):
                state = np.zeros(6)
                state[axis] = sign*np.deg2rad(45.)
                env = self.synthetic_env([state], initial_tick=4999)
                _, reward, terminated, truncated, info = env.step([0., 0.])
                self.assertTrue(terminated)
                self.assertFalse(truncated)
                self.assertEqual(info["plant_ticks"], 1)
                self.assertEqual(info["episode_terms"]["fall"], 1.)
                self.assertAlmostEqual(reward, bounded_reward(float(state**2 @ env.q))-1., places=14)
                with self.assertRaises(RuntimeError):
                    env.step([0., 0.])
        for sign in (-1., 1.):
            for value, physical in ((1.5, False), (np.nextafter(1.5, np.inf), True)):
                state = np.array([sign*value, 0, 0, 0, 0, 0])
                env = self.synthetic_env([state], initial_tick=4999)
                _, reward, terminated, truncated, info = env.step([0., 0.])
                self.assertEqual(terminated, physical)
                self.assertEqual(truncated, not physical)
                self.assertEqual(info["episode_terms"]["fall"], float(physical))
                self.assertAlmostEqual(reward, bounded_reward(40*value**2)-float(physical), places=14)

    def test_early_physical_violation_uses_only_completed_post_tick_costs(self):
        states = [np.array([0., 0, 0, .03, 0, 0]),
                  np.array([.02, 0, 0, 0, 0, 0]),
                  np.array([1.6, 0, 0, 0, 0, 0])]
        env = self.synthetic_env(states)
        _, reward, terminated, truncated, info = env.step([0., 0.])
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertEqual(info["plant_ticks"], 3)
        # .0072, .016, 102.4 are post-tick costs; no initial/unfinished ticks.
        mean_cost = (.0072+.016+102.4)/3
        self.assertAlmostEqual(reward, 1/(1+(1250/291)*mean_cost)-1, places=14)
        self.assertEqual(info["episode_terms"]["fall"], 1.)

    def test_step_charges_clipped_total_command_not_residual(self):
        env = self.synthetic_env([np.zeros(6)]*5)
        # Fixed synthetic causal measurement makes LQR request [100,-200].
        # The held residual is [.4,-.8], so total clipping still issues [2,-4].
        observation = replace(env._observation, measurement=np.array([1., 0, 0, 0, 0, 0]))
        env._observation = env.runtime.observation = observation
        gain = np.zeros_like(env.gains[env.delay_s])
        gain[:, 0] = [-100., 200.]
        env.gains = {env.delay_s: gain}
        _, reward, terminated, truncated, info = env.step([1., -1.])
        np.testing.assert_array_equal(env.runtime.commands, np.tile([2., -4.], (5, 1)))
        self.assertAlmostEqual(info["reward_terms"]["command"], 12.8, places=14)
        self.assertEqual(info["reward_terms"]["residual_penalty"], 0.)
        self.assertAlmostEqual(reward, 291/16291., places=14)
        self.assertFalse(terminated or truncated)

    def test_extreme_finite_post_tick_costs_still_have_positive_reward(self):
        state = np.array([0., 0, 0, np.sqrt(1e308/8), 0, 0])
        env = self.synthetic_env([state]*5)
        _, reward, terminated, truncated, _ = env.step([0., 0.])
        self.assertGreater(reward, 0.)
        self.assertLessEqual(reward, 1.)
        self.assertFalse(terminated or truncated)

    def test_hand_computed_state_and_total_command_costs(self):
        # Q=[40,200,200,8,8,8], R=[.8,.6]; no residual penalty.
        # State [.01,0,0,.02,0,0] costs .004+.0032=.0072.
        # TOTAL command [.5,-1] costs .2+.6=.8; beta=1250/291.
        q = np.asarray(load_protocol()["reward"]["Q_diagonal"])
        r = np.asarray(load_protocol()["reward"]["R_diagonal"])
        state = np.array([.01, 0, 0, .02, 0, 0])
        command = np.array([.5, -1.])
        cost = float(state**2 @ q + command**2 @ r)
        self.assertAlmostEqual(cost, .8072, places=15)
        self.assertAlmostEqual(bounded_reward(cost), 291/1300., places=14)
        self.assertEqual(bounded_reward(0.), 1.)
        # Isolated xdot tolerance .03: C=8*.03^2=.0072, reward=.97.
        self.assertAlmostEqual(bounded_reward(.0072), .97, places=15)
        # x=.02 with both TOTAL commands at [2,4]: C=.016+3.2+9.6.
        self.assertAlmostEqual(bounded_reward(12.816), 291/16311., places=14)

    def test_reward_of_mean_completed_costs_is_not_mean_of_rewards(self):
        env = PilotEnv()
        self.addCleanup(env.close)
        env._components = [np.array([.0072, 0, 0, 0, 0, 0, 0]),
                           np.array([0, 0, 0, 0, 0, 0, .8])]
        expected = 1/(1+(1250/291)*((.0072+.8)/2))
        self.assertAlmostEqual(env._reward([.0072, .8], False), expected, places=14)
        self.assertNotAlmostEqual(expected, (bounded_reward(.0072)+bounded_reward(.8))/2)
        self.assertAlmostEqual(env._reward([.0072, .8], True), expected-1, places=14)

    def test_bounded_reward_tolerances_and_domain(self):
        p = load_protocol()
        costs = np.asarray(p["reward"]["Q_diagonal"]) * np.asarray(
            p["acceptance"]["state_abs_tolerance"])**2
        penalty = np.array([1 - bounded_reward(c) for c in costs])
        self.assertAlmostEqual(beta_for_tolerances(), 4.29553264604811, places=12)
        self.assertAlmostEqual(min(penalty), .03, places=14)
        np.testing.assert_allclose(penalty, [0.06430868, .20741782, .20741782,
                                           .03, .07911392, .07911392], atol=1e-8)
        for cost in (0, 1, 12.8, 10000, 1e308, np.finfo(float).max):
            self.assertGreater(bounded_reward(cost), 0.)
            self.assertLessEqual(bounded_reward(cost), 1.)
            self.assertLessEqual(bounded_reward(cost, True), 0.)
            self.assertGreaterEqual(bounded_reward(cost, True), -1.)
        for invalid in (-1, np.nan, np.inf):
            with self.assertRaises(NumericalFailure):
                bounded_reward(invalid)

    def test_v2_and_pilot_have_identical_causal_plant_and_truth(self):
        for delay in (.002, .003, .004, .005):
            old, new = V2Env("residual", record=True), PilotEnv(record=True)
            self.addCleanup(old.close)
            self.addCleanup(new.close)
            case = {**CASE, "delay_s": delay}
            np.testing.assert_array_equal(old.reset(options=case)[0], new.reset(options=case)[0])
            for action in ([0, 0], [2, -2], [.1, -.2]):
                a, b = old.step(action), new.step(action)
                np.testing.assert_array_equal(a[0], b[0])
                np.testing.assert_array_equal(old.runtime.truth(), new.runtime.truth())
                self.assertEqual(a[2:4], b[2:4])
                costs = np.mean(new._components, axis=0)
                self.assertAlmostEqual(b[1], 1/(1 + beta_for_tolerances()*sum(costs)), places=14)
                self.assertAlmostEqual(sum(b[4]["allocated_losses"]), b[4]["reward_terms"]["precision_loss"], places=14)
            for key in ("truth", "command_Nm", "noise", "times_s", "requested_Nm",
                        "actual_dt_s", "applied_effort"):
                np.testing.assert_array_equal(old.capture.arrays()[key], new.capture.arrays()[key])

    def test_partial_hold_duration_and_timeout_are_truthful(self):
        env = PilotEnv()
        self.addCleanup(env.close)
        env.max_ticks = 3
        env.reset(options=CASE)
        _, reward, terminated, truncated, info = env.step([0, 0])
        self.assertFalse(terminated)
        self.assertTrue(truncated)
        self.assertEqual(info["plant_ticks"], 3)
        self.assertAlmostEqual(info["episode_terms"]["sim_seconds"], .006)
        terms = info["episode_terms"]
        self.assertAlmostEqual(reward, terms["alive"]-terms["precision_loss"]-terms["fall"])
        env.reset(options=CASE)
        self.assertEqual(env.episode_terms["sim_seconds"], 0.)
        self.assertNotIn("loss_x", env.episode_terms)

    def test_fall_is_termination_with_single_penalty(self):
        env = PilotEnv()
        self.addCleanup(env.close)
        env.reset(options=CASE)
        env.runtime.reset(state=[1.501, 0, 0, 0, 0, 0], seed=2000)
        _, reward, done, truncated, info = env.step([0, 0])
        self.assertTrue(done)
        self.assertFalse(truncated)
        self.assertEqual(info["episode_terms"]["fall"], 1.)
        self.assertLessEqual(reward, 0.)
        self.assertEqual(info["plant_ticks"], 1)


class PolicyTests(unittest.TestCase):
    def assert_rng_unchanged(self, operation):
        python_state = random.getstate()
        numpy_state = deepcopy(np.random.get_state())
        torch_state = torch.random.get_rng_state().clone()
        result = operation()
        self.assertEqual(python_state, random.getstate())
        actual_numpy = np.random.get_state()
        self.assertEqual(numpy_state[0], actual_numpy[0])
        np.testing.assert_array_equal(numpy_state[1], actual_numpy[1])
        self.assertEqual(numpy_state[2:], actual_numpy[2:])
        torch.testing.assert_close(torch_state, torch.random.get_rng_state(), rtol=0, atol=0)
        return result

    def test_actor_zero_mean_reload_preserves_noise_and_normalizer(self):
        single_thread()
        vec = VecNormalize(DummyVecEnv([lambda: PilotEnv()]), norm_reward=False)
        self.addCleanup(vec.close)
        vec.reset()
        model = PPO("MlpPolicy", vec, n_steps=2, batch_size=2, seed=42,
                    policy_kwargs={"log_std_init": -1.})
        before = model.policy.log_std.detach().clone()
        np.testing.assert_array_equal(before.numpy(), [-1., -1.])
        zero_actor_mean(model)
        np.testing.assert_array_equal(model.policy.log_std.detach().numpy(), before.numpy())
        probes = np.stack([physical_upright(d) for d in (.002, .003, .004, .005)])
        np.testing.assert_array_equal(model.predict(vec.normalize_obs(probes), deterministic=True)[0], np.zeros((4, 2)))
        normalized = vec.normalize_obs(probes)
        self.assertFalse(np.array_equal(normalized, probes))
        with tempfile.TemporaryDirectory() as folder:
            snapshot = self.assert_rng_unchanged(lambda: save_snapshot(Path(folder)/"zero", model, vec))
            parity = self.assert_rng_unchanged(lambda: verify_zero_initialization(model, vec, snapshot, lqr_gains()))
            # Check actual checkpoint/evaluator setup without a development run.
            with patch("sim.rl.v3_pilot.development_panel", return_value=[]):
                self.assertFalse(self.assert_rng_unchanged(lambda: evaluate_snapshot(snapshot, lqr_gains()))["complete"])
            self.assertEqual(parity["status"], "PASS")
            self.assertEqual(len(parity["cases"]), 4)
            self.assertEqual(sum(row["plant_ticks"] for row in parity["cases"]), 60)
            loaded, frozen = v2.load_frozen(snapshot, "residual")
            self.addCleanup(frozen.close)
            actual, baseline = PilotEnv(record=True), V2Env("residual", record=True)
            self.addCleanup(actual.close)
            self.addCleanup(baseline.close)
            for delay in (.002, .003, .004, .005):
                obs, _ = actual.reset(options={**CASE, "delay_s": delay})
                baseline.reset(options={**CASE, "delay_s": delay})
                for _ in range(3):
                    action = loaded.predict(frozen.normalize_obs(obs), deterministic=True)[0]
                    np.testing.assert_array_equal(action, [0., 0.])
                    obs, *_ = actual.step(action)
                    baseline.step([0., 0.])
                np.testing.assert_array_equal(actual.capture.arrays()["truth"], baseline.capture.arrays()["truth"])
                np.testing.assert_array_equal(actual.capture.arrays()["command_Nm"], baseline.capture.arrays()["command_Nm"])

    def test_monitor_raw_terms_timeout_bootstrap_and_callback_without_learning(self):
        single_thread()
        env = PilotEnv()
        env.max_ticks = 5
        vec = VecNormalize(PreciseVecMonitor(DummyVecEnv([lambda: env]),
                            info_keywords=("episode_terms",)), norm_reward=False)
        self.addCleanup(vec.close)
        model = PPO("MlpPolicy", vec, n_steps=2, batch_size=2, seed=42,
                    policy_kwargs={"log_std_init": -1.})
        zero_actor_mean(model)
        with tempfile.TemporaryDirectory() as folder:
            callback = Telemetry(folder)
            callback.init_callback(model)
            callback.on_rollout_start()
            obs = vec.reset()
            for step in range(2):
                obs, rewards, dones, infos = vec.step(np.zeros((1, 2)))
                self.assertTrue(dones[0])
                self.assertTrue(infos[0]["TimeLimit.truncated"])
                self.assertEqual(infos[0]["terminal_observation"].shape, (15,))
                self.assertAlmostEqual(rewards[0], infos[0]["episode"]["r"], places=6)
                model.num_timesteps = step + 1
                callback.locals = {"infos": infos, "actions": np.zeros((1, 2)),
                                   "obs_tensor": torch.as_tensor(obs, dtype=torch.float32)}
                callback.on_step()
            callback.after_update(.1)
            self.assertEqual(len(callback.episode_rows), 2)
            self.assertEqual(callback.episode_rows[0]["length"], 1)
            self.assertAlmostEqual(callback.episode_rows[0]["sim_seconds"], .01)
            row = callback.update_rows[0]
            self.assertEqual(row["policy_transitions"], 2)
            self.assertEqual(row["log_std"], [-1., -1.])
            self.assertEqual(row["mean_abs_deterministic_output_fraction_cap"], [0., 0.])
            self.assertTrue((Path(folder)/"episodes.jsonl").is_file())

    def test_monitor_long_sum_and_clipped_deterministic_telemetry(self):
        monitor = PreciseVecMonitor(DummyVecEnv([CheapWorker]))
        self.addCleanup(monitor.close)
        monitor.reset()
        for _ in range(4096):
            monitor.step(np.zeros((1, 1)))
        self.assertEqual(monitor.episode_returns[0], float(np.float32(.1234567))*4096)
        vec = VecNormalize(DummyVecEnv([PilotEnv]), norm_reward=False)
        self.addCleanup(vec.close)
        model = PPO("MlpPolicy", vec, n_steps=2, batch_size=2, seed=42)
        zero_actor_mean(model)
        with torch.no_grad():
            model.policy.action_net.bias.copy_(torch.tensor([2., -2.]))
        with tempfile.TemporaryDirectory() as folder:
            callback = Telemetry(folder)
            callback.init_callback(model)
            callback.locals = {"infos": [{"plant_ticks": 5}],
                               "actions": np.array([[3., -2.]]),
                               "obs_tensor": torch.zeros((1, 15))}
            callback.on_step()
            callback.after_update(.1)
            row = callback.update_rows[0]
            self.assertEqual(row["mean_abs_deterministic_output_fraction_cap"], [1., 1.])
            self.assertEqual(row["sampled_mean_abs_residual_fraction_cap"], [1., 1.])
            self.assertEqual(row["sampling_noise_rms_fraction_cap"], [1., 0.])
            self.assertEqual(row["action_box_clipping_fraction"], [1., 1.])


class FailureTests(unittest.TestCase):
    def test_worker_error_aborts_before_monitor_without_learning(self):
        env = PilotEnv()
        monitor = PreciseVecMonitor(DummyVecEnv([lambda: v2.ReportWorkerFailure(env)]),
                                   info_keywords=("episode_terms",))
        self.addCleanup(monitor.close)
        monitor.reset()
        with patch.object(env, "step", side_effect=NumericalFailure("injected original worker fault")):
            with self.assertRaisesRegex(NumericalFailure, "injected original worker fault"):
                monitor.step(np.zeros((1, 2)))
        self.assertEqual(monitor.episode_count, 0)

    def test_dead_second_worker_cleanup_never_drains_or_leaves_workers(self):
        threads = {t.ident for t in threading.enumerate()}
        raw = SubprocVecEnv([CheapWorker, CheapWorker], start_method="spawn")
        vec = VecNormalize(PreciseVecMonitor(raw), norm_reward=False)
        self.addCleanup(close_vector, vec, failed=True)
        vec.reset()
        vec.step_async(np.array([[0.], [1.]]))
        with self.assertRaises((EOFError, BrokenPipeError)):
            vec.step_wait()
        self.assertTrue(raw.waiting)  # Worker 0's response was already consumed.
        started = time.monotonic()
        with patch.object(raw, "close", side_effect=AssertionError("must not drain")):
            close_vector(vec, failed=True)
        self.assertLess(time.monotonic() - started, 8.)
        self.assertFalse(any(p.is_alive() for p in raw.processes))
        self.assertTrue(all(r.closed for r in (*raw.remotes, *raw.work_remotes)))
        self.assertTrue(raw.closed)
        self.assertFalse(raw.waiting)
        self.assertEqual({t.ident for t in threading.enumerate()}, threads)


class ScreenTests(unittest.TestCase):
    def test_budget_complete_update_logic(self):
        self.assertFalse(stop_boundary(198000, 601))
        self.assertFalse(stop_boundary(200000, 599))
        self.assertTrue(stop_boundary(200000, 600))
        self.assertTrue(stop_boundary(80000, 1200))
        self.assertFalse(stop_boundary(80000, 1199))

    def test_development_seeds_disjoint_and_all_cases_required(self):
        panel = development_panel()
        self.assertEqual(len(panel), 16)
        self.assertEqual({c["noise_seed"] for c in panel}, {2000, 2001})
        self.assertEqual(load_protocol()["evaluation"]["noise_seeds"], list(range(1000, 1020)))
        self.assertFalse(set(c["noise_seed"] for c in panel) & set(load_protocol()["evaluation"]["noise_seeds"]))
        rows = [{**case, "success": True, "survived": True, "E": .8,
                 "leg_rate_violation": False} for case in panel]
        self.assertTrue(summarize_panel(rows)["complete"])
        self.assertFalse(summarize_panel(rows[:-1])["complete"])
        self.assertFalse(summarize_panel(rows[:-1] + [rows[0]])["complete"])

    def test_leg_rate_and_all16_strict_cannot_hide_behind_E(self):
        start = dict(complete=True, strict=16, survived=16, leg_rate_violations=0, E=.9)
        middle = {**start, "E": 1.}
        end = {**start, "E": .8}
        panels = {"snapshot-0": start, "snapshot-100k": middle, "final": end}
        episodes = [{"policy_transitions": 50000, "return": 10., "length": 1000},
                    {"policy_transitions": 200000, "return": 20., "length": 1000}]
        self.assertTrue(pilot_screens(panels, episodes, 200000)["pass"])
        for update in ({"leg_rate_violations": 1}, {"strict": 15}, {"survived": 15},
                       {"E": 1.1}, {"E": None}, {"complete": False}):
            changed = deepcopy(panels)
            changed["final"].update(update)
            self.assertFalse(pilot_screens(changed, episodes, 200000)["pass"])
        self.assertFalse(pilot_screens({"final": end}, episodes, 200000)["pass"])
        for update in ({"return": 10.}, {"length": 999}):
            changed = deepcopy(episodes)
            changed[-1].update(update)
            self.assertFalse(pilot_screens(panels, changed, 200000)["pass"])


if __name__ == "__main__":
    unittest.main()
