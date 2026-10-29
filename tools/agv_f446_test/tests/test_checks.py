import math
import unittest

from agv_home_test import (
    check_close_pair,
    check_common_scale,
    check_disabled,
    check_nan_ignored,
    check_timeout,
    check_timeout_timing,
    check_zero_pair,
    expected_wheel_speeds,
)


class KinematicsChecks(unittest.TestCase):
    def test_forward_uses_configured_feedback_signs(self):
        left, right = expected_wheel_speeds(0.3, 0.0)
        self.assertAlmostEqual(left, 5.0)  # wheel frame per docs/topics.md
        self.assertAlmostEqual(right, 5.0)

    def test_turning_produces_differential_targets(self):
        left, right = expected_wheel_speeds(0.2, 0.5)
        self.assertAlmostEqual(left, (0.2 - 0.345 * 0.5 / 2) / 0.06)
        self.assertAlmostEqual(right, (0.2 + 0.345 * 0.5 / 2) / 0.06)

    def test_saturation_scales_both_wheels_to_limit(self):
        left, right = expected_wheel_speeds(2.0, 0.0)
        self.assertAlmostEqual(abs(left), 20.0)
        self.assertAlmostEqual(abs(right), 20.0)
        ok, _ = check_common_scale((left, right), (2 / 0.06, 2 / 0.06), 0.01)
        self.assertTrue(ok)

    def test_saturation_preserves_turning_ratio(self):
        raw = expected_wheel_speeds(1.0, 2.0, max_wheel_speed=1e9)
        scaled = expected_wheel_speeds(1.0, 2.0)
        ok, _ = check_common_scale(scaled, raw, 0.01)
        self.assertTrue(ok)


class FeedbackChecks(unittest.TestCase):
    def test_close_and_zero_checks(self):
        self.assertTrue(check_close_pair((1.0, -1.0), (1.1, -0.9), 0.11)[0])
        self.assertTrue(check_zero_pair((0.1, -0.2), 0.25)[0])
        self.assertFalse(check_zero_pair((0.3, 0.0), 0.25)[0])

    def test_nan_feedback_fails_finite_check(self):
        self.assertFalse(check_close_pair((math.nan, 0.0), (0.0, 0.0), 1.0)[0])

    def test_timeout_requires_bit_and_stopped_wheels(self):
        self.assertTrue(check_timeout((0x01, 0x20), (0.0, 0.1), 0.2)[0])
        self.assertFalse(check_timeout((0x01,), (0.0, 0.0), 0.2)[0])
        self.assertFalse(check_timeout((0x20,), (2.0, 0.0), 0.2)[0])

    def test_timeout_and_zero_must_be_observed_within_deadline(self):
        samples = ((1.6, 0x20),)
        feedback = ({"elapsed_s": 1.7, "left_velocity_rad_s": 0.0, "right_velocity_rad_s": 0.1},)
        self.assertTrue(check_timeout_timing(1.0, samples, feedback, 0.2, 0.9)[0])
        late = ({"elapsed_s": 2.1, "left_velocity_rad_s": 0.0, "right_velocity_rad_s": 0.0},)
        self.assertFalse(check_timeout_timing(1.0, samples, late, 0.2, 0.9)[0])

    def test_disabled_requires_clear_enable_bit_and_zero_wheels(self):
        self.assertTrue(check_disabled((0x03, 0x03), (0.0, 0.1), 0.2)[0])
        self.assertFalse(check_disabled((0x13,), (0.0, 0.0), 0.2)[0])
        self.assertFalse(check_disabled((0x03,), (1.0, 0.0), 0.2)[0])

    def test_nan_ignored_means_velocity_remains_at_valid_baseline(self):
        self.assertTrue(check_nan_ignored((-5.0, 5.0), (-5.3, 5.1), 0.5)[0])
        self.assertFalse(check_nan_ignored((-5.0, 5.0), (0.0, 0.0), 0.5)[0])


if __name__ == "__main__":
    unittest.main()
