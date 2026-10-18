"""Offline regression coverage for defects confirmed by the R_T15 review."""
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_n4a_timing as fixtures
from test_n4a_timing import HERE, REPO, RUNNER, ANALYZER, FIXTURE, load_module, timing

analysis = load_module('n4a_review_analysis', ANALYZER)


class ReviewTests(unittest.TestCase):
    make_platform = fixtures.N4ATimingTests.make_platform
    make_config = fixtures.N4ATimingTests.make_config
    make_stubs = fixtures.N4ATimingTests.make_stubs
    create_inputs = fixtures.N4ATimingTests.create_inputs
    command = fixtures.N4ATimingTests.command

    def saved_run(self, root):
        exp = root / 'experiment'; exp.mkdir()
        shutil.copy2(HERE / 'config.json', exp / 'config.json')
        (exp / 'provenance.json').write_text(json.dumps({'runs': 1}))
        (exp / 'preflight.json').write_text(json.dumps({'status': 'PASS', 'criteria': []}))
        run = exp / 'run01'; engine = run / 'accuracy/run01'; engine.mkdir(parents=True)
        (run / 'capture.json').write_text(json.dumps({'check_status': 'PASS'}))
        (engine / 'exit_code.txt').write_text('0\n')
        (engine / 'stdout.log').write_text('IMU initialized\n')
        for name in ('throttled_before.txt', 'throttled_after.txt'):
            (engine / name).write_text('throttled=0x0\n')
        # SYNTHETIC 20 Hz EuRoC time base, non-collinear exact trajectory.
        gt = root / 'gt.csv'; times = root / 'times.txt'
        stamps = [1403636579000000000 + i * 50000000 for i in range(20)]
        positions = [(i / 10, (i % 4) / 10, (i % 3) / 10) for i in range(20)]
        times.write_text(''.join(f'{t}\n' for t in stamps))
        gt.write_text(''.join(f'{t},{x},{y},{z},1,0,0,0\n' for t, (x,y,z) in zip(stamps, positions)))
        (engine / 'f_test.txt').write_text(''.join(f'{t} {x} {y} {z} 0 0 0 1\n' for t, (x,y,z) in zip(stamps, positions)))
        profile = run / 'profile'; profile.mkdir()
        with FIXTURE.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        row = rows[0]
        row['throttled_raw'] = '0x0'
        for key in row:
            if key.startswith(('undervoltage_', 'frequency_capped_', 'throttled_', 'soft_temperature_limit_')) and key != 'throttled_raw':
                row[key] = '0'
        with (profile / 'samples.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=row); writer.writeheader(); writer.writerow(row)
        (profile / 'metadata.json').write_text(json.dumps({'sample_count': 1}))
        (profile / 'run_tracking.csv').write_text('image_s,state,imu_initialized,imu_samples,track_ms\n1,2,1,4,10\n2,2,1,4,20\n')
        return exp, run, engine, profile, gt, times

    def analyze(self, data):
        exp, _, _, _, gt, times = data
        proc = self.command([sys.executable, str(ANALYZER), '--analyze-only', str(exp),
                             '--sequence', 'MH01', '--ground-truth', str(gt), '--times', str(times)])
        self.assertNotIn('Traceback', proc.stdout)
        self.assertTrue((exp / 'result.json').is_file(), proc.stdout)
        result = json.loads((exp / 'result.json').read_text())
        for key in ('started_utc', 'ended_utc', 'host', 'criteria', 'raw_files', 'notes'):
            self.assertIn(key, result)
        return proc, result

    def test_default_tools_valid_and_repeatable(self):
        with tempfile.TemporaryDirectory() as td:
            data = self.saved_run(Path(td))
            for _ in range(2):
                proc, result = self.analyze(data)
                self.assertEqual(proc.returncode, 0, proc.stdout)
                self.assertEqual(result['status'], 'PASS')
                self.assertEqual(result['aggregate']['latency_p95_ms']['mean'], 20)
                self.assertEqual(result['valid_run_count'], 1)

    def test_missing_evidence_blocks(self):
        for name in ('preflight', 'capture', 'samples', 'metadata', 'latency', 'ground_truth', 'times', 'config'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                data = self.saved_run(Path(td)); exp, run, _, profile, gt, times = data
                paths = {'preflight': exp / 'preflight.json', 'capture': run / 'capture.json',
                         'samples': profile / 'samples.csv', 'metadata': profile / 'metadata.json',
                         'latency': profile / 'run_tracking.csv', 'ground_truth': gt,
                         'times': times, 'config': exp / 'config.json'}
                paths[name].unlink()
                proc, result = self.analyze(data)
                self.assertEqual(proc.returncode, 2, proc.stdout)
                self.assertEqual(result['status'], 'BLOCKED')
                self.assertEqual(result['valid_run_count'], 0)
                self.assertTrue(result['excluded_runs'][0]['reasons'])

    def test_missing_declared_repetition_blocks_overall(self):
        with tempfile.TemporaryDirectory() as td:
            data = self.saved_run(Path(td)); exp = data[0]
            (exp / 'provenance.json').write_text(json.dumps({'runs': 2}))
            proc, result = self.analyze(data)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(result['valid_run_count'], 1)
            self.assertEqual(result['criteria'][-1]['status'], 'BLOCKED')
            self.assertEqual(result['missing_runs'], ['run02'])

    def test_no_runs_writes_blocked_result(self):
        with tempfile.TemporaryDirectory() as td:
            data = self.saved_run(Path(td)); shutil.rmtree(data[1])
            proc, result = self.analyze(data)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(result['status'], 'BLOCKED')

    def test_engine_failure_and_post_run_throttle_fail(self):
        for field in ('engine', 'post_throttle', 'prior_throttle'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                data = self.saved_run(Path(td)); exp, _, engine, _, _, _ = data
                if field == 'engine':
                    (engine / 'exit_code.txt').write_text('9\n')
                elif field == 'post_throttle':
                    (engine / 'throttled_after.txt').write_text('throttled=0x50000\n')
                else:
                    (exp / 'preflight.json').write_text(json.dumps({'status': 'PASS', 'prior_throttle_allowed': True,
                        'criteria': [{'id': 'no_prior_throttle_bits', 'measured': {'invalid_bits_set': [16]}}]}))
                proc, result = self.analyze(data)
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertEqual(result['valid_run_count'], 0)
                self.assertTrue(result['excluded_runs'][0]['reasons'])
                if field in ('prior_throttle', 'post_throttle'):
                    self.assertEqual(result['runs'][0]['throttle_status'], 'FAIL')

    def test_mismatched_sample_count_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            data = self.saved_run(Path(td))
            (data[3] / 'metadata.json').write_text(json.dumps({'sample_count': 7}))
            proc, result = self.analyze(data)
            self.assertEqual(proc.returncode, 2)
            self.assertIn('sampler_metadata_blocked', result['excluded_runs'][0]['reasons'])

    def test_missing_tools_block_without_stale_results(self):
        with tempfile.TemporaryDirectory() as td:
            data = self.saved_run(Path(td)); exp, _, _, _, gt, times = data
            proc, _ = self.analyze(data); self.assertEqual(proc.returncode, 0, proc.stdout)
            proc = self.command([sys.executable, str(ANALYZER), '--experiment', str(exp), '--sequence', 'MH01',
                '--ground-truth', str(gt), '--times', str(times), '--accuracy-tool', str(exp / 'absent.py'),
                '--profile-tool', str(exp / 'absent.py')])
            self.assertEqual(proc.returncode, 2, proc.stdout)
            self.assertEqual(json.loads((exp / 'result.json').read_text())['valid_run_count'], 0)

    def test_stale_latency_is_not_used(self):
        with tempfile.TemporaryDirectory() as td:
            data = self.saved_run(Path(td)); profile = data[3]
            proc, _ = self.analyze(data); self.assertEqual(proc.returncode, 0, proc.stdout)
            (profile / 'run_tracking.csv').write_text('broken\n')
            proc, result = self.analyze(data)
            self.assertEqual(proc.returncode, 2, proc.stdout)
            self.assertIsNone(result['runs'][0]['latency_p95_ms'])
            self.assertEqual(result['runs'][0]['latency_status'], 'BLOCKED')

    def test_event_latency_session_schema_and_loss(self):
        for loss, unpaired in ((0, False), (1, False), (0, True)):
            with self.subTest(loss=loss, unpaired=unpaired), tempfile.TemporaryDirectory() as td:
                data = self.saved_run(Path(td)); profile = data[3]
                (profile / 'run_tracking.csv').unlink()
                (profile / 'events.csv').write_text(
                    f'# observer_loss overwritten={loss} contention=0 invalid=0 clock_errors=0\n'
                    'host_ns,host_domain,host_session,frame_id,event,source_ns,source_domain,source_session,reason,depth\n'
                    '1,host_steady,run,1,frame_received,,,,,\n'
                    '2,host_steady,run,1,track_start,,,,,\n'
                    '10000002,host_steady,run,1,track_end,,,,,\n'
                    '10000003,host_steady,run,1,snapshot_published,,,,,\n' + (
                    '10000004,host_steady,run,2,track_start,,,,,\n'
                    '20000004,host_steady,run,3,track_end,,,,,\n' if unpaired else ''))
                proc, result = self.analyze(data)
                self.assertEqual(proc.returncode, 0 if loss == 0 and not unpaired else 2, proc.stdout)
                self.assertEqual(result['runs'][0]['latency_p95_ms'], 10)
                self.assertEqual(result['valid_run_count'], 1 if loss == 0 and not unpaired else 0)

    def test_empty_or_nonfinite_latency_blocks(self):
        for latency in ({'frame_count': 0, 'tracking_latency_ns': {}},
                        {'frame_count': 1, 'tracking_latency_ns': {'p50': 1, 'p95': float('nan'), 'p99': 3}},
                        {'frame_count': 1, 'tracking_latency_ns': {'p50': 3, 'p95': 2, 'p99': 1}}):
            self.assertEqual(analysis.latency_values(latency), (None, None, None, None))

    def preflight_args(self, root, platform, config, extra=()):
        return ['bash', str(RUNNER), '--preflight-only', '--config', str(config),
                '--thermal-root', str(platform['thermal']), '--governor-root', str(platform['governors']),
                '--vcgencmd', str(platform['vcgencmd']), '--lock-file', str(root / 'lock'), *extra,
                '/bin/sleep', 'vocab', 'settings', 'dataset', 'times', 'MH01', '1', str(root / 'experiment')]

    def test_preflight_replay_without_hardware_and_verbatim_raw(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); platform = self.make_platform(root); config = self.make_config(root)
            platform['vcgencmd'].write_text("#!/bin/sh\nprintf 'throttled=0x0'\n")
            proc = self.command(self.preflight_args(root, platform, config))
            self.assertEqual(proc.returncode, 0, proc.stdout)
            exp = root / 'experiment'; raw = exp / 'throttled_before.txt'
            self.assertEqual(raw.read_bytes(), b'throttled=0x0')
            shutil.rmtree(root / 'sys'); platform['vcgencmd'].unlink()
            proc = self.command(['bash', str(RUNNER), '--analyze-only=' + str(exp)])
            self.assertEqual(proc.returncode, 0, proc.stdout)
            self.assertEqual(raw.read_bytes(), b'throttled=0x0')
            (exp / 'temperature.txt').unlink()
            proc = self.command(['bash', str(RUNNER), '--analyze-only', str(exp)])
            self.assertEqual(proc.returncode, 2, proc.stdout)
            self.assertEqual(json.loads((exp / 'result.json').read_text())['status'], 'BLOCKED')
            (exp / 'config.json').unlink()
            proc = self.command(['bash', str(RUNNER), '--analyze-only', str(exp)])
            self.assertEqual(proc.returncode, 2, proc.stdout)
            self.assertEqual(json.loads((exp / 'result.json').read_text())['status'], 'BLOCKED')

    def test_preflight_hot_governor_missing_vcgencmd_and_busy_lock(self):
        for condition, rc in (('hot', 1), ('governor', 1), ('missing_vc', 2), ('busy_lock', 1), ('unknown_governor', 2), ('unknown_cooling', 2)):
            with self.subTest(condition=condition), tempfile.TemporaryDirectory() as td:
                root = Path(td); platform = self.make_platform(root); config = self.make_config(root)
                if condition == 'hot':
                    (platform['thermal'] / 'thermal_zone0/temp').write_text('70000')
                if condition in ('governor', 'unknown_governor'):
                    (platform['governors'] / 'cpu0/cpufreq/scaling_governor').write_text(
                        'powersave' if condition == 'governor' else '')
                if condition == 'missing_vc': platform['vcgencmd'].unlink()
                if condition == 'unknown_cooling': (platform['thermal'] / 'cooling_device0').mkdir()
                with (root / 'lock').open('w') as lock:
                    if condition == 'busy_lock': timing.fcntl.flock(lock, timing.fcntl.LOCK_EX)
                    proc = self.command(self.preflight_args(root, platform, config, ['--require-performance', '--wait-for-cooldown']))
                self.assertEqual(proc.returncode, rc, proc.stdout)
                self.assertFalse((root / 'experiment/run01').exists())

    def capture(self, root, stubs, platform, config, runs=1):
        inputs = self.create_inputs(root)
        return self.command(['bash', str(RUNNER), '--config', str(config), '--accuracy-runner', str(stubs['runner']),
            '--profile-tool', str(stubs['sampler']), '--thermal-root', str(platform['thermal']),
            '--governor-root', str(platform['governors']), '--vcgencmd', str(platform['vcgencmd']),
            '--lock-file', str(root / 'lock'), str(inputs['binary']), str(inputs['vocab']), str(inputs['settings']),
            str(inputs['dataset']), str(inputs['times']), 'MH01', str(runs), str(root / 'experiment')],
            env=dict(os.environ, N4A_ORB_PID_FILE=str(root / 'orb.pid')))

    def test_sampler_crash_blocks_capture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); platform = self.make_platform(root); config = self.make_config(root); stubs = self.make_stubs(root)
            stubs['sampler'].write_text('raise SystemExit(7)\n')
            proc = self.capture(root, stubs, platform, config)
            self.assertEqual(proc.returncode, 2, proc.stdout)
            result = json.loads((root / 'experiment/result.json').read_text())
            self.assertEqual(result['status'], 'BLOCKED')

    def test_capture_engine_failure_and_missing_pid(self):
        for condition, rc in (('engine', 1), ('missing_pid', 2)):
            with self.subTest(condition=condition), tempfile.TemporaryDirectory() as td:
                root = Path(td); platform = self.make_platform(root); config = self.make_config(root); stubs = self.make_stubs(root)
                if condition == 'engine':
                    with stubs['runner'].open('a') as stream:
                        stream.write('printf "9\\n" > "$out/run01/exit_code.txt"\n')
                else:
                    stubs['runner'].write_text('#!/bin/bash\nset -euo pipefail\nmkdir -p "$8/run01"\nprintf "0\\n" > "$8/run01/exit_code.txt"\n')
                proc = self.capture(root, stubs, platform, config)
                self.assertEqual(proc.returncode, rc, proc.stdout)
                self.assertEqual(json.loads((root / 'experiment/result.json').read_text())['status'], 'FAIL' if rc == 1 else 'BLOCKED')

    def test_inter_run_preflight_refuses_hot_second_run(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); platform = self.make_platform(root); config = self.make_config(root); stubs = self.make_stubs(root)
            with stubs['runner'].open('a') as stream:
                stream.write(f"printf '71000' > '{platform['thermal']}/thermal_zone0/temp'\n")
            proc = self.capture(root, stubs, platform, config, runs=2)
            self.assertEqual(proc.returncode, 1, proc.stdout)
            receipt = json.loads((root / 'experiment/run02/capture.json').read_text())
            self.assertEqual(receipt['reason'], 'inter_run_preflight_refused')
            self.assertFalse((root / 'experiment/run02/accuracy').exists())

    def test_proc_parent_with_spaces_and_parentheses(self):
        with patch.object(Path, 'read_text', return_value='42 (name with ) space) S 19 0 0'):
            self.assertEqual(timing.parent_pid(42), 19)

    def test_usage_and_invalid_config_exit_three(self):
        self.assertEqual(self.command(['bash', str(RUNNER)]).returncode, 3)
        self.assertEqual(self.command([sys.executable, str(ANALYZER)]).returncode, 3)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); platform = self.make_platform(root); config = self.make_config(root)
            config.write_text('broken')
            proc = self.command(self.preflight_args(root, platform, config))
            self.assertEqual(proc.returncode, 3, proc.stdout)
            self.assertNotIn('Traceback', proc.stdout)
