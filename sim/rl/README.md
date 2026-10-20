# Frozen direct-torque PPO versus delay-aware LQR

**SIMULATION / ASSUMED. Implementation and verification do not constitute a full
training result.** The read-only [protocol](protocol.json) fixes five independent
PPO seeds, exactly 150,000 steps each, one shared policy across four delays and
two scenarios, and final checkpoints only. Evaluation uses 800 PPO episode slots
and **160 unique LQR episodes**, paired by held-out noise seed 1000–1019.

The conductor authorization hash-locks the plant, protocol, archived baseline
result and four conditional LQR matrices. They are loaded directly, never
re-synthesized. `gain_schedule` is not called or duplicated. Both controllers see
only the same 15 measurements/causal estimates/history/delay values. Truth is
used for rewards and evaluation; neither actor nor critic receives privileged
state, time or future force. Four ideal sensor channels remain assumptions.

## Run from the repository root

Use Python 3.12 and the pinned [requirements](requirements.txt). Every output
path must be new and outside the repository; failed attempts remain intact.
The CLI sets all numerical-library thread limits to one before importing them.

```sh
PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
AUTH=/private/tmp/wbr-augmented-20261020/training-authorization.json
"$PY" .github/run_unittest.py sim/rl/tests
"$PY" -m sim.rl.run smoke --seed 0 --authorization "$AUTH" --out /tmp/wbr-ppo-smoke-NEW
"$PY" -m sim.rl.run verify --jobs 4 --authorization "$AUTH" --out /tmp/wbr-ppo-parity-NEW
# Commit the tested code first. Full execution rejects dirty simulation files.
"$PY" -m sim.rl.run run --train-jobs 5 --eval-jobs 6 --authorization "$AUTH" --out /tmp/wbr-ppo-full-NEW
```

`smoke` performs **one genuine 1,000-step WBR PPO rollout and optimizer update**
with the frozen hyperparameters, verifies parameter changes and checkpoint
reload, and labels its output ineligible for the full comparison. This is an
additional implementation check, not a change to the protocol's CartPole CI
smoke or a substitute for any training seed. `verify` runs eight full-duration
LQR adapter/original-evaluator pairs using noise seed 77 (not the held-out panel).
It compares raw truth, noise hashes, acceptance and 20 physical metrics.

`run` launches five independent single-environment training processes, waits for
every exit, then evaluates every slot. There are no budget, checkpoint-selection
or hyperparameter-search options. A failed seed does not cancel the others.
Missing final policies produce zero success, 10 s penalized recovery and null
physical metrics with explicit reasons. A complete valid experiment can exit 0
when policies fall; infrastructure/numerical/missing-policy failures exit 1 and
remain in the reports. No early failure is silently retrained.

To evaluate already completed full-budget seeds, use a new evaluation folder:

```sh
"$PY" -m sim.rl.run evaluate --training /tmp/wbr-ppo-full-EXISTING/training \
  --jobs 6 --authorization "$AUTH" --out /tmp/wbr-ppo-evaluation-NEW
```

This requires the same source hashes and verified final checkpoints. A standalone
full seed is `train --seed N --authorization ... --out .../seed-N`. Smoke
checkpoints can never pass the final-policy eligibility check.

## Evidence and interpretation

Each training directory contains source/config snapshots, authorization and gain
copies, provenance/versions, optimizer logs, progress, final status, a checkpoint
hash and a checksum manifest. `trace/` holds lossless compressed NPZ chunks with
per-control truth/measurement/noise before and after, normalized observation,
raw Gaussian action, clipped command, torque, push, reward, termination/truncation
and actual elapsed time. Every mechanical substep is retained: truth at its
start, exact duration, torque endpoints/applied mean, exact torque-squared
integrals, delayed command/source timestamp and force. `schema.json` names the
segment columns; offsets associate them with control ticks. Intentional NaNs
represent absent prehistory timestamps or unavailable raw-action slots only.
The SB3 callback captures unclipped samples before the next chunk flush, including
steps followed by automatic reset. A numerical exception preserves valid prior
chunks, the attempted-action/failure state and its traceback.

Evaluation retains every outcome and trajectory, then writes `outcomes.json`,
`policies.json` and `aggregate.json`. The latter includes all seed/condition
values, failure counts, conditional physical diagnostics with denominators, and
paired intervals. `training_failure_count` at the report root counts policy
seeds; per-panel/per-outcome counts count missing episode slots. RMSE and effort
use actual substep time; early failures also report elapsed duration. Saturation
means a bounded command at a cap, as frozen in this protocol. The older evaluator
counts only strict clipping, so its saturation metric is deliberately not used
as a parity reference. Recovery is null unless the full episode and held final
window exist. No change was made to the original evaluator or its CSV format.

The primary differences are computed at the **training-seed** level:

\[
d_s = \frac{1}{8}\sum_{c=1}^{8}\left(\frac{1}{20}\sum_{n=1}^{20}
 I_{\mathrm{PPO},s,c,n} - \frac{1}{20}\sum_{n=1}^{20}I_{\mathrm{LQR},c,n}\right),
\qquad \bar d \pm t_{0.975,4}\frac{s_d}{\sqrt{5}}.
\]

For example, differences \((-0.8,-0.6,-0.4,-0.2,0)\) have mean \(-0.4\),
sample SD \(\sqrt{0.1}\), and interval about \([-0.793,-0.007]\). Reusing the
same LQR panel does not create five LQR replicates. This interval describes
training-seed uncertainty conditional on this particular noise panel. Missing
physical data makes the all-slot continuous mean/interval undefined; available
observations are explicitly labeled diagnostics.

The frozen reward is
\(r_k=-0.002(x_{k+1}^{T}Qx_{k+1}+u_k^{T}Ru_k)-100I_{\mathrm{failure}}\),
where \(u_k\) is the bounded command before transport delay. At zero state with
command \((1,0)\) N m, the nonterminal reward is \(-0.0016\). Termination denotes
a fall/displacement violation; the 10 s time limit is truncation, so SB3 retains
the terminal observation for value bootstrapping.

PPO maximizes the clipped surrogate
\(\mathbb{E}[\min(r_t A_t,\operatorname{clip}(r_t,1-\epsilon,1+\epsilon)A_t)]\),
where this \(r_t\) is a probability ratio, not the reward. With positive advantage
2, ratio 1.3 and \(\epsilon=0.2\), the contribution is 2.4 rather than 2.6.
The implementation uses the fixed SB3 parameters from the protocol, including
separate 64–64 actor/critic networks and a Gaussian direct-torque policy.
Primary references: [PPO paper](https://arxiv.org/abs/1707.06347),
[SB3 2.3.2 PPO](https://stable-baselines3.readthedocs.io/en/v2.3.2/modules/ppo.html),
[Gymnasium Env API](https://gymnasium.farama.org/api/env/).

**Recommendation:** launch the committed command from the conductor's durable
session, retain all five slots and the full paired report, then request the
completed-milestone review. No RL superiority or hardware claim follows from
implementation smoke/parity checks.
