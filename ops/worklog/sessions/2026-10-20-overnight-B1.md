# B1 — saved-evidence reporting

- Dedicated `chatgpt/20261020-result-tools` worktree started clean at `6fbe9a3`.
  Read AGENTS, USER_PROFILE, CURRENT, RESEARCH_RULES and existing aggregate,
  metrics/evaluation/v2 archive writers before edits. Owner worker limits apply.
- Added only `sim/rl/reporting/` plus this log: standard-library CLI, v1/v2
  readers, Markdown/JSON/CSV comparison tables, seven SVG plots, usage and tests.
  All declared seeds and delay/scenario panels remain visible. Expected versus
  observed coverage, null recovery, saved failure penalties, action/plant rates,
  conditional extensions and one frozen LQR reference remain explicit.
- First real CLI on saved v1 aggregate passed before fixture checks. Combined
  CSV fields subsequently handle both version schemas. Input limits reject large
  JSON; no NPZ, trace, checkpoint, simulator or training imports/reads.
- Final validation (single-thread BLAS environment), **16/16 passed**:
  `/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python -m unittest discover -s sim/rl/reporting/tests -v`.
- Same Python: `-m sim.rl.reporting --v1-aggregate /Users/quockaiser/wbr-evidence-archive/sim-ppo-vs-lqr-20261020-01/evaluation/aggregate.json --out /private/tmp/wbr-overnight-20261020/B1/report-final`.
  Exit 0, 54 rows, 339201 JSON bytes; archived rates 500 Hz; LQR160/160,
  PPO0/800 across all five seeds. Tests + CLI **0.509 s total** (<20 s).
  `git diff --check` passed. Full suites/training/replay were not run.
- External artifacts: `/private/tmp/wbr-overnight-20261020/B1/report-final/`
  (tables and seven SVGs), `validation-final.txt`, `validation-summary.json`.
- Limitations: v1 aggregate omits survival joint events, so survival is NA;
  unavailable rates stay unknown without archived protocol. v2 covered by small
  analytic fixtures (partial seeds, interrupted evaluation, smoke, duplicate
  identities, null recovery, 100 Hz action/500 Hz plant); no live evaluation run.
  No new intervals, archive hash audit, hardware evidence or cross-version
  algorithm-only inference. Full v2 report awaits saved completed results.
- No backend/environment/config/reward/training/owner gain changes; no active
  evidence mutation or other account/checkout use. Conductor handles central
  documentation logs, decisions, CI verification and merge.
