"""Exercise digest publication with controlled AGY stdout, without network calls."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


HEADERS = [
    "## What works now (with key numbers)",
    "## What failed or is blocked",
    "## What the owner must do by hand",
    "## Open PRs to decide",
    "## How to demo it yourself",
    "## Next steps",
]


class DigestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / "out"
        self.out.mkdir()
        source = Path(__file__).resolve().parent
        for name in ("digest.sh", "prompt_daily.md", "prompt_afternoon.md"):
            shutil.copyfile(source / name, self.root / name)
        (self.root / "collect.sh").write_text('printf "%s\\n" "$AGY_BUNDLE"\n')
        (self.root / "bundle.md").write_text("Source bundle fixture\n")
        fake_agy = self.root / "agy"
        fake_agy.write_text(
            '#!/usr/bin/env bash\n'
            'printf "%s\\0" "$@" > "$AGY_ARGS"\n'
            'cat "$AGY_FIXTURE"\n'
            'exit "${AGY_EXIT:-0}"\n'
        )
        fake_agy.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.root}{os.pathsep}{os.environ['PATH']}",
                        AGY_BUNDLE=str(self.root / "bundle.md"),
                        AGY_FIXTURE=str(self.root / "stdout.md"),
                        AGY_ARGS=str(self.root / "args"), AGY_EXIT="0")
        self.run_date = subprocess.check_output(["date", "+%F"], text=True).strip()

    def draft(self, mode="afternoon", lines=20):
        headers = HEADERS if mode == "afternoon" else HEADERS[:4]
        return "\n".join(headers + ["- Source-backed fixture"] * (lines - len(headers))) + "\n"

    def path(self, mode="afternoon", suffix=".md"):
        return self.out / f"digest-{self.run_date}-{mode}{suffix}"

    def run_digest(self, content, mode="afternoon"):
        (self.root / "stdout.md").write_text(content)
        return subprocess.run(["bash", str(self.root / "digest.sh"), mode],
                              env=self.env, capture_output=True, text=True)

    def assert_rejected(self, content):
        self.path().write_text("Previous accepted digest\n")
        result = self.run_digest(content)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(self.path().read_text(), "Previous accepted digest\n")
        self.assertEqual(self.path(suffix=".rejected.md").read_text(), content)
        self.assertFalse(list(self.out.glob(".digest.*")))

    def test_rejects_original_seven_line_status_note(self):
        self.assert_rejected("Digest is ready for your review.\n" * 7)

    def test_line_limits(self):
        for lines in (0, 19, 60):
            with self.subTest(lines=lines):
                self.assert_rejected(self.draft(lines=lines) if lines else "")

    def test_each_afternoon_heading_is_required(self):
        for header in HEADERS:
            with self.subTest(header=header):
                self.assert_rejected(self.draft().replace(header, "Missing section"))

    def test_daily_requires_its_four_headings(self):
        for header in HEADERS[:4]:
            with self.subTest(header=header):
                result = self.run_digest(self.draft("daily").replace(header, "Missing section"), "daily")
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertFalse(self.path("daily").exists())

    def test_valid_modes_and_boundary_lengths_publish_stdout(self):
        for mode in ("daily", "afternoon"):
            for lines in (20, 59):
                with self.subTest(mode=mode, lines=lines):
                    content = self.draft(mode, lines)
                    result = self.run_digest(content, mode)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(self.path(mode).read_text(), content)
                    self.assertEqual(result.stdout.strip(), str(self.path(mode)))
                    args = (self.root / "args").read_text().split("\0")[:-1]
                    self.assertEqual(args[-2], "-p")
                    self.assertIn("Source bundle fixture", args[-1])
                    self.assertIn("Return ONLY the digest Markdown itself on stdout", args[-1])
                    self.assertEqual(args[args.index("--output-format") + 1], "text")
                    self.assertNotIn("--effort", args)

    def test_agy_failure_preserves_digest_and_exit_status(self):
        self.path().write_text("Previous accepted digest\n")
        self.env["AGY_EXIT"] = "7"
        result = self.run_digest(self.draft())
        self.assertEqual(result.returncode, 7)
        self.assertEqual(self.path().read_text(), "Previous accepted digest\n")
        self.assertFalse(list(self.out.glob(".digest.*")))


if __name__ == "__main__":
    unittest.main()
