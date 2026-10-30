# Brief: AGY secretary (Codex, codex-k)

Goal: a small tool so `agy` (model `claude-opus-4-6-thinking`) acts as the team's secretary. It gathers every
progress report, then writes a short digest for the owner. Allowed files: `ops/secretary/**` only.

Build:
1. `ops/secretary/collect.sh`:
   - `git fetch origin`;
   - for every remote branch updated in the last 3 days, print each changed file under
     `ops/worklog/reviews/*.md` (use `git show origin/<branch>:<path>`, never check out);
   - also add any matching files in the main repo at `~/Desktop/OS/OS-project/heterogeneous-edge-ai-os`
     and `~/Desktop/CN` if those folders exist;
   - write it all to one bundle file `ops/secretary/out/bundle-<date>.md`, with a header per file
     (repo, branch, path, last commit date);
   - also list open PRs with `gh pr list --state open --json number,title,headRefName,updatedAt` (this repo,
     plus `KaiserRichard/heterogeneous-edge-ai-os` if gh can see it).
2. `ops/secretary/digest.sh [daily|afternoon]`: runs collect.sh, then
   `agy --model claude-opus-4-6-thinking -p "<prompt>"` with the bundle inlined in the prompt (`-p` must be LAST;
   do NOT pass `--effort`). Writes the result to `ops/secretary/out/digest-<date>-<mode>.md`.
   Prompt rules for agy (put them in `ops/secretary/prompt_<mode>.md`):
   - English.
   - Under 60 lines.
   - Evidence statuses kept as written (MEASURED/ASSUMED/PASS/FAIL/BLOCKED); never upgrade a status.
   - Every claim names its source file.
   - Sections: what works now (with key numbers), what failed or is blocked, what the owner must do by hand, open PRs to decide.
   - `afternoon` mode adds "How to demo it yourself" (exact commands copied from the sources, not invented)
     and "Next steps" (max 5 bullets).
   - Image links: list existing PNG/SVG paths found in the bundle's branches (`git ls-tree` for
     `*.png` under `reports/`, `results/`, `docs/`) that fit each section; don't invent paths.
3. `ops/secretary/README.md`: how to run it; one line on why agy (cheap, fast, plenty of quota) and that the
   output is a draft to be checked against the sources.

Done = run `bash ops/secretary/digest.sh afternoon` once for real. It must produce a non-empty digest. If agy fails,
fix it from the actual error, retry, and keep the error in the README. Commit on the current branch
`claude2/20261030-agy-secretary` and push it. Don't open a PR and don't merge. Don't commit the `out/` bundle files
(add `.gitignore`); do commit one example digest as `ops/secretary/example-digest.md`.
