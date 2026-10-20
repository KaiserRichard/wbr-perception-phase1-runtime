# C3 documentation link checker

- Added `scripts/check_doc_links.py`, a standard-library checker for Markdown links and explicit repository-root paths in `docs/learning` and `ops`.
- Local references are checked by default. Worklog references to retired files are labeled historical warnings; absolute host paths, URLs, inline/fenced examples and glob patterns are excluded from repository-path findings.
- Optional HTTP probing has bounded timeouts, at most eight concurrent requests and a 100-URL cap; HTTP 403/429 are reported as unverified. HTTP probing was not run.
- Added four focused unit tests. Command `python3 -m unittest discover -s scripts/tests -p test_doc_links.py -v`: 4/4 passed.
- `python3 scripts/check_doc_links.py --help`: passed. `python3 scripts/check_doc_links.py`: exit 0, zero active broken references, eight missing historical paths in `ops/worklog/sessions/2026-10-20-simulation-control.md` to proposed/retired files and `docs/mechanical/shaft_analysis_notes.md`. Historical records were preserved.
- No document path fixes were needed; current links in learning docs and active ops guidance resolve.
