# Camera TrackStereo frame budget worker — 2026-10-21

- Added a standard-library analyzer, focused tests, and offline README usage for the three archived `frames.csv` replays.
- Validates exact schema, integer fields, increasing source stamps, contiguous processed counters, and positive non-overlapping serial Track intervals.
- Counts strict `duration_ns > 66,700,000` and exact rational `15 * duration_ns > 1,000,000,000`; reports tracked subset (`pose_published=true`), nearest-rank p50/p95/max, total duration and budget excess.
- Ran only the existing replay CSVs; did not start replay/Docker workload or access Pi/camera/hardware. External JSON/Markdown/CSV/SVG outputs and commands/input hashes: `/Users/quockaiser/wbr-evidence-archive/camera-recording-20261021-01/claude-review-followup-01/j-budget/` (`worker-receipt.json`).
- Results (all calls / over 66.7 ms / tracked-call overruns; p50/p95/max ms): replay 1 `2215 / 6 / 6; 21.448 / 36.087 / 144.116`; replay 2 `2215 / 135 / 135; 26.000 / 71.697 / 512.931`; replay 3 `2215 / 14 / 12; 22.079 / 39.541 / 487.859`.
- All counts are compute-budget misses in a no-drop 1× offline queue, not observed live drops or latest-image queue forecasts; Intel Mac x86_64 numbers do not transfer to Pi.
- Tests: `python3 -m unittest discover -s scripts/camera_day/offline -p test_track_budget.py -v` — 4 passed. CLI help and three-run batch command passed; histogram denominators verified at 2,215 each.
