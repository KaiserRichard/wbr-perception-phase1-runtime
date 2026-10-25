# Live advisory link — 2026-10-24

- Worktree/branch: `wbr-wt-c2-advisory-link`, `claude2/20261024-advisory-link`; changes intentionally uncommitted and unpushed.
- Added `advisory_link.py --ros --duration 60` (default duration): aligned depth + color CameraInfo subscriptions, best-effort depth-1 QoS, single-slot newest-frame worker, detector/temporal policy, existing UART Runner, Pi monotonic receipt-to-write timing, and dropped-frame summary count.
- Factored `handle_ros_frame` to accept duck-typed images and a Runner; test uses a fake 16UC1 Image and fake link. Moved rosbags imports inside bag replay so the shared `decode_depth` helper can load without bag dependencies.
- Added `lab-day-20261026/live_chain.sh`; follows the 24 Oct 640×480×15 Hz aligned-depth RealSense settings and runs the live chain for 60 s. Updated the LIVE checklist.
- `make -C tools/link_bench test`: PASS, 10 tests, one skipped (QEMU toolchain unavailable).
- `python3 -m unittest discover -s tools/obstacle_decision/tests`: BLOCKED at `test_replay_bag` import (`mcap_ros2` missing). Attempted install into `/tmp/wbr-advisory-tests`; package-index DNS failed. Core suite separately: 5/5 PASS.
- `git diff --check`, Python AST syntax checks and `bash -n lab-day-20261026/live_chain.sh`: PASS.
- UNVERIFIED: ROS 2 runtime/API compatibility on Pi, actual RealSense topic/QoS/profile, UART wiring/MCU response, measured live throughput/drop/latency, and full obstacle bag replay suite. No Pi/hardware command was run.
