# Proposal: understand LQR, RL, PPO, then investigate residual control

**For Claude review — 21 October 2026.** Proposal only; no new training,
controller changes, or lesson illustrations have been produced.

## Goal and starting point

Build an English, mathematics-first WBR lesson pack. The owner knows RL notation
but needs refreshing and deeper LQR foundations; Roboticsbook Chapter 6 is partly
read and Chapter 7 unread. Skip generic AI introductions.

**Learning spine:** dynamics → Bellman optimality → LQR → learned value/policy
functions → policy gradient → GAE → PPO → residual control → fair experiments.
Each section explains intuition, assumptions, symbols/dimensions, derivation,
a worked example, common errors, and a short exercise with an answer.

## Proposed lesson sequence

| Part | Mathematics and practical outcome |
| --- | --- |
| 1. Recover the toolkit | Diagnostic refresher: expectations, gradients, quadratic forms, eigenvalues and Jacobians. State versus observation versus actuator history. |
| 2. Model our robot | Six-state planar surrogate, coordinates, paired torques, upright linearization and held-input discretization. Explain assumed parameters, ideal rolling and 500 Hz plant/LQR versus 100 Hz policy. |
| 3. Derive LQR carefully | Bellman recursion → quadratic value → optimal feedback → Riccati recursion → DARE. Explain CARE separately, Q/R scaling, stabilizability/detectability, poles and local validity. Hand-work a scalar example, then inspect WBR matrices. |
| 4. Connect control to RL | MDP, return, Bellman equations, V/Q/advantage, TD and bootstrapping. Delay/state augmentation and partial observability. Distinguish discounted RL from undiscounted LQR; negative cost alone does not equate their objectives. |
| 5. Derive PPO | Likelihood/log-derivative → REINFORCE → baseline → actor–critic → GAE → importance ratio → clipping. Hand-compute a rollout and both advantage signs. Explain Gaussian exploration, critic loss, normalization, epochs/transitions and termination/truncation. |
| 6. Understand residual PPO | Baseline + bounded correction + total saturation. Zero-mean initialization versus sampled noise, equilibrium bias and residual penalties. A cap is not a stability proof. Teach the actual clipped-action implementation. |
| 7. Build evidence | Reproduce LQR and saved-policy evaluation; propose a separate frozen v3 experiment. Interpret failures as well as improvements. |

**Priority:** Parts 2–5 are Must Know. CARE details, Lyapunov connections and
broader related work are Good to Know after the discrete-time derivation.
Full drone dynamics, DQN implementation, Isaac migration and hardware deployment
are Skip For Now. Chapter 7 is optional context, not a prerequisite.

## Sources and how they will be used

- **Reconnect with familiar material:** Roboticsbook [§3.5](https://www.roboticsbook.org/S35_vacuum_decision.html), [§3.6](https://www.roboticsbook.org/S36_vacuum_RL.html), and [§6.6](https://www.roboticsbook.org/S66_driving_DRL.html). [§7.5](https://www.roboticsbook.org/S75_drone_planning.html) is an optional trajectory-optimization bridge, not the LQR derivation source.
- **LQR derivation:** [Tedrake's MIT notes](https://underactuated.mit.edu/lqr.html).
- **RL refresher:** Hugging Face [Units 1, 4, 6 and 8](https://huggingface.co/learn/deep-rl-course/en/unit0/introduction). The course is in low maintenance; use theory and locally verified exercises, not leaderboard-dependent tasks.
- **Algorithm authority:** original [PPO](https://arxiv.org/abs/1707.06347) and [GAE](https://arxiv.org/abs/1506.02438) papers; distinguish their equations from [our pinned SB3 2.3.2](https://stable-baselines3.readthedocs.io/en/v2.3.2/modules/ppo.html) implementation.
- **Residual prior art:** [Johannink et al.](https://arxiv.org/abs/1812.03201) and [Silver et al.](https://arxiv.org/abs/1812.06298). Residual RL is established; a WBR-specific research gap remains unproven. A targeted survey of balancing, delay compensation and residual policies must precede any novelty claim.

## Obsidian delivery after review

One ZIP containing a main `WBR-LQR-RL-PPO.md` lesson with a table of contents,
YAML tags, local image embeds and sources; an `assets/` folder; worked exercises
and answers; and a small `START-HERE.md`. It must work after extraction into an
existing vault, offline except for external readings, without community plugins.
Use `$...$` / `$$...$$` MathJax, defined notation and relative asset paths.

Six figure groups: robot coordinates/torques; feedback/delay timing; quadratic
value/response; rollout/TD/GAE; both PPO clipping cases; residual signals/limits.
Generate monochrome mechanical illustrations and inspect geometry/torque directions.
Use deterministic tools for exact diagrams, equations and plots. Label illustrative
images; attribute reused figures and check rights. Never invent measured plots.

## Project application and acceptance

Read existing [controller code](../../../sim/lqr.py),
[augmented LQR](../../../sim/augmented_lqr.py),
[v2 runtime](../../../sim/rl/v2.py), and
[v2 configuration](../../../sim/rl/v2_config.json) at source commit
`28f1eb7b897b88fc1d8d152223a7155c09e6d849`. Reuse the
[existing guide](../../../docs/learning/LQR_RL_GUIDE.md), glossary and paper notes.
Do not solve the owner's protected gain-scheduling exercise.

**Candidate question, not a claimed gap:** can a residual improve recovery or
effort over delay-aware LQR while preserving strict settling, particularly under
held-out actuator/delay mismatch? Compare against the existing augmented LQR,
not only a nominal controller that ignores delay. Separate inference-rate effects
from algorithm effects; disclose the current 500/100 Hz scheduling difference.

Later experiments vary reward scale, zero-mean initialization and residual penalty
separately. Freeze cases, limits, observations and selection rules; separate tuning
from held-out testing and report all seeds/failures. Measure strict settling,
survival, recovery, RMSE, commanded/applied torque effort, saturation, transitions,
wall time, CPU/RAM and inference latency. Retain config/version/commit/raw evidence.

**Acceptance:** check derivations/numerical examples against sources, verify code
explanations, inspect extracted math/images in Obsidian, and run included examples
with documented commands/expected outputs/failure symptoms. Figures must be
reproducible. Avoid causal claims from bundled v1/v2 changes, stability guarantees
from clipping, or assumed success counts. Identify each result's exact test panel.

**Claude decision requested:** approve or amend the learning sequence, mathematical
depth, visual/ZIP format and proposed experimental question. This review approves
lesson production only; new training and hardware work require their own scope.

The owner's preferences are preserved in [the profile](../../USER_PROFILE.md) and
the portable [Obsidian lesson skill](../../skills/wbr-obsidian-lessons/SKILL.md).
Repository copies support another account; account memory does not transfer
automatically. Documentation-only changes can be rolled back by reverting this PR.
