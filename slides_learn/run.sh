#!/bin/zsh
cd "$(dirname "$0")/.."
mkdir -p slides_learn/logs
run() { # $1=prompt $2=tag $3..=accounts
  local P=$1 tag=$2; shift 2
  for acc in "$@"; do
    log=slides_learn/logs/$tag-$acc.log
    echo "=== $(date) start $tag codex-$acc" >> slides_learn/logs/rotation.log
    CODEX_HOME="$HOME/.codex-$acc" codex exec --sandbox workspace-write --skip-git-repo-check "$P" > $log 2>&1 < /dev/null
    rc=$?; echo "=== $(date) $tag codex-$acc rc=$rc" >> slides_learn/logs/rotation.log
    tail -20 $log | grep -qiE "usage limit|rate limit|quota|429" || return $rc
  done
}
run "Read slides_learn/BRIEF.md and follow it exactly. If slides_learn/ already has work, continue from it. Finish the full build and reader self-review loop before stopping." build g d b a || exit 1
run "Read slides_learn/REVIEW_BRIEF.md and follow it exactly." review b g d a
