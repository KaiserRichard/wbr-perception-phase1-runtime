# Current state

Updated 2026-10-20 +07 by codex-f conductor.

## Simulation / control
- Claude approved nominal assumed six-state MuJoCo/LQR in PR44. Nominal PR42, parity scaffold PR38, guide PR45 and frozen RL protocol PR46 merged.
- NEW: causal 2/3/4/5 ms delay, 5 ms motor lag, body-only IMU noise implemented at source0900606. These parameter values are ASSUMED.
- Conductor completed120 cases: frozen K0/40 controlled successes; delay-aware LQR40/40; all40 expected-fall controls passed. Frozen failures are settling/recovery, no controlled falls. No thresholds or Q/R changed.
- Conditional recovery1.756–2.762s. Same seeds/noise, limits, initial state and0.9Ns push. Freeze conditional per-delay gains for the PPO comparison; retain nominal failures.
- Conductor27/27 simulation tests PASS, zero skips;373 artifact hashes and paired noise hashes verified. Raw run /private/tmp/wbr-actuator-conductor-20261020-05; merged in PR47 after both CI checks passed.
- RL protocol merged: five independent policies,150000 steps each;20 held-out noise seeds ×8 conditions/policy. Compatible Intel Mac backend verified, but actual WBR PPO code/training NOT complete.
- Next: publish verified actuator milestone, implement/check PPO adapter/trainer/evaluator, then train and compare on this identical plant. Claude reviews completed milestones only.

## Accounts / learning
- Owner prioritizes codex-b until reported expiry tomorrow. After its unrelated task completed07:52:11Z, b/AstraUltra was assigned PPO implementation in its isolated worktree. g/i/k hit usage limits; f remains conductor.
- Read docs/learning/LQR_RL_GUIDE.md: geometry, energy/dynamics, linearization, LQR, delay/noise and RL comparison. All64 math expressions rendered successfully; analytical A/B checked against MuJoCo.
- sim/parity/student.py gain_schedule remains owner-only TODO. Source gain/VMC parity incomplete. No sim-to-real or full-five-bar claim.

## Hardware
- Pi track deferred by owner: slow32GB card and no camera this afternoon; camera lab planned tomorrow. No Pi build/live ROS pose/STM32/motor action in this milestone.
- Last measured cafe SSH: richard@wbr-pi5.local →192.168.111.243. Old alias points to Ethernet192.168.50.2. Addresses can change;128GB migration status UNKNOWN.
- Prior nominal archive ~/wbr-evidence-archive/sim-lqr-20261020-01. New actuator archive ~/wbr-evidence-archive/sim-actuator-20261020-01; final review reviews/2026-10-20-actuator-noise.md pending Claude. No gate promoted.
- Pre-existing generated host-test files remain untracked and unstaged.
