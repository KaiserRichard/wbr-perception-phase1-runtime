# T3 bench twin redo worklog — 2026-10-30

## Scope and changes

- Read ops CURRENT/USER_PROFILE and existing IMU/link/partial-twin sources.
- Reworked only `tools/bench_twin_fw/**`; no ops logs changed because this
  ticket restricts allowed files. This file records the documentation changes.
- Replaced partial IMU/RobStride default with a combined DM F446 image:
  IMU I-lines, interrupt UART RX, advisory parser/echo/LEDs, CAN1 commands,
  four fake CAN2 motors, CAN1 feedback and counters/latency.
- Added DM C codec/model, portable text/multiplex/advisory module, host byte
  helpers and compiled-C Python tests. Link codec wrappers use canonical source.
- Rewrote README protocol/ID/pin/LED/bandwidth/owner-flash documentation;
  added REVIEW with concrete conductor commands and limitations.
- Decision: source-selected hips 6/8 (right pair) plus wheel IDs 0/1 on one
  joined bench wire; original left hips omitted. No IDs renumbered.
- Decision: reply IDs `0x700+id` are ASSUMED; supplied reference does not specify
  configured reply IDs. Save-zero absent in the four supplied files; no guessed
  source-supported opcode or save-zero feature claimed.
- Kept RobStride behind explicit compile-time AGV-codec flag, default excluded.
  Optional build does not change the DM runtime or implement AGV velocity mode.

## Actual execution and fixes

- First real `make -C tools/bench_twin_fw`: PASS, 16948 text / 0 data /
  5920 BSS; no build error or missing dependency.
- First host test run: 9/9 PASS. No failing test was hidden/skipped.
- Follow-up: evaluate newly received MIT torque before feedback; document
  stable UID-derived session rather than claiming a unique boot ID.
- Follow-up inspection: timeout abort must verify the mailbox still holds
  that motor's requested frame, since a completed mailbox can be reused.
  Corrected that condition and rebuilt successfully.
- Fixed inherited incorrect partial-doc assumptions: RobStride default,
  invented IDs, stale red blink, and 37-byte IMU budget. Final I-line maximum
  is CALCULATED 64 bytes. Conservative TX budget is 9148 B/s at 115200 8N1,
  including 10 immediate advisory replies plus 10 stale periodic echoes/s;
  the initial 8638 B/s calculation covered only 10 total echoes/s.
- `make -B -C tools/bench_twin_fw AGV_CODEC=1`: PASS; optional codec compiles
  with warnings as errors and is discarded when unreferenced.
- Restored/rebuilt default DM image; final build and tests recorded below.
- Source citation pass corrected local IMU-bench line references against
  `nl -ba`; Markdown lint reported 0 issues before handoff.

## Final results (MEASURED on Mac only)

- `make -C tools/bench_twin_fw`: PASS; final ARM size text=17020,
  data=0, bss=5920, dec=22940. Binary length 17020 bytes.
- `python3 -m unittest discover -s tools/bench_twin_fw/tests -v`: 10/10 PASS.
- `arm-none-eabi-nm -u build/bench_twin.elf`: no undefined symbols.
- `shasum -a 256 -c SHA256SUMS`: `bench_twin.bin: OK`.
- Final binary SHA-256: `eb79538a8e01aca0080aacb45c5d6c7cc59719e05747b5f726cb9b4c14397a7a`.
- Lint command: `python3 tools/lint_markdown.py tools/bench_twin_fw/README.md tools/bench_twin_fw/WORKLOG.md tools/bench_twin_fw/REVIEW.md`.
  Result: 0 issues across 3 files. Raw final command output: VALIDATION.txt.
- No SSH, serial device access, real motor commands, flash, MuJoCo rendering,
  Git write, commit, push or PR operation. All hardware timing is unmeasured.

## Read-only source fingerprints (MEASURED)

- `DM_Motor/dm4310_drv.c`: `0c395a6da558e97ce64e49d70faa147a5feaa62b0505367eb4f6d9190066dd2b`
- `DM_Motor/dm4310_drv.h`: `5df502e5793dec3f8924551aebc2c531f5c212519344de8b3cac6181b23a751b`
- `chassisL_task.c`: `a1c17c1ecc72b94264f4efaf56b29d348a96f0b8e3c815a4dde14aaa4e33cf81`
- `chassisR_task.c`: `8865ea4e9bd7a245bba08cab58c1db670b8d12b2482c6deae3625486be0b4b51`

The tests extract verbatim reference C functions into a temporary translation
unit, stub only CAN send/HAL types, and compare actual C bytes/conversions.
The source driver hash is checked unchanged after the suite.
