# Independent review — T11 platform environment check

## Verdict

**APPROVE-WITH-FIXES**

## Ranked findings

1. **Medium — stand-in board identity incorrectly failed the target check** ([`manifest.yaml:5-6`](manifest.yaml)). The measured manifest pins came from a 4 GB Rev 1.0 stand-in, while the project target is the 8 GB board. Treating both as REQUIRED exact values would fail the target on known hardware identity alone. Changed both fields to INFO and explicitly marked them for re-pin after review of 8 GB target evidence. Added a regression in [`test_check_platform.py:24-33`](tests/test_check_platform.py) proving Rev 1.1 / 8 GiB values remain recorded and do not fail the environment result.

## Requirements review

- Manifest values and source evidence: present for the requested platform, ROS/RealSense, ORB-SLAM3, dependencies, clocksource, governor, swap, time sync, recording mount/free space, and D435i udev rule fields. Camera firmware is labeled expected and INFO because the check does not access the camera.
- Board-specific stand-in values: corrected as described above; both are INFO until re-pinned.
- Read-only collection, per-field comparison, raw command output, result contract, snapshot, candidate manifest, and offline analyze-only: implemented. Candidate output is written under the run directory.
- Fixture and test coverage: measured snapshot fixture, pass/fail comparisons, missing-fact blocking, missing-command handling, analyze-only, and target-board regression are covered.
- README and REPORT: describe use, criteria, limits, hardware verification status, risks, and proposed commit message.
- Hardware validation: not performed; fixture success is explicitly not a gate PASS.

No other confirmed defects or missing ticket requirements were found during review. The manifest still needs a reviewed refresh from the 8 GB target before it can serve as that board's pinned baseline.

## Fixes and verification

- Updated `manifest.yaml`, `README.md`, and `REPORT.md` to mark board model/RAM as informational and pending re-pin.
- Added `test_target_board_model_and_ram_are_recorded_without_failing_standin_pins`.
- Ran: `python3 -m unittest discover -s lab/platform_env/tests -v`
- Result: **7 tests passed**. Exact output is saved in `tests/last-run.log`.
