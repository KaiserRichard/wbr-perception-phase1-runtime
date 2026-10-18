# T25 independent review

## Verdict

**APPROVE-WITH-FIXES**

The submitted fuzzing work is sound after the targeted review fixes below. The parser implementations were not changed. The bounded fuzz suite passes, including the previously omitted MCU-side `ph_rx` decoder, and the root runner discovers both the Makefile and Python unittest paths.

## Ranked findings and fixes

1. **High — required MCU decoder was not fuzzed** (`tests/fuzz/Makefile:11-18`, `tests/fuzz/c/fuzz_ph_rx.c:1`). The binding review ticket explicitly requires a driver for `tools/perception_health/c/mcu/ph_rx`. The submitted change only fuzzed the host codec and incorrectly documented `ph_rx` as absent. Added a sanitizer-backed deterministic driver covering mutated health frames, arbitrary bytes, valid health delivery, and valid heartbeat/session delivery; added it to `make test`.

2. **High — the full test runner did not discover this ticket** (`tools/run_all_tests.sh:98-110`). Added `tests/fuzz` to the optional Makefile loop and unittest-directory discovery. Both paths now execute successfully in the full runner.

3. **Medium — corpus claims did not match test inputs** (`tests/fuzz/test_fuzz.py:52-92`). The submitted tests rewrote one tracked corpus file during execution and reconstructed the link and rosbag inputs from other source files, leaving two committed corpus files unused. The tests now read each committed corpus file, compare it to its cited source/golden value, exercise the Python link message encoder against the frozen vector, and explicitly include malformed/oversized length mutations.

4. **Medium — the timeout helper hid unexpected parser exceptions** (`tests/fuzz/test_fuzz.py:32-34`). `IndexError`, `KeyError`, and `OverflowError` were treated as normal malformed-input rejection, contrary to the requirement to expose uncaught exception types. Narrowed the allowlist to the documented `ValueError`, `struct.error`, and `UnicodeError` paths and added a regression test.

## Requirement check

- Python mutation coverage: PASS. Six unittest cases cover perception-health framing/payloads, link_proto Python COBS/message encoding, both CDR header readers, trajectory parsing, truncation, bit flips, arbitrary bytes, explicit length lies, reversed timestamps, nonfinite values, and accepted-frame rebuilding.
- C mutation coverage: PASS. Host perception-health, link_proto, and MCU `ph_rx` drivers use deterministic seeds and AddressSanitizer/UndefinedBehaviorSanitizer.
- Bounds/configuration: PASS. Iteration counts, seed, and timeout are centralized in `fuzz_config.json`; the final fuzz target completed in 14.3 seconds on this Mac.
- Documentation/reporting: PASS. README, REPORT, FINDINGS, and this review identify evidence labels and hardware limitations; no crash, hang, or incorrect accept was found.
- Root runner integration: PASS for the ticket suite. `tests/fuzz` is discovered as both optional suite types.

## Exact verification

`make -C tests/fuzz test` — exit 0; 6 Python tests passed; `fuzz_ph`, `fuzz_link`, and `fuzz_ph_rx` each completed 1,200 mutations under ASan/UBSan.

`bash -n tools/run_all_tests.sh` — exit 0.

`bash tools/run_all_tests.sh` — exit 1 overall. The summary reported `make:tests/fuzz:test PASS`, `python:tests/fuzz PASS`, and `python:calibration/allan/tests PASS`. The only existing unrelated failure was `tools/link_bench` (Mac pseudo-terminal rejects 460800 baud); no changes were made to that suite.

`git diff --check` — exit 0.

## Remaining open items

No Pi, STM32 hardware, UART transport, interrupt concurrency, or safety behavior was verified. The bounded deterministic workload can miss defects outside its corpus and mutation budget. The unrelated `tools/link_bench` full-runner failure remains for its owning ticket.
