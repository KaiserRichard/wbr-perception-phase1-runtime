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
