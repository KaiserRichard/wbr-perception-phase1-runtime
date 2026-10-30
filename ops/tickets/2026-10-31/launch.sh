#!/bin/zsh
# 31 Oct ticket launcher. Usage: launch.sh wave1 | wave2a | wave2b | status
T=${0:A:h}; L=$HOME/wbr-evidence/c1-20261031; mkdir -p $L
REP="$HOME/Desktop/30:10 video /WBR_Phase1_Report"
idle(){ [ $(ps eww -ax | grep "CODEX_HOME=$HOME/.codex-$1 " | grep -v app-server | grep -v grep | wc -l) -eq 0 ]; }
run(){ acct=$1; flags=$2; dir=$3; tk=$4
  idle $acct || { echo "SKIP $tk: codex-$acct busy"; return; }
  CODEX_HOME=$HOME/.codex-$acct nohup codex ${=flags} --sandbox workspace-write -C "$dir" "$(cat $T/$tk.txt)" < /dev/null > $L/$tk.log 2>&1 &
  echo "started $tk on codex-$acct"; }
case $1 in
  wave1)
    run k "exec --skip-git-repo-check" "$REP" A1-report-owner-comments
    mkdir -p "$REP/review_next"
    run c "exec -m gpt-6-luna --skip-git-repo-check" "$REP/review_next" A2-report-critique
    run a "exec -m gpt-6-luna" "$HOME/.worktrees/wbr-c1-model" A4-model-generator
    run j "exec -m gpt-6-luna --skip-git-repo-check" "$HOME/wbr-evidence/c1-20261030/p1-run" A5-yolo-variants
    run h "--search exec -m gpt-6-luna" "$HOME/.worktrees/wbr-c1-simplan" A6-sim-compute-plan ;;
  wave2a) run k "exec --skip-git-repo-check" "$REP" B1-apply-critique ;;     # after A1 and A2
  wave2b) run e "exec --skip-git-repo-check" "$REP" B2-report-vietnamese ;;  # after B1
  status) for f in $L/*.log; do echo "$(basename $f): $(tail -1 $f | cut -c1-120)"; done
          grep -lE '^ERROR:.*(usage limit|not supported)' $L/*.log 2>/dev/null ;;
esac
