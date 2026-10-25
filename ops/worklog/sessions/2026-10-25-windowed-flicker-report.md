# 2026-10-25 windowed flicker report

- Updated `tools/obstacle_decision/flicker_check.py` to replay only depth frames whose camera header stamps fall in each run's inclusive live packet timestamp window.
- Report includes window duration, old/new/live transition counts and rates, plus new transition distance/height for approach runs.
- Regenerated `FLICKER_REPORT_window.md` from `/Users/quockaiser/wbr-evidence-archive/lab-day-20261025` (5 runs; 59.84–59.91 s windows; 58 report lines, at most 25 new transitions listed per run).
- `python -m unittest tools.obstacle_decision.tests.test_obstacle_decision -v`: 7 tests PASS.
- Full `python -m unittest discover -s tools/obstacle_decision/tests -v`: first 7 tests passed; remained at `test_box_empty_floor_and_wall_sections` without completion in the captured run (`/private/tmp/obstacle-decision-tests-20261025.log`).
- `py_compile` and `git diff --check` passed. All changes remain uncommitted on `claude2/20261025-lab-fixes`.
