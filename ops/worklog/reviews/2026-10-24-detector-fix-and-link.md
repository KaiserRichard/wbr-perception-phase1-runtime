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
