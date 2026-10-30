# AGY secretary

Run from this repository with Git/SSH access to origin, authenticated `gh`, and
`agy` on PATH. **Run the real digest outside the Codex sandbox**, for example
from a normal macOS Terminal. AGY starts a localhost server; this sandbox denies
its socket bind with `listen tcp 127.0.0.1:0: bind: operation not permitted`.
Changing AGY's print/output flags cannot lift that operating-system restriction.
The sandbox can also block shared Git metadata writes and GitHub access.

```sh
bash ops/secretary/digest.sh daily
bash ops/secretary/digest.sh afternoon
# Collect sources without calling agy:
bash ops/secretary/collect.sh
```

AGY is used because it is cheap, fast, and has plenty of quota; its output is a
draft to be checked against the named sources.

The collector fetches origin and reads every remote branch except
`origin/HEAD`, without checking branches out. At each branch tip it includes
every existing Markdown file under `ops/worklog/reviews/` and
`ops/worklog/ledger/`, regardless of branch age or file commit date. Paths are
deduplicated within each branch; each copy records repo, branch, path and last
commit date. PNG/SVG inventories come from `git ls-tree` under `reports/`,
`results/` and `docs/` on each branch.

If present, `~/Desktop/OS/OS-project/heterogeneous-edge-ai-os` and `~/Desktop/CN`
are also collected, including their local review and ledger files (which may be
uncommitted). No checkout is changed. Open PR JSON is
queried for this repo and `KaiserRichard/heterogeneous-edge-ai-os`; unavailable
queries are recorded as BLOCKED rather than an empty list.

Outputs are ignored under `ops/secretary/out/`: `bundle-YYYY-MM-DD.md`,
`digest-YYYY-MM-DD-MODE.md`, and the retained agy stderr log. Same-day successful
runs replace the corresponding bundle/digest. A failed agy run preserves any
previous digest and exits nonzero. Digests must contain 20–59 lines and every
exact `##` section heading specified in the selected prompt (four for daily,
six for afternoon). Rejected drafts are retained as `*.rejected.md`, with the
reason appended to the stderr log. These checks validate the output's shape;
the owner still checks its claims against sources.
Stderr attempts are appended to the same day's log, and AGY's own log is directed
into `out/` with its supported `--log-file` option. The prompt is inlined with the
bundle into the final `-p` argument to
`agy --model claude-opus-4-6-thinking --output-format text`; `--effort` is never
passed. Both prompts require ONLY the digest Markdown on stdout and prohibit
file writes and status notes. The default mode is `daily`.

When a fetch fails, the bundle explicitly marks the repo BLOCKED and all its
remote refs as cached/potentially stale. Collection continues with those refs
and other available repos, so the draft can expose collection failures.

## Run record

- Implementation and run evidence are kept here because this task permits edits
  only under `ops/secretary/**`; shared worklogs are outside its scope.
- 2026-10-30: ran `bash ops/secretary/digest.sh afternoon` for real. The initial
  fetch failed with `cannot open '.../FETCH_HEAD': Operation not permitted`:
  shared Git metadata is outside this sandbox's writable roots. Changed the
  collector to retain and label cached sources instead of discarding the run.
- Retried: collected an approximately 82 KB bundle from all three repo roots.
  Independently compared all 22 recent primary branches and 13 included review
  copies with `git show`: contents and provenance matched. Both PR queries
  reported BLOCKED because GitHub was unreachable. `bash -n` passed for both
  scripts; invalid mode returned usage and exit 2 before collection.
- Actual AGY error: `Failed to redirect output for CLI: ... log ... operation
  not permitted`, followed by `Failed to start: listen tcp 127.0.0.1:0: bind:
  operation not permitted`. Read `agy --help`, added the supported `--log-file`
  pointing into `out/`, and ran the afternoon command again. The logging error
  was fixed; the local socket bind still failed (exit 1). Both attempts remain
  in `out/digest-2026-10-30-afternoon.stderr.log`; AGY's log is
  `out/agy-2026-10-30-afternoon.log`. No successful digest or example digest is
  claimed, and no substitute was fabricated.
- A local clone on the same branch, `claude2/20261030-agy-secretary`, is retained
  in ignored `out/run-checkout/` for committing without modifying the shared
  checkout's Git metadata. Both SSH and HTTPS fetch attempts there failed:
  `ssh: Could not resolve hostname github.com: -65563` and
  `Could not resolve host: github.com`. Publishing requires network access.

## 2026-10-30 stdout fix

- Measured failure from `FIX-BRIEF.md`: the 15:24 output had only AGY's seven-line
  "Digest is ready for your review" note. It passed the old nonempty/under-60
  check. That ignored `out/digest-2026-10-30-afternoon.md` is invalid historical
  output, not an accepted digest from the fixed script.
- Read the installed `agy --help`: `-p` prints a single response and
  `--output-format text` explicitly selects plain-text stdout. Updated both
  prompts to return the actual Markdown only, use 20–59 lines and exact section
  headings, and never save a file or return a status note.
- Added minimum-length and per-mode heading validation before the atomic rename.
  All rejected stdout is retained, and an existing digest is preserved on error.
- Real test at 15:50 +07: `bash ops/secretary/digest.sh afternoon` collected a
  122,251-byte bundle (fetch/PR failures labelled BLOCKED), then exited 1 with
  `Failed to start: listen tcp 127.0.0.1:0: bind: operation not permitted`.
  This confirms the sandbox blocker persists. Logs remain in
  `out/digest-2026-10-30-afternoon.stderr.log` and
  `out/agy-2026-10-30-afternoon.log`. No new digest or example is claimed.
- `python3 ops/secretary/test_digest.py -v`: six tests PASS using controlled
  AGY stdout and a source-bundle fixture, without network or a model call.
  Covers the original seven-line note, 0/19/60-line rejection, each missing
  heading in both modes, valid 20/59-line publication in both modes, prompt
  argument placement and preservation of prior output on validation/CLI errors.
  `bash -n ops/secretary/digest.sh ops/secretary/collect.sh`: PASS.
- Documentation/decision record: kept fixes and run evidence here within the
  brief's `ops/secretary/**` scope; no shared worklog or hardware changes.
- `git add` in the supplied worktree failed creating the shared worktree's
  `index.lock` (`Operation not permitted`). The existing writable local clone
  at `out/run-checkout/` holds the task branch and original implementation
  commit `7730000`; stage the fix there using the supplied worktree as
  `--work-tree`, so the fix commit can be retained without changing shared
  Git metadata. Push output is retained in `out/push-2026-10-30-fix.log`.

The real afternoon command still needs a run outside the Codex sandbox and a
source check before its output can be committed as `example-digest.md`. The
fixture tests demonstrate validation behavior, not successful model generation.
Do not commit `out/`, open a PR, or merge for this task.
