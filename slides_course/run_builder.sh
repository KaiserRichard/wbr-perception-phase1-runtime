#!/bin/zsh
# Usage: run_builder.sh 1|2  — runs the deck builder phase, rotating Codex accounts on quota exhaustion.
cd "$(dirname "$0")/.."
PH=$1
P="Read slides_course/BRIEF.md and follow it exactly. Do PHASE $PH only. If slides_course/ already contains work from a previous builder, continue from its current state instead of restarting."
for acc in ${=ACCS:-d b a}; do
  log=slides_course/logs/phase$PH-$acc.log
  echo "=== $(date) start codex-$acc phase $PH" >> slides_course/logs/rotation.log
  CODEX_HOME="$HOME/.codex-$acc" codex exec --sandbox workspace-write --skip-git-repo-check "$P" > $log 2>&1 < /dev/null
  rc=$?
  echo "=== $(date) codex-$acc rc=$rc" >> slides_course/logs/rotation.log
  tail -20 $log | grep -qiE "usage limit|rate limit|quota|429" || exit $rc
done
