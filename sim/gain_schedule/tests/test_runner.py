"""Runner wiring with synthetic backends only; these are NOT physics results."""

from dataclasses import dataclass
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from sim.gain_schedule.model import EVALUATION_LENGTHS
from sim.gain_schedule.run import evaluate, fit_sweep, main, sweep


@dataclass(frozen=True)
class SyntheticConfig:
    delay_s: float = 0.002
    motor_time_constant_s: tuple = (0.005, 0.005)
    integration_max_step_s: float = 0.00025
    body_angle_std_deg: float = 0.1
    body_gyro_std_rad_s: float = 0.01


class RunnerTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[3]
        self.base = json.loads((root / "sim/configs/assumed_planar.json").read_text())
        self.nominal_calls, self.augmented_calls, self.cases = [], [], []

        def nominal(plant):
            self.nominal_calls.append(plant.cfg["physics"]["leg_length"]["value"])
            return np.full((2, 6), 123.), {"synthetic": True}

        def augmented(cfg, effects, nominal_gain):
            np.testing.assert_array_equal(nominal_gain, np.full((2, 6), 123.))
            length = cfg["physics"]["leg_length"]["value"]
            self.augmented_calls.append((length, effects.delay_s))
            size = 10 if effects.delay_s == 0.002 else 12
            gain = np.full((2, size), length**2 + effects.delay_s)
            record = {
                "synthetic": True, "state_order": [f"z{i}" for i in range(size)],
                "max_closed_loop_pole_magnitude": 0.5, "DARE_relative_residual": 0.,
                "A_discrete_actual": (np.eye(size) * 0.5).tolist(),
                "B_discrete_actual": np.zeros((size, 2)).tolist(),
            }
            return gain, record

        def evaluate_case(runtime, feedback, scenario, seed, out):
            out.mkdir(parents=True)
            size = 10 if runtime.effects.delay_s == 0.002 else 12
            action = feedback(SimpleNamespace(vector=lambda: np.ones(size)))
            self.assertEqual(action.shape, (2,))
            self.cases.append((runtime.cfg, runtime.effects, scenario, seed))
            metrics = {"status": "FAIL" if scenario == "push" else "PASS",
                       "failed_checks": ["synthetic_push_failure"] if scenario == "push" else []}
            (out / "metrics.json").write_text(json.dumps(metrics))
            return metrics

        self.modules = {
            "sim.augmented": SimpleNamespace(
                RuntimeConfig=SyntheticConfig,
                load_experiment=lambda path: (self.base, {"synthetic": True}, SyntheticConfig()),
                AugmentedRuntime=lambda cfg, effects: SimpleNamespace(cfg=cfg, effects=effects)),
            "sim.augmented_lqr": SimpleNamespace(synthesize_augmented=augmented),
            "sim.augmented_eval": SimpleNamespace(evaluate=evaluate_case),
            "sim.lqr": SimpleNamespace(synthesize=nominal),
            "sim.planar": SimpleNamespace(
                Plant=lambda cfg: SimpleNamespace(cfg=cfg, xml="<synthetic/>")),
        }

    def test_sweep_fit_and_five_length_evaluation_without_physics(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, self.modules), \
                patch("sim.gain_schedule.run.source_info", return_value={"synthetic": True}), \
                patch("builtins.print"):
            root = Path(tmp)
            sweep_out, fit_out, eval_out = (root / name for name in ("sweep", "fit", "evaluation"))
            for path in (sweep_out, fit_out, eval_out):
                path.mkdir()
            lengths = [0.12, 0.16, 0.20, 0.25, 0.30]
            result = sweep(SimpleNamespace(lengths=lengths, delays=[0.002, 0.003],
                                           config=Path("unused")), sweep_out)
            self.assertEqual(result["designs_completed"], 10)
            self.assertEqual(result["physics_acceptance"], "NOT_EVALUATED")
            self.assertEqual(self.nominal_calls, lengths)
            fit_sweep(SimpleNamespace(sweep=sweep_out / "sweep.json", degree=3,
                                      max_condition=1e8), fit_out)
            result = evaluate(SimpleNamespace(schedule=fit_out / "schedule.json",
                                              lengths=EVALUATION_LENGTHS, seeds=[0, 1]), eval_out)
            self.assertEqual(result["status"], "COMPLETE")
            self.assertEqual(result["acceptance"], {"fresh_dare": "FAIL", "polynomial": "FAIL"})
            # Each evaluated length is freshly synthesized, including off-grid lengths.
            self.assertEqual(self.nominal_calls[5:], list(EVALUATION_LENGTHS))
            self.assertEqual(len(self.augmented_calls), 20)
            self.assertEqual(len(self.cases), 5 * 2 * 2 * 2 * 2)
            for cfg, _, _, _ in self.cases:
                self.assertEqual(cfg["protocol"], self.base["protocol"])
                self.assertEqual(cfg["controller"], self.base["controller"])
            saved = json.loads((eval_out / "evaluation.json").read_text())
            self.assertEqual(len(saved["cases"]), len(self.cases))
            self.assertTrue(all(c["failed_checks"] == ["synthetic_push_failure"]
                                for c in saved["cases"] if c["scenario"] == "push"))

    def test_failed_design_is_retained_and_cannot_be_fitted(self):
        self.modules["sim.augmented_lqr"] = SimpleNamespace(
            synthesize_augmented=lambda *args: (_ for _ in ()).throw(RuntimeError("synthetic error")))
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, self.modules), \
                patch("sim.gain_schedule.run.source_info", return_value={"synthetic": True}):
            root = Path(tmp)
            result = sweep(SimpleNamespace(lengths=[0.12, 0.30], delays=[0.002],
                                           config=Path("unused")), root)
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertEqual(len(result["errors"]), 2)
            self.assertIn("synthetic error", (root / "length_00/delay_00.error.txt").read_text())
            with self.assertRaisesRegex(ValueError, "complete"):
                fit_sweep(SimpleNamespace(sweep=root / "sweep.json", degree=1,
                                          max_condition=1e8), root)

    def test_cli_retains_errors_and_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp, patch("builtins.print"):
            root = Path(tmp)
            missing = root / "missing.json"
            out = root / "new_output"
            args = ["fit", "--sweep", str(missing), "--out", str(out)]
            self.assertEqual(main(args), 1)
            self.assertEqual(json.loads((out / "result.json").read_text())["status"], "ERROR")
            before = (out / "error.txt").read_bytes()
            with self.assertRaises(FileExistsError):
                main(args)
            self.assertEqual((out / "error.txt").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
