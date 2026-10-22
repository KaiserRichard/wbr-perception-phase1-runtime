# V3 research: a bounded residual pilot, not another overnight run

**Recommendation for Claude:** review the candidate below before implementation;
no pilot/full training is authorized or running. Reward implementation remains the
owner's exercise. k/i (Plus, Astra Ultra) researched independently; b (Free, Luna)
audited arithmetic. Conductor corrected two b errors and reran the corrected audit.

**Evidence.** Frozen source `f1b5ee7`; checked source `128c8bd`, with unchanged
`sim/rl/{v2.py,v2_config.json,protocol.json}`. Direct strict successes per seed:
[39,20,0,0,0]/160. Residual: 0/480 strict, 480/480 survived; leg-rate violations
480/480. Cause remains unproven; legacy return/length curves are unavailable.

**Why scale 2 alone is insufficient.** For equal-length surviving trajectories,
$G=S_T-s\sum_k\gamma^k C_k$: changing $s$ preserves their ranking and the
precision/effort trade-off, though optimization and termination incentives change.
Here $C_k$ is mean post-tick $e^TQe+u^TRu$ over up to five completed ticks;
$u$ is clipped total issued torque. At both angles ±10°, $1-2C=-23.3694$
before torque; at simultaneous [2,4] Nm caps it is −48.9694. These are
instantaneous arithmetic, not measured rollouts or evidence of intentional falling.

**Candidate hypothesis:** keep Q/R, plant, observations, gamma0.99 and timing;
replace only the reward objective with

$$r_k=\frac{1}{1+\beta C_k}-I_{\mathrm{physical}},\qquad
\beta=\frac{0.03}{0.97\min_i(Q_{ii}t_i^2)}=4.29553.$$

$t_i$ are unchanged evaluation tolerances. Isolated tolerance penalties (% alive):

| Error | V2 | Candidate |
|---|---:|---:|
| Position | 0.160 | 6.43 |
| Each angle | 0.609 | 20.74 |
| Translation rate | 0.072 | 3.00 |
| Each angular rate | 0.200 | 7.91 |

Nonterminal rewards stay positive; no new residual penalty. This changes
trajectory preferences, **not policy-invariant shaping**. Counterexamples:
large-cost recovery gets a weak reward slope; brief rate spikes can still fail
strict acceptance. It does not guarantee balance or that every survivor outranks
every later fall. The 3% design target is a hypothesis, not an optimum.

**Proposed bounded experiment, after review.** Zero only actor-output mean
weights/bias; retain exploration SD $e^{-1}$ (initial residual SD 0.147/0.294 Nm).
First verify constructed-policy/save-reload zero-output parity with LQR; literal
zero-action tests do not check actor/normalization. Preserve 500 Hz LQR,
100 Hz corrections, caps, delay/lag/noise and observation-only VecNormalize.
Pilot seed42; 8 environments; target200k aggregate transitions, not per environment.
Stop at the first 2k-transition update meeting both200k and10min, or reaching20min;
report actual duration/transitions and boundary overrun. Never stop on a good score.

Use fixed development noise2000/2001 × four delays × balance/push (16 cases),
snapshots0/100k/end with frozen evaluation statistics. Record raw episode
length/return and decomposed reward terms via VecMonitor before VecNormalize;
verify their sum. Proposed screen: last50k return improves over first50k without
shorter episodes; final survival16/16, no strict-pass regression, and
$E_{end}\le0.9E_{100k}$ and $E_{end}\le E_0$, where
$E=\operatorname{mean}_{cases}\max_{i,t\in[9,10]}|e_i(t)|/t_i$.
Missing/partial cases fail; these are engineering screens, not significance tests.
If100k is not reached, evidence is insufficient. No checkpoint/seed selection.
Initialization plus reward tests feasibility; causal attribution needs a separately
approved matched control changing reward only.

**Limits / verification.** LQR160/160 leaves no strict-success headroom; no claim
RL will beat it. Preserve held-out1000–1019 and the primary endpoint; any later
full arm needs at least five seeds and its own successful pilot. Research used
code reads, primary sources and stdlib arithmetic only: independent audit PASS;
no training/rollouts/config changes. Detailed worker drafts remain on isolated
research branches; this is the canonical review. Two understanding checks for the
owner: why does scaling preserve survivor ranking; why is zero mean not zero action?

Sources: [residual initialization, §IV-A](https://arxiv.org/html/1812.06298#S4.SS1)
(manipulation/DDPG, no WBR/PPO guarantee);
[SB3 evaluation/wrappers](https://stable-baselines3.readthedocs.io/en/v2.3.2/guide/rl_tips.html);
[Gaussian SD](https://stable-baselines3.readthedocs.io/en/v2.3.2/_modules/stable_baselines3/common/distributions.html#DiagGaussianDistribution).
