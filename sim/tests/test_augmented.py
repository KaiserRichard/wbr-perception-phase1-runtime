"""Behavioral checks; retained temp outputs include any failed integration case."""

from dataclasses import replace
import csv
from pathlib import Path
import tempfile
import unittest

import mujoco
import numpy as np

from sim.augmented import AugmentedRuntime, RuntimeConfig, gain_hash, load_experiment
from sim.augmented_eval import evaluate
from sim.augmented_lqr import linearize, synthesize_augmented
from sim.planar import Plant
from sim.run_augmented import verify_frozen
from sim.run_planar import evaluate as evaluate_nominal


CONFIG = Path(__file__).resolve().parents[1]/"configs"/"assumed_actuator_noise.json"


class AugmentedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base, cls.cfg, cls.effects = load_experiment(CONFIG)
        cls.K, cls.nominal_design = verify_frozen(cls.base, cls.cfg)

    def runtime(self, **kwargs):
        return AugmentedRuntime(self.base, replace(self.effects, **kwargs))

    def test_frozen_gain_identity_and_unchanged_base(self):
        np.testing.assert_array_equal(self.K, self.cfg["frozen_nominal"]["K"])
        self.assertEqual(gain_hash(self.K), "fd1c16dccb418a4949caffcab67fc8e4c4f16d22ec19e7929bbd04acceda5acf")
        self.assertLess(self.nominal_design["frozen_verification"]["max_abs_difference"], 1e-8)
        self.assertEqual(self.base["simulation"]["dt_s"], 0.002)
        self.assertEqual(self.base["protocol"]["version"], "predeclared-v1")
        self.assertEqual(self.cfg["experiment"]["seeds"], list(range(5)))

    def test_timestamp_causality_fractional_delay_and_no_extra_tick(self):
        actions = np.array([[1., -2.], [-.5, 1.], [.25, .75], [0., -.5], [1.5, 3.]])
        for delay in (0.002, 0.003, 0.005):
            with self.subTest(delay=delay):
                r = self.runtime(delay_s=delay, motor_time_constant_s=(0., 0.))
                r.reset(np.zeros(6))
                segments = [s for u in actions for s in r.step(u).intervals]
                for s in segments:
                    eligible = [i for i in range(len(actions)) if i*.002+delay <= s.time_s+1e-12]
                    expected = actions[eligible[-1]] if eligible else np.zeros(2)
                    np.testing.assert_array_equal(s.applied_mean, expected)
                    if eligible:
                        self.assertAlmostEqual(s.source_submitted_s, eligible[-1]*.002, places=12)
                        self.assertGreaterEqual(s.time_s+1e-12, s.source_submitted_s+delay)
                    self.assertLessEqual(s.dt_s, .00025+1e-12)
                first = next(s for s in segments if np.any(s.applied_mean))
                self.assertAlmostEqual(first.time_s, delay, places=12)
                self.assertAlmostEqual(sum(s.dt_s for s in segments), .01, places=12)

    def test_analytical_lag_endpoint_impulse_and_effort(self):
        # Different pair constants and a pure delayed step: independent oracle.
        for delay in (0., .002, .003, .005):
            r = self.runtime(delay_s=delay, motor_time_constant_s=(.005, .008))
            r.reset(np.zeros(6))
            command = np.array([1., -2.])
            impulse, effort = np.zeros(2), np.zeros(2)
            for _ in range(12):
                result = r.step(command)
                impulse += sum((s.applied_mean*s.dt_s for s in result.intervals), np.zeros(2))
                effort += sum((s.torque_squared_integral for s in result.intervals), np.zeros(2))
                t = max(0., r.time-delay)
                T = np.array([.005, .008])
                expected = command*(1-np.exp(-t/T))
                np.testing.assert_allclose(r.torque(), expected, atol=3e-14, rtol=0)
                np.testing.assert_allclose(result.observation.torque_estimate, expected, atol=3e-14, rtol=0)
            np.testing.assert_allclose(impulse, command*(t-T*(1-np.exp(-t/T))), atol=1e-14)
            expected_effort = command**2*(t-2*T*(1-np.exp(-t/T))+T/2*(1-np.exp(-2*t/T)))
            np.testing.assert_allclose(effort, expected_effort, atol=1e-14)

    def test_seeded_cached_noise_statistics_independence_and_no_truth_mutation(self):
        r = self.runtime(delay_s=0, motor_time_constant_s=(0., 0.))
        r.reset(np.zeros(6), seed=123)
        samples = []
        for _ in range(6000):
            truth = r.truth()
            first = r.measurement()
            for _ in range(3):
                np.testing.assert_array_equal(r.measurement(), first)
            first[:] = 999.  # Returned data cannot mutate the cache/physics.
            sample = r.measurement()-truth
            np.testing.assert_array_equal(sample[[0, 1, 3, 4]], 0.)
            np.testing.assert_array_equal(r.truth(), truth)
            samples.append(sample[[2, 5]])
            r.step([0., 0.])
        samples = np.array(samples)
        standard = samples/np.array([np.deg2rad(.1), .01])
        self.assertLess(max(abs(standard.mean(axis=0))), .05)
        np.testing.assert_allclose(standard.std(axis=0), 1., atol=.04)
        self.assertLess(abs(np.corrcoef(standard.T)[0, 1]), .05)
        for i in range(2):
            self.assertLess(abs(np.corrcoef(standard[:-1, i], standard[1:, i])[0, 1]), .05)
        r.reset(np.zeros(6), seed=123)
        for expected in samples[:30]:
            np.testing.assert_array_equal(r.sensor_noise(), expected)
            r.step([0., 0.])
        r.reset(np.zeros(6), seed=124)
        self.assertFalse(np.array_equal(r.sensor_noise(), samples[0]))
        np.testing.assert_array_equal(r.truth(), 0.)

    def test_noise_stream_is_independent_of_substeps_and_controller_actions(self):
        a = self.runtime(delay_s=.002)
        b = self.runtime(delay_s=.005, integration_max_step_s=.00013)
        a.reset(seed=4)
        b.reset(seed=4)
        for i in range(40):
            np.testing.assert_array_equal(a.sensor_noise(), b.sensor_noise())
            a.observation()  # Extra reads cannot consume noise.
            a.step([.1, -.2])
            b.step([-.1, .3])

    def test_all_effects_disabled_reproduce_nominal_bitwise(self):
        r = self.runtime(delay_s=0, motor_time_constant_s=(0., 0.),
                         body_angle_std_deg=0, body_gyro_std_rad_s=0)
        plant = Plant(self.base)
        data = plant.data(self.base["protocol"]["initial_state"])
        rng = np.random.default_rng(2)
        for _ in range(100):
            action = rng.uniform(-8, 8, 2)
            push = rng.uniform(-6, 6)
            result = r.step(action, push)
            plant.forward(data, np.clip(action, -plant.limits, plant.limits), push)
            mujoco.mj_step(plant.model, data)
            np.testing.assert_array_equal(r.truth(), plant.state(data))
            np.testing.assert_array_equal(r.measurement(), r.truth())
            self.assertEqual(r.time, data.time)
            self.assertEqual(len(result.intervals), 1)

    def test_caps_are_physical_and_clipping_precedes_transport(self):
        r = self.runtime(delay_s=.003, motor_time_constant_s=(0., .005))
        r.reset(np.zeros(6))
        for i in range(20):
            raw = np.array([100., -100.]) * (-1)**(i//4)
            result = r.step(raw)
            np.testing.assert_array_equal(result.clipped, np.clip(raw, -r.limits, r.limits))
            np.testing.assert_array_equal(r.command_history()[0].value, result.clipped)
            for s in result.intervals:
                for torque in (s.torque_start, s.torque_end, s.applied_mean, s.delayed_command):
                    self.assertTrue(np.all(abs(torque) <= r.limits+1e-12))
            np.testing.assert_allclose(result.observation.torque_estimate, r.torque(), atol=0., rtol=0.)
        obs = r.observation()
        obs.torque_estimate[:] = 999
        obs.command_history[:] = 999
        self.assertTrue(np.all(abs(r.observation().torque_estimate) <= r.limits))
        self.assertTrue(np.all(abs(r.observation().command_history) <= r.limits))

    def test_reconstructed_torque_does_not_read_physical_torque(self):
        r = self.runtime()
        r.reset(np.zeros(6))
        r._tau[:] = [.5, -.5]  # Fault injection into physical filter, not estimator.
        result = r.step([0., 0.])
        np.testing.assert_array_equal(result.observation.torque_estimate, 0.)
        self.assertGreater(np.linalg.norm(r.torque()), .1)

    def test_exact_pulse_csv_and_nominal_protocol_equivalence(self):
        root = Path(tempfile.mkdtemp(prefix="wbr-augmented-zero-regression-"))
        r = self.runtime(delay_s=0, motor_time_constant_s=(0., 0.),
                         body_angle_std_deg=0, body_gyro_std_rad_s=0)
        for scenario in ("balance", "push", "open_loop"):
            nominal_dir = root/f"nominal_{scenario}"
            nominal_dir.mkdir()
            old, rows = evaluate_nominal(Plant(self.base), self.K, scenario, nominal_dir)
            new = evaluate(r, lambda obs: -self.K@obs.measurement, scenario, 0, root/scenario)
            self.assertEqual(new["status"], old["status"], str(root))
            self.assertEqual(new["recovery_time_after_event_s"], old["recovery_time_after_event_s"])
            np.testing.assert_array_equal(new["final_error"], old["final_error"])
            with (root/scenario/"control.csv").open() as stream:
                data = list(csv.DictReader(stream))
            states = [[float(row[n]) for n in self.base["controller"]["state_order"]] for row in data]
            np.testing.assert_array_equal(states, rows[:, 1:7])
        with (root/"push"/"intervals.csv").open() as stream:
            segments = list(csv.DictReader(stream))
        impulse = sum(float(s["push_N"])*float(s["interval_dt_s"]) for s in segments)
        self.assertAlmostEqual(impulse, .9, places=10)
        self.assertAlmostEqual(sum(float(s["interval_dt_s"]) for s in segments), 10., places=10)

    def test_mechanical_substep_refinement_converges(self):
        finals = []
        for h in (.00025, .000125, .0000625, .00003125):
            r = self.runtime(delay_s=.003, integration_max_step_s=h)
            for i in range(30):
                r.step([.2*(-1)**(i//5), -.1], push_N=6. if 10 <= i < 15 else 0.)
            finals.append(r.truth())
        errors = [np.linalg.norm(x-finals[-1]) for x in finals[:-1]]
        self.assertLess(errors[1], .3*errors[0], errors)
        self.assertLess(errors[2], .3*errors[1], errors)
        self.assertLess(errors[0], 3e-5, errors)

    def test_linearization_map_replays_live_history_at_integer_and_fractional_delays(self):
        rng = np.random.default_rng(42)
        for delay in (.002, .003, .004, .005):
            live, restored = self.runtime(delay_s=delay), self.runtime(delay_s=delay)
            live.reset(np.zeros(6))
            for _ in range(5):
                live.step(rng.normal(size=2)*.001)
            z, u = live.evaluation_state(), rng.normal(size=2)*.001
            live.step(u)
            replay = restored.transition_for_linearization(z, u)
            np.testing.assert_allclose(replay, live.evaluation_state(), rtol=1e-11, atol=1e-13)

    def test_augmented_dare_residual_poles_and_actual_step_prediction(self):
        rng = np.random.default_rng(7)
        for delay in (.002, .003, .004, .005):
            effects = replace(self.effects, delay_s=delay)
            K, design = synthesize_augmented(self.base, effects, self.K)
            r = AugmentedRuntime(self.base, effects)
            A, B = np.array(design["A_discrete_actual"]), np.array(design["B_discrete_actual"])
            self.assertLess(design["DARE_relative_residual"], 1e-8)
            self.assertLess(design["max_closed_loop_pole_magnitude"], 1)
            self.assertEqual(design["controllability"]["rank"], r.state_size)
            self.assertEqual(gain_hash(K), design["K_sha256"])
            np.testing.assert_array_equal(np.diag(design["Q_discrete"])[:6],
                                          .002*np.array(self.base["controller"]["Q_diagonal"]))
            np.testing.assert_array_equal(np.diag(design["Q_discrete"])[6:], 0.)
            Ah, Bh = linearize(r, 1e-5)
            np.testing.assert_allclose(Ah, A, atol=1e-9, rtol=1e-8)
            np.testing.assert_allclose(Bh, B, atol=1e-9, rtol=1e-8)
            for _ in range(3):
                z, u = rng.normal(size=r.state_size)*1e-5, rng.normal(size=2)*1e-5
                actual = r.transition_for_linearization(z, u)
                np.testing.assert_allclose(actual, A@z+B@u, atol=1e-12, rtol=1e-6)

    def test_full_augmented_protocol_failure_retained_then_conditional_recovery(self):
        root = Path(tempfile.mkdtemp(prefix="wbr-augmented-integration-"))
        fixed = evaluate(self.runtime(delay_s=.002), lambda obs: -self.K@obs.measurement,
                         "balance", 0, root/"fixed")
        self.assertEqual(fixed["status"], "FAIL", str(root))
        self.assertIn("held_final_window", fixed["failed_checks"])
        effects = replace(self.effects, delay_s=.005)
        K, _ = synthesize_augmented(self.base, effects, self.K)
        for scenario in ("balance", "push", "open_loop"):
            result = evaluate(AugmentedRuntime(self.base, effects), lambda obs: -K@obs.vector(),
                              scenario, 0, root/scenario)
            self.assertEqual(result["status"], "PASS", f"{result}; retained {root}")
            self.assertTrue(result["caps_respected"])
        with (root/"push"/"intervals.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertAlmostEqual(sum(float(r["push_N"])*float(r["interval_dt_s"]) for r in rows),
                               .9, places=10)
        with (root/"fixed"/"control.csv").open() as f, (root/"balance"/"control.csv").open() as a:
            for fixed_row, augmented_row in zip(csv.DictReader(f), csv.DictReader(a)):
                self.assertEqual(fixed_row["body_angle_noise_rad"], augmented_row["body_angle_noise_rad"])
                self.assertEqual(fixed_row["body_gyro_noise_rad_s"], augmented_row["body_gyro_noise_rad_s"])
        self.assertTrue((root/"fixed"/"metrics.json").is_file())

    def test_invalid_runtime_settings_and_actions_are_rejected(self):
        for kwargs in ({"delay_s": -.001}, {"motor_time_constant_s": (.005, -1)},
                       {"body_angle_std_deg": float("nan")}, {"integration_max_step_s": 0}):
            with self.assertRaises(ValueError):
                RuntimeConfig(**kwargs)
        r = self.runtime()
        for action in ([1.], [float("nan"), 0.], [0., float("inf")]):
            with self.assertRaises(ValueError):
                r.step(action)


if __name__ == "__main__":
    unittest.main()
