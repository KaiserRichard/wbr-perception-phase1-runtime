# Repository CI

`workflows/tests.yml` runs the repository's host tests on pushes and pull requests
using Ubuntu 24.04 and Python 3.12. Checkout disables submodules. The workflow
installs NumPy 1.26.4 and PyYAML 6.0.2; GCC/G++ and make come from the image.
SOURCE-SUPPORTED: the NumPy pin is validated in
[`calibration/allan/verification.md`](../calibration/allan/verification.md),
which records a real test receipt. The root README does not specify a NumPy version.

From the repository root on the Mac or Pi, with Python 3.11+ (Pi: 3.12), NumPy,
PyYAML, make and host C/C++ compilers already available:

```bash
bash -n tools/run_all_tests.sh
bash tools/run_all_tests.sh > tools/run_all_tests.last-run.log 2>&1
```

The second command preserves the runner's exit status. Read its log even when it
exits nonzero. No physical devices are required or opened by this CI entrypoint;
the link bench uses a software simulator and pseudo-terminal.

Run just the CI regression tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .github/tests -v
```

The shell entrypoint runs each of the five reviewed Makefile `test` targets and
each discovered Python directory in a separate process. The targets are
`tools/link_proto`, `tools/link_bench`, `tools/runtime_observer`,
`tools/vio_adapter` and `tools/ros2_bridge`. VIO explicitly selects its fake
engine; the ROS bridge builds only its ROS-free core probe. None requires
`third_party/`, ROS, ORB-SLAM3, a firmware toolchain or physical hardware.
Firmware build targets, real ORB bindings and ROS package builds are outside
this host test inventory. There are no whole-suite SKIPPED rows for these targets.

Python discovery includes `tools/*/tests`, `tools/trajectory_eval`,
`calibration/*/tests`, `lab/*/tests`, `tools/eval_pipeline/tests` and
`tools/eval_pipeline/*/tests`. This automatically includes
`tools/perception_health/tests` and `tools/n4b_offline/tests` when they land.
Future directories may be absent. The existing baseline directories listed in
the shell script must be present; deliberate suite removal must update that list.
Duplicate glob matches run once. Bytecode writes are disabled, and neither the
entrypoint nor its regression tests rewrite other suites' committed receipts.

Each Python suite must discover tests from every `test*.py` file and execute at
least one test. `run_unittest.py` uses the standard unittest loader and runner;
it also checks the recursive file inventory so unpackaged nested tests cannot
silently disappear. Nested test directories need `__init__.py`. Test helper
modules that define no tests should use names outside `test*.py`.

| Result | Meaning |
| --- | --- |
| PASS | Make target succeeds, or Python discovery is complete and executed tests succeed. Individual skipped tests still print their reasons. |
| FAIL | Make, test assertions, imports or another process error failed. |
| BLOCKED | A required directory/Makefile is missing, discovery is empty/incomplete, or every test was skipped. |

The aggregate command exits 0 only if all rows PASS, and 1 for FAIL or BLOCKED.
The internal Python helper uses 0/1/2 for PASS/FAIL/BLOCKED. This is CI orchestration;
T8 explicitly excludes the lab `result.json` contract. No measured acceptance
thresholds are introduced: nonempty discovery is a logical requirement.

The frozen fixture `tests/fixtures/pr8-summary.txt` is the verbatim summary from
the engineer's saved Mac receipt, before review edits. Its inventory drives
temporary repository fixtures; those tests exercise PASS, FAIL and BLOCKED,
missing/empty/nested suites, optional skips, quoting and all future suite paths.

MEASURED fixture success proves host software behavior only. It is not a Pi gate
PASS, sensor qualification, timestamp validation, real ROS/ORB build or hardware
test. The MH01 real-data check may skip when its untracked ground truth is absent;
the QEMU firmware check may skip when its two tools are absent. A standalone
ROS bridge Python run skips parity, which the Makefile run executes. See
[`REVIEW_CI.md`](REVIEW_CI.md) for the measured results and existing Mac failure.
