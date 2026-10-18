# T14 independent review — 2026-10-18

## Verdict

**APPROVE-WITH-FIXES**

The implementation satisfies the T14 requirements in the reviewed source. The
ROS package and native ORB path remain intentionally unbuilt here, as required
by the ticket and documented in `REPORT.md`; that is an environment limitation,
not a host-core review failure.

## Findings and fixes

1. **Fixed — image rejection was misclassified as IMU loss**
   (`src/core.cpp:159-171`). A stereo pair rejected by `vio::Adapter` (for
   example, mismatched image dimensions) called `input_imu_loss()`, latched the
   whole session and falsely treated an image fault as lost IMU evidence. The
   rejection now increments the image/association invalid count and emits one
   drop event without being reported as an IMU loss; source clock/value faults
   still fail closed through their validation paths.
   `tests/core_test.cpp` and `tests/test_node.py` add the regression scenario,
   including a check that the image drop event is not duplicated.

2. **Fixed — root test runner omitted ROS package suites**
   (`tools/run_all_tests.sh:94-112`). The runner did not discover Makefile or
   Python unittest targets below `ros2/*/`. It now discovers both, preserving
   the existing non-empty/review-hardened Python runner behavior. This is the
   only edit outside the ticket-owned directory permitted by R_T14.

## Requirement checklist

- `ament_cmake` package, sensor-data QoS image/IMU subscriptions, exact source
  stamp stereo pairing, bounded IMU buffering, fake engine and optional
  `WITH_ORB_SLAM3`: present.
- Diagnostic `odom -> imu_camera` Odometry, original source image stamp, and
  sender-compatible JSONL with invalid mapping unless a qualified live map is
  configured: present.
- Monotonic observer receipt/processing/output events, queue depth, bounded
  drop-oldest queues and explicit loss counts: present.
- ROS-free core, Makefile target, exact pairing/coverage/drop/stamp tests and a
  real saved source-epoch fixture: present.
- README, REPORT, result-contract checker, PASS/FAIL/BLOCKED tests and saved
  `tests/last-run.log`: present.

## Verification

All commands were run from this worktree without hardware, ROS devices, serial
access, package installation, or network access.

- `make -B -C ros2/wbr_orb_node test` — **PASS**, 19 unittest tests, no skips.
- `make -C tools/vio_adapter test` — **PASS**, adapter probe plus 4 unittest
  tests.
- `make -C tools/ros2_bridge test` — **PASS**, 20 unittest tests.
- `make -C tools/runtime_observer test` — **PASS**, recorder probe plus 20
  unittest tests.
- `python3 ros2/wbr_orb_node/scripts/check_core.py --outdir /tmp/...` followed
  by `--analyze-only` — **PASS**, `all`, `real`, and `emit` criteria.
- `bash -n tools/run_all_tests.sh` and `git diff --check` — **PASS**.
- `tools/run_all_tests.sh` reported both
  `make:ros2/wbr_orb_node:test PASS` and
  `python:ros2/wbr_orb_node/tests PASS`. Its overall result was FAIL only for
  the existing `tools/link_bench` macOS pseudo-serial host simulator; that
  unrelated implementation was not changed.

## Remaining open items

Colcon/ROS Jazzy compilation, yaml-cpp linkage, native ORB-SLAM3 ABI and
shutdown, rosbag replay, D435i calibration and clock binding, live DDS loss,
Pi resource/thermal/power behavior, latency, tracking quality, and hardware
gate evidence remain UNKNOWN as recorded in `REPORT.md`. No gate is promoted.

Proposed commit message remains:

```text
feat(ros2): add bounded stereo-inertial ORB node on vio_adapter
```
