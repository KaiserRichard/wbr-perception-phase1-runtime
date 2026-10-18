# CI runner report

## What changed

- Added `.github/workflows/tests.yml`, which runs on pushes and pull requests with Ubuntu 24.04 and Python 3.12. Checkout explicitly leaves submodules disabled. It installs `numpy==1.26.4` and invokes `tools/run_all_tests.sh`; the runner image supplies GCC/G++.
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

## Proposed commit message

`Add GitHub Actions test workflow and suite runner`
