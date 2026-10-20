---
name: wbr-claude-review-request
description: Ask Claude for a review or decision with a self-contained file, so Claude can answer cold and cheaply. Use for code/config/threshold changes, research-plan changes, unlocalized failures, or gate interpretation.
---

# Claude review request

Claude's quota is limited: ask only what needs Claude (see `AGENTS.md` and the
lab "Decision authority"), and make the request answerable without a conversation.

1. Make sure the work under review is pushed (branch + PR).
2. Copy the template from `ops/worklog/reviews/README.md` to
   `ops/worklog/reviews/YYYY-MM-DD-<topic>.md`. Fill it in:
   - at most 3 questions, each answerable with a decision;
   - a cold-start context of at most 15 lines with exact paths/PRs;
   - your own recommendation with evidence labels.
3. Commit it on the same branch and push.
4. Give the user this exact line to send in the WBR Claude project:
   `Review ops/worklog/reviews/<file> on branch <branch> (PR #<n>).`
5. Continue with work that does not depend on the answer. When the user says Claude
   answered, pull the branch, read `## Claude review`, record the outcome as a
   decision in `DECISIONS.md`, and act on it.
