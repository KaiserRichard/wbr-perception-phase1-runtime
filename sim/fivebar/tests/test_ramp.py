import math
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from sim.fivebar.compare import FixedLength
from sim.fivebar.model import Plant
from sim.fivebar.ramp import (
    Controller, PrescribedLength, Sensor, full_duration_reached, length_profile,
    mechanical_step,
)
from sim.planar import load_config


class RampMechanicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[2] / 'configs/assumed_planar.json'
        cls.cfg = load_config(path)

    def test_profile_endpoints_derivatives_and_peak_speed(self):
        for time, expected in ((0., (.12, 0., 0.)), (2., (.12, 0., 0.)),
                               (10., (.20, 0., 0.)), (15., (.20, 0., 0.))):
            np.testing.assert_allclose(length_profile(time), expected, atol=1e-15)
        samples = [length_profile(t) for t in np.linspace(2., 10., 1001)]
        self.assertAlmostEqual(max(v[1] for v in samples), .01875, places=9)
        self.assertAlmostEqual(length_profile(2.000001)[1], 0., places=10)
        self.assertAlmostEqual(length_profile(9.999999)[1], 0., places=10)
        for time in (-1., math.nan, math.inf):
            with self.subTest(time=time), self.assertRaises(ValueError):
                length_profile(time)

    def test_duration_acceptance_converts_numpy_scalar_to_json_safe_bool(self):
        result = full_duration_reached(np.float64(15.))
        self.assertIs(result, True)
        self.assertIsInstance(result, bool)
        self.assertIs(full_duration_reached(np.float64(14.999)), False)

    def test_constant_length_matches_existing_fixed_length_derivative(self):
        state = np.array([.003, .075, -.045, .012, -.08, .06])
        control = np.array([.16, -.22])
        plant = Plant(self.cfg)
        prescribed = PrescribedLength(plant, profile=lambda _: (.16, 0., 0.))
        fixed = FixedLength(plant)
        actual = prescribed.derivative(.7, state, control)
        expected = fixed.derivative(state, control)
        np.testing.assert_allclose(actual, expected, rtol=2e-9, atol=2e-9)

    def test_ideal_extension_reaction_balances_full_four_coordinate_equations(self):
        state = np.array([.001, .06, -.035, .01, -.04, .025])
        control = np.array([.12, -.18])
        prescribed = PrescribedLength(
            Plant(self.cfg), profile=lambda _: (.16, .013, -.021))
        derivative, extension, closure, _ = prescribed.evaluate(.4, state, control)
        m4, b4, force4, lddot = prescribed.terms(.4, state, control)
        qdd = derivative[3:]
        np.testing.assert_allclose(m4[:3, :3] @ qdd + m4[:3, 3]*lddot + b4[:3],
                                   force4[:3], atol=1e-10)
        np.testing.assert_allclose(m4[3, :3] @ qdd + m4[3, 3]*lddot + b4[3],
                                   force4[3] + extension, atol=1e-10)
        self.assertTrue(math.isfinite(extension))
        self.assertLess(closure, 1e-7)

    def test_one_control_interval_closes_and_refines_with_half_substep(self):
        state = np.array([0., .04, -.025, 0., 0., 0.])
        profile = lambda _: (.16, 0., 0.)
        mechanics = PrescribedLength(Plant(self.cfg), profile=profile)
        coarse, coarse_metrics = mechanical_step(mechanics, .3, state, np.zeros(2), .001)
        fine_mid, first_metrics = mechanical_step(mechanics, .3, state, np.zeros(2), .0005)
        fine, second_metrics = mechanical_step(mechanics, .3005, fine_mid, np.zeros(2), .0005)
        np.testing.assert_allclose(fine, coarse, rtol=2e-5, atol=2e-8)
        self.assertLess(max(coarse_metrics['closure_max_m'], first_metrics['closure_max_m'],
                            second_metrics['closure_max_m']), 1e-7)
        self.assertEqual(coarse_metrics['extension_work_J'], 0.)


class CausalInputTests(unittest.TestCase):
    def test_sensor_caches_noise_once_per_tick_and_returns_copies(self):
        sensor = Sensor(seed=0)
        truth = np.arange(6, dtype=float)
        first = sensor.measure(0, truth)
        first_copy = sensor.measure(0, truth + 100)
        np.testing.assert_array_equal(first_copy, first)
        first_copy[0] = -100
        np.testing.assert_array_equal(sensor.measure(0, truth), first)
        next_tick = sensor.measure(1, truth)
        np.testing.assert_array_equal(next_tick[[0, 1, 3, 4]], truth[[0, 1, 3, 4]])

    def test_controller_uses_only_supplied_measurement_and_prior_clipped_commands(self):
        fit = {'fixture': True}
        controller = Controller(fit)
        gain = np.zeros((2, 10))
        gain[0, 0], gain[1, 1] = 1., 1.
        with patch('sim.fivebar.ramp.evaluate_polynomial', return_value=gain):
            measured = np.array([5., -9., .1, 0., 0., 0.])
            observation, raw, clipped = controller.tick(measured, .16)
            np.testing.assert_array_equal(observation[:6], measured)
            np.testing.assert_array_equal(raw, [ -5., 9.])
            np.testing.assert_array_equal(clipped, [-2., 4.])
            next_observation, _, _ = controller.tick(np.zeros(6), .17)
        # Command selection sees only measured state plus the observer's own
        # prior command history; no plant state or applied torque is accepted.
        np.testing.assert_array_equal(next_observation[8:], [-2., 4.])
        self.assertEqual(controller.fit, fit)


if __name__ == '__main__':
    unittest.main()
