# 2026-10-24 afternoon — detector bias fix, speed-up, advisory link (Claude 2)

Branches (pushed, not merged): `claude2/20261024-demo` (detector), `claude2/20261024-advisory-link`
(link, based on demo). Owner approval needed to merge.

## 1. Evaluate + bias fix — DONE (`claude2/20261024-demo`, 8407715, 09e3ee9, 3faf796)
- Causes: forward was optical Z (+(H−h)·sin pitch ≈ +3 cm); height p95 took the top-face noise tail;
  width ptp included flying edge pixels. Fixes: ground-frame coords from the plane, top-face height
  from near-horizontal local normals, lateral edge filter + p0.5–p99.5 width, k-th nearest face,
  2-cell cluster linking.
- MEASURED, all frames, 7 box runs ≤ 13 cm: height −0.2..+0.4 cm, distance −1.6..+0.3 cm,
  width −1.3..+1.7 cm; 2.45 cm book now UNCERTAIN (correct). W1 1.006 m (PASS). Table:
  `tools/obstacle_decision/results/lab-20261024/`.
- Open: B-H05-D1p3 books touch the lamp base → STOP (safe); W2 −5 % (setup); settings chosen on
  all runs, no held-out set; synthetic sweep still within 1.1 cm height / 4.4 cm distance / 1.8 cm width.
- Pi 5 detector time: 118 → 67 ms p50 (not throttled).

## 2. Pi → STM32 link — BUILT, hardware UNVERIFIED (`claude2/20261024-advisory-link`, c6432b5)
- codex-k wrote it; Claude 2 reviewed and committed. Type 4 TerrainAdvisory (ADVISORY_SPEC layout),
  new type 5 AdvisoryEcho (PROPOSED). Firmware only validates/echoes, stale after 300 ms, no actuation.
  Prebuilt bin SHA-256 f1982bc5…d717cf. `make -C tools/link_proto test`, `make -C tools/link_bench test`
  pass (one flaky sim-timing failure seen in 1 of 5 runs, not reproduced).
- On the Pi against the firmware simulator (pty, not UART): B-H08 bag, 139/139 echoed, 0 loss,
  detector+decision p50 75 ms, CRC/sequence/session/non-finite rejected with the right reason,
  400 ms silence → stale, then recovery. Sim RTT is not UART timing.
- Pi prepared: `/dev/ttyAMA0` = RP1 uart0 on GPIO14/15, `stm32flash` installed, clone
  `~/wbr-link-20261024`, venv `~/venv-link`.
- Next: owner wires Nucleo (power from Pi 5V → E5V with JP5 on E5V, no USB cable today), flash over
  the ROM UART bootloader (BOOT0 → VDD), run synthetic + bag replay on real UART, logic analyzer.
- Needs firmware-owner review before any use on the WBR STM32H7.

## Nucleo state (evening)
- Wired to the Pi, powered via E5V; running the OS-project firmware (`A5 5A` frames at 921600 baud,
  matches heterogeneous-edge-ai-os `protocol/`). MCU TX → Pi RX verified. BOOT0 did not take effect.
- Coordinator decision: overwrite only after a verified flash backup. Script on the Pi:
  `~/wbr-link-20261024/nucleo_backup_flash.sh` (reads 512 KB twice and compares them, refuses to write
  if the backup is not usable, then writes the bench bin and starts it). Not run yet: it needs BOOT0 + RESET.
  An unattended watcher that would flash automatically was blocked by the permission classifier, so
  flashing waits for the owner's go.

## Real UART run (19:00 local) — `claude2/20261024-advisory-link` ecca446
- OS-project firmware backed up (512 KB, double read identical, sha256 6d3aeb36…5d4beb09) in
  `~/wbr-evidence-archive/nucleo-backup-20261024/`, then bench firmware flashed over the ROM UART
  bootloader (`tools/link_bench/pi/stm32boot.py`; stm32flash could not sync).
- MEASURED: health 3000/3000, RTT P50 4.07 ms, faults rejected, 150 ms silence rule exact.
  Advisory 900/900 synthetic and 139/139 B-H08 replay, RTT P50 2.8 ms, detector P50 78 ms.
  Details: `tools/link_bench/results/20261024-nucleo/README.md`.
- To do: set VTOR in the bench firmware (it does not run after bootloader GO); logic-analyzer timing;
  restore the OS firmware from the backup when that project needs the board.
