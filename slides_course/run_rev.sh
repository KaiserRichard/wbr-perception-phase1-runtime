#!/bin/zsh
# Usage: ACCS="x y" run_rev.sh <folder> <section-name>
cd "$(dirname "$0")/.."
D=$1; S=$2
P="Read $D/BRIEF.md. Do only the section '$S' (earlier sections are already done; the deck exists). Follow the builder rules at the top of the brief."
mkdir -p $D/logs
for acc in ${=ACCS:-b}; do
  log=$D/logs/rev-$acc.log
  echo "=== $(date) start $S codex-$acc" >> $D/logs/rotation.log
  CODEX_HOME="$HOME/.codex-$acc" codex exec --sandbox workspace-write --skip-git-repo-check "$P" > $log 2>&1 < /dev/null
  rc=$?; echo "=== $(date) $S codex-$acc rc=$rc" >> $D/logs/rotation.log
  tail -20 $log | grep -qiE "usage limit|rate limit|quota|429" || exit $rc
done
