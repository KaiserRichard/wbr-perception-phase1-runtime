# PR110 control margins a/b/c — 22 October 2026

**Status:** a/b are merged: #115 source `2390fcaf2de4cad3071557a52627d1ddd03e7245`, merge `8f8cd947`; #114 source `41decfc9499264a2a291acc733ecc1a35b5c3fea`, merge `a35fc912`. Both PRs had two successful exact-head CI checks. Ramp PR #116 head `a9b8f24568e2f02e9fbbc13b59f9c0ecec475010` remains OPEN; both CI jobs were IN_PROGRESS at close. No merge is claimed. All models/configurations are assumed. Archive: `/Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/`.

## a. Reduced-model fixed-design stress

Source `2390fcaf2de4cad3071557a52627d1ddd03e7245`; config `sim/configs/assumed_actuator_noise.json`. Recorded command: `nice -n 10 /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python -m sim.gain_schedule.stress --out /Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/stress/study-01`. Supervisor exit 0, 538.5955 s; 56 cases: 40 PASS / 16 FAIL / 0 ERROR. One nominal L=0.16 m, 2 ms augmented DARE gain and its 2 ms/5 ms command-only observer were fixed across cases.

Seed confirmations: push 42 N passed 5/5 vs 45 N 0/5; delay 9 ms 5/5 vs 10 ms 0/5 (10 ms stayed upright); body mass and inertia scaled together at 4× passed 5/5 vs 8× 0/5. The finite wheel-map grid had no failure; delta 1 and 2 each passed 5/5. These are sampled values, not continuous bounds or hardware uncertainty. Delta .167 is a generalized-reaction value, not a 17% full-B discrepancy. Receipts/results: `stress/study-01/{summary.json,report.md,run.json}`, `stress/receipts-01/supervisor.json`.

## b. Delayed five-bar local linear comparison

Source `8ccd6268667c6942446a635882f0e7b3938492de`; config snapshot `fivebar-delay/run-01/comparison.json`. Command: `nice -n 10 /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python -m sim.fivebar.delayed_linear --out /Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/fivebar-delay/run-01`; exit 0, 7.2587 s. Sixteen upright fixed-length conditions (0.12/0.16/0.20/0.21 m × 2/3/4/5 ms) were locally stable; five-bar rho `0.997442684–0.997688181`.

Worker/conductor saved matrices and eigenpairs match exactly except one synthesized rho by `1.11e-16` (`fivebar-ramp/receipts-01/b-comparison-differences.json`). This is a command-reconstruction check using existing `lag_interval`, not an independent mathematical derivation. Exact matched delay/lag and noiseless physical states are assumed. No nonlinear, saturation/noise robustness, estimator uncertainty, hardware or ramp claim follows. `1-rho` is radial distance, not gain/phase margin. PR #114 is merged green.

## c. Prescribed-extension ramp

Source `7aeb34bf4cb366621442b6c3a996d8f9c2670e43`; schedule `/Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study/fit-01/schedule.json`. Exact command/environment in `fivebar-ramp/run-03/execution.json`; supervisor exit 0, 235.449 s. Seed 0 completed 15 s/15,000 steps with 8/8 checks PASS: peak displacement 0.029149 m, tilt 8.00734°, closure `2.30e-16 m`, ideal extension reaction 28.639 N, signed/absolute work 1.762 J; physical wheel/hip torque peaks 0.577/0.847 N m; clipped commands 1.750/2.337 N m; no saturation. Motor feasibility UNKNOWN. Length is an ideal prescribed coordinate, so reaction/work are not evidence for a physical actuator. Stored recovery `-1.78e-15 s` is floating subtraction at ramp end, not negative recovery time.

Run-01 was interrupted before source-before-measurement; run-02 retained its completed trace but failed serialization on NumPy `bool_`; final corrected run is run-03. These failures remain archived. The targeted log's first four checks are conductor-run; appended checks/refinements are worker-run. Refinement state infinity difference mixes units and is not hardware accuracy. The projected mass matrix is positive in the chosen mixed coordinates; its raw minimum eigenvalue has no kg unit.

## Repeats and next step

Three repeats from unchanged `d4b4249b4dd472621f5f9c76c53ebd930fd3e88a` match original metrics/control/intervals byte-for-byte (`reproducibility/case_*/repeat-comparison.json`). Ramp worker's final focused command is in `/private/tmp/wbr-control-margins-20261022/free/b-ready.md`; appended worker output records 8/8 PASS (0.390 s). No experiments, training, code, camera work, or learning-state changes in this documentation closeout. Previous 400-case and frozen PPO v2 evidence remain untouched.

**Recommendation:** after the conductor verifies #116 green exact-head CI and merge, add only its factual receipt, then ask Claude to review this milestone. Keep the recorded model limits and failed attempts in the review.
