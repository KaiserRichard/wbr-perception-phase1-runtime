"""Failures retain evidence, preserve seed slots and do not cancel other seeds."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sim.rl.environment import WbrEnv, NumericalFailure
from sim.rl.evaluation import final_policies
from sim.rl.provenance import new_output
from sim.rl.run import experiment
from sim.rl.training import train


class FailureTests(unittest.TestCase):
    def test_warning_and_displacement_are_distinct_from_time_limit(self):
        env = WbrEnv()
        self.addCleanup(env.close)
        env.reset(seed=0)
        original = type(env.runtime).warning_counts
        with patch.object(type(env.runtime), 'warning_counts', property(lambda _: [1])):
            with self.assertRaises(NumericalFailure):
                env.step([0., 0.])
        env.reset(seed=0)
        env.runtime.reset([1.501, 0., 0., 0., 0., 0.], seed=100)
        _, reward, terminated, truncated, _ = env.step([0., 0.])
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertLess(reward, -100.)

    def test_failed_training_attempt_keeps_reason_and_missing_slot(self):
        root = Path(tempfile.mkdtemp(prefix='wbr-rl-failure-test-'))
        with patch('sim.rl.training.capture', side_effect=ValueError('frozen source mismatch')):
            status = train(0, root / 'seed-0', root / 'authorization.json')
        self.assertEqual(status['exit_code'], 1)
        self.assertEqual(status['actual_env_steps'], 0)
        self.assertTrue((root / 'seed-0/error.txt').is_file())
        self.assertFalse((root / 'seed-0/final.zip').exists())
        slots = final_policies(root)
        self.assertEqual(set(slots), set(range(5)))
        self.assertTrue(all(not p['complete'] for p in slots.values()))
        self.assertIn('frozen source mismatch', (root / 'seed-0/error.txt').read_text())

    def test_existing_attempt_is_never_overwritten(self):
        root = Path(tempfile.mkdtemp(prefix='wbr-rl-existing-test-'))
        path = root / 'attempt'
        path.mkdir()
        (path / 'partial.txt').write_text('retained evidence')
        with self.assertRaises(FileExistsError):
            new_output(path)
        self.assertEqual((path / 'partial.txt').read_text(), 'retained evidence')

    def test_all_five_subprocesses_and_evaluation_continue_after_failure(self):
        root = Path(tempfile.mkdtemp(prefix='wbr-rl-runner-test-'))
        launched = []

        def process(command, **kwargs):
            seed = int(command[command.index('--seed') + 1])
            launched.append(seed)
            return int(seed == 2)

        with patch('sim.rl.run.capture'), patch('sim.rl.run.subprocess.call', side_effect=process), \
                patch('sim.rl.evaluation.run_evaluation', return_value=1) as evaluator:
            code = experiment(root / 'attempt', root / 'authorization.json', 5, 6)
        self.assertEqual(code, 1)
        self.assertEqual(sorted(launched), list(range(5)))
        evaluator.assert_called_once()
        status = json.loads((root / 'attempt/status.json').read_text())
        self.assertEqual(status['training_exits']['2'], 1)
        self.assertEqual(sum(status['training_exits'].values()), 1)
