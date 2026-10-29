#!/usr/bin/env bash
# Back up the whole F446 flash (read twice, must match), then write and verify an image.
# Usage: flash.sh <image.bin> <expected-sha256> <archive-dir>
# Uses tools/link_bench/pi/stm32boot.py (copied next to this script on the Pi).
# If the bench firmware is running it is sent "BOOTLOADER" first, so BOOT0 is not needed;
# otherwise fit BOOT0 (CN7 pin 5 to 7) and press RESET when asked.
set -euo pipefail
img=$1; want=$2; out=$3; port=${PORT:-/dev/ttyAMA0}
here=$(cd "$(dirname "$0")" && pwd)
got=$(sha256sum "$img" | cut -d' ' -f1)
[ "$got" = "$want" ] || { echo "REFUSE: $img sha256 $got != $want"; exit 2; }
if fuser "$port" >/dev/null 2>&1; then echo "REFUSE: $port is in use (stop the micro-ROS agent first)"; fuser -v "$port"; exit 2; fi
mkdir -p "$out"
python3 - "$port" <<'PY'
import sys, time, serial
with serial.Serial(sys.argv[1], 115200, timeout=0.2) as s:
    s.write(b"BOOTLOADER\n"); s.flush(); time.sleep(0.3)
    print("magic sent; reply:", s.read(64).decode("ascii", "replace").strip() or "(none)")
PY
sleep 0.5
python3 "$here/stm32boot.py" --port "$port" --out "$out" --flash "$img" --sync-seconds "${SYNC_SECONDS:-180}" 2>&1 | tee "$out/flash.log"
echo "image sha256 $got" | tee -a "$out/flash.log"
echo "Remove BOOT0 if fitted, then press RESET."
