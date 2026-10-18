from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "tools/orb_settings_check/check_orb_settings.py"
FIXTURES = ROOT / "tools/orb_settings_check/fixtures"


class OrbSettingsCliTests(unittest.TestCase):
    def run_check(self, settings: Path | None, out: Path, *args: str) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, str(TOOL)]
        if settings is not None:
            cmd.append(str(settings))
        cmd += ["--outdir", str(out), *args]
        return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def mutate(self, directory: Path, name: str, changes: dict[str, str]) -> Path:
        source = FIXTURES / "EuRoC.yaml"
        text = source.read_text()
        for before, after in changes.items():
            self.assertIn(before, text)
            text = text.replace(before, after, 1)
        target = directory / name
        target.write_text(text)
        return target

    def result(self, out: Path) -> dict:
        return json.loads((out / "result.json").read_text())

    def criterion(self, result: dict, key: str) -> str:
        return next(c["status"] for c in result["criteria"] if c["id"] == key)

    def test_upstream_euroc_fixture_passes_named_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "pass"
            proc = self.run_check(FIXTURES / "EuRoC.yaml", out, "--profile", "euroc_mh01")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            result = self.result(out)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(self.criterion(result, "stereo_baseline"), "PASS")
            self.assertEqual(self.criterion(result, "imu_noise_calibration"), "PASS")
            self.assertTrue(any(f["path"] == "settings.yaml" for f in result["raw_files"]))

    def test_bad_intrinsics_fail_intrinsics_criterion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bad = self.mutate(root, "bad-intrinsics.yaml", {"Camera1.fy: 457.296": "Camera1.fy: 800.0"})
            out = root / "out"
            proc = self.run_check(bad, out, "--profile", "euroc_mh01")
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(self.criterion(self.result(out), "intrinsics"), "FAIL")

    def test_bad_stereo_rotation_fails_transform_criterion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bad = self.mutate(root, "bad-rotation.yaml", {"0.999997256477797,-0.002317135723275": "2.0,-0.002317135723275"})
            out = root / "out"
            proc = self.run_check(bad, out, "--profile", "euroc_mh01")
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(self.criterion(self.result(out), "transform_geometry"), "FAIL")

    def test_wrong_camera_profile_rate_and_noise_each_fail(self) -> None:
        cases = [
            ("profile", {"Camera.fps: 20": "Camera.fps: 15"}, "camera_profile"),
            ("gyro", {"IMU.Frequency: 200.0": "IMU.Frequency: 100.0"}, "imu_profile_rate"),
            ("noise", {"IMU.NoiseGyro: 1.7e-04": "IMU.NoiseGyro: 1.7e-03"}, "imu_noise_calibration"),
            ("baseline", {"0.110074137800478": "0.220074137800478"}, "stereo_baseline"),
            ("extractor", {"ORBextractor.nLevels: 8": "ORBextractor.nLevels: 80"}, "extractor_sane"),
        ]
        for name, changes, expected in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bad = self.mutate(root, name + ".yaml", changes)
                out = root / "out"
                proc = self.run_check(bad, out, "--profile", "euroc_mh01")
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertEqual(self.criterion(self.result(out), expected), "FAIL")

    def test_missing_input_is_blocked_and_result_contract_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "out"
            proc = self.run_check(Path(temp) / "missing.yaml", out, "--profile", "euroc_mh01")
            self.assertEqual(proc.returncode, 2)
            result = self.result(out)
            self.assertEqual(result["status"], "BLOCKED")
            for key in ("check", "tool_version", "started_utc", "ended_utc", "host", "criteria", "raw_files", "notes"):
                self.assertIn(key, result)

    def test_analyze_only_rechecks_saved_raw_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "original"
            self.assertEqual(self.run_check(FIXTURES / "EuRoC.yaml", original, "--profile", "euroc_mh01").returncode, 0)
            analyzed = root / "analyzed"
            proc = self.run_check(None, analyzed, "--analyze-only", str(original))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(self.result(analyzed)["status"], "PASS")

    def test_saved_d435i_candidate_matches_factory_camchain_and_imu_reference(self) -> None:
        settings = ROOT / "experiments/2026-10-13-n4b-d435i-prep/D435i_317422076650_stereo_inertial.yaml"
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "d435i"
            proc = self.run_check(settings, out, "--profile", "d435i_n4b")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            result = self.result(out)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(self.criterion(result, "stereo_baseline"), "PASS")
            self.assertEqual(self.criterion(result, "imu_noise_calibration"), "PASS")

    def test_make_orb_yaml_provenance_hash_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "orbslam3.yaml"
            shutil.copyfile(FIXTURES / "EuRoC.yaml", generated)
            digest = hashlib.sha256(generated.read_bytes()).hexdigest()
            (root / "provenance.json").write_text(json.dumps({"outputs": {"orbslam3.yaml": {"sha256": digest}}}))
            out = root / "out"
            proc = self.run_check(generated, out, "--profile", "euroc_mh01")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(self.criterion(self.result(out), "generator_provenance"), "PASS")

            altered = root / "altered.yaml"
            altered.write_text(generated.read_text() + "# edited copy\n")
            failed_out = root / "failed"
            proc = self.run_check(altered, failed_out, "--profile", "euroc_mh01", "--provenance", str(root / "provenance.json"))
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(self.criterion(self.result(failed_out), "generator_provenance"), "FAIL")


if __name__ == "__main__":
    unittest.main()
