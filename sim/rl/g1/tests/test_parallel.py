"""Real spawned PPO/evaluation parity; wall-clock observations are not deterministic."""
import csv
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import torch

from sim.rl.g1.evaluation import evaluate, load_policy
from sim.rl.g1.parallel import default_jobs, jobs_count
from sim.rl.g1.protocol import HERE, panel
from sim.rl.g1.runner import train_seeds


class ParallelTests(unittest.TestCase):
    def test_job_limits(self):
        for cpus, expected in ((None, 1), (1, 1), (2, 1), (8, 4), (16, 5)):
            with patch('os.cpu_count', return_value=cpus):
                self.assertEqual(default_jobs(), expected)
        with self.assertRaises(ValueError):
            jobs_count(0)

    def test_tiny_serial_parallel_bit_identity(self):
        # Small test fixture only; production config/cases are never written.
        cfg = json.loads((HERE/'config.json').read_text())
        cfg.update(n_envs=2, n_steps=8, batch_size=16, n_epochs=1, transitions=64)
        with tempfile.TemporaryDirectory() as tmp:
            serial, parallel = Path(tmp)/'serial', Path(tmp)/'parallel'
            a = train_seeds(serial, seeds=[0, 1], jobs=1, config=cfg)
            b = train_seeds(parallel, seeds=[0, 1], jobs=2, config=cfg)
            self.assertEqual([r['completed_steps'] for r in a], [64, 64])
            self.assertEqual([r['completed_steps'] for r in b], [64, 64])
            for receipt in a+b:
                self.assertEqual(receipt['torch_num_threads'], 1)
                self.assertEqual(set(receipt['thread_env'].values()), {'1'})
            for receipt in a:
                self.assertEqual(len(receipt['worker_process_cpu_s']), 2)
            for receipt in b:
                self.assertEqual(receipt['worker_process_cpu_s'], [])
                self.assertEqual(receipt['environment_backend'], 'in_process')
            for seed in (0, 1):
                left, right = serial/f'seed-{seed}', parallel/f'seed-{seed}'
                models = []
                for run in (left, right):
                    model, norm, state = load_policy(run)
                    models.append((model, norm, state))
                (m1, n1, s1), (m2, n2, s2) = models
                for key, value in m1.policy.state_dict().items():
                    self.assertTrue(torch.equal(value, m2.policy.state_dict()[key]), key)
                for key in ('mean', 'var', 'count'):
                    np.testing.assert_array_equal(getattr(n1.obs_rms, key), getattr(n2.obs_rms, key))
                # IPC changes pickle object aliasing, not the generator bits.
                self.assertEqual(s1['samplers'], s2['samplers'])
                self.assertTrue(torch.equal(s1['torch'], s2['torch']))
                n1.close(); n2.close()
                losses = []
                for run in (left, right):
                    with next(run.glob('optimizer-*/progress.csv')).open() as stream:
                        losses.append([{k:v for k,v in row.items() if k not in ('time/fps','time/time_elapsed')}
                                       for row in csv.DictReader(stream)])
                self.assertEqual(*losses)
            # Both arms, real frozen development cases, in original order.
            cases = [panel(True)[0], panel(True)[-1]]
            for run in (None, serial/'seed-0'):
                one = evaluate(cases, run, jobs=1)
                many = evaluate(cases, run, jobs=2)
                self.assertEqual(one['strata'], many['strata'])
                for result in (one, many):
                    result.pop('elapsed_s')
                    for row in result['rows']:
                        row.pop('inference_mean_s'); row.pop('inference_max_s')
                # Exact JSON bytes, with every scientific metric retained.
                self.assertEqual(json.dumps(one, sort_keys=True).encode(),
                                 json.dumps(many, sort_keys=True).encode())
            self.assertEqual(torch.get_num_threads(), 1)
            for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
                self.assertEqual(os.environ[key], '1')


if __name__ == '__main__':
    unittest.main()
