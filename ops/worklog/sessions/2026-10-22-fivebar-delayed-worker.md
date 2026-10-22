# Fivebar delayed local linear worker — 2026-10-22

- Owner-authorized codex-i; branch `chatgpt/20261022-fivebar-delayed-linear`, worktree `/Users/quockaiser/.codex/worktrees/fivebar-linear-review/wbr-lab-ops`. Read root/sim AGENTS, RESEARCH_RULES, CURRENT/profile and appended Claude PR110 control review.
- Scope: new `sim/fivebar/delayed_linear.py`, its focused test module, appended README delay section and this session only. Existing runtime/model/linearize/compare/LQR/configs and owner-only gain function unchanged. No agents/accounts/chats/Pi/SSH/hardware/training/deletion/force-push/merge.
- Initial scalar lift executed before tests; all four exact transport cases produced expected history ordering and zero current-input physical effect. No failed calculation or implementation fix so far.
- Implementation commit `b51237f0f2b9fb349699cd792982bf0917b6e488`; draft [PR114](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/114). Early handoff written before documentation completion: `/private/tmp/wbr-control-margins-20261022/i-ready.md`; exact PR body in `i-pr-body.md` beside it.
- **11 focused tests PASS**, 0.724 s suite; log `/Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/fivebar-delay/tests-01.log`. Analytical integrator/lag and coupled scalar solutions, fractional arrivals/history shift, zero equilibrium/channel independence, feedback sign/unstable retention, saved eigenpairs, production/output guards and one bounded actual reduced runtime check.
- Local reduced L=.16/delay3ms finite-difference check: A Frobenius discrepancy from exact lift decreases `4.41725748e-7→1.10438553e-7` for `0.25→0.125 ms` mechanics; no false equivalence threshold. Fresh augmented DARE has unchanged Q/R and expected 12-state history order. No nonlinear trajectory run.
- Full production is pending conductor `STRESS_FIRST_RUN.json`; CLI enforces marker and clean committed source. Planned fresh continuous sources: all four lengths, 3 projection × 3 paired state/input refinements each; selected epsilons `1e-6` each. Planned refinement conditions: L=.12/delay3ms and L=.21/delay5ms. Each row will use fresh actual-runtime K, unchanged Q/R and identical K on both exact lifts.
- README documents derivation, worked analytic fixture, observer assumption, exact arrivals, separate actual-runtime approximation, output schema and limits. No global worklogs updated; parent owns CURRENT/final review.

Exact commands (from the worktree; existing venv read-only, no installs):

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
nice -n 10 "$PY" -m unittest sim.fivebar.tests.test_delayed_linear -v
# Only after the conductor marker exists and source is committed:
nice -n 10 "$PY" -m sim.fivebar.delayed_linear \
  --out /Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/fivebar-delay/run-01
```

- Limits: assumed upright fixed-length local linear systems; exact known matched torque reconstruction/noiseless states; 0.21 m upright only, excluded104deg nonlinear start. No nonlinear fivebar balance, noise/saturation robustness, hardware or ramp claim. Six-state nominal and delayed comparisons are different experiments. No retuning when a transferred gain is unstable.
- Artifact-attachment tool is unavailable; evidence remains at the explicit local path. Parent independently reproduces and merges only after green CI; worker does not merge.
