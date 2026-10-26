# 2026-10-26 — Firmware study pack

- Read `ops/worklog/CURRENT.md` and `ops/USER_PROFILE.md`; worked on branch `claude2/20261026-lessons`.
- Inspected local CAN monitor, link bench, F446 micro-ROS receiver, advisory interface, and DM-jump integration analysis.
- Read the provided read-only `DM-jump` and `Microros_H723_USB` snapshots. Traced CAN timing/protocol, micro-ROS entity setup, AGV kinematics/watchdogs/RC logic, and WBR LQR/VMC/jump code with line references.
- Found requested directories `tools/agv_f446`, `tools/agv_f446_test`, and `tools/supervisor_demo` absent. Used available references and marked scope limits in the pack.
- Created `docs/lessons/README.md` and lessons 01–06. Each lesson is 150–300 lines and ends with implementation relevance and answered self-check questions in `<details>`.
- Corrected CAN BTR literal to `0x801A0002` after checking bit positions: 42 MHz / (3 × 14 tq) = 1 Mbit/s.
- No network, firmware build, test run, flashing, hardware operation, or motor command.
- Final lesson line counts: 247, 231, 219, 208, 188, 244; README 64.
- Changes are uncommitted and unpushed as requested. No temporary logs were needed.
