# Current state

Updated 2026-10-21 07:48 +07; overnight handoff prepared; PPO continues.

## Simulation
- Obsidian three-pack series delivered under docs/learning/obsidian: LQR, RL→PPO, residual/saved-runs/experiment; reviews2026-10-21-obsidian-pack1.md and2026-10-21-obsidian-packs2-3.md. No fresh training; mismatch study remains proposed.
- Claude approved the assumed six-state planar LQR (PR44) and delay/lag/noise baseline (PR47–48). Hardware parameters remain ASSUMED/UNKNOWN; source gain parity remains the owner exercise.
- PPO v1 complete: LQR160/160, PPO0/800. See sim/rl/RESULTS_2026-10-20.md; archived evidence retained.
- PPO v2 RUNNING independently (PR55; frozen source f1b5ee7): eight envs,3M policy transitions/seed,100Hz policy,unchanged500Hz plant/LQR. Supervisor75443; no duplicate or tuning.
- Initial seeds0–2 complete: direct strict[39,20,0]/160 each, survival[160,160,120]; residual strict[0,0,0], survival[160,160,160]. All exact3M/reloadPASS. Directseed3 training~0.84M; seed4 follows; residual has no extension. Full comparison incomplete.
- Evidence ~/wbr-evidence-archive/sim-ppo-v2-20261020-01; process/progress /private/tmp/wbr-ppo-v2-20261020/. Root training checkout stays32c00c4.
- sim/parity/student.py::gain_schedule remains owner-only. Separate live LQR viewer uses parameter-source-audit checkout; Desktop launcher remains available.

## Overnight work
- f conducts; g/i/k hard,AstraUltra; b/e/default medium,Sol; d/h/j simple. Actual metadata shows g/k share one login/quota; treat them as one pool. 06:30pass completed; a/b/c exhausted,other authorized workers ready; default busy. No runnable worker task remains.
- Idle/quota checks now use documented read-only app-server metadata plus a tiny model ping; no credentials/emails retained. Shared-alias idle checks prevent duplicate use.
- A2 host C LQR mergedPR66:6testsPASS,recorded maximumerror1.86e-15; no STM32 deployment. B1 reporting mergedPR64:16testsPASS; original v1 table reproduced.
- C1 six primary-source literature notes mergedPR62; C2 glossary mergedPR60; C3 link tool mergedPR59, localized HTTP parser follow-upPR70 merged;12focused testsPASS.
- B2 real ONNX/C export and frozen-normalization parity passed5tests,no skips; PR63 merged; combined C LQR+policy integration mergedPR73:4testsPASS,1464recorded ticks,maxLQRerror7.88e-7 (limit1e-6). Isolated wheels leave the active PPO environment unchanged; H7 cycles are analytical estimates.
- A1 D435 wrapper/launch/bag/calibration prep mergedPR68:12fixturetests and shell syntaxPASS. Pi install/C++build/live camera still UNVERIFIED.
- A3 sweep/fitter mergedPR65:14synthetic testsPASS.76designs/400physics cases NOT RUN. Domain0.12–0.30m is a hypothetical rigid-leg family, not the five-bar workspace.
- A4 five-bar/VMC mergedPR69:14quick tests including pinned-C VMC parityPASS; kinematic/hip-power agreement measured. Mass matrix and wheel reaction differ from reduced model; heavy dynamics comparison queued.
- B3 renderer mergedPR67;11tests and one tiny framePASS. Framing improvement mergedPR71; one additional tiny frame inspected. Full balance/push clips await compute and FFmpeg; no full video claim.
- Queue/briefs/process/error receipts: /private/tmp/wbr-overnight-20261020/. 06:30wakeup completed/deleted; overnight dispatch ends with handoff. PPO completion monitor remains active.
- Mac edits/quick tests only while PPO runs. Heavy jobs use an available Pi or wait. Morning review: reviews/2026-10-21-overnight.md. A1/A3/A4/B3 remain queued for actual execution.

## Hardware
- Pi alias richard@192.168.50.2 and last cafe address192.168.111.243 timed out tonight. No remote install/build or physical validation performed; no network scan.
- Camera D435/noIMU, SDKserial048622071151; camera day resumes when hardware/network return.128GB migration completion UNKNOWN.
- Mac AC attached at07:43,72%; caffeinate remains attached to the independent PPO supervisor. STM32/motors untouched. Pre-existing root untracked build artifacts preserved.
