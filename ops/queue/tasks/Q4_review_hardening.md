# Q4 — independent review and hardening of existing tools, dir: tools/ (may edit tools/take_tools, tools/calib_tools,
# tools/link_proto, tools/frames, tools/clockmap) and write tools/REVIEW_Q4.md
Read queue/tasks/COMMON_QUEUE.md first. Act as a skeptical reviewer. For each tool: re-derive its key conventions from
primary sources (Kalibr yaml-formats, ORB-SLAM3 Settings.cc/ImuTypes, librealsense ros2 writer, REP-103/105, CRC-32C/COBS
specs), look for correctness bugs (transform direction, units, off-by-one, wrap, integer/float precision of ns stamps,
silent fallbacks), and missing tests. Fix confirmed bugs with a failing-then-passing test each; do not refactor style.
Run every test suite (unittest dirs and make -C tools/link_proto test) and record results. REVIEW_Q4.md lists findings
ranked by severity with status FIXED / OPEN / NOT-A-BUG and evidence.
