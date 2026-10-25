# F446 AGV home acceptance tooling

- Branch/worktree: `claude2/20261025-agv-hometest`; local, uncommitted. No branch switch, push, network use, or firmware edits.
- Added `tools/agv_f446_test/agv_home_test.py`: ROS graph/topic discovery; disabled output; forward, turn, common-ratio 20 rad/s saturation; 500 ms command timeout/status bit; NaN rejection; final disable. Saves `/motor_fb` samples to CSV and a run summary to JSON. ROS imports are deferred so pure checks run without ROS.
- Geometry/sign defaults: `WHEEL_RADIUS=0.060 m`, `WHEEL_BASE=0.345 m`, left sign −1, right sign +1 from read-only H723 `User/Config/robot_config.h`; kinematics, limit, topic and status contract from its `docs/topics.md`.
- Added beginner wiring/flash/agent/diagnostic guide `tools/agv_f446_test/HOME_TEST_GUIDE.md`. F446 pin mappings are marked as requiring confirmation against the firmware README. No live board test performed.
- Added standard-library tests under `tools/agv_f446_test/tests`; `python3 -m unittest -v`: 10 tests passed. `python3 -m py_compile agv_home_test.py tests/test_checks.py`: passed.
- Next: after firmware README/image and bench wiring are ready, compare node/topic and pin/baud choices, then run the live test against the Pi/F446 fake-motor setup and archive CSV/JSON output.
