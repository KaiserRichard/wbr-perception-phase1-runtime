---
name: wbr-lab-handoff-review
description: Review a WBR lab handoff written by ChatGPT or Codex (ops/lab-assistant/handoffs/*.md) and decide next steps. Use when the user asks Claude to review a lab handoff.
---

# Review a lab handoff

Goal: spend as little Claude effort as possible while keeping the evidence standard.

1. Read the handoff file (Mac repo folder `ops/lab-assistant/handoffs/`, or the
   pasted block). Do not re-run steps the handoff already reports.
2. For each tool result named in it, read only that run's `result.json` (and the
   one log a FAIL/BLOCKED criterion points to). Check that the handoff's statuses
   and exit codes match. Treat everything else in the handoff as the assistant's
   claim: MEASURED only if the output path backs it.
3. Flag rule breaks: gate PASS claims, reused output folders, edited results or
   thresholds, mixed clock domains, destructive steps without a CONFIRM record,
   evidence deleted before checksum verification, a different camera serial than
   317422076650.
4. Answer the handoff's open decisions with a recommendation each.
5. Reply in English, short: what is confirmed, what is wrong in the handoff, the
   decisions, and the next lab step (name the skill to run). Do not update
   `docs/PROJECT_STATE.md` or any gate status without the owner's explicit review.
