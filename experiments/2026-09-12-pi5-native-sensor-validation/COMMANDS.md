# Commands and execution record

> **Phase A preparation update, 2026-09-12:** Commands below are an execution
> history, including old camera launches and a pending mount tied to the
> historical USB device. Do not rerun them as a present-session recipe.
> Use the [Phase A runbook](PHASE_A_RUNBOOK.md) after the user explicitly sends
> `CAMERA AVAILABLE`. Until then, run only the documented non-camera checks.
> A 300-second N2 soak is mandatory; the old "practical" qualification does
> not make it optional. Never substitute root-hub speed for the camera's own
> ≥5000M branch, broaden permissions to accommodate USB2, or reuse the old
> mount identity for the future NVMe. The Mac is canonical; transfer only
> verified first-party preparation artifacts to an isolated Pi runtime
> directory and preserve both checkouts. Historical manifest hashes describe
> the pre-preparation files; new runs must record the current artifact hashes.
> [EVIDENCE_RECONCILIATION.md](EVIDENCE_RECONCILIATION.md) records the audit and
> rollback boundary. No commit or push is authorized.

## Current cable revalidation — 2026-09-12 09:56–09:58 UTC

All commands in `usb-revalidation-20260912T095610Z/*-command.sh` were run
through `ssh -o BatchMode=yes -o ConnectTimeout=10 richard@wbr-pi5.local bash -s`.
Their paired `.txt` files retain full output, including SDK enumeration.
Commands inspect hardware/access only; no stream, mount, system edit,
package install, commit or push was performed. `sudo -n true` is an
authentication availability check only; no privileged mutation was requested.
The initial helper lookup used an incorrect `/usr/local/sbin` path; the
follow-up checks the installed rule's actual `/usr/local/libexec` path.

Current gate: **N1 REGRESSED / BLOCKED (480 Mb/s); N2 BLOCKED BY N1**.
Camera is at `4-1.1.2` behind two 480M hubs; the existing SDK collector must
not be started on this path. Profiles and acceptance limits are unchanged.

Next physical action: reconnect the D435i directly to a Pi USB 3 Type-A
port using the previous known-SuperSpeed A↔C cable, bypassing both hubs.
Resume with `lsusb`, `lsusb -t` and the camera's sysfs identity/speed, then
normal-user video/HID/IIO access and complete SDK enumeration. Expected:
actual camera branch ≥5000M, identifiers unchanged, device/control access
available without sudo. A 480M branch, missing serial, EACCES, reset or
re-enumeration leaves the relevant gate blocked.

The storage subtask is paused for manual authentication. Pending command
on the Pi (not executed):

```bash
sudo mount -t exfat -o uid=1000,gid=1000,umask=0022 /dev/sda1 /mnt/wbr-data
```

After the user runs it, verify `findmnt /mnt/wbr-data`,
`findmnt -T /mnt/wbr-data -o TARGET,SOURCE,FSTYPE,UUID,OPTIONS`,
`df -hT /mnt/wbr-data`, and normal-user writable access. Required source:
`/dev/sda1`, exFAT UUID `1017-F615`. Do not record if the source is microSD.

No build is required for these diagnostics. Once N1, permissions and mount
checks pass, reuse `run_sdk_capture.py` and `raw-profile.csv` with a **new**
output directory on the verified drive for smoke, ≥60-second validation,
and a practical 300-second soak. Retain existing 15/200/100 profiles and
rate/gap limits. Collect kernel and health evidence throughout. Analyze
counts, whole-window rates, separate repeated/backward timestamps and
maximum timestamp/arrival gaps including boundaries; verify clean startup
and shutdown. Historical timing results are not substitutes for these runs.

Documentation rollback: remove only the clearly marked resumed sections
from this file, README and the manager report; restore `manifest.json` from
`usb-revalidation-20260912T095610Z/manifest-before-resume.json` if needed.
Keep both old and new raw evidence intact. No runtime change needs rollback.

## Previous session commands retained below (historical)

Run location is explicit. Commands marked pending are not execution evidence.
Canonical experiment files are on the Mac feature branch. The Pi's repository
has a newer documentation commit and has not been edited.

## Completed before interruption (Pi via SSH)

The initial output was captured in the interactive session; the manager report
and manifest preserve those observations. It is not misrepresented as a saved
raw transcript. No repetition of this full inventory is required.

```bash
ssh -o BatchMode=yes -o ConnectTimeout=12 richard@wbr-pi5.local
date -u --iso-8601=seconds
hostname
id
uname -a
cat /etc/os-release
uptime
df -hT
lsblk -o NAME,PATH,TRAN,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS,MODEL
lsusb
lsusb -t
free -h
cat /proc/device-tree/model
cat /sys/class/thermal/thermal_zone0/temp
vcgencmd get_throttled
vcgencmd measure_temp
ls -l /dev/video* /dev/hidraw* /dev/iio*
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --all
ip -brief address
ip route
systemctl is-active ssh
timedatectl status
journalctl -k -b --no-pager -o short-iso
apt-cache policy ros-jazzy-librealsense2 ros-jazzy-realsense2-camera
apt-get -s --no-install-recommends install ros-jazzy-librealsense2 ros-jazzy-realsense2-camera ros-jazzy-realsense2-description
```

Also read camera sysfs identity/speed and IIO name/control attributes, current
package inventory and ROS prefixes. `sudo -n true` failed because a password
was required; `udisksctl mount --no-user-interaction -b /dev/sda1` failed due
to authentication. No sudo workaround was configured. The user subsequently
mounted `/dev/sda1` at `/mnt/wbr-data`.

## Completed after resumption

Mac, from repository root:

```bash
git status --short
git branch --show-current
git log --oneline -5
ssh richard@wbr-pi5.local python3 - < experiments/2026-09-12-pi5-native-sensor-validation/inspect_dependencies.py > experiments/2026-09-12-pi5-native-sensor-validation/dependency-costs.json
```

Pi, SDK archive inspection (download completed; not an installation):

```bash
cd /home/richard/wbr-sensor-validation-20260912/package-inspection
apt-get download ros-jazzy-librealsense2=2.58.4-1noble.20260831.020056
sha256sum *.deb
dpkg-deb -c *.deb
dpkg-deb -e *.deb control
cat control/control
```

Pi, storage and permission preview:

```bash
findmnt -rn -S /dev/sda1 -o SOURCE,FSTYPE,TARGET,OPTIONS
df -B1 -T /mnt/wbr-data
lsblk -o NAME,PATH,TRAN,SIZE,FSTYPE,UUID,MOUNTPOINTS,MODEL /dev/sda
python3 /home/richard/wbr-sensor-validation-20260912/wbr-d435i-iio-permissions.py /sys/bus/iio/devices/iio:device0
python3 /home/richard/wbr-sensor-validation-20260912/wbr-d435i-iio-permissions.py /sys/bus/iio/devices/iio:device1
udevadm verify /home/richard/wbr-sensor-validation-20260912/99-wbr-d435i.rules
udevadm trigger --dry-run --verbose --action=add --parent-match=/sys/bus/usb/devices/5-1
```

The storage operation checked UUID `1017-F615` and exFAT before creating only
the requested dated subdirectories and `metadata/write-access-check.txt`
(exclusive create; existing user files are not overwritten).

## Manual user setup — completed and verified on Pi

Only the following operations require interactive sudo authentication. They
install the SDK, install two new serial-specific permission files, reload
rules and apply them to the current camera subtree. They do not install the
ROS wrapper or description package. Keep the camera attached at its current
port while applying this session-specific trigger command.

```bash
sudo apt-get install --no-install-recommends ros-jazzy-librealsense2=2.58.4-1noble.20260831.020056
sudo install -D -o root -g root -m 0755 /home/richard/wbr-sensor-validation-20260912/wbr-d435i-iio-permissions.py /usr/local/libexec/wbr-d435i-iio-permissions
sudo install -D -o root -g root -m 0644 /home/richard/wbr-sensor-validation-20260912/99-wbr-d435i.rules /etc/udev/rules.d/99-wbr-d435i.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --action=add --settle --parent-match=/sys/bus/usb/devices/5-1
```

No logout is needed for current SSH sessions, which already include video.
A new login is needed only for an old shell whose `id` still omits video.

## Completed normal-user verification and stream procedure

```bash
source /opt/ros/jazzy/setup.bash
rs-enumerate-devices
rs-data-collect --help
```

Verified: SDK device serial 243322073847, ASIC/USB serial 251843061466, USB3, exact IR1/gyro/accel profiles. Check for
permission errors. Save the full output and actual library linkage.
Before measurement, start a continuous normal-user kernel follower:

```bash
journalctl -k -f -n 0 -o short-iso-precise
```

Capture its output to a unique file under the USB experiment's `logs/`.
Retain it from before startup until after orderly sensor shutdown, monitor
it during the run, and fail on camera USB reset/disconnect/re-enumeration.
Do not accept burst-only FPS: evaluate declared whole windows with both
internal and boundary gaps. The measured stream commands are below.

## Rollback (not executed)

Stop all sensor processes first. Remove only the newly created
`/etc/udev/rules.d/99-wbr-d435i.rules` and
`/usr/local/libexec/wbr-d435i-iio-permissions`, reload udev and physically
reattach this camera to restore default device/sysfs modes. Review apt's
transaction history before deciding which new packages to remove; do not
blindly autoremove. To remove the USB drive, finish writes and unmount it
through the user terminal. Preserve the experiment root and existing files.

## Live raw SDK tests

The first `sdk-smoke-01` matched all profiles but hit `Permission denied` on
custom-HID `enable_sensor` during shutdown. Its empty CSV cannot establish
counts/rates. The runner interrupted the child after detecting the error.
The user installed the updated helper/rule (same install paths as above),
reloaded udev and retriggered the camera. Normal-user inspection confirmed
that single custom-HID control became root:video 0660 before `sdk-smoke-02`.

Pi, via SSH from the Mac, after `source /opt/ros/jazzy/setup.bash`:

```bash
python3 /mnt/wbr-data/wbr-perception-phase1/2026-09-12/metadata/run_sdk_capture.py --config /mnt/wbr-data/wbr-perception-phase1/2026-09-12/metadata/raw-profile.csv --seconds 20 --output /mnt/wbr-data/wbr-perception-phase1/2026-09-12/raw/sdk-smoke-01
python3 /mnt/wbr-data/wbr-perception-phase1/2026-09-12/metadata/run_sdk_capture.py --config /mnt/wbr-data/wbr-perception-phase1/2026-09-12/metadata/raw-profile.csv --seconds 20 --output /mnt/wbr-data/wbr-perception-phase1/2026-09-12/raw/sdk-smoke-02
python3 /mnt/wbr-data/wbr-perception-phase1/2026-09-12/metadata/analyze_sdk_csv.py /mnt/wbr-data/wbr-perception-phase1/2026-09-12/raw/sdk-smoke-02/frames.csv --start 5 --duration 10 --output /mnt/wbr-data/wbr-perception-phase1/2026-09-12/metadata/smoke-02-analysis.json
python3 /mnt/wbr-data/wbr-perception-phase1/2026-09-12/metadata/run_sdk_capture.py --config /mnt/wbr-data/wbr-perception-phase1/2026-09-12/metadata/raw-profile.csv --seconds 105 --output /mnt/wbr-data/wbr-perception-phase1/2026-09-12/raw/sdk-sustained-01
```

The actual SDK argv and UTC interval are also in each run's `command.json`
and `capture-result.json`; the runner starts and stops its own journal
follower and records both `lsusb` and `lsusb -t` before and after. Its health
samples record temperature, throttling flags, MemAvailable, free storage,
system CPU deltas and `ps` process CPU/RSS. `ps %CPU` is a lifetime average
for that process; system CPU is a sample interval average across all cores.

Image-only content check, compiled using existing Pi g++ and SDK headers:

```bash
g++ -O2 -std=c++17 -Wall -Wextra /home/richard/wbr-sensor-validation-20260912/sample_ir.cpp -I/opt/ros/jazzy/include -L/opt/ros/jazzy/lib/aarch64-linux-gnu -Wl,-rpath,/opt/ros/jazzy/lib/aarch64-linux-gnu -lrealsense2 -o /home/richard/wbr-sensor-validation-20260912/sample_ir
/home/richard/wbr-sensor-validation-20260912/sample_ir 243322073847 /mnt/wbr-data/wbr-perception-phase1/2026-09-12/raw/ir-content-01
```

The invocation was bounded by Python `subprocess.run(..., timeout=25)` with
an owned journal follower covering the entire operation. Exact argv/UTC is
in `ir-content-command.json`. Compiler warnings came from installed SDK
headers and are retained in `custom-hid-fix-preview.txt`.

The 64 MiB storage write probe used 64 sequential 1 MiB buffered writes,
`flush()` and `os.fsync()`, SHA-256 readback, then removed only its own
exclusive-created `.wbr-sequential-write-*` file. Timing includes fsync;
readback may use cache. It ran separately from sensor streaming.
