# T22 independent review

## Verdict: REQUEST-CHANGES

The implementation meets the receiver, policy, wraparound, parity, and documentation requirements after the latch API fix below. One required integration item remains: `tools/run_all_tests.sh` does not invoke this Makefile target. Its Make suites are a fixed list at `tools/run_all_tests.sh:99-101`, and the Python test discovery paths do not include nested `tools/perception_health/c/mcu/`. The ticket-owned-path restriction does not permit changing that runner here.

## Ranked findings

1. **P1 — Fixed: candidate could clear its own latch.** `ph_policy_rearm()` set `latched` to zero and reset the recommendation, contrary to the requirement that this optional module never clear a latch. Removed that API and its unused `rearm_healthy_us` policy field. Added `sticky_latch_test()` in `test_mcu.c:29-46`, which triggers LOST, then feeds a new session heartbeat and a healthy report and asserts FAILSAFE remains latched.
2. **P2 — Open: the aggregate test runner skips this suite.** `tools/run_all_tests.sh:99-101` invokes Make targets only for five hard-coded directories; the newly added `tools/perception_health/c/mcu/Makefile` is absent. The new suite passes when run directly, but does not satisfy the ticket's `run_all_tests.sh` discovery requirement. The runner is outside the ticket-owned path and was not edited.

## Requirement check

- `ph_rx` accepts only protocol v3 health and heartbeat messages, reuses the existing C health decoder and CRC, and uses fixed storage without allocation or floating point.
- The ISR-to-task queue is fixed-size SPSC with ownership and platform atomicity/barrier caveats documented. Queue overflow drops the report and increments its counter.
- `ph_policy` only returns `NONE`, `HOLD`, or `FAILSAFE`; it does not expose FRESH or latch-clear operations. It uses MCU u32 modulo elapsed arithmetic and does not compare Pi timestamps with MCU time.
- Generated stepwise vectors exercise sequence gaps/duplicates, CRC rejection, age HOLD/FAILSAFE, unavailable and saturated age, LOST, silence, and u32 wraparound. The saved excerpt fixture is identified as synthetic estimator output.
- README includes firmware call sites, calculated airtime at both requested baud rates, and measured host-only `size` output. REPORT records host-only limitations and a proposed commit message.
- Outstanding: aggregate runner integration described above. Hardware behavior, target memory ordering, timing, and safety remain unverified and are documented as such.

## Tests after fixes

Exact commands and output are saved in [`tests/last-run.log`](tests/last-run.log).

- `make -C tools/perception_health/c/mcu test` — PASS; strict C99 build, parity harness, and address/undefined sanitizer run passed.
- `python3 -m unittest discover -s tools/perception_health/tests -v` — PASS; 28 tests.

## Remaining open items

- Add this Makefile suite to the aggregate runner in a change that owns `tools/run_all_tests.sh`, then rerun the aggregate suite.
- Review ISR/task publication barriers and atomicity for the actual STM32 toolchain and memory model before firmware adoption.
- Verify target ABI, integration, UART behavior, and safety on the target; host fixtures do not establish those properties.
