# Completed milestone: LQR with actuator delay, torque lag and IMU noise

Conductor verified; final Claude review pending. **SIMULATION / ASSUMED only.**

## Merged implementation
- [PR42](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/42): nominal six-state MuJoCo/LQR; approved by Claude in PR44.
- [PR45](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/45): explanatory LQR/RL mathematical guide.
- [PR46](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/46): predeclared paired PPO protocol/backend, no training claim.
- [PR47](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/47): causal actuator/noise runtime, conditional DARE, tests and worklogs; merged0c70a32. Both CI checks SUCCESS at exact head bdac630.

## What actually ran
From the actuator worktree, clean runtime source `0900606085527e73167dc5b1119af284076e479a`:

```sh
.venv/bin/python -m sim.run_augmented --config sim/configs/assumed_actuator_noise.json --out /private/tmp/wbr-actuator-conductor-20261020-05 --jobs 4
```

Conductor execution exit0, experiment COMPLETE. Acceptance is separate:

| Controller | Controlled successes | Expected-fall controls |
| --- | ---: | ---: |
| Frozen original K | 0/40 | 20/20 |
| Conditional delay-aware LQR | 40/40 | 20/20 |

Four exact delays2/3/4/5ms ×five noise seeds ×balance/push; negative controls separate. Original failures were final-window/recovery checks; no controlled falls. Conditional recovery1.756–2.762s. All cases retain raw controls/intervals and metrics, including failures.

Independent conductor command: backend Python `.github/run_unittest.py sim/tests`, exit0,27/27 PASS, zero skips,58.334s. Log `/private/tmp/wbr-augmented-20261020/conductor-actuator-tests.log`. Verified373 artifact checksums, runtime source hashes and identical paired noise hashes. Tests cover causal arrivals including fractional ticks, analytic lag, independent cached noise, saturation, nominal equivalence, integration refinement and actual augmented transition/DARE.

## Reproduce and inspect
- Stable archive: `~/wbr-evidence-archive/sim-actuator-20261020-01`;373 artifact hashes in result.json. Result SHA256 `d8e85e361707f7da19660e737ce689da8ad4d29682fb60e860c4f3427af2f503`.
- Config/model/command/source/package receipts, nominal K and four conditional designs are archived. Plot `comparison-5ms-seed0.png` compares the same push/noise case; it is an illustration of this one case, not an extra run.
- Failed/interrupted attempts01–04 remain under `/private/tmp`; quota-interrupted runs are not counted as completed matrices. Source fixes: NumPy bool serialization and integer lag input coercion; neither changes acceptance.

## Limits and next step
Known, fixed delay/lag and zero initial torque permit causal command-only torque reconstruction. Body angle/gyro are noisy; four other sensor coordinates remain ideal. Mechanics use exact mean actuator torque on at most0.25ms RK4 intervals; coupling is approximate and refinement-tested. No full five-bar/contact/slip, parameter identification or sim-to-real validation.

Original mechanics,2ms rate,Q/R,2/4Nm caps, initial state,10s duration,6N×0.15s pulse and acceptance unchanged. Conditional synthesis followed observed frozen failure and added zero-cost delay/torque states, without weight search. Freeze its per-delay gains for every PPO condition under D26. No actual WBR PPO result is claimed here. Protected gain_schedule remains unfinished owner work; no Pi/STM32/motor command or gate promotion.

## Claude final review
Please review implementation/claims and the frozen comparison baseline. Record your conclusion below. The conductor continues PPO implementation in parallel; no intermediate architecture change is requested.
