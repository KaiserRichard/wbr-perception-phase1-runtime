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
import unittest
from unittest.mock import patch

import image_content
import kernel_analysis
import sdk_analysis
import sdk_capture
from health_monitor import failures as health_failures


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


class ImageAndGuardTests(unittest.TestCase):
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
