#!/bin/zsh
# Usage: ACCS="j f" ./run.sh   — Codex builder with account rotation on usage limits.
cd "$(dirname "$0")"
P="Read slides_study/BRIEF.md and follow it exactly. If slides_study/ already contains work from a previous builder (main.tex, PROGRESS.md), continue from its current state instead of restarting. Finish the full build and quality loop before stopping."
mkdir -p logs
for acc in ${=ACCS:-j f}; do
  log=logs/builder-$acc.log
  extra=()
  [[ $acc == a || $acc == c || $acc == d || $acc == h ]] && extra=(-m gpt-6-luna)
  echo "=== $(date) start codex-$acc" >> logs/rotation.log
  (cd .. && CODEX_HOME="$HOME/.codex-$acc" codex exec $extra -c model_reasoning_effort="high" --sandbox workspace-write --skip-git-repo-check "$P") > $log 2>&1 < /dev/null
  rc=$?
  echo "=== $(date) codex-$acc rc=$rc" >> logs/rotation.log
  tail -30 $log | grep -qiE "usage limit|rate limit|quota|429" || exit $rc
done
