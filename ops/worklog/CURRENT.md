# Current state

Updated 2026-10-21 +07; camera visual milestone complete with limitations; simulation snapshot below retained.

## Simulation
- Obsidian three-pack series delivered under docs/learning/obsidian: LQR, RL→PPO, residual/saved-runs/experiment; reviews2026-10-21-obsidian-pack1.md and2026-10-21-obsidian-packs2-3.md. No fresh training; mismatch study remains proposed.
- Claude approved the assumed six-state planar LQR (PR44) and delay/lag/noise baseline (PR47–48). Hardware parameters remain ASSUMED/UNKNOWN; source gain parity remains the owner exercise.
- PPO v1 complete: LQR160/160, PPO0/800. See sim/rl/RESULTS_2026-10-20.md; archived evidence retained.
- PPO v2 COMPLETE 2026-10-21 12:13 +07 (PR55; frozen source f1b5ee7): eight exact3M-step seeds,all reloadPASS,1,280 evaluated cases; supervisor exited0.100Hz PPO versus unchanged500Hz LQR; no tuning.
- Direct seeds0–4 strict[39,20,0,0,0], survival[160,160,120,160,160]:59/800 strict,760/800 survived. Residual seeds0–2:0/480 strict,480/480 survived; no extension. Reused LQR160/160. Legacy episode-length/return curves unavailable. Results: sim/rl/RESULTS_V2_2026-10-20.md; review2026-10-20-ppo-v2.md. Owner requested Mac rest/charging: no further heavy work or workers until resumed.
- Evidence ~/wbr-evidence-archive/sim-ppo-v2-20261020-01; process/progress /private/tmp/wbr-ppo-v2-20261020/. Camera lab worktree updated to main; training runtime files unchanged.
- sim/parity/student.py::gain_schedule remains owner-only. Separate live LQR viewer uses parameter-source-audit checkout; Desktop launcher remains available.

## Overnight work
- f conducts; g/i/k hard,AstraUltra; b/e/default medium,Sol; d/h/j simple. Actual metadata shows g/k share one login/quota; treat them as one pool. 06:30pass completed; a/b/c exhausted,other authorized workers ready; default busy. No runnable worker task remains.
- Idle/quota checks now use documented read-only app-server metadata plus a tiny model ping; no credentials/emails retained. Shared-alias idle checks prevent duplicate use.
- A2 host C LQR mergedPR66:6testsPASS,recorded maximumerror1.86e-15; no STM32 deployment. B1 reporting mergedPR64:16testsPASS; original v1 table reproduced.
- C1 six primary-source literature notes mergedPR62; C2 glossary mergedPR60; C3 link tool mergedPR59, localized HTTP parser follow-upPR70 merged;12focused testsPASS.
- B2 real ONNX/C export and frozen-normalization parity passed5tests,no skips; PR63 merged; combined C LQR+policy integration mergedPR73:4testsPASS,1464recorded ticks,maxLQRerror7.88e-7 (limit1e-6). Isolated wheels leave the active PPO environment unchanged; H7 cycles are analytical estimates.
- Camera ROS build/link fixes mergedPR77; conductor independently rebuilt and verified linking/startup. Live visual poses and three cart-bag replays completed; see Hardware below for losses and limitations.
- A3 sweep/fitter mergedPR65:14synthetic testsPASS.76designs/400physics cases NOT RUN. Domain0.12–0.30m is a hypothetical rigid-leg family, not the five-bar workspace.
- A4 five-bar/VMC mergedPR69:14quick tests including pinned-C VMC parityPASS; kinematic/hip-power agreement measured. Mass matrix and wheel reaction differ from reduced model; heavy dynamics comparison queued.
- B3 renderer mergedPR67;11tests and one tiny framePASS. Framing improvement mergedPR71; one additional tiny frame inspected. Full balance/push clips await compute and FFmpeg; no full video claim.
- Queue/briefs/process/error receipts: /private/tmp/wbr-overnight-20261020/. 06:30wakeup completed/deleted; overnight dispatch ended. PPO completion monitor retires after final report handoff.
- Mac edits/quick tests only while PPO runs. Heavy jobs use an available Pi or wait. Morning review: reviews/2026-10-21-overnight.md. A1/A3/A4/B3 remain queued for actual execution.

## Hardware
- SSH `wbr-pi5` works; Pi5/aarch64/3.9GiB; migrated SG128 boots, expanded113GiB root,80GiBfree.
- Borrowed D435i317422076650/FW5.17.3.10 USB5000M stays mounted on robot. Calibration read-only; no robot/motor/firmware edits.
- Visual stereo/RGB-D+ROS pose accepted by Claude; review2026-10-21-camera-visual-pose.md. ImplementationPR77/79–81, reportPR84.
- Recording fix: MCAP+stereo-only+reliable images/history100. rmem max/default4194304 intentionally retained for session; no persistent sysctl file. Stationary895/895 equal headers,zero observed gaps/transportlosses.
- Fresh marked loop09:53:03–09:55:33+07:147.607s,2215left/2215right/2215CameraInfo each,identical headers,zero observed gaps/transportlosses. Owner confirms returned by120s and held30s; physical alignment not independently measured.
- Full loop+logs copied to ~/wbr-evidence-archive/camera-recording-20261021-01; loopSHA5749908bb94a6c9a7e5496f3c8b58db3596cf5f53f2542502a1468dcd97703c8 matchesPi. Older lossy loops/replays remain evidence, not new-loop endpoints.
- Native unified IMU interpolation corrected; isolated compile/link PASS, SDK body-from-camera Tbc/200Hz checks added. Single75s planar excitation exit0:final initialized61.8s,965poses,14.87trackedFPS,4loss transitions; VIBA1/2complete. Initial resets and late STOP/short stationary tail documented.
- Local50camera-day+7native tests PASS; codePR87. All176archive artifacts SHAverified; finalcalibration unchanged,allcamera/ROS/daemon stopped,PiFREE receipt10:15:21+07. Claude acceptedPR87 inPR88. New-loop3replays queued afterPPO; noMacSLAM whiletraining,Pi onlywithnewownerrelease. Queue/review2026-10-21-clean-loop-replay-queue.md;15minfollow-upactive. STM32/PPO/student exercise untouched.
