# Advisory bridge — 2026-10-25

- Added `tools/link_bench/pi/topic_to_nucleo.py`: pure eight-value payload validator/encoder, ROS best-effort subscriber, serial forwarding, echo matching, RTT percentiles, and shutdown summary.
- Added ROS-independent encoder tests under `tools/link_bench/tests`.
- Added `/terrain_advisory` Float64MultiArray output to `wbr_obstacle_node`, including advisory code, measurements, confidence, plane validity, sequence, and age placeholder.
- Added `lab-day-20261025/replay_chain.sh`: sources ROS and `WS`, starts obstacle and bridge nodes, applies `near_m=1.3`, plays the MCAP at 1.0x, and stops child process groups on exit.
- Ran with the requested dependency path: `PATH="/private/tmp/claude-501/-Users-quockaiser-Desktop-Research-wbr-wt-claude2/86f1e3fb-27f1-4b36-ad4d-133cc09819f7/scratchpad/venv/bin:$PATH" make -C tools/link_bench test`.
- Result: 13 tests passed; QEMU firmware test skipped because `qemu-system-arm` and `arm-none-eabi-gcc` are unavailable.
- Also passed `git diff --check`, `bash -n lab-day-20261025/replay_chain.sh`, and Python byte compilation for the bridge and obstacle node.
- No ROS bag, Pi, or Nucleo live replay was run in this environment. Generated `tests/test_leds` test binary was removed after the run.
