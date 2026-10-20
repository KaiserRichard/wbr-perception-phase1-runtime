# Current state

Updated 2026-10-20 +07; owner switched this chat's conductor from codex-f to codex-b.

## Completed simulation milestone
- Nominal assumed six-state MuJoCo/LQR approved by Claude in PR44. Actuator delay/lag/IMU extension merged PR47; final actuator review merged PR48.
- Frozen original K failed 40/40 controlled settling checks. Conditional delay-state LQR passed 40/40; no Q/R, acceptance or physical-limit changes. Source gain parity remains incomplete.
- PPO implementation merged PR49 (e821212), after both CI checks passed at head781d702. Conductor independently passed 27/27 RL tests and real optimizer/reload smoke.
- FULL comparison COMPLETE, exit0: five policies ×150000 steps (750000 total), 800 PPO +160 unique LQR evaluation episodes. LQR160/160 successes; PPO0/800, with680 falls and120 displacement exits. No numerical/training failures or retuning.
- All five seed success differences are−1; prescribed 95%t interval[-1,−1], df4. This is a conditional, degenerate endpoint result, not proof that RL generally fails or that real-world uncertainty is zero.
- Independent audit:6680 hashes, five budgets/checkpoints,960 episode identities, all800 paired noise prefixes and raw metric spot checks verified. Stable archive: ~/wbr-evidence-archive/sim-ppo-vs-lqr-20261020-01.
- Read sim/rl/RESULTS_2026-10-20.md. Full panel/secondary metrics: archive/evaluation/aggregate.json. Final Claude review: ops/worklog/reviews/2026-10-20-rl-comparison.md (prepared; Claude response pending).
- Parameter source table/guide link and float64 test-oracle repair merged PR50 (31a5d1a), both CI checks green. Current physical values remain ASSUMED or UNKNOWN; runtime/reward unchanged.

## Next step and ownership
- ACTIVE: owner authorized Claude-reviewed PPO v2 (review75a304d): direct plus residual,100Hz policy,eight envs,observation VecNormalize,3M policy steps,initial3seeds/arm. Implementation and optimizer checks running; full training not yet launched. v1 result retained.
- g/AstraUltra implements v2 in isolated ppo-outcome-audit worktree/runner branch after idle check. i launch hit quota; k busy elsewhere. Conductor independently checks; b reserved. Short v2 session/log paths in sessions/2026-10-20-ppo-v2.md.
- docs/learning/LQR_RL_GUIDE.md explains geometry, energy/dynamics, LQR and the measured RL result. sim/parity/student.py gain_schedule remains the owner's exercise.
- Model has assumed masses/COM, ideal planar rolling/equivalent rigid leg, known delay/lag and four ideal sensor channels; no full-five-bar/contact or sim-to-real validation.

## Hardware
- Pi/camera track remains deferred until equipment returns; no Pi build/live ROS pose/STM32/motor action in this milestone.
- Last measured cafe SSH: richard@wbr-pi5.local →192.168.111.243; old alias uses Ethernet192.168.50.2. Addresses can change. 128GB migration completion UNKNOWN.
- Nominal archive ~/wbr-evidence-archive/sim-lqr-20261020-01; actuator archive ~/wbr-evidence-archive/sim-actuator-20261020-01.
- Pre-existing host-test generated files remain untracked/unstaged and untouched. Every document change is recorded in DOCUMENTATION_LOG.
