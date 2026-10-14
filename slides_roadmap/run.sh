#!/bin/zsh
cd "$(dirname "$0")/.."
L=slides_roadmap/logs; mkdir -p $L
job() { # tag prompt accounts...
  local tag=$1 P=$2; shift 2
  for acc in "$@"; do
    echo "=== $(date) start $tag codex-$acc" >> $L/rotation.log
    CODEX_HOME="$HOME/.codex-$acc" codex exec --sandbox workspace-write --skip-git-repo-check -c web_search=live "$P" > $L/$tag-$acc.log 2>&1 < /dev/null
    rc=$?; echo "=== $(date) $tag codex-$acc rc=$rc" >> $L/rotation.log
    tail -20 $L/$tag-$acc.log | grep -qiE "usage limit|rate limit|quota|429" || return $rc
  done
}
job R1 "Read slides_roadmap/research/R1_BRIEF.md and follow it exactly." b g d a &
job R2 "Read slides_roadmap/research/R2_BRIEF.md and follow it exactly." g c d a &
job R3 "Read slides_roadmap/research/R3_BRIEF.md and follow it exactly." c b d a &
wait
job SYNTH "Read slides_roadmap/SYNTH_BRIEF.md and follow it exactly." a d b g c
job REVIEW "Read slides_roadmap/REVIEW_BRIEF.md and follow it exactly." d b g c a
echo ALLDONE >> $L/rotation.log
