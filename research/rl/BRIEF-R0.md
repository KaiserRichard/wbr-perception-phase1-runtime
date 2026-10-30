# R0 brief (codex-e): reopen RL with a plan that learns from v1–v3

Owner decision, 2026-10-30: reopen RL as a research axis. It was closed on 22 Oct after v1–v3.
Write `research/rl/PLAN.md` (max ~150 lines, English). Don't commit. Edit only that file.

Read first:
- On `main` (use `git show origin/main:<path>`):
  - `sim/rl/RESULTS_2026-10-20.md`, `sim/rl/RESULTS_V2_2026-10-20.md`;
  - `ops/worklog/reviews/2026-10-21-v3-research.md`, `ops/worklog/reviews/2026-10-22-v3-pilot-result.md`;
  - `ops/worklog/reviews/2026-10-20-cafe-compute-strategy.md`, `ops/worklog/DECISIONS.md` (D-20261020-CAFE);
  - `docs/learning/MODEL_PARAMETER_SOURCES.md`, `docs/lessons/05_wbr_jump_sequence.md`.
- `research/explore/x2-rl-locomotion.md` in this worktree.

Facts to respect:
- The WBR has DM-J4310 hip and DM-H6215 wheel motors, and no micro-ROS.
- Single parameter source: team-report masses 3.5/0.2/0.7 kg; five-bar 0.075/0.14/0.08 m; wheel radius 0.0603 m. Inertias are ASSUMED.
- `sim/parity/student.py::gain_schedule` is owner-only.
- Compute is an internet-cafe NVIDIA PC: likely Windows, no admin rights, wiped at shutdown, 2–4 h sessions. Its exact config is PENDING from the owner.

PLAN.md sections:
1. **Why v1–v3 failed.** Separate MEASURED from INFERRED: reward barely penalising precision, CPU sample budget, direct torque at 100–500 Hz, noise. For each, the concrete change.
2. **Task ladder.** Balance + speed tracking → low step → jump with the 4-phase reference as a prior or residual. For each rung give the pass criteria fixed in advance, the LQR / mode-switch baseline, 5 seeds, and a matched budget.
3. **Reward and action design.** Precision-weighted terms with scales computed so that a 2 cm error matters; action-rate penalty; residual-on-LQR vs direct.
4. **Stack options for a Windows cafe PC**, as a compatibility matrix:
   - MJX/JAX: CUDA JAX needs Linux or WSL2;
   - MuJoCo Warp;
   - Isaac Lab on Windows;
   - SB3 + CPU MuJoCo as a fallback.
   For each say what works without admin rights. Open and cite official install docs. Mark UNVERIFIED where you can't confirm.
5. **Portable bundle design:** a USB/zip layout, one setup script, a checkpoint every N minutes, and resume. Results get pushed or copied off before shutdown.
6. **First 3 cafe sessions:** an exact plan per 2–4 h session, the GPU-hours estimate, and what each session must output.
7. **Risks**, and what result would make us close RL again.
