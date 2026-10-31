"""Runtime cap/resume regressions using tiny real PPO updates and cloud fixtures."""
import hashlib
import json
from pathlib import Path
import pickle
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from sim.rl.g1.protocol import HERE, identity, seed_wall_cap, write_json
from sim.rl.g1.runner import full, train_seeds
from sim.rl.g1.training import G1PPO, newest, train


def tiny_config():
    cfg = json.loads((HERE/'config.json').read_text())
    cfg.update(n_envs=1, n_steps=8, batch_size=8, n_epochs=1, transitions=32)
    return cfg


class WallCapTests(unittest.TestCase):
    def test_invalid_caps(self):
        self.assertIsNone(seed_wall_cap(None))
        for cap in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                seed_wall_cap(cap)

    def test_cumulative_cap_and_unlimited_resume_past_old_90_minutes(self):
        cfg = tiny_config()
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            first = train(run, 17, seconds=.01, config=cfg, subprocess=False)
            self.assertEqual(first['completed_steps'], 8)
            dest = newest(run)
            # Simulate accumulated wall time without spending 90 minutes in a test.
            state = pickle.loads((dest/'state.pkl').read_bytes())
            state['wall_s'] = 5401
            (dest/'state.pkl').write_bytes(pickle.dumps(state))
            marker = json.loads((dest/'complete.json').read_text())
            marker['files']['state.pkl'] = hashlib.sha256((dest/'state.pkl').read_bytes()).hexdigest()
            write_json(dest/'complete.json', marker)
            capped = train(run, 17, resume=True, config=cfg, subprocess=False, seed_wall_cap_min=90)
            self.assertEqual((capped['status'], capped['segment_steps']), ('PARTIAL', 0))
            self.assertFalse((run/'failure.json').exists())
            result = train(run, 17, resume=True, config=cfg, subprocess=False)
            self.assertEqual((result['status'], result['completed_steps']), ('COMPLETE', 32))
            self.assertIsNone(result['seed_wall_cap_min'])
            self.assertGreater(result['cumulative_wall_s'], 5400)
            complete = train(run, 17, resume=True, config=cfg, subprocess=False, seed_wall_cap_min=90)
            self.assertEqual((complete['status'], complete['segment_steps']), ('COMPLETE', 0))

    def test_global_stop_checkpoints_active_update_and_blocks_queued_seeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stop = root/'STOP'
            original = G1PPO.collect_rollouts
            def collect(model, *args, **kwargs):
                result = original(model, *args, **kwargs)
                stop.touch()
                return result
            with patch.object(G1PPO, 'collect_rollouts', collect):
                receipt = train(root/'seed-0', 0, config=tiny_config(), subprocess=False, stop_file=stop)
            self.assertEqual((receipt['status'], receipt['completed_steps']), ('PARTIAL', 8))
            self.assertEqual(json.loads((newest(root/'seed-0')/'complete.json').read_text())['steps'], 8)
            with self.assertRaisesRegex(RuntimeError, 'queue STOP'):
                train_seeds(root, seeds=[1, 2], jobs=1, config=tiny_config(), require_complete=False)
            self.assertFalse((root/'seed-1/declaration.json').exists())

    def test_full_ignores_historical_throughput_gate_only_when_uncapped(self):
        # Readiness still blocks this fixture before any scientific work begins.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root/'smoke/smoke.json', dict(identity=identity(), status='PASS', jobs=1,
                       laptop_ESTIMATE=dict(throughput_gate=False, evaluation_gate=True,
                                            transitions_per_second=80)))
            with self.assertRaisesRegex(RuntimeError, 'prerequisites unresolved'):
                full(root, jobs=1)
            with self.assertRaisesRegex(RuntimeError, 'configured seed wall cap'):
                full(root, jobs=1, seed_wall_cap_min=90)


class CloudCapTests(unittest.TestCase):
    def test_notebook_configuration_and_launch_cells(self):
        for path in (HERE/'cloud').glob('*.ipynb'):
            with self.subTest(notebook=path.name), tempfile.TemporaryDirectory() as tmp:
                nb = json.loads(path.read_text())
                source = ''.join(nb['cells'][2]['source'])
                # Do not mount Drive/create service directories in a local test.
                source = '\n'.join(line for line in source.splitlines()
                                   if 'mkdir(' not in line and not line.startswith('drive.mount('))
                scope = {}
                with patch.dict('sys.modules', {'google.colab': SimpleNamespace(drive=None)}):
                    exec(source, scope)
                self.assertIsNone(scope['SEED_WALL_CAP_MIN'])
                if path.name.startswith('kaggle'):
                    self.assertEqual(scope['MAX_HOURS'], 11.5)
                for cap in (None, 240):
                    commands = []
                    scope.update(SCRATCH=Path(tmp), RUN=Path(tmp)/'g1-run', REPO=HERE.parents[2],
                                 PYTHON=Path('/fixture/python'), JOBS=4, DRIVER_SOURCE='# fixture',
                                 SEED_WALL_CAP_MIN=cap, os=__import__('os'),
                                 subprocess=SimpleNamespace(run=lambda command, **kwargs:
                                     (commands.append(command) or SimpleNamespace(returncode=0))))
                    exec(''.join(nb['cells'][9]['source']), scope)
                    command = commands[-1]
                    self.assertIn('--session-elapsed-s', command)
                    if cap is None:
                        self.assertNotIn('--seed-wall-cap-min', command)
                    else:
                        self.assertEqual(command[-2:], ['--seed-wall-cap-min', '240'])

    def test_both_notebook_supervisors_soft_stop_export_and_resume(self):
        for path in (HERE/'cloud').glob('*.ipynb'):
            with self.subTest(notebook=path.name), tempfile.TemporaryDirectory() as tmp:
                scope = {}
                nb = json.loads(path.read_text())
                for cell in nb['cells']:
                    source = ''.join(cell['source'])
                    if source.startswith('DRIVER_SOURCE'):
                        exec(source, scope)
                driver = {'__name__': 'cloud_cap_test'}
                exec(compile(scope['DRIVER_SOURCE'], str(path), 'exec'), driver)
                run = Path(tmp)/'g1-run'
                write_json(run/'smoke/smoke.json', dict(status='PASS'))
                write_json(run/'seed-0/declaration.json', {})
                # Real verified-checkpoint selection/export, mocked subprocess timing.
                dest = run/'seed-0/checkpoints/fixture'
                dest.mkdir(parents=True)
                (dest/'policy.zip').write_bytes(b'checkpoint fixture')
                write_json(dest/'complete.json', dict(steps=8, created_ns=1,
                           files={'policy.zip': hashlib.sha256(b'checkpoint fixture').hexdigest()}))
                clock = SimpleNamespace(now=0)
                clock.monotonic = lambda: clock.now
                clock.sleep = lambda seconds: setattr(clock, 'now', clock.now+seconds)
                class Process:
                    pid = 999999
                    returncode = None
                    def poll(self):
                        return self.returncode
                    def wait(self, timeout):
                        self.returncode = -15
                process = Process()
                calls = []
                def launch(command, **kwargs):
                    calls.append(command)
                    # Installation used one hour, training reaches global 11.5h.
                    clock.now = 10.5*3600
                    return process
                argv = ['driver', '--out', str(run), '--jobs', '4', '--hours', '11.5',
                        '--session-elapsed-s', '3600', '--seed-wall-cap-min', '240']
                with patch.dict(driver, time=clock), patch('sys.argv', argv), \
                        patch.object(driver['subprocess'], 'Popen', side_effect=launch), \
                        patch.object(driver['os'], 'killpg') as kill:
                    with self.assertRaises(TimeoutError):
                        driver['main']()
                self.assertTrue((run/'STOP').exists())
                self.assertTrue((run/'seed-0/STOP').exists())
                self.assertEqual(calls[0][-2:], ['--seed-wall-cap-min', '240.0'])
                self.assertIn('same code bundle', (run/'RESUME.md').read_text())
                self.assertEqual(json.loads((run/'cloud-status.json').read_text())['status'], 'PARTIAL')
                note = json.loads((run/'resume-note.json').read_text())
                self.assertEqual(note['verified_checkpoints'], 1)
                with zipfile.ZipFile(run.parent/'g1-recovery.zip') as archive:
                    self.assertIn('g1-run/RESUME.md', archive.namelist())
                    self.assertIn('g1-run/resume-note.json', archive.namelist())
                    self.assertIn('g1-run/seed-0/checkpoints/fixture/policy.zip', archive.namelist())
                # A new session records/clears STOP and passes the unlimited default.
                process.returncode = 0
                def complete(command, **kwargs):
                    calls.append(command)
                    write_json(run/'complete.json', dict(identity=identity(), status='COMPLETE'))
                    return process
                with patch('sys.argv', ['driver', '--out', str(run), '--jobs', '4']), \
                        patch.object(driver['subprocess'], 'Popen', side_effect=complete):
                    driver['main']()
                self.assertFalse(list(run.rglob('STOP')))
                self.assertNotIn('--seed-wall-cap-min', calls[-1])
                self.assertEqual(json.loads((run/'cloud-status.json').read_text())['status'], 'COMPLETE')


if __name__ == '__main__':
    unittest.main()
