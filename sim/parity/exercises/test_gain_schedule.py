"""Run with WBR_PARITY_BUILD pointing at a compiled reference build."""
import os
from pathlib import Path
import unittest

from sim.parity.check_student import evaluate


class LearnerGainParity(unittest.TestCase):
    def test_gain_schedule_matches_original_c(self):
        directory = os.environ.get("WBR_PARITY_BUILD")
        self.assertIsNotNone(directory, "Set WBR_PARITY_BUILD to your reference build directory")
        result = evaluate(Path(directory))
        self.assertEqual(result["status"], "PASS", result["cases"])
        self.assertEqual(len(result["cases"]), result["case_count_planned"])


if __name__ == "__main__":
    unittest.main()
