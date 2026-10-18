# Independent review — R_T19

Verdict: **APPROVE-WITH-FIXES**. All confirmed T19 defects below were fixed in
this worktree. No unresolved implementation requirement remains. This verdict
approves software diagnostics only; N3 and hardware timing remain unverified.

## Scope and evidence

Read COMMON.md, R_T19.md, T19_stampdrift.md, the required project documents,
clockmap and rosbag qualification tools/READMEs, and the change against
`origin/main`. `git status --short` was initially clean. The branch also differs
from origin/main outside this ticket (lab session and perception_health work);
those inherited differences were not changed. All review edits and logs are
under `tools/stamp_drift/`. No applicable AGENTS.md was present in this worktree
or its ancestor directories.

The original 8 stamp_drift tests and 37 clockmap tests passed before review.
They did not cover the defects below. Eight selected new regression methods
were subsequently run against the original committed analyzer loaded read-only
from `git show HEAD:tools/stamp_drift/analyze.py`; they exposed 9 assertion
failures and 3 errors, including configuration subtests. That expected failing
run, exact command and output are in [tests/review-before.log](tests/review-before.log).
The log's wrapper exits zero after confirming the regression suite failed.

## Ranked findings and fixes

Line references below point to the reviewed, fixed files.

1. **P1 — Missing COMMON result contract and incorrect exit codes**
   ([analyze.py:532](analyze.py#L532), [analyze.py:555](analyze.py#L555)).
   Previously any completed analysis returned 0, including FAIL/BLOCKED, and
   no result.json, criterion table, host/times, saved raw input or raw hashes
   existed. Added contract generation using existing qual_common helpers,
   0/1/2/3 exits, saved raw/config/independent clock declarations, and faithful
   analyze-only evaluation. Missing/corrupt evidence and NumPy are BLOCKED;
   argument and explicit configuration errors exit 3. Regression tests cover
   every status, hash verification, input deletion after capture, missing saved
   files, corrupt saved metadata, stale report removal, and input overwrite
   rejection.

2. **P1 — Every bag payload decoded as a first-member Header**
   ([analyze.py:183](analyze.py#L183)). The reader ignored topic types and
   serialization, allowing plausible false timestamps from TF sequences and
   unstamped context or aborting on normal mixed bags. It also never counted
   empty declared sensor topics. Now only explicitly supported sensor types
   are decoded; skipped types are listed, unsupported serialization is refused,
   full Header strings are validated, and empty supported topics BLOCK.
   Reused lab/rosbag_qual's little-endian decoder; retained a minimal validated
   big-endian fallback because that decoder only supports little endian.
   Its aggregate reader cannot expose paired raw timestamps. Tests cover mixed
   bags, empty topics, both byte orders, corrupt Headers and serialization.

3. **P1 — Residuals lost nanoseconds at realistic receive epochs**
   ([analyze.py:289](analyze.py#L289)). Absolute receive epochs were converted
   to float and subtracted from absolute floating predictions, despite the
   centered underlying fitter. A UTC-scale stream with 1 ns jitter reported
   zero residuals. Residual arithmetic now uses integer-centered receive
   deltas; regression recovers nonzero ~1 ns residuals. The original offset
   and post-step drift tests now also assert recovered values within tolerance.

4. **P2 — Failure precedence and degenerate evidence**
   ([analyze.py:226](analyze.py#L226), [analyze.py:344](analyze.py#L344)). A
   two-row reversal was BLOCKED rather than FAIL, an empty iterable raised,
   and constant receive clocks caused fitting exceptions. Reversals/steps now
   FAIL before unavailable fits are considered; empty and degenerate evidence
   BLOCKS without crashing. Dedicated tests reproduce each original failure.

5. **P2 — Unbounded whole-bag allocation**
   ([analyze.py:471](analyze.py#L471)). analyze_path read the entire DB3 into
   bytes just to hash it, then separately opened SQLite. That could exhaust
   the Pi's memory on ordinary recordings. Reused streaming SHA-256 and kept
   timestamp-only SQLite iteration. A regression forbids DB3 read_bytes;
   a saved 266 MB mixed-topic bag also completes offline analysis.

6. **P2 — Timestamp domain fabricated option readback**
   ([analyze.py:449](analyze.py#L449)). SYSTEM_TIME/HARDWARE_TIME forced
   global_time_enabled=false; a declared global-time domain forced true.
   Effective frame domains do not prove option readback. Added independent
   --global-time-enabled metadata, UNKNOWN by default, preserved for re-analysis.
   CSV receive-clock identity is also explicitly UNKNOWN rather than being
   described as a rosbag recorder clock. Tests cover all domain declarations.

7. **P2 — Unsafe configuration accepted**
   ([analyze.py:73](analyze.py#L73)). Nonfinite rejection scales, a one-sample
   fit minimum, missing required residual percentiles, and a non-object config
   could silently weaken rejection or crash reporting. Validation now rejects
   these and requires source/rationale strings. Configuration regression
   subtests cover each case. All chosen detector limits remain PROPOSED in the
   single config.json; continuity's zero-event criterion is configured there.

8. **P2 — Segment cap overshot its configured limit**
   ([analyze.py:250](analyze.py#L250)). A configured cap of 3 produced 4
   segments because multiple pieces split in one pass. The splitter now
   reserves space for remaining pieces and enforces the cap. A detected
   discontinuity is still reported if the cap prevents splitting, including
   cap=1. Tests cover both the overshoot and capped detection behavior.

9. **P3 — Evidence fixture precision and incomplete real-bag coverage**
   ([tests/fixtures/real_saved_evidence.csv:12](tests/fixtures/real_saved_evidence.csv#L12)).
   One adapted SDK stamp was 100 ns above the exact saved decimal value.
   Corrected it, preserved the first 12 original Accel JSONL lines, and added a
   Decimal conversion provenance test. Added portable Header prefixes and DB3
   timestamps from the existing rosbag qualification fixture, independently
   verified against its original source file and SHA-256. Replaced the old
   report's synthetic-only DB3 claim with precise converted-bag limitations.

## Requirement audit

| Requirement | Reviewed result |
|---|---|
| T19.1 CSV or DB3 input, minimal CDR, reuse lab reader where possible | Both inputs supported; type-aware decoder reused; SQLite timestamp-pair iteration and big-endian fallback remain local for API limitations. |
| T19.2 Robust fit, ppm, residual P50/P95/P99/max, lower envelope, steps/reversals, IR–IMU differences | Present in JSON/Markdown; known offset/drift/jitter/outlier and post-step recovery asserted; nanosecond receive-epoch regression added. |
| T19.3 Read/reuse clockmap | Centered _fit_affine imported without modifying clockmap; full suite passes. |
| T19.4 JSON + Markdown and inference limits | Both emitted; offset/latency inseparability and effective-domain UNKNOWN are explicit; COMMON result.json added. |
| T19.5 Synthetic and real fixtures | Known synthetic streams plus exact adapted SDK rows and real converted ROS Header excerpts; source provenance independently checked. |
| COMMON contract, replay, statuses and exits | result.json fields, hashes, table, saved raw/config/run metadata and analyze-only tested; FAIL precedes BLOCKED. |
| COMMON thresholds and labels | Numeric detector limits in config.json, each with PROPOSED source/rationale. Input observations are MEASURED; derived fits are CALCULATED; identity without run evidence is UNKNOWN. |
| COMMON tests/logs/docs | Final commands/output saved; README describes Pi/offline commands, criteria and limits; REPORT updated and proposed commit message included. |
| COMMON ownership, software-only and repository restrictions | Only owned paths edited; no hardware, network, GUI, installs, commit, push or Git mutation. No shell scripts added, so bash -n is not applicable. |

## Final test results

**MEASURED software verification: 114 tests passed, zero failures/errors.**

| Exact command | Tests |
|---|---:|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/stamp_drift/tests -v` | 25 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/clockmap/tests -v` | 37 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s lab/rosbag_qual/tests -v` | 41 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s experiments/2026-09-12-pi5-native-sensor-validation -p test_n3_metrics.py -v` | 11 |

All imported suites, including the historical manifest dependency, were run.
Complete final output is in [tests/last-run.log](tests/last-run.log).

The additional read-only source check and its exact command/output are in
[tests/real-evidence-run.log](tests/real-evidence-run.log). It verifies the 12
portable CDR prefixes and timestamps against the source bag SHA-256
`d9adff8ae17b4e9f8b89bf6a8a798ca1abfd19bf06575efdd7ea1befe05ea1fe`,
analyzes all 5,372 sensor rows (447 IR1, 447 IR2, 1,507 Accel, 2,971 Gyro),
and verifies all 12 adapted SDK rows against their exact saved source. No large
raw bag was copied into the worktree.

## Remaining open items

No confirmed software defect remains open in the owned scope. No external
clockmap/lab-tool defect was confirmed; those tools were left untouched.

Hardware and physical N3 remain **UNKNOWN / unverified**. The converted real
bag sets receive and Header stamps equal: its calculated zero drift is a
conversion artifact, not measured device synchronization or ROS recorder
arrival timing. The adapted SDK fixture uses camera IMU CLOCK_MONOTONIC pairs,
not the STM32 body IMU or ROS recorder pairs. A live ROS recording with effective
timestamp-domain and option-readback evidence is still needed. Detector
sensitivity, absolute latency and camera–IMU physical synchronization were not
qualified. Proposed thresholds are diagnostic settings, never gate approval.

Changes are uncommitted for the conductor. Proposed commit message:
`Fix and independently validate stamp drift diagnostics`.
