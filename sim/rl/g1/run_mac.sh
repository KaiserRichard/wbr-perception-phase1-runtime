#!/usr/bin/env bash
# Forward runner options, including --seed-wall-cap-min (default unlimited).
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../../.." && pwd)"
if [[ -f "${G1_ENV_FILE:-/private/tmp/wbr-g1-env.sh}" ]]; then
    source "${G1_ENV_FILE:-/private/tmp/wbr-g1-env.sh}"
fi
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"
g1_python="${G1_PYTHON:-$HOME/Desktop/Research/wbr-lab-ops/.venv/bin/python}"
if [[ ! -x "$g1_python" ]]; then
    g1_python=python3
fi
exec caffeinate -i "$g1_python" -u -m sim.rl.g1.runner run "$@"
