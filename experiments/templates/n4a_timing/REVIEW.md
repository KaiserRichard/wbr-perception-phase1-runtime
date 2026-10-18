# R_T15 independent review

## Verdict

**APPROVE-WITH-FIXES — T15 owned path only.** All confirmed defects within the
editable package were fixed and covered by regression tests. Hardware and
sustained real-time performance remain UNKNOWN; no project gate PASS is claimed.

Reviewed the original ticket and COMMON.md, required project documents, relevant
tool READMEs/source, the diff against origin/main and untracked working files.
The starting HEAD was `b6063cd8eb2607edabc248289c8310d49dca10d7`;
origin/main was observed at `c1b5919d7c04dba1e8c9319c96adcb0f924ba4a9`
during review and advanced independently. The original four ticket tests passed
before fixes; they did not exercise the default tools or missing-evidence paths.

## Ranked findings and fixes

Locations below refer to the corrected files in this directory.

1. **HIGH — default analyzer tools pointed outside the repository**
   (`analyze_n4a_timing.py:308`). The original `parents[2]` resolved to
   `experiments/`, so the documented command could not invoke either dependency.
   Corrected to the repository root. Regression:
   `test_default_tools_valid_and_repeatable` executes the real default accuracy
   and profile tools on a synthetic EuRoC trajectory.
2. **HIGH — one healthy run masked failed or absent repetitions**
   (`analyze_n4a_timing.py:315`, `analyze_n4a_timing.py:331`). Overall PASS was
   selected whenever any run was VALID. Missing latency with successful accuracy
   could also become FAIL rather than BLOCKED, and FAIL/BLOCKED exclusions could
   lack reasons. Added independent run check status, FAIL-before-BLOCKED
   precedence, declared-run completeness, explicit missing run names and reasons.
   Aggregates still include only VALID runs. Regressions: mixed healthy/throttle
   test, missing declared repetition, no runs, missing evidence, engine failure
   and allowed prior-throttle tests.
3. **HIGH — incomplete latency and stale outputs could qualify a run**
   (`analyze_n4a_timing.py:83`, `analyze_n4a_timing.py:131`,
   `analyze_n4a_timing.py:157`). Observer frame counts live inside their session,
   not at the top level; empty/nonfinite percentiles and failed tool output were
   not checked. Re-analysis also failed because accuracy output already existed.
   Added session-aware extraction, finite/nonempty/ordered metrics, observer
   loss/pair checks, explicit derived-output replacement and delegated accuracy
   `--overwrite`. Regressions: real default-tool repeat, event-session and loss,
   empty/nonfinite latency, stale latency and missing-tool tests.
4. **HIGH — successful wrapper exit hid failed engine or sampler capture**
   (`run_n4a_timing.py:419`, `run_n4a_timing.py:481`). The reviewed launcher saves
   engine exit status but can itself exit zero. The original capture ignored
   engine exit, sampler exit and metadata, then always returned zero. Capture
   now reads the engine receipt, requires successful sampler evidence, emits
   FAIL/BLOCKED accurately and cleans up child processes/log handles on errors.
   Analysis also requires capture and sample-count consistency. Regressions:
   sampler crash, engine failure/missing PID and mismatched metadata count.
5. **HIGH — preflight/evidence was not sufficient across the run set**
   (`run_n4a_timing.py:268`, `run_n4a_timing.py:431`,
   `analyze_n4a_timing.py:197`). Only the first run had a thermal/throttle check;
   unknown governor/cooling fields could pass; analysis ignored missing
   preflight and boundary throttle snapshots. Added inter-run preflight refusal,
   unknown-field blocking, before/after throttle checks and accurate throttle
   summary status. The actual runner's shared lock path is enforced for real
   invocations. Regressions: hot second run, hot/governor/busy-lock/missing-VC/
   unknown-resource preflight matrix and post-run throttle rejection.
6. **MEDIUM — result contract and replay were incomplete**
   (`run_n4a_timing.py:398`, `run_n4a_timing.py:506`,
   `analyze_n4a_timing.py:333`). Preflight wrote only `preflight.json`, combined
   analysis lacked required result fields, no offline preflight mode existed,
   and argparse usage returned 2 rather than 3. Added `result.json`, required
   provenance/criteria/hashes/tables, saved-snapshot replay and usage/internal
   exit 3. VideoCore output is retained verbatim, including absent final newline.
   Regressions: replay after removing fake hardware, missing saved snapshots,
   missing config, result-schema assertions and usage/config failure tests.
7. **MEDIUM — Linux parent PID parsing split process names on spaces**
   (`run_n4a_timing.py:136`). Parse after the final closing parenthesis in
   `/proc/PID/stat`; a regression includes spaces and an embedded parenthesis.
8. **MEDIUM — evidence descriptions overstated timing and fixture provenance**
   (`README.md:85`, `PROTOCOL.md:37`, `tests/fixtures/README.md:1`). The profiler's
   fixed 30 Hz budget is unrelated to MH01's measured 20 Hz camera rate. VALID
   now explicitly qualifies evidence only, with real-time status UNKNOWN.
   Fixture provenance distinguishes reported measurements from synthetic fields
   and does not claim that maximum temperature and throttle were simultaneous.
   Sampler cadence provenance is labeled PROPOSED in config.json. This is a
   documentation/source audit; the existing tracking-budget dependency test
   confirms the 33.3 ms behavior. No immutable dependency was changed.

## Ticket requirements, one by one

| Requirement | Review outcome |
|---|---|
| Owned `run_n4a_timing.sh` | Present; Bash strict-mode wrapper with a stdlib helper. |
| Shared ORB lock preflight | Observes the reviewed runner's lock; actual launcher reacquires it. Busy-lock refusal tested. |
| SoC start threshold, optional bounded cooldown | Configured limits/provenance; threshold boundary/refusal tested; repeated before later runs. |
| Since-boot throttle refusal or explicit override | Raw VideoCore capture, configured current/historical bits, override recorded; diagnostic runs excluded. |
| Governor and cooling state | Captured; optional performance requirement; absent/unreadable evidence blocks where required. |
| N runs through reviewed EuRoC launcher | One sequence/run; exact child PID discovery, delegated sampler, stop/flush and inter-run cooldown/check. |
| One experiment directory and provenance | Config, host/inputs/commands, raw logs, per-run launcher hashes, capture receipts and output hashes retained. |
| Delegated accuracy plus profile analysis/validity | Both invoked as subprocesses; original tools unchanged. Real default-tool integration tested. |
| Accuracy, P50/P95/P99, max temperature, throttle, VALID/INVALID | Included per run with exclusions; missing evidence is BLOCKED. Percentiles are tracking-call durations with explicit host clock semantics. |
| VALID-only aggregate with exclusions | Included; whole-experiment failure cannot be hidden by successful subset; missing repetitions listed. |
| Operator protocol | Hypothesis, falsifiers, fixed variables, controls, commands, evidence and interpretation present. Missing observations block the test. |
| Stub tests and real saved evidence | Valid capture, throttle exclusion, preflight refusal and review regressions; derived throttle fixture plus historical accuracy and trajectory suites. |
| COMMON result contract, docs, logs | result.json, exit codes, offline analysis/replay, README, REPORT and complete test log present. |

No software deliverable remains missing within T15. A real timing run requires
an instrumented engine that emits events.csv/run_tracking.csv; obtaining or
modifying that external engine was not part of this review's owned paths.

## Test results after fixes

Exact commands, raw output and exit codes are in `tests/last-run.log`, generated
by:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experiments/templates/n4a_timing/tests/run_checks.py
```

| Suite/check | Result |
|---|---:|
| T15 original plus regressions | 21 passed |
| Accuracy (including three real saved runs) | 10 passed |
| Profile | 12 passed |
| ClockMap | 37 passed |
| Runtime observer (including C++ CSV round trip) | 20 passed |
| Trajectory evaluator (including historical evo/TUM comparison) | 30 passed |
| Standalone observer C++ executable | PASS |
| Three shell syntax checks and owned-path whitespace | PASS |

**130 unittest tests passed; zero skips.** The observer C++ binary and trajectory
scratch paths were redirected into temporary owned directories. Shared evidence
was only read. No hardware, SSH, GUI, package installation or network was used.

## Remaining open items

- UNKNOWN: target Pi capture behavior, sampler overhead, power/thermal behavior,
  actual frame latency and sustained real-time execution. Fixture success is not
  N4A or any project-gate PASS. See REPORT.md for physical and clock limitations.
- SOURCE-SUPPORTED dependency limitation: profile/config.json fixes its camera
  budget at 33.3 ms (30 Hz), while the saved N4A report §2 says MH01 is 20 Hz.
  Its over-budget count must not be used as MH01 acceptance. The existing shared
  observer decoder field-shift bug is also reported in REPORT.md; the selected
  profiling tool does its own correct decode. Both directories are immutable
  for this ticket, so no dependency fixes were attempted.
- **Conductor integration item:** `git diff origin/main` includes inherited
  deletions of unrelated lab/tool files outside T15. `git status --short` was
  clean before review; these are branch ancestry differences, not review edits.
  Preserve current main's unrelated files when integrating the owned change.
  This verdict does not approve those deletions or a blind whole-branch merge.
- All changes remain uncommitted and limited to the owned directory. No commit,
  push, index update, shared-checkout mutation or other state-writing git
  operation was performed.
