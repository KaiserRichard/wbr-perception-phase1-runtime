# 2026-10-21 — codex-k camera open-loop follow-up

- Scope: dedicated `chatgpt/20261021-camera-openloop` worktree; worker only.
  No delegation/chat contact, native replay/build, Pi/SSH, shared checkout,
  calibration, control/PPO/student exercise changes or merge.
- Read AGENTS, profile, CURRENT and appended Claude clean-loop review.
- Added `align_replays.py`, `analyze_openloop.py` and focused NumPy tests.
  No C++/runner/batch changes; original evidence is read-only.
- Documentation changes: offline README CLI/math/interpretation additions and
  this session log. Main worklogs/reviews/decision log remain conductor-owned.

## Executed analysis and tests

Mac Python 3.11.0rc2, NumPy 1.26.4. From the dedicated worker checkout:

```bash
ARCHIVE=/Users/quockaiser/wbr-evidence-archive/camera-recording-20261021-01
BATCH="$ARCHIVE/clean-loop-mac-01/three-replays-02"
K_ANALYSIS="$ARCHIVE/claude-review-followup-01/k-analysis"
python3 scripts/camera_day/offline/align_replays.py \
  "$BATCH/replay-1" "$BATCH/replay-2" "$K_ANALYSIS/alignment-02"
python3 scripts/camera_day/offline/analyze_openloop.py \
  "$BATCH/replay-1" "$BATCH/pairs.csv" "$K_ANALYSIS/archived-replay-1-segments-01" \
  --settings "$BATCH/stereo.yaml" --log "$BATCH/replay-1.log" \
  --expected-pairs 2215 --jump-threshold-m 0.25 --physical-return owner-reported
python3 scripts/camera_day/offline/analyze_openloop.py \
  "$BATCH/replay-2" "$BATCH/pairs.csv" "$K_ANALYSIS/archived-replay-2-segments-01" \
  --settings "$BATCH/stereo.yaml" --log "$BATCH/replay-2.log" \
  --expected-pairs 2215 --jump-threshold-m 0.25 --physical-return owner-reported
python3 -m unittest discover -s scripts/camera_day/offline -p test_align_replays.py -v
python3 -m unittest discover -s scripts/camera_day/offline -p test_analyze_openloop.py -v
git diff --check
```

- All three analysis commands exited 0. Initial successful alignment retained
  at `alignment-01`; `alignment-02` records final code after stricter integer
  validation. No native replay repeated. All output paths exclusive-created.
- Alignment: 2,215 exact shared integer stamps; source schedules identical;
  zero unmatched tracked stamps. B→A proper rotation, determinant
  1.0000000000000013, scale fixed at 1, all fit ranks 3.
- Before-fit RMS/median/p95/max: 0.025700952 / 0.016693385 / 0.040769750 /
  0.099151104 m. After-fit: 0.009977410 / 0.006658158 / 0.012041390 /
  0.113615177 m. RMS fitting does not minimize the maximum residual.
- Fitted translation [-0.0055066521, -0.0026139044, 0.0066538824] m;
  rotation, singular values, exact residual stamps and input/code hashes in
  `alignment-02/report.json` and `residuals.csv`. Agreement only, no GT claim.
- Archived replay 1/2 segment diagnostics each observed 2,215 tracked frames,
  map 0, no tracking loss; endpoint 0.018319191 / 0.005408242 m. Both correctly
  withheld a disabled-loop drift candidate because original settings enable LC;
  replay 2 also has a loop log marker. These are historical runs only.
- 15 alignment + 14 open-loop tests PASS (29 total, no skips); CLI output and
  overwrite refusal exercised. Rigid/reflection/no-scale/degenerate tests and
  exact/malformed/unequal stamps covered; loss/map/translation/rotation jumps
  cannot bridge segment geometry. Main CI runner does not discover these two
  suites automatically; explicit commands above are required.

## Read-only runtime inspection / conductor handoff

- Early handoff: `/private/tmp/wbr-camera-review-20261021/k-runtime-ready.md`.
  Exact exclusive single-run Python dispatch, derived settings, hashes and
  copy/analyzer commands. All 2,215 pairs, 1x, existing headless binary, no batch.
- `System.cc:101–105,213` passes `loopClosing` to the loop closer;
  `LoopClosing.cc:324–328` returns false when disabled. `Run():112,121` gates
  the only merge/correction call sites (181,183,274). Local BA/maps remain active.
- `ldd` resolves existing ORB library; runner/library/source hashes recorded in
  handoff. Missing container `rg` was handled by read-only `grep`.
- Later `docker exec` failed because container was stopped externally; worker
  did not restart it. Read-only `docker cp` preserved LoopClosing source/header
  under `k-analysis/runtime-inspection-01` and completed final inspection.
- Potential upstream disabled-mode defect: constructor initializes
  `mpLastCurrentKF`, but not `mpCurrentKF` (header 175); early disabled return
  skips its assignment, while `Run():296` copies it to `mpLastCurrentKF` for a
  possible later dereference. Static gating is proven; native success is not.
  No worker runtime patch/build/run. Handoff updated with this source limitation.
- Native outcome remains conductor-owned: no claim here about future loss/maps,
  successful completion or drift. Segment eligibility needs complete start-to-
  return coverage, disabled settings, clean event evidence and owner-reported
  return; physical alignment, smaller corrections and local BA remain limits.
- PR attachment tool discovery found no available attachment capability;
  code/docs are pushed normally, raw data and reports stay outside git.
