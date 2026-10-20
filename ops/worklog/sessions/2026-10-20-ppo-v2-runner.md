# PPO v2 implementation worker — 2026-10-20

- codex-g; conductor b; dedicated `chatgpt/20261020-ppo-v2-runner`.
- Read AGENTS, CURRENT, USER_PROFILE and Claude's final review on
  `origin/claude/project-thread-2pff7j`. Owner authorized this reward/run.
- Added only `sim/rl/v2.py`, `v2_config.json`, `tests/test_v2.py` and this note.
  Runtime, v1 protocol/evaluator, owner gain exercise and hardware untouched.
- Direct and bounded residual PPO: 8 subprocess envs, 5 plant ticks/action,
  observation-only VecNormalize, exact 3M policy transitions/full seed.
  Residual LQR recomputes at 500 Hz from the causal common Observation.
- Fixed training randomization/reward in config; all 160 old evaluation cases
  and strict criteria retained. Compact 500 Hz NPZ plus per-tick integrals.
- Sequential seeds; independent strict-balance stage extension; failed attempts
  retained without retries. Completed model/stats validated before resume.
- Backend: `/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python`.
- `PYTHONPATH=. <backend> .github/run_unittest.py sim/rl/tests`: 44/44, no skips
  (18.830 s). Full LQR push/failed direct metrics match v1; zero-residual
  trajectories match 500 Hz LQR exactly at all four delays.
- `<backend> -m sim.rl.v2 smoke --out /private/tmp/wbr-ppo-v2-20261020/worker-smoke-01`:
  exit 0, 33.851 s; each arm 2,000 transitions/10 optimizer epochs, 8 envs,
  saved/reloaded model+stats and deterministic held-out evaluation.
  Direct: fall; residual: strict PASS. Smoke only, no learned-policy claim.
- Code review fixed stale capture after failed evaluation reset; regression
  included. Fresh final smoke in `worker-smoke-02`; original artifacts retained.
- Resume check: both complete smoke seeds reused without retraining or changing
  checkpoint/stats/status. No full training, other accounts, push or merge.
- Logs, final timing, limitations and commit: `/private/tmp/wbr-ppo-v2-20261020/worker-report.md`.
