---
name: wbr-session-start
description: Start any WBR work session (lab, code, research). Loads state from the worklog, syncs git and states a plan. Use at the beginning of every session or after a long break.
---

# Session start

1. Sync the worktree (read-only for other folders):
   ```sh
   cd ~/Desktop/Research/wbr-lab-ops && git fetch origin && git status -sb && git log --oneline -1 origin/main
   ```
   If the worktree has uncommitted changes from an earlier session, show them and
   ask the user whether they belong to unfinished work before doing anything else.
   To start new work: `git switch -c chatgpt/$(date +%Y%m%d)-<topic> origin/main`.
2. Read, in order: `ops/worklog/CURRENT.md`, the last 15 entries of
   `ops/worklog/DECISIONS.md`, the newest file in `ops/worklog/sessions/`,
   any open file in `ops/worklog/reviews/` (one with an answered `## Claude review`
   section is closed), `ops/RESEARCH_RULES.md`, `docs/NEXT_GATE.md`.
3. For lab work, also read `ops/lab-assistant/INSTRUCTIONS.md`.
4. Tell the user, in at most 10 lines:
   - current goal and blockers (from CURRENT.md);
   - anything Claude answered since last time;
   - your plan for this session, step by step, and what you need from the user;
   - **Recommendation**: the first step and why.
5. Note the session start time; you will need it for the session log.
