import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from sim.policy_export.export import FrozenActor, contract, export_c, export_onnx, load_completed
from sim.policy_export.validate import HostPolicy, validate


torch.set_num_threads(1)


class TinyEnv(gym.Env):
    observation_space = gym.spaces.Box(-np.inf, np.inf, (15,), dtype=np.float64)
    action_space = gym.spaces.Box(-1., 1., (2,), dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        return np.zeros(15), {}


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.folder = Path(self.temporary.name)
        self.env = VecNormalize(DummyVecEnv([TinyEnv]), norm_obs=True, norm_reward=False,
                                clip_obs=2.5, epsilon=1e-7)
        self.env.obs_rms.update(np.random.default_rng(4).normal(size=(20, 15)))
        self.env.obs_rms.var[0] = 0.  # epsilon must remain inside the square root
        self.env.training = False
        self.model = PPO("MlpPolicy", self.env, n_steps=2, batch_size=2, seed=7,
                         policy_kwargs={"net_arch": dict(pi=[8, 8], vf=[8])}, device="cpu")
        with torch.no_grad():
            self.model.policy.action_net.weight.mul_(300.)
        self.model.save(self.folder / "final.zip")
        self.env.save(self.folder / "vecnormalize.pkl")
        self.status = {"status": "COMPLETE", "checkpoint_reload": "PASS", "arm": "direct"}
        self.write_status()

    def write_status(self):
        (self.folder / "status.json").write_text(json.dumps(self.status))

    def tearDown(self):
        self.env.close()
        self.temporary.cleanup()

    def test_saved_direct_and_residual_c_match_sb3(self):
        for arm in ("direct", "residual"):
            with self.subTest(arm=arm):
                self.status["arm"] = arm
                self.write_status()
                actor, model, norm, hashes = load_completed(self.folder)
                self.assertEqual(set(hashes), {"final.zip", "vecnormalize.pkl", "status.json"})
                out = self.folder / arm
                export_c(actor, out)
                report = validate(actor, model, norm, out)
                self.assertEqual(report["c_status"], "PASS")
                host = HostPolicy(out)
                _, _, held, _ = host.predict(np.ones(15), np.zeros(2, np.float32))
                cap = np.array([2., 4.]) * (0.2 if arm == "residual" else 1)
                self.assertTrue(np.all(abs(held) <= cap + 1e-6))
                # Composition is called again as causal LQR changes within a hold.
                for base in ([100., -100.], [-100., 100.]):
                    got = np.zeros(2, np.float32)
                    self.assertEqual(host.lib.wbr_compose(held, np.array(base, np.float32), got), 0)
                    expected = np.clip(held + (base if arm == "residual" else np.zeros(2)), [-2, -4], [2, 4])
                    np.testing.assert_allclose(got, expected, atol=1e-6)
                # Enforce caps even when an invalid oversized held value is supplied.
                got = np.zeros(2, np.float32)
                self.assertEqual(host.lib.wbr_compose(np.array([99, -99], np.float32), np.zeros(2, np.float32), got), 0)
                np.testing.assert_allclose(got, cap * [1, -1], atol=1e-6)

    def test_encoder_and_nonfinite_errors(self):
        actor = FrozenActor(self.model.policy, self.env, "direct")
        export_c(actor, self.folder)
        host = HostPolicy(self.folder)
        p, _ = contract()
        s = p["policy_input"]
        m, t, h = np.arange(6, dtype=float), np.array([.1, .2]), np.arange(6, dtype=float)
        got = np.zeros(15)
        self.assertEqual(host.lib.wbr_encode(m, t, h, .003, got), 0)
        expected = np.r_[m / s["sensor_divisors"], t / s["torque_estimate_divisors"],
                         (h.reshape(3, 2) / s["history_divisors"]).ravel(), .003 / s["delay_divisor_s"]]
        np.testing.assert_array_equal(got, expected)
        for bad in (float("nan"), float("inf")):
            x = np.zeros(15)
            x[3] = bad
            with self.assertRaises(ValueError):
                host.predict(x, np.zeros(2, np.float32))
            with self.assertRaises(ValueError):
                host.predict(np.zeros(15), np.array([bad, 0], np.float32))

    def test_incomplete_checkpoint_rejected(self):
        self.status["status"] = "RUNNING"
        self.write_status()
        with self.assertRaisesRegex(ValueError, "Refusing"):
            load_completed(self.folder)

    def test_unsupported_architecture_rejected(self):
        self.model.policy.mlp_extractor.policy_net[1] = torch.nn.Sigmoid()
        with self.assertRaisesRegex(ValueError, "Unsupported layer"):
            FrozenActor(self.model.policy, self.env, "direct")

    @unittest.skipUnless(importlib.util.find_spec("onnx") and importlib.util.find_spec("onnxruntime"),
                         "ONNX dependencies absent; actual ONNX export/runtime parity pending")
    def test_onnx_export_checker_and_runtime(self):
        for arm in ("direct", "residual"):
            with self.subTest(arm=arm):
                self.status["arm"] = arm
                self.write_status()
                actor, model, norm, _ = load_completed(self.folder)
                out = self.folder / (arm + "-onnx")
                export_c(actor, out)
                self.assertEqual(export_onnx(actor, out)["status"], "EXPORTED_CHECKED")
                self.assertTrue((out / "policy.onnx").is_file())
                report = validate(actor, model, norm, out)
                self.assertEqual(report["sb3_action_composition_reference"], "PASS")
                self.assertEqual(report["onnx"]["status"], "PASS")
                self.assertEqual(report["onnx"]["checker"], "PASS")
                self.assertEqual(report["onnx"]["batch_sizes"], [64, 1])
                self.assertEqual(set(report["onnx"]["max_abs_error_vs_c"]),
                                 {"raw", "bounded", "held_Nm", "command_Nm"})


if __name__ == "__main__":
    unittest.main()
