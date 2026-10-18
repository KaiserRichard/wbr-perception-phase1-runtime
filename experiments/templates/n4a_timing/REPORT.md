# T15 report — reviewed N4A controlled timing package

## Built and corrected

The package provides a preflight/capture runner, delegated accuracy and profile
analysis, VALID-only aggregates and an operator protocol. The independent review
corrected default analyzer paths, result/exit-code precedence, stale derived
outputs, missing/partial telemetry handling, event-session latency parsing,
capture completion checks and inter-run preflight checks. Version is 1.1.0.

Preflight and combined analysis now write the COMMON.md `result.json` contract
and print tables. Both support hardware-free saved-evidence re-evaluation.
Capture distinguishes engine failure from missing sampler evidence, handles
process names containing spaces/parentheses, closes logs and cleans up processes
on exceptions. Numeric settings remain in `config.json`, with the existing
accuracy/profile limits delegated to their original configurations.

`REVIEW.md` records ranked findings, fixes, the requirements audit and remaining
integration items. No dependency implementation was changed.

## Verification

### T15b flaky capture fixture

The intermittent `test_valid_stub_capture` BLOCKED result came from the test
stub, which ran `/bin/sleep` for a fixed 0.20 seconds. The runner first has to
discover the child PID, launch Python, and let the sampler initialize and write
its first sample. Under host scheduling delay, the stub engine could exit
before that sequence completed; the sampler then had no live target and capture
was correctly BLOCKED. This is a fixture timing assumption, not a Pi capture
logic defect: the actual EuRoC engine is expected to remain active while the
sampler attaches, and the capture contract requires sampled evidence.

The test stub now holds the target process until the sampler signals that its
first sample row is written, then ends the stub process and allows normal
sampler shutdown. This keeps the test deterministic while still checking that
the PID was discovered, the sampler ran, and sample metadata was saved.

T15b verification: the full T15 test suite passes 20/20 in separate normal-load
processes (21 tests each, 0 skipped), and passes once while CPU-bound `yes`
processes occupy all 16 reported CPU cores. Exact commands and output are
recorded in `tests/last-run.log`. These are Mac fixture results; Pi capture
behavior remains UNKNOWN pending hardware execution.

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experiments/templates/n4a_timing/tests/run_checks.py
```

Exact subprocess commands, complete output and exit codes are saved in
`tests/last-run.log`. Final coverage: 21 ticket tests, 10 accuracy tests,
12 profile tests, 37 ClockMap tests, 20 observer tests and 30 trajectory tests:
**130 unittest tests passed, none skipped**. The observer C++ executable also
passes, as do all three relevant `bash -n` checks and the owned-path whitespace
check. Dependency scratch and the C++ executable are redirected into temporary
owned directories; no dependency source/build directory is modified.

The accuracy suite reads the shared historical MH01 evidence and reproduces
SE3 ATE RMSE 0.041461 / 0.036844 / 0.041604 m (CALCULATED). The trajectory suite
also checks historical evo/TUM agreement using those read-only inputs. The
compact throttle fixture is derived from reported measured values, with
synthetic scaffolding explicitly described in `tests/fixtures/README.md`.
These results verify software and saved-file evaluation only, not a Pi gate.

## Not verified and open risks

- UNKNOWN: hardware behavior, actual Pi process/sysfs paths, sampling overhead,
  cooling effectiveness, power quality and sustained EuRoC performance. No SSH,
  camera, serial device, GUI, installation or network action was used.
- UNKNOWN: full-window real-time pace/backlog. VALID means usable saved accuracy
  and timing evidence; it does not mean real time. The dependency's 33.3 ms
  budget assumes 30 Hz, whereas saved MH01 evidence reports 20 Hz. This package
  does not use that over-budget count as MH01 acceptance. The operator must
  establish full-window pacing with an appropriate clock relationship.
- A latency trace must already be produced by the selected instrumented engine.
  An uninstrumented ORB executable cannot produce VALID timing via the resource
  sampler alone. Patch timing is a tracking duration, not camera-to-pose age.
- Shared execution locking protects cooperating accuracy launchers. A preflight
  observation does not hold the lock until launch, but the reviewed launcher
  independently acquires it for execution. Uncoordinated ORB jobs remain an
  operator responsibility. Locks between repetitions are not held continuously.
- The sampler attaches after discovering the engine PID and may miss startup.
  Boundary throttle snapshots guard sticky faults at the tail; they cannot
  prove physical conditions between polls. The profile temperature ceiling
  and package cooldown/start settings remain PROPOSED.
- Dataset identity/checksums, headless engine build, ORB revision/patches and
  supply/cooling arrangement must be confirmed and saved by the operator as
  directed in PROTOCOL.md; labels/paths alone do not establish their identity.
- Existing dependency defect, reported only: the shared observer sampler's
  `throttling()` field zip is shifted by inclusion of `throttled_raw` in its
  slice. The profile dependency decodes its own eight fields, so the template
  does not use that faulty decoder. See profile/REPORT.md.
- The diff against the advancing origin/main contains inherited deletions
  outside this ticket (lab checks and other tools). They were present before
  review edits and were not changed. Conductor integration must preserve those
  unrelated main-branch files; this review approves only the T15 owned path.

All review changes remain uncommitted, inside
`experiments/templates/n4a_timing/`. No git state-changing command was run.

Proposed commit message: `Stabilize N4A timing capture fixture under scheduler load`
