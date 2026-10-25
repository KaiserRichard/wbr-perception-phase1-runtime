#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 BAG_DIR" >&2
  exit 2
fi
BAG_DIR=$(cd "$1" && pwd)
WS=${WS:-"$HOME/wbr-demo-ws-20261025"}
ROS_SETUP=${ROS_SETUP:-/opt/ros/jazzy/setup.bash}
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ ! -f "$ROS_SETUP" || ! -f "$WS/install/setup.bash" ]]; then
  echo "Missing ROS or workspace setup: $ROS_SETUP, $WS/install/setup.bash" >&2
  exit 1
fi
if [[ ! -d "$BAG_DIR" ]]; then
  echo "Bag directory not found: $BAG_DIR" >&2
  exit 1
fi

source "$ROS_SETUP"
source "$WS/install/setup.bash"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

pids=()
stop_children() {
  local pid
  for pid in "${pids[@]}"; do kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true; done
  for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done
}
trap stop_children EXIT INT TERM

setsid ros2 run wbr_obstacle_node obstacle_node --ros-args \
  -p algo_path:="$REPO_ROOT" -p near_m:=1.3 &
pids+=("$!")
setsid python3 "$REPO_ROOT/tools/link_bench/pi/topic_to_nucleo.py" &
pids+=("$!")
sleep 2
ros2 bag play "$BAG_DIR" --rate 1.0
