# Overnight handoff — 21 October 2026

Snapshot 07:48 +07. Implementations merged after conductor checks and green CI; **four tasks remain partial/blocked**. No hardware deployment or final PPO conclusion.

| Task | Status / merged PRs | Actually run / remaining work |
|---|---|---|
| A1 camera prep | BLOCKED; [#68](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/68) | 12 fixture tests (`scripts/camera_day/tests`) + shell syntax passed; Pi install, ROS C++ build, calibration and live pose UNRUN: both SSH addresses timed out. |
| A2 C LQR | DONE; [#66](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/66) | 6 host tests (`sim/control_c/tests`), recorded parity max 1.86e-15; no STM32 deployment. |
| A3 length schedule | PARTIAL; [#65](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/65) | 14 synthetic tests (`sim/gain_schedule/tests`); 76 augmented designs and 400 balance/push cases UNRUN. |
| A4 five-bar/VMC | PARTIAL; [#69](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/69) | 14 quick tests (`sim/fivebar/tests`) including pinned-C VMC; hip/kinematics agree, mass dynamics and wheel reaction differ; nine-case dynamics comparison UNRUN. |
| B1 result tooling | DONE; [#64](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/64) | 16 tests (`sim/rl/reporting/tests`) + saved v1 report reproduced LQR160/160 vs PPO0/800; missing metrics stay explicit. |
| B2 policy export | DONE (host); [#63](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/63), [#73](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/73) | 5 real ONNX/C tests (`sim/policy_export/tests`) + 4 C LQR/actor integration tests (`sim/policy_export/integration/tests`), 1,464 recorded ticks; max LQR error7.88e-7 within1e-6. H7 cycles analytical, not measured. |
| B3 video | PARTIAL; [#67](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/67), [#71](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/71) | 11 tests (`sim/video/tests`), two tiny frames inspected across iterations; full clips and FFmpeg validation UNRUN. |
| C1 papers | DONE; [#62](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/62) | Six primary-source notes + index; source/local-link/math checks passed. |
| C2 glossary | DONE; [#60](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/60) | Term/unit/examples and GitHub math/local-link checks passed. |
| C3 links | DONE; [#59](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/59), [#70](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/70) | 12 tests (`scripts/tests/test_doc_links.py`); zero current missing paths at conductor snapshot, historical warnings retained; 17 private GitHub404s verified authenticated. |

Test commands above used `python -m unittest discover -s <test-directory> -v` with the existing backend interpreter (C3: `python3 -m unittest discover -s scripts/tests -p test_doc_links.py -v`). Reporting CLI read the original v1 aggregate; no new simulation was run for this report. Worker session files retain exact commands. Rules/progress receipts: [#61](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/61), [#72](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/72), [#74](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/74).

## PPO v2 — interim, still running

Each completed seed trained exactly 3M policy transitions and reloaded successfully; this morning's read of six saved `evaluation/outcomes.json` files confirmed 160 cases each.

| Controller | Seed0 strict / survived | Seed1 strict / survived | Seed2 strict / survived | Initial total strict / survived |
|---|---|---|---|---|
| Direct PPO | 39 / 160 | 20 / 160 | 0 / 120 | 59 / 440 out of480 |
| Residual PPO | 0 / 160 | 0 / 160 | 0 / 160 | 0 / 480 out of480 |
| LQR (reused unchanged reference) | 160 / 160 | — | — | 160 / 160 |

Direct seed3 is training (~0.84M/3M at07:48); seed4 follows under the frozen extension rule. Initial direct balance passes39; residual balance passes0, so residual stops at three seeds. Survival alone is not strict success: residual failures include the held final window/recovery criteria. No retuning or best-seed selection.

Plant parameters remain ASSUMED; PPO acts at100Hz, causal LQR at500Hz, unchanged2ms plant/delay/lag/noise. These results do not establish sim-to-real performance or RL superiority. A3's0.12–0.30m rigid-leg family is separate from A4's pinned linkage reach (~0.211m); no model/policy transfer claim.

Evidence: `~/wbr-evidence-archive/sim-ppo-v2-20261020-01`; frozen source `f1b5ee7faa41fdd45af1df7afdbddb8a1c4d66aa`. Queue, heavy-job commands and conductor receipts: `/private/tmp/wbr-overnight-20261020/{queue,verification}.json`, each task's `result.json`. Active supervisor75443; no duplicate. Training checkout/environment and owner exercise unchanged.

06:30 all-idle-account pass completed: a/b/c exhausted; d/e/g/h/i/j/k ready, default busy; g/k share one quota. The extra wakeup was deleted. One local quota-helper cleanup timeout was fixed and its retry/mock checks passed; PPO was unaffected. All runnable implementations finished; blocked heavy jobs were retained instead of rerunning tests.

**Recommendation:** finish the authorized direct seeds3/4 before final comparison; retain failed outcomes. Resume camera work when Pi/network/camera return, and run A3/A4/B3 heavy commands once compute is free. Keep the five-bar model separate until its dynamics are measured.

## Claude review

Reviewed 2026-10-21 on main. I read this file and `sim/rl/v2_config.json` /
`sim/rl/v2.py`. I re-ran nothing.

**Overnight work: accepted.**
- Done: A2, B1, B2, C1-C3.
- Partial: A3, A4, B3. Their code is merged; the heavy runs wait for free CPU.
- A1 is blocked only because the Pi was off. Run it first today, with the Pi on.
- Keep the five-bar model separate until its dynamics match the planar model.

**PPO v2 interim: real progress, plus one clear design issue.**
1. **Direct PPO now survives** 440/480 runs and passes the strict test 59/480,
   against 0/800 in v1. The survival reward and randomization worked.
2. **Strict passes are rare, and residual PPO is 0/480 even though LQR alone is
   160/160.**
   - Likely cause (inferred, not measured): `cost_scale` 0.1 makes precision
     almost free.
   - At the strict tolerance (x = 0.02 m), the per-step penalty is
     0.1 x 40 x 0.02^2, about 0.0016 against +1 for being alive. So the policies
     learn to stay up, not to settle exactly.
   - The residual output has no penalty and no zero start, so a small constant
     bias can push LQR off its exact equilibrium. That fails the final-window
     test while the robot still survives.
   - **Check:** use the B1 tool to look at final-window errors per state. A
     steady x or xdot offset would confirm this.
3. **Next experiment (v3), after seeds 3 and 4 finish; don't stop them:**
   - `cost_scale` about 2-5, so a tolerance-sized error costs about 1-5% of
     the alive reward;
   - for residual: zero-initialize the output layer, and add a penalty on the
     residual action (for example 0.5 x (a / cap)^2 per step);
   - keep everything else and the same evaluation panel.
   Run 3 seeds per arm.
