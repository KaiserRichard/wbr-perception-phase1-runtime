# PR110 control margins a/b/c — 22 October 2026

**Status:** code milestone complete. PRs #114, #115 and #116 are merged to `main` with two successful exact-head CI checks each. PR #116: head `a9b8f24568e2f02e9fbbc13b59f9c0ecec475010`, merge `7e90dd01871132feb2192b47ce8dbd5fa3bbd40`, merged 2026-10-22 03:02:15 UTC. Assumed-model evidence only; no hardware or general robustness claim. Exact commands and receipts: [session](../sessions/2026-10-22-control-margins.md), archive `/Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/`.

## a. Reduced-model fixed-design stress

Source `2390fcaf2de4cad3071557a52627d1ddd03e7245`; #115 merged green. Of 56 cases, 40 PASS / 16 FAIL / 0 ERROR. Sampled confirmations: push 42 N passed 5/5 vs 45 N 0/5; delay 9 ms passed 5/5 vs 10 ms 0/5 (10 ms stayed upright); body mass and inertia scaled together at 4× passed 5/5 vs 8× 0/5. These are discrete samples, not continuous limits or hardware uncertainty. The finite wheel-map grid had no failure; delta 1 and 2 each passed 5/5.

## b. Delayed five-bar local linear comparison

Source `8ccd6268667c6942446a635882f0e7b3938492de`; #114 merged green. Sixteen fixed-length conditions (0.12/0.16/0.20/0.21 m × 2/3/4/5 ms) were locally stable; spectral radius was `0.997442684–0.997688181`, so radial distance `1−rho` was about `0.002312–0.002557`. This scalar is not gain or phase margin. The saved conductor/worker matrix and eigenpair comparison matched except one synthesized rho by `1.11e-16`; this is a comparison receipt, not an independent derivation. Exact matched delay/lag and noiseless physical states are assumed. No nonlinear, saturation/noise, estimator uncertainty or hardware claim follows.

## c. Prescribed-extension ramp

Source `7aeb34bf4cb366621442b6c3a996d8f9c2670e43`; #116 merged green. Seed 0 completed one 15 s / 15,000-step run with 8/8 saved checks PASS: peak displacement 0.029149 m, tilt 8.00734°, closure `2.30e-16 m`, ideal extension reaction 28.639 N, work 1.762 J; no saturation. Motor feasibility is UNKNOWN. Length was an ideal prescribed coordinate, so reaction/work do not establish a physical actuator. The targeted ramp controller test includes a lagged observer/command reconstruction using `lag_interval`; it is a check of that controller path, not the b matrix comparison. The projected mass matrix was positive in the chosen mixed coordinates; its raw minimum eigenvalue has no standalone kg unit. Refinement state infinity differences mix units and are not hardware accuracy.

Run-01 was interrupted before source-before-measurement; run-02 completed its trace but failed JSON serialization on NumPy `bool_`; both failures remain archived. Only the original four ramp checks were independently run by the conductor. Appended eight-check output and refinement results are worker-owned, not independent conductor checks. Three repeats from unchanged source `d4b4249b4dd472621f5f9c76c53ebd930fd3e88a` match original metrics, controls and intervals byte-for-byte. Prior 400-case evidence and frozen PPO v2 remain untouched.

**Claude handoff:** Review this completed PR110 a/b/c evidence and its model boundaries; do not infer hardware feasibility or general robustness.
