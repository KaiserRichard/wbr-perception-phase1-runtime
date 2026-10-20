# Setting up ChatGPT Work as the main WBR agent

Goal: ChatGPT Work does the day-to-day WBR work (lab, code, analysis, docs) and keeps
every state, decision and result in `ops/worklog/`, so Claude can be called in
occasionally as a reviewer and read everything cold from GitHub.

Menu names below may differ slightly in your ChatGPT version; the intent of each
step is what matters.

## 1. One-time preparation on the Mac

1. The worktree `~/Desktop/Research/wbr-lab-ops` is ChatGPT Work's folder. Bring it
   up to date (this does not touch your main checkout):
   ```sh
   git -C ~/Desktop/Research/wbr-lab-ops fetch origin
   git -C ~/Desktop/Research/wbr-lab-ops status -sb
   git -C ~/Desktop/Research/wbr-lab-ops checkout --detach origin/main
   ```
   If `status` shows changes, keep them: ask ChatGPT Work to commit them on a branch
   during its first session instead of running the checkout.
2. SSH alias for the Pi, so all skills work unchanged. Add to `~/.ssh/config`:
   ```
   Host wbr-pi5
       HostName 192.168.50.2
       User richard
   ```
   Test: `ssh wbr-pi5 hostname` prints `wbr-pi5`.
3. Optional but recommended: GitHub CLI, so ChatGPT Work can open and merge its own
   worklog PRs: `brew install gh && gh auth login`. Without it, ChatGPT Work gives you
   a link and you click "Create pull request" yourself.

## 2. Configure ChatGPT Work

1. Open ChatGPT Work and select the folder **`~/Desktop/Research/wbr-lab-ops`** as
   the workspace/project folder. Do not select
   `~/Desktop/Research/wbr-perception-phase1-runtime`.
2. Permissions: allow reading and writing files in that folder; allow terminal
   commands with approval (ask before running). Do not choose a mode that runs
   everything without asking.
3. Instructions: paste this into the workspace/project instructions field:
   ```
   You are the main engineering and research agent for the WBR perception project in this folder.
   Before anything else in every session, read AGENTS.md and follow it, starting with the wbr-session-start skill (ops/skills/wbr-session-start/SKILL.md).
   The repository files are the memory: record state in ops/worklog/CURRENT.md, decisions in ops/worklog/DECISIONS.md and every session in ops/worklog/sessions/. Do not rely on chat memory for project facts.
   Always reply in English unless I explicitly ask for Vietnamese. Expand an abbreviation the first time you use it.
   Decide routine engineering steps yourself and end every result with a Recommendation. Ask me only for physical actions, CONFIRM phrases for destructive steps, and real decisions.
   Claude is an occasional reviewer: use ops/skills/wbr-claude-review-request only when AGENTS.md says a change needs review.
   Never push to main, never force-push, never claim a gate PASS.
   ```
4. Memory: keep ChatGPT memory for personal preferences only. Project facts must live
   in `ops/worklog/`, because Claude and other sessions cannot see ChatGPT memory.
5. Model: pick a reasoning ("Thinking") model for planning, debugging and reviews; a
   faster model is fine for routine command steps.

## 3. Daily use

- **Start**: "Start a session. Today I want to <goal>." It runs `wbr-session-start`
  and proposes a plan.
- **During**: let it decide routine steps. Answer its physical-action requests and
  type `CONFIRM ...` only when you agree with the destructive step it names.
- **End**: "End session." It runs `wbr-session-end`: session log, CURRENT.md,
  decisions, commit, push, PR.

## 4. When you need Claude

ChatGPT Work writes a review request file and gives you one line. Send that line in
the WBR Claude project, for example:

`Review ops/worklog/reviews/2026-10-21-pyrealsense2-install.md on branch chatgpt/20261021-binding (PR #36).`

Claude reads the file and the PR from GitHub, writes its answer under
`## Claude review` in the same file, and merges or comments on the PR. Then tell
ChatGPT Work "Claude answered" and it picks the answer up.

What still goes to Claude: changes to code, configs, thresholds or profiles before
merge; research-plan changes (for example the missing camera IMU); failures that
survive one diagnostic retry; anything about gate status.
