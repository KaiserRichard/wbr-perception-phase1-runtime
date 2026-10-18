# T10 implementation and evidence — 2026-10-18

Owned-path implementation is complete under `tools/perception_health/integration/`.
**Acceptance remains FAIL because the unmodified T7 supervisor violates the
requested unmapped HOLD-only behavior.** Exact ORB-state recovery from current
adapter snapshots is also unavailable. These upstream issues cannot be repaired
within T10's binding ownership rule; they are recorded below for the owners.
No files outside the owned directory were edited. No Git write, network,
hardware, camera, serial-device, installation, SSH or GUI operation was run.
Only local PTYs were opened.

## Built

- `vio_to_pose_events.py`: streaming converter and explicit four-stamp clockmap
  validation using the existing ClockMap library. Camera integer epochs remain
  in their declared source domain; only T7 computes mapped age at send time.
  Missing mapping is invalid, never synthesized from receipt time. Missing exact
  tracking state, camera-IMU initialization, feature counts and reset provenance
  remain explicitly unavailable/degraded. Available adapter reset/epoch counters
  are retained modulo u16; map-only transitions are labeled as local observations
  with incomplete reset coverage. Source/counter regressions stop conversion.
- `e2e_pty_test.py`: existing sender subprocess, `os.openpty()` transport, existing
  codec/parser and supervisor model; no replacement implementation. Five captures
  cover synthetic no mapping, mapped OK, LOST/recovery latch, sender EOF/silence,
  and all saved real-association snapshots. Saved raw bytes/read timing support
  `--analyze-only`, the common result contract, SHA-256 manifests and short tables.
- `config.json`: the integration's numeric diagnostic limits and UART comparison
  assumptions, with rationale/evidence labels. T7 timing policy is reused and
  saved with each capture. Silence-only overrides are explicitly diagnostic.
- README: exact offline commands, field/clock/availability contracts, criteria,
  result limitations and the future Pi FIFO-to-UART pipeline with its prerequisites.
- Tests and small retained evidence, including a verbatim four-line real fixture
  with source hash. No individual artifact exceeds 1 MB; nothing was added to data/.

## Validation (MEASURED on the Mac)

Host: macOS 15.7.9, x86_64, Python 3.11.0rc2; the existing NumPy dependency was
available. No Pi execution is claimed.

```bash
python3 -B -m unittest discover -s tools/perception_health/integration/tests -v
python3 -B tools/perception_health/integration/e2e_pty_test.py -v
python3 -B tools/perception_health/integration/e2e_pty_test.py \
  --outdir tools/perception_health/integration/evidence
python3 -B tools/perception_health/integration/e2e_pty_test.py \
  --analyze-only tools/perception_health/integration/evidence
```

Final suite: **21 tests: 20 passed, 1 expected failure** (exit 0).
`tests/last-run.log` retains the complete unittest output. The script entry point
was also exercised before the last test addition. Tests cover all seven exact
ORB names, ambiguity and missing-field handling, reset wrapping/derivation,
clock identity/fit rejection, regressions, CLI success/errors, PTY state sequences,
raw-byte corruption, and PASS/FAIL/BLOCKED analyzer paths. The analyzer PASS
fixture intentionally contains one unmapped report, which legitimately HOLDs;
it cannot establish sustained HOLD. The separate multiple-report expected-failure
test exposes that regression and fails as an unexpected success if T7 is fixed.

Full capture and independent saved-raw analysis both exit **1 / FAIL**, with
**9 criteria PASS and 1 FAIL (`no_mapping`)**. See `tests/e2e-run.log`,
`tests/analyze-run.log`, `evidence/result.json` and each scenario's `trace.json`.
All five transport criteria PASS. Synthetic mapped reports become FRESH; LOST
latches FAILSAFE through subsequent OK. EOF terminates the sender. With explicitly
isolated receipt deadlines, simulated MCU silence enters HOLD/RESULT_SILENCE and
FAILSAFE/RESULT_TIMEOUT. All 445 real-association snapshots reach the sender and
receiver; unknown age/degraded flags are preserved and no result becomes FRESH.

Python syntax compilation and `bash -n` of the documented live pipeline passed.
`git diff --check` passed; status shows only the new integration directory.

## Throughput evidence

**MEASURED on this Mac**, sender-process observation window including startup,
imports, and EOF exit; counts include received HEARTBEAT frames:

| Capture | Frames/s | Bytes/s | Utilization at 115200 | Utilization at 921600 |
|---|---:|---:|---:|---:|
| no_mapping | 9.70 | 264.35 | 0.023 | 0.003 |
| mapped_ok | 11.73 | 314.33 | 0.027 | 0.003 |
| lost_latched | 14.77 | 402.40 | 0.035 | 0.004 |
| sender_stops | 13.76 | 375.06 | 0.033 | 0.004 |
| real_replay (unpaced burst) | 1201.70 | 33631.41 | 2.919 | 0.365 |

**CALCULATED** 8N1 capacities are 11,520 and 92,160 bytes/s, respectively.
The saved replay is deliberately unpaced; its burst exceeds ideal 115200 capacity.
A PTY ignores wire-baud throttling. This is a software write/count comparison,
not measured Pi performance, UART throughput, sustained real VIO rate or latency.
Exact counts, observation durations and host provenance are in `evidence/metrics.json`.

## Upstream defects and limits requiring owner follow-up

1. **MEASURED T7 defect — unavailable age becomes immediate source timeout.**
   In `tools/perception_health/py/supervisor_model.py:47–57`, the next update ages
   `last_age` before checking whether the preceding age/mapping flags were valid.
   T7's sender correctly transmits UINT32_MAX for unavailable age. The first
   health report enters HOLD/SOURCE_AGE_UNAVAILABLE at lines 75–76, then the next
   health/heartbeat/tick sees that sentinel beyond the source timeout and latches
   FAILSAFE/SOURCE_AGE_TIMEOUT. Captured sequence is HOLD → FAILSAFE → FAILSAFE
   despite continuously delivered synthetic OK reports. This directly contradicts
   T10's HOLD-only requirement and T7's README statement. The owner must preserve
   age validity in deadline evaluation while retaining independent receipt and
   heartbeat watchdogs. T10 does not mask the sentinel or modify the model.

2. **SOURCE-SUPPORTED producer loss — exact states cannot be reconstructed.**
   `tools/vio_adapter/orb_engine.cpp:16–19` collapses SYSTEM_NOT_READY/NO_IMAGES_YET,
   OK/OK_KLT and RECENTLY_LOST/LOST. The snapshot schema emits only those collapsed
   states. No converter can recover the exact original value from saved snapshots.
   T10's proposed optional `orb_tracking_state` name extension preserves every
   exact name when present; without it, conservative fallback is marked degraded
   and `tracking_exact=false`. Adapter LOST is conservatively mapped to wire LOST,
   which may latch FAILSAFE even for native RECENTLY_LOST. The producer owner must
   retain the exact ORB name to distinguish those policies. No upstream edit made.

3. **SOURCE-SUPPORTED availability gaps.** The current EstimateSnapshot/JSONL
   producer does not report camera-IMU initialization or tracked features.
   Tracking does not establish initialization. The existing health payload has no
   per-field unavailable bits for feature count/reset; T10 uses T7's degraded flag
   plus explicit JSONL availability metadata. Placeholder zero is never evidence
   of a measured count or known reset history. Real ORB map/reset observation is
   already limited as documented in the adapter README; local counters cannot
   prove that every internal map discontinuity was observed.

4. **UNKNOWN live integration.** No live snapshot serializer/executable or real
   clock-exchange collector is present in this worktree. `replay_fake` stays fake,
   even in an optional ORB build. The README's future live command consumes an
   explicit proposed FIFO/session/map contract; it does not claim those missing
   producers exist. Static exchanges require caller-qualified session binding,
   validity and restart/invalidation policy; they cannot detect later unseen
   clock steps or authenticate a Pi boot ID. T7 does not verify that a declared
   Pi clock session is the sender's actual boot. No online sync service was added.

## Not verified / open risks

The real ORB-SLAM3 binding was not built or executed; real-replay estimates are
synthetic fake-engine outputs over MEASURED D435i input associations. The fixture
source SHA-256 is `14c6a1caf12bb2b458e96b09f7cef14620ae4bc883bc6f6c3efcc80b4062c7ce`.
No real camera-to-Pi raw-clock mapping, exposure semantics, clock-step response,
Pi scheduling/load, UART hardware, transit bound, STM32 firmware parsing or
supervisor integration was qualified. MCU receipt timestamps are simulated local
timer observations, with no Pi/MCU epoch subtraction. Power, thermal and storage
problems remain outside this software check. No safety/hardware gate is PASS.

Proposed commit message:

```text
feat(perception-health): integrate VIO snapshots with sender PTY evidence

Preserve unavailable clock/state/reset observables, exercise synthetic and saved
D435i association events through the existing sender and supervisor, and report
local throughput plus the upstream unmapped-age HOLD regression.
```

Changes are intentionally uncommitted for the conductor.
