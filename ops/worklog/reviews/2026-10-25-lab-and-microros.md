# 2026-10-25 — live LED tests, map run, micro-ROS integration (Claude 2)

Merged to main today: #140 LEDs+planner, #134 Foxglove demo, #141 firmware proposal + DM-jump analysis,
#142 lab fixes (range/height hysteresis), #143 /terrain_advisory topic + bridge, #144 micro-ROS F446, #145 dense map.

MEASURED
- Live (cardboard rig, D435 29 cm, ~13°): empty NONE 553/553; books 4.6 cm JUMP 561/563, h 4.75 cm d 0.998 m;
  box 13.1 cm STOP then NONE on removal, h 13.4 cm d 0.993 m; UART 2.8 ms, no loss.
- Approach: detection at the 1.3 m limit, tape vs detector 1–3 cm; LED flicker at the range edge.
  Replay with hysteresis inside live windows: 156→2, 218→25 transitions.
- ORB-SLAM3 2 m line along the table: 2.009 m, one map, no pose jumps (return leg cut by the 45 s window).
- Dense map: 225 frames, 354k points @1 cm, table plane RMS 5.8 mm.
- micro-ROS on Nucleo-F446RE over USART1 (E5V power): STM32 acked 712/712 and 739/739 advisories from the
  13 cm box recording replayed through wbr_obstacle_node.
- Data: ~/wbr-evidence-archive/lab-day-20261025/ (120 files SHA-256 verified vs the Pi).

Decisions / facts
- Robot STM32 runs micro-ROS over USB CDC (lab senior; repo nguyenbinh-shark/Microros_H723_USB):
  advisory = /terrain_advisory Float64MultiArray (docs/interfaces/). Custom COBS/CRC link is bench-only.
- Nucleo USB (ST-Link) was unstable at home (disconnects); USART1 transport + E5V power is reliable.
- ST-Link SWD flashing needed --freq=100k; when it failed, the ROM UART bootloader (stm32boot.py) worked.

Open
- Firmware owner: add the subscriber (example in docs/interfaces/terrain_advisory_microros_example.c).
- Live ORB-SLAM3 + detector together, IMU, long loop with return check: during integration.
- Dense map is camera-aligned, not gravity-aligned.
