# codex-b — frozen PPO implementation, 2026-10-20

- Scope: assigned worker on `chatgpt/20261020-ppo-training`; no other workers/accounts launched, no merge, hardware, protected learner, mechanics or shared-log edits. Conductor-owned `sim/rl/environment.py` scaffolding reviewed and incorporated. No model-switch facility is exposed to this worker; model selection is left to the conductor.
- Read AGENTS, CURRENT, USER_PROFILE, RESEARCH_RULES, Claude nominal review, full frozen protocol, authorization and runtime contract. Authorization and all named source/config/gain/baseline hashes match. Conditional archived matrices used for all delays; no synthesis or tuning. Protocol/requirements unchanged.
- Added Gym adapter, fixed-budget SB3 trainer, compressed raw trace recorder, evaluator, five-seed paired aggregate, provenance capture, CLI and behavioral tests. Numerical failures abort a seed and retain prior raw data; other seeds continue. Missing policies retain 160 zero-success/null-physical episode slots each. No best checkpoint, early stopping, residual control or truth/critic input.
- Real adapter: 1,000 steps, 1.767 s (566 steps/s; no optimizer/trace); imported and executed actual MuJoCo model.
- Genuine WBR optimizer smoke: `/private/tmp/wbr-augmented-20261020/ppo-smoke-b-01`, exit 0; exactly 1,000 env/recorded/SB3 steps, 10 PPO epochs, changed parameters, exact checkpoint reload; 6.215 s (161 steps/s including setup/trace). 8,000 mechanical substeps, 11 episodes; 13 unbounded Gaussian samples exceed Box and are retained separately. Checkpoint SHA-256 `f1503560c248024ddb2e7bd7d757c221b5f22c5fa72edb09805a6cb0fd35d800`. Explicitly ineligible as a full policy.
- Original-evaluator parity: `/private/tmp/wbr-augmented-20261020/ppo-parity-b-01`, exit 0; all 8 delay/scenario pairs PASS, each 5,000 steps per adapter and original; 20 metrics/checks/raw truth compared; max state difference `1.4432899320127035e-15`, identical noise hashes, all acceptance PASS. Verification noise seed77; not the held-out comparison. Original evaluator untouched; 120-case actuator experiment not repeated.
- Actual PPO evaluation path: `/private/tmp/wbr-augmented-20261020/ppo-evaluator-smoke-b-01`; smoke checkpoint falls after97 steps/0.194s, numerical failure count0; trace and explicit failed checks retained. Not a full-policy performance result.
- Tests: initial21/21 PASS; extended25/25 PASS (zero skips), logs `/private/tmp/wbr-augmented-20261020/ppo-tests-b-01.log` and `ppo-tests-b-02.log`. Covers independent RNG/noise mapping, shared observation/causality, clipping/odd delay, exact reward, terminal penalty, truncation bootstrap info, compact data, paired df4 analytic CI, missing seed semantics, refusal to overwrite, retained authorization failure and continuation after one subprocess failure.
- Commands published early in `/private/tmp/wbr-augmented-20261020/ppo-commands.md`; final worker report at `ppo-b-report.md` beside it. Full five-seed training/evaluation is **not launched** here: authorized durable-session conductor handoff. No full-result or superiority claim.
- Documentation/docstring changes: replaced `sim/rl/README.md` future-work text with actual CLI, evidence layout, assumptions, failure semantics, rendered reward/PPO/paired-CI equations, worked examples and primary PPO/SB3/Gym links; added focused module/class/function docstrings in new `sim/rl` Python files; this own session entry. Conductor owns shared DOCUMENTATION_LOG update.

Commands from this worktree (`PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python`, `AUTH=/private/tmp/wbr-augmented-20261020/training-authorization.json`):

```sh
"$PY" .github/run_unittest.py sim/rl/tests
"$PY" -m sim.rl.run smoke --seed 0 --authorization "$AUTH" --out /private/tmp/wbr-augmented-20261020/ppo-smoke-b-01
"$PY" -m sim.rl.run verify --authorization "$AUTH" --jobs 4 --out /private/tmp/wbr-augmented-20261020/ppo-parity-b-01
# Prepared command; not run by this worker. Use a NEW output path.
"$PY" -m sim.rl.run run --authorization "$AUTH" --train-jobs 5 --eval-jobs 6 --out /private/tmp/wbr-augmented-20261020/ppo-full-conductor-01
```

Next: conductor independently reruns the small checks, launches the frozen full command in a durable session, retains all final-policy/failure slots and secondary tables, then asks Claude for completed-milestone review. PR is for review only; worker must not merge.
