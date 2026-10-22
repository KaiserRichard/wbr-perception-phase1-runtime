"""Focused combined-study contract checks; fixtures retained, no full grid."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from sim.augmented import load_experiment
from sim.gain_schedule import combined as c
from sim.gain_schedule.model import config_at_length
from sim.gain_schedule.stress import CONFIG, Condition, actual_config


class CombinedTests(unittest.TestCase):
    def test_declared_matrix_and_nominal_family_separate_from_actual_errors(self):
        base, _, _ = load_experiment(CONFIG)
        rows = c.matrix()
        self.assertEqual(len(rows), 30)
        self.assertEqual(len({r['id'] for r in rows}), 30)
        for length in (.12, .20):
            nominal = config_at_length(base, length)
            cases = [r for r in rows if r['length_m'] == length]
            self.assertEqual(len(cases), 15)
            for row in cases:
                cond = Condition(**row['condition'])
                actual = actual_config(nominal, cond)
                for key in ('body_mass', 'body_inertia'):
                    self.assertEqual(actual['physics'][key]['value'],
                                     base['physics'][key]['value']*cond.mass_scale)
                for key in ('body_com', 'leg_length', 'leg_com', 'leg_inertia'):
                    self.assertEqual(actual['physics'][key], nominal['physics'][key])
            self.assertEqual(nominal['protocol'], base['protocol'])

    def test_numpy_receipt_serialization_and_incomplete_attempt_retention(self):
        root = Path(tempfile.mkdtemp(dir=os.environ.get('WBR_TEST_OUT')))
        path = c.attempt_directory(root)
        c.write_json(path/'result.json', {'ok': np.bool_(True), 'n': np.int64(7),
                                        'v': np.array([1., np.nan])})
        self.assertEqual(json.loads((path/'result.json').read_text()),
                         {'ok': True, 'n': 7, 'v': [1., None]})
        retry = c.attempt_directory(root)
        self.assertNotEqual(path, retry)
        self.assertTrue((path/'result.json').exists())

    def test_all_conditions_use_supplied_fixed_design_and_receipts_resume(self):
        root = Path(tempfile.mkdtemp(dir=os.environ.get('WBR_TEST_OUT')))
        nominal, _, effects = load_experiment(CONFIG)
        gain = np.arange(20).reshape(2, 10)*.01
        observed = []
        runtime = SimpleNamespace(plant=SimpleNamespace(xml='<mock/>'), limits=np.array([2., 4.]))

        def evaluate(rt, controller, scenario, seed, path):
            observed.append(controller.gain.copy())
            self.assertEqual(scenario, 'push')
            # Only six-state measurement is supplied; privileged state is absent.
            np.testing.assert_allclose(controller(SimpleNamespace(measurement=np.ones(6))),
                                       -gain @ np.r_[np.ones(6), np.zeros(4)])
            return {'status': 'FAIL', 'failed_checks': ['fixture']}

        with patch.object(c, 'make_runtime', return_value=runtime), patch.object(c, 'evaluate', side_effect=evaluate) as run:
            for spec in c.matrix()[:15]:
                c.run_case(spec, nominal, effects, gain, root)
            self.assertEqual(run.call_count, 15)
            c.run_case(c.matrix()[0], nominal, effects, gain, root)
            self.assertEqual(run.call_count, 15)
        for actual in observed:
            np.testing.assert_array_equal(actual, gain)


if __name__ == '__main__':
    unittest.main()
