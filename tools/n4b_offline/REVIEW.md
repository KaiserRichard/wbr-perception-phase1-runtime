# T9 independent review

## Verdict

**APPROVE-WITH-FIXES** — the requested offline toolchain is present. Three confirmed defects were fixed in this review, with regression coverage for each behavior.

## Ranked findings

1. **High — Pi runner omitted ORB runtime library search paths.** `run_n4b.sh` ran `ldd` before adding `$ORB_ROOT/lib` and the ORB third-party library directories to `LD_LIBRARY_PATH`. A standard ORB build could therefore be rejected as unresolved or fail at launch. Added the paths before `ldd` and execution, and added a synthetic runner regression test.
2. **Medium — qualifier usage errors returned the wrong contract code.** `qualify_euroc.py` delegated argument errors to argparse, which exits 2; the required check contract assigns usage/internal errors exit 3. Added a contract parser and an invalid-invocation regression test.
3. **Medium — runner provenance omitted the dynamically loaded ORB library.** The runner recorded the executable and inputs but not `libORB_SLAM3.so`, although that library can contain the changed runtime code independently. Added its SHA-256 to the receipt when present and tested the receipt entry.

## Requirement review

- **DB3 export:** emits stereo EuRoC PNG/CSV files, combined IMU CSV, nanosecond time files, and metadata that names the ROS header clock policy and separates bag receive time. CDR/image/layout and stream-order validation are implemented. `driver_method` stays UNKNOWN when separate topics do not identify the unite policy.
- **Qualification:** checks the requested camera counts, exact stereo timestamps, image and IMU order, IMU coverage, rates, gaps and time-file policy. Thresholds and rationales are in `qualify_config.json`; saved-file analysis and PASS/FAIL/BLOCKED outputs are implemented.
- **ORB settings:** reuses `calib_convert.py`, builds from the factory camera and provisional IMU inputs, and records field-level provenance and hashes. Generator invocation completed successfully against the repository calibration inputs.
- **Pi runner:** verifies the configured executable hash unless explicitly overridden, sets ORB library paths, records runtime inputs including the linked ORB library, saves `ldd` and command receipts, and uses the optional profiler when available. It does not access a camera.
- **Required test paths:** PASS, FAIL and BLOCKED fixtures are covered. A saved real-evidence summary is labeled MEASURED and is not used to claim a tool PASS.
- **Documentation and scope:** README, REPORT and this review are present. The report includes open risks and the proposed commit message. Changes remain in `tools/n4b_offline/`.

## Test results after fixes

- `python3 -m unittest discover -s tools/n4b_offline/tests -v` — 6 tests passed.
- `python3 -m unittest discover -s tools/calib_tools/tests -v` — 16 tests passed.
- `bash -n tools/n4b_offline/run_n4b.sh` — passed with exit 0.
- `git diff --check origin/main` — passed.
- Exact unittest output and shell syntax result are saved in `tests/last-run.log`.

The runner regression uses a fake ORB tree and fake `ldd` to verify the environment and receipt without launching ORB. No Pi execution, real DB3 replay, or hardware behavior was verified. These remain open N4B evidence items; passing fixtures do not pass the gate.
