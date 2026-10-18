# Review: T23 gate-to-tool index

## Verdict

**APPROVE-WITH-FIXES** — the index now covers the additional tools present in
this worktree and corrects identified coverage and criterion-name errors.

## Findings

1. **High — merged tools were omitted.** The index omitted `lab/calib_result`,
   `tools/stamp_drift`, and `tools/perception_health/c/mcu`, despite all three
   being present and their READMEs describing relevant checks. It also marked
   the existing `stamp_drift` path absent. Added their commands, criteria or
   host scenarios, limitations, and hardware-run status; removed the stale
   absence claim. Fixed in [GATE_TOOLING.md](GATE_TOOLING.md:233),
   [GATE_TOOLING.md](GATE_TOOLING.md:692), and
   [GATE_TOOLING.md](GATE_TOOLING.md:751).
2. **Medium — ROS wrapper software evidence was misrepresented.**
   `ros2/wbr_orb_node` had no substantive entry, and the index said no criteria
   existed although its software checker emits `all`, `real`, and `emit`.
   Added the host-check command/IDs, documented fake-only Pi build and bag
   replay commands, and clarified the unbuilt/live limitations and hardware
   status. Fixed in [GATE_TOOLING.md](GATE_TOOLING.md:500).
3. **Medium — the N3 timestamp mapping used incomplete criterion names.** The
   mapping omitted the per-topic `topic:<name>:` prefix emitted by
   `rosbag_qual`. Corrected these IDs and added the stamp-drift fit and
   continuity IDs to the timestamp mapping. Fixed in [GATE_TOOLING.md](GATE_TOOLING.md:682).

## Verification

Exact commands and captured output are in [2026-10-18-gate-tooling-review-tests.log](2026-10-18-gate-tooling-review-tests.log).
The post-fix runs passed: calib_result (8 tests), stamp_drift (25), clockmap
(37), rosbag_qual (41), N3 metrics (11), MCU receiver parity (normal and
sanitized runs), and ROS wrapper (19). All three Python CLI help checks
accepted the documented flags. `git diff --check` passed for the changed
index. Generated MCU build files were removed after verification.

## Remaining items

- No Pi hardware commands were run; all new hardware-run entries remain NONE.
- The ROS 2 / ORB wrapper build and live behavior remain unverified as stated in
  its README.
- The ticket's requested gate index is documentation; no project gate status
  changes follow from fixture or host-test results.
