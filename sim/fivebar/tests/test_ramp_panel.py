"""Targeted profile, virtual-work and moving-length numerical checks."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from sim.fivebar import ramp_panel as panel
from sim.fivebar.model import Plant
from sim.fivebar.ramp import PrescribedLength, mechanical_step
from sim.planar import load_config


class PanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config(Path(__file__).resolve().parents[2]/'configs/assumed_planar.json')

    def test_all_profiles_c2_reverse_and_analytic_rate(self):
        self.assertEqual(len(panel.matrix()), 12)
        for duration in (8., 2., 1.):
            forward, reverse = panel.Profile(.12, .20, duration), panel.Profile(.20, .12, duration)
            self.assertEqual(forward(2.), (.12, 0., 0.))
            self.assertEqual(forward(2.+duration), (.20, 0., 0.))
            self.assertAlmostEqual(forward(2.+duration/2)[1], .08*1.875/duration)
            self.assertAlmostEqual(forward.max_abs_rate_m_s, .08*1.875/duration)
            for s in (.1, .37, .7, .95):
                t, h = 2.+duration*s, 1e-5
                value = forward(t)
                back = reverse(t)
                np.testing.assert_allclose(np.array(value)+back, [.32, 0., 0.], atol=1e-14)
                self.assertAlmostEqual((forward(t+h)[0]-forward(t-h)[0])/(2*h), value[1], places=8)
                self.assertAlmostEqual((forward(t+h)[1]-forward(t-h)[1])/(2*h), value[2], places=8)

    def test_extension_joint_torque_virtual_work_and_unchanged_dynamics(self):
        plant = Plant(self.cfg)
        state = np.array([.002, .07, -.05, .03, -.06, .04])
        torque = np.array([.4, -.7])
        profile = panel.Profile(.12, .20, 1.)
        base = PrescribedLength(plant, profile=profile)
        diagnostic = panel.RequiredTorque(plant, profile=profile)
        t = 2.35
        a, b = base.evaluate(t, state, torque), diagnostic.evaluate(t, state, torque)
        np.testing.assert_array_equal(a[0], b[0])
        self.assertEqual(a[1], b[1])
        q4 = np.r_[state[:3], profile(t)[0]]
        velocity4 = np.r_[state[3:], profile(t)[1]]
        tree_velocity = plant.tangent(q4) @ velocity4
        motor_velocity = tree_velocity[[plant.joints['motor_A'], plant.joints['motor_E']]]
        extension_power = (b[3]-a[3])[1:] @ motor_velocity
        self.assertAlmostEqual(extension_power, a[1]*velocity4[3], places=8)
        self.assertAlmostEqual(a[3][1:] @ motor_velocity, torque[1]*(state[5]-state[4]), places=9)
        record = diagnostic.peaks[0]
        np.testing.assert_allclose(np.array(record['balance_only_A_E_Nm'])+record['extension_only_A_E_Nm'],
                                   record['required_A_E_Nm'], atol=1e-15)
        self.assertEqual(record['time_s'], t)

    def test_required_peaks_keep_same_stage_loads(self):
        mechanics = panel.RequiredTorque(Plant(self.cfg), profile=panel.Profile(.12, .20, 1.))
        state = np.array([.002, .07, -.05, .03, -.06, .04])
        mechanical_step(mechanics, 2.35, state, np.array([.4, -.7]), .001)
        for record in [*mechanics.peaks, mechanics.pair_peak]:
            self.assertIn(record['time_s'], (2.35, 2.3505, 2.351))
            expected = mechanics.plant.controls(record['q4'], *record['balance_Tw_Th_Nm'],
                                                 extension_N=record['extension_N'])[1:]
            np.testing.assert_array_equal(expected, record['required_A_E_Nm'])

    def test_endpoint_windows_include_boundaries_and_preserve_incomplete_stop(self):
        times = np.array([0., 2., 2.5, 3.])
        states = np.zeros((4, 6))
        states[:, 0] = [.02, .01, -.03, .005]
        states[:, 1] = np.deg2rad([9., 1., 2., 3.])
        states[:, 2] = np.deg2rad([8., 4., 5., 6.])
        m = panel.window_metrics(times, states, 2., 3.)
        self.assertEqual(m['samples'], 3)
        self.assertTrue(m['complete'])
        self.assertAlmostEqual(m['leg_peak_abs_deg'], 3.)
        self.assertAlmostEqual(m['body_peak_abs_deg'], 6.)
        self.assertAlmostEqual(m['x_end_minus_start_m'], -.005)
        self.assertAlmostEqual(m['x_change_from_window_start_peak_abs_m'], .04)
        self.assertFalse(panel.window_metrics(times, states, 2., 4.)['complete'])
        self.assertEqual(panel.window_metrics(times, states, 4., 9.)['samples'], 0)

    def test_fast_moving_nonzero_torque_refinement(self):
        result = panel.refinement({'reference_config': self.cfg})
        coarse, half, finest, projection = result['variants']
        self.assertLess(max(half['state_abs_difference_from_finest']),
                        max(coarse['state_abs_difference_from_finest']))
        self.assertLess(max(coarse['state_abs_difference_from_finest']), 1e-4)
        self.assertLess(max(abs(projection['final_state']-coarse['final_state'])), 1e-7)
        self.assertLess(abs(coarse['reaction_difference_from_finest_N']), 1e-3)
        for row in result['variants']:
            np.testing.assert_allclose(row['final_torque_Nm'], finest['final_torque_Nm'], atol=2e-15)
        path = Path(tempfile.mkdtemp(dir=os.environ.get('WBR_TEST_OUT')))/'refinement.json'
        panel.write_json(path, result)
        print('Retained targeted refinement:', path)


if __name__ == '__main__':
    unittest.main()
