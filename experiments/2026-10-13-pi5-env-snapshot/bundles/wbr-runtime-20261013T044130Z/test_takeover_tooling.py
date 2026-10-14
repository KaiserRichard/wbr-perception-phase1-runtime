"""Synthetic rejection tests. No camera, sysfs scan or benchmark writes."""
import copy
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import image_content
import n3_record
from n1_precheck import evaluate_usb
from n3_observer import qos_failures
from phase_gate import completed_capture, validate_review, REVIEW_FIELDS
from storage_qualify import assess_benchmark, evaluate_mount_snapshot, GIB
from validation_common import ACTIVE_UNIT, evidence_hashes, verify_evidence, write_json
from wrapper_inspect import validate_readback


def mount_fixture():
    return {'euid': 1000, 'symlink_component': False, 'mount_st_dev': 8, 'root_st_dev': 179,
            'device_is_block': True, 'device_major_minor': '8:1', 'mount_major_minor': '8:1',
            'writable': True, 'free_bytes': 30 * GIB, 'mount_inode': 2,
            'findmnt': {'filesystems': [{'target': '/mnt/synthetic', 'source': '/dev/sda1',
                'uuid': 'SYNTHETIC', 'fstype': 'ext4', 'options': 'rw,relatime', 'maj:min': '8:1'}]},
            'lsblk': {'blockdevices': [{'path': '/dev/sda1', 'type': 'part', 'ro': False,
                'children': [{'path': '/dev/sda', 'type': 'disk', 'ro': False, 'tran': 'usb',
                              'model': 'SYNTHETIC', 'serial': 'SYNTHETIC'}]}]}}


class StorageTests(unittest.TestCase):
    def test_qualified_identity_and_rejected_mounts(self):
        base = mount_fixture()
        self.assertEqual(evaluate_mount_snapshot(base, '/mnt/synthetic', 'SYNTHETIC', '/dev/sda1')['uuid'], 'SYNTHETIC')
        for key, value in [('euid', 0), ('symlink_component', True), ('mount_st_dev', 179),
                           ('device_is_block', False), ('mount_major_minor', '179:2'),
                           ('writable', False), ('free_bytes', GIB)]:
            fixture = copy.deepcopy(base); fixture[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                evaluate_mount_snapshot(fixture, '/mnt/synthetic', 'SYNTHETIC', '/dev/sda1')
        for key, value in [('source', '/dev/mmcblk0p2'), ('uuid', 'OLD-UUID'), ('options', 'ro'), ('target', '/')]:
            fixture = copy.deepcopy(base); fixture['findmnt']['filesystems'][0][key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                evaluate_mount_snapshot(fixture, '/mnt/synthetic', 'SYNTHETIC', '/dev/sda1')
        fixture = copy.deepcopy(base); fixture['lsblk']['blockdevices'][0]['children'][0]['tran'] = 'mmc'
        with self.assertRaises(RuntimeError):
            evaluate_mount_snapshot(fixture, '/mnt/synthetic', 'SYNTHETIC', '/dev/sda1')

    def test_slow_short_corrupt_nonfinite_benchmark_rejected(self):
        sample = [{'decimal_MB_per_second': 20, 'fsync_seconds': .1}]
        self.assertEqual(assess_benchmark(sample, 2 * GIB, 100, True)['failures'], [])
        for samples, volume, seconds, checksum in [
            ([{'decimal_MB_per_second': .944, 'fsync_seconds': 1}], GIB, 100, True),
            (sample, GIB, 5, True), (sample, 2 * GIB, 100, False), ([], 0, 0, True)]:
            self.assertTrue(assess_benchmark(samples, volume, seconds, checksum)['failures'])
        with self.assertRaises(ValueError):
            assess_benchmark(sample, GIB, float('nan'), True)


class EvidenceTests(unittest.TestCase):
    def test_missing_changed_and_escaping_hashes_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); data = root / 'raw.txt'; data.write_text('synthetic')
            result = root / 'result.json'; write_json(result, {'evidence_sha256': evidence_hashes(root)})
            verify_evidence(result)
            data.write_text('changed')
            with self.assertRaises(RuntimeError): verify_evidence(result)
            result.write_text('{}')
            with self.assertRaises(RuntimeError): verify_evidence(result)

    def test_review_is_explicit(self):
        review = {key: True for key in REVIEW_FIELDS}
        review.update({key: 'synthetic review' for key in ('reviewer', 'notes', 'power_supply', 'cooling', 'scene', 'calibration_provenance')})
        review['utc'] = datetime.now(timezone.utc).isoformat()
        validate_review(review)
        review['raw_logs_clean'] = 'yes'
        with self.assertRaises(RuntimeError): validate_review(review)

    def test_105_seconds_never_substitutes_for_soak(self):
        fixture = {'stage': 'N2_REPRODUCTION', 'duration_requested_seconds': 105,
                   'automatic_checks_pass': True, 'failures': [], 'sdk_returncode': 0,
                   'sdk_orderly_shutdown': True, 'n1_sha256': 'synthetic'}
        with patch('phase_gate.verify_evidence', return_value=fixture), self.assertRaises(RuntimeError):
            completed_capture(Path('/synthetic/result.json'), 300, 'synthetic')

    def test_no_camera_flags_block_entry_points(self):
        root = Path(__file__).parent
        commands = [('n1_precheck.py', ['--output', '/not-created']),
                    ('phase_gate.py', ['n2', '--seconds', '20', '--n1-result', '/absent', '--output', '/not-created']),
                    ('n3_observer.py', ['--mode', 'live', '--output', '/not-created']),
                    ('n3_record.py', ['--n1-result', '/absent', '--n2-result', '/absent', '--storage-result', '/absent',
                                      '--bag', '/not-created', '--output', '/not-created'])]
        for name, argv in commands:
            with self.subTest(script=name):
                result = subprocess.run([sys.executable, str(root/name), *argv], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('CAMERA AVAILABLE', result.stderr)

    def test_recorder_never_uses_all_topics(self):
        from n3_metrics import read_topics
        argv = n3_record.recorder_argv(Path('/synthetic/bag'), read_topics())
        self.assertNotIn('-a', argv); self.assertNotIn('--all', argv)
        self.assertEqual(argv[argv.index('--topics')+1:], [s['name'] for s in read_topics()])
        self.assertNotIn('/camera/camera/imu', argv)

    def test_parameter_fallback_and_latched_qos_rejected(self):
        expected = {'gyro_fps': 200, 'serial_no': ACTIVE_UNIT['device_serial'], 'enable_infra': False}
        self.assertEqual(validate_readback({'gyro_fps': 200, 'serial_no': ACTIVE_UNIT['device_serial']}, expected), [])
        self.assertTrue(validate_readback({'gyro_fps': 400, 'serial_no': int(ACTIVE_UNIT['device_serial'])}, expected))
        specs = [{'name': '/tf_static', 'latched': True}]
        self.assertTrue(qos_failures({'/tf_static': [{'reliability': 'BEST_EFFORT', 'durability': 'VOLATILE'}]}, specs))

    def test_nonfinite_usb_speed_is_not_superspeed(self):
        self.assertTrue(evaluate_usb({'idVendor': '8086', 'idProduct': '0b3a', 'speed_mbps': float('nan'),
                                      'sysfs_name': '5-1', 'usb_descriptor_serial': None}, True))


class ImageTests(unittest.TestCase):
    def test_full_content_and_frozen_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (root/'frames.csv').open('w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow('frame_number,stamp_ms,domain,width,height,stride,bytes,saved_file'.split(','))
                for i in range(1, 181):
                    name = f'synthetic-{i}.pgm' if i in (30, 90, 150) else ''
                    writer.writerow([i, i*1000/15, 'Hardware Clock', 640, 480, 640, 307200, name])
                    if name:
                        (root/name).write_bytes(b'P5\n640 480\n255\n' + bytes((x+i)%256 for x in range(256))*1200)
            self.assertTrue(image_content.analyze(root)['automatic_checks_pass'])
            for path in root.glob('*.pgm'):
                path.write_bytes(b'P5\n640 480\n255\n' + b'\x00'*307200)
            self.assertFalse(image_content.analyze(root)['automatic_checks_pass'])


if __name__ == '__main__':
    unittest.main()
