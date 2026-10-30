#!/usr/bin/env python3
"""Offline integration tests for collecting historical branch-tip sources."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("collect.sh")
OLD_DATE = "2020-01-02T03:04:05Z"


def run(*args, cwd, env=None):
    return subprocess.run(
        args, cwd=cwd, env=env, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


class CollectorHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        gh = self.bin / "gh"
        gh.write_text("#!/bin/sh\nprintf '[]\\n'\n")
        gh.chmod(0o755)
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env["PATH"] = f"{self.bin}{os.pathsep}{self.env['PATH']}"

        run("git", "init", "-q", cwd=self.repo)
        run("git", "config", "user.name", "Collector test", cwd=self.repo)
        run("git", "config", "user.email", "collector@example.invalid", cwd=self.repo)
        (self.repo / "ops/worklog/ledger").mkdir(parents=True)
        (self.repo / "ops/worklog/reviews").mkdir(parents=True)
        (self.repo / "ops/secretary").mkdir(parents=True)
        shutil.copy2(SCRIPT, self.repo / "ops/secretary/collect.sh")

        self.old_ledger = self.repo / "ops/worklog/ledger/old-entry.md"
        self.old_ledger.write_text("Historical ledger entry that must be collected.\n")
        self.commit("old ledger", OLD_DATE)
        run("git", "branch", "old-ledger", cwd=self.repo)
        run("git", "branch", "unchanged-ledger", cwd=self.repo)
        self.default_branch = run("git", "branch", "--show-current", cwd=self.repo)

        # Advance a different branch with an unrelated recent commit. The
        # ledger remains untouched and must still be present at that branch tip.
        run("git", "checkout", "-q", "unchanged-ledger", cwd=self.repo)
        (self.repo / "unrelated.txt").write_text("recent unrelated change\n")
        self.commit("unrelated recent change", "2026-10-30T00:00:00Z")
        run("git", "checkout", "-q", self.default_branch, cwd=self.repo)
        self.origin = self.root / "origin.git"
        run("git", "init", "--bare", "-q", str(self.origin), cwd=self.root)
        run("git", "remote", "add", "origin", str(self.origin), cwd=self.repo)
        run("git", "push", "-q", "origin", "old-ledger", "unchanged-ledger", cwd=self.repo)

    def commit(self, message, date):
        run("git", "add", "-A", cwd=self.repo)
        env = self.env.copy()
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
        run("git", "commit", "-q", "-m", message, cwd=self.repo, env=env)

    def bundle(self):
        run("bash", "ops/secretary/collect.sh", cwd=self.repo, env=self.env)
        return next((self.repo / "ops/secretary/out").glob("bundle-*.md")).read_text()

    def test_old_branch_tip_is_collected(self):
        bundle = self.bundle()
        self.assertIn("Branch: origin/old-ledger", bundle)
        self.assertIn("Source file: ops/worklog/ledger/old-entry.md", bundle)
        self.assertIn("Historical ledger entry that must be collected.", bundle)

    def test_unchanged_ledger_is_collected_after_unrelated_commit(self):
        bundle = self.bundle()
        self.assertIn("Branch: origin/unchanged-ledger", bundle)
        self.assertIn("Source file: ops/worklog/ledger/old-entry.md", bundle)
        self.assertIn("Window: all existing review and ledger Markdown files", bundle)


if __name__ == "__main__":
    unittest.main()
