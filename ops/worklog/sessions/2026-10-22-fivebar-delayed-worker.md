# Fivebar delayed local linear worker — 2026-10-22

- Owner-authorized codex-i; branch `chatgpt/20261022-fivebar-delayed-linear`, worktree `/Users/quockaiser/.codex/worktrees/fivebar-linear-review/wbr-lab-ops`. Read root/sim AGENTS, RESEARCH_RULES, CURRENT/profile and appended Claude PR110 control review.
- Scope: new `sim/fivebar/delayed_linear.py`, its focused test module, appended README delay section and this session only. Existing runtime/model/linearize/compare/LQR/configs and owner-only gain function unchanged. No agents/accounts/chats/Pi/SSH/hardware/training/deletion/force-push/merge.
- Initial scalar lift executed before tests; all four exact transport cases produced expected history ordering and zero current-input physical effect. No failed calculation or implementation fix so far.
- Implementation commit `b51237f0f2b9fb349699cd792982bf0917b6e488`; draft [PR114](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/114). Early handoff written before documentation completion: `/private/tmp/wbr-control-margins-20261022/i-ready.md`; exact PR body in `i-pr-body.md` beside it.
- **11 focused tests PASS**, 0.724 s suite; log `/Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/fivebar-delay/tests-01.log`. Analytical integrator/lag and coupled scalar solutions, fractional arrivals/history shift, zero equilibrium/channel independence, feedback sign/unstable retention, saved eigenpairs, production/output guards and one bounded actual reduced runtime check.
- Local reduced L=.16/delay3ms finite-difference check: A Frobenius discrepancy from exact lift decreases `4.41725748e-7→1.10438553e-7` for `0.25→0.125 ms` mechanics; no false equivalence threshold. Fresh augmented DARE has unchanged Q/R and expected 12-state history order. No nonlinear trajectory run.
- Conductor marker received, verified UTC `2026-10-22T02:09:01.391016+00:00`. Per `conductor-feedback-i.md`, removed machine-specific marker/clean-tree gates and their guard test from reusable code; retained source-status recording. External production supervisor will preserve marker content. Remaining 10 meaningful tests retained. No numerical implementation change.
- **Production completed** from clean committed source `8ccd6268667c6942446a635882f0e7b3938492de`, exit0, **8.8891174 s** external process time, **6.4350115 s** calculation before serialization. Full 16-case evidence in `/Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/fivebar-delay/run-01/{comparison.json,metrics.csv,report.md,execution.json}`; sibling `run-01.log` and `run-01-supervisor.json` preserve external command, marker/content, start/end times and actual child exit. Deterministic, no random seeds. Python3.12.13/numpy1.26.4/scipy1.15.3/MuJoCo3.3.7.
- Final **10 focused tests PASS**, suite0.295s/process2.142800s at the production source; `tests-02.log`/`tests-02-supervisor.json` beside run-01. No failed production/test attempt. Earlier guard-test removal was conductor-requested orchestration cleanup, not a numerical fix.
- Fresh continuous sources retained for all four lengths, 3 projection × 3 paired state/input refinements each (36 sources); selected epsilons `1e-6` each. Each of 16 rows uses fresh actual-runtime K, unchanged Q/R and identical K on both exact lifts; all 144 lifted refinement pairs are stable. Maximum fivebar rho refinement spread `3.91e-7`.
- **16/16 local cases STABLE**; fivebar rho `0.997442684–0.997688181`, radial margin `0.002311819–0.002557316`, tau `0.781070–0.864119 s`. All actual-runtime and exact reduced comparisons also stable. Exact map dimensions10/12/12/14 and all sorted eigenpairs retained. Output inspection confirms16unique rows, 9refinements/row, same saved K on all3maps, and eigenpair residual maximum `1.11855e-14`.
- Actual reduced RK4/mean-torque versus exact continuous lift: max raw entry difference A=`4.29576e-7`, B=`0` (new input changes history only); max rho discrepancy `8.85136e-10`. At L=.12/delay3ms, A Frobenius error `6.69939e-7→1.67499e-7` for0.25→0.125ms (ratio.250022); L=.21/delay5ms `3.15002e-7→7.87547e-8` (ratio.250013). Same K retained, no false parity threshold or asymptotic-order claim.
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
