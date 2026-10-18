# T10/T10b independent review — 2026-10-18

## Verdict

**APPROVE-WITH-FIXES.** The integration meets the ticket requirements after
three targeted analyzer hardening fixes. No unresolved correctness defect was
found in the T10b HOLD-versus-FAILSAFE reconciliation.

## Findings, ranked

1. **MEDIUM — raw evidence could pass without a HEARTBEAT.**
   `e2e_pty_test.py:222-226` previously considered a capture intact when its
   health frames, CRCs and sequences were valid, even if all HEARTBEAT frames
   were absent. The `no_mapping` state assertion could then pass without
   exercising the sender's session/heartbeat path. Fixed by requiring at least
   one health frame and one HEARTBEAT in transport integrity, and by counting
   HEARTBEAT frames explicitly. Regression: `test_analyzer_requires_heartbeat_evidence`
   in `tests/test_integration.py:207-228`.

2. **MEDIUM — missing capture prerequisites violated the result contract.**
   `e2e_pty_test.py` previously raised an internal-error exit (3) while
   attempting to read a missing real-replay fixture, without writing
   `result.json`. A missing fixture/tool is unavailable evidence and must be
   BLOCKED. The `--outdir` path now preflights required inputs and delegates to
   the analyzer, which writes the common BLOCKED result. Regression:
   `test_missing_capture_prerequisite_returns_blocked_result` in
   `tests/test_integration.py:245-254`.

3. **LOW — malformed read timing could create negative simulated MCU time.**
   `e2e_pty_test.py` previously subtracted capture start from saved read times
   without checking that the values came from the same nondecreasing host
   `CLOCK_MONOTONIC` observation. A crafted capture could therefore feed
   negative or regressed times into the supervisor model. Analysis now rejects
   timestamps before capture start or earlier than the previous read. Regression:
   `test_analyzer_rejects_read_timestamp_before_capture_start` in
   `tests/test_integration.py:230-243`.

## Requirements checked

- Read `COMMON.md`, T10 and T10b, plus the adapter README/header, sender,
  reviewed `SPEC.md`, `supervisor_model.py`, and the read-only upstream
  supervisor snapshot.
- `vio_to_pose_events.py` preserves camera-domain source epochs, requires an
  explicit session-bound `CLOCK_MONOTONIC_RAW` mapping for age, maps all
  available exact ORB names, and marks collapsed/unavailable fields degraded.
- PTY scenarios cover no mapping/HOLD, mapped OK/FRESH, LOST latch,
  sender-stop receipt silence, synthetic and saved real-replay snapshots, and
  measured frame/byte rates versus calculated 115200/921600 8N1 capacity.
- README documents exact offline and future Pi commands and states that real
  ORB execution, live serialization, UART hardware and STM32 parsing remain
  unverified.
- Retained evidence is summary-plus-hashes only and remains below 200 kB; full
  raw captures are regenerated in temporary directories.
- The reviewed T7 model now correctly keeps unavailable age in HOLD while
  independent receipt/heartbeat watchdogs remain active. Valid saturated age,
  LOST, sequence handling, transit allowance, latching and rearm behavior were
  checked against SPEC and upstream semantics.

## Test results after fixes

Exact commands and complete output are retained in the listed logs:

- `python3 -B -m unittest discover -s tools/perception_health/integration -p 'test*.py' -v` — **24 passed**, `tests/last-run.log`.
- `python3 -B -m unittest discover -s tools/perception_health/tests -v` — **28 passed**, `../tests/last-run.log`.
- `python3 -B tools/perception_health/integration/e2e_pty_test.py --outdir <temporary>/full --summary-outdir <temporary>/summary` — **10/10 criteria PASS**, `tests/e2e-run.log`.
- `python3 -B tools/perception_health/integration/e2e_pty_test.py --analyze-only <temporary>/full` — **10/10 criteria PASS**, `tests/analyze-run.log`.
- Python compilation, `git diff --check`, and the C99 codec suite passed.

## Remaining open items

- This is software/fixture evidence only; no Pi execution, live ORB binding,
  real camera-to-Pi clockmap collection, physical UART, STM32 parser, or safety
  supervisor integration was exercised.
- The saved replay contains measured D435i associations but synthetic
  fake-engine estimates. The adapter still cannot recover exact collapsed ORB
  states, camera-IMU initialization, tracked-feature counts, or complete map
  reset history without producer changes.
- Synthetic clock exchanges, independent `primary_fresh=True`, thresholds and
  transit bound are ASSUMED/PROPOSED, not hardware-qualified limits. The
  unpaced replay exceeds calculated 115200-baud ideal capacity; PTYs do not
  emulate baud or latency.
- The branch also contains unrelated `tools/n4b_offline/` deletions relative
  to `origin/main`; they were outside this review's owned path and were left
  untouched.

Proposed commit message from the implementation remains:

```text
fix(perception-health): reconcile integration with reviewed health policy
```
