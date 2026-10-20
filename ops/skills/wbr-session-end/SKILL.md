---
name: wbr-session-end
description: End a WBR work session: short notes, commit, push, merge. Use when the owner says "end session" or work stops.
---

# Session end

1. Write `ops/worklog/sessions/YYYY-MM-DD-<topic>.md`: bullets of what was run,
   what happened, what was fixed, where logs are.
2. Overwrite `ops/worklog/CURRENT.md`: what works, what's broken, next step
   (under ~40 lines).
3. `git add -A && git commit -m "<topic>: <what changed>" && git push -u origin HEAD`,
   open a PR (`gh pr create --fill`), and merge it once CI is green
   (`gh pr merge --merge`). Without `gh`, give the owner the PR link.
4. Tell the owner in 3 lines: what got done, what's next.
