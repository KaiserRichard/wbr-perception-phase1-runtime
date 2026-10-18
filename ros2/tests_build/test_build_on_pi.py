import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ros2" / "build_on_pi.sh"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "orbslam3_pi_build_evidence.json"


class BuildOnPiTests(unittest.TestCase):
    def run_script(self, *args, env=None):
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(
            ["bash", str(SCRIPT), *map(str, args)],
            cwd=ROOT,
            env=merged,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_plan_without_orb_is_explicitly_off(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_script(
                "--plan",
                "--orb-root",
                Path(temp) / "missing-orb",
                "--workspace",
                Path(temp) / "ws",
                "--outdir",
                Path(temp) / "out",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ORB_MODE=OFF", result.stdout)
        self.assertIn("-DWITH_ORB_SLAM3=OFF", result.stdout)
        self.assertNotIn("-DORB_SLAM3_ROOT=", result.stdout)
        self.assertIn("MAKEFLAGS=-j2", result.stdout)

    def test_plan_with_orb_adds_root_only_to_orb_package(self):
        with tempfile.TemporaryDirectory() as temp:
            orb = Path(temp) / "orb"
            (orb / "lib").mkdir(parents=True)
            (orb / "lib" / "libORB_SLAM3.so").write_bytes(b"fixture")
            result = self.run_script("--plan", "--orb-root", orb)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ORB_MODE=ON", result.stdout)
        self.assertIn("-DWITH_ORB_SLAM3=ON", result.stdout)
        self.assertIn(f"-DORB_SLAM3_ROOT={orb}", result.stdout)

    def make_stub_environment(self, temp, orb_present=True):
        temp = Path(temp)
        fake_bin = temp / "bin"
        fake_bin.mkdir()
        log = temp / "commands.log"
        fake_bin.joinpath("git").write_text(
            "#!/usr/bin/env bash\n"
            'if [[ "$*" == *"rev-parse HEAD"* ]]; then echo "fixture-commit-123"; else echo "git-stub"; fi\n'
        )
        fake_bin.joinpath("colcon").write_text(
            "#!/usr/bin/env bash\n"
            'echo "colcon $*" >> "$STUB_LOG"\n'
            'if [[ "$1" == "--version" ]]; then echo "colcon-core 0.18.0"; fi\n'
        )
        fake_bin.joinpath("cmake").write_text(
            "#!/usr/bin/env bash\n"
            'if [[ "$1" == "--version" ]]; then echo "cmake version 3.28.3"; fi\n'
        )
        fake_bin.joinpath("gcc").write_text(
            "#!/usr/bin/env bash\n"
            'if [[ "$1" == "--version" ]]; then echo "gcc (Ubuntu 13.2.0) 13.2.0"; fi\n'
        )
        fake_bin.joinpath("sha256sum").write_text(
            "#!/usr/bin/env bash\n"
            'printf "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  %s\\n" "$1"\n'
        )
        for path in fake_bin.iterdir():
            path.chmod(0o755)
        ros = temp / "ros"
        ros.mkdir()
        (ros / "setup.bash").write_text("#!/usr/bin/env bash\nexport WBR_FAKE_ROS=1\n")
        orb = temp / "orb"
        if orb_present:
            (orb / "lib").mkdir(parents=True)
            (orb / "lib" / "libORB_SLAM3.so").write_bytes(b"fixture ORB library")
        env = {
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "STUB_LOG": str(log),
        }
        return env, ros, orb, log

    def test_stubbed_build_captures_provenance_and_runs_tests(self):
        with tempfile.TemporaryDirectory() as temp:
            env, ros, orb, log = self.make_stub_environment(temp)
            workspace = Path(temp) / "workspace"
            outdir = Path(temp) / "evidence"
            result = self.run_script(
                "--ros-prefix",
                ros,
                "--workspace",
                workspace,
                "--outdir",
                outdir,
                "--orb-root",
                orb,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((outdir / "result.json").read_text())
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["provenance"]["orb_mode"], "ON")
            provenance = json.loads((outdir / "provenance.json").read_text())
            self.assertEqual(provenance["git_commit"], "fixture-commit-123")
            self.assertEqual(provenance["orb_library_sha256"], "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
            self.assertTrue((workspace / "src" / "wbr_orb_node").is_symlink())
            commands = log.read_text()
            self.assertIn("colcon build --symlink-install", commands)
            self.assertIn("-DWITH_ORB_SLAM3=ON", commands)
            self.assertIn(f"-DORB_SLAM3_ROOT={orb}", (outdir / "build.log").read_text())
            self.assertIn("colcon test --packages-select wbr_orb_node", commands)
            self.assertIn("colcon test-result --verbose", commands)

    def test_missing_ros_is_blocked_and_does_not_create_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            outdir = Path(temp) / "evidence"
            result = self.run_script(
                "--ros-prefix",
                Path(temp) / "missing-jazzy",
                "--workspace",
                workspace,
                "--outdir",
                outdir,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("BLOCKED", result.stderr)
            report = json.loads((outdir / "result.json").read_text())
            self.assertEqual(report["status"], "BLOCKED")
            self.assertFalse(workspace.exists())

    def test_fixture_is_derived_from_saved_pi_build_evidence(self):
        fixture = json.loads(FIXTURE.read_text())
        self.assertEqual(fixture["evidence_label"], "SOURCE-SUPPORTED")
        self.assertEqual(fixture["source"], "experiments/2026-10-13-orbslam3-pi-build/build_orbslam3.sh")
        self.assertEqual(fixture["orb_root"], "~/orbslam3/ORB_SLAM3")
        self.assertEqual(fixture["build_parallelism"], "-j2")


if __name__ == "__main__":
    unittest.main()

