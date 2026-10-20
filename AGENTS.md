# Agent guide (ChatGPT Work, Codex, Claude)

The main working agent for this repository is **ChatGPT Work**. Claude is an
occasional reviewer. Everything an agent learns or decides goes into files in
this repository, so any later session (ChatGPT or Claude) can pick up cold.

Always reply in English unless the user explicitly asks for Vietnamese.

## Read at the start of every session, in this order

1. `ops/worklog/CURRENT.md` — live state: what is in progress, blockers, next step.
2. The last 15 entries of `ops/worklog/DECISIONS.md`.
3. `ops/RESEARCH_RULES.md` — the research standard every claim must meet, and
   `ops/USER_PROFILE.md` — who the owner is and how they want to work.
4. `docs/PROJECT_STATE.md` and `docs/NEXT_GATE.md` — canonical project state
   (owner-promoted; agents propose changes, they do not promote gates).
5. Then the mode file below.

The `wbr-session-start` skill does this for you.

## Modes

| Mode | When | Rules | Skills |
|---|---|---|---|
| Lab | Anything touching the Pi, camera, power, storage or evidence | `ops/lab-assistant/INSTRUCTIONS.md` | `ops/lab-assistant/skills/` |
| Build / research | Code, analysis, docs, experiment design, literature | `ops/RESEARCH_RULES.md` + "Git workflow" below | `ops/skills/` |
| Simulation / control | MuJoCo models, RL training, LQR baseline comparison | `ops/RESEARCH_RULES.md` "Simulation and learned control" + "Git workflow" | `ops/skills/` |

## Files you write (see `ops/worklog/README.md`)

- `ops/worklog/CURRENT.md` — overwrite to reflect the state at session end.
- `ops/worklog/DECISIONS.md` — append one entry per decision. Never rewrite old entries.
- `ops/worklog/sessions/YYYY-MM-DD-<topic>.md` — one log per session.
- `ops/worklog/reviews/YYYY-MM-DD-<topic>.md` — a question for Claude, when needed.

The `wbr-session-end` skill writes these and commits them.

## Git workflow

- Work in the worktree `~/Desktop/Research/wbr-lab-ops`. Never touch the branch of
  `~/Desktop/Research/wbr-perception-phase1-runtime` (shared checkout).
- Start each task on a fresh branch: `git fetch origin && git switch -c chatgpt/<YYYYMMDD>-<topic> origin/main`.
- Commit small, clear commits. Push with `git push -u origin <branch>` and open a PR.
- Never push to `main`, never force-push, never rewrite history.
- PRs that change only `ops/worklog/` may be merged by you once CI is green.
  Any PR that changes code, configs, thresholds, profiles or `docs/` needs a Claude
  review (`wbr-claude-review-request`) and the owner's go-ahead before merging.

## Hard limits (all modes)

- No gate PASS without explicit evidence reviewed by the owner.
- Never relax a threshold or edit a result to change its status.
- Destructive actions need the user's typed `CONFIRM <action> <target>`.
- Keep Pi perception and STM32 control separate; never touch STM32 or motors.
- Never subtract timestamps across clock domains without a defined mapping.
