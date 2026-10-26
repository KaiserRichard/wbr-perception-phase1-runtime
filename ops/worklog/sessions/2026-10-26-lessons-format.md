# Lessons Markdown formatting repair

- Scope: formatting only in `docs/lessons/README.md` and lessons 01–06; added `tools/lint_markdown.py` (stdlib only).
- Fixed display-math delimiter layout in lessons 01, 03, 04, and 05. Remaining lesson files already met the checked format rules.
- Ran `python3 tools/lint_markdown.py`: `0 issues across 7 file(s)`.
- Ran `git diff --check`: exit 0.
- HTML rendering skipped: Python `markdown` module is unavailable (`python -m markdown` cannot run).
- Branch `claude2/20261026-lessons-format`; changes remain uncommitted and unpushed.
