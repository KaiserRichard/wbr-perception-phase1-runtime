# Simcam IMU worker handoff — 2026-10-30

Implementation is complete within the two authorized directories. No commit,
push or PR was attempted. The original IMU CSV was read, never written. Existing
simcam, imu_view, detector, policy and gate files are unchanged.

Local non-rendering checks passed: 21 tests in 2 files, zero skipped. The real
115,073-row recording loads and produces bias metadata and 9 qualifying windows.
The real detector/gate test uses closed-form floor depth arrays, and geometry
tests use MuJoCo forward kinematics without a graphics context. Paired file
orchestration is tested with a renderer stub; rendered behavior remains unverified.

## Exact conductor commands

From `~/Desktop/Research/wbr-wt-simcam-imu`:

```bash
~/Desktop/Research/wbr-lab-ops/.venv/bin/python .github/run_unittest.py tools/simcam_imu
python3 tools/lint_markdown.py docs/simcam_imu/README.md docs/simcam_imu/WORKLOG.md docs/simcam_imu/REVIEW.md
~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m tools.simcam_imu.tilt_source ~/wbr-evidence-archive/imu-view-live-20261030/imu_view_run.csv
~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m tools.simcam_imu.run docs/simcam/example_box132.json --imu-csv ~/wbr-evidence-archive/imu-view-live-20261030/imu_view_run.csv --imu-start 12 --record /tmp/wbr-simcam-imu-12s/frames --out /tmp/wbr-simcam-imu-12s/timeline.csv
```

The last command needs an unrestricted Mac graphics context and an empty/absent
record directory. It runs both trajectories and writes 61 ticks per run,
122 PNGs, two timelines, a joined comparison and metadata. Its path is a fresh
example; an existing nonempty `frames` directory is rejected rather than cleared.

## Review focus and recommendation

Run the paired command, retain its output/error, and inspect both views at shared
ticks. Evaluate the stated height-error hypothesis using current-cluster errors
when both planes are valid and the target is visible before contact. Report
visibility/plane loss and rate-driven SETTLE separately from height errors and
advisory equality. The brief's PR #170 static MAE of 0.21 mm is not reproduced here.

The default trajectory passes through the box. Axle-before-face is not proof of
no intersection, and synthetic contact telemetry does not reflect a wheel lifted
by roll. Hand acceleration, unknown board-to-robot mounting, ideal depth and the
assumed body trajectory limit inference to this replay; no robot safety or
hardware perception accuracy result follows.

Claude handoff: review `docs/simcam_imu/REVIEW.md` after the conductor appends paired
render commands/results and limitations; no PR exists from this worker.
