"""Runner pieces that need no full episode."""

import hashlib
import json
from pathlib import Path
import unittest

import numpy as np

from sim.pil.run import compare, load_gains

FIXTURE = Path(__file__).resolve().parents[2] / "control_c/fixtures/recorded.json"


class Runner(unittest.TestCase):
    def test_gains_match_recorded_k_used_bytes(self):
        gains = load_gains()
        for profile in json.loads(FIXTURE.read_text())["profiles"]:
            k = gains[profile["delay_ms"]]
            self.assertEqual(k.shape, (2, 8 + 2 * profile["history_steps"]))
            self.assertTrue(np.array_equal(k, np.asarray(profile["K"])))
            self.assertEqual(hashlib.sha256(k.astype("<f8").tobytes()).hexdigest(), profile["K_sha256"])

    def test_compare_counts_and_pairs(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            results = []
            for controller, success, rec in (("python", True, 2.5), ("pil", False, None)):
                path = Path(tmp) / controller
                path.mkdir()
                np.save(path / "truth_after.npy", np.zeros((3, 6)) + (controller == "pil") * 1e-3)
                results.append({"controller": controller, "delay_ms": 2, "scenario": "push", "noise_seed": 1000,
                                "success": success, "recovery_time_after_event_s": rec, "path": str(path),
                                "link": {} if controller == "python" else {
                                    "round_trip_s": {"p50": 1e-3, "p99": 2e-3, "max": 3e-3},
                                    "mcu_exec_s": {"p50": 1e-6, "max": 2e-6},
                                    "max_abs_torque_diff_vs_python_Nm": 0.0}})
            s = compare(results)
        self.assertEqual((s["python"]["success"], s["pil"]["success"]), (1, 0))
        self.assertEqual(s["pil_vs_python"]["outcome_mismatches"], 1)
        self.assertAlmostEqual(s["pil_vs_python"]["max_abs_true_state_diff"], 1e-3)


if __name__ == "__main__":
    unittest.main()
