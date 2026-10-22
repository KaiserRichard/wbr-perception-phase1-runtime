"""Analytical delay fixtures and one bounded local runtime refinement check."""

from dataclasses import replace
import math
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from sim.augmented import AugmentedRuntime, RuntimeConfig
from sim.augmented_lqr import linearize as runtime_linearize, synthesize_augmented
from sim.fivebar.delayed_linear import exact_lift, main, spectrum
from sim.fivebar.linearize import linearize
from sim.planar import Plant, load_config


class ExactTransportTests(unittest.TestCase):
    def test_fractional_integrator_lag_matches_closed_form_impulse(self):
        # xdot=tau, T*tau_dot=command-tau. Independent integral formula,
        # using explicit expected command sequences, not the lift's schedule.
        tau0, x0, T = -.3, .7, .005
        history = [1.7, -.8, 2.4]
        sequences = {
            .002: [(history[0], .002)],
            .003: [(history[1], .001), (history[0], .001)],
            .004: [(history[1], .002)],
            .005: [(history[2], .001), (history[1], .001)],
        }
        for delay, sequence in sequences.items():
            with self.subTest(delay=delay):
                A, B, _ = exact_lift([[0]], [[1]], .002, delay, T)
                expected_x, expected_tau = x0, tau0
                for command, duration in sequence:
                    decay = math.exp(-duration / T)
                    expected_x += command * duration + (expected_tau - command) * T * (1 - decay)
                    expected_tau = command + (expected_tau - command) * decay
                z = np.r_[x0, tau0, history[:len(A)-2]]
                result = A @ z + B @ np.array([30.])
                np.testing.assert_allclose(result[:2], [expected_x, expected_tau], rtol=1e-13, atol=1e-14)
                np.testing.assert_array_equal(result[2:], [30., *history[:len(A)-3]])

    def test_full_continuous_coupling_not_one_mean_torque_step(self):
        # xdot=a*x+tau, tau(t)=u+(tau0-u)*exp(-t/T).
        # This scalar solution explicitly weights varying torque by exp(a*t).
        a, T, dt, x, tau, u = 17., .005, .002, .13, -.3, 1.7
        A, B, _ = exact_lift([[a]], [[1]], dt, dt, T)
        result = A @ [x, tau, u] + B @ [-99.]
        ea, et = math.exp(a * dt), math.exp(-dt / T)
        exact_x = ea*x + u*(ea-1)/a + (tau-u)*(ea-et)/(a+1/T)
        exact_tau = u+(tau-u)*et
        np.testing.assert_allclose(result[:2], [exact_x, exact_tau], rtol=2e-14)
        mean = u+(tau-u)*T/dt*(1-et)
        mean_held_x = ea*x + mean*(ea-1)/a
        self.assertGreater(abs(result[0] - mean_held_x), 1e-6)

    def test_arrival_at_tick_end_has_no_current_input_effect(self):
        for delay, n in ((.002, 10), (.003, 12), (.004, 12), (.005, 14)):
            with self.subTest(delay=delay):
                A, B, meta = exact_lift(np.zeros((6, 6)), np.ones((6, 2)), .002, delay, .005)
                self.assertEqual(A.shape, (n, n))
                self.assertEqual(B.shape, (n, 2))
                self.assertEqual(meta['state_dimension'], n)
                np.testing.assert_array_equal(B[:8], 0.)
                np.testing.assert_array_equal(B[8:10], np.eye(2))
                np.testing.assert_array_equal(B[10:], 0.)
                state = np.arange(n, dtype=float)
                nxt = A @ state + B @ [21., 22.]
                np.testing.assert_array_equal(nxt[8:], np.r_[21., 22., state[8:-2]])

    def test_integer_transport_pulse_cannot_act_before_arrival(self):
        A, B, _ = exact_lift([[0]], [[1]], .002, .004, .005)
        z = np.zeros(len(A))
        z = A @ z + B[:, 0]
        np.testing.assert_array_equal(z[:2], [0., 0.])
        z = A @ z
        np.testing.assert_array_equal(z[:2], [0., 0.])
        z = A @ z
        self.assertGreater(z[0], 0.)
        self.assertAlmostEqual(z[1], 1-math.exp(-.002/.005), places=14)

    def test_zero_equilibrium_and_two_independent_channels(self):
        for delay in (.002, .003, .004, .005):
            A, B, _ = exact_lift(np.zeros((2, 2)), np.eye(2), .002, delay, .005)
            np.testing.assert_array_equal(A @ np.zeros(len(A)) + B @ np.zeros(2), 0.)
            z = np.zeros(len(A))
            z[2::2] = 1.  # Only first torque/history channel.
            np.testing.assert_array_equal((A @ z)[1::2], 0.)

    def test_invalid_settings_and_shapes_rejected(self):
        for delay, lag in ((.001, .005), (float('nan'), .005), (.003, 0.), (.003, -1.)):
            with self.subTest(delay=delay, lag=lag), self.assertRaises(ValueError):
                exact_lift([[0]], [[1]], .002, delay, lag)
        for A, B in (([[float('inf')]], [[1]]), ([[0, 1]], [[1]]), ([[0]], [[1], [2]])):
            with self.assertRaises(ValueError):
                exact_lift(A, B, .002, .003, .005)


class SpectrumTests(unittest.TestCase):
    def test_negative_feedback_and_unstable_results_preserved(self):
        good = spectrum([[1.1]], [[.3]], [[1]], .002)
        bad = spectrum([[1.1]], [[.3]], [[-1]], .002)
        self.assertAlmostEqual(good['rho'], .8)
        self.assertAlmostEqual(good['margin_to_unit_circle'], .2)
        self.assertAlmostEqual(good['dominant_decay_tau_s'], -.002/math.log(.8))
        self.assertEqual(good['status'], 'STABLE')
        self.assertEqual(bad['status'], 'UNSTABLE')
        self.assertAlmostEqual(bad['rho'], 1.4)
        self.assertIsNone(bad['dominant_decay_tau_s'])
        self.assertFalse(spectrum([[1]], [[0]], [[0]], .002)['stable'])

    def test_saved_eigenpairs_reconstruct_complex_modes(self):
        matrix = np.array([[.8, -.3], [.3, .8]])
        result = spectrum(matrix, np.zeros((2, 1)), np.zeros((1, 2)), .002)
        poles = np.asarray(result['poles_real_imag']) @ np.array([1., 1j])
        vectors = np.asarray(result['right_eigenvectors_real']) + 1j*np.asarray(result['right_eigenvectors_imag'])
        np.testing.assert_allclose(matrix @ vectors, vectors * poles, atol=1e-14)
        np.testing.assert_allclose(np.linalg.norm(vectors, axis=0), 1., atol=1e-14)


class ReducedRuntimeTests(unittest.TestCase):
    def test_actual_runtime_refinement_and_fresh_dare_cost(self):
        cfg = load_config(Path(__file__).resolve().parents[2] / 'configs/assumed_planar.json')
        plant = Plant(cfg)
        ac, bc = linearize(plant.derivative, 1e-6, 1e-6)
        exact_a, exact_b, _ = exact_lift(ac, bc, .002, .003, .005)
        rc = RuntimeConfig(delay_s=.003, body_angle_std_deg=0., body_gyro_std_rad_s=0.)
        # The nominal gain argument only records a comparator; does not enter DARE.
        K, design = synthesize_augmented(cfg, rc, np.zeros((2, 6)))
        actual_a, actual_b = np.array(design['A_discrete_actual']), np.array(design['B_discrete_actual'])
        fine = AugmentedRuntime(cfg, replace(rc, integration_max_step_s=.000125))
        fine_a, fine_b = runtime_linearize(fine, 1e-6)
        coarse_error, fine_error = np.linalg.norm(actual_a-exact_a), np.linalg.norm(fine_a-exact_a)
        print(f'Local runtime refinement L=.16 delay=3ms: A error {coarse_error:.9g} -> {fine_error:.9g}', flush=True)
        self.assertGreater(coarse_error, 0.)
        self.assertLess(fine_error, coarse_error)  # Observed convergence, no equivalence tolerance.
        np.testing.assert_array_equal(actual_b, exact_b)
        np.testing.assert_array_equal(fine_b, exact_b)
        np.testing.assert_array_equal(np.diag(design['Q_discrete']), np.r_[.002*np.array(cfg['controller']['Q_diagonal']), np.zeros(6)])
        np.testing.assert_array_equal(np.diag(design['R_discrete']), .002*np.array(cfg['controller']['R_diagonal']))
        self.assertEqual(K.shape, (2, 12))
        self.assertEqual(design['state_order'][-4:], ['previous_1_wheel_command_Nm', 'previous_1_hip_command_Nm',
                                                   'previous_2_wheel_command_Nm', 'previous_2_hip_command_Nm'])
        self.assertTrue(spectrum(exact_a, exact_b, K, .002)['stable'])
        # Independently execute a tiny one-tick state, checking the derivative's
        # prediction against the actual runtime, not against the exact lift.
        runtime = AugmentedRuntime(cfg, rc)
        z = np.linspace(-1e-7, 1e-7, 12)
        u = np.array([2e-7, -3e-7])
        predicted = actual_a @ z + actual_b @ u
        np.testing.assert_allclose(runtime.transition_for_linearization(z, u), predicted, rtol=1e-8, atol=1e-14)


class OutputTests(unittest.TestCase):
    def test_existing_output_is_preserved_without_running(self):
        with patch('sys.argv', ['delayed_linear', '--out', str(Path(__file__).parent)]), \
                patch('sim.fivebar.delayed_linear.compare_length') as compare, \
                self.assertRaises(SystemExit) as error:
            main()
        self.assertEqual(error.exception.code, 2)
        compare.assert_not_called()

    def test_production_waits_for_conductor_marker(self):
        with patch('sys.argv', ['delayed_linear', '--out', '/unused-fixture-output']), \
                patch.object(Path, 'exists', return_value=False), \
                patch.object(Path, 'is_file', return_value=False), \
                patch('sim.fivebar.delayed_linear.compare_length') as compare, \
                self.assertRaises(SystemExit) as error:
            main()
        self.assertEqual(error.exception.code, 2)
        compare.assert_not_called()


if __name__ == '__main__':
    unittest.main()
