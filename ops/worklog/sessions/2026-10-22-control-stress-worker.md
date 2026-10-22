# Control stress worker — 22 October 2026

- Owner transferred follow-up (a) to codex-k; source worktree
  `/Users/quockaiser/.codex/worktrees/reachable-gain-study/wbr-lab-ops`, branch
  `chatgpt/20261022-control-stress`; starting commit `2eea34e`.
- Read root/sim AGENTS, RESEARCH_RULES, CURRENT, profile and appended Claude PR110
  review. Scope: four stress axes, fixed nominal 2 ms observer/gain, no RL/Pi/
  hardware/other agents, no frozen code/config/student/evidence edits. Parent owns
  CURRENT and consolidated review; no DOCLOG/DECISIONS entries.
- Added only `sim/gain_schedule/stress.py`, focused `tests/test_stress.py`, and a
  new README stress section. One new nominal augmented DARE, unchanged Q/R;
  independent controller reconstructs torque from its own clipped commands.
- First `python -m sim.gain_schedule.stress --help` attempt exited 1: SyntaxError
  in starred conditional command-argument expansion (line 337). Parenthesized
  the expression; no rollout started and no evidence directory was reused.
- Focused actual run: existing read-only interpreter
  `/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python`
  `-m unittest sim.gain_schedule.tests.test_stress -v`, with
  `PYTHONDONTWRITEBYTECODE=1`, OPENBLAS/OMP/MKL/VECLIB_MAXIMUM/NUMEXPR threads=1,
  `WBR_STRESS_TEST_OUT=/Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/stress/fixtures`.
  Exit 0; **9 tests PASS, 1.239 s**. Matched action maximum difference
  **4.4408920985006262e-15 Nm**, including clipping. Retained injected ERROR,
  real early-fall FAIL and short strict FAIL fixtures; actual map/mass and
  hidden-state causality fixtures pass. Log: `stress/fixtures/tests-01.log`.
- Production pending source commit. Declared schedule: at most 57 unique cases
  (hard cap 60); baseline first; push stop/bisection; remaining finite grids;
  five-seed confirmation, with nominal/seed-0 reuse. Full 10 s or evaluator's
  physical/numerical stop. All new evidence below
  `/Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/stress`.
