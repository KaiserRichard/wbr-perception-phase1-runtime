import json
from pathlib import Path
import unittest

import mujoco
import numpy as np

from sim.fivebar.model import Plant
from sim.planar import Plant as ReducedPlant


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((Path(__file__).resolve().parents[2]/'configs/assumed_planar.json').read_text())
        cls.plant = Plant(cls.cfg)
        cls.reduced = ReducedPlant(cls.cfg)

    def test_xml_compiles_with_separate_joint_actuation(self):
        m = self.plant.model
        self.assertEqual((m.nq, m.nv, m.nu, m.neq), (8, 8, 3, 2))
        self.assertEqual(m.actuator_trnid[1, 0], m.joint('motor_A').id)
        self.assertEqual(m.actuator_trnid[2, 0], m.joint('motor_E').id)
        self.assertEqual(np.sum(m.geom_contype), 0)
        d = self.plant.data()
        self.assertLess(self.plant.closure_error(d), 1e-12)
        # Six connect rows include two redundant y rows; four independent rows.
        self.assertEqual(np.linalg.matrix_rank(d.efc_J.reshape(-1, m.nv), tol=1e-8), 4)

    def test_nonzero_configurations_close_and_match_reduced_hip_position(self):
        length = self.cfg['physics']['leg_length']['value']
        for x, theta, phi in ((0., 0., 0.), (.2, .08, -.05), (-.1, -.12, .06)):
            q = np.array([x, theta, phi, length])
            d = self.plant.data(q)
            r = self.reduced.data([x, theta, phi, 0., 0., 0.])
            self.assertLess(self.plant.closure_error(d), 1e-12)
            np.testing.assert_allclose(self.plant.virtual(d), q, atol=2e-14)
            np.testing.assert_allclose(d.xpos[self.plant.model.body('chassis').id],
                                       r.xpos[self.reduced.body_id], atol=2e-14)

    def test_fixed_length_hip_power_and_actuator_reactions(self):
        q = np.array([.1, .08, -.05, .16])
        velocity = np.array([.2, -.4, .3, 0.])
        hip = .7
        d = self.plant.data(q, velocity)
        d.ctrl[:] = self.plant.controls(q, 0., hip, extension_N=23.)
        mujoco.mj_forward(self.plant.model, d)
        tangent = self.plant.tangent(q)
        generalized = tangent.T @ d.qfrc_actuator
        np.testing.assert_allclose(generalized, [0., -hip, hip, 23.], atol=3e-8)
        self.assertAlmostEqual(d.qfrc_actuator@d.qvel, hip*(velocity[2]-velocity[1]), places=8)
        # A direct hinge motor applies equal and opposite moments to link and
        # chassis: rigid common rotation does no motor work (q1,q4 fixed).
        m = self.plant.model
        self.assertAlmostEqual(d.qfrc_actuator[m.joint('body_pitch').dofadr[0]], 0., places=12)

    def test_wheel_force_and_lower_link_reaction(self):
        q = np.array([0., .08, -.05, .16])
        d = self.plant.data(q)
        wheel = .6
        d.ctrl[:] = [wheel, 0., 0.]
        mujoco.mj_forward(self.plant.model, d)
        j = self.plant.joints
        radius = self.cfg['physics']['wheel_radius']['value']
        self.assertAlmostEqual(d.qfrc_actuator[j['axle_x']], wheel/radius, places=12)
        for name in ('body_pitch', 'motor_A', 'knee_B'):
            self.assertAlmostEqual(d.qfrc_actuator[j[name]], -wheel, places=12)
        projected = self.plant.tangent(q).T @ d.qfrc_actuator
        self.assertAlmostEqual(projected[0], wheel/radius, places=8)
        # The mounting link has a different angle than the reduced virtual
        # leg; preserving that reaction exposes a real mechanical difference.
        self.assertGreater(np.linalg.norm(projected[1:3]-[-wheel, 0.]), .001)

    def test_one_step_is_finite_with_bounded_closure_error(self):
        d = self.plant.data()
        mujoco.mj_step(self.plant.model, d)
        mujoco.mj_forward(self.plant.model, d)
        self.assertTrue(np.all(np.isfinite(d.qpos)))
        self.assertLess(self.plant.closure_error(d), 2e-6)
        self.assertFalse(any(w.number for w in d.warning))

    def test_projected_dynamics_energy_rate_includes_joint_curvature(self):
        from sim.fivebar.compare import FixedLength, full_mass
        fixed = FixedLength(self.plant)
        state = np.array([.03, .08, -.05, .12, -.4, .3])
        control = np.array([.07, -.1])
        mass, _, force = fixed.terms(state, control)
        self.assertGreater(np.min(np.linalg.eigvalsh(mass)), 0.)
        derivative = fixed.derivative(state, control)

        def energy(s):
            q = np.r_[s[:3], fixed.length]
            d = self.plant.data(q, np.r_[s[3:], 0.])
            return .5*d.qvel@full_mass(self.plant.model, d)@d.qvel+d.energy[0]

        h = 1e-5
        rate = (energy(state+h*derivative)-energy(state-h*derivative))/(2*h)
        self.assertAlmostEqual(rate, force@state[3:], delta=3e-6)

    def test_comparison_snapshot_reports_both_agreement_and_differences(self):
        from sim.fivebar.compare import snapshot
        report = snapshot(self.cfg)
        np.testing.assert_allclose(report['hip_position_error_m'], 0., atol=1e-12)
        inputs = np.array(report['input_difference'])
        np.testing.assert_allclose(inputs[:, 1], 0., atol=3e-8)
        self.assertGreater(abs(inputs[1, 0]), .01)
        self.assertGreater(abs(np.array(report['mass_difference'])[1, 1]), 1e-5)
