---
title: "Pack 3 — residual PPO and a delay-mismatch experiment"
tags: [wbr, residual-rl, ppo, lqr, experiments, delay]
created: 2026-10-21
previous: "[[Pack 2 - RL to PPO]]"
---

# Residual PPO — combine a controller with a learned correction

This pack uses [[Pack 1 - LQR]] and [[Pack 2 - RL to PPO]]. It explains the
composition, plots **saved simulation runs**, and defines a candidate experiment.
It does not train a model or claim a research gap.

## Reading map

- [[#1. Define the command precisely|Command definition]]
- [[#2. Why a small residual can cause drift|Drift and stability]]
- [[#3. Read a saved comparison honestly|Saved-run plot]]
- [[#4. Candidate study: unseen delay mismatch|Delay-mismatch study]]
- [[#5. Literature boundary and self-check|Literature and self-check]]

## 1. Define the command precisely

### Put the correction back onto the mechanism

![Aggregate motor actions, reaction torques and push](assets/04_motor_reactions_and_push.png)

*Owner-supplied Plate 04: the assumed planar surrogate, not the full CAD robot.
The printed generalized-force $Q$ is $\mathcal Q$ here, not the LQR cost matrix.*

Read the **wheel** panel first: adding wheel torque also reacts on the equivalent
leg. Read the **hip** panel next: its torque helps rotate the body but applies an
opposite torque to the leg. A learned correction has the same reaction effects
as the baseline command. It is not an independent “stabilizing force” acting
only on body pitch.

Before total-command saturation, its generalized-force contribution is

$$
\mathcal Q_{\mathrm{res}}=G\Delta u=
\begin{bmatrix}
\Delta\tau_w/r\\-\Delta\tau_w-\Delta\tau_h\\\Delta\tau_h
\end{bmatrix}.
$$

For a proposed $\Delta u=[0.1,-0.2]^T$ N m and $r=0.0603$ m, this is
approximately $[1.6584\,\mathrm N,\ 0.1\,\mathrm{N\,m},\ -0.2\,\mathrm{N\,m}]^T$.
The three entries belong to the translation, leg-pitch and body-pitch equations;
they are not three actuator commands. At saturation, use the **effective command
increment** instead of the proposed $\Delta u$ when interpreting its effect.

The right-hand panel supplies the external push, a different input channel:
$F=6$ N at the body COM from 3.00 to 3.15 s, world $+x$, no separate applied
couple. A fair comparison changes the controller, keeping that disturbance fixed.



Let $u_b$ be the delay-aware LQR command using the causal controller state $z$.
Our existing v2 residual implementation is

$$
\begin{aligned}
u_b(z_k)&=-K_dz_k,\\
\Delta u_j&=c\odot\operatorname{clip}(a_j,-1,1),\\
u_k&=\operatorname{clip}(u_b(z_k)+\Delta u_j,-u_{\max},u_{\max}),
\end{aligned}
$$

where $c=0.2u_{\max}=[0.4,0.8]^T\,\mathrm{N\,m}$, $\odot$ denotes
elementwise multiplication, and the policy command indexed by $j$ is held for
five 500 Hz plant ticks. LQR feedback is recomputed at every tick. The outer
clip acts on the **sum**. Realized motor torque then depends on delay and lag.

![Residual command signal path](assets/residual-signal-path.svg)

*Calculated layout of the current signal schedule. The mechanical meaning of
the two channels is given by Plate 04 above.*

The baseline makes a useful initial policy available. Learning can focus on
corrections, but it may also damage a good controller. A20% residual cap limits
the correction, not the closed-loop state or the total input to 20%.

> [!example] Saturation changes the effective correction
> If wheel LQR asks for 1.9 Nm and RL adds 0.4 Nm, the 2 Nm total cap leaves only 0.1 Nm
> extra applied to the issued command. The policy proposed 0.4 Nm, but its effect
> on the saturated command was 0.1 Nm. Log proposed residual, baseline command,
> total requested/clipped command and realized torque separately in a future run.

### Follow issued command → delayed command → realized torque

![Transport, actuator and measurement paths](assets/08_delay_lag_and_noise.png)

*Owner-supplied Plate 08, with two qualifications: its six displayed mechanical
channels are only part of the current 15-value policy observation (causal torque
estimates, command history and delay are also present). Its “evaluation metrics
only” label must also include training reward and termination; simulator truth
is excluded from both actor and critic inputs.*

Follow the arrows in order. Total saturation limits the command **before** it
enters the transport queue. The queue preserves command arrival times. The motor
then follows the arrived command with first-order lag, and the mechanical model
converts those realized torques into motion. Body-angle/rate noise changes what
the controller believes happened; it does not directly change the physical
angle. Other mechanical state channels are ideal proxies in this model.

At a 2 ms LQR tick, three different quantities can coexist: the new total
command, an older command currently arriving, and a motor torque still catching
up. The policy's 10 ms hold is a fourth timing mechanism. None may silently be
substituted for another. With a 3 ms transport delay, a command issued at 0 ms
arrives at 3 ms even though LQR updates at 0, 2 and 4 ms.

> [!question] Explain the two paths without looking
> Which arrows carry actual actuator input, and which carry information? Why
> does a residual still affect future motion after its current output becomes zero?

> [!success]- Answer
> The forward clipped-command/queue/motor path drives the plant. The returning
> sensor/estimate path informs controllers. Commands may remain queued and motor
> torque may still be nonzero because of lag, even after the current addition is zero.

## 2. Why a small residual can cause drift

For intuition, consider a linear sampled plant and constant correction $d$:

$$
s_{k+1}=(A-BK)s_k+Bd.
$$

If $A-BK$ is stable, the new equilibrium is

$$
s_\infty=(I-A+BK)^{-1}Bd.
$$

It need not be zero. A controller can remain upright while sitting off-target
or moving within an insufficiently penalized direction. This calculation is an
explanation of a possible mechanism, not a diagnosis of our trained network.
For an actual drifting trajectory, distinguish constant bias, noisy feedback,
periodic corrections, saturation and estimator error using logs.

With ideal unsaturated LQR value $V=s^TPs$, define $A_{cl}=A-BK$.
Adding a residual changes its one-step decrement by

$$
\Delta V=-s^T(Q+K^TRK)s
+2s^TA_{cl}^TPB\Delta u
+\Delta u^TB^TPB\Delta u.
$$

The extra terms can be positive. Near zero, the baseline decrease is small;
a bounded nonzero correction can increase value. This directly explains why
**bounded residual does not imply stability or hardware safety**. With delay,
the appropriate analysis needs the augmented model as well.

### Three learning-design hypotheses

1. **Zero mean-output initialization:** initialize the actor's final mean layer
   to zero. Deterministic inference starts with $\Delta u=0$, but stochastic
   training still has Gaussian exploration. It is not a guarantee of a pass count.
2. **Correction penalty:** discourage unnecessary additions, for example
   $r\leftarrow r-\beta\sum_i(\Delta u_i/c_i)^2$. Define whether this uses the
   proposed capped residual or its effective post-saturation contribution.
3. **Precision-aware cost:** make tolerance-sized state errors matter relative
   to the alive reward. Test separately before claiming which change helped.

These are hypotheses for a later version, not changes to the frozen v2 run.

## 3. Read a saved comparison honestly

The completed v2 campaign gives **0/480 strict settling and 480/480 survival**
for three residual seeds, versus the reused LQR panel's 160/160 strict passes.
Direct PPO had 59/800 strict and 760/800 survival across five seeds. All eight
PPO seeds used exactly 3M total transitions each. This lesson's single selected
trace below illustrates one case; it does not replace those full campaign counts.
Source: `sim/rl/RESULTS_V2_2026-10-20.md` at repository snapshot
`4f49447f6b494ad3dc7aaa68e5f52256f03bd7fc` (frozen training source `f1b5ee7`).
Episode-length/return learning curves were not saved in the legacy campaign and
remain unavailable; no curve is inferred from a finished torque trace.



![Archived LQR and residual issued torque](assets/saved-torque.svg)

The plot uses a preselected case: 5 ms delay, push scenario, noise seed 1000, and
residual training seed 0. It was chosen as the first noise seed in the highest
existing delay condition, not as a best-result seed. The baseline and residual
use matching initial conditions, noise samples and 6 N push for 0.15 s at 3 s.
Both records cover 10 s. LQR is the prior 500 Hz delay-aware baseline; the residual
includes a 100 Hz learned addition. That scheduling difference must be disclosed.

The plotted signals are **total clipped issued torques** from two separate
closed-loop trajectories. Their difference is not the learned $\Delta u$,
because $u_b(z)$ differs as the trajectories diverge. The saved compact residual
record does not directly log the additive channel; we do not invent it.
The plot shows every fifth tick for readability, without anti-alias filtering.
It can miss peaks/high-frequency behaviour. Metrics below come from the original
full-resolution records, not integration of the thinned plot.

| This single case | Strict settling | Survived | Wheel command effort | Hip command effort |
| --- | --- | --- | ---: | ---: |
| Delay-aware LQR | Pass | Yes | 0.032303 | 0.045308 |
| LQR + residual PPO seed 0 | Fail | Yes | 0.091412 | 0.206968 |

Effort units are $\mathrm{N^2m^2s}$, the integral of squared issued torque;
this is **not electrical energy**. Applied torque effort is a separate metric
because the actuator filters commands. The residual case fails the held final
settling window and recovery deadline. That does not establish the cause, nor
does one case estimate performance over all training seeds.

### Run the one small script

Use a separate environment with NumPy1.26.4 and Matplotlib3.10.3:

```sh
python plot_saved_torque.py --out assets/saved-torque.svg
```

It also regenerates `assets/residual-signal-path.svg`. Compare the console with
[expected-output.txt](expected-output.txt). It checks finite values, monotonic
time and torque caps; it reads only the included small CSV/JSON. No MuJoCo,
network, model checkpoint or GPU is used. Missing files, NaNs or failed checks
must be diagnosed rather than replacing data with synthetic lines.

The CSV is a thinned teaching extract; source commits, logical archive paths,
selection rule and copied full-resolution metrics are in [evidence.json](data/evidence.json).
This is an **assumed simulation**, not measured robot hardware data.

## 4. Candidate study: unseen delay mismatch

**Question:** does residual PPO improve recovery/effort over delay-aware LQR
when trained with 2–5 ms delay and tested with 6–10 ms delay, while preserving strict
settling? This is a proposed experiment, not an established contribution.

### Define what is mismatched

Transport delay means when a submitted command arrives. Motor time constant
means how quickly realized torque approaches the arrived command. They are
different mechanisms; vary transport delay first and freeze lag/noise/plant.
Training/test delays here are **not** the100Hz policy period.

The controller's delay knowledge is a required part of the question. A concrete
primary design for review is:

| Item | Proposed rule |
| --- | --- |
| Training delay | Uniformly choose2,3,4,5ms per episode; known matching controller delay/model in training |
| Held-out physical delay |6,7,8,9,10ms; never use these outcomes for reward tuning or seed selection |
| Controller's test delay hint | Freeze at5ms for both methods: actual delay is larger than their believed value |
| LQR comparator | Frozen existing5ms augmented K/estimator, without retuning for the hidden test delay |
| Residual comparator | Same baseline/estimator plus learned correction, same observations and total caps |
| Additional reference | Separately labelled oracle delay-aware controller if later authorized; never silently replace the primary baseline |

This tests stale delay knowledge. Giving exact6–10ms hints to the residual while
holding LQR's hint at5ms would be unfair. Re-synthesizing LQR at every true delay
would instead ask whether learning beats a model-aware oracle. Both questions
may be useful, but they require separate named comparisons.

### Integration work required before execution

Current v2 validates four known delays and has only three command-history pairs.
It is not a ready-made6–10ms benchmark. A separately reviewed v3 environment
must represent exact arrivals through10ms, define observation history and reset
behaviour, and distinguish hidden physical delay from the controller's hint.
For the primary stale-hint comparison, keep both controllers' belief-state
representation identical; acknowledge it is not a full true Markov state under
mismatch. Do not quietly give RL extra past commands or privileged torque truth.
If longer observation history is studied, declare it as another arm and grant
the same information to baselines. No owner-protected gain-scheduling solution
is part of this work.

### Stage the work without losing evidence

1. **Specification and baseline:** freeze scenarios, tolerance definitions,
   delay knowledge, gain selection, observation encoding, rates and endpoints.
   Check delay arrivals numerically and reproduce original in-range LQR cases.
2. **Reward arithmetic:** at each relevant tolerance, show a visible few-percent
   cost relative to the alive reward. Check units and total versus residual effort.
3. **Required pilot:** one 10–20 min CPU pilot, about 200k policy steps. Record actual
   duration/steps, return, episode length and individual reward magnitudes; plot
   return/episode length against steps. Proceed to a full run only if learning
   clearly improves, following current control rules. Otherwise diagnose first.
4. **Ablations on training/validation only:** zero mean-output initialization,
   residual penalty and precision scale one at a time, then their combination.
   Fix the final recipe and budget before opening held-out6–10ms results.
5. **Final evaluation:** use all declared training seeds (for example five),
   paired held-out noise/push cases, final checkpoints, frozen normalization and
   deterministic actions. Report missing/failed seeds and all cases.

### Measure what answers the question

- **Primary:** strict settling success at each held-out delay and across delays;
  do not replace it with survival. Use the same tolerances/deadlines across arms.
- **Secondary:** recovery time with failures retained (or explicitly censored),
  state RMSE, displacement/tilt maxima, commanded/applied squared-torque effort,
  saturation, physical failures and numerical failures.
- **Learning/compute:** return and episode-length curves, reward components,
  transitions, wall time, CPU/RAM and inference latency. Never compare a short
  failed episode's low effort directly with a successful full 10 s recovery.
- **Uncertainty:** aggregate across independent training seeds; do not treat
  repeated baseline episodes as new training replicates. Show per-delay/seed
  values and paired differences. If both always pass, compare recovery/effort
  without inventing a success-rate improvement.
- **Reproducibility:** goal/hypothesis, source commit, configuration, versions,
  hardware, commands, selection rules, lean raw metrics/required curves and paths.
  No mass hashing or large raw logging by default.

Keep evaluation probes/tuning separate from final held-out tests. A negative
result can show that delay-aware LQR remains the stronger method under this
recipe; it is not evidence that all RL fails or that the code never learned.

## 5. Literature boundary and self-check

The general residual idea already appears in [Johannink et al.,2018](https://arxiv.org/abs/1812.03201)
and [Silver et al.,2018](https://arxiv.org/abs/1812.06298). These original works
combine existing policies/controllers with learned additions, including settings
with imperfect modelling. They do not establish novelty for our delay benchmark.

A targeted literature check must still compare wheeled-biped balancing,
delay-aware LQR, residual policies, robust/delay-mismatch control and evaluation
protocols. An IEEE search also located a wheel-legged residual-policy paper
(document11202537), but its full text was inaccessible here; it is an unread lead,
not evidence for a technical claim. No research gap is asserted in this pack.

> [!question] Check your understanding
> If two total-torque traces differ by0.1Nm, is that the learned residual? If
> a policy is trained on2–5ms and tested on8ms but receives the exact8ms hint,
> are you testing the same mismatch as a controller believing5ms? Can a capped
> residual invalidate the baseline value-function decrease near equilibrium?

> [!success]- Answers
> No: the trajectories and baseline terms differ. No: exact delay knowledge is
> another information regime. Yes: the cross and quadratic residual terms can
> dominate the small nominal decrease.

**Next practical step:** review the experiment specification and the current
environment's delay assumptions before implementing a v3 pilot. This lesson
provides understanding and saved-data plots; no new training has been started.

Read [Figure prompts](FIGURE_REVIEW_AND_PROMPTS.md) for a replacement multirate
mechanical plate and causal actor–critic loop, each with its intended filename.
