import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.check_doc_links as checker


class DocLinkCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs/learning").mkdir(parents=True)
        (self.root / "ops/worklog/sessions").mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def scan(self, source: str):
        path = self.root / "docs/learning/example.md"
        path.write_text(source, encoding="utf-8")
        with patch.object(checker, "ROOT", self.root):
            return checker.scan_local(("docs/learning",))

    def test_resolves_relative_and_repo_root_markdown_links(self):
        (self.root / "docs/learning/guide.md").touch()
        (self.root / "sim").mkdir()
        (self.root / "sim/plant.py").touch()
        findings = self.scan("[relative](guide.md) [root](sim/plant.py)\n")
        self.assertEqual(findings, [])

    def test_reports_broken_doc_link_but_ignores_external_and_machine_paths(self):
        findings = self.scan(
            "[missing](absent.md) [web](https://example.org/x)\n"
            "Machine path: `/Users/guest/file.md`.\n"
        )
        self.assertEqual([(f.status, f.target) for f in findings],
                         [("BROKEN", "absent.md")])

    def test_code_examples_and_globs_are_not_repo_path_findings(self):
        findings = self.scan(
            "`sim/not-real.py`\n"
            "Example: `ops/lab-assistant/handoffs/*.md`.\n"
        )
        self.assertEqual(findings, [])

    def test_missing_worklog_link_is_labeled_historical(self):
        path = self.root / "ops/worklog/sessions/old.md"
        path.write_text("[old source](../../../docs/old.md)\n", encoding="utf-8")
        with patch.object(checker, "ROOT", self.root):
            findings = checker.scan_local(("ops",))
        self.assertEqual([(f.status, f.target) for f in findings],
                         [("HISTORICAL-MISSING", "../../../docs/old.md")])


if __name__ == "__main__":
    unittest.main()
