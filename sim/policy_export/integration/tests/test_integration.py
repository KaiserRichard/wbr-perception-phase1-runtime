"""Bounded compiled-C controller arithmetic replay; no plant or training."""
import ctypes
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time
import unittest

import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from sim.policy_export.export import contract, export_c, load_completed


ROOT = Path(__file__).resolve().parents[4]
INTEGRATION = Path(__file__).resolve().parents[1]
A2_ATOL = 1e-6
B2_ATOL = B2_RTOL = 3e-5
torch.set_num_threads(1)


class TinyEnv(gym.Env):
    observation_space = gym.spaces.Box(-np.inf, np.inf, (15,), dtype=np.float64)
    action_space = gym.spaces.Box(-1., 1., (2,), dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        return np.zeros(15), {}


class Oracle:
    """Frozen SB3 normalization/mean; archived K; analytical command-only lag.

    float64_composition reproduces v2's external scaling/composition precision.
    Both variants own their history; neither reads C state to advance it.
    """
    def __init__(self, profile, model, norm, arm, float64_composition=False):
        self.delay = profile["delay_ms"]
        self.n = profile["history_steps"]
        self.k = np.array(profile["K"])
        self.model, self.norm, self.arm = model, norm, arm
        p, self.config = contract()
        s = p["policy_input"]
        self.divisors = np.r_[s["sensor_divisors"], s["torque_estimate_divisors"],
                              np.tile(s["history_divisors"], 3), s["delay_divisor_s"]]
        self.limits = np.array(p["plant"]["torque_limits_Nm"])
        self.wide = float64_composition
        self.reset()

    def reset(self):
        self.torque = np.zeros(2)
        self.history = np.zeros((3, 2))
        self.phase = self.calls = 0
        self.raw = self.bounded = self.held = np.zeros(2, np.float32)

    def baseline(self, measurement):
        return -self.k @ np.r_[measurement, self.torque, self.history[:self.n].ravel()]

    def tick(self, measurement):
        encoded = np.r_[measurement, self.torque, self.history.ravel(),
                        self.delay / 1000] / self.divisors
        baseline = self.baseline(measurement)
        if self.phase == 0:
            # Actual saved VecNormalize + SB3 mean, independent of FrozenActor.
            normalized = self.norm.normalize_obs(encoded[None])
            with torch.no_grad():
                self.raw = self.model.policy._predict(torch.from_numpy(normalized),
                                                     deterministic=True).numpy()[0]
            self.bounded = np.clip(self.raw, -1., 1.)
            self.held = self.bounded.astype(np.float64 if self.wide else np.float32)
            self.held = self.held * self.limits.astype(self.held.dtype)
            if self.arm == "residual":
                self.held *= self.config["residual_cap_fraction"]
            self.calls += 1
        base = baseline if self.wide else baseline.astype(np.float32)
        command = self.held + base if self.arm == "residual" else self.held
        command = np.clip(command, -self.limits, self.limits).astype(float)
        # Exact analytical endpoints; OLD history throughout, then prepend total.
        segments = ([(self.n-1, .001), (self.n-2, .001)] if self.delay % 2
                    else [(self.n-1, .002)])
        for index, duration in segments:
            delivered = self.history[index]
            self.torque = delivered + (self.torque-delivered) * math.exp(-duration/.005)
        self.history[1:self.n] = self.history[:self.n-1].copy()
        self.history[0] = command
        self.phase = (self.phase + 1) % self.config["policy_hold_ticks"]
        return np.r_[encoded, self.raw, self.bounded, self.held, baseline,
                     np.clip(baseline, -self.limits, self.limits), command,
                     self.torque, self.history.ravel(), self.phase, self.calls]


class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.started = time.monotonic()
        # Preserve all generated artifacts/logs, including failed runs, externally.
        cls.build = Path(tempfile.mkdtemp(prefix="wbr-b2-integration-"))
        cls.profiles = json.loads((ROOT / "sim/control_c/fixtures/recorded.json").read_text())["profiles"]
        cls.fixtures, cls.errors, cls.wide_errors, cls.c_wide_errors = {}, {}, {}, {}
        cls.ticks = 0
        for name, arm, constant in (("direct", "direct", None),
                                    ("residual", "residual", None),
                                    ("zero", "residual", [0, 0]),
                                    ("positive", "residual", [2, -2]),
                                    ("negative", "residual", [-2, 2])):
            folder = cls.build / name
            folder.mkdir()
            env = VecNormalize(DummyVecEnv([TinyEnv]), norm_obs=True, norm_reward=False,
                               clip_obs=2.5, epsilon=1e-7)
            env.obs_rms.update(np.random.default_rng(4).normal(size=(20, 15)))
            env.obs_rms.var[0] = 0.
            env.training = False
            model = PPO("MlpPolicy", env, n_steps=2, batch_size=2, seed=7, device="cpu",
                        policy_kwargs={"net_arch": dict(pi=[8, 8], vf=[8])})
            with torch.no_grad():
                model.policy.action_net.weight.mul_(300.)
                if constant is not None:
                    model.policy.action_net.weight.zero_()
                    model.policy.action_net.bias.copy_(torch.tensor(constant))
            model.save(folder / "final.zip")
            env.save(folder / "vecnormalize.pkl")
            (folder / "status.json").write_text(json.dumps({"status": "COMPLETE",
                "checkpoint_reload": "PASS", "arm": arm, "fixture": "untrained deterministic"}))
            actor, saved_model, norm, hashes = load_completed(folder)
            export_c(actor, folder)
            command = [*shlex.split(os.environ.get("CC", "cc")), "-std=c99", "-O2",
                       "-Wall", "-Wextra", "-Werror", "-pedantic", "-ffp-contract=off",
                       "-shared", "-fPIC", "-I", str(ROOT / "sim/control_c"),
                       "-I", str(folder), str(INTEGRATION / "host.c"),
                       str(ROOT / "sim/control_c/wbr_lqr.c"), str(folder / "policy.c"),
                       "-lm", "-o", str(folder / "host.so")]
            run = subprocess.run(command, capture_output=True, text=True, timeout=10)
            (folder / "compile.log").write_text(shlex.join(command)+"\n"+run.stdout+run.stderr)
            if run.returncode:
                raise RuntimeError(f"Compile failed: {folder / 'compile.log'}")
            lib = ctypes.CDLL(str(folder / "host.so"))
            f64 = np.ctypeslib.ndpointer(dtype=np.float64, flags="C_CONTIGUOUS")
            lib.host_tick.argtypes = [f64, f64]
            lib.host_init.argtypes = [ctypes.c_uint]
            lib.host_reset.argtypes = []
            for fn in (lib.host_tick, lib.host_init, lib.host_reset):
                fn.restype = ctypes.c_int
            cls.fixtures[name] = lib, saved_model, norm, arm
            (folder / "source_hashes.json").write_text(json.dumps(hashes, indent=2))
            env.close()

    @classmethod
    def tearDownClass(cls):
        report = {"max_absolute_errors": cls.errors,
                  "float32_vs_simulator_float64_max_absolute_errors": cls.wide_errors,
                  "c_vs_simulator_float64_max_absolute_errors": cls.c_wide_errors,
                  "compiled_fixtures": len(cls.fixtures), "replayed_ticks": cls.ticks,
                  "a2_atol": A2_ATOL, "a2_rtol": 0,
                  "b2_atol": B2_ATOL, "b2_rtol": B2_RTOL,
                  "elapsed_s": time.monotonic()-cls.started,
                  "scope": "Controller arithmetic replay only; no closed-loop plant result"}
        (cls.build / "report.json").write_text(json.dumps(report, indent=2)+"\n")
        print(f"\nIntegration artifacts: {cls.build}\n{json.dumps(report, indent=2)}")

    def start(self, name, profile):
        lib, model, norm, arm = self.fixtures[name]
        self.assertEqual(lib.host_init(profile["delay_ms"]), 0)
        return (lib, Oracle(profile, model, norm, arm),
                Oracle(profile, model, norm, arm, float64_composition=True))

    def tick(self, context, measurement):
        lib, oracle, wide = context
        actual = np.zeros(37)
        self.assertEqual(lib.host_tick(np.ascontiguousarray(measurement, dtype=float), actual), 0)
        expected, wide_row = oracle.tick(measurement), wide.tick(measurement)
        type(self).ticks += 1
        self.assertTrue(np.isfinite(actual).all())
        for label, section, atol, rtol in (
                ("encoded", slice(0, 15), A2_ATOL, 0),
                ("policy", slice(15, 21), B2_ATOL, B2_RTOL),
                ("lqr", slice(21, 25), A2_ATOL, 0),
                ("issued", slice(25, 27), B2_ATOL, B2_RTOL),
                ("torque_history", slice(27, 35), A2_ATOL, 0)):
            self.errors[label] = max(self.errors.get(label, 0.),
                                     float(abs(actual[section]-expected[section]).max()))
            np.testing.assert_allclose(actual[section], expected[section], atol=atol, rtol=rtol,
                                       err_msg=label)
        np.testing.assert_array_equal(actual[35:], expected[35:])
        for label, section in (("issued_Nm", slice(25, 27)), ("lqr_requested_Nm", slice(21, 23)),
                               ("torque_history_Nm", slice(27, 35))):
            self.wide_errors[label] = max(self.wide_errors.get(label, 0.),
                                         float(abs(expected[section]-wide_row[section]).max()))
            self.c_wide_errors[label] = max(self.c_wide_errors.get(label, 0.),
                                           float(abs(actual[section]-wide_row[section]).max()))
        # Prove history stores the total, not baseline or residual in isolation.
        np.testing.assert_array_equal(actual[29:31], actual[25:27])
        return actual

    def test_zero_correction_matches_archived_a2_vectors(self):
        for profile in self.profiles:
            context = self.start("zero", profile)
            for record in profile["archive_case"]["records"]:
                row = self.tick(context, record["input"])
                np.testing.assert_array_equal(row[19:21], [0, 0])
                expected = record["requested"] + record["clipped"]
                np.testing.assert_allclose(row[21:25], expected, atol=A2_ATOL, rtol=0)
                n = 2 + 2*profile["history_steps"]
                np.testing.assert_allclose(row[27:27+n], record["after"], atol=A2_ATOL, rtol=0)

    def test_direct_and_residual_measured_replay_and_five_tick_hold(self):
        for name in ("direct", "residual"):
            for profile in self.profiles:
                context = self.start(name, profile)
                mean = context[1].norm.obs_rms.mean.copy()
                var = context[1].norm.obs_rms.var.copy()
                rows = [self.tick(context, r["input"]) for r in profile["archive_case"]["records"]]
                for tick, row in enumerate(rows):
                    self.assertEqual(row[36], tick//5+1)
                    if tick % 5:
                        np.testing.assert_array_equal(row[15:21], rows[tick-1][15:21])
                self.assertTrue(any(not np.array_equal(r[21:23], rows[0][21:23]) for r in rows[1:5]))
                self.assertTrue(any(not np.array_equal(rows[t][19:21], rows[t-5][19:21])
                                    for t in range(5, len(rows), 5)))
                np.testing.assert_array_equal(mean, context[1].norm.obs_rms.mean)
                np.testing.assert_array_equal(var, context[1].norm.obs_rms.var)

    def test_residual_is_added_before_saturation_both_signs(self):
        for name, sign in (("positive", 1), ("negative", -1)):
            for profile in self.profiles:
                context = self.start(name, profile)
                oracle = context[1]
                for tick in range(12):
                    # Deliberate bounded sensor stimuli, not a gain/controller change.
                    target = sign * np.array([-2.2, 4.4] if tick % 2 == 0 else [3., -6.])
                    internal = oracle.baseline(np.zeros(6))
                    measurement = np.linalg.lstsq(-oracle.k[:, :6], target-internal, rcond=None)[0]
                    self.assertLess(float(abs(measurement).max()), 10.)
                    row = self.tick(context, measurement)
                    np.testing.assert_allclose(row[21:23], target, atol=A2_ATOL, rtol=0)
                    np.testing.assert_allclose(row[19:21], sign*np.array([.4, -.8]), atol=A2_ATOL, rtol=0)
                    if tick % 2 == 0:
                        wrong = np.clip(row[23:25].astype(np.float32)+row[19:21].astype(np.float32), [-2,-4], [2,4])
                        self.assertGreater(float(abs(row[25:27]-wrong).min()), .19)
                    else:
                        np.testing.assert_array_equal(row[25:27], sign*np.array([2., -4.]))

    def test_reset_discards_hold_phase_torque_and_pending_history(self):
        for name in ("direct", "residual", "zero"):
            for profile in self.profiles:
                for ticks in (1, 2, 6, 9):
                    context = self.start(name, profile)
                    for _ in range(ticks):
                        self.tick(context, [1., -.1, .2, -.2, .1, -.1])
                    self.assertEqual(context[0].host_reset(), 0)
                    context[1].reset()
                    context[2].reset()
                    for tick in range(8):
                        row = self.tick(context, np.zeros(6))
                        if tick == 0:
                            np.testing.assert_array_equal(row[6:14], np.zeros(8))
                            np.testing.assert_array_equal(row[21:25], np.zeros(4))
                            self.assertEqual(row[36], 1)


if __name__ == "__main__":
    unittest.main()
