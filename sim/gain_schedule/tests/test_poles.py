"""Known closed-loop fixtures; no synthesis or physics needed."""

import unittest

import numpy as np

from sim.gain_schedule.fitting import fit_polynomial
from sim.gain_schedule.poles import check_fitted_poles


class PoleTests(unittest.TestCase):
    def test_complex_eigenpairs_and_strict_unit_circle_boundary(self):
        gain = np.array([[.2, .1], [-.1, .3]])
        regime = {
            "fit": fit_polynomial([.12, .20], [gain, gain], degree=0),
            "runtime": {"delay_s": .002},
            "state_order": ["x", "xdot"], "input_order": ["wheel", "hip"],
        }
        cfg = {"simulation": {"dt_s": .002},
               "controller": {"input_order": regime["input_order"]}}
        for radius in (.8, 1., 1.1):
            # ±i*radius has a known modulus, even at exactly the unit boundary.
            closed = np.array([[0., -radius], [radius, 0.]])
            design = {"A_discrete_actual": closed + gain,
                      "B_discrete_actual": np.eye(2), "dt_s": .002,
                      "state_order": regime["state_order"],
                      "max_closed_loop_pole_magnitude": radius}
            check = check_fitted_poles(regime, .135, gain, design, cfg)
            self.assertAlmostEqual(check["polynomial_pole_radius"], radius)
            self.assertAlmostEqual(check["margin_to_one"], 1-radius)
            self.assertEqual(check["polynomial_local_status"], "PASS" if radius < 1 else "FAIL")
            if radius < 1:
                self.assertAlmostEqual(check["slowest_time_constant_s"], -.002/np.log(radius))
            else:
                self.assertIsNone(check["slowest_time_constant_s"])
            for p, v in zip(check["polynomial_closed_loop_eigenvalues"],
                            check["right_eigenvectors_by_mode_real_imag"]):
                p = complex(*p)
                v = np.array([complex(*entry) for entry in v])
                np.testing.assert_allclose(closed @ v, p*v, atol=1e-14)


if __name__ == "__main__":
    unittest.main()
