# Pi 5 environment inspection — 2026-10-13

Scope: local, read-only inspection; only this report was written. No SSH, hardware execution, installation, service changes, commit or push. **No gate is promoted by this review.**
Mac provenance: branch `feat/d435i-camera-capture-20260913`, HEAD `5932457`; pre-existing modified/deleted/untracked files and dirty ORB-SLAM3 submodule were preserved.

Labels: **MEASURED** = output in `snapshot.txt`, limited to its sampled interval; **SOURCE-SUPPORTED** = repository documentation/historical evidence; **INFERRED** = interpretation or estimate; **UNKNOWN** = not established. User-supplied context is identified separately, never relabeled as a measurement.
Snapshot starts at 2026-10-13 04:19:52 UTC (11:19:52 +07), uptime 19 minutes. `snapshot.sh` was read, not executed; several searches use `head`/`tail` and are incomplete inventories.
SHA-256: `snapshot.txt` = `0558d8cef14d165de84a2043e24faf0e2e40a2e28303937fc15de8aab64385eb`; `snapshot.sh` = `7f77732f54e1f5fe429e4ae33452707fe103a56d60992aa0733e1ca7bc4dfce8`.

## 1. Environment against repository claims

| Item | Classification and observed state | Interpretation / source boundary |
|---|---|---|
| Host / OS / kernel | **MEASURED:** `wbr-pi5`, Pi 5 Model B Rev 1.0; Ubuntu 24.04.4 LTS, `6.8.0-1064-raspi`, aarch64, 4 CPUs. | Consistent with the native Ubuntu/Jazzy stack in `docs/PROJECT_STATE.md` and `docs/RPI5_NATIVE_PERCEPTION_BRINGUP.md`. |
| RAM | **MEASURED:** 3.9 GiB total, 3.6 GiB available, no swap. | **INFERRED:** 4 GB model, consistent with the user-reported temporary stand-in; `PROJECT_STATE.md` lists 8 GB. September evidence measured 7.8 GiB, so its memory/performance results cannot be transferred directly. |
| SDK / wrapper | **MEASURED:** installed ARM64 `ros-jazzy-librealsense2` `2.58.4-1noble.20260831.020056`; camera `4.58.4-1noble.20260902.181721`; messages `4.58.4-1noble.20260902.134137`. | **SOURCE-SUPPORTED:** September 13 physical `camera.log` reports wrapper/SDK 4.58.4/2.58.4. Installation exists; current binary loading/streaming is **UNKNOWN**. |
| SDK tools / Python | **MEASURED:** unsourced `rs-enumerate-devices` is not found; default Python 3.12.3 cannot import `pyrealsense2`. | **INFERRED:** likely ROS SDK tool PATH issue, not evidence that the installed C++ SDK is absent. **SOURCE-SUPPORTED:** SDK archive contains tools; experiments use C++ SDK utilities. Python binding absence does not itself block the C++ ROS driver. Sourced tool availability is **UNKNOWN**. |
| ROS / bags | **MEASURED:** `/opt/ros/jazzy`; ros-base 0.11.0, rosbag2 0.26.11, SQLite3/MCAP plugins, image transport, cv_bridge, tf2 and Fast DDS packages. Sourced package list finds camera/messages. | **MEASURED:** `AMENT_PREFIX_PATH=/opt/ros/jazzy`, discovery `SUBNET`; no RMW selection or domain appears in the filtered output. **UNKNOWN:** actual default middleware resolution and live graph. Future baseline explicitly uses domain 42 and localhost discovery. |
| USB / camera | **MEASURED:** only root hubs, including 5000M roots; no `8086:0b3a` camera. | Consistent with user context: camera unplugged. Root-hub speed does not qualify a camera cable/branch. Current camera identity, firmware and access are **UNKNOWN**. |
| udev / nodes | **MEASURED:** serial-specific USB/video/hidraw/IIO/custom-HID rules request `root:video 0660`, referencing `/usr/local/libexec/wbr-d435i-iio-permissions`. Only `/dev/video19`–`37` listed. | **SOURCE-SUPPORTED:** September report identifies these as Pi codec/ISP nodes. Rule text exists; current helper existence/hash/ownership, user groups, rule activation and reconnect permissions are **UNKNOWN**. No broad access is justified. |
| Camera identifiers | **SOURCE-SUPPORTED:** SDK device `243322073847`; ASIC `251843061466`; firmware-update ID `251843061466`; USB descriptor serial observed separately as `251843061466`; firmware `5.17.3.10`, BMI085. | Historical N1/N3 evidence only. udev matches descriptor ancestry, ROS selects SDK device serial; equal strings do not merge the fields. |
| Workspaces / source | **MEASURED:** `~/ros2_ws/src` empty; no build/install tree shown. Pi checkout `main...origin/main`, HEAD `5a2a7be`, differs from canonical Mac HEAD. ORB-SLAM3, its ROS wrapper and realsense-ros directories exist. | **MEASURED:** separate `~/wbr-runtime/wbr-runtime-20260913T055800Z` contains utilities/binaries/manifest/checksums. **UNKNOWN:** present checksums, build completeness and executable health. Empty colcon workspace does not block binary Jazzy packages or standalone utilities. Source/binary existence is not N4 evidence. |
| Storage | **MEASURED:** only 29.1 GiB `mmcblk0`, boot partition and 28.6 GiB ext4 root; `/` is `/dev/mmcblk0p2`, `rw,relatime`; `df` rounds to 10 GiB used / 17 GiB available. | Confirms user-reported nominal 32 GB microSD, no attached SSD/NVMe. `PROJECT_STATE.md` calls 128 GB NVMe and separate 64 GB USB storage targets, not measured installations. History of copying to `/dev/sda` is not a current mount. |
| Power / thermal / CPU | **MEASURED:** `throttled=0x50000`, 50.5°C, ARM ~1.8 GHz, CPU0 governor `ondemand`; low idle load. | **INFERRED:** latched undervoltage and throttling history, with current low bits clear. Idle temperature/load cannot qualify camera load. PSU/cable/cooling and event cause are **UNKNOWN**. |
| Clock | **MEASURED:** UTC/RTC agree at reported second; timezone +07, RTC UTC; clock synchronized `yes`, NTP `active`, timesyncd running. | Contradicts any claim that NTP was inactive at snapshot time. User-reported earlier ~3-day lag remains historical context. **UNKNOWN:** synchronization peer, age, offset, uncertainty and correction history; no camera clock measured. |

## 2. Documentation discrepancies

- **SOURCE-SUPPORTED / MEASURED:** `PROJECT_STATE.md` presents 8 GB hardware; snapshot has 3.9 GiB. Its storage targets are unattached, not qualified runtime storage. It leaves the verified gate and blocking question OPEN rather than supplying a current measured baseline.
- **SOURCE-SUPPORTED:** `NEXT_GATE.md` correctly leaves N3 OPEN, but its failure-class list is unresolved drafting. Evidence narrows this to live parameter-readback validation, an ARM parameter name difference, a hardware notification, and an incomplete retry; see section 5.
- **SOURCE-SUPPORTED / MEASURED:** `N3_PREPARATION.md` and the Phase A runbook say the wrapper was absent during takeover. Snapshot and September 13 static/physical receipts show it installed. Do not reinstall based on that historical paragraph.
- **SOURCE-SUPPORTED:** September 12 report says no completed 300-second soak / N3 not started for that session. Later `resume-20260913T055451Z/n2-accepted/result.json` records historical reviewed 20/105/300-second evidence, and two physical N3 attempt directories exist. Neither that receipt nor earlier N1 receipts qualify the changed October platform.
- **SOURCE-SUPPORTED:** `EVIDENCE_INDEX.md` contains placeholders; top-level September 13 `mission-status.json` predates the later N3 attempts. These are incomplete summaries, not proof that later work never happened.
- **INFERRED:** `NEXT_GATE.md` candidate criteria are less specific than the runbook: retain exact profile, full 60-second live observation, required context topics, strict timestamps/gaps, finalized counts/payload checks and isolated replay. A successful launch or `bag info` alone cannot qualify N3.

## 3. OS-course leftovers and measurement contamination

User context: `~/osbuild`, `~/heterogeneous-edge-ai-os`, `~/os-project-setup` were backed up and retained. Snapshot independently shows `osbuild/venv`, the custom unit/sudoers names and Wi-Fi setup history; it does not inventory all three trees or verify backups.

| Potential confounder | Evidence / does it matter? |
|---|---|
| CPU policy | **MEASURED:** CPU0 `ondemand`; no evidence of a current forced `performance` governor. **UNKNOWN:** other CPUs, policy limits, persistence or OS-course attribution. Frequency ramping can affect CPU/latency measurements; record the same policy for comparisons, do not silently change it. |
| LTTng | **MEASURED:** `lttng-sessiond.service` running. **UNKNOWN:** active tracing, buffers, consumers or output path. **INFERRED:** an idle session daemon may cost little; active tracing can consume CPU/RAM and compete with bag writes. Presence alone does not establish significant overhead. |
| Wi-Fi priority | **MEASURED:** `/etc/systemd/system/os-wifi-priority.service` exists; history invokes its installer. Not in running-service list. **UNKNOWN:** contents, enablement, oneshot execution, restart behavior and routes. **INFERRED:** route/Wi-Fi churn can disturb NTP/control traffic; even localhost ROS can see CPU/IRQ effects. Do not alter persistent networking here. |
| Sudoers | **MEASURED:** `os-project-agent` and `90-richard` exist in `/etc/sudoers.d`. **UNKNOWN:** effective privilege grants/content. **INFERRED:** files themselves have no measurement CPU cost; an authorized background agent could mutate governor/services/configuration. Do not infer unrestricted sudo or run camera code as root. |
| Other daemons | **MEASURED:** cron, snapd, unattended-upgrades, journald/rsyslog, ModemManager, NetworkManager, networkd and Wi-Fi services running. **UNKNOWN:** jobs/timers, active updates and process resource use. **INFERRED:** bursts/log writes can confound timing/storage; low idle load is insufficient. These services are not all attributable to the course project. |
| Packages / environments | **MEASURED:** retained venv paths, ROS-filtered package list and missing default `pyrealsense2`. **UNKNOWN:** full package inventory, apt history, tracing modules, shell startup exports and dependency modifications. **INFERRED:** dormant packages/folders usually matter through disk usage; activated venv/PATH/PYTHONPATH/LD_LIBRARY_PATH changes can select different tools/libraries. Use a fresh, explicitly sourced ROS shell. |
| Boot leftovers | **MEASURED:** UART/I2C/SPI enabled, `dwc2`, camera/display autodetection; `vmtoolsd.service` unit filename exists but is not listed running. **UNKNOWN:** provenance and actual VM-tools activity. These entries alone do not establish camera interference. |

Before a future measurement, inspect actual service definitions, tracing sessions, jobs, effective sudo policy and process load. Preserve folders/backups; do not uninstall or disable everything based on names.

## 4. Storage, power and timestamp risks

- **INFERRED:** exact baseline IR1 pixels alone are `640*480*15 = 4,608,000 B/s`: ~92 MB/20 s, ~276 MB/60 s, ~1.38 GB/300 s, ~16.59 GB/hour. IMU, context, serialization and filesystem overhead add to these lower bounds; other image profiles grow faster.
- **INFERRED:** rounded 17 GiB free corresponds to ~66 minutes of pixel-only recording if all free space were consumed, or ~27 minutes retaining 10 GiB headroom. Neither is a safe duration budget or throughput qualification; filling `/` endangers OS/log/evidence finalization. Do not redirect a missing external mount into a same-named microSD directory.
- **SOURCE-SUPPORTED:** `pi/storage-microsd/result.json` is a September 13 **bounded diagnostic** probe: 128 MiB / ~6.92 s, ~19.40 MB/s overall, ~16.87 MB/s worst batch, matching readback hashes. It explicitly grants no external-storage qualification. Same nominal card size does not prove same card or current sustained throughput after course work.
- **SOURCE-SUPPORTED:** `bounded_microsd.py` limits its exception to ≤60 s / ≤512 MiB and ≥8 GiB free with a valid probe receipt. This is not authorization for a new exception now. Large bags require separately qualified storage; no such attached storage is shown.
- **MEASURED / INFERRED:** `0x50000` sets historical bits 16 (undervoltage occurred) and 18 (throttling occurred); current undervoltage/frequency-cap/throttle bits are clear at that sample. It is not a current undervoltage reading, nor proof of a continuously clean boot. Event timing/severity and supply negotiation are unknown.
- **SOURCE-SUPPORTED:** N1 requires `throttled=0x0`; snapshot therefore does not satisfy that prerequisite. Preserve flags/logs and inspect PSU/cable/cooling before a separately authorized fresh interval; rebooting alone cannot establish that the cause was fixed.
- **INFERRED:** clock correction can step wall time and invalidate UTC ordering, durations derived from wall time or cross-host comparisons. Keep boot ID, monotonic time and raw device timestamp domains. No stepping/manual clock changes during capture. Host NTP does not establish camera–IMU alignment or ROS-header accuracy; never subtract uncharacterized clock domains.

## 5. First unresolved N3 condition and minimum discriminating test

Evidence base `E` below is repository-relative:
`experiments/2026-09-13-d435i-post-reboot-20260913T023833Z/resume-20260913T055451Z`.

1. **SOURCE-SUPPORTED:** `E/n3-physical-20260913T071621Z/result.json` stops at parameter readback, before live-rate observation/recording. It reports four missing keys: `depth_module.infra_profile`, `depth_module.infra1_format`, `pointcloud.enable`, `align_depth.enable`.
2. **SOURCE-SUPPORTED:** its saved dump actually contains the profile, Y8 and alignment value as nested YAML. `physical_session.py` passes that nested dictionary to a flat-key validator. Installed ARM readback declares `pointcloud__neon_.enable=false`, not `pointcloud.enable`. `camera.log` opens exactly IR1 Y8 640×480/15, accel/100, gyro/200.
3. **SOURCE-SUPPORTED:** raw `camera.log` also reports `Hardware Notification:Left MIPI error,...,Hardware Error`. Its automatic `faults: []` misses this; a clean automatic summary cannot override the raw warning. Calibration fallback warning also remains and blocks VIO qualification.
4. **SOURCE-SUPPORTED:** `E/n3-physical-20260913T072201Z/launch-receipt.json` records the flattening/ARM-name correction and negative gyro-rate regression. Local directory contains the corrected script/YAML but no result, camera log, publisher-ready, live metrics, finalized bag or replay evidence. **UNKNOWN:** outcome on the Pi; snapshot lists the directory, not its contents.

**First unresolved condition:** acceptance of the physical publisher's actual parameter/profile readback, with no serious hardware error. The first failure includes tooling mistakes; the later correction has no preserved live completion here. Do not claim a QoS/storage/replay failure when those stages were not reached in the complete attempt. Recover the Pi-only retry evidence in a separately authorized session before repeating hardware work.

Minimum camera-free discriminator (Mac, repo root; **saved physical input / offline tooling only**):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json, sys
from pathlib import Path
import yaml
sys.path.insert(0, 'experiments/2026-09-12-pi5-native-sensor-validation')
from wrapper_inspect import validate_readback
e = Path('experiments/2026-09-13-d435i-post-reboot-20260913T023833Z/resume-20260913T055451Z')
a = yaml.safe_load(json.loads((e/'n3-physical-20260913T071621Z/parameter-readback.json').read_text())['stdout'])['/camera/camera']['ros__parameters']
b = yaml.safe_load((e/'n3-physical-20260913T071621Z/requested-parameters.yaml').read_text())['/camera/camera']['ros__parameters']
c = yaml.safe_load((e/'n3-physical-20260913T072201Z/n3-baseline.yaml').read_text())['/camera/camera']['ros__parameters']
def flat(d, prefix=''):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict): out.update(flat(v, prefix+k+'.'))
        else: out[prefix+k] = v
    return out
print('original:', validate_readback(a, b))
print('flattened:', validate_readback(flat(a), b))
print('flattened ARM:', validate_readback(flat(a), c))
PY
```

Executed during this review: original gives those four errors; flattened gives only `pointcloud.enable`; flattened ARM gives `[]`. Decision: this saved failure is reproducible as a validator/name mismatch, not evidence that the three raw streams failed to open. This does not establish current live delivery or explain the MIPI notification.

If recovered retry evidence still leaves this unresolved, the minimum **future physical** test is one ≤30-second publisher/readback interval, without recording. Not executed or authorized by this report. Prerequisites: explicit `CAMERA AVAILABLE`, documented supply/cooling, clean power baseline, fresh N1 (camera branch ≥5000M and normal-user permissions), then reviewed N2 20/105/**300** s at the unchanged raw profile and thresholds. October's changed RAM/power state prevents reuse of September receipts.
Use the corrected historical YAML only after confirming its Pi hash equals `e84bfb0c2c61ab92dd4b3b5f6276de9ed134fe9e885772a59f1dda7c44508100`; mismatch/missing file → STOP. Do not launch the old recorder: canonical `n3_record.py` still uses nested dump comparison and the generic pointcloud baseline.

Future Pi terminal A, fresh ROS shell, normal user, after those prerequisites:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1
export WBR_DIAG="$HOME/wbr-evidence/n3-readback-$(date -u +%Y%m%dT%H%M%SZ)"
export WBR_PARAMS="$HOME/wbr-evidence/2026-09-13-d435i-post-reboot-20260913T023833Z/resume-20260913T055451Z/n3-physical-20260913T072201Z/n3-baseline.yaml"
sha256sum "$WBR_PARAMS"
# Inspect the hash before continuing; retain the existing YAML unchanged.
mkdir "$WBR_DIAG"
printf '%s\n' "$WBR_DIAG"
timeout --signal=INT --kill-after=5s 40s journalctl -k -f -n 0 --no-pager \
  -o short-monotonic > "$WBR_DIAG/kernel.log" 2>&1 &
WBR_KERNEL_PID=$!
(
  for WBR_SAMPLE in {1..40}; do
    date -u +%Y-%m-%dT%H:%M:%SZ
    vcgencmd get_throttled
    vcgencmd measure_temp
    sleep 1
  done
) > "$WBR_DIAG/power-temperature.log" 2>&1 &
WBR_HEALTH_PID=$!
timeout --signal=INT --kill-after=10s 30s ros2 run realsense2_camera realsense2_camera_node \
  --ros-args -r __ns:=/camera -r __node:=camera --params-file "$WBR_PARAMS" \
  > "$WBR_DIAG/camera.log" 2>&1
wait "$WBR_KERNEL_PID" "$WBR_HEALTH_PID"
```

Terminal B, same host/domain during that interval; paste the directory printed by A:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1
export WBR_DIAG=/absolute/directory/printed/by/terminal/A
ros2 node list --no-daemon > "$WBR_DIAG/nodes.txt"
ros2 param dump /camera/camera > "$WBR_DIAG/readback.yaml"
ros2 param get /camera/camera depth_module.infra_profile
ros2 param get /camera/camera depth_module.infra1_format
ros2 param get /camera/camera pointcloud__neon_.enable
ros2 param get /camera/camera align_depth.enable
```

Expected output from the four gets: `String value is: 640,480,15`, `String value is: Y8`, then `Boolean value is: False` twice. Full dump must match corrected YAML after flattening, with the disabled nonexistent `enable_infra` allowance only. Log must show the exact three profiles and retain calibration warnings. Monitor the three retained logs during the interval; unavailable journal access, nonzero power flags, temperature ≥80°C, forced kill, wrong/missing parameter, extra publisher/profile, MIPI/Hardware Error or new kernel fault → STOP, preserve evidence and distinguish hardware from readback tooling. Interrupt only this owned publisher on faults. Timeout normally returns 124: inspect normal SIGINT sensor close logs, not its exit status alone. The diagnostic's one-Hz power/temperature samples are limited checks, not the runbook's full qualification health metrics. Matching readback only permits the next live observation; it does not qualify N3, recording or replay. Qualified external storage remains necessary for large bags.

## 6. Not verified / review limitations

- **UNKNOWN:** current D435i serial/firmware/profile availability, camera USB speed/cable topology, loaded sensor drivers, reconnect permissions, helper integrity, video group membership or non-root streaming.
- **UNKNOWN:** present ROS graph, middleware selection, effective shell environments, parameter readback, topic names/types/QoS/rates/stamps/TF/context, live-versus-replay isolation, recorder shutdown and bag payload equality.
- **UNKNOWN:** second physical retry outcome or any physical bag on Pi. Snapshot's bag filename search shows no matches, but absence from that snapshot is not proof of a complete filesystem audit; local inspected attempts contain no bag/replay completion evidence.
- **UNKNOWN:** full OS-course package/service/sudo policy, active LTTng sessions, scheduled jobs, startup configuration, process CPU/RSS/I/O, directory sizes, backup integrity or provenance of all boot settings.
- **UNKNOWN:** PSU specification/negotiation/cable voltage, cooling setup, exact undervoltage timing/cause, behavior under load, microSD health/identity/endurance/current sustained write margin, or external-storage qualification.
- **UNKNOWN:** NTP peer/offset/last synchronization/time correction history and timestamp uncertainty across device/ROS/host clocks; historical ~3-day offset was not quantified by the snapshot.
- **UNKNOWN:** complete current build/dependency/linkage state, deployed bundle hash equality and ORB-SLAM3 algorithm/VIO performance. No build or hardware test was run; no current gate verdict follows.
- Validation performed: local document/evidence comparison, snapshot/source SHA-256, and the read-only offline saved-readback discriminator above. Offline results concern tooling only; historical evidence was left unchanged.
