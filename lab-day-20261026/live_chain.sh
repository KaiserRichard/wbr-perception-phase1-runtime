#!/usr/bin/env bash
# Live D435 aligned depth -> Pi detector -> UART advisory. Run after sourcing Jazzy.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="${1:-$HOME/wbr-evidence/lab-day-20261026/LIVE-chain-$(date +%Y%m%d-%H%M%S)}"
port="${UART_PORT:-/dev/ttyAMA0}"
test ! -e "$out" || { echo "output exists: $out" >&2; exit 1; }
mkdir -p "$out"
command -v ros2 >/dev/null || { echo "source ROS 2 Jazzy before running this script" >&2; exit 1; }

ros2 launch realsense2_camera rs_launch.py \
  enable_color:=true enable_depth:=true enable_sync:=true \
  enable_infra1:=false enable_infra2:=false \
  align_depth.enable:=true depth_module.emitter_enabled:=1 \
  depth_module.depth_profile:=640x480x15 rgb_camera.color_profile:=640x480x15 \
  camera_name:=camera >"$out/camera.log" 2>&1 &
camera_pid=$!
stop_camera() {
  kill -INT "$camera_pid" 2>/dev/null || true
  wait "$camera_pid" 2>/dev/null || true
}
trap stop_camera EXIT INT TERM

topic=/camera/camera/aligned_depth_to_color/image_raw
ready=0
for _ in $(seq 1 90); do
  kill -0 "$camera_pid" 2>/dev/null || { echo "RealSense launch exited; see $out/camera.log" >&2; exit 1; }
  if ros2 topic list -t 2>/dev/null | grep -Fq "$topic [sensor_msgs/msg/Image]"; then ready=1; break; fi
  sleep 1
done
if [[ $ready != 1 ]]; then echo "timed out waiting for $topic; see $out/camera.log" >&2; exit 1; fi

if [[ "${RECORD:-0}" == 1 ]]; then
  # Colour + aligned depth for looking back at the run in Foxglove (MCAP, ~30 MB/s at 15 Hz).
  ros2 bag record -s mcap -o "$out/camera-bag" /camera/camera/color/image_raw /camera/camera/color/camera_info \
    /camera/camera/aligned_depth_to_color/image_raw /camera/camera/aligned_depth_to_color/camera_info /tf_static \
    >"$out/record.log" 2>&1 &
  record_pid=$!
  trap 'kill -INT "$record_pid" 2>/dev/null || true; wait "$record_pid" 2>/dev/null || true; stop_camera' EXIT INT TERM
fi
python3 "$repo/tools/link_bench/pi/advisory_link.py" --port "$port" --out "$out" --ros --duration "${DURATION:-60}" --max-forward "${MAX_FORWARD:-3.0}"
echo "live run complete: $out"
