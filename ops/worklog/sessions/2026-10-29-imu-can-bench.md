# IMU + dual-CAN bench check — 29 Oct 2026

- Branch `claude2/20261029-imu-can-bench`; tool `tools/imu_can_bench/`. No motors connected or commanded.
- Partial work found: codex runs in `~/.codex/worktrees/f446-home-test/wbr-lab-ops`. Codex flashed `canfix01`
  (SHA256 `f614cde0…f296`, source d163063) at 07:10. Evidence is in `~/wbr-evidence-archive/f446-home-test-2026102{8,9}/`.
  - The handoff hash `fcc29359…517e` is the older `agv_f446_home_loopback.bin`. The board was running
    `canfix01`; MEASURED by backup prefix.
- ST-LINK on the Mac cannot reach the target (SWD error, per the 28 Oct log), so all flashing went through the
  Pi UART ROM bootloader (`tools/link_bench/pi/stm32boot.py`): BOOT0 + RESET.

## Runs
- Stale session: the agent from Codex logged its output to a dead pipe, so I replaced it.
  - The first `kill -INT` did not stop it, and two agents briefly shared the port. Fixed with SIGTERM.
  - Board LD2 off, D6 blinking, i.e. stuck after a failed `setup()`. One RESET gave a full session.
  - MEASURED: 288/288 status samples = 32 over 60 s, no session drops.
- IMU on `canfix01` (10 s, rclpy, sensor-data QoS) — MEASURED, PASS:
  - 19.49 Hz, |a| 9.629 m/s²
  - gyro bias −3.24/+0.02/−0.18 °/s
  - 0 all-zero samples
  - The first attempt received nothing: reliable QoS vs a best-effort publisher. Fixed.
- Built `imu_can_bench.bin` (8.6 kB, SHA256 `75489187…7411`). The first build passed; 6 checker unit tests pass.
- Flash: owner CONFIRMED in chat. BOOT0 + RESET; backup read twice, identical, SHA256 `da44b209…5ad4`;
  prefix = canfix01; `verify True`.
- run-01 FAIL 0/6: the capture was garbled because it was taken before the clean RESET. Not a firmware result.
- run-02 MEASURED, SUMMARY PASS 10/10:
  - pins all as expected
  - WHO_AM_I 0x68 @0x68, 99.48 Hz, |a| 9.629, gyro bias −3.25/+0.02/−0.18 °/s
  - CAN loopback 10/10 ×2
  - 1900/1900 round trips, TEC/REC 0, no bus-off in window
- CANH-unplug test: skipped by owner → UNKNOWN. Termination resistance: UNKNOWN (no multimeter).
- Restore `canfix01`:
  - Bootloader-jump path: FAIL ×3.
    - (1) False sync: the letter `y` in app output looks like ACK 0x79.
    - (2) RX overrun during I2C reads; fixed by sending 5 ms per byte.
    - (3) Trailing `\n` locked autobaud; removed.
    - Still no bootloader reply after the jump. Cause INFERRED: bootloader interface probing; not proven.
  - BOOT0 path PASS: backup identical (SHA256 `6996ba79…cc02`, prefix = bench image), `verify True`.
  - After RESET: participant + 6 datawriters, 91/91 status = 32 in 20 s.
- **Board state at end: `canfix01` (f614cde0…f296), read-back verified, session up.**
  The agent runs on the Pi (log `agent-02.log`).
- Evidence: `~/wbr-evidence-archive/imu-can-bench-20261029/` (also on the Pi `~/wbr-evidence/imu-can-bench-20261029/`).

## Findings about canfix01 (source, INFERRED; not fixed here)
- A failed `setup()` loops forever (red blink); only RESET recovers. Connected pings use 1 attempt / 100 ms.
- `one_init()` waits on INAK with no timeout before micro-ROS starts; a dominant CRX hangs the boot.
- `loopback_fake` emulates only the left wheel, its echo applies `LEFT_SIGN` twice, and both fake motors share ID 1
  on the joined bus, so `agv_home_test.py` cannot reach 8/8 on this bench regardless of wiring.
- IMU: no re-init after one failed read; an all-zero read is not rejected.

## Night, 22:50–00:30 (fake-motor fix)
- Sign convention: H723 `docs/topics.md` defines `/motor_fb` in wheel frame, so `agv_home_test.py` defaults go to +1/+1 (thresholds unchanged).
- canfix02 (two-way fake, 1 Mbit/s): flashed (backup = canfix01, `verify True`), started via GO, session up.
  - MEASURED: home test 5/8; feedback [0,0]; status 16, no fresh or bus-off bit.
- codex-e review (read-only, log in the side-session notes, `codex-logs/FAKEMOTOR-REVIEW-e.log`):
  - Identical command IDs from both controllers on one bus are never ACKed. INFERRED as the main cause.
  - `status(now)` freshness underflow. CONFIRMED in source.
  - Both fixed in canfix04 (built, not flashed).
- Flashing problems, all MEASURED:
  - Reopening the port after the bootloader started: no reply.
  - Running app bytes faked an ACK (`expected ACK, got a5`).
  - `flash_safe.py` (ACK only on a quiet line) synced and flashed once: PASS.
  - Bench image started by GO prints garbled UART (v2 and v3), so 1M results are invalid and the magic reset is never received: BLOCKED.
- End state: flash = bench 1M v3 `575eb692…`, BOOT0 fitted, Pi jobs stopped, port free.
