# C3 documentation link checker

- Added `scripts/check_doc_links.py`, a standard-library checker for Markdown links and explicit repository-root paths in `docs/learning` and `ops`.
- Local references are checked by default. Markdown hrefs resolve relative to their source file, including hrefs beginning with a repository directory; naked/backtick repository paths resolve from repo root. Missing references in worklog sessions/reviews are historical warnings. Other live worklog files fail normally; an explicit `<!-- doc-link-checker: historical -->` marker also opts a document into historical status. Absolute host paths, URLs, fenced examples, template placeholders and glob patterns are excluded from repository-path findings.
- Undefined full/collapsed Markdown reference links are detected. Undefined shortcut references are not detected because `[words]` is ambiguous with bracketed prose.
- Optional HTTP probing has bounded timeouts, at most eight concurrent requests and a 100-URL cap; HTTP 403/429 are reported as unverified. HTTP probing was not run.
- Added regression tests for source-relative hrefs, live worklog files, and undefined full reference links. `python3 -m unittest discover -s scripts/tests -p test_doc_links.py -v`: 7/7 passed.
- `python3 scripts/check_doc_links.py --help`: passed. `python3 scripts/check_doc_links.py`: exit 0, zero current broken references and twelve missing repository paths in historical sessions. Examples include a generated build directory, retired simulation paths and `docs/mechanical/shaft_analysis_notes.md`; historical records were preserved.
- HTTP probing remains optional and was not run. No doc fixes were needed after the corrected scan.
