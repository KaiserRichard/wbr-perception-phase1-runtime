# Current state

Updated 2026-10-20 23:37 +07; codex-f conducts the overnight queue.

## Simulation
- Claude approved the assumed six-state planar LQR (PR44) and delay/lag/noise baseline (PR47–48). Hardware parameters remain ASSUMED/UNKNOWN; source gain parity remains the owner exercise.
- PPO v1 complete: LQR160/160, PPO0/800. See sim/rl/RESULTS_2026-10-20.md; archived evidence retained.
- PPO v2 RUNNING independently (PR55; frozen source f1b5ee7): eight envs,3M policy transitions/seed,100Hz policy,unchanged500Hz plant/LQR. Supervisor75443; no duplicate or tuning.
- Seed0 only: direct39/160 strict successes,160/160survival; residual0/160 strict,160/160survival. Both trained3M/reloadPASS. Directseed1 now training; full comparison incomplete. Conditional extension rule unchanged.
- Evidence ~/wbr-evidence-archive/sim-ppo-v2-20261020-01; process/progress /private/tmp/wbr-ppo-v2-20261020/. Root training checkout stays32c00c4.
- sim/parity/student.py::gain_schedule remains owner-only. Separate live LQR viewer uses parameter-source-audit checkout; Desktop launcher remains available.

## Overnight work
- f conducts; g/i/k hard,AstraUltra; b/e/default medium,Sol; d/h/j simple. Actual metadata shows g/k share one login/quota; treat them as one pool. Reset reported02:16local. Default app chat reserved/busy.
- Idle/quota checks now use documented read-only app-server metadata plus a tiny model ping; no credentials/emails retained. Shared-alias idle checks prevent duplicate use.
- A2 host C LQR mergedPR66:6testsPASS,recorded maximumerror1.86e-15; no STM32 deployment. B1 reporting mergedPR64:16testsPASS; original v1 table reproduced.
- C1 six primary-source literature notes mergedPR62; C2 glossary mergedPR60; C3 link tool mergedPR59, localized HTTP parser follow-upPR70 pending.
- B2 real ONNX/C export and frozen-normalization parity passed5tests,no skips; PR63 pending merge. Isolated wheels leave the active PPO environment unchanged; H7 cycles are analytical estimates.
- A1 D435 wrapper/launch/bag/calibration prep PR68:12fixturetests and shell syntaxPASS. Pi install/C++build/live camera still UNVERIFIED.
- A3 sweep/fitter mergedPR65:14synthetic testsPASS.76designs/400physics cases NOT RUN. Domain0.12–0.30m is a hypothetical rigid-leg family, not the five-bar workspace.
- A4 five-bar/VMC PR69:14quick tests including pinned-C VMC parityPASS; kinematic/hip-power agreement measured. Mass matrix and wheel reaction differ from reduced model; heavy dynamics comparison queued.
- B3 renderer mergedPR67;11tests and one tiny framePASS. Framing improvement in flight. Full balance/push clips await compute and FFmpeg; no full video claim.
- Queue/briefs/process/error receipts: /private/tmp/wbr-overnight-20261020/. Every30min follow-up and06:30refill/resume active; morning report checkpoint08:00local.
- Mac edits/quick tests only while PPO runs. Heavy jobs use an available Pi or wait. One morning Claude review only: reviews/2026-10-21-overnight.md.

## Hardware
- Pi alias richard@192.168.50.2 and last cafe address192.168.111.243 timed out tonight. No remote install/build or physical validation performed; no network scan.
- Camera D435/noIMU, SDKserial048622071151; camera day resumes when hardware/network return.128GB migration completion UNKNOWN.
- Mac is on AC, charging; caffeinate remains attached to the independent PPO supervisor. STM32/motors untouched. Pre-existing root untracked build artifacts preserved.
