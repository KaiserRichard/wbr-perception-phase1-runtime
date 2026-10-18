# T7 independent review

## Verdict

**APPROVE-WITH-FIXES.** The confirmed defects below were fixed in this worktree and regression-tested. The implementation remains a software prototype; no firmware or hardware gate is approved by these fixture results.

## Ranked findings

1. **High — cross-clock subtraction could produce falsely fresh pose age** (`py/sender.py:20-22,95-108`; regression at `tests/test_perception_health.py:42-44`). The sender mapped D435i time into the event's `pi_domain` (the README example used `host_steady`) and subtracted it from `CLOCK_MONOTONIC_RAW` send time. These are distinct clocks without a mapping between them. The sender now accepts only `CLOCK_MONOTONIC_RAW` mappings, samples send time after acquiring the serial-write lock, and the example uses the matching domain.
2. **High — healthy perception input could promote FRESH, and the model did not preserve upstream rearm/latch rules** (`py/supervisor_model.py:25-28,39-42,108-129`; regressions at `tests/test_perception_health.py:63-72,91-101`). The model could reach FRESH using only this optional health report, rearm immediately, or transition out of FAILSAFE on a session change. FRESH now also requires an independently supplied primary-supervisor freshness input. FAILSAFE remains latched through all received events and session changes; rearm is local-only and requires the configured uninterrupted healthy interval.
3. **High — transit allowance was omitted at the report boundary** (`py/supervisor_model.py:56-66,97-103`; regression at `tests/test_perception_health.py:74-76`). A health frame with age below HOLD could leave an already FRESH model in FRESH even when age plus `transit_bound_us` crossed HOLD. The model now applies the conservative age including transit allowance when accepting the frame and while evaluating later age.
4. **Medium — the model accepted duplicate or out-of-order frames** (`py/supervisor_model.py:67-83`; regression at `tests/test_perception_health.py:83-89`). Replayed frames could renew health timers because the reference event omitted protocol sequence validation. The model now checks the shared u16 sequence with wrap-aware ordering, validates receipt time against `now_us`, and rejects duplicates/old frames before refreshing timers.
5. **Medium — non-boolean camera IMU and mapping validity values could be treated as true** (`py/perception_health.py:58-64`, `py/sender.py:17-19,86,109-111`, `py/supervisor_model.py:97-103`; regressions at `tests/test_perception_health.py:46-52,78-81`). The C decoder rejected IMU values outside 0/1, but Python decoding and sender coercion could treat any nonzero/truthy value as true. Python decoding now rejects invalid encodings; sender accepts JSON `true` only for positive claims and marks malformed degraded flags conservatively.
6. **Medium — initial downgrade reasons did not match the upstream enum, and reset semantics omitted relocalization** (`py/supervisor_model.py:92-103`, `SPEC.md:15,19,52`). LOST and other degraded reports now use existing `SOURCE_AGE_TIMEOUT` / `SOURCE_AGE_HOLD` reasons. The reset-counter contract now explicitly includes relocalization discontinuities.

## Upstream compatibility and motion-safety check

- Confirmed the frame header against `upstream_snapshot/hea_proto.h` and `PROTOCOL.md`: `A5 5A`, version, type, little-endian shared u16 sequence, length, payload, and little-endian CRC-16/CCITT-FALSE over version through payload. The CRC known vector is `123456789 -> 0x29B1`; captured upstream frames are parsed by the fixture tests.
- Confirmed v3 HEARTBEAT payload layout is `linux_send_ns:u64 LE` followed by `session_id:u64 LE`, exactly 16 payload bytes; the new test checks byte positions and total frame size against the snapshot contract.
- Compared state/reason numeric values to the upstream snapshot: INIT/FRESH/HOLD/FAILSAFE are 0/1/2/3; NONE, READY, RESULT_SILENCE, HEARTBEAT_TIMEOUT, RESULT_TIMEOUT, REARM, CLOCK_REGRESSION, SESSION_CHANGE, INVALID_CONFIG, SOURCE_AGE_HOLD, SOURCE_AGE_TIMEOUT are 0 through 10 in that order. The model uses the corresponding names.
- The health message can only downgrade the independent primary state. It cannot promote to FRESH by itself, send a motion command, or clear a latched FAILSAFE. Only the local `rearm()` path can clear the model latch after the healthy interval.

## Requirements check

- Fixed 19-byte v3 `0x05` payload, little-endian codec, Python/C frozen-vector parity, CRC known vector, and byte-at-a-time parser: covered.
- D435i-to-Pi mapping, source-age saturation, clock-domain table, proposed thresholds in one config with rationales, reset/merge/relocalization semantics, sender heartbeat/session and JSONL/stdin serial path: covered. Mapping provenance/session validity is supplied by the producer and is not independently established by this prototype.
- Supervisor HOLD/FAILSAFE policy, receipt and heartbeat timeouts, LOST handling, map-reset downgrade, shared sequence behavior, explicit rearm, and non-promotion: covered by model and regression tests.
- Pty sender/parser scenarios, sender silence, corruption recovery, map-reset field, saturation, and C99 codec: covered.
- README commands and limits, REPORT, and saved test output: present and updated.
- Source naming for ORB-SLAM3 Tracking states points to official `include/Tracking.h`; that third-party file is absent from this checkout, so enum identity is disclosed as not locally verified.

## Test results after fixes

- `python3 -m unittest discover -s tools/perception_health/tests -v` — 24 tests passed, including the C99 `cc -std=c99 -Wall -Wextra -Werror` fixture build.
- `python3 -m unittest discover -s tools/clockmap/tests -v` — 37 tests passed for the imported mapping dependency.
- Exact commands and complete outputs are saved in `tests/last-run.log`.

## Remaining open items

- No Pi, UART, camera, STM32 firmware, or physical timing behavior was tested. Hardware transit bounds and all timing thresholds remain PROPOSED.
- The upstream firmware has not implemented or accepted `0x05`; receiver integration, validation against the selected ORB-SLAM3 `Tracking.h`, and mapping/session production remain separate work.
- A passing software fixture suite is not a hardware or system gate PASS.
