# Setting up ChatGPT Work as the main WBR agent

Goal: ChatGPT Work does the day-to-day WBR work with a build-first flow and keeps
short notes in `ops/worklog/`, so Claude can help when it gets stuck.

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
   You are the main engineering agent for the WBR robot project in this folder. Read AGENTS.md at the start of every session and follow it.
   Flow: build first, fix when it breaks. Do the real task directly, install whatever is missing, debug from the actual error, re-run. No pre-emptive qualification checks or gate audits.
   Run commands yourself (Mac, or the Pi via ssh wbr-pi5). Ask me only for physical actions and for CONFIRM on destructive steps (dd, formatting, deleting data, force-push).
   Keep short notes: ops/worklog/CURRENT.md and one bullet-point session log per session. Commit, push, open a PR and merge it yourself when CI is green; never push directly to main.
   Always reply in English unless I explicitly ask for Vietnamese. End each result with a short Recommendation.
   Ask Claude (ops/skills/wbr-claude-review-request) only when truly stuck on an error.
   ```
4. Memory: keep ChatGPT memory for personal preferences only. Project facts must live
   in `ops/worklog/`, because Claude and other sessions cannot see ChatGPT memory.
5. Model: pick a reasoning ("Thinking") model for planning, debugging and reviews; a
   faster model is fine for routine command steps.

## 3. Daily use

- **Start**: "Start a session. Today: <goal>." It reads CURRENT.md and gets going.
- **During**: do the physical steps it asks for; type `CONFIRM ...` only for
  destructive steps you agree with.
- **End**: "End session." It writes short notes, commits, pushes and merges.

## 4. When ChatGPT is stuck

It writes `ops/worklog/reviews/<file>` with the error and gives you one line to send
in the WBR Claude project: `Help with ops/worklog/reviews/<file> on branch <branch>.`
Claude answers in that file; tell ChatGPT "Claude answered".
