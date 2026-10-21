import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from sim.fivebar.compare import FixedLength
from sim.fivebar.linearize import (
    EquilibriumError, closed_loop, compare_length, equilibrium,
    linearize, main, mechanics, zoh,
)
from sim.fivebar.model import Plant
from sim.gain_schedule.model import config_at_length
from sim.lqr import synthesize
from sim.planar import Plant as ReducedPlant, load_config


class NumericalTests(unittest.TestCase):
    def test_known_linear_plant_and_independent_state_input_epsilons(self):
        A = np.arange(36).reshape(6, 6) / 13.
        B = np.arange(12).reshape(6, 2) / 7.
        actual_A, actual_B = linearize(lambda x, u: A @ x + B @ u, 1e-5, 3e-7)
        np.testing.assert_allclose(actual_A, A, atol=1e-14)
        np.testing.assert_allclose(actual_B, B, atol=1e-14)

    def test_affine_drift_is_rejected_without_hidden_bias_subtraction(self):
        def drift(x, u):
            return x + np.array([0., 0., 0., .01, 0., 0.])

        self.assertFalse(equilibrium(drift)['valid'])
        with self.assertRaises(EquilibriumError):
            linearize(drift, 1e-5, 1e-5)

    def test_nonfinite_or_wrong_shape_derivative_is_rejected(self):
        residual = equilibrium(lambda x, u: np.full(6, np.nan))
        self.assertFalse(residual['valid'])
        json.dumps(residual, allow_nan=False)
        with self.assertRaises(EquilibriumError):
            linearize(lambda x, u: np.full(6, np.nan), 1e-5, 1e-5)
        with self.assertRaises(ValueError):
            linearize(lambda x, u: np.zeros(3), 1e-5, 1e-5)

    def test_invalid_epsilon_and_dt_are_rejected(self):
        for value in (0., -1., float('nan'), float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                linearize(lambda x, u: x, value, 1e-5)
            with self.subTest(value=value), self.assertRaises(ValueError):
                zoh(np.zeros((2, 2)), np.zeros((2, 1)), value)

    def test_zoh_double_integrator_retains_half_dt_squared_position_response(self):
        dt = .002
        A, B = zoh([[0., 1.], [0., 0.]], [[0.], [1.]], dt)
        np.testing.assert_allclose(A, [[1., dt], [0., 1.]], atol=1e-16)
        np.testing.assert_allclose(B, [[dt**2 / 2], [dt]], atol=1e-16)

    def test_zoh_scalar_decay_and_constant_input(self):
        A, B = zoh([[-2.]], [[3.]], .1)
        np.testing.assert_allclose(A, [[math.exp(-.2)]], atol=1e-16)
        np.testing.assert_allclose(B, [[1.5 * (1 - math.exp(-.2))]], atol=1e-16)
        with self.assertRaises(ValueError):
            zoh(np.eye(2), np.ones((3, 1)), .1)

    def test_feedback_sign_poles_margin_and_decay_time(self):
        A = np.diag([1.1, 1.05, .7, .6, .5, .4])
        B = np.eye(6, 2)
        K = np.zeros((2, 6))
        K[0, 0], K[1, 1] = .2, .25
        result = closed_loop(A, B, K, .002)
        self.assertTrue(result['stable'])
        np.testing.assert_allclose(np.diag(result['matrix']), [.9, .8, .7, .6, .5, .4])
        self.assertAlmostEqual(result['margin_to_unit_circle'], .1)
        self.assertAlmostEqual(result['dominant_decay_tau_s'], -.002 / math.log(.9))
        unstable = closed_loop(A, B, -K, .002)
        self.assertFalse(unstable['stable'])
        self.assertIsNone(unstable['dominant_decay_tau_s'])

    def test_controller_transposition_or_nonfinite_data_is_rejected(self):
        for K in (np.zeros((6, 2)), np.zeros((2, 5)), np.full((2, 6), np.nan)):
            with self.subTest(shape=K.shape), self.assertRaises(ValueError):
                closed_loop(np.eye(6), np.eye(6, 2), K, .002)

    def test_unit_change_preserves_poles_when_controller_is_transformed(self):
        A = np.diag([1.1, 1.05, .7, .6, .5, .4])
        B = np.eye(6, 2)
        K = np.array([[.2, .02, 0., 0., 0., 0.], [.01, .25, 0., 0., 0., 0.]])
        S = np.diag([1000., 180 / math.pi, 180 / math.pi, 1000., 180 / math.pi, 180 / math.pi])
        original = closed_loop(A, B, K, .002)
        scaled = closed_loop(S @ A @ np.linalg.inv(S), S @ B, K @ np.linalg.inv(S), .002)
        np.testing.assert_allclose(original['poles_real_imag'], scaled['poles_real_imag'], atol=1e-14)


class PlantComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config(Path(__file__).resolve().parents[2] / 'configs/assumed_planar.json')
        cls.reduced = ReducedPlant(cls.cfg)
        cls.fixed = FixedLength(Plant(cls.cfg))
        cls.result = compare_length(cls.cfg, .16, [1e-5, 1e-6], [1e-5, 1e-6], [1e-5, 1e-6])

    def test_mass_and_map_explain_actual_acceleration_jacobians(self):
        result = mechanics(self.reduced, self.fixed)
        for name, plant in (('reduced', self.reduced), ('fivebar', self.fixed)):
            A, B = linearize(plant.derivative, 1e-5, 1e-6)
            np.testing.assert_allclose(A[:3, :3], 0., atol=1e-12)
            np.testing.assert_allclose(A[:3, 3:], np.eye(3), atol=1e-12)
            np.testing.assert_allclose(B[:3], 0., atol=1e-12)
            M, G = np.asarray(result[name + '_mass']), np.asarray(result[name + '_generalized_input_map'])
            np.testing.assert_allclose(B[3:], np.linalg.solve(M, G), atol=1e-7)
            self.assertTrue(np.all(np.linalg.eigvalsh(M) > 0))
            np.testing.assert_allclose(G[:, 1], [0., -1., 1.], atol=1e-8)
            self.assertAlmostEqual(G[0, 0], 1 / self.cfg['physics']['wheel_radius']['value'], places=8)
        effect = np.array(result['mass_effect_at_reduced_map']) + result['map_effect_at_fivebar_mass']
        np.testing.assert_allclose(effect, np.array(result['fivebar_acceleration_input_jacobian']) -
                                   result['reduced_acceleration_input_jacobian'], atol=1e-12)

    def test_real_comparison_retains_existing_dare_and_actual_step(self):
        result = self.result
        self.assertEqual(result['status'], 'valid_local_linearization')
        K, design = synthesize(self.reduced)
        np.testing.assert_allclose(result['reduced_synthesis']['K_used'], K, atol=1e-12)
        np.testing.assert_allclose(result['reduced_synthesis']['A_discrete_actual'], design['A_discrete_actual'], atol=1e-12)
        for item in result['closed_loop'].values():
            self.assertEqual(len(item['poles_real_imag']), 6)
            self.assertTrue(item['stable'])
        self.assertEqual(len(result['refinements']), 4)
        self.assertEqual(result['selected_refinement'], 3)

    def test_existing_length_transform_does_not_mutate_reference_or_match_link_inertia(self):
        before = json.dumps(self.cfg, sort_keys=True)
        scaled = config_at_length(self.cfg, .20)
        self.assertEqual(before, json.dumps(self.cfg, sort_keys=True))
        self.assertEqual(scaled['controller'], self.cfg['controller'])
        self.assertEqual(scaled['source_geometry_inventory_unused'], self.cfg['source_geometry_inventory_unused'])
        self.assertAlmostEqual(scaled['physics']['leg_com']['value'], .1)
        self.assertAlmostEqual(scaled['physics']['leg_inertia']['value'], .0012 * 1.25**2)

    def test_unreachable_and_straight_chain_rejections_are_preserved(self):
        maximum_length = math.sqrt((.075 + .14)**2 - (.08 / 2)**2)
        for length in (.22, maximum_length):
            with self.subTest(length=length):
                result = compare_length(self.cfg, length, [1e-6], [1e-5], [1e-5])
                self.assertEqual(result['status'], 'rejected_geometry')
                self.assertIn('Unreachable or straight/folded', result['error'])
                self.assertNotIn('closed_loop', result)

    def test_nonequilibrium_does_not_get_a_stability_claim(self):
        with patch.object(FixedLength, 'derivative', return_value=np.array([0., 0., 0., .01, 0., 0.])):
            result = compare_length(self.cfg, .16, [1e-6], [1e-5], [1e-5])
        self.assertEqual(result['status'], 'invalid_equilibrium')
        self.assertFalse(result['equilibrium']['fivebar'][0]['valid'])
        self.assertNotIn('closed_loop', result)
        self.assertEqual(result['refinements'], [])

    def test_invalid_refinement_pairs_are_rejected(self):
        with self.assertRaises(ValueError):
            compare_length(self.cfg, .16, [1e-6], [1e-5, 1e-6], [1e-5])

    def test_existing_output_is_preserved(self):
        directory = Path(__file__).resolve().parent
        with patch('sys.argv', ['linearize', '--out', str(directory)]), \
                patch.object(Path, 'mkdir') as mkdir, \
                self.assertRaises(SystemExit) as caught:
            main()
        self.assertEqual(caught.exception.code, 2)
        mkdir.assert_not_called()


if __name__ == '__main__':
    unittest.main()
