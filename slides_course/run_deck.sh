#!/bin/zsh
# Usage: ACCS="b d" run_deck.sh <folder>  — runs a Codex builder on <folder>/BRIEF.md with account rotation.
cd "$(dirname "$0")/.."
D=$1
P="Read $D/BRIEF.md and follow it exactly. If $D/ already contains work from a previous builder, continue from its current state instead of restarting. Finish the full build and self-review loop before stopping."
mkdir -p $D/logs
for acc in ${=ACCS:-b d}; do
  log=$D/logs/builder-$acc.log
  echo "=== $(date) start codex-$acc" >> $D/logs/rotation.log
  CODEX_HOME="$HOME/.codex-$acc" codex exec --sandbox workspace-write --skip-git-repo-check "$P" > $log 2>&1 < /dev/null
  rc=$?
  echo "=== $(date) codex-$acc rc=$rc" >> $D/logs/rotation.log
  tail -20 $log | grep -qiE "usage limit|rate limit|quota|429" || exit $rc
done
