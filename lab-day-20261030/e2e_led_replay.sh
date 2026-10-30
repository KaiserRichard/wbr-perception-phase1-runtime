#!/usr/bin/env bash
# End-to-end replay on the Pi: recorded 24 Oct bags -> advisory_link.py --ros (the LIVE chain)
# -> TerrainAdvisory over UART 460800 -> Nucleo link_bench LED image -> AdvisoryEcho.
# Run on the Pi (ssh wbr-pi5), one mode at a time:
#   e2e_led_replay.sh led      back up the Nucleo flash, write the LED image bf5721b4, start it (GO)
#   e2e_led_replay.sh replay --live-uart-confirmed  confirm LED bf5721b4 and BOOT0 removed interactively
#   e2e_led_replay.sh restore  back up, then write canfix05 13279727 back and start it (GO)
# led/restore need the ROM bootloader: with BOOT0 fitted, press RESET when it says "waiting".
# A running canfix05 image has no software reset, so that one press cannot be avoided.
# Env: PORT (default /dev/ttyAMA0), OUT (default ~/wbr-evidence/e2e-replay-20261030), SECONDS_PER_BAG (20).
set -euo pipefail
mode=${1:-}
PORT=${PORT:-/dev/ttyAMA0}
OUT=${OUT:-$HOME/wbr-evidence/e2e-replay-20261030}
BENCH=$HOME/imu-can-bench
REPO=${REPO:-$HOME/wbr-demo-20261026}
LED_IMG=$BENCH/link_bench_f446.bin
LED_SHA=bf5721b44c0d9eafa4b5b53fb75f1ceec8c6e3c72a0c81d5a6bfd7635fe003ed
CANFIX05_IMG=$BENCH/agv_f446_home_canfix05_500k.bin
CANFIX05_SHA=13279727ab597f5e777699b1e744e801ffbf7a3cfbeefc9ae744df571621b9ed
BAGS=${BAGS:-"B-H13 B-H05 S1-empty"}
mkdir -p "$OUT"

flash() {  # flash IMAGE SHA TAG: double read-back backup, erase, write, verify, GO (stm32boot.py)
  local img=$1 sha=$2 dir=$OUT/flash-$3-$(date +%H%M%S)
  [ "$(sha256sum "$img" | cut -d' ' -f1)" = "$sha" ] || { echo "REFUSE: $img is not $sha"; exit 2; }
  pkill -f "micro_ros_agent serial" 2>/dev/null || true
  if fuser "$PORT" >/dev/null 2>&1; then echo "REFUSE: $PORT in use"; fuser -v "$PORT"; exit 2; fi
  echo "waiting for the ROM bootloader: with BOOT0 fitted, press RESET on the Nucleo now"
  (cd "$BENCH" && python3 flash_safe.py --port "$PORT" --out "$dir" --flash "$img" --sync-seconds "${SYNC_SECONDS:-600}") 2>&1 \
    | grep -avE '^\s+read' | tee "$dir.console"
  grep -q "verify True" "$dir.console" && grep -q "started new firmware" "$dir.console" \
    || { echo "FAIL: flash of $3 not verified/started; backup (if any) in $dir"; exit 1; }
  echo "OK: $3 written, verified and started; previous flash backed up in $dir/flash-backup.bin"
}

replay() {
  local resolved_port confirmation failed=0
  if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != --live-uart-confirmed ]; }; then
    echo "REFUSE: replay accepts only the optional --live-uart-confirmed flag"
    return 2
  fi
  resolved_port=$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$PORT")
  # Simulator PTYs need no hardware confirmation. All other ports fail closed,
  # including aliases/symlinks to real UARTs.
  if [[ ! "$resolved_port" =~ ^/dev/pts/[0-9]+$ && ! "$resolved_port" =~ ^/dev/ttys[0-9]+$ ]]; then
    if [ "${1:-}" != --live-uart-confirmed ]; then
      echo "REFUSE: real-UART replay on $PORT requires --live-uart-confirmed and interactive confirmation of LED link-bench bf5721b4 with BOOT0 removed"
      return 2
    fi
    if [ ! -t 0 ]; then
      echo "REFUSE: real-UART replay requires an interactive terminal to confirm LED link-bench bf5721b4 is running and BOOT0 is removed"
      return 2
    fi
    echo "Confirm the LED link-bench image (SHA starting bf5721b4) is running and BOOT0 is removed."
    if ! read -r -p 'Type "CONFIRM bf5721b4 BOOT0 removed": ' confirmation || [ "$confirmation" != 'CONFIRM bf5721b4 BOOT0 removed' ]; then
      echo "REFUSE: LED link-bench bf5721b4 running and BOOT0 removed were not confirmed"
      return 2
    fi
  fi
  set +u; source /opt/ros/jazzy/setup.bash; set -u
  export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-79} ROS_LOCALHOST_ONLY=1
  if fuser "$PORT" >/dev/null 2>&1; then echo "REFUSE: $PORT in use"; fuser -v "$PORT"; exit 2; fi
  for b in $BAGS; do
    local bag=$HOME/wbr-evidence/mobile-demo-20261024-01/$b/rgbd-bag run=$OUT/replay-$b-$(date +%H%M%S)
    timeout $(( ${SECONDS_PER_BAG:-20} + 15 )) ros2 bag play "$bag" --loop --topics \
      /camera/camera/aligned_depth_to_color/image_raw /camera/camera/aligned_depth_to_color/camera_info \
      /camera/camera/color/camera_info >/dev/null 2>&1 &
    local play=$!
    sleep 2
    local advisory_status=0
    (cd "$REPO" && python3 tools/link_bench/pi/advisory_link.py --port "$PORT" --out "$run" --ros \
       --duration "${SECONDS_PER_BAG:-20}" --max-forward 3.0) > "$run.log" 2>&1 || advisory_status=$?
    kill "$play" 2>/dev/null || true; wait "$play" 2>/dev/null || true
    # Preserve every run's artifacts and attempt the remaining bags on failure.
    python3 - "$run" "$b" "$advisory_status" <<'PY' || failed=1
import csv, json, sys, collections, pathlib
d = pathlib.Path(sys.argv[1]); rows = []; s = {}; errors = []
try:
    s = json.loads((d / "summary.json").read_text())
    with (d / "packets.csv").open() as f:
        rows = list(csv.DictReader(f))
except (OSError, ValueError) as exc:
    errors.append(f"cannot read run artifacts: {exc}")
names = {"0": "NONE", "1": "JUMP", "2": "STOP", "3": "UNCERTAIN"}
sent = collections.Counter(names.get(r.get("advisory"), r.get("advisory")) for r in rows)
echo_ok = sum(1 for r in rows if r["echo_result"] == "0")
keys = ("frames", "sent", "echoed", "loss", "rejected_echoes", "mcu_accepted_count", "mcu_rejected_count", "stale_events", "unmatched_echoes")
print(f"{sys.argv[2]}: advisories sent {dict(sent)}; echoes accepted {echo_ok}/{len(rows)}; " + ", ".join(f"{k}={s.get(k)}" for k in keys))
if int(sys.argv[3]):
    errors.append(f"advisory_link.py exited {sys.argv[3]} (see {d}.log)")
if not isinstance(s.get("sent"), int) or s["sent"] <= 0:
    errors.append("sent must be greater than zero")
if s.get("echoed") != s.get("sent") or "echoed" not in s:
    errors.append("echoed must equal sent")
if s.get("rejected_echoes") != 0 or s.get("mcu_rejected_count", 0) != 0 or any(r["echo_result"] not in ("", "0") for r in rows):
    errors.append("echo rejection detected or rejection count unavailable")
for error in errors:
    print(f"FAIL: {error}")
sys.exit(bool(errors))
PY
  done
  return "$failed"
}

case $mode in
  led) flash "$LED_IMG" "$LED_SHA" led ;;
  replay) replay "${@:2}" ;;
  restore) flash "$CANFIX05_IMG" "$CANFIX05_SHA" canfix05 ;;
  *) sed -n 2,11p "$0"; exit 2 ;;
esac
