
## Update 00:45
- The owner's first two reflash tries failed (stopped at 64 KB; `short read at 0x8002d00`). No erase happened in either. A third try with the flasher waiting before RESET: PASS (backup identical `41de9967…`, `verify True`).
- **canfix04_500k home test: 7/8 PASS (MEASURED).** Forward [5.000, 4.999]; turning [1.897, 4.770]; saturation [20.000, 19.999]; timeout stop 0.63 s; fresh bits seen.
- FAIL: "motors disabled at test end" (feedback stayed 0.667 rad/s). The stop frame can be lost when the TX mailboxes are busy. Fixed in canfix05 (e2f4802, `13279727…`, PR #156). Not flashed.
- **Board state:** flash = `agv_f446_home_canfix04_500k.bin` SHA256 `d33f7c975520e65398588d4c3f1c4a3e8d26f6ddf6be6364ecaf5b2da99545bd`, verified. BOOT0 fitted.
  - To run it: remove BOOT0, press RESET, start the agent.
- Pi released for the camera reboot. No jobs running; ttyAMA0 free.
