# Simcam IMU worker log — 2026-10-30

- Scope: only `tools/simcam_imu/**` and `docs/simcam_imu/**`; no existing tool edits,
  Git mutations, rendering, SSH, hardware access or training.
- Read session notes, owner profile, imu_view stream/filter/view calibration and
  axle geometry, simcam scenario/run/depth/README, wbr_pose placement and jump gate.
- Built a measured-CSV tilt source, continuous-window listing, offline bias
  correction, complementary filtering, linear interpolation and rate extraction.
- Built paired ideal-depth runs by composing simcam helpers and wbr_pose; a Tick
  adapter supplies filtered Euler rates to the unchanged gate. Added current
  cluster dimensions, fit-validity-masked errors, comparison join and provenance.
- Actual source command: `~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m tools.simcam_imu.tilt_source ~/wbr-evidence-archive/imu-view-live-20261030/imu_view_run.csv`.
  PASS: 115,073 samples; first board timestamp 138.488 s; duration 1,159.92 s;
  maximum sample gap 0.015 s. First 2 s include 199 samples; mean gyro bias
  (-3.350712, +0.122902, -0.110012) deg/s; per-axis standard deviations
  (0.035328, 0.034590, 0.030997) deg/s. Stillness remains an assumption.
- Window listing: 9 qualifying absolute-angle windows at scale 1.0, including
  11.360–41.955 s (peak pitch 28.026 degrees, peak roll 8.803 degrees).
  The initial 0–4.345 s span also qualifies because initial bench pitch exceeds
  3 degrees; a threshold window does not by itself establish motion.
- First complete test run: `~/Desktop/Research/wbr-lab-ops/.venv/bin/python .github/run_unittest.py tools/simcam_imu`.
  PASS: 21 tests, 2 test files, 0 skipped, 0.373 s; no failures encountered.
- CLI help: `~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m tools.simcam_imu.run --help`.
  PASS; positional scenario optional, required IMU path and replay options present.
- Documentation added: README (status, commands, time/filter/geometry assumptions,
  output/error definitions, hypothesis and limitations), this log and REVIEW.
- Final test rerun after the strict-duration floating-point tolerance fix:
  PASS, 21 tests, 2 files, 0 skipped, 0.345 s. The fix prevents an exactly 2 s
  window from qualifying solely due to timestamp subtraction roundoff.
- Markdown: `python3 tools/lint_markdown.py docs/simcam_imu/README.md docs/simcam_imu/WORKLOG.md docs/simcam_imu/REVIEW.md`.
  PASS: 0 issues across 3 files. Git status shows only the two allowed new
  directories; no tracked file modifications.
- Rendering and dynamic-tilt MAE/advisory outcomes remain pending conductor execution.
