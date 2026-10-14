#!/bin/zsh
cd "$(dirname "$0")/../.."
L=research/sw-foundation/logs
job() { local tag=$1 P=$2; shift 2
  for acc in "$@"; do
    if ps eww -ax | grep "codex exec" | grep -v grep | grep -q "codex-$acc"; then echo "$(date) $tag skip busy codex-$acc" >> $L/rotation.log; continue; fi
    echo "$(date) start $tag codex-$acc" >> $L/rotation.log
    CODEX_HOME="$HOME/.codex-$acc" codex exec --sandbox workspace-write --skip-git-repo-check -c web_search=live "$P" > $L/$tag-$acc.log 2>&1 < /dev/null
    rc=$?; echo "$(date) $tag codex-$acc rc=$rc" >> $L/rotation.log
    tail -30 $L/$tag-$acc.log | grep -qiE "usage limit|rate limit|quota|429" || return $rc
  done; }
job J1 "Read research/sw-foundation/J1_BRIEF.md and follow it exactly." b g c &
sleep 5
job J2 "Read research/sw-foundation/J2_BRIEF.md and follow it exactly." g b c &
wait; echo ALLDONE >> $L/rotation.log
