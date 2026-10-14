"""Synthetic and saved-text tests only: never hardware evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from n1_precheck import evaluate_usb, parse_enumeration, supported_profiles
from validation_common import camera_guard, write_json


class GateToolingTests(unittest.TestCase):
    def camera(self, speed=5000, path="5-1"):
        return {"idVendor": "8086", "idProduct": "0b3a", "speed_mbps": speed,
                "sysfs_name": path, "usb_descriptor_serial": "251843061466"}

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
