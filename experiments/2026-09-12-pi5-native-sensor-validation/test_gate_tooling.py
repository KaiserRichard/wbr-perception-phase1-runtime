"""Synthetic and saved-text tests only: never hardware evidence."""
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

import n1_precheck
from n1_precheck import evaluate_usb, parse_enumeration, supported_profiles
from validation_common import ACTIVE_UNIT, baseline_text, camera_guard, power_allowed, write_json


class GateToolingTests(unittest.TestCase):
    def camera(self, speed=5000, path="5-1"):
        return {"idVendor": "8086", "idProduct": "0b3a", "speed_mbps": speed,
                "sysfs_name": path, "usb_descriptor_serial": ACTIVE_UNIT['usb_descriptor_serial']}

    def test_old_usb_identity_rejected(self):
        camera = self.camera()
        camera['usb_descriptor_serial'] = '251843061466'
        self.assertTrue(evaluate_usb(camera, True))

    def test_n3_serial_uses_shared_identity(self):
        text = baseline_text(Path(__file__).with_name('n3_baseline.yaml'))
        self.assertIn('serial_no: "' + ACTIVE_UNIT['device_serial'] + '"', text)
        self.assertNotIn('${ACTIVE_DEVICE_SERIAL}', text)

    def test_power_mask_rejects_live_unknown_and_malformed_bits(self):
        for value in (0x50005, 0x100, 0x100000, -1):
            self.assertFalse(power_allowed(value, True))
        self.assertTrue(power_allowed(0xF0000, True))

    def test_synthetic_n1_identity_power_and_verdict(self):
        # Every Pi/camera observation is mocked; no hardware access or evidence claim.
        profiles = 'Infrared 1 640x480 Y8 @ 15 Hz\nGyro MOTION_XYZ32F @ 200 Hz\nAccel MOTION_XYZ32F @ 100 Hz\n'
        cases = [('throttled=0x0', False, False, 'PASS'),
                 ('throttled=0x50000', False, False, 'FAIL'),
                 ('throttled=0x50000', True, False, 'OPEN_DIAGNOSTIC'),
                 ('throttled=0x0', True, False, 'OPEN_DIAGNOSTIC'),
                 ('throttled=0x50005', True, False, 'FAIL'),
                 ('throttled=0x0', False, True, 'FAIL')]
        for raw, diagnostic, old, verdict in cases:
            identity = dict(n1_precheck.EXPECTED)
            if old:
                identity.update(device_serial='243322073847', asic_serial='251843061466', firmware_update_id='251843061466')
            labels = {'device_serial': 'Serial Number', 'asic_serial': 'Asic Serial Number',
                      'firmware_update_id': 'Firmware Update Id', 'firmware': 'Firmware Version', 'imu_type': 'Imu Type'}
            enumeration = ''.join(f'{labels[k]} : {v}\n' for k, v in identity.items()) + profiles
            def checked(argv):
                return {'dpkg': 'arm64', 'timedatectl': 'yes', 'vcgencmd': raw}.get(argv[0], '')
            def read(path):
                return '60000' if str(path).endswith('/temp') else 'MemAvailable: 524288 kB'
            def run(argv, **kwargs):
                return {'returncode': 1 if argv[0] == 'fuser' else 0, 'stderr': '', 'stdout': enumeration}
            with self.subTest(raw=raw, diagnostic=diagnostic, old=old), tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / 'synthetic-n1'
                argv = ['n1_precheck.py', '--camera-available', '--direct-cable-confirmed', '--output', str(output)]
                if diagnostic:
                    argv.append('--diagnostic-latched-power')
                with patch.object(sys, 'argv', argv), patch.object(n1_precheck, 'camera_guard'), \
                        patch.object(n1_precheck, 'provenance', return_value={'os_release': 'VERSION_ID="24.04"'}), \
                        patch.object(n1_precheck, 'checked', side_effect=checked), patch.object(n1_precheck, 'read', side_effect=read), \
                        patch.object(n1_precheck, 'run', side_effect=run), patch.object(n1_precheck, 'usb_snapshot', side_effect=lambda: self.camera()), \
                        patch.object(n1_precheck, 'active_camera_processes', return_value=[]), \
                        patch.object(n1_precheck, 'permissions', return_value={'pass': True, 'paths': []}), \
                        patch.object(Path, 'is_file', return_value=True), patch.object(Path, 'glob', return_value=[]), \
                        patch.object(n1_precheck.time, 'sleep'), patch('builtins.print'):
                    code = n1_precheck.main()
                result = json.loads((output / 'result.json').read_text())
                self.assertEqual(result['verdict'], verdict)
                self.assertEqual(code, 1 if verdict == 'FAIL' else 0)
                self.assertEqual(result['throttled_raw'], raw)
                self.assertEqual(result['power_mode'], 'diagnostic_latched_history' if diagnostic else 'strict')

    def test_480m_is_blocked_even_with_expected_identity(self):
        self.assertTrue(evaluate_usb(self.camera(480), True))

    def test_superspeed_hub_path_is_blocked(self):
        self.assertTrue(evaluate_usb(self.camera(5000, "5-1.2"), True))

    def test_superspeed_or_better_direct_path(self):
        self.assertEqual([], evaluate_usb(self.camera(10000), True))
        self.assertTrue(evaluate_usb(self.camera(), False))

    def test_saved_enumeration_keeps_identifiers_separate(self):
        text = Path(__file__).with_name("sdk-enumeration-full.txt").read_text()
        result = parse_enumeration(text)
        self.assertEqual(result["device_serial"], "243322073847")
        self.assertEqual(result["asic_serial"], "251843061466")
        self.assertEqual(result["firmware_update_id"], "251843061466")
        self.assertNotIn("usb_descriptor_serial", result)
        self.assertTrue(supported_profiles(text))
        self.assertFalse(supported_profiles(text.replace("640x480", "640x400")))

    def test_ambiguous_enumeration_fails(self):
        with self.assertRaises(ValueError):
            parse_enumeration("Serial Number : 1\nSerial Number : 2\n")

    def test_unavailable_camera_never_enters_hardware_path(self):
        with self.assertRaises(RuntimeError):
            camera_guard(False)

    def test_root_not_allowed(self):
        with patch("os.geteuid", return_value=0), self.assertRaises(RuntimeError):
            camera_guard(True)

    def test_output_is_append_only(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "result.json"
            write_json(p, {"synthetic": True})
            with self.assertRaises(FileExistsError):
                write_json(p, {"synthetic": False})
            self.assertTrue(json.loads(p.read_text())["synthetic"])


if __name__ == "__main__":
    unittest.main()
