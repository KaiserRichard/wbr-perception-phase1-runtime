#!/usr/bin/env bash
# End-to-end replay on the Pi: recorded 24 Oct bags -> advisory_link.py --ros (the LIVE chain)
# -> TerrainAdvisory over UART 460800 -> Nucleo link_bench LED image -> AdvisoryEcho.
# Run on the Pi (ssh wbr-pi5), one mode at a time:
#   e2e_led_replay.sh led      back up the Nucleo flash, write the LED image bf5721b4, start it (GO)
#   e2e_led_replay.sh replay   replay B-H13, B-H05, S1-empty for 20 s each; print sent/echoed per run
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
    (cd "$REPO" && python3 tools/link_bench/pi/advisory_link.py --port "$PORT" --out "$run" --ros \
       --duration "${SECONDS_PER_BAG:-20}" --max-forward 3.0) > "$run.log" 2>&1 || echo "advisory_link exit $? for $b (see $run.log)"
    kill "$play" 2>/dev/null || true; wait "$play" 2>/dev/null || true
    python3 - "$run" "$b" <<'PY'
import csv, json, sys, collections, pathlib
d = pathlib.Path(sys.argv[1]); rows = list(csv.DictReader(open(d / "packets.csv")))
s = json.loads((d / "summary.json").read_text())
names = {"0": "NONE", "1": "JUMP", "2": "STOP", "3": "UNCERTAIN"}
sent = collections.Counter(names.get(r["advisory"], r["advisory"]) for r in rows)
echo_ok = sum(1 for r in rows if r["echo_result"] == "0")
keys = ("frames", "sent", "echoed", "loss", "rejected_echoes", "mcu_accepted_count", "mcu_rejected_count", "stale_events", "unmatched_echoes")
print(f"{sys.argv[2]}: advisories sent {dict(sent)}; echoes accepted {echo_ok}/{len(rows)}; " + ", ".join(f"{k}={s.get(k)}" for k in keys))
PY
  done
}

case $mode in
  led) flash "$LED_IMG" "$LED_SHA" led ;;
  replay) replay ;;
  restore) flash "$CANFIX05_IMG" "$CANFIX05_SHA" canfix05 ;;
  *) sed -n 2,11p "$0"; exit 2 ;;
esac
