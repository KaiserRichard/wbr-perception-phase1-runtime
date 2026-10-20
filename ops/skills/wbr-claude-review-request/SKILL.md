---
name: wbr-claude-review-request
description: Ask Claude for help when truly stuck on an error after a few real fix attempts.
---

# Ask Claude for help

1. Create `ops/worklog/reviews/YYYY-MM-DD-<topic>.md` from the template in
   `ops/worklog/reviews/README.md`: exact error, log path, what you tried, one question.
2. Commit and push it on your branch.
3. Give the owner the line: `Help with ops/worklog/reviews/<file> on branch <branch>.`
4. Meanwhile keep working on anything that doesn't depend on the answer.
