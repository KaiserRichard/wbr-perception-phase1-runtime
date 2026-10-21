# WBR-Control

Owner instructions, 21 October 2026. These override older logging and overnight
account rules for control work. Read `../ops/RESEARCH_RULES.md` before RL work.

- This chat is **WBR-Control**: simulation, LQR, RL and host control tooling.
  **WBR-Perception** owns camera work. Do not touch its branches, worktrees,
  files or accounts **d/h/j**, including availability pings.
- Use only the remaining owner-authorized accounts after checking idle state
  and quota. Treat g/k as a shared pool while their login matches. Keep each
  worker on its own task branch/worktree; never change shared checkouts.
- Before a new full training experiment, run one pilot seed for 10–20 minutes,
  targeting about 200k policy steps. Record the actual duration and steps.
  Print episode length, return and individual reward-term magnitudes.
  Plot episode length and return versus steps. Launch the full run only if
  learning clearly improves; otherwise diagnose the pilot first.
- Before that pilot, show that a tolerance-sized error costs a visible few
  percent of the alive reward. Check units and each relevant state term.
- Every RL result includes episode-length and return learning curves, plus
  final evaluation metrics. Survival and strict balance success are distinct.
- Keep evidence lean: config, source commit, seeds, final metrics and required
  curves. Reports fit one page. No mass hashing and no DECISIONS.md or
  DOCUMENTATION_LOG.md entries, including for documentation changes.
- Keep owner messages short, plain English, ending with exactly one
  `NEED FROM YOU: ...` or `NOTHING NEEDED: ...` line.
- Existing PPO v2 remains frozen through already-authorized seeds 3/4, as Claude
  explicitly requested. Do not restart it or retrofit the new pilot rule.
  Future experiments must pass the pilot rule. No v3 launch is implied here.
  Legacy v2 did not save episode-length/return histories: mark its missing
  curves unavailable; never substitute optimizer losses for learning returns.
- `sim/parity/student.py::gain_schedule` stays owner-only. No motor commands,
  STM32 flashing or hardware deployment without explicit owner authorization.
