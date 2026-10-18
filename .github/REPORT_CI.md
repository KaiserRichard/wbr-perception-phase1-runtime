# CI runner report

## What changed

- Added `.github/workflows/tests.yml`, which runs on pushes and pull requests with Ubuntu 24.04 and Python 3.12. Checkout explicitly leaves submodules disabled. It installs `numpy==1.26.4` and `PyYAML==6.0.2` and invokes `tools/run_all_tests.sh`; the runner image supplies GCC/G++.
- Added `tools/run_all_tests.sh`. It discovers Python unittest directories under `tools/*/tests`, `tools/trajectory_eval`, `calibration/*/tests`, `lab/*/tests`, `tools/eval_pipeline` and `tools/perception_health` when present. It runs the five specified Makefile `test` targets as separate make processes, prints PASS/FAIL/SKIPPED rows, and exits nonzero on failures.
- The selected Makefile targets are host-only: `link_proto`, `link_bench`, and `runtime_observer` compile host code; `vio_adapter` defaults to the fake engine and does not enable ORB-SLAM3; `ros2_bridge` builds a ROS-free core probe. None needs a submodule, ROS installation, firmware toolchain, or hardware. No target is skipped in the current repository state.
- The `.gitmodules` file declares three large third-party submodules. None of the discovered test suites or the five default Makefile test targets imports or builds them, so the workflow checks out with submodules disabled.

## Dependency pin

`numpy==1.26.4` is the version recorded in `calibration/allan/verification.md` for a successful Python test receipt. The existing Python suites use NumPy; the checkout does not validate a separate version in the root README.

## Verification

The local run is recorded in `tools/run_all_tests.last-run.log`. That file is the complete human-readable output of `bash tools/run_all_tests.sh` on the Mac worktree. `bash -n tools/run_all_tests.sh` also passed. The runner exited 1 because the `tools/link_bench` Makefile and Python suite both failed on the same platform-specific host simulator test: the test invokes the link script with `/dev/ttys...`, but macOS Python does not expose `termios.B460800` (`baud 460800 not supported by termios`), and simulator cleanup then times out. This failure is recorded without changing the existing suite. All other reported Makefile targets and Python suites passed; one real-data trajectory test and the optional QEMU firmware test reported their own expected skips.

This run validates the checked-out host test fixtures only. It does not run ROS, ORB-SLAM3, arm-none-eabi firmware, hardware tests, or any Pi gate. See the output log for each suite's status. Existing suite failures, if any, are reported there and are outside CI-wiring scope.

## Not verified and risks

- The GitHub Actions job has not run on GitHub from this worktree.
- The local Mac run is not an Ubuntu 24.04 / Python 3.12 run. CI provides that separate environment check.
- Future test suites added under the configured generic locations will be discovered automatically; a future Makefile target may need an explicit dependency review if it adds ROS, ORB-SLAM3, arm-none-eabi, or hardware requirements.

## Independent review changes

Review fixes reject missing baseline suites/Makefiles, empty or incomplete Python
discovery, and entirely skipped Python suites. Reviewed host Make targets are
always attempted, with no keyword-based skip heuristic. VIO explicitly disables
its optional real ORB binding even when inherited environment variables enable it.
The runner also tolerates an entirely missing Python inventory on macOS Bash.
Regression tests under `.github/tests` are included in the aggregate command;
their inventory fixture comes from the original saved test summary. See
`REVIEW_CI.md` and `tests/last-run.log` for final results and exact commands.

MEASURED review host: macOS 15.7.9 x86_64, Python 3.11.0rc2, NumPy 1.26.4,
PyYAML 6.0.3. The workflow's PyYAML 6.0.2 environment was not recreated locally.
SOURCE-SUPPORTED (ticket statement): PR 8's Ubuntu 24.04 Actions run passed before
these review fixes. The revised workflow was not dispatched or verified remotely.
No Pi, camera, serial hardware, ROS or real ORB-SLAM3 run was performed. No gate
is promoted. The existing Mac `link_bench` failure is retained and reported.

The purpose, Pi/local commands, criteria and limits are in `.github/README.md`.

## Proposed commit message

`Fix CI suite discovery and prevent silent test skips`
