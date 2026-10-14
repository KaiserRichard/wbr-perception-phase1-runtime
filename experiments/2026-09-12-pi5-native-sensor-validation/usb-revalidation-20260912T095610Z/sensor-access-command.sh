date -u --iso-8601=seconds
id
printf '\nVIDEO MODES\n'
ls -l /dev/video*
printf '\nHID MODES\n'
ls -l /dev/hidraw* 2>/dev/null
printf '\nIIO EXPOSURE\n'
for d in /sys/bus/iio/devices/iio:device*; do
    [ -e "$d" ] || continue
    printf '=== %s ===\n' "$d"
    cat "$d/name"
    readlink -f "$d"
done
ls -l /dev/iio:* 2>/dev/null
printf '\nNONROOT DEVICE OPEN / CONTROL ACCESS (NO STREAMING OR CONTROL WRITES)\n'
python3 - <<'REMOTE_PY'
import os
from pathlib import Path
usb = Path('/sys/bus/usb/devices/4-1.1.2').resolve()
for group in ('video4linux/video*', 'hidraw/hidraw*', 'iio/iio:device*'):
    for p in sorted(Path('/sys/class').glob(group)):
        if not p.resolve().is_relative_to(usb):
            continue
        node = Path('/dev') / p.name
        try:
            fd = os.open(node, os.O_RDWR | os.O_NONBLOCK)
            os.close(fd)
            print(str(node) + ': OPEN_RDWR_OK')
        except OSError as e:
            print(str(node) + ': ' + str(e))
for d in sorted(Path('/sys/bus/iio/devices').glob('iio:device*')):
    paths = list(d.glob('scan_elements/*_en')) + list(d.glob('buffer/*')) + list(d.glob('*sampling_frequency')) + list(d.glob('*hysteresis')) + list(d.glob('trigger/current_trigger'))
    for p in sorted(paths):
        if p.is_file():
            print(f'{p}: read={os.access(p, os.R_OK)} write={os.access(p, os.W_OK)} mode={oct(p.stat().st_mode & 0o777)} uid={p.stat().st_uid} gid={p.stat().st_gid}')
for p in usb.rglob('enable_sensor'):
    print(f'{p}: read={os.access(p, os.R_OK)} write={os.access(p, os.W_OK)}')
REMOTE_PY
printf '\nV4L2 QUERY\n'
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --all
printf '\nDEVICE OWNERS\n'
fuser -v /dev/video* /dev/hidraw* /dev/iio:* 2>&1
printf '\nSDK PACKAGE\n'
dpkg-query -W -f='${Package} ${Version} ${Architecture}\n' ros-jazzy-librealsense2
printf '\nPI REPOSITORY (READ ONLY)\n'
git -C /home/richard/wbr-perception-phase1-runtime status --short
git -C /home/richard/wbr-perception-phase1-runtime branch --show-current
git -C /home/richard/wbr-perception-phase1-runtime log --oneline -5
printf '\nSDK FULL ENUMERATION FOLLOWS IN SEPARATE CAPTURE\n'
