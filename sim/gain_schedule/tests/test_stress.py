"""Small retained fixtures; production still uses the full ten-second protocol."""

from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import mujoco
import numpy as np

from sim.augmented import AugmentedRuntime, load_experiment
from sim.augmented_lqr import synthesize_augmented
from sim.gain_schedule import stress
from sim.planar import FROM_JOINT, TO_JOINT, finite_difference


class StressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base, experiment, cls.effects = load_experiment(stress.CONFIG)
        cls.gain, _ = synthesize_augmented(cls.base, cls.effects, experiment["frozen_nominal"]["K"])
        cls.root = Path(tempfile.mkdtemp(prefix="stress-fixtures-", dir=os.getenv("WBR_STRESS_TEST_OUT")))
        print(f"Retained SMALL stress fixtures: {cls.root}", flush=True)

    def test_matched_nominal_action_parity_and_clipped_history(self):
        runtime = AugmentedRuntime(self.base, self.effects)
        controller = stress.DesignObserverController(self.gain, runtime.limits)
        obs = runtime.reset(seed=0)
        max_difference = 0.
        # Large measurement excursions force clipping, so raw-history errors cannot hide.
        for tick in range(120):
            measurement = obs.measurement.copy()
            if tick in (4, 5, 19, 20):
                measurement[1:3] += [2., -3.]
            obs = replace(obs, measurement=measurement)
            expected = -self.gain @ obs.vector()
            actual = controller(obs)
            max_difference = max(max_difference, float(np.max(abs(expected-actual))))
            np.testing.assert_allclose(actual, expected, atol=2e-12, rtol=1e-13)
            np.testing.assert_array_equal(controller.previous_clipped, np.clip(actual, -runtime.limits, runtime.limits))
            obs = runtime.step(actual).observation
            np.testing.assert_allclose(controller.estimated_tau, obs.torque_estimate, atol=1e-12, rtol=0)
        print(f"Matched nominal max action difference: {max_difference:.17g}", flush=True)

    def test_matched_independent_closed_loop_trajectories(self):
        original = AugmentedRuntime(self.base, self.effects)
        adapted = stress.make_runtime(self.base, self.effects, stress.Condition())
        observer = stress.DesignObserverController(self.gain, original.limits)
        a, b = original.reset(seed=2), adapted.reset(seed=2)
        for _ in range(100):
            a = original.step(-self.gain @ a.vector()).observation
            b = adapted.step(observer(b)).observation
            np.testing.assert_allclose(adapted.truth(), original.truth(), atol=2e-12, rtol=1e-11)

    def test_unknown_delay_physical_truth_and_metadata_cannot_change_action(self):
        a = stress.make_runtime(self.base, self.effects, stress.Condition())
        b = stress.make_runtime(self.base, self.effects, stress.Condition(delay_s=.010, mass_scale=3, wheel_delta=2))
        self.assertNotEqual(a.state_size, b.state_size)
        ca = stress.DesignObserverController(self.gain, a.limits)
        cb = stress.DesignObserverController(self.gain, a.limits)
        rng = np.random.default_rng(22)
        for _ in range(20):
            measurement = rng.normal(size=6)
            b._data.qpos[:] = rng.normal(size=3)
            b._tau[:] = rng.normal(size=2)
            b._estimated_tau[:] = rng.normal(size=2)*50
            oa = replace(a.observation(), measurement=measurement)
            ob = replace(b.observation(), measurement=measurement,
                         command_history=rng.normal(size=(5, 2))*100,
                         command_times_s=np.arange(5)*99., time_s=999.)
            np.testing.assert_array_equal(ca(oa), cb(ob))
        # A minimal object with no metadata at all must also be accepted.
        controller = stress.DesignObserverController(self.gain, a.limits)
        np.testing.assert_array_equal(controller(SimpleNamespace(measurement=np.zeros(6))), 0.)

    def test_observer_one_tick_delay_independent_exponential_oracle(self):
        gain = np.zeros((2, 10))
        gain[:, :2] = -np.eye(2)
        c = stress.DesignObserverController(gain, [2, 4])
        c(SimpleNamespace(measurement=np.array([20., -20., 0., 0., 0., 0.])))
        np.testing.assert_array_equal(c.estimated_tau, 0.)
        c(SimpleNamespace(measurement=np.zeros(6)))
        np.testing.assert_allclose(c.estimated_tau, np.array([2., -4.])*(1-np.exp(-.002/.005)), atol=1e-15)
        c(SimpleNamespace(measurement=np.zeros(6)))
        np.testing.assert_allclose(c.estimated_tau, np.array([2., -4.])*(1-np.exp(-.4))*np.exp(-.4), atol=1e-15)

    def test_actual_mass_inertia_change_without_nominal_or_other_runtime_mutation(self):
        before = deepcopy(self.base)
        nominal = stress.make_runtime(self.base, self.effects, stress.Condition())
        changed = stress.make_runtime(self.base, self.effects, stress.Condition(mass_scale=3.))
        body = changed.plant.body_id
        self.assertEqual(changed.plant.model.body_mass[body], 6.)
        np.testing.assert_allclose(changed.plant.model.body_inertia[body], [.054]*3, rtol=0, atol=1e-16)
        np.testing.assert_array_equal(changed.plant.model.body_ipos[body], nominal.plant.model.body_ipos[body])
        self.assertEqual(self.base, before)
        self.assertEqual(nominal.plant.model.body_mass[body], 2.)
        self.assertIsNot(changed.plant.model, nominal.plant.model)
        # Replacement data is compatible with the replacement model and used by a real step.
        nominal.step([.2, -.3])
        changed.step([.2, -.3])
        self.assertGreater(np.linalg.norm(nominal.truth()-changed.truth()), 1e-6)

    def test_wheel_map_finite_jacobian_virtual_work_and_hip_unchanged(self):
        for delta in (-.5, 0., .167, .5, 1., 2.):
            p = stress.PerturbedPlant(self.base, delta)
            radius = self.base["physics"]["wheel_radius"]["value"]
            expected = np.array([[1/radius, 0], [-1+delta, -1], [-delta, 1.]])
            columns = []
            for u in np.eye(2):
                d = p.data([.1, .07, -.03, 0, 0, 0])
                p.forward(d, u)
                columns.append(TO_JOINT.T @ d.qfrc_actuator)
            np.testing.assert_allclose(np.column_stack(columns), expected, atol=1e-14)
            # Independent finite derivative of tendon length in virtual coordinates.
            epsilon = 1e-6
            derivatives = []
            for dq in epsilon*np.eye(3):
                plus, minus = p.data(np.r_[dq, [0, 0, 0]]), p.data(np.r_[-dq, [0, 0, 0]])
                derivatives.append((plus.ten_length[0]-minus.ten_length[0])/(2*epsilon))
            np.testing.assert_allclose(derivatives, expected[:, 0], atol=1e-12)
            dq, u = np.array([.2, -.3, .4]), np.array([.8, -.6])
            d = p.data()
            p.forward(d, u)
            self.assertAlmostEqual(float(dq @ expected @ u), float((TO_JOINT @ dq) @ d.qfrc_actuator), places=13)
            _, acceleration_map = finite_difference(p.derivative, epsilon)
            mass = np.zeros((3, 3))
            mujoco.mj_fullM(p.model, mass, d.qM)
            virtual_mass = TO_JOINT.T @ mass @ TO_JOINT
            np.testing.assert_allclose(acceleration_map[3:], np.linalg.solve(virtual_mass, expected), atol=1e-9)

    def test_real_early_failure_preserved_with_strict_checks(self):
        cfg = deepcopy(self.base)
        cfg["protocol"]["initial_state"][1] = np.deg2rad(46)
        out = self.root / "physical-failure"
        out.mkdir()
        study = stress.Study(out, cfg, self.effects, self.gain, {"fixture": True})
        row = study.run(stress.Condition())
        self.assertEqual(row["status"], "FAIL")
        self.assertIn("no_fall", row["failed_checks"])
        self.assertIn("full_duration", row["failed_checks"])
        self.assertEqual(row["metrics"]["duration_s"], 0.)
        self.assertEqual(json.loads((out/row["artifact_directory"]/"rollout/metrics.json").read_text())["status"], "FAIL")
        self.assertIs(study.run(stress.Condition()), row)
        self.assertEqual(len(study.cases), 1)

    def test_partial_exception_retained_then_independent_case_continues(self):
        cfg = deepcopy(self.base)
        cfg["protocol"].update(duration_s=.006, push_start_s=.002, push_duration_s=.002, settle_window_s=.002)
        out = self.root / "exception"
        out.mkdir()
        study = stress.Study(out, cfg, self.effects, self.gain, {"fixture": True})
        def broken(runtime, controller, scenario, seed, path):
            path.mkdir()
            (path / "partial.csv").write_text("actual partial marker\n")
            raise RuntimeError("injected evaluator interruption")
        with patch.object(stress, "evaluate", side_effect=broken):
            row = study.run(stress.Condition())
        self.assertEqual(row["status"], "ERROR")
        self.assertIn("injected evaluator interruption", (out/row["artifact_directory"]/"error.txt").read_text())
        self.assertTrue((out/row["artifact_directory"]/"rollout/partial.csv").is_file())
        other = study.run(stress.Condition(push_N=12))
        self.assertIn(other["status"], ("PASS", "FAIL"))
        self.assertEqual(json.loads((out/"cases.json").read_text())[0]["status"], "ERROR")

    def test_declared_grid_budget_and_five_seed_boundary_reuse(self):
        for threshold in (6., 15., 90., float("inf")):
            calls = {}
            def run(c):
                if c not in calls:
                    calls[c] = {"id": str(len(calls)), "condition": stress.asdict(c),
                                "status": "FAIL" if c.push_N >= threshold else "PASS", "failed_checks": []}
                return calls[c]
            axes = stress.bounded_plan(run)
            self.assertEqual(next(iter(calls)), stress.Condition())
            self.assertLessEqual(len(calls), 57)
            self.assertEqual([r["condition"]["delay_s"] for r in axes["delay"]["seed0"]], [.002,.005,.006,.007,.008,.009,.010])
            self.assertEqual([r["condition"]["wheel_delta"] for r in axes["wheel_map"]["seed0"]], [-.5,0.,.167,.5,1.,2.])
            for axis in axes.values():
                for group in axis["confirmations"]:
                    self.assertEqual([r["condition"]["seed"] for r in group["cases"]], list(range(5)))
                    self.assertIs(group["cases"][0], calls[stress.Condition(**group["cases"][0]["condition"])])
            if threshold == float("inf"):
                self.assertEqual(axes["mass"]["seed0"][-1]["condition"]["mass_scale"], 8.)
                self.assertTrue(all(p["result"] == "NO_FAILURE_OBSERVED" for p in axes.values()))
            elif threshold > 6:
                push_values = sorted(r["condition"]["push_N"] for r in axes["push"]["seed0"])
                self.assertFalse(any(v > 96 for v in push_values))


if __name__ == "__main__":
    unittest.main()
