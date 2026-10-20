#!/bin/bash
# Double-click in Finder on macOS. Uses this checkout's environment.
set -e
wbr_sim_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$wbr_sim_root"
if [ ! -x .venv/bin/mjpython ]; then
    echo "Create the simulation environment first:"
    echo "python3.12 -m venv .venv"
    echo ".venv/bin/python -m pip install -r sim/requirements.lock"
    exit 1
fi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec .venv/bin/mjpython -m sim.view
