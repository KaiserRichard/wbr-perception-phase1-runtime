#!/usr/bin/env bash
# Back up the whole F446 flash (read twice, must match), then write and verify an image.
# Usage: flash.sh <image.bin> <expected-sha256> <archive-dir>
# Uses tools/link_bench/pi/stm32boot.py (copied next to this script on the Pi).
# Stop the micro-ROS agent first. When it says "waiting for bootloader": FIRST fit BOOT0
# (CN7 pin 5 to 7), THEN press RESET. A running bench image prints the letter "y" (0x79),
# which the sync loop would take for a bootloader ACK.
# Options (environment):
#   MAGIC=1        send "BOOTLOADER" first: a running bench image (ver>=2) system-resets,
#                  which lands in the ROM bootloader when BOOT0 is fitted. No RESET press.
#   WAIT_SILENT=1  start the sync only after the line has been silent for 2 s, so binary
#                  output from a running app cannot fake an ACK; then press RESET (BOOT0 fitted).
set -euo pipefail
img=$1; want=$2; out=$3; port=${PORT:-/dev/ttyAMA0}
here=$(cd "$(dirname "$0")" && pwd)
got=$(sha256sum "$img" | cut -d' ' -f1)
[ "$got" = "$want" ] || { echo "REFUSE: $img sha256 $got != $want"; exit 2; }
if fuser "$port" >/dev/null 2>&1; then echo "REFUSE: $port is in use (stop the micro-ROS agent first)"; fuser -v "$port"; exit 2; fi
mkdir -p "$out"
python3 - "$port" "${MAGIC:-0}" "${WAIT_SILENT:-0}" <<'PY'
import sys, time, serial
port, magic, wait = sys.argv[1], sys.argv[2] == "1", sys.argv[3] == "1"
with serial.Serial(port, 115200, timeout=0.1) as s:
    if magic:
        for c in b"BOOTLOADER":  # 5 ms per byte: the app polls RX between I2C reads
            s.write(bytes([c])); s.flush(); time.sleep(0.005)
        print("magic sent", flush=True)
    if magic or wait:
        quiet_since = time.monotonic()
        while time.monotonic() - quiet_since < 2.0:
            if s.read(256): quiet_since = time.monotonic()
        print("line silent for 2 s", flush=True)
PY
python3 "$here/stm32boot.py" --port "$port" --out "$out" --flash "$img" --sync-seconds "${SYNC_SECONDS:-900}" 2>&1 | tee "$out/flash.log"
echo "image sha256 $got" | tee -a "$out/flash.log"
echo "Remove BOOT0, then press RESET."
