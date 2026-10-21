"""Synthetic algebra only: no MuJoCo import, synthesis, rollout, or training."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np
from numpy.polynomial.chebyshev import chebvander

from sim.gain_schedule.fitting import evaluate_polynomial, fit_polynomial
from sim.gain_schedule.model import DEFAULT_LENGTHS, DOMAIN_M, FAMILY, check_length, config_at_length
from sim.gain_schedule.run import controller, fit_sweep


class FittingTests(unittest.TestCase):
    def setUp(self):
        self.lengths = np.array(DEFAULT_LENGTHS)
        self.coefficients = np.arange(80, dtype=float).reshape(4, 2, 10) / 30 - 1
        self.gains = self.exact(self.lengths)

    def exact(self, lengths):
        x = (2 * np.asarray(lengths) - sum(DOMAIN_M)) / (DOMAIN_M[1] - DOMAIN_M[0])
        return np.tensordot(chebvander(x, 3), self.coefficients, axes=([-1], [0]))

    def test_recovers_cubic_matrix_and_off_grid_values(self):
        fit = fit_polynomial(self.lengths, self.gains)
        np.testing.assert_allclose(fit["coefficients"], self.coefficients, atol=1e-13)
        queries = np.array([0.12, 0.135, 0.16, 0.185, 0.20])
        np.testing.assert_allclose(evaluate_polynomial(fit, queries), self.exact(queries), atol=1e-13)
        np.testing.assert_allclose(evaluate_polynomial(fit, 0.165), self.exact(0.165)[0], atol=1e-13)
        self.assertEqual(evaluate_polynomial(fit, 0.12).shape, (2, 10))
        self.assertLess(fit["diagnostics"]["max_abs_error"], 1e-13)

    def test_json_round_trip_and_conditioning(self):
        fit = json.loads(json.dumps(fit_polynomial(self.lengths, self.gains), allow_nan=False))
        d = fit["diagnostics"]
        self.assertLess(d["condition_number_2"], 3)
        self.assertGreater(d["raw_metre_power_basis_condition_number_2"],
                           1000 * d["condition_number_2"])
        self.assertEqual(d["rank"], 4)
        np.testing.assert_allclose(evaluate_polynomial(fit, self.lengths), self.gains, atol=1e-13)

    def test_noisy_fit_reports_actual_residuals(self):
        rng = np.random.default_rng(1)
        gains = self.gains + rng.normal(0, 0.01, self.gains.shape)
        fit = fit_polynomial(self.lengths, gains)
        errors = evaluate_polynomial(fit, self.lengths) - gains
        np.testing.assert_allclose(fit["diagnostics"]["entry_rmse"],
                                   np.sqrt(np.mean(errors**2, axis=0)))
        self.assertGreater(fit["diagnostics"]["max_abs_error"], 0.005)
        self.assertIn("no stability", fit["validation"])

    def test_unsorted_samples_and_constant_zero_gain(self):
        order = np.arange(len(self.lengths))[::-1]
        fit = fit_polynomial(self.lengths[order], self.gains[order])
        np.testing.assert_allclose(evaluate_polynomial(fit, self.lengths), self.gains, atol=1e-13)
        zero = fit_polynomial(self.lengths, np.zeros_like(self.gains), degree=0)
        self.assertEqual(zero["diagnostics"]["relative_frobenius_error"], 0)
        np.testing.assert_array_equal(evaluate_polynomial(zero, 0.16), np.zeros((2, 10)))

    def test_outside_domain_and_nonfinite_queries_are_errors(self):
        fit = fit_polynomial(self.lengths, self.gains)
        for query in (np.nextafter(0.12, 0), np.nextafter(0.20, 1), 0.21, 0.30,
                      np.nan, np.inf, [0.16, 0.201]):
            with self.subTest(query=query), self.assertRaises(ValueError):
                evaluate_polynomial(fit, query)
        evaluate_polynomial(fit, list(DOMAIN_M))

    def test_invalid_samples_and_degrees(self):
        invalid = [
            (self.lengths[:-1], self.gains),
            (np.r_[self.lengths[:-1], self.lengths[-2]], self.gains),
            (self.lengths[1:], self.gains[1:]),
            (np.r_[np.nan, self.lengths[1:]], self.gains),
            (self.lengths, self.gains * np.nan),
            (self.lengths, self.gains[:, 0, :]),
        ]
        for lengths, gains in invalid:
            with self.subTest(lengths=lengths), self.assertRaises(ValueError):
                fit_polynomial(lengths, gains)
        for degree in (-1, 19, 1.5, True):
            with self.subTest(degree=degree), self.assertRaises(ValueError):
                fit_polynomial(self.lengths, self.gains, degree=degree)

    def test_ill_conditioning_is_rejected(self):
        lengths = np.r_[0.12, 0.12 + 1e-14, 0.12 + 2e-14, 0.20]
        with self.assertRaisesRegex(ValueError, "condition"):
            fit_polynomial(lengths, np.zeros((4, 2, 10)))
        with self.assertRaisesRegex(ValueError, "condition"):
            fit_polynomial(self.lengths, self.gains, max_condition=1)

    def test_malformed_saved_fit_is_rejected(self):
        fit = fit_polynomial(self.lengths, self.gains)
        for key, value in (("basis", "power"), ("out_of_domain", "clip"),
                           ("coefficients", [[[float("nan")]]]), ("degree", -1),
                           ("domain_m", [0.20, 0.12])):
            broken = {**fit, key: value}
            with self.subTest(key=key), self.assertRaises(ValueError):
                evaluate_polynomial(broken, 0.16)

    def test_fit_sweep_preserves_separate_delay_shapes_and_metadata(self):
        regimes = []
        for delay, size in ((0.002, 10), (0.003, 12), (0.005, 14)):
            values = np.pad(self.gains, ((0, 0), (0, 0), (0, size - 10)))
            regimes.append({
                "runtime": {"delay_s": delay},
                "samples": [{"length_m": length, "K": gain.tolist(),
                             "state_order": [f"synthetic_{i}" for i in range(size)],
                             "input_order": ["wheel", "hip"]}
                            for length, gain in zip(self.lengths, values)],
            })
        source = {
            "schema_version": 1, "kind": "assumed_leg_sweep", "family": FAMILY,
            "status": "COMPLETE", "domain_m": list(DOMAIN_M),
            "lengths_m": self.lengths.tolist(), "regimes": regimes,
            "reference_config": {"synthetic": True}, "experiment_config": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            path = out / "synthetic_sweep.json"
            args = SimpleNamespace(sweep=path, degree=3, max_condition=1e8)
            path.write_text(json.dumps(source))
            result = fit_sweep(args, out)
            saved = json.loads((out / "schedule.json").read_text())
            self.assertEqual(result["physics_acceptance"], "NOT_EVALUATED")
            self.assertEqual(saved["reference_config"], source["reference_config"])
            for regime, size in zip(saved["regimes"], (10, 12, 14)):
                self.assertEqual(evaluate_polynomial(regime["fit"], 0.16).shape, (2, size))
            for change in ("incomplete", "order", "missing_sample", "duplicate_delay", "legacy_domain"):
                broken = deepcopy(source)
                if change == "incomplete":
                    broken["status"] = "INCOMPLETE"
                elif change == "order":
                    broken["regimes"][0]["samples"][1]["state_order"].reverse()
                elif change == "missing_sample":
                    broken["regimes"][0]["samples"].pop()
                elif change == "duplicate_delay":
                    broken["regimes"].append(broken["regimes"][0])
                else:
                    broken["domain_m"] = [0.12, 0.30]
                path.write_text(json.dumps(broken))
                with self.subTest(change=change), self.assertRaises(ValueError):
                    fit_sweep(args, out)

    def test_controller_uses_causal_observation_vector(self):
        K = self.gains[0].copy()
        z = np.arange(10)
        expected = -K @ z
        feedback = controller(K)
        K[:] = 0  # Controller owns its captured matrix.
        np.testing.assert_array_equal(feedback(SimpleNamespace(vector=lambda: z)), expected)


class ModelFamilyTests(unittest.TestCase):
    def test_family_scaling_and_no_input_mutation(self):
        root = Path(__file__).resolve().parents[3]
        base = json.loads((root / "sim/configs/assumed_planar.json").read_text())
        original = deepcopy(base)
        cfg = config_at_length(base, 0.20)
        self.assertEqual(base, original)
        self.assertAlmostEqual(cfg["physics"]["leg_com"]["value"], 0.10)
        self.assertAlmostEqual(cfg["physics"]["leg_inertia"]["value"], 0.001875)
        changed = {"leg_length", "leg_com", "leg_inertia"}
        for name in base["physics"].keys() - changed:
            self.assertEqual(cfg["physics"][name], base["physics"][name])
        for name in ("controller", "simulation", "protocol", "source_geometry_inventory_unused"):
            self.assertEqual(cfg[name], base[name])
        for endpoint in DOMAIN_M:
            config_at_length(base, endpoint)
        # Shared transform remains usable by fivebar's .21 m comparison and
        # its geometry rejection tests; it never clamps hypothetical lengths.
        for length in (0.11, 0.21, 0.22, 0.30):
            scaled = config_at_length(base, length)
            self.assertEqual(scaled["physics"]["leg_length"]["value"], length)
            self.assertAlmostEqual(scaled["physics"]["leg_com"]["value"], length / 2)
            with self.assertRaises(ValueError):
                check_length(length)
        for bad in (0, -0.1, np.inf, np.nan):
            with self.subTest(length=bad), self.assertRaises(ValueError):
                config_at_length(base, bad)


if __name__ == "__main__":
    unittest.main()
