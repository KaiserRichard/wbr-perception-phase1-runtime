# Independent review of T8 CI

Verdict: **APPROVE-WITH-FIXES**. Confirmed CI wiring defects were fixed with
regressions. The existing Mac `link_bench` test failure remains outside CI scope.
No hardware or perception gate is credited.

## Ranked findings and fixes

1. **High — successful incomplete discovery.** The original
   `tools/run_all_tests.sh:25` trusted unittest's exit code, including `Ran 0 tests`.
   It also missed unpackaged nested test files when other tests passed.
   Fixed at `tools/run_all_tests.sh:25` and `.github/run_unittest.py:23`: compare
   the recursive `test*.py` inventory to discovered test modules, reject empty or
   incomplete discovery, and reject a suite where every test is skipped.
   These produce BLOCKED and a nonzero aggregate exit, with missing paths/skip
   reasons visible. Regressions cover empty baseline/new directories, partially
   hidden tests, nested packages, all-skipped and mixed-skipped suites.

2. **High — missing suites silently omitted.** Original glob discovery ignored
   a missing baseline Python directory, and the original missing-Makefile branch
   at line 53 printed SKIPPED without affecting success. Fixed at
   `tools/run_all_tests.sh:40` and `tools/run_all_tests.sh:76`: require the existing
   baseline inventory and label missing evidence BLOCKED. Future suites retain
   generic, optional discovery. The loop at `tools/run_all_tests.sh:103` also
   tolerates an empty array under macOS Bash with `set -u`. Regressions remove a
   baseline directory, a Makefile and the entire Python inventory, checking both
   exit status and the continued summary.

3. **Medium — unjustified dependency skips.** Original lines 35–77 scanned the
   entire Makefile for ROS/ORB/hardware words, including comments and unrelated
   targets. A comment could suppress a host suite and still yield success.
   Removed that heuristic; the five individually reviewed host `test` targets
   now always run (`tools/run_all_tests.sh:45`). Regression adds every marker to
   each target's Makefile comment and verifies all targets execute.

4. **Medium — inherited environment could enable real ORB.** The original
   VIO invocation inherited `WBR_WITH_ORBSLAM3=1`, which changes its test build to
   require upstream ORB headers/libraries. `tools/run_all_tests.sh:49` explicitly
   selects `WBR_WITH_ORBSLAM3=0`; a regression runs with the enabling environment
   variable and verifies the fake target is selected.

Additional regressions check Python/import/make failures, continued execution,
path quoting with spaces, disabled bytecode, distinct process isolation, and
exactly-once discovery across overlapping globs. The suite inventory fixture is
derived from the engineer's real saved Mac receipt; see `tests/fixtures/README.md`.

## Requirement audit

| Requirement | Result |
| --- | --- |
| Run every existing specified Python suite | Covered: 13 baseline Python directories, plus the new CI regression suite. Every original saved summary row is retained. |
| Generic future discovery | Regression verifies `lab/*/tests`, `tools/eval_pipeline/tests`, `tools/eval_pipeline/*/tests`, `tools/perception_health/tests`, `tools/n4b_offline/tests`, including overlapping globs and spaces. |
| Five Makefile test targets, justified external-dependency exclusions | Inspected every target and prerequisite. All five targets are host-only and run; no entire suite is skipped. Firmware build targets, ROS package builds and real ORB bindings are outside the selected inventory. |
| Separate processes, disabled bytecode, summary and failure exit | Python runs via the standard unittest loader/runner in one child per directory; make uses one child per target. FAIL/BLOCKED makes the aggregate exit 1 while continuing other suites. |
| Existing committed receipts preserved | Audited test code for receipt writes; no suite depends on or rewrites committed `last-run.log`. Only explicitly requested aggregate/review receipts are refreshed. |
| Actions events/image/Python/dependencies | Static configuration check passes: push + pull_request, ubuntu-24.04, Python 3.12, NumPy 1.26.4, PyYAML 6.0.2 and host compilers from the image. |
| NumPy source | SOURCE-SUPPORTED: `calibration/allan/verification.md:21` records successful NumPy 1.26.4 verification. The root README has no validated version, so the existing real receipt is the available repository source. No unsupported root-README validation claim is made. |
| Checkout without submodules | Explicit `submodules: false`. `.gitmodules` and all selected Makefile/test imports were reviewed; none needs a third-party checkout. |
| Local run, report, README and review receipt | Complete; exact commands and full final output in `tests/last-run.log`; aggregate output also in `../tools/run_all_tests.last-run.log`. |

## Test results after fixes

MEASURED: macOS 15.7.9 x86_64, Python 3.11.0rc2, NumPy 1.26.4, PyYAML 6.0.3.

- `bash -n tools/run_all_tests.sh`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .github/tests -v`:
  all 15 regression tests PASS (`tests/regressions.log`).
- Workflow YAML configuration assertions: PASS (exact command in `tests/last-run.log`).
- `bash tools/run_all_tests.sh`: all 19 suite rows attempted; 17 PASS, 2 FAIL,
  aggregate exit 1. Both FAIL rows are the same existing `link_bench` host
  simulator test, once via make and once via direct Python discovery. The CI
  regression suite passes again inside the aggregate run.

The original engineer's script was also rerun before final verification from its
HEAD snapshot with only `ROOT_DIR` relocated for `bash -c`; complete output is in
`tests/before-fixes.log`. It reproduces the same two failures (18 original rows).
The final command receipt records every invocation and exit code without filtering
raw test output.

## Remaining open items and evidence limits

- **Existing Mac failure, not fixed:** `tools/link_bench/tests/test_link_bench.py:109`
  requests a simulator PTY; the CLI reports `baud 460800 not supported by termios`,
  and cleanup at line 119 times out waiting for the simulator. This predates the
  review. The runner correctly retains FAIL. No existing suite was modified.
- **Justified individual skips:** optional firmware test requires both
  `qemu-system-arm` and `arm-none-eabi-gcc`; the standalone ROS bridge Python run
  skips its optional C++ parity check (the Makefile invocation executes it);
  MH01 real-data validation lacks `eval/gt_data.csv` and `eval/gt_data.tum` in this
  worktree. All reasons appear in raw logs. Missing MH01 evidence is not a
  measured accuracy PASS.
- SOURCE-SUPPORTED by the review ticket: PR 8's prior Ubuntu 24.04 Actions run
  passed. The revised code has not been run on GitHub or Python 3.12 locally;
  no remote access or package installation was attempted.
- UNKNOWN: physical Pi behavior, ROS/ORB integration and sensor/MCU performance.
  Host fixture tests cannot establish these. Future changes to Makefile test
  prerequisites still require review. Deliberate baseline removals must update
  the explicit inventory; new generic suites need no inventory entry.

Proposed commit message: `Fix CI suite discovery and prevent silent test skips`.
Changes remain uncommitted for the conductor.
