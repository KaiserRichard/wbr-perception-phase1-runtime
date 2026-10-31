"""Real independent PPO seeds: single root versus two portable merged parts."""
import csv
import hashlib
import json
from pathlib import Path
import pickle
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from sim.rl.g1.evaluation import evaluate, load_policy
from sim.rl.g1.merge_runs import merge_runs, validate_part
from sim.rl.g1.protocol import HERE, identity, json_hash, panel, write_json
from sim.rl.g1.run_manifest import FINAL_SEEDS, MANIFEST, prepare_run, seed_list
from sim.rl.g1.runner import full, train_seeds
from sim.rl.g1.training import newest


class SplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.single = cls.root/'single'
        cls.parts = [cls.root/'kaggle', cls.root/'colab']
        cls.cfg = json.loads((HERE/'config.json').read_text())
        cls.cfg.update(n_envs=2, n_steps=8, batch_size=16, n_epochs=1, transitions=64)
        train_seeds(cls.single, jobs=1, subprocess_envs=False, config=cls.cfg)
        train_seeds(cls.parts[0], seeds=[0, 1, 2], jobs=2, config=cls.cfg)
        train_seeds(cls.parts[1], seeds=[3, 4], jobs=1, config=cls.cfg)
        cls.merged = merge_runs(cls.parts, cls.root/'merged')

    def assert_state_equal(self, left, right):
        if isinstance(left, torch.Tensor):
            self.assertTrue(torch.equal(left, right))
        elif isinstance(left, np.ndarray):
            np.testing.assert_array_equal(left, right)
        elif isinstance(left, dict):
            self.assertEqual(left.keys(), right.keys())
            for key in left:
                self.assert_state_equal(left[key], right[key])
        elif isinstance(left, (list, tuple)):
            self.assertEqual(len(left), len(right))
            for a, b in zip(left, right):
                self.assert_state_equal(a, b)
        else:
            self.assertEqual(left, right)

    def test_single_machine_equals_split_merge(self):
        manifest = validate_part(self.merged)
        self.assertEqual(manifest['seeds'], FINAL_SEEDS)
        self.assertEqual(manifest['code_hash'], json_hash(identity()))
        self.assertEqual(len(manifest['parts']), 2)
        for seed in FINAL_SEEDS:
            source = self.parts[0 if seed < 3 else 1]/f'seed-{seed}'
            merged = self.merged/f'seed-{seed}'
            # Merge preserves every checkpoint and result byte, including timing.
            for path in source.rglob('*'):
                if path.is_file():
                    self.assertEqual(path.read_bytes(), (merged/path.relative_to(source)).read_bytes())
            models = [load_policy(root/f'seed-{seed}') for root in (self.single, self.merged)]
            try:
                (a, na, sa), (b, nb, sb) = models
                self.assert_state_equal(a.policy.state_dict(), b.policy.state_dict())
                self.assert_state_equal(a.policy.optimizer.state_dict(), b.policy.optimizer.state_dict())
                self.assert_state_equal(na.obs_rms.__dict__, nb.obs_rms.__dict__)
                for key in ('samplers', 'python', 'numpy', 'torch', 'completed_steps', 'updates'):
                    self.assert_state_equal(sa[key], sb[key])
            finally:
                for _, norm, _ in models:
                    norm.close()
            losses = []
            results = []
            for root in (self.single, self.merged):
                run = root/f'seed-{seed}'
                with next(run.glob('optimizer-*/progress.csv')).open() as stream:
                    losses.append([{k:v for k,v in row.items() if k not in ('time/fps', 'time/time_elapsed')}
                                   for row in csv.DictReader(stream)])
                result = evaluate([panel(True)[0]], run, jobs=1)
                result.pop('elapsed_s')
                for row in result['rows']:
                    row.pop('inference_mean_s'); row.pop('inference_max_s')
                results.append(result)
            self.assertEqual(*losses)
            self.assertEqual(*results)

    def test_refuses_missing_duplicate_or_existing_destination(self):
        for parts in ([self.parts[0]], self.parts+[self.parts[0]]):
            out = self.root/'rejected'
            with self.assertRaisesRegex(ValueError, 'exactly once'):
                merge_runs(parts, out)
            self.assertFalse(out.exists())
        with self.assertRaises(FileExistsError):
            merge_runs(self.parts, self.merged)

    def test_refuses_mismatched_and_incomplete_parts(self):
        path = self.parts[1]/MANIFEST
        original = path.read_bytes()
        manifest = json.loads(original)
        try:
            for key, value, message in [('code_hash', 'different', 'Code hash'),
                                        ('status', 'PARTIAL', 'Incomplete part'),
                                        ('config_hash', 'different', 'Config hash')]:
                write_json(path, dict(manifest, **{key:value}))
                with self.assertRaisesRegex(ValueError, message):
                    merge_runs(self.parts, self.root/'rejected')
        finally:
            path.write_bytes(original)
        receipt = self.parts[1]/'seed-4/receipt.json'
        original = receipt.read_bytes()
        try:
            write_json(receipt, dict(json.loads(original), status='PARTIAL', completed_steps=16))
            with self.assertRaisesRegex(ValueError, 'Incomplete or mismatched seed'):
                merge_runs(self.parts, self.root/'rejected')
        finally:
            receipt.write_bytes(original)

    def test_refuses_different_training_recipes_and_partial_final_evaluation(self):
        with tempfile.TemporaryDirectory() as tmp:
            different = Path(tmp)/'different'
            shutil.copytree(self.parts[1], different)
            cfg = dict(self.cfg, learning_rate=self.cfg['learning_rate']/2)
            manifest = json.loads((different/MANIFEST).read_text())
            write_json(different/MANIFEST, dict(manifest, config=cfg, config_hash=json_hash(cfg)))
            for seed in (3, 4):
                run = different/f'seed-{seed}'
                declaration = json.loads((run/'declaration.json').read_text())
                write_json(run/'declaration.json', dict(declaration, config=cfg))
                dest = newest(run)
                state = pickle.loads((dest/'state.pkl').read_bytes())
                (dest/'state.pkl').write_bytes(pickle.dumps(dict(state, config=cfg)))
                marker = json.loads((dest/'complete.json').read_text())
                marker['files']['state.pkl'] = hashlib.sha256((dest/'state.pkl').read_bytes()).hexdigest()
                write_json(dest/'complete.json', marker)
            with self.assertRaisesRegex(ValueError, 'Training config mismatch'):
                merge_runs([self.parts[0], different], self.root/'rejected')
        # The tiny test budget is allowed for plumbing tests, never final science.
        with self.assertRaisesRegex(ValueError, 'exactly1M'):
            load_policy(self.merged/'seed-0', require_final=True)

    def test_refuses_corrupt_checkpoint_and_wrong_seed(self):
        dest = newest(self.parts[1]/'seed-4')
        state_path, marker_path = dest/'state.pkl', dest/'complete.json'
        state_bytes, marker_bytes = state_path.read_bytes(), marker_path.read_bytes()
        try:
            state_path.write_bytes(b'corrupt')
            with self.assertRaisesRegex(RuntimeError, 'No verified complete'):
                merge_runs(self.parts, self.root/'rejected')
            state = pickle.loads(state_bytes)
            state['seed'] = 3
            state_path.write_bytes(pickle.dumps(state))
            marker = json.loads(marker_bytes)
            marker['files']['state.pkl'] = hashlib.sha256(state_path.read_bytes()).hexdigest()
            write_json(marker_path, marker)
            with self.assertRaisesRegex(ValueError, 'source/config/seed mismatch'):
                merge_runs(self.parts, self.root/'rejected')
        finally:
            state_path.write_bytes(state_bytes)
            marker_path.write_bytes(marker_bytes)

    def test_seed_parser_and_resume_contract(self):
        self.assertEqual(seed_list('2,0,1'), [0, 1, 2])
        for value in ('', '0,0', '0,5', 'a', '1,', [-1], [True], [1.0]):
            with self.assertRaises(ValueError):
                seed_list(value)
        with self.assertRaisesRegex(ValueError, 'seed list mismatch'):
            prepare_run(self.parts[0], [3, 4], self.cfg)

    def test_subset_queue_skips_final_evaluation_and_keeps_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root/'smoke/smoke.json', dict(identity=identity(), status='PASS', jobs=1,
                       laptop_ESTIMATE=dict(evaluation_gate=True, transitions_per_second=80)))
            with self.assertRaisesRegex(RuntimeError, 'prerequisites unresolved'):
                full(root, jobs=1, seeds=[3, 4])
            write_json(root/'host-readiness.json', dict.fromkeys(
                ['report_assembly_resolved', 'windows_smoke_passed',
                 'offline_bundle_verified', 'host_and_usb_permitted'], True))
            write_json(root/'pilot-seed42/pilot.json', dict(pass_pilot=True))
            baseline = dict(rows=[dict(numerical_failure=False)],
                            strata={f'{d}ms':dict(strict=.5) for d in (2,5,6,8,10)})
            with patch('sim.rl.g1.evaluation.parity', return_value={}), \
                    patch('sim.rl.g1.evaluation.evaluate', return_value=baseline), \
                    patch('sim.rl.g1.runner.train_seeds') as train, \
                    patch('sim.rl.g1.runner.command') as command:
                full(root, jobs=1, seeds=[3, 4])
            self.assertEqual(train.call_args.kwargs['seeds'], [3, 4])
            command.assert_not_called()
            self.assertEqual(json.loads((root/'part-complete.json').read_text())['seeds'], [3, 4])
            self.assertFalse((root/'complete.json').exists())


class CloudSplitTests(unittest.TestCase):
    def test_notebook_parameters_forwarding_and_trained_part_resume(self):
        for path in (HERE/'cloud').glob('*.ipynb'):
            with self.subTest(notebook=path.name), tempfile.TemporaryDirectory() as tmp:
                nb = json.loads(path.read_text())
                cfg = ''.join(nb['cells'][2]['source'])
                expected = [0, 1, 2] if path.name.startswith('kaggle') else [3, 4]
                self.assertIn('parameters', nb['cells'][2]['metadata']['tags'])
                # Execute only the parameter assignment, without mounting Drive.
                scope = {}
                exec(cfg.splitlines()[0], scope)
                self.assertEqual(scope['SEEDS'], expected)
                calls = []
                scope.update(SCRATCH=Path(tmp), RUN=Path(tmp)/'run', REPO=HERE.parents[2],
                             PYTHON=Path('/fixture/python'), JOBS=4, DRIVER_SOURCE='# fixture',
                             MAX_HOURS=11, SEED_WALL_CAP_MIN=None, SESSION_STARTED=0,
                             time=__import__('time'), os=__import__('os'),
                             subprocess=SimpleNamespace(run=lambda command, **kwargs:
                                 (calls.append(command) or SimpleNamespace(returncode=0))))
                exec(''.join(nb['cells'][9]['source']), scope)
                command = calls.pop()
                self.assertEqual(command[command.index('--seeds')+1], ','.join(map(str, expected)))
                exec(''.join(nb['cells'][8]['source']), scope)
                driver = {'__name__':'cloud_split_fixture'}
                exec(compile(scope['DRIVER_SOURCE'], str(path), 'exec'), driver)
                run = Path(tmp)/'g1-run'
                write_json(run/'smoke/smoke.json', dict(status='PASS'))
                def finish(command, **kwargs):
                    calls.append(command)
                    write_json(run/'part-complete.json', dict(status='TRAINED', seeds=expected, identity=identity()))
                    return SimpleNamespace(returncode=0, poll=lambda:0)
                argv = ['driver', '--out', str(run), '--jobs', '4',
                        '--seeds', ','.join(map(str, expected))]
                with patch('sys.argv', argv), patch.object(driver['subprocess'], 'Popen', side_effect=finish):
                    driver['main']()
                self.assertEqual(calls[0][-2:], ['--seeds', ','.join(map(str, expected))])
                status = json.loads((run/'cloud-status.json').read_text())
                self.assertEqual((status['status'], status['seeds']), ('TRAINED', expected))
                self.assertFalse((run/'complete.json').exists())
                with patch('sys.argv', argv), patch.object(driver['subprocess'], 'Popen') as launch:
                    driver['main']()
                    launch.assert_not_called()
                with patch('sys.argv', argv[:-1]+['0,1,2,3,4']):
                    with self.assertRaisesRegex(RuntimeError, 'source/jobs/seeds differ'):
                        driver['main']()


if __name__ == '__main__':
    unittest.main()
