# Overnight 2026-10-30: PIL bench rungs 3–4 (Mac only, nothing flashed)

- **DONE** host PIL (`sim/pil`): COBS + CRC-32C frames reusing `tools/link_proto`, lockstep MuJoCo stepper, fake MCU (same C behind a pty), 16 unit tests (15 pass, 1 QEMU test skipped). PR: https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/160
- **DONE, MEASURED (fake MCU):** Python LQR 160/160 and PIL 160/160, 0 outcome mismatches. Per-cell mean recovery equals the archived RESULTS table (e.g. 2 ms push 2.7432 s). Max PIL−Python difference: torque 2.0e-11 N·m, state 2.4e-12.
- **DONE, MEASURED (fake MCU):** unmodelled link latency of +2/4/6 ms (push, 2 ms and 5 ms profiles, 10 seeds): still 10/10; recovery 2.7448 → 2.7516 s at 2 ms. ASSUMED plant only.
- **CALCULATED:** 460800 8N1, 62 B STATE + 54 B TORQUE = 2.517 ms > 2 ms, so real-time 500 Hz lockstep over this link is impossible; lockstep (sim owns the clock) is the design.
- **DONE, BUILD ONLY:** F446RE firmware `sim/pil/firmware` (8.2 KB): USART2 ST-Link VCP, PA8 HIGH around `wbr_lqr_step`, DWT cycles in the reply. binary64 runs as soft-double on the M4, so the F446 timing is pessimistic vs the H7. Not flashed.
- **BLOCKED:** QEMU replay of the ARM binary. `brew install qemu` was still building dependencies at push time; the test skips until QEMU is installed.
- **Docs:** `docs/pil/DESIGN.md` (frame, rate, clock, latency, fault isolation), `docs/pil/LESSON.md` (why PIL ≠ balance, worked latency budget, Mermaid).
- **Owner on the bench:** `make -C sim/pil/firmware`; copy the `.bin` to NOD_F446RE; logic analyser on D7 (PA8). Run `sim.pil.run --port /dev/cu.usbmodem… --controllers pil --delays 5 --noise-seeds 5`, then compare the PA8 pulse width with `mcu_exec_s`. Commands: `sim/pil/README.md`.
- Limits: lockstep only; no retransmission; INFERRED F446 step ≈ 0.1–0.3 ms is untested; PIL cannot prove balance.
