---
name: wbr-session-end
description: End a WBR work session. Writes the session log, updates CURRENT.md, appends decisions, commits and pushes. Use when the user stops, says "end session"/"handoff", or after a major milestone.
---

# Session end

Conventions are in `ops/worklog/README.md`. Write for a reader who has never seen
this conversation.

1. **Session log**: create `ops/worklog/sessions/YYYY-MM-DD-<topic>.md` (new file;
   add `-2` if it exists). Sections: Done (numbered, with evidence labels, exact
   paths, commits, exit codes), Notes, Decisions (IDs), Not done / blocked.
2. **Decisions**: append one entry per decision taken this session to
   `ops/worklog/DECISIONS.md` (next free `D-YYYYMMDD-N`). Include who decided.
3. **CURRENT.md**: rewrite it to the state *now*: Active goal, Hardware right now,
   Evidence so far (add new results on top, keep it short), Blockers, Open questions
   for the owner, Next step. Update the "Last updated" line.
4. **Lab evidence**: confirm every run folder was copied with `wbr-evidence-copy`;
   list any that were not under Blockers.
5. **Commit and push** (in `~/Desktop/Research/wbr-lab-ops`, on your `chatgpt/...`
   branch, never `main`):
   ```sh
   git add ops/worklog && git status -sb
   git commit -m "worklog: <date> <topic>" && git push -u origin HEAD
   ```
   Open a PR (`gh pr create --fill` if `gh` exists; otherwise give the user the
   compare link printed by `git push`). If the PR changes only `ops/worklog/` and CI
   is green, you may merge it (`gh pr merge --merge`). Otherwise leave it for review.
6. If a decision belongs to Claude or the owner, run `wbr-claude-review-request`.
7. Tell the user in at most 6 lines: what changed, PR link, open questions,
   **Recommendation** for the next session.
