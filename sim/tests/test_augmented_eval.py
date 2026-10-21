"""Retained reporting fixtures only: scripted states, no physics or synthesis."""

from copy import deepcopy
from dataclasses import asdict
import csv
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

from sim.augmented import Interval, Observation, RuntimeConfig, StepResult
from sim.augmented_eval import evaluate
from sim.gain_schedule import run
from sim.gain_schedule.model import FAMILY
from sim.planar import STATE_NAMES


FINITE = np.array([.01, .01, -.005, .02, -.03, .04])
CONFIG = Path(__file__).resolve().parents[1]/"configs"/"assumed_planar.json"


class ScriptedRuntime:
    """A two-tick trace with optional corruption in a recorded subinterval."""

    def __init__(self, states, interval_truth=None):
        cfg = json.loads(CONFIG.read_text())
        cfg["protocol"].update(duration_s=.004, settle_window_s=.002,
                               push_start_s=.002, push_duration_s=.002,
                               initial_state=FINITE.tolist())
        self.plant = SimpleNamespace(cfg=cfg)
        self.config = RuntimeConfig()
        self.dt, self.history_steps = .002, 1
        self.limits, self.warning_counts = np.array([2., 4.]), [0]
        self.states = [np.array(s, dtype=float) for s in states]
        self.interval_truth = interval_truth

    @property
    def time(self):
        return self.steps*self.dt

    def reset(self, seed=0):
        self.steps = 0
        return self.observation()

    def truth(self):
        return self.states[self.steps].copy()

    def sensor_noise(self):
        return np.zeros(2)

    def torque(self):
        return np.zeros(2)

    def observation(self):
        return Observation(self.time, self.truth(), np.zeros(2), np.zeros((1, 2)),
                           np.array([-self.dt]), self.config.delay_s)

    def step(self, raw, push_N=0.):
        if self.steps >= len(self.states)-1:
            raise AssertionError("Extra dynamics step after terminal truth")
        intervals = []
        for half in range(2):
            truth = self.truth() if half == 0 or self.interval_truth is None else self.interval_truth
            intervals.append(Interval(self.time+half*self.dt/2, self.dt/2, truth,
                                      np.zeros(2), np.zeros(2), np.zeros(2), np.zeros(2),
                                      np.zeros(2), None, push_N))
        self.steps += 1
        return StepResult(self.observation(), np.asarray(raw),
                          np.clip(raw, -self.limits, self.limits), tuple(intervals))


class AugmentedEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix="wbr-nonfinite-eval-"))
        print(f"Retained synthetic reporting artifacts: {cls.root}", flush=True)

    def read_metrics(self, path):
        def reject_constant(value):
            self.fail(f"Non-JSON numeric literal: {value}")
        return json.loads(path.read_text(), parse_constant=reject_constant)

    def test_nonfinite_initial_and_terminal_truth_is_saved_without_extra_step(self):
        # Every coordinate, including velocities that do not trigger fall/displacement.
        for label, bad in (("nan", np.nan), ("posinf", np.inf), ("neginf", -np.inf)):
            for coordinate in range(6):
                for prefix in (0, 1, 2):
                    with self.subTest(value=label, coordinate=coordinate, prefix=prefix):
                        terminal = FINITE.copy()
                        terminal[coordinate] = bad
                        runtime = ScriptedRuntime([FINITE]*prefix + [terminal])
                        controller = Mock(return_value=np.array([.25, -.5]))
                        out = self.root/f"{label}_{coordinate}_{prefix}"
                        metrics = evaluate(runtime, controller, "push", 7, out)
                        saved = self.read_metrics(out/"metrics.json")
                        self.assertEqual(saved["status"], "FAIL")
                        self.assertFalse(saved["checks"]["numerics"])
                        self.assertTrue(saved["numerical_failure"])
                        self.assertIn("numerics", saved["failed_checks"])
                        self.assertEqual(saved["final_error"], metrics["final_error"])
                        expected = FINITE.tolist()
                        expected[coordinate] = None
                        self.assertEqual(saved["final_error"], expected)
                        self.assertEqual(saved["initial_state"], expected if not prefix else FINITE.tolist())
                        if prefix:
                            window = abs(FINITE).tolist()
                            window[coordinate] = None
                            self.assertEqual(saved["final_window_max_abs_error"], window)
                            np.testing.assert_allclose(saved["state_rmse_over_actual_duration"], abs(FINITE))
                        else:
                            self.assertIsNone(saved["final_window_max_abs_error"])
                            self.assertIsNone(saved["state_rmse_over_actual_duration"])
                        self.assertIsNone(saved["recovery_time_after_event_s"])
                        self.assertFalse(saved["held_final_window"])
                        if coordinate == 0:
                            self.assertIsNone(saved["peak_displacement_m"])
                        else:
                            self.assertEqual(saved["peak_displacement_m"], .01)
                        if coordinate in (1, 2):
                            self.assertIsNone(saved["peak_tilt_deg"])
                            self.assertIsNone(saved["peak_tilt_after_push_start_deg"])
                        else:
                            self.assertAlmostEqual(saved["peak_tilt_deg"], np.rad2deg(.01))
                        self.assertEqual(runtime.steps, prefix)
                        self.assertEqual(controller.call_count, prefix)
                        self.assertEqual(saved["control_steps"], prefix)
                        self.assertEqual(saved["integration_steps"], 2*prefix)
                        with (out/"control.csv").open() as stream:
                            rows = list(csv.DictReader(stream))
                        self.assertEqual(len(rows), prefix+1)
                        raw_failure = float(rows[-1][STATE_NAMES[coordinate]])
                        self.assertTrue(np.isnan(raw_failure) if label == "nan" else raw_failure == bad)
                        self.assertEqual(float(rows[-1]["interval_dt_s"]), 0.)

    def test_nonfinite_subinterval_summaries_keep_finite_components(self):
        for label, bad in (("nan", np.nan), ("posinf", np.inf), ("neginf", -np.inf)):
            with self.subTest(value=label):
                terminal = FINITE.copy()
                terminal[5] = bad
                runtime = ScriptedRuntime([FINITE, terminal], interval_truth=terminal)
                out = self.root/f"interval_{label}"
                evaluate(runtime, lambda obs: [0., 0.], "balance", 0, out)
                saved = self.read_metrics(out/"metrics.json")
                self.assertEqual(saved["status"], "FAIL")
                self.assertFalse(saved["checks"]["numerics"])
                self.assertTrue(saved["numerical_failure"])
                for key in ("state_squared_error_integral", "state_rmse_over_actual_duration"):
                    self.assertIsNone(saved[key][5])
                    self.assertTrue(all(v is not None for v in saved[key][:5]))
                np.testing.assert_allclose(saved["state_squared_error_integral"][:5],
                                           [2e-7, 2e-7, 5e-8, 8e-7, 1.8e-6])
                np.testing.assert_allclose(saved["state_rmse_over_actual_duration"][:5], abs(FINITE[:5]))
                self.assertEqual(runtime.steps, 1)

    def test_open_loop_nonfinite_truth_remains_a_numerical_failure(self):
        for label, bad in (("nan", np.nan), ("posinf", np.inf), ("neginf", -np.inf)):
            with self.subTest(value=label):
                terminal = FINITE.copy()
                terminal[1] = bad
                runtime = ScriptedRuntime([terminal])
                controller = Mock(side_effect=AssertionError("Terminal controller call"))
                out = self.root/f"open_loop_{label}"
                evaluate(runtime, controller, "open_loop", 0, out)
                saved = self.read_metrics(out/"metrics.json")
                self.assertEqual(saved["status"], "FAIL")
                self.assertFalse(saved["checks"]["numerics"])
                self.assertTrue(saved["numerical_failure"])
                self.assertIsNone(saved["peak_tilt_deg"])
                self.assertEqual(runtime.steps, 0)
                controller.assert_not_called()

    def test_finite_pass_and_ordinary_fail_keep_numeric_results(self):
        for status, state in (("PASS", FINITE), ("FAIL", FINITE*2)):
            with self.subTest(status=status):
                out = self.root/f"finite_{status}"
                runtime = ScriptedRuntime([state]*3)
                evaluate(runtime, lambda obs: [.25, -.5], "push", 0, out)
                saved = self.read_metrics(out/"metrics.json")
                self.assertEqual(saved["status"], status)
                self.assertTrue(saved["checks"]["numerics"])
                self.assertFalse(saved["numerical_failure"])
                self.assertEqual(saved["failed_checks"], [] if status == "PASS" else
                                 ["held_final_window", "recovery_deadline"])
                self.assertEqual(saved["initial_state"], state.tolist())
                self.assertEqual(saved["final_error"], state.tolist())
                self.assertEqual(saved["final_window_max_abs_error"], abs(state).tolist())
                expected_integral = np.array([4e-7, 4e-7, 1e-7, 1.6e-6, 3.6e-6, 6.4e-6])
                np.testing.assert_allclose(saved["state_squared_error_integral"],
                                           expected_integral*(1 if status == "PASS" else 4))
                np.testing.assert_allclose(saved["state_rmse_over_actual_duration"], abs(state))
                self.assertEqual(saved["push_impulse_Ns"], .012)
                self.assertEqual(saved["push_duration_applied_s"], .002)
                self.assertEqual(saved["duration_s"], .004)
                self.assertEqual(saved["sum_actual_dt_s"], .004)
                self.assertEqual(saved["control_steps"], 2)
                self.assertEqual(saved["integration_steps"], 4)
                np.testing.assert_allclose(saved["clipped_command_squared_integral_Nm2_s"], [.00025, .001])

    def test_gain_schedule_caller_retains_failure_and_continues_without_physics(self):
        terminal = FINITE.copy()
        terminal[3] = np.nan
        runtimes = [ScriptedRuntime(states) for states in
                    ([terminal], [FINITE*2]*3, [FINITE]*3, [FINITE]*3)]
        cfg = deepcopy(runtimes[0].plant.cfg)
        gain = np.full((2, 10), .01)
        design = {"state_order": [f"z{i}" for i in range(10)],
                  "max_closed_loop_pole_magnitude": .5,
                  "A_discrete_actual": (.5*np.eye(10)).tolist(),
                  "B_discrete_actual": np.zeros((10, 2)).tolist()}
        schedule = {"schema_version": 1, "kind": "assumed_leg_schedule", "family": FAMILY,
                    "status": "COMPLETE", "reference_config": cfg,
                    "regimes": [{"runtime": asdict(RuntimeConfig()),
                                 "state_order": design["state_order"],
                                 "input_order": cfg["controller"]["input_order"], "fit": {}}]}
        schedule_path = self.root/"synthetic_schedule.json"
        schedule_path.write_text(json.dumps(schedule, allow_nan=False))
        out = self.root/"caller"
        out.mkdir()
        with patch("sim.augmented.AugmentedRuntime", side_effect=runtimes), \
                patch("sim.planar.Plant", return_value=SimpleNamespace(cfg=cfg)), \
                patch("sim.lqr.synthesize", return_value=(np.zeros((2, 6)), {})), \
                patch("sim.augmented_lqr.synthesize_augmented", return_value=(gain, design)), \
                patch.object(run, "evaluate_polynomial", return_value=gain), \
                patch.object(run, "source_info", return_value={"synthetic": True}):
            result = run.evaluate(SimpleNamespace(schedule=schedule_path, lengths=[.16], seeds=[0]), out)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["acceptance"], {"fresh_dare": "FAIL", "polynomial": "PASS"})
        manifest = self.read_metrics(out/"evaluation.json")
        self.assertEqual([case["status"] for case in manifest["cases"]], ["FAIL", "FAIL", "PASS", "PASS"])
        for case in manifest["cases"]:
            saved = self.read_metrics(out/case["artifact_directory"]/"metrics.json")
            self.assertEqual(case["status"], saved["status"])
            self.assertEqual(case["failed_checks"], saved["failed_checks"])
        self.assertEqual([r.steps for r in runtimes], [0, 2, 2, 2])


if __name__ == "__main__":
    unittest.main()
