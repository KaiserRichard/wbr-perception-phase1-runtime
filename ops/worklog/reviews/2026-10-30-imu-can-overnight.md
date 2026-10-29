# IMU/CAN bench — overnight summary (29→30 Oct)

- DONE: both CAN transceivers and the MPU6050 work. Bench image run-02: 10/10 PASS at 500 kbit/s (1900/1900 CAN round trips, TEC/REC 0; IMU 0x68, 99.5 Hz, |a| 9.63 m/s²). PR https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/155
- DONE (7/8 on hardware): fake-motor fix for the joined bench bus, draft PR https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/156 (base: PR #154 branch).
  - **canfix04_500k home test, MEASURED:** forward [5.000, 4.999]; turning [1.897, 4.770]; saturation [20.000, 19.999]; timeout stop 0.63 s; fresh bits seen.
  - **Fixes that got there:**
    - two-way fake;
    - distinct motor IDs per bus (codex-e found that identical IDs from both controllers collide without ACK);
    - status freshness underflow;
    - wheel-frame test signs per H723 `docs/topics.md`;
    - 500 kbit/s bench rate.
- PARTIAL: the remaining FAIL is "motors disabled at test end" (feedback stayed 0.667 rad/s). INFERRED cause: `disable_hw()` ignored a refused stop frame when the mailboxes were busy. Fixed in canfix05 (e2f4802, SHA256 `13279727…`), **built, not flashed**.
- BLOCKED (owner's hands): flash canfix05. Leave BOOT0 fitted, then:
  1. On the Pi run `python3 ~/imu-can-bench/flash_safe.py --out <dir> --flash <canfix05.bin> --sync-seconds 600`.
  2. Press RESET once and don't touch the board for 7 min (a RESET mid-read caused `short read` twice tonight).
  3. Remove BOOT0 and press RESET.
  4. Start the agent and run `agv_home_test.py`.
- UNKNOWN: 1 Mbit/s on these transceivers (bench images started via GO print garbled UART, so both 1M runs are invalid); CANH-unplug test; 120 Ω value.
- BOARD STATE: flash = `agv_f446_home_canfix04_500k.bin`, SHA256 `d33f7c975520e65398588d4c3f1c4a3e8d26f6ddf6be6364ecaf5b2da99545bd`, read-back verified. BOOT0 fitted, so it starts in the ROM bootloader. canfix01 backups are in `~/wbr-evidence-archive/imu-can-bench-20261029/`.
- Pi released for the camera reboot; no jobs left; ttyAMA0 free.
