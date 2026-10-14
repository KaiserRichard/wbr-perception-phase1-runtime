date -u --iso-8601=seconds
printf '\nCURRENT PLATFORM / BOOT\n'
uname -a
cat /etc/os-release
cat /proc/device-tree/model
printf '\n'
uptime -s
cat /proc/sys/kernel/random/boot_id
timedatectl status
printf '\nINSTALLED CAMERA RULE / HELPER (READ ONLY)\n'
ls -l /etc/udev/rules.d/99-wbr-d435i.rules /usr/local/sbin/wbr-d435i-iio-permissions.py
sha256sum /etc/udev/rules.d/99-wbr-d435i.rules /usr/local/sbin/wbr-d435i-iio-permissions.py
cat /etc/udev/rules.d/99-wbr-d435i.rules
printf '\nIIO NONROOT OPEN CHECK (NO STREAMING)\n'
python3 - <<'REMOTE_PY'
import os
from pathlib import Path
for d in sorted(Path('/sys/bus/iio/devices').glob('iio:device*')):
    node=Path('/dev') / d.name
    try:
        fd=os.open(node, os.O_RDWR | os.O_NONBLOCK)
        os.close(fd)
        print(f'{node}: OPEN_RDWR_OK')
    except OSError as e:
        print(f'{node}: {e}')
REMOTE_PY
printf '\nUSB DESCRIPTORS (NO SUDO)\n'
lsusb -v -d 8086:0b3a
printf '\nCURRENT BOOT CAMERA / USB / POWER KERNEL ENTRIES\n'
journalctl -k -b --no-pager -o short-iso-precise --grep='usb|xhci|uvc|hid|iio|throttl|voltage|temperature'
date -u --iso-8601=seconds
