# Completed milestone: first frozen PPO–LQR comparison

2026-10-20; conductor now codex-b following the owner's account switch.
**Conductor verified; final Claude review pending. SIMULATION / ASSUMED only.**

## Merged work and actual execution
- PR47 merged0c70a32: causal actuator delay/lag/IMU noise and conditional LQR.
- PR48 merged6cae11d: verified actuator/LQR milestone and final review.
- PR49 mergede821212: direct-torque PPO pipeline, Gym/API correction and CPU CI
  dependencies. Both test checks SUCCESS at exact head781d702.
- PR50 merged31a5d1a: verified parameter sources and float64 test-oracle repair,
  both CI checks SUCCESS at head934e846. Reward/runtime/physical settings unchanged.
- Read-only g audit receipt bbf4908 is included in this publication; conductor
  reran both diagnostic scripts in a new folder and matched both JSON results exactly.

Conductor command (not a worker-only claim):

```sh
/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python -m sim.rl.run run --authorization /private/tmp/wbr-augmented-20261020/training-authorization.json --train-jobs 5 --eval-jobs 6 --out /private/tmp/wbr-augmented-20261020/ppo-full-conductor-01
```

Exit0, COMPLETE. Five independent final policies completed exactly150000 steps
and1500 PPO epochs each. Evaluation produced960 outcomes:800PPO plus160unique
LQR episodes. The same held-out noise panel and physical/sensor/control limits
were used; no residual controller, retuning or checkpoint/seed selection.

| Outcome | Delay-aware LQR | PPO final policies |
| --- | ---: | ---: |
| Success |160/160 |0/800 |
| Falls |0 |680 |
| Displacement exits |0 |120 |
| Numerical failures |0 |0 |
| Training failures |— |0/5 |

All five seed success rates were0. PPO-minus-LQR success differences were all−1;
mean−1, sample SD0, prescribed95%t interval `[−1,−1]`, df4. This degenerate
binary endpoint interval is conditional on these seeds/panel and does not prove
universal certainty or that all RL fails. Only20/400 PPO push episodes received
the complete pulse; the others failed before it ended. Early-ending effort
cannot be presented as an efficiency advantage.

## Independent checks and evidence
- Conductor27/27 expanded RL tests PASS, zero skips, plus a real1000-step WBR
  optimizer/update/reload smoke. Smokes are excluded from the five final seeds.
- Conductor verified6680 artifact hashes,750000 total training steps, five
  distinct checkpoint digests/reloads, all960 unique episode identities and
  every800 PPO noise prefix against its LQR pair. Independently recomputed CI
  and raw RMSE/effort/impulse/held-window metrics for four selected cases.
- Stable archive:`~/wbr-evidence-archive/sim-ppo-vs-lqr-20261020-01`;
  `SHA256.json` and `conductor/ppo-independent-audit-01.json` are the receipts.
  Full physical metrics/48panels/secondary intervals:`evaluation/aggregate.json`.
- Aggregate SHA256:`fcd5b38fab96d65c8f16a92ce23c5b4ecb94a43c792b3f1428144fddfdd530bf`.
- Training source608222b; evaluation receipt781d702 differs only in worklogs,
  with equal runtime/config/protocol hashes. All source snapshots/checkpoints,
  raw substeps/commands/rewards/failures are outside git. Existing untracked
  host-test binaries were recorded and untouched.
- Main result note:[sim/rl/RESULTS_2026-10-20.md](../../../sim/rl/RESULTS_2026-10-20.md).
  Learning guide and parameter-source table explain assumptions and definitions.

- Independent codex-g audit: no actionable defect in inspected feedback/action/
  reward/episode/budget paths;750000 recorded transitions, finite optimizer
  states and21 deterministic action probes checked. Only10/1379 started training
  push episodes experienced force (nine full pulses, one partial). This is
  measured; its causal role in poor learning is not established.

## Interpretation and recommendation
The frozen PPO recipe did not solve this assumed task within its declared
budget. The execution completed; changing a threshold, dropping failures or
calling the optimizer smoke a learned controller would misrepresent it.

**Recommendation:** retain the matched LQR and this negative comparison as the
reference. Review learning objective, horizon/discount, exploration and budget
before one explicitly predeclared next experiment; no automatic retraining or
evaluation-driven tuning has been performed. No ablation identifies the failure
cause. No physical deployment, full-five-bar model, source-gain parity or gate
promotion is implied. Camera/Pi work remains deferred until equipment returns.

## Claude final review

Reviewed 2026-10-20 on main 819659c. I read `sim/rl/protocol.json`,
`environment.py`, `training.py` and the results note. I did not re-run training.

**Verdict: the run is valid, but the comparison tells us almost nothing about RL.**
"Delay-aware LQR 160/160, this PPO recipe 0/800" is a correct statement. It is
not evidence that RL cannot balance this robot.

What the results show:
- **PPO never learned to survive.** 1379 training episodes fit into 150k steps,
  an average of about 110 steps (0.22 s) each, which is roughly how long the
  open-loop robot takes to fall (0.18 s). In total the policy saw about 300 s of
  balancing time.
- **The final policies fall within 0.7-2.8 s** (mean duration per seed), on
  every condition.

Why this recipe was set up to fail (inferred from the code, not ablated):
1. **Budget.** 150k steps of 2 ms control is about 5 minutes of experience.
   PPO balancing tasks usually need millions of steps.
2. **No survival reward.** The reward is cost-only plus -100 on a fall. Early on
   every episode falls, so every return looks alike and there is little
   gradient toward "stay up longer".
3. **Control rate and horizon.** The policy acts every 2 ms with gamma 0.9995.
   Credit assignment over thousands of steps is hard for PPO.
4. **Training covers only two fixed starts.** Every training episode begins from
   the same +8/-6 deg tilt. There is no random initial state and no random push,
   so the policy rarely sees states near upright.

Next bounded experiment (PPO v2; declare it once, then run):
- **Reward:** r = 1 - (the same quadratic cost, scaled so a balanced step is
  about 0.9). Keep a small fall penalty.
- **Rate:** the policy acts at 100 Hz (each action held for 5 plant ticks),
  with gamma 0.99. The plant, delay, lag and noise stay unchanged.
- **Training randomization:** initial leg and body angles uniform in +/-10 deg,
  and random 0-10 N pushes at random times. The evaluation panel stays exactly
  as it is now.
- **Scale:** 8 parallel envs, VecNormalize on observations, 3M steps per seed.
  Start with 3 seeds; if any seed balances, run all 5 on the same held-out panel.
- **Second arm, the more useful research question:** residual PPO, where the
  action is the LQR torque plus a bounded correction. It answers "can RL
  improve LQR under delay?"

Process note: this milestone spent most of its effort on provenance (6680
artifact hashes, long documentation logs). Per AGENTS.md, keep the next one
lean: run it, keep raw results outside git, and write a short results note.
