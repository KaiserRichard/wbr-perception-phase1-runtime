# Worklog conventions

The worklog is the shared memory between ChatGPT Work, Codex and Claude. Write it so
that someone who has never seen the conversation can continue the work.

| File | Rule |
|---|---|
| `CURRENT.md` | Overwrite at session end. At most ~60 lines. Sections fixed (see file). |
| `DECISIONS.md` | Append-only, newest at the bottom. Fix a wrong entry by adding a new one that supersedes it (`Supersedes D-YYYYMMDD-N`). |
| `sessions/YYYY-MM-DD-<topic>.md` | One per session. What was done, evidence paths, results, decisions taken. |
| `reviews/YYYY-MM-DD-<topic>.md` | A request for Claude. Claude answers in the same file under `## Claude review`. |

Rules:
- Label claims (MEASURED, CALCULATED, INFERRED, ASSUMED, UNKNOWN, SOURCE-SUPPORTED).
- Give exact paths (Pi, Mac archive, repo), commits and exit codes. Point to logs;
  do not paste them.
- Keep secrets out: no passwords, tokens, private keys, Wi-Fi credentials.
- Evidence data (run folders, bags, images) never goes in git. It lives under
  `~/wbr-evidence/` on the Pi and `~/wbr-evidence-archive/` on the Mac, with SHA-256
  manifests; the worklog only references it.
- Times: local time with offset, e.g. `2026-10-20 08:54 +07`.
- Keep at most one open worklog PR: merge it before the next session starts, so
  `CURRENT.md` does not conflict between branches.

Decision entry format (in `DECISIONS.md`):

```markdown
### D-20261020-1: <short title>
- Decided by: owner | ChatGPT Work | Claude review | Codex
- Decision: <one or two sentences>
- Why: <reason, with evidence labels>
- Evidence: <paths, PRs, sessions>
- Revisit when: <condition, or "never">
```
