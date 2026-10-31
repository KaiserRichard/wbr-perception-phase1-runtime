# Jump gate worker run log

2026-10-30; worktree `wbr-wt-jump-gate`, branch `chatgpt/20261030-jump-gate`.
Edits are confined to `tools/jump_gate/` and `docs/jump_gate/` as requested.
This file records runs and documentation changes within that allowed scope.

## Implemented

- Pure Python gate, named ASSUMED thresholds, explicit UNKNOWN handling, bounce,
  abort, post-contact history reset and distinct fresh-plane dwell.
- Replay joins source packet times with synthetic telemetry; original frame
  timestamps survive held samples. Added CSV-only mode before renderer creation.
- MuJoCo demo reuses wbr_pose five-bar pose XML and timeline; obstacle color uses
  gated output. Synthetic phases and assumed confidence/quality are labeled.
- Added README with source mapping, policy, commands and limitations; exported
  the complete default lab-day timeline for independent replay.

## Actual runs

- Existing environment: `~/Desktop/Research/wbr-lab-ops/.venv/bin/python`.
- `python -m tools.jump_gate.demo --csv-only docs/jump_gate/timeline.csv`:
  exit 0, 6,594 ticks, 603 source packets, duration 59.911952393 s.
- Default CSV phase counts: STAND 6,416; CROUCH 57; FLIGHT 61; LAND 5;
  SETTLE 55. All non-STAND outputs are UNCERTAIN, confidence 0.
- First suite run: `python3 .github/run_unittest.py tools/jump_gate`:
  20 tests passed, 2 files discovered, 0 skipped. Added slow-plane cadence and
  saved-artifact replay coverage afterward.
- Final suite run with the same command: exit 0, **22 tests passed**, 2 test files
  discovered, 0 skipped. Includes replay and comparison of every saved CSV tick.
- `python3 tools/lint_markdown.py docs/jump_gate/README.md docs/jump_gate/RUN_LOG.md`:
  exit 0, **0 issues across 2 files**.
- Non-rendering MuJoCo scene compilation and pose/color application at stand,
  crouch, thrust, flight, landing and settle: exit 0. Verified installed Renderer
  height/width signature and viewer text API by inspection; no renderer created.
- No SSH/Pi, motor operations, firmware, commits, pushes or PR actions performed.

## Handoff

The conductor renders using the README command, checks the visible box/robot and
overlay, and handles commit/PR review. Rendering is explicitly untested here.

## Gate/history follow-up — 2026-10-30

- Worktree `wbr-wt-gate-fix`, branch `chatgpt/20261030-gate-fix`; changes limited
  to the owner's gate, simcam and simcam_imu allowlist. Session/current profile
  read; this allowed log records the follow-up instead of editing `ops/` files.
- Implemented maximum absolute pitch/roll rate confidence scaling in STAND with
  `ASSUMED_WOBBLE_LIMIT_DEG_S = 60`. Above that limit inhibits to SETTLE; exactly
  the limit retains the raw advisory at zero confidence. Missing/invalid rates
  still enter UNKNOWN. The strict 5 deg/s rule remains for SETTLE recovery.
- Removed simcam's per-inhibited-tick decision wipe. Detector and decision
  histories reset only on CROUCH entry or the first tick after FLIGHT.
- Added both-axis/signed wobble tests, extreme-rate recovery, confidence boundary
  and raw-UNCERTAIN coverage; retained all jump inhibition and saved CSV tests.
  Added a simcam test using real decision/gate and supplied geometry to check
  plane-cache/EMA/vote continuity and both reset boundaries without rendering.
  Updated the IMU adapter integration test for persistent history and 15/80 deg/s.
- Actual runs (first implementation run; all exit 0, zero skips):
  `python3 .github/run_unittest.py tools/jump_gate`: 26 tests, 2 files;
  `~/Desktop/Research/wbr-lab-ops/.venv/bin/python .github/run_unittest.py tools/simcam`:
  22 tests, 3 files;
  `~/Desktop/Research/wbr-lab-ops/.venv/bin/python .github/run_unittest.py tools/simcam_imu`:
  21 tests, 2 files. No test failures encountered.
- Documentation changes: updated jump_gate README policy/constants and worked
  confidence example; added simcam_imu README Re-run commands, pending acceptance
  and the scorer's known NOT SCORED exit behavior. Earlier measured results and
  saved timeline remain historical evidence, unchanged by this follow-up.
- `python3 tools/lint_markdown.py docs/jump_gate/README.md docs/jump_gate/RUN_LOG.md docs/simcam_imu/README.md docs/simcam_imu/WORKLOG.md docs/simcam_imu/REVIEW.md`:
  exit 0, 0 issues across 5 files. `git diff --check`: exit 0. Final tracked
  changes are confined to 8 allowed files; the untracked scenario copy is untouched.
- No rendering, SSH/Pi, motors, commits, pushes or PR actions attempted.
  The conductor owns rendered STOP-count acceptance and all 13 scenario re-runs.
