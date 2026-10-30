# AGY secretary

Run from this repository with Git/SSH access to origin, authenticated `gh`, and
`agy` on PATH:

```sh
bash ops/secretary/digest.sh daily
bash ops/secretary/digest.sh afternoon
# Collect sources without calling agy:
bash ops/secretary/collect.sh
```

AGY is used because it is cheap, fast, and has plenty of quota; its output is a
draft to be checked against the named sources.

The collector fetches origin and reads recent remote branches with `git show`,
without checking them out. “Recent” means a branch tip committer date within the
last 72 hours; included reviews are files changed in that window, including
merge changes, under `ops/worklog/reviews/*.md`. Deleted reviews are noted.
Each review records repo, branch, path and last commit date. PNG/SVG inventories
come from `git ls-tree` under `reports/`, `results/` and `docs/` on each branch.

If present, `~/Desktop/OS/OS-project/heterogeneous-edge-ai-os` and `~/Desktop/CN`
are also collected, including their local review files (which may be uncommitted
or older than the remote-branch window). No checkout is changed. Open PR JSON is
queried for this repo and `KaiserRichard/heterogeneous-edge-ai-os`; unavailable
queries are recorded as BLOCKED rather than an empty list.

Outputs are ignored under `ops/secretary/out/`: `bundle-YYYY-MM-DD.md`,
`digest-YYYY-MM-DD-MODE.md`, and the retained agy stderr log. Same-day successful
runs replace the corresponding bundle/digest. A failed agy run preserves any
previous successful digest and exits nonzero. Blank digests and digests of 60 or
more lines are rejected; an overlong draft is retained as `*.rejected.md`.
Stderr attempts are appended to the same day's log, and AGY's own log is directed
into `out/` with its supported `--log-file` option. The prompt is inlined with the
bundle into the final `-p` argument to `agy --model claude-opus-4-6-thinking`;
`--effort` is never passed. The default mode is `daily`.

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

To finish the real run in an environment allowing AGY's local server, Git
metadata writes and GitHub access, run the afternoon command above, check the
generated draft against its sources, then copy that result to
`ops/secretary/example-digest.md` and commit/push on the task branch. Do not
commit `out/`, open a PR, or merge.
