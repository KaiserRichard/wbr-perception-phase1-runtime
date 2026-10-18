import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_patch", HERE / "verify_patch.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class PatchChecks(unittest.TestCase):
    """Saved pinned source plus a real historical crash report; no shared path required."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.saved = self.root / "saved"
        shutil.copytree(HERE / "validation/pinned-source/raw", self.saved / "raw")

    def tearDown(self):
        self.temporary.cleanup()

    def run_check(self, compiler=None):
        output = self.root / "result"
        with contextlib.redirect_stdout(io.StringIO()):
            code = verify.check(self.saved, output, compiler, analyze=True)
        result = json.loads((output / "result.json").read_text())
        for entry in result["raw_files"]:
            self.assertEqual(hashlib.sha256((output / entry["path"]).read_bytes()).hexdigest(), entry["sha256"])
        for criterion in result["criteria"]:
            self.assertTrue((output / criterion["evidence"]).is_file())
            self.assertTrue(criterion["threshold_source"])
        return code, result

    def test_pass_reanalyzes_actual_pinned_source_and_executes_probe(self):
        if not (shutil.which("clang++") or shutil.which("c++")):
            self.skipTest("C++ compiler unavailable; missing-compiler path tested separately")
        code, result = self.run_check()
        self.assertEqual((code, result["status"]), (0, "PASS"))
        raw = self.root / "result/raw"
        self.assertIn("Applied patch include/LocalMapping.h cleanly", (raw / "apply.stderr").read_text())
        for standard in ("c++11", "c++17"):
            self.assertEqual((raw / (standard + "-run.exit.txt")).read_text().strip(), "0")

    def test_fail_source_bytes_changed(self):
        with (self.saved / "raw/include/LocalMapping.h").open("a") as stream:
            stream.write("\n// fixture alteration\n")
        code, result = self.run_check()
        self.assertEqual((code, result["status"]), (1, "FAIL"))
        self.assertEqual(result["criteria"][0]["status"], "FAIL")

    def test_fail_wrong_revision(self):
        (self.saved / "raw/revision.txt").write_text("wrong-revision\n")
        code, result = self.run_check()
        self.assertEqual((code, result["status"]), (1, "FAIL"))

    def test_fail_unapplicable_patch(self):
        patch = self.saved / "raw" / verify.PATCH
        patch.write_text(patch.read_text().replace("-    KeyFrame* mpCurrentKeyFrame;", "-    KeyFrame* absentMember;"))
        code, result = self.run_check()
        self.assertEqual((code, result["status"]), (1, "FAIL"))
        self.assertEqual(result["criteria"][1]["status"], "FAIL")
        self.assertIn("patch failed", (self.root / "result/raw/apply-check.stderr").read_text())

    def test_blocked_missing_source(self):
        (self.saved / "raw/src/System.cc").unlink()
        code, result = self.run_check()
        self.assertEqual((code, result["status"]), (2, "BLOCKED"))

    def test_blocked_missing_compiler(self):
        code, result = self.run_check(compiler=str(self.root / "missing-compiler"))
        self.assertEqual((code, result["status"]), (2, "BLOCKED"))
        self.assertEqual(result["criteria"][1]["status"], "PASS")

    def test_real_saved_crash_report_is_explicit_about_missing_raw_trace(self):
        fixture = json.loads((HERE / "tests/fixtures/real_saved_crash.json").read_text())
        self.assertIn("MEASURED", fixture["label"])
        self.assertIn("main → System::GetTimeFromIMUInit → LocalMapping::GetCurrKFTime", fixture["verbatim"])
        self.assertIn("mpCurrentKeyFrame = nullptr", fixture["verbatim"])
        self.assertFalse(fixture["raw_backtrace_available"])

    def test_patch_four_alone_leaves_timestamp_indeterminate(self):
        header = (self.saved / "raw/include/LocalMapping.h").read_text()
        patch_four_only = header.replace("KeyFrame* mpCurrentKeyFrame;", "KeyFrame* mpCurrentKeyFrame = nullptr;")
        self.assertIn("double mFirstTs;", patch_four_only)
        body = verify.function((self.saved / "raw/src/System.cc").read_text(), "double System::GetTimeFromIMUInit()")
        self.assertLess(body.index("mpLocalMapper->mFirstTs"), body.index("mpAtlas->isImuInitialized()"))

    def test_usage_exit_code(self):
        result = subprocess.run([sys.executable, str(HERE / "verify_patch.py")], capture_output=True)
        self.assertEqual(result.returncode, 3)


if __name__ == "__main__":
    unittest.main()
