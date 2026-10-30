# Agent guide (ChatGPT Work, Codex, Claude)

**Flow: build first, fix when it breaks.** Get the thing running, then integrate,
then improve. When something fails, debug from the actual error message, fix it,
and run again. Do not run qualification checks, gate audits or layer-by-layer
tests before trying the real thing.

The main working agent is **ChatGPT Work**, acting as conductor. Claude is the
final reviewer of completed milestones. Always reply in English unless the owner explicitly asks
for Vietnamese.

## Start of a session
Read `ops/worklog/CURRENT.md` (where we are, what's next) and `ops/USER_PROFILE.md`.
Then start working on the next step.

## Current direction
1. Plug in the camera (currently a D435, no IMU) and get ORB-SLAM3 running on the Pi
   (stereo or RGB-D). Skill: `ops/lab-assistant/skills/wbr-orbslam3-bringup`.
2. Get the software running end to end (ROS 2 wrapper, pose output).
3. Integrate with the robot hardware.
4. In parallel when useful: MuJoCo simulation and RL vs LQR (`ops/RESEARCH_RULES.md`).

## How to work
- Install whatever is missing (apt, pip, build from source) and keep going.
- Run commands yourself when you can (Mac, or the Pi via `ssh wbr-pi5`).
- One fix at a time when something breaks; re-run; note what fixed it.
- End every owner-facing message with exactly one final line:
  `NEED FROM YOU: <one physical action or one decision, in plain words>` or
  `NOTHING NEEDED: <what you are doing next>`.
- Put recommendations only inside review files, never in messages to the owner.

## Notes you keep (short)
- `ops/worklog/CURRENT.md`: overwrite at session end — current state, what works,
  what's broken, next step. Keep it under ~40 lines.
- `ops/worklog/sessions/YYYY-MM-DD-<topic>.md`: what was run, what happened, what
  was fixed. Bullet points, no essays.
- `ops/worklog/ledger/<branch-name-with-slashes-as-dashes>.md` (owner rule, 2026-10-30): every
  branch keeps its own ledger. When a task, run or fix finishes, append ONE line:
  `- YYYY-MM-DD HH:MM | who (session/worker) | what | status DONE/PARTIAL/BLOCKED | evidence (number, file, PR)`.
  Commit it with the work. Don't write long summaries there. On request, `agy` aggregates all
  ledgers and reviews across branches (`ops/secretary/`), and Claude only reads and spot-checks that digest.
Record documentation changes in `ops/worklog/DOCUMENTATION_LOG.md` and decisions
in `ops/worklog/DECISIONS.md`, following the owner's current logging instruction.
Keep learning notes concise but complete: render Markdown math properly, explain
model assumptions and derivations, and include a worked example. Never replace
necessary explanation with a rigid line limit or unexplained formulas.

## Conducting Codex
- Conductor plans, scopes, launches and independently runs worker results, then merges PRs only after green CI. Claude reviews completed milestones only.
- Accounts (owner, 2026-10-30; supersedes the tiers below): **codex-e and codex-k are ChatGPT Plus**: use the default model, no `-m`. All other accounts are free plans and need `-m gpt-6-luna`. `agy` (print mode, `-p` last; `--effort` is not accepted by the Opus model) is also available for reading/report drafts.
- Historical overnight override (2026-10-20): f conducts; Plus g/i/k take hard tasks (Astra Ultra), b/e/default medium tasks (Sol), d/h/j simple tasks. Check shared-account idle state and quota before dispatch; never interrupt unrelated work. Recheck refills every 30 minutes and at 06:30; move quota-limited partial work to an idle account of the same or lower tier. f implements only after all workers exhaust quota. Earlier b-conductor receipts remain historical.
- One worker per task, each in its own worktree and `chatgpt/<YYYYMMDD>-<topic>` branch. Never use the shared Mac checkout or change its branch.
- Give a short brief: goal, allowed files and exact command proving done. Build first; install missing dependencies and fix actual errors, preserving logs/failures.
- Workers never run dd, format/partition/delete, force-push, command motors or flash STM32; only conductor merges. Keep Pi perception separate from hardware control.
- While PPO trains on the Mac, workers only edit and run quick targeted unit tests. Heavy simulation, training and rendering use an available Pi or wait; never alter the running experiment, its environment or evidence.
- `sim/parity/student.py::gain_schedule` is owner-only: review it without writing it or bypassing it with a duplicate solution.
- Record actual runs and document edits in worklogs. At a completed milestone, write one `ops/worklog/reviews/<date>-<milestone>.md` listing merged PRs, commands/results and limitations; give the owner one line for Claude.
- Overnight exception: consolidate task outcomes into `ops/worklog/reviews/2026-10-21-overnight.md` (one line per task: done/partial/blocked, PR). Claude reviews that single file in the morning.

## Git
- Work in `~/Desktop/Research/wbr-lab-ops` on a `chatgpt/<YYYYMMDD>-<topic>` branch
  from `origin/main`. Never touch the branch of the shared checkout
  `~/Desktop/Research/wbr-perception-phase1-runtime`.
- Commit, push, open a PR, and merge it yourself once CI is green.
- Never push directly to `main`, never force-push.

## Always ask the owner first (type `CONFIRM <action> <target>`)
- Formatting or partitioning a disk, writing a disk image (`dd`), deleting data,
  force-push or history rewrite.

## Safety boundary
- The STM32 owns balance and motor safety. Do not send commands to motors or flash
  the STM32 without the owner explicitly asking for it.

## When stuck
Workers report the actual error, attempts and log path to the conductor. Continue
independent work; ask the owner for physical access or missing information. Keep
blocked work explicit. Ask Claude only after a milestone is complete, using the
Conducting Codex summary above.
