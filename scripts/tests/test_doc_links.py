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

    def test_markdown_href_is_relative_to_source_even_when_repo_prefixed(self):
        (self.root / "docs/learning/guide.md").touch()
        (self.root / "sim").mkdir()
        (self.root / "sim/plant.py").touch()
        findings = self.scan("[relative](guide.md) [root](sim/plant.py)\n")
        self.assertEqual([(f.status, f.target) for f in findings],
                         [("BROKEN", "sim/plant.py")])

    def test_naked_root_prefixed_path_resolves_from_repository_root(self):
        (self.root / "sim").mkdir()
        (self.root / "sim/plant.py").touch()
        self.assertEqual(self.scan("See `sim/plant.py`.\n"), [])

    def test_reports_broken_doc_link_but_ignores_external_and_machine_paths(self):
        findings = self.scan(
            "[missing](absent.md) [web](https://example.org/x)\n"
            "Machine path: `/Users/guest/file.md`.\n"
        )
        self.assertEqual([(f.status, f.target) for f in findings],
                         [("BROKEN", "absent.md")])

    def test_inline_repo_paths_are_checked_but_globs_are_skipped(self):
        findings = self.scan(
            "`sim/not-real.py`\n"
            "Example: `ops/lab-assistant/handoffs/*.md`.\n"
            "Template: `ops/worklog/sessions/YYYY-MM-DD-<topic>.md`.\n"
        )
        self.assertEqual([(f.status, f.target) for f in findings],
                         [("BROKEN", "sim/not-real.py")])

    def test_missing_worklog_link_is_labeled_historical(self):
        path = self.root / "ops/worklog/sessions/old.md"
        path.write_text("[old source](../../../docs/old.md)\n", encoding="utf-8")
        with patch.object(checker, "ROOT", self.root):
            findings = checker.scan_local(("ops",))
        self.assertEqual([(f.status, f.target) for f in findings],
                         [("HISTORICAL-MISSING", "../../../docs/old.md")])

    def test_current_and_worklog_readme_missing_links_are_broken(self):
        worklog = self.root / "ops/worklog"
        (worklog / "CURRENT.md").write_text("[missing](../../absent.md)\n", encoding="utf-8")
        (worklog / "README.md").write_text("[missing](../../absent.md)\n", encoding="utf-8")
        with patch.object(checker, "ROOT", self.root):
            findings = checker.scan_local(("ops",))
        self.assertEqual([(f.file.name, f.status) for f in findings],
                         [("CURRENT.md", "BROKEN"), ("README.md", "BROKEN")])

    def test_undefined_reference_use_is_reported(self):
        (self.root / "docs/learning/guide.md").touch()
        findings = self.scan("[good][present] [bad][absent]\n[present]: guide.md\n")
        self.assertEqual([(f.status, f.target) for f in findings],
                         [("BROKEN", "[absent]")])


if __name__ == "__main__":
    unittest.main()
