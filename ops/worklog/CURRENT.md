# Current state

Last updated: 2026-10-20 +07 by codex-f conductor; nominal simulation baseline approved by Claude (PR44); actuator/noise milestone active.

## Active goal
- PRIORITY: delay2-5ms + motorlag + IMUnoise, frozenK first; conditional augmentedLQR then same-plant RL across seeds. Mac simulation/control. ASSUMED reduced six-state MuJoCo model + NEW matched LQR + declared push recovery implemented, independently rerun and merged in PR42 (caae6ff).
- PR38 parity scaffold, PR40 conducting rules and PR41 Pi preparation also merged after green CI. See final review ops/worklog/reviews/2026-10-20-lqr-mujoco.md.
- Claude only reviews completed milestones. Conductor verifies and merges green PRs; worker accounts checked idle, f reserved for conductor.

## Results
- Conductor: balance recovery1.732s; 6N*0.15s push recovery2.714s, post-push peak6.095deg; zero-control fall0.182s. Controlled10s runs: caps respected, no saturation/warnings.
- Simulation11/11 testsPASS, parity infrastructure15/15PASS, ROS-free wrapper19/19PASS. Linux CI green at exact PR42head be061d8, including actual MuJoCo CLI.
- Stable raw/config/model/source/plot archive: ~/wbr-evidence-archive/sim-lqr-20261020-01, SHA256.json34entries. Commands/hashes in final review/session log.
- sim/parity/student.py gain_schedule remains owner-only TODO. Gain/VMC parity incomplete; this new LQR does not reproduce source gains.

## Hardware and Pi track
- Owner explicitly deferred Pi work due slow32GB microSD/no camera. No Pi build, SLAM/ROS-pose run, storage migration or STM32/motor commands this session.
- Cafe SSH works: richard@wbr-pi5.local ->192.168.111.243. Measured Pi5ModelB,4GBRAM,root6.2Gfree; native stereo_euroc/MH01/ROS2/colcon exist. Address may change with network.
- g worker briefly inventoried read-only, then stopped at owner priority change. Pi stereo/ROS worktree clean and retained; runtime milestone not achieved.
- Old alias wbr-pi5 still points to Ethernet192.168.50.2; not changed. D435 absent this afternoon; prior power evidence historical only.128GBmigration completionUNKNOWN.

## Limitations and next step
- Nominal ASSUMED masses/COM/inertias, ideal planar rolling, fixed equivalent leg, ideal state feedback/instant torque. No contact/slip, fullfivebar, physical validation or RLtraining.
- Claude approved baseline in ops/worklog/reviews/2026-10-20-lqr-mujoco.md (main417c1e2). i/AstraUltra implements actuator/noise; conductor writes short learning guide. RL execution waits for actuator/LQR verification.
- Read docs/learning/LQR_RL_GUIDE.md (~50lines). Pi remains deferred; owner plans camera lab tomorrow with equipment.
- Two understanding questions sent; answers pending. No gate promoted. Pre-existing generated host-test binaries remain untracked and unstaged; no deletion performed.
