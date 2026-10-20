# Agent guide (ChatGPT Work, Codex, Claude)

**Flow: build first, fix when it breaks.** Get the thing running, then integrate,
then improve. When something fails, debug from the actual error message, fix it,
and run again. Do not run qualification checks, gate audits or layer-by-layer
tests before trying the real thing.

The main working agent is **ChatGPT Work**. Claude is only called when ChatGPT is
truly stuck on an error. Always reply in English unless the owner explicitly asks
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
- End each result with a short **Recommendation** for the next step.

## Notes you keep (short)
- `ops/worklog/CURRENT.md`: overwrite at session end — current state, what works,
  what's broken, next step. Keep it under ~40 lines.
- `ops/worklog/sessions/YYYY-MM-DD-<topic>.md`: what was run, what happened, what
  was fixed. Bullet points, no essays.
No per-change documentation log, decision entries or evidence labels required.

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
If the same error survives a few real fix attempts, write
`ops/worklog/reviews/YYYY-MM-DD-<topic>.md` (the error, what you tried, the exact
log path) and give the owner one line to send to Claude:
`Help with ops/worklog/reviews/<file> on branch <branch>.`
