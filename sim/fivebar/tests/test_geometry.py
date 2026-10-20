import hashlib
import json
import math
import os
from pathlib import Path
import unittest

import numpy as np

from sim.fivebar.geometry import Geometry, GeometryError


ROOT = Path(__file__).resolve().parents[2]


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.g = Geometry()

    def test_inventory_and_source_provenance(self):
        cfg = json.loads((ROOT/"configs/assumed_planar.json").read_text())
        self.assertEqual(self.g, Geometry.from_inventory(cfg))
        manifest = json.loads((ROOT/"fivebar/PROVENANCE.json").read_text())
        for name, digest in manifest["reference_files_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), digest)
        self.assertEqual((ROOT/"fivebar/LICENSE").read_bytes(),
                         (ROOT/"parity/vendor/dm_jump/LICENSE").read_bytes())

    def test_both_circle_branches_and_distances(self):
        q = [2.3, 0.8]
        for branch in (-1, 1):
            b, c, d = self.g.forward(q, branch)
            self.assertAlmostEqual(np.linalg.norm(c-b), self.g.l2, places=13)
            self.assertAlmostEqual(np.linalg.norm(c-d), self.g.l3, places=13)
            self.assertEqual(int(np.sign(np.linalg.det(np.array([d-b, c-b])))), branch)

    def test_standing_inverse_grid(self):
        for length in (0.10, 0.13, 0.16, 0.19):
            for beta in np.linspace(1.25, 1.9, 7):
                q = self.g.inverse(length, beta)
                np.testing.assert_allclose(self.g.virtual(q), [length, beta], atol=2e-14)

    def test_cartesian_and_virtual_jacobians_against_finite_differences(self):
        eps = 1e-6
        for branch in (-1, 1):
            for q in (np.array([2.3, .8]), np.array([1.3, 1.8]), np.array([2.0, 1.0])):
                cart, polar = self.g.jacobians(q, branch)
                cart_fd = np.column_stack([(self.g.forward(q+e, branch)[1]-self.g.forward(q-e, branch)[1])/(2*eps)
                                           for e in eps*np.eye(2)])
                polar_fd = np.column_stack([(self.g.virtual(q+e, branch)-self.g.virtual(q-e, branch))/(2*eps)
                                            for e in eps*np.eye(2)])
                np.testing.assert_allclose(cart, cart_fd, atol=2e-10, rtol=2e-8)
                np.testing.assert_allclose(polar, polar_fd, atol=2e-9, rtol=2e-8)

    def test_virtual_work_endpoint_moment_and_stator_reaction(self):
        q, dq = np.array([2.3, .8]), np.array([.7, -.4])
        force, moment = 31., -.6
        result = self.g.wrench(q, force, moment)
        cart, jac = self.g.jacobians(q)
        self.assertAlmostEqual(result['motor_Nm']@dq, np.array([force, moment])@jac@dq, places=12)
        self.assertAlmostEqual(result['endpoint_force_uv_N']@cart@dq, result['motor_Nm']@dq, places=12)
        offset = self.g.forward(q)[1]-[self.g.l5/2, 0]
        f = result['endpoint_force_uv_N']
        self.assertAlmostEqual(offset[0]*f[1]-offset[1]*f[0], moment, places=12)
        self.assertAlmostEqual(result['direct_stator_Nm'], -sum(result['motor_Nm']), places=12)
        self.assertEqual(result['chassis_moment_about_O_Nm'], -moment)
        np.testing.assert_array_equal(result['chassis_force_uv_N'], -f)

    def test_invalid_and_singular_inputs_rejected(self):
        for lengths in ({'l1': 0}, {'l5': float('nan')}):
            with self.assertRaises(GeometryError):
                Geometry(**lengths)
        for q in ([float('nan'), 1], [1], [float('inf'), 0]):
            with self.assertRaises(GeometryError):
                self.g.forward(q)
        with self.assertRaises(GeometryError):
            self.g.forward([1, 1], branch=0)
        # B=D at the crossing of equal proximal circles.
        angle = math.acos(self.g.l5/(2*self.g.l1))
        with self.assertRaises(GeometryError):
            self.g.forward([angle, math.pi-angle])
        with self.assertRaises(GeometryError):
            Geometry(l2=.01, l3=.01).forward([math.pi, 0])
        for length in (0, .5, float('nan')):
            with self.assertRaises(GeometryError):
                self.g.inverse(length, math.pi/2)
        with self.assertRaises(GeometryError):
            self.g.inverse(.16, math.pi/2, elbows=(-1, 1))

    @unittest.skipUnless(os.environ.get('WBR_FIVEBAR_C_REFERENCE'), 'Optional prebuilt C reference path not configured')
    def test_against_existing_compiled_pinned_c_vmc(self):
        # Read-only use of a prior build; this test never compiles or changes it.
        from sim.parity.reference import CReference
        reference = CReference(Path(os.environ['WBR_FIVEBAR_C_REFERENCE']))
        vectors = json.loads((ROOT/"parity/fixtures/shared_vectors.json").read_text())
        cases = vectors['vmc_cases'] + [dict(side='right', phi1_rad=2.3, phi4_rad=.8,
                pitch_rad=.1, pitch_rate_rad_s=0., dt_s=.001, F0_N=31., Tp_Nm=-.6)]
        for case in cases:
            args = {name: case[name] for name in ('side', 'phi1_rad', 'phi4_rad', 'pitch_rad',
                    'pitch_rate_rad_s', 'dt_s', 'F0_N', 'Tp_Nm')}
            upstream = reference.vmc(**args)
            q = [case['phi1_rad'], case['phi4_rad']]
            np.testing.assert_allclose(self.g.virtual(q), [upstream['L0'], upstream['phi0']], atol=2e-6, rtol=2e-5)
            jac = self.g.jacobians(q)[1]
            np.testing.assert_allclose(jac.T, [[upstream['j11'], upstream['j12']],
                                              [upstream['j21'], upstream['j22']]], atol=3e-6, rtol=3e-5)
            np.testing.assert_allclose(self.g.wrench(q, case['F0_N'], case['Tp_Nm'])['motor_Nm'],
                                       [upstream['tau0'], upstream['tau1']], atol=1e-5, rtol=3e-5)
