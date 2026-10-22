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

## Claude review (2026-10-22)

**Decision: accepted.** The model boundaries are stated correctly throughout. Read:
this file, the session notes, `sim/gain_schedule/stress.py` (axes and wheel-map
perturbation) and `sim/fivebar/ramp.py` (length profile, initial state). Archives
not re-read.

### What the evidence shows

- **a. Margins are large, one factor at a time.** At the 0.16 m / 2 ms design:
  push 42 N × 0.15 s = 6.3 N·s passes, about 7× the 0.9 N·s panel push. Delay
  9 ms passes, 4.5× the design delay, and 10 ms fails strict criteria but stays
  upright. Body mass and inertia 4× pass.
- **Wheel-map perturbation closes my earlier concern.** The grid
  δ ∈ {−0.5, 0, 0.167, 0.5, 1, 2} all passed. The generalized wheel-reaction
  term barely affects this LQR, so the five-bar's 0.167 difference is not a
  stability risk *in this model*.
- **b.** Delayed five-bar linearizations are locally stable at all 16
  length/delay points, with a slowest mode of about 0.8 s, matching the reduced
  model. Correctly labelled as not a gain or phase margin.

### Limits that matter for the next step

1. **The stress test is one-factor-at-a-time, at one length and one design
   delay.** Combined effects can fail far earlier than any single axis suggests.
   Next: a small corner set at 0.12 and 0.20 m, for example delay 6 ms + mass 1.5×
   + δ 0.167 + push 30 N, 5 seeds each.
2. **The ramp's peak tilt is the initial condition, not the ramp.** The protocol
   starts at 8.0° leg tilt (`initial_state[1] = 0.1396 rad`), and peak tilt is
   8.007°. The ramp begins at 2 s, while the controller is still recovering
   (worst recovery about 2.9 s), so the two effects are mixed and the ramp's own
   disturbance is not measured. Next: report peak tilt and displacement within
   the 2–10 s window only, or start from upright.
3. **One slow ramp.** The peak extension rate is about 19 mm/s (0.08 m over 8 s,
   quintic). Add faster ramps (2 s and 1 s) and the reverse 0.20 → 0.12 m to find
   where scheduling starts to matter.
4. Extension force 28.6 N on an ideal prescribed coordinate: motor feasibility
   stays UNKNOWN until it is converted to hip torque against the real motor
   limits. Correctly stated.
5. Only 4 of the 8 ramp checks were run independently by the conductor; the
   other 4 are worker-owned. That is a minor independence gap; fine for a sim
   milestone.
