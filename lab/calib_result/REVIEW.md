# T18 independent review

## Verdict

**APPROVE-WITH-FIXES** — the acceptance criteria are implemented and the confirmed policy replay and exit-contract defects below are fixed.

## Ranked findings

1. **High — reanalysis could silently change the acceptance policy.** In the original `--analyze-only` path, a missing saved `input-thresholds.yaml` fell back to the current default thresholds. This could produce a PASS under a policy different from the one used for the original result. The fallback is removed; missing policy now produces `BLOCKED` with `result.json`. Regression: `test_analyze_only_missing_saved_policy_is_blocked` in [test_check_kalibr_result.py](tests/test_check_kalibr_result.py:148); implementation at [check_kalibr_result.py](check_kalibr_result.py:119).

2. **Medium — invalid threshold policy could exit before writing the required result.** An unreadable or malformed policy raised before result generation. It now prevents evaluation and yields `BLOCKED` with a threshold-policy criterion, while preserving the input snapshot when available. Regression: `test_unreadable_threshold_policy_writes_blocked_result` in [test_check_kalibr_result.py](tests/test_check_kalibr_result.py:161); implementation at [check_kalibr_result.py](check_kalibr_result.py:122).

3. **Low — CLI usage errors returned exit code 2.** `argparse`'s default code conflicted with the ticket's code 3 for usage/internal errors. `ContractArgumentParser` now returns 3. Regression: `test_usage_error_uses_contract_exit_code` in [test_check_kalibr_result.py](tests/test_check_kalibr_result.py:174); implementation at [check_kalibr_result.py](check_kalibr_result.py:285).

## Requirements reviewed

- Reuses `calibration/lab/mac/summarize_kalibr.py` for YAML loading, transform validation/direction, reprojection parsing, vector validation, and the factory camera–IMU reference. Both camera–IMU and stereo result summaries and chains are parsed.
- Evaluates per-camera pixel reprojection mean/std, gyro and accelerometer residual mean/std in report SI units, absolute camera-to-IMU time shift with the documented sign, camera-to-IMU translation/rotation, factory-relative stereo baseline, factory-relative intrinsics/distortion, distortion model and coefficient sanity, and exact run-vs-provisional IMU provenance.
- Numeric acceptance thresholds are centralized in `thresholds.yaml`, with a source/rationale for every entry and PROPOSED labels on locally selected limits. The 30 ms time-shift bound is the cited search limit; equality is rejected as suspect, consistent with the calibration section.
- Emits contract-shaped `result.json`, criterion evidence/status/source fields, hashes of saved input snapshots, a factory `diff.txt`, and a human-readable table. Missing required data blocks evaluation. Analyze-only reuses saved inputs and now requires its saved policy.
- README documents Pi capture commands, Mac fitting/check commands, each criterion's meaning, exit codes, and limits. Fixtures clearly distinguish software validation from physical gate evidence. The real TUM-VI fixture tests parsing only.
- No additional requirements were found missing.

## Test results after fixes

Exact commands and full output are saved in [tests/last-run.log](tests/last-run.log).

- `python3 -m unittest discover -s lab/calib_result/tests -v` — **8 tests passed**. Covers fixture PASS, criterion perturbations/FAIL, missing input/BLOCKED, saved-input reanalysis, missing/invalid policy/BLOCKED, usage code 3, and real saved TUM-VI parser evidence.
- `python3 -m unittest discover -s calibration/lab/tests -v` — **20 tests passed** for the imported summary/recorder utilities.

## Remaining open items

- No camera, Pi, production D435i Kalibr result, or hardware calibration was tested. Fixture PASS is software-only.
- Proposed residual, time-shift, intrinsics, and distortion acceptance limits still need review against real D435i runs; assumed transform and baseline bounds need physical validation. The provisional IMU noise file is only checked for provenance, not physical accuracy.
- Reports/PDF residual structure, target metrology, repeated-take time-shift stability, clock mapping, and ORB-SLAM3 behavior remain outside what this checker can establish.
