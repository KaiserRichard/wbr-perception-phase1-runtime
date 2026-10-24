#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 RUN_DIR [SECONDS]" >&2
  exit 2
fi
RUN_DIR=$1
DURATION=${2:-90}
if ! [[ $DURATION =~ ^[0-9]+$ ]] || (( DURATION < 1 )); then
  echo "SECONDS must be a positive integer" >&2
  exit 2
fi
mkdir -p "$RUN_DIR"
RUN_DIR=$(cd "$RUN_DIR" && pwd)
if [[ -e "$RUN_DIR/bag" ]]; then
  echo "Refusing to record into existing bag path: $RUN_DIR/bag" >&2
  exit 1
fi
SCRIPT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CAMERA_SETUP=${CAMERA_SETUP:-/home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash}
PLANNER_SETUP=${PLANNER_SETUP:-/home/richard/wbr-demo-ws-20261024/install/setup.bash}
export WBR_REPO_ROOT=${WBR_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
ROS_SETUP=${ROS_SETUP:-/opt/ros/jazzy/setup.bash}
for setup in "$ROS_SETUP" "$CAMERA_SETUP" "$PLANNER_SETUP"; do
  if [[ ! -f $setup ]]; then
    echo "Missing setup file: $setup" >&2
    exit 1
  fi
done
# shellcheck disable=SC1090
source "$ROS_SETUP"
# shellcheck disable=SC1090
source "$CAMERA_SETUP"
# shellcheck disable=SC1090
source "$PLANNER_SETUP"
export PYTHONPATH="$SCRIPT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export ROS_DOMAIN_ID=201
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST

pids=()
labels=()
cleanup() {
  trap - INT TERM EXIT
  for pid in "${pids[@]}"; do kill -INT -- "-$pid" 2>/dev/null || true; done
  for pid in "${pids[@]}"; do
    for _ in {1..30}; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.2
    done
    kill -TERM -- "-$pid" 2>/dev/null || true
  done
  for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done
  if [[ -n ${monitor_pid:-} ]]; then
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
  fi
  echo "Stopped live path session at $(date -Is)" >> "$RUN_DIR/session.log"
}
trap cleanup INT TERM EXIT
start_job() {
  local label=$1 logfile=$2
  shift 2
  setsid "$@" >"$RUN_DIR/$logfile" 2>&1 &
  pids+=("$!")
  labels+=("$label")
  echo "Started $label pid=${pids[-1]} log=$RUN_DIR/$logfile" | tee -a "$RUN_DIR/session.log"
}

(
  while :; do
    printf '%s ' "$(date -Is)"
    if [[ -r /proc/stat && -r /proc/meminfo ]]; then
      awk '/^cpu / {printf "cpu_ticks="; for(i=2;i<=NF;i++) printf "%s%s",$i,(i==NF?" ":",")}' /proc/stat
      awk '/^MemAvailable:/ {printf "mem_available_kB=%s\n",$2}' /proc/meminfo
    else
      top -b -n 1 | head -5 | tr '\n' ' '
      printf '\n'
    fi
    sleep 1
  done
) >"$RUN_DIR/cpu.log" 2>&1 &
monitor_pid=$!

start_job camera camera.log ros2 launch wbr_orb_node d435_camera.launch.py mode:=rgbd serial:=317422076650 width:=640 height:=480 fps:=15
sleep 2
start_job slam slam.log ros2 launch wbr_orb_node d435_slam.launch.py mode:=rgbd vocabulary:=/home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt settings:=/home/richard/wbr-evidence/mobile-demo-20261024-01/setup/rgbd-ros-15fps.yaml
pose_ready=0
for _ in {1..90}; do
  if timeout 1s ros2 topic echo --once /d435_orb/pose >/dev/null 2>&1; then pose_ready=1; break; fi
  sleep 1
done
if (( ! pose_ready )); then
  echo "Timed out waiting for /d435_orb/pose; inspect $RUN_DIR/slam.log" | tee -a "$RUN_DIR/session.log" >&2
  exit 1
fi
start_job planner planner.log ros2 launch wbr_planner_node planner.launch.py
start_job foxglove foxglove.log ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765
start_job bag bag.log ros2 bag record --storage sqlite3 --output "$RUN_DIR/bag" --topics \
  /camera/camera/aligned_depth_to_color/image_raw \
  /camera/camera/color/image_raw \
  /camera/camera/color/camera_info \
  /camera/camera/depth/camera_info \
  /d435_orb/pose /d435_orb/status \
  /wbr_planner_node/suggestion /wbr_planner_node/markers

echo "Live planner running for ${DURATION}s; Foxglove bridge port 8765" | tee -a "$RUN_DIR/session.log"
for ((elapsed=0; elapsed<DURATION; elapsed++)); do sleep 1; done
