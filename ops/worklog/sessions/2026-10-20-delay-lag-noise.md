# Actuator/noise → RL comparison — 2026-10-20

- Conductor f, branch chatgpt/20261020-delay-lag-noise from origin/main417c1e2. Prior generated host-test binaries remain untracked/unstaged, untouched.
- Read Claude's approved review from PR44; recorded D22. Owner wants short LQR/RL reading now and camera lab tomorrow; D23.
- Existing mechanics: reduced six-state MuJoCo, 2ms sample, instant torques/ideal observations. Add a reusable actuator/measurement layer; freeze base config/protocol/K before conditional state-augmented synthesis. Preserve failed cases and rollback through additive feature commits, no resets/deletion.
- i/AstraUltra dispatched in isolated sim-lqr-push worktree/actuator-noise branch after idle process/session check. Goal/config/allowedfiles/donecommand in /private/tmp/wbr-augmented-20261020/actuator-brief.txt; raw actuator-events.log. Starts with nominal reproduction before edits.
- g/SolHigh briefly dispatched to write learning guide; stopped cleanly when owner required a concise document, before edits. Conductor wrote docs/learning/LQR_RL_GUIDE.md directly (~50lines); AGENTS records concise-note preference. Each document change recorded here and DOC11.
- k rechecked: terminal30573 open in Desktop/CN, no descendants, latest session task_complete07:05:22Z. Open terminal alone was not evidence of active work. Separate k task may be assigned after this idle check; f never launched as worker.
- RL must use same augmented plant/observations/rate/limits/pushes/initial states; no training until actuator/LQR checks. At least5seeds and held-out paired evaluation; keep failures and uncertainty. No learner gain edits, Pi/STM32/motor actions.
- Learning guide links actual plant/config/synthesis/README and primary SciPy/MuJoCo/Gymnasium/PPO docs. No new runtime result is claimed there.
- Validation: guide length/relative links/whitespace checked before publication; model work in progress, RL not run yet.
