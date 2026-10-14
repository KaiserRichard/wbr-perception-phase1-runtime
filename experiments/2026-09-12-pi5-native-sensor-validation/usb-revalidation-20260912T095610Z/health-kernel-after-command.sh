printf 'DIAGNOSTIC SNAPSHOT UTC\n'
date -u --iso-8601=seconds
printf '\nPI HEALTH (IDLE, NO STREAM)\n'
free -h
vcgencmd measure_temp
vcgencmd get_throttled
df -hT
python3 - <<'REMOTE_PY'
import time
from pathlib import Path

def cpu():
    values = [int(x) for x in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
    return sum(values), values[3] + values[4]
a=cpu()
t=time.monotonic()
time.sleep(2)
b=cpu()
print(f'cpu_interval_seconds={time.monotonic()-t:.6f}')
print(f'cpu_system_busy_percent={100*(1-(b[1]-a[1])/(b[0]-a[0])):.6f}')
print('loadavg=' + Path('/proc/loadavg').read_text().strip())
REMOTE_PY
printf '\nCURRENT STORAGE ACCESS (NO WRITES)\n'
findmnt -M /mnt/wbr-data -o TARGET,SOURCE,FSTYPE,UUID,OPTIONS
printf 'findmnt_exact_mount_exit=%s\n' "$?"
ls -ld /mnt/wbr-data
if test -w /mnt/wbr-data; then printf 'directory_writable=yes (NOT evidence of USB writability)\n'; else printf 'directory_writable=no\n'; fi
printf '\nEXPECTED USB DEVICE ATTRIBUTES\n'
lsblk -b -o NAME,SIZE,FSTYPE,UUID,MOUNTPOINTS /dev/sda
printf '\nKERNEL DURING CURRENT DIAGNOSTICS\n'
journalctl -k -b --since '2026-09-12 09:56:00 UTC' --no-pager -o short-iso-precise
printf '\nRECENT USB KERNEL HISTORY (SEPARATE FROM DIAGNOSTIC INTERVAL)\n'
journalctl -k -b --since '2026-09-12 09:40:00 UTC' --no-pager -o short-iso-precise --grep='usb|xhci|uvc|hid|iio|throttl|voltage|temperature'
printf '\nUSB AFTER DIAGNOSTICS\n'
lsusb
lsusb -t
for d in /sys/bus/usb/devices/*; do
    [ -f "$d/idVendor" ] || continue
    [ "$(cat "$d/idVendor")" = 8086 ] || continue
    [ "$(cat "$d/idProduct")" = 0b3a ] || continue
    printf 'SYSFS_PATH=%s\n' "$d"
    for f in busnum devnum devpath idVendor idProduct product serial speed bcdDevice; do
        if [ -f "$d/$f" ]; then printf '%s=%s\n' "$f" "$(cat "$d/$f")"; else printf '%s=ABSENT\n' "$f"; fi
    done
done
date -u --iso-8601=seconds
