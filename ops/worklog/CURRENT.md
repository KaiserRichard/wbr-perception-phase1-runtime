# Current state

Updated 2026-10-20 23:10 +07; overnight owner override: codex-f conducts.

## Completed simulation milestone
- Nominal assumed six-state MuJoCo/LQR approved by Claude in PR44. Actuator delay/lag/IMU extension merged PR47; final actuator review merged PR48.
- Frozen original K failed 40/40 controlled settling checks. Conditional delay-state LQR passed 40/40; no Q/R, acceptance or physical-limit changes. Source gain parity remains incomplete.
- PPO implementation merged PR49 (e821212), after both CI checks passed at head781d702. Conductor independently passed 27/27 RL tests and real optimizer/reload smoke.
- FULL comparison COMPLETE, exit0: five policies ×150000 steps (750000 total), 800 PPO +160 unique LQR evaluation episodes. LQR160/160 successes; PPO0/800, with680 falls and120 displacement exits. No numerical/training failures or retuning.
- All five seed success differences are−1; prescribed 95%t interval[-1,−1], df4. This is a conditional, degenerate endpoint result, not proof that RL generally fails or that real-world uncertainty is zero.
- Independent audit:6680 hashes, five budgets/checkpoints,960 episode identities, all800 paired noise prefixes and raw metric spot checks verified. Stable archive: ~/wbr-evidence-archive/sim-ppo-vs-lqr-20261020-01.
- Read sim/rl/RESULTS_2026-10-20.md. Full panel/secondary metrics: archive/evaluation/aggregate.json. Claude review75a304d confirms valid execution/limited interpretation and authorizes v2.
- Parameter source table/guide link and float64 test-oracle repair merged PR50 (31a5d1a), both CI checks green. Current physical values remain ASSUMED or UNKNOWN; runtime/reward unchanged.

## Next step and ownership
- RUNNING PPO v2: direct+residual,100Hz policy,eight envs,observation VecNormalize,3M POLICY steps/seed,initial3seeds/arm; extend each arm to5 only after strict balance PASS. Sourcef1b5ee7; prior result retained. Full run started2026-10-20 16:43+07; may run overnight or longer.
- v2 implementation merged PR55; prior44/44tests,optimizer/reload and zero-residualLQR parity passed. Directseed0:3M transitions,39/160strictPASS,160/160survival; residualseed0 evaluation running. Full experiment incomplete.
- Active output: ~/wbr-evidence-archive/sim-ppo-v2-20261020-01; process/console/progress at /private/tmp/wbr-ppo-v2-20261020/. Heartbeat finish-ppo-v2-comparison checks every30min; never duplicate active job.
- docs/learning/LQR_RL_GUIDE.md explains geometry, energy/dynamics, LQR and the measured RL result. sim/parity/student.py gain_schedule remains the owner's exercise.
- Model has assumed masses/COM, ideal planar rolling/equivalent rigid leg, known delay/lag and four ideal sensor channels; no full-five-bar/contact or sim-to-real validation.
- Visual demo: Desktop `WBR Simulation.command`, or `.venv/bin/mjpython -m sim.view` in the viewer checkout. Space pause,P push,R reset. Separate live LQR simulation; closing it leaves PPO running. See sessions/2026-10-20-sim-viewer.md.

## Hardware
- Pi/camera track remains deferred until equipment returns; no Pi build/live ROS pose/STM32/motor action in this milestone.
- Last measured cafe SSH: richard@wbr-pi5.local →192.168.111.243; old alias uses Ethernet192.168.50.2. Addresses can change. 128GB migration completion UNKNOWN.
- Nominal archive ~/wbr-evidence-archive/sim-lqr-20261020-01; actuator archive ~/wbr-evidence-archive/sim-actuator-20261020-01.
- Pre-existing host-test generated files remain untracked/unstaged and untouched. Every document change is recorded in DOCUMENTATION_LOG.

## Overnight queue
- f conducts eight idle/quota-checked workers: g/A1,i/A2,k/A3,b/B1,e/B2,d/C1,h/C2,j/C3; A4/B3 queued. Session: sessions/2026-10-20-overnight.md; external state: /private/tmp/wbr-overnight-20261020/queue.json.
- Every30min +06:30 refill wakeups active. Mac code/quick tests only while PPO runs; heavy sweeps/rendering await Pi or completed training. Root checkout and student.py protected.
- Morning Claude handoff only: reviews/2026-10-21-overnight.md (honest task status/PR); no milestone review stops overnight.
