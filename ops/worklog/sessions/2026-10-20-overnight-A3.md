# A3 — separate assumed-model leg gains, 2026-10-20

- Assigned worktree/branch: `overnight-gain/wbr-lab-ops`,
  `chatgpt/20261020-leg-gains`; initial tree clean, base `6fbe9a3`.
  Read AGENTS, USER_PROFILE, CURRENT, RESEARCH_RULES and existing plant,
  delay/lag synthesis/evaluator. Owner's worker/account/resource limits override
  older conductor instructions. No subagents, other accounts, Pi, or hardware.
- Added only `sim/gain_schedule/` and this log. Existing plant/configs, active
  backend/evidence, PPO, and owner-only `sim/parity/student.py` untouched.
- Implemented serial `sweep`, `fit`, and `evaluate` commands. Default sweep:
  19 lengths (0.12–0.30 m), four separate delay regimes (2/3/4/5 ms).
  Recomputes fresh nominal diagnostic gains and augmented DARE gains.
  No DM-jump/student coefficient import or copied polynomial solution.
- Explicit assumed fixed-mass rigid-leg family scales COM by L/L0 and inertia
  by (L/L0)^2 in config copies. Original Q/R, runtime timing/noise, limits,
  initial conditions and acceptance protocol are retained.
- Cubic Chebyshev least squares on normalized [-1,1]; saved basis/order,
  rank/singular values/conditioning, per-entry and matrix errors. Rejects
  extrapolation/nonfinite inputs, incomplete grids, mixed ordering, rank loss
  and condition number >1e8. Separate coefficient matrices per delay.
- Documentation added: `sim/gain_schedule/README.md`, with modeling derivation,
  synthetic worked example, output/exit semantics and complete queued commands.
  Central documentation log/decisions/review intentionally left to conductor.
- Actual validation, with OPENBLAS/OMP/MKL/VECLIB/NUMEXPR thread limits all 1
  and PYTHONDONTWRITEBYTECODE=1:
  `/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python -m unittest discover -s sim/gain_schedule/tests -v`
  initially 11/11 in 0.069 s; after synthetic runner coverage, 14/14 in 0.416 s.
  Tests use NumPy/config arithmetic and fake backend fixtures only, including
  five-length balance/push routing and preserved FAIL results. No real MuJoCo
  synthesis/rollouts or training ran. CLI `--help` and `git diff --check` passed.
- Pending heavy jobs: real 76-design sweep; dependent real-data fit; evaluation
  at 0.12/0.165/0.21/0.255/0.30 m, four delays, fresh DARE versus polynomial,
  seeds 0–4, balance+push = 400 unchanged 10 s cases. Single-process commands
  are in README and worker result JSON. Queue until PPO ends on Mac, or conduct
  separately on a reachable Pi with its own checkout/environment.
- Honest status: implementation/synthetic validation complete; overall A3
  partial until real gains and physical evaluations are run. No measured local
  stability, nonlinear acceptance, continuous-length stability, varying-length
  behavior, source-gain parity, or hardware validation claimed.
- Feature commit `252fd0d` pushed; opened
  [PR #65](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/65).
  Not merged; conductor verifies/merges. No attach_artifact tool was exposed;
  PR URL is returned in worker result for conductor attachment.
