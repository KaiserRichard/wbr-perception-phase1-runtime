#!/usr/bin/env python3
"""Offline tooling tests. Synthetic fixtures are NOT physical camera evidence."""
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import image_content
import kernel_analysis
import sdk_analysis
import sdk_capture
import phase_gate
from health_monitor import failures as health_failures
from validation_common import EXPECTED_CAMERA, evidence_hashes, write_json


def fixture(seconds=2):
    """Synthetic v2.58.4-format constant-rate stream with exact baseline profiles."""
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Configuration:"])
    writer.writerow(sdk_analysis.CONFIG_HEADER)
    writer.writerows(sorted(sdk_analysis.PROFILES))
    for name, hz in (("Infrared", 15), ("Gyro", 200), ("Accel", 100)):
        writer.writerow(sdk_analysis.SAMPLE_HEADER + ([] if name == "Infrared" else ["3DOF_x", "3DOF_y", "3DOF_z"]))
        for index in range(seconds * hz):
            stamp_ms = (index + .5) / hz * 1000
            writer.writerow([name, sdk_analysis.EXPECTED[name]["index"], index + 1, stamp_ms, stamp_ms]
                            + ([] if name == "Infrared" else [0.1, 0.2, 0.3]))
    return stream.getvalue()


class SDKAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wbr-synthetic-n2-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic-frames.csv"

    def analyze(self, text):
        self.path.write_text(text)
        return sdk_analysis.analyze(self.path, 2)

    def test_full_interval_and_exact_profile(self):
        result = self.analyze(fixture())
        self.assertTrue(result["automatic_checks_pass"])
        self.assertEqual(result["whole_request"]["Infrared"]["whole_window_hz"], 15)
        self.assertEqual(result["whole_request"]["Gyro"]["whole_window_hz"], 200)
        self.assertEqual(result["verdict"], "REVIEW_REQUIRED")
        self.assertIn("NOT DECIDED", result["N2"])

    def test_synthetic_300_second_soak_uses_whole_interval(self):
        self.path.write_text(fixture(300))
        result = sdk_analysis.analyze(self.path, 300)
        self.assertTrue(result['automatic_checks_pass'])
        self.assertEqual(result['whole_request']['Infrared']['count'], 4500)
        self.assertEqual(result['whole_request']['Gyro']['count'], 60000)
        self.assertEqual(result['whole_request']['Accel']['count'], 30000)
        self.assertEqual(len(result['interior_windows']), 9)
        self.assertIn('NOT DECIDED', result['N2'])

    def test_burst_does_not_pass_full_window(self):
        rows = list(csv.reader(io.StringIO(fixture())))
        rows = [r for r in rows if not r or r[0] not in sdk_analysis.EXPECTED or len(r) < 5
                or r[1] not in ("0", "1") or float(r[4]) < 1000]
        output = io.StringIO()
        csv.writer(output).writerows(rows)
        self.assertFalse(self.analyze(output.getvalue())["automatic_checks_pass"])

    def test_repeat_backward_missing_and_unexpected_stream_fail(self):
        for mutate in (lambda r: r.__setitem__(3, "0"), lambda r: r.__setitem__(2, "999"),
                       lambda r: r.__setitem__(4, "0")):
            rows = list(csv.reader(io.StringIO(fixture())))
            selected = [r for r in rows if r and r[0] == "Infrared" and r[1] == "1"]
            mutate(selected[10])
            output = io.StringIO()
            csv.writer(output).writerows(rows)
            self.assertFalse(self.analyze(output.getvalue())["automatic_checks_pass"])
        with self.assertRaisesRegex(ValueError, "Unexpected stream"):
            self.analyze(fixture() + "Depth,0,1,1,1\n")

    def test_nonfinite_or_wrong_profile_rejected(self):
        for text in (fixture().replace("Y8,15,640,480", "Y8,30,640,480"),
                     fixture().replace("0.1,0.2,0.3", "nan,0.2,0.3", 1),
                     fixture().replace("Infrared 1,Infrared", "Infrared 2,Infrared"), ""):
            with self.assertRaises(ValueError):
                self.analyze(text)

    def test_startup_gap_is_explicit_review_not_loss_exemption(self):
        rows = [{"stamp": n / 200, "arrival": .1 + n / 200, "frame": n + 1, "vector": [0., 0., 0.]}
                for n in range(390)]
        result = sdk_analysis.window(rows, 0., 2., sdk_analysis.EXPECTED["Gyro"], setup_boundary=True)
        self.assertTrue(result["setup_boundary_review_required"])
        self.assertEqual(result["start_boundary_gap_seconds"], .1)
        self.assertTrue(result["automatic_checks_pass"])
        strict = sdk_analysis.window(rows, 0., 2., sdk_analysis.EXPECTED["Gyro"])
        self.assertFalse(strict["automatic_checks_pass"])

    def test_analyzer_cli_failure_is_nonzero_and_additive(self):
        self.path.write_text("")
        output = self.path.parent / "analysis.json"
        result = subprocess.run([sys.executable, str(Path(sdk_analysis.__file__)), str(self.path),
                                 "--duration", "300", "--output", str(output)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(output.read_text())["verdict"], "FAIL")
        existing = output.read_bytes()
        subprocess.run([sys.executable, str(Path(sdk_analysis.__file__)), str(self.path),
                        "--duration", "300", "--output", str(output)], capture_output=True)
        self.assertEqual(output.read_bytes(), existing)


class KernelAndHealthTests(unittest.TestCase):
    def test_usb2_reset_disconnect_and_corruption_are_faults(self):
        text = ("usb 4-1: reset SuperSpeed USB device number 2 using xhci_hcd\n"
                "usb 4-1: USB disconnect, device number 2\n"
                "usb 4-1: new high-speed USB device number 3 using xhci_hcd\n"
                "Incomplete video frame\nxhci_hcd: host controller not responding\n")
        result = kernel_analysis.classify(text)
        self.assertFalse(result["automatic_checks_pass"])
        self.assertEqual(len(result["faults"]), 5)

    def test_calibration_warning_preserved_separately(self):
        result = kernel_analysis.classify("IMU Calibration is not available, default intrinsic and extrinsic will be used.")
        self.assertTrue(result["automatic_checks_pass"])
        self.assertEqual(len(result["calibration_warnings"]), 1)
        self.assertFalse(result["vio_calibration_qualified"])
        self.assertTrue(result["raw_log_review_required"])

    def test_historical_logs_are_analysis_only(self):
        root = Path(__file__).parent
        result = kernel_analysis.classify((root / "sustained-sdk.log").read_text())
        self.assertTrue(result["automatic_checks_pass"])
        self.assertEqual(len(result["calibration_warnings"]), 1)
        summary = json.loads((root / "sustained-analysis.json").read_text())
        self.assertEqual(summary["all_received_samples"]["Infrared"]["count"], 1573)
        self.assertIn("NOT DECIDED", summary["N2"])

    def test_health_nonzero_flags_fail(self):
        sample = {"throttled_value": 0, "temperature_c": 60, "vcgencmd_temperature_c": 60,
                  "memory_available_kib": 1024**2, "storage_free_bytes": 1024**3}
        self.assertEqual(health_failures(sample), [])
        sample["throttled_value"] = 0x50000
        self.assertTrue(health_failures(sample))
        self.assertEqual(health_failures(sample, True), [])
        sample['throttled_value'] = 0x50005
        self.assertTrue(health_failures(sample, True))
        sample['throttled_value'] = 0x100000
        self.assertTrue(health_failures(sample, True))


class ImageAndGuardTests(unittest.TestCase):
    def test_synthetic_capture_records_diagnostic_mode_and_stops_on_live_flags(self):
        # Owned processes, health samples and every Pi operation are synthetic.
        for diagnostic, flags, verdict in ((True, 0x50000, 'OPEN_DIAGNOSTIC'),
                                           (False, 0x50000, 'FAIL'), (True, 0x50005, 'FAIL')):
            with self.subTest(diagnostic=diagnostic, flags=flags), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                n1_path = root / 'synthetic-n1.json'
                n1_path.write_text('synthetic N1 input')
                binary = root / 'synthetic-sdk'
                binary.write_text('synthetic; never executed')
                args = SimpleNamespace(n1_result=n1_path, sdk_binary=binary, image_sampler=None,
                                       output=root / 'capture', seconds=20, diagnostic_latched_power=diagnostic)
                n1 = {'camera': dict(EXPECTED_CAMERA), 'throttled_raw': 'throttled=0x0'}
                follower = Mock()
                follower.poll.return_value = None
                collector = Mock(pid=123)
                collector.poll.side_effect = [None] * 20 + [0]
                collector.wait.return_value = 0
                def start(argv, **kwargs):
                    if argv[0] == str(binary):
                        kwargs['stdout'].write('Task completed\n')
                        kwargs['stdout'].flush()
                        return collector
                    return follower
                sampler = Mock()
                counter = iter(range(100))
                def sample(pid=None):
                    return {'monotonic_seconds': next(counter), 'throttled_raw': f'throttled={hex(flags)}',
                            'throttled': hex(flags), 'throttled_value': flags,
                            'temperature_c': 60, 'vcgencmd_temperature_c': 60,
                            'memory_available_kib': 524288, 'storage_free_bytes': 1024**3}
                sampler.sample.side_effect = sample
                with patch.object(sdk_capture, 'require_n1', return_value=n1) as require, \
                        patch.object(sdk_capture, 'owners'), patch.object(sdk_capture, 'validate_camera'), \
                        patch.object(sdk_capture, 'HealthSampler', return_value=sampler), \
                        patch.object(sdk_capture, 'snapshot', return_value={k: {'returncode': 0} for k in ('lsusb', 'usb_tree', 'storage')}), \
                        patch.object(sdk_capture, 'provenance', return_value={}), \
                        patch.object(sdk_capture.platform, 'platform', return_value='synthetic platform'), \
                        patch.object(sdk_capture, 'command', return_value={'returncode': 0, 'stdout': 'synthetic', 'stderr': ''}), \
                        patch.object(sdk_capture, 'analyze_csv', return_value={'automatic_checks_pass': True, 'setup_boundary_review_required': False}), \
                        patch.object(sdk_capture, 'stop_child', return_value='SIGINT'), \
                        patch.object(sdk_capture.subprocess, 'Popen', side_effect=start), patch.object(sdk_capture.os, 'access', return_value=True), \
                        patch.object(sdk_capture.signal, 'signal'), patch.object(sdk_capture.time, 'sleep'), \
                        patch.object(Path, 'read_text', autospec=True) as read_text, patch('builtins.print'):
                    original_read = io.open
                    def read(p, *a, **kw):
                        if str(p) == '/proc/sys/kernel/random/boot_id': return 'synthetic-boot'
                        if str(p) == '/etc/os-release': return 'synthetic OS'
                        with original_read(p, 'r', **kw) as handle: return handle.read()
                    read_text.side_effect = read
                    code = sdk_capture.run_capture(args)
                    require.assert_called_once_with(n1_path, diagnostic_latched_power=diagnostic)
                result = json.loads((args.output / 'capture-result.json').read_text())
                self.assertEqual(result['verdict'], verdict)
                self.assertEqual(code, 0 if verdict == 'OPEN_DIAGNOSTIC' else 1)
                self.assertEqual(result['power_mode'], 'diagnostic_latched_history' if diagnostic else 'strict')
                self.assertEqual(result['throttled_raw'], f'throttled={hex(flags)}')
                self.assertIn(f'throttled={hex(flags)}', result['throttled_samples_raw'])

    def test_synthetic_n1_new_identity_and_explicit_diagnostic_receipt(self):
        with tempfile.TemporaryDirectory(prefix='wbr-synthetic-n1-') as temp:
            root = Path(temp)
            (root / 'raw.txt').write_text('synthetic only')
            path = root / 'result.json'
            base = {'stage': 'N1_PRECHECK', 'verdict': 'PASS', 'failures': [],
                    'utc_end': datetime.now(timezone.utc).isoformat(), 'hostname': sdk_capture.socket.gethostname(),
                    'boot_id': 'synthetic-boot', 'camera': {**EXPECTED_CAMERA, 'speed_mbps': 5000},
                    'power_mode': 'strict', 'throttled_raw': 'throttled=0x0',
                    'evidence_sha256': evidence_hashes(root)}
            original_read = Path.read_text
            def read_text(p, *args, **kwargs):
                return 'synthetic-boot' if str(p) == '/proc/sys/kernel/random/boot_id' else original_read(p, *args, **kwargs)
            with patch.object(Path, 'read_text', read_text), patch.object(sdk_capture, 'validate_camera') as validate:
                write_json(path, base)
                self.assertEqual(sdk_capture.require_n1(path)['camera'], base['camera'])
                validate.assert_called_once()
                old = {**base, 'camera': {**base['camera'], 'device_serial': '243322073847',
                                       'asic_serial': '251843061466', 'firmware_update_id': '251843061466'}}
                path.write_text(json.dumps(old))
                with self.assertRaisesRegex(ValueError, 'identity'):
                    sdk_capture.require_n1(path)
                missing_imu = {**base, 'camera': {k: v for k, v in base['camera'].items() if k != 'imu_type'}}
                path.write_text(json.dumps(missing_imu))
                with self.assertRaisesRegex(ValueError, 'identity'):
                    sdk_capture.require_n1(path)
                diagnostic = {**base, 'verdict': 'OPEN_DIAGNOSTIC', 'power_mode': 'diagnostic_latched_history',
                              'throttled_raw': 'throttled=0x50000'}
                path.write_text(json.dumps(diagnostic))
                with self.assertRaisesRegex(ValueError, 'N1 is not PASS'):
                    sdk_capture.require_n1(path)
                self.assertEqual(sdk_capture.require_n1(path, diagnostic_latched_power=True)['verdict'], 'OPEN_DIAGNOSTIC')
                diagnostic['throttled_raw'] = 'throttled=0x50005'
                path.write_text(json.dumps(diagnostic))
                with self.assertRaisesRegex(ValueError, 'power flags'):
                    sdk_capture.require_n1(path, diagnostic_latched_power=True)

    def test_accept_n2_refuses_diagnostic_inputs(self):
        # Test both mode and verdict markers, even if automatic checks succeeded.
        args = SimpleNamespace(camera_available=True, n1_result=Path('/synthetic/n1/result.json'),
                               smoke=Path('/synthetic/smoke/capture-result.json'),
                               reproduction=Path('/synthetic/reproduction/capture-result.json'),
                               soak=Path('/synthetic/soak/capture-result.json'))
        for marker in ({'power_mode': 'diagnostic_latched_history', 'verdict': 'PASS'},
                       {'power_mode': 'strict', 'verdict': 'OPEN_DIAGNOSTIC'}):
            with self.subTest(marker=marker), patch.object(phase_gate, 'camera_guard'), \
                    patch.object(phase_gate, 'receipt', return_value={'camera': {}, **marker}), \
                    patch.object(sdk_capture, 'validate_camera'), patch.object(phase_gate, 'sha256', return_value='synthetic'), \
                    patch.object(phase_gate, 'verify_evidence', return_value=marker):
                with self.assertRaisesRegex(RuntimeError, 'Diagnostic'):
                    phase_gate.accept(args)
        for marker in ({'power_mode': 'diagnostic_latched_history', 'verdict': 'REVIEW_REQUIRED'},
                       {'power_mode': 'strict', 'verdict': 'OPEN_DIAGNOSTIC'}):
            with self.subTest(capture_marker=marker), patch.object(phase_gate, 'camera_guard'), \
                    patch.object(phase_gate, 'receipt', return_value={'camera': {}, 'verdict': 'PASS'}), \
                    patch.object(sdk_capture, 'validate_camera'), patch.object(phase_gate, 'sha256', return_value='synthetic'), \
                    patch.object(phase_gate, 'verify_evidence', return_value=marker):
                with self.assertRaisesRegex(RuntimeError, 'Diagnostic'):
                    phase_gate.accept(args)

    def test_diagnostic_stage_progression_requires_opt_in(self):
        data = {'stage': 'N2_SMOKE', 'duration_requested_seconds': 20, 'automatic_checks_pass': True,
                'failures': [], 'sdk_returncode': 0, 'sdk_orderly_shutdown': True, 'n1_sha256': 'synthetic',
                'power_mode': 'diagnostic_latched_history', 'verdict': 'OPEN_DIAGNOSTIC'}
        with patch.object(phase_gate, 'verify_evidence', return_value=data), \
                patch.object(phase_gate, 'analyze_csv', return_value={'automatic_checks_pass': True}):
            with self.assertRaisesRegex(RuntimeError, 'Diagnostic'):
                phase_gate.completed_capture(Path('/synthetic/capture-result.json'), 20, 'synthetic')
            self.assertEqual(phase_gate.completed_capture(Path('/synthetic/capture-result.json'), 20, 'synthetic', True), data)

    def test_pgm_does_not_eat_whitespace_pixel_bytes(self):
        with tempfile.TemporaryDirectory(prefix="wbr-synthetic-pgm-") as temp:
            path = Path(temp) / "synthetic.pgm"
            pixels = bytes([10, 32, 13, 9]) * (640 * 480 // 4)
            path.write_bytes(b"P5\n# synthetic parser fixture\n640 480\n255\n" + pixels)
            self.assertEqual(image_content.read_pgm(path), pixels)
            path.write_bytes(path.read_bytes()[:-1])
            with self.assertRaisesRegex(ValueError, "307200"):
                image_content.read_pgm(path)

    def test_absent_camera_guard_fails_before_n1_or_hardware_read(self):
        result = subprocess.run([sys.executable, str(Path(sdk_capture.__file__)),
                                 "--n1-result", "/does-not-exist", "--output", "/does-not-exist", "--seconds", "20"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CAMERA AVAILABLE", result.stderr)

    def test_failed_n1_never_reads_hardware(self):
        with tempfile.TemporaryDirectory(prefix="wbr-synthetic-n1-") as temp:
            path = Path(temp) / "synthetic-n1.json"
            path.write_text(json.dumps({"stage": "N1_PRECHECK", "verdict": "FAIL", "utc_end": datetime.now(timezone.utc).isoformat()}))
            with patch.object(sdk_capture, "validate_camera", side_effect=AssertionError("must not inspect camera")):
                with self.assertRaisesRegex(ValueError, "N1 is not PASS"):
                    sdk_capture.require_n1(path)


if __name__ == "__main__":
    unittest.main()
