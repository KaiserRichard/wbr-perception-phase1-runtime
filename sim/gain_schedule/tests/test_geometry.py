"""Pinned geometry only; no dynamics, synthesis, rollout or training."""

from copy import deepcopy
import json
import math
from pathlib import Path
import unittest

import numpy as np

from sim.fivebar.geometry import Geometry, GeometryError
from sim.gain_schedule.geometry import geometry_evidence
from sim.gain_schedule.model import DEFAULT_LENGTHS, DOMAIN_M, training_midpoints


class GeometryTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[3]
        self.base = json.loads((root / "sim/configs/assumed_planar.json").read_text())

    def test_interval_certificate_and_existing_inverse_jacobians_for_both_postures(self):
        original = deepcopy(self.base)
        lengths = [*DEFAULT_LENGTHS, *training_midpoints(DEFAULT_LENGTHS)]
        evidence = geometry_evidence(self.base, lengths)
        self.assertEqual(self.base, original)
        self.assertEqual(evidence["source_geometry"], self.base["source_geometry_inventory_unused"])
        self.assertAlmostEqual(evidence["max_upright_reach_m"], math.sqrt(.215**2 - .04**2))
        self.assertIn("UNKNOWN", evidence["limitation"])
        geometry = Geometry.from_inventory(self.base)
        for posture, beta_deg in zip(evidence["postures"], (90, 104)):
            self.assertAlmostEqual(math.degrees(posture["beta_rad"]), beta_deg)
            self.assertTrue(posture["interval_reachable_and_nonsingular"])
            self.assertGreater(posture["length_margin_to_extension_m"], 0)
            self.assertEqual(len(posture["samples"]), 17)
            lower, upper = posture["distal_angle_separation_bounds_rad"]
            self.assertGreater(lower, 0)
            self.assertLess(upper, math.pi)
            for sample in posture["samples"]:
                q = np.asarray(sample["motor_angles_rad"])
                np.testing.assert_allclose(geometry.virtual(q),
                                           [sample["length_m"], posture["beta_rad"]], atol=1e-14)
                # Independently finite-difference existing forward kinematics.
                eps = 1e-6
                numeric = np.column_stack([(geometry.virtual(q+dq) - geometry.virtual(q-dq))/(2*eps)
                                           for dq in eps*np.eye(2)])
                np.testing.assert_allclose(sample["virtual_jacobian"], numeric, rtol=1e-7, atol=1e-9)
                self.assertGreater(abs(sample["virtual_determinant"]), 1e-9)
                self.assertGreater(min(sample["cartesian_singular_values"]), 1e-9)
            for rlo, rhi in posture["serial_radius_bounds_m"]:
                self.assertGreater(rlo, .065)
                self.assertLess(rhi, .215)

    def test_singular_upright_boundary_and_unreachable_old_endpoint_are_rejected(self):
        geometry = Geometry.from_inventory(self.base)
        for length in (math.sqrt(.215**2 - .04**2), .22, .30):
            with self.subTest(length=length), self.assertRaises(GeometryError):
                geometry.inverse(length, math.pi / 2)
        with self.assertRaises(ValueError):
            geometry_evidence(self.base, [.21])

    def test_midpoints_are_all_eight_intervals_not_training_or_evaluation_grid(self):
        np.testing.assert_allclose(training_midpoints(DEFAULT_LENGTHS),
                                   [.125, .135, .145, .155, .165, .175, .185, .195])
        for invalid in ([.12, .19], [.13, .20], [.12, .12, .20], [.12, .30], []):
            with self.subTest(grid=invalid), self.assertRaises(ValueError):
                training_midpoints(invalid)

    def test_tilted_start_rejects_upright_only_extension(self):
        geometry = Geometry.from_inventory(self.base)
        beta = math.radians(104)
        evidence = geometry_evidence(self.base, [])
        upright, tilted = evidence["postures"]
        # Independently solve the farther-pin extension quadratic.
        roots = np.roots([1, 2*.04*abs(math.cos(beta)), .04**2 - .215**2])
        limit = float(max(roots))
        self.assertAlmostEqual(tilted["serial_extension_ray_limit_m"], limit)
        self.assertGreater(limit, .20)
        self.assertLess(limit, .21)
        self.assertGreater(upright["serial_extension_ray_limit_m"], .21)
        geometry.inverse(.21, math.pi / 2)
        geometry.inverse(.20, beta)
        for length in (.21, limit):
            with self.subTest(length=length), self.assertRaises(GeometryError):
                geometry.inverse(length, beta)


if __name__ == "__main__":
    unittest.main()
