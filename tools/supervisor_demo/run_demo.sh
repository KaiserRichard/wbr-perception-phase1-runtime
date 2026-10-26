#!/usr/bin/env bash
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
BAG=${1:-"$HOME/wbr-evidence/lab-day-20261025/3-box13/camera-bag"}
WS=${WS:-"$HOME/wbr-demo-ws-20261025"}
ROS_SETUP=${ROS_SETUP:-/opt/ros/jazzy/setup.bash}

if [[ ! -d "$BAG" ]]; then
  echo "Bag directory not found: $BAG" >&2
  exit 1
fi
if [[ ! -f "$ROS_SETUP" || ! -f "$WS/install/setup.bash" ]]; then
  echo "Missing ROS or demo workspace setup: $ROS_SETUP, $WS/install/setup.bash" >&2
  exit 1
fi

set +u  # ROS setup scripts read unset variables.
source "$ROS_SETUP"
source "$WS/install/setup.bash"
source "${UROS_WS:-$HOME/microros_ws}/install/local_setup.bash"  # micro_ros_agent
set -u
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

pids=()
stop_children() {
  local pid
  trap - EXIT INT TERM
  for pid in "${pids[@]}"; do kill -INT -- "-$pid" 2>/dev/null || true; done
  sleep 0.4
  for pid in "${pids[@]}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done
  for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done
}
trap stop_children EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

start_group() {
  setsid bash -c 'exec "$@"' _ "$@" &
  pids+=("$!")
}

start_group ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyAMA0 -b 115200
start_group ros2 run wbr_obstacle_node obstacle_node --ros-args \
  -p algo_path:="$ROOT" -p range_limit_m:=1.3
start_group python3 "$HERE/safety_filter.py"
start_group python3 "$HERE/drive_pattern.py"
if ros2 pkg prefix foxglove_bridge >/dev/null 2>&1; then
  start_group ros2 run foxglove_bridge foxglove_bridge --ros-args -p port:=8765
else
  echo "foxglove_bridge is not installed; continuing without Foxglove." >&2
fi

sleep 2
start_group ros2 bag play "$BAG" --rate 1.0
bag_pid=${pids[-1]}
wait "$bag_pid"
