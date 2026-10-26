import unittest

from tools.supervisor_demo.safety_filter import decide


class SafetyFilterTests(unittest.TestCase):
    def test_none_passes_through(self):
        result = decide(0.3, -0.2, 0, None, 0.05)
        self.assertEqual((result.linear_x, result.angular_z), (0.3, -0.2))
        self.assertEqual(result.state, 'NONE')

    def test_near_stop_candidate_clamps_forward_but_keeps_rotation(self):
        result = decide(0.3, 0.4, 2, 0.8, 0.05)
        self.assertEqual((result.linear_x, result.angular_z), (0.0, 0.4))

    def test_far_stop_candidate_does_not_trigger_distance_rule(self):
        result = decide(0.3, 0.0, 2, 1.1, 0.05)
        self.assertEqual(result.linear_x, 0.3)

    def test_jump_limits_forward_and_keeps_rotation(self):
        result = decide(0.3, -0.1, 1, 0.8, 0.05)
        self.assertEqual((result.linear_x, result.angular_z), (0.15, -0.1))
        self.assertEqual(result.reason, 'jump candidate (would ask operator)')

    def test_stale_and_missing_advisory_clamp_forward(self):
        stale = decide(0.3, 0.2, 0, None, 0.301)
        missing = decide(0.3, 0.2, 0, None, None)
        self.assertEqual((stale.linear_x, missing.linear_x), (0.0, 0.0))
        self.assertEqual((stale.angular_z, missing.angular_z), (0.2, 0.2))

    def test_reverse_is_not_changed_by_forward_clamp(self):
        result = decide(-0.1, 0.3, 2, 0.5, 0.1)
        self.assertEqual((result.linear_x, result.angular_z), (-0.1, 0.3))


if __name__ == '__main__':
    unittest.main()
