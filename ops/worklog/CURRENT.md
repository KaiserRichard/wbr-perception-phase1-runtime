# Current state

Updated 2026-10-21 +07; camera visual milestone complete with limitations; simulation snapshot below retained.

## Simulation
- Obsidian LQR/RL/PPO lesson proposal: reviews/2026-10-21-obsidian-lqr-ppo-plan.md; owner requested Claude review before lesson/images/ZIP. Preferences saved in USER_PROFILE and portable skill; no experiment changes.
- Claude approved the assumed six-state planar LQR (PR44) and delay/lag/noise baseline (PR47–48). Hardware parameters remain ASSUMED/UNKNOWN; source gain parity remains the owner exercise.
- PPO v1 complete: LQR160/160, PPO0/800. See sim/rl/RESULTS_2026-10-20.md; archived evidence retained.
- PPO v2 RUNNING independently (PR55; frozen source f1b5ee7): eight envs,3M policy transitions/seed,100Hz policy,unchanged500Hz plant/LQR. Supervisor75443; no duplicate or tuning.
- Initial seeds0–2 complete: direct strict[39,20,0]/160 each, survival[160,160,120]; residual strict[0,0,0], survival[160,160,160]. All exact3M/reloadPASS. Directseed3 training~0.84M; seed4 follows; residual has no extension. Full comparison incomplete.
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
- Queue/briefs/process/error receipts: /private/tmp/wbr-overnight-20261020/. 06:30wakeup completed/deleted; overnight dispatch ends with handoff. PPO completion monitor remains active.
- Mac edits/quick tests only while PPO runs. Heavy jobs use an available Pi or wait. Morning review: reviews/2026-10-21-overnight.md. A1/A3/A4/B3 remain queued for actual execution.

## Hardware
- SSH works: `ssh wbr-pi5` -> richard@192.168.50.2; WiFi192.168.0.107 at readback. Actual Pi has3.9GiBRAM. SG128 card boots; expanded root113GiB/82GiB free at final readback.
- Borrowed D435i317422076650/FW5.17.3.10 atUSB5000M; mount remains on mobile robot. SDK calibration readback unchanged after first native/ROS runs; no calibration writes/firmware/robot config edits.
- Headless native helpers, metrics and export merged PR79–81; ROS build fixes PR77. Pi evidence: ~/wbr-evidence/camera-day-20261021-01; final Mac archive: ~/wbr-evidence-archive/camera-day-20261021-01-final.
- Native stereo30Hz/800:29.76trackedFPS,0loss/overwrites;RGBD15Hz/800:14.65FPS;throttle0x0. BothROSvisualmodespublishposes. Inertialtransientlyinitializes thenresets;nouserusabletrajectory.
- Loop03 saved09:00:30–09:03:00+07 despitechatinterruption;1.9GiB,1318transportlosses. Ownerreportsreturnat120s/hold30s;alignmentnotgroundtruth.
- COMPLETE: three fresh 0.5x replays, all processes/exports exit0. Endpoints 0.6963/0.6957/0.6927 m; 3.379/3.386/3.339% estimated path; loop detections yes/yes/no; loss episodes15/18/15. Map resets/merges invalidate pure continuous-map drift accuracy.
- Final calibration readback identical; temporary receive buffers restored; owned camera/replay processes stopped. Next: Claude review reviews/2026-10-21-camera-visual-pose.md, recording-loss fix and sustained inertial motion retry. STM32/motors/protected exercise untouched.
