"""Runner wiring with synthetic backends only; these are NOT physics results."""

from dataclasses import dataclass
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from sim.gain_schedule.model import DEFAULT_DELAYS, DEFAULT_LENGTHS, EVALUATION_LENGTHS, training_midpoints
from sim.gain_schedule.run import evaluate, fit_sweep, linear_check, main, sweep


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
            size = 8 + 2 * int(np.ceil(effects.delay_s / 0.002))
            gain = np.full((2, size), length**2 + effects.delay_s)
            B = np.zeros((size, 2))
            B[0, 0] = 1
            record = {
                "synthetic": True, "state_order": [f"z{i}" for i in range(size)],
                "max_closed_loop_pole_magnitude": 0.5, "DARE_relative_residual": 0.,
                "A_discrete_actual": (np.eye(size) * 0.5).tolist(),
                "B_discrete_actual": B.tolist(), "dt_s": 0.002,
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
            lengths = [0.12, 0.14, 0.16, 0.18, 0.20]
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
            result = sweep(SimpleNamespace(lengths=[0.12, 0.20], delays=[0.002],
                                           config=Path("unused")), root)
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertEqual(len(result["errors"]), 2)
            self.assertIn("synthetic error", (root / "length_00/delay_00.error.txt").read_text())
            with self.assertRaisesRegex(ValueError, "complete"):
                fit_sweep(SimpleNamespace(sweep=root / "sweep.json", degree=1,
                                          max_condition=1e8), root)

    def make_schedule(self, root):
        sweep_out, fit_out = root / "sweep", root / "fit"
        sweep_out.mkdir()
        fit_out.mkdir()
        sweep(SimpleNamespace(lengths=DEFAULT_LENGTHS, delays=DEFAULT_DELAYS,
                              config=Path("unused")), sweep_out)
        fit_sweep(SimpleNamespace(sweep=sweep_out / "sweep.json", degree=3,
                                  max_condition=1e8), fit_out)
        return fit_out / "schedule.json"

    def test_midpoints_use_fresh_actual_matrices_and_retain_unstable_fit(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, self.modules), \
                patch("sim.gain_schedule.run.source_info", return_value={"synthetic": True}), \
                patch("builtins.print"):
            root = Path(tmp)
            path = self.make_schedule(root)
            saved = json.loads(path.read_text())
            # Deliberately destabilize one fitted regime: A00=.5, B00=1, K00=-.6.
            coefficients = np.asarray(saved["regimes"][0]["fit"]["coefficients"])
            coefficients[:, 0, 0] = [-.6, 0, 0, 0]
            saved["regimes"][0]["fit"]["coefficients"] = coefficients.tolist()
            path.write_text(json.dumps(saved))
            self.augmented_calls.clear()
            out = root / "linear"
            out.mkdir()
            result = linear_check(SimpleNamespace(schedule=path), out)
            self.assertEqual((result["status"], result["checks_completed"]), ("COMPLETE", 32))
            self.assertEqual(result["polynomial_local_acceptance"], "FAIL")
            self.assertEqual(result["nonlinear_cases_run"], 0)
            self.assertEqual(self.cases, [])
            self.assertEqual(self.augmented_calls,
                             [(L, d) for d in DEFAULT_DELAYS for L in training_midpoints(DEFAULT_LENGTHS)])
            panel = json.loads((out / "linear_checks.json").read_text())
            self.assertEqual(sum(c["polynomial_local_status"] == "FAIL" for c in panel["cases"]), 8)
            for case in panel["cases"]:
                folder = out / case["artifact_directory"]
                check = json.loads((folder / "polynomial_check.json").read_text())
                design = json.loads((folder / check["actual_matrices_file"]).read_text())
                A, B, K = (np.asarray(v) for v in (design["A_discrete_actual"],
                           design["B_discrete_actual"], check["Kfit"]))
                expected = np.linalg.eigvals(A - B @ K)
                actual = np.array([complex(*p) for p in check["polynomial_closed_loop_eigenvalues"]])
                np.testing.assert_allclose(actual, expected)
                radius = max(abs(expected))
                self.assertAlmostEqual(check["margin_to_one"], 1 - radius)
                if radius > 1:
                    self.assertAlmostEqual(radius, 1.1)
                    self.assertIsNone(check["slowest_time_constant_s"])
                else:
                    self.assertAlmostEqual(check["slowest_time_constant_s"], -.002 / np.log(radius))

    def test_midpoint_order_mismatch_is_retained_and_other_regimes_continue(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, self.modules), \
                patch("sim.gain_schedule.run.source_info", return_value={"synthetic": True}), \
                patch("builtins.print"):
            root = Path(tmp)
            path = self.make_schedule(root)
            schedule = json.loads(path.read_text())
            schedule["regimes"][0]["state_order"].reverse()
            path.write_text(json.dumps(schedule))
            out = root / "linear"
            out.mkdir()
            result = linear_check(SimpleNamespace(schedule=path), out)
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertEqual(result["checks_completed"], 24)
            self.assertEqual(len(result["errors"]), 8)
            self.assertIn("state/input order", result["errors"][0]["error"])
            self.assertTrue((out / "delay_00/midpoint_00/exact_design.json").exists())
            self.assertTrue((out / "delay_00/midpoint_00/error.txt").exists())
            self.assertEqual(self.cases, [])

    def test_nonlinear_evaluator_rejects_legacy_domain_and_impossible_length_before_physics(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, self.modules), \
                patch("sim.gain_schedule.run.source_info", return_value={"synthetic": True}), \
                patch("builtins.print"):
            root = Path(tmp)
            path = self.make_schedule(root)
            original = json.loads(path.read_text())
            self.nominal_calls.clear()
            self.augmented_calls.clear()
            for legacy, lengths in ((True, EVALUATION_LENGTHS), (False, [0.12, 0.21])):
                schedule = deepcopy(original)
                if legacy:
                    schedule["regimes"][-1]["fit"]["domain_m"] = [0.12, 0.30]
                path.write_text(json.dumps(schedule))
                with self.subTest(legacy=legacy), self.assertRaises(ValueError):
                    evaluate(SimpleNamespace(schedule=path, lengths=lengths, seeds=[0]), root)
            self.assertEqual(self.nominal_calls, [])
            self.assertEqual(self.augmented_calls, [])
            self.assertEqual(self.cases, [])
            self.assertFalse((root / "evaluation.json").exists())

    def test_cli_defaults_select_nine_training_five_evaluation_and_all_midpoints(self):
        with tempfile.TemporaryDirectory() as tmp, patch("builtins.print"):
            for command, extras, handler in (("sweep", [], "sweep"),
                    ("fit", ["--sweep", "unused"], "fit_sweep"),
                    ("linear-check", ["--schedule", "unused"], "linear_check"),
                    ("evaluate", ["--schedule", "unused"], "evaluate")):
                with patch("sim.gain_schedule.run." + handler, return_value={"status": "COMPLETE"}) as run:
                    self.assertEqual(main([command, *extras, "--out", str(Path(tmp) / command)]), 0)
                    args = run.call_args.args[0]
                    if command == "sweep":
                        self.assertEqual(args.lengths, (.12, .13, .14, .15, .16, .17, .18, .19, .20))
                        self.assertEqual(args.delays, (.002, .003, .004, .005))
                    elif command == "fit":
                        self.assertEqual(args.degree, 3)
                    elif command == "evaluate":
                        self.assertEqual(args.lengths, (.12, .135, .16, .185, .20))
                        self.assertEqual(args.seeds, list(range(5)))
                        self.assertEqual(sum(L not in DEFAULT_LENGTHS for L in args.lengths), 2)
                    else:
                        self.assertFalse(hasattr(args, "lengths"))  # derived from saved training grid

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
