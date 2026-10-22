# WBR Lab Day Execution — 2026-10-22

**Purpose:** collect short stereo datasets on the Pi, validate each immediately,
and retain an offline ORB sparse-map sample for Foxglove. This is an operator
checklist, not a software-build plan.

Status labels include today's read-only Pi preflight (2026-10-22); recorded
capture and replay results remain dated to the runs that produced them. Recheck
before capture if power, USB, storage, or networking changes. **Do not rebuild,
install packages, change camera calibration, or touch motors/STM32 during this
session.**

## 1. Readiness before leaving

| Item | Evidence/status |
|---|---|
| Pi and SSH | **VERIFIED 2026-10-22:** Mac `en7=192.168.50.1`, `wbr-pi5=192.168.50.2`; bounded SSH succeeded. Pi identity is `wbr-pi5`, `aarch64`, Ubuntu 24.04.4, 3.9 GiB RAM. |
| Camera and software prerequisites | **VERIFIED 2026-10-22:** D435i serial `317422076650`, firmware `5.17.3.10`, enumerated at USB `5000M`; ROS executables and expected runner/settings/vocabulary/map replay paths are present. Enumeration does not establish an active camera stream or current ORB tracking. |
| Sensor recording | **VERIFIED:** 150.1 s, 1.3 GiB, 2,215 left/right image pairs and CameraInfo each; headers matched and the existing quality checker reported zero estimated gaps. One successful run is not a general storage qualification. |
| Sparse ORB landmarks from a recorded stereo MCAP | **VERIFIED for first 20 source seconds only:** Pi replay produced a separate MCAP with 20/20 nonempty actual `PointCloud2` snapshots, up to 965 landmarks, finite float32 XYZ in `slam_world`. Full-duration replay/export is **UNVERIFIED**. |
| PLY export | **BLOCKED/not implemented.** The verified artifact is ROS `PointCloud2` in a separate MCAP. |
| Foxglove | Local MCAP is a supported data source ([official instructions](https://docs.foxglove.dev/docs/visualization/connecting/local-data)); this feature's cloud was validated from MCAP data, but its appearance in the GUI has not yet been checked. |

The direct Ethernet SSH path worked during today's check. If it becomes
unreachable before capture, stop at preflight and fix power/network physically;
do not start with unverified launch commands.

## 2. Preflight — check before capture

### [MAC] Confirm SSH and inspect the Pi — **VERIFIED 2026-10-22; rerun before capture if the connection changes**

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o ConnectionAttempts=1 \
  -o StrictHostKeyChecking=yes wbr-pi5 \
  'hostname; uname -m; . /etc/os-release; echo "$PRETTY_NAME"; free -h; df -h /'
```

Expected identity: `wbr-pi5`, `aarch64`, Ubuntu 24.04, Pi 5 with about 4 GiB
RAM. Today's bounded SSH check returned `wbr-pi5`, `aarch64`, Ubuntu 24.04.4,
3.9 GiB RAM, and 80 GiB free on `/`.

### [PI] Power, temperature and USB — **read-only; last checked 2026-10-22**

```bash
set +u # ROS setup scripts expect some environment variables to be unset.
vcgencmd pmic_read_adc EXT5V
vcgencmd get_throttled
vcgencmd measure_temp
lsusb -t
source /opt/ros/jazzy/setup.bash
rs-enumerate-devices -s
```

Today's values: `EXT5V_V=5.16704000V`, `throttled=0x0`, temperature `51.0'C`;
D435i serial `317422076650` enumerated on a `5000M` link. Recheck if the supply,
USB cable, or port changes. Use the Pi's 27 W supply and a blue USB 3 port.
Confirm D435i serial `317422076650` and `5000M` in `lsusb -t`. **Stop/reseat power or cable and
repeat preflight** if the camera is missing, USB is below `5000M`, or the Pi
reports current throttling/undervoltage. A latched historical throttle bit is a
review signal; retain its raw value rather than clearing it.

### [PI] Storage — **read-only; verified 2026-10-22**

```bash
df -h / /home/richard/wbr-evidence
findmnt -T /home/richard/wbr-evidence
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT
```

The current check found the evidence path on `/dev/mmcblk0p2`, 113 GiB root with
80 GiB free. A prior 150 s run wrote 1.3 GiB; the planned captures total 145 s,
so use **3 GiB free** as a conservative space reserve for today's planned sensor
data, derived map bags, and logs. This is a planning margin, not a sustained-write
qualification or a guarantee. Do **not** run `dd`, `fio`, or a write benchmark.
If the evidence path is not on the expected root or less than 3 GiB is free,
stop before capture.

### [PI] ROS and runner prerequisites — **verified 2026-10-22; recheck before capture**

```bash
set +u # ROS setup scripts expect some environment variables to be unset.
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
set -eo pipefail
printf 'ROS_DISTRO=%s ROS_DOMAIN_ID=%s\n' "$ROS_DISTRO" "${ROS_DOMAIN_ID:-unset}"
ros2 pkg executables wbr_orb_node
test -r /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py || { echo "Missing verified capture runner" >&2; exit 1; }
test -r /home/richard/wbr-camera-native-20261021/settings/stereo-15fps-800features.yaml || { echo "Missing verified stereo settings" >&2; exit 1; }
test -r /home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt || { echo "Missing ORB vocabulary" >&2; exit 1; }
```

If any `test` fails, **do not build or improvise at the lab**. Preserve the
output and stop. Today's check found both ROS executables and all listed files.
This does not mean a camera node or SLAM process is currently running. Do not
enable Bash `nounset` (`set -u`) before sourcing ROS setup; its setup script
expects some variables to be unset.

The sparse-map install and replay helper were separately verified at:

```text
/home/richard/wbr-orb-map-points-20261021-01/install/wbr_orb_node/lib/wbr_orb_node/d435_node
/home/richard/wbr-orb-map-points-20261021-01/source/ros2/wbr_orb_node/tests/replay_map_points.py
```

Check them without changing anything before relying on the map replay:

```bash
test -x /home/richard/wbr-orb-map-points-20261021-01/install/wbr_orb_node/lib/wbr_orb_node/d435_node || { echo "Missing verified sparse-map node" >&2; exit 1; }
test -r /home/richard/wbr-orb-map-points-20261021-01/source/ros2/wbr_orb_node/tests/replay_map_points.py || { echo "Missing verified map replay helper" >&2; exit 1; }
```

These files were rechecked on 2026-10-22. No camera stream, new capture, or
offline replay was started during today's preflight.

## 3. Capture with the existing runner

The successful capture used the session runner archived on the Pi at
`/home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py`.
Use this exact verified copy; the retained top-level `capture_loop.py` is an
older recorder/best-effort configuration. The verified runner launches
the existing stereo camera and ORB nodes, waits for an actual pose before
recording, writes a new MCAP, then stops its own recorder/SLAM/camera process
groups and saves a capture summary. It uses D435i `317422076650`, stereo
640×480 at 15 Hz and the saved 800-feature settings. The script supports 1–180 s.

**[PI] Runner behavior VERIFIED; exact shell invocation reconstructed from its
saved argument interface (the command line itself was not retained).** The
archived script sets its child processes to ROS domain 201 / localhost and copies
the verified stereo settings into each run as `stereo.yaml`. It creates the final
output directory exclusively; the parent must exist and the run path must not.

```bash
set +u # ROS setup scripts expect some environment variables to be unset.
source /opt/ros/jazzy/setup.bash
set -eo pipefail
RUNROOT="$HOME/wbr-evidence/camera-day-20261022-01"
mkdir "$RUNROOT"

# A — stationary baseline, 25 s
python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py \
  "$RUNROOT/A-stationary" 25
```

Run one scenario, validate it in Section 5, then decide whether to continue.
Do not paste all three commands as a batch. For live CLI inspection from a
second Pi terminal, use the same isolated ROS domain as the runner:

```bash
set +u # ROS setup scripts expect some environment variables to be unset.
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=201 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
ros2 topic list
ros2 topic echo /d435_orb/status --once
ros2 topic echo /d435_orb/pose geometry_msgs/msg/PoseStamped --once
```

The runner's archived source sets the child-process environment to domain 201.
The second-terminal topic-list/echo sequence is an **optional, UNVERIFIED**
diagnostic for today; skip it if discovery does not work rather than changing
the runner. An optional live rate check is also **UNVERIFIED**:

```bash
ros2 topic hz /camera/camera/infra1/image_rect_raw --window 15
```

The runner records only left/right IR images and CameraInfo in the sensor MCAP;
it does not record every live pose/status message. The pre-recording pose check
and `slam.log` prove initialization/startup, not uninterrupted tracking for the
whole capture.

**Safe stop:** let the requested duration finish. If stopping early, press
Ctrl-C once in the runner terminal and wait for `capture_summary.json`. If
recording had started, also wait for the sensor bag metadata to finish. If the
runner was still waiting for the first pose, no sensor bag is expected; retain
the summary/logs and do not wait for bag metadata. Do not kill ROS processes
globally or remove partial runs.

## 4. Three short scenarios

Total image-recording time is 145 s, within the runner's 180 s per-run limit.
Each run has its own output directory. Keep the D435i mount fixed; move the
robot/camera smoothly by hand only if the cart is safe to move. Do not command
motors.

| Run | Duration | Motion / operator note |
|---|---:|---|
| A — `A-stationary` | 25 s | Robot still; stable lighting and textured desk scene. Record if the image is blank, occluded, or visibly frozen. |
| B — `B-slow-sweep` | 75 s | Slow sweep around the desk with overlapping views; avoid abrupt turns. Note start/end viewpoint and tracking symptoms. |
| C — `C-return-sweep` | 45 s | Moderate but controlled sweep with overlapping views; return near the starting viewpoint. Note physical alignment as operator-reported, not ground truth. |

After A passes Section 5, run B:

```bash
set -eo pipefail
python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py \
  "$RUNROOT/B-slow-sweep" 75
```

After B passes Section 5, run C:

```bash
set -eo pipefail
python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py \
  "$RUNROOT/C-return-sweep" 45
```

Keep handwritten notes in a new file under `$RUNROOT` after each capture:
motion, lighting, obstacles/occlusion, mount movement, and any visible tracking
loss. Do not overwrite failed runs; use a new suffix if a deliberate retry is
later approved.

## 5. Validate each capture before the next

Run on the **Pi**, with ROS Jazzy sourced. Set `RUN` to the just-completed path:

```bash
RUN="$HOME/wbr-evidence/camera-day-20261022-01/A-stationary"
set -eo pipefail
ros2 bag info "$RUN/sensor-bag" | tee "$RUN/bag-info-after.txt"
python3 /home/richard/wbr-pi-camera-day-20261021/scripts/camera_day/stereo_bag_quality.py \
  "$RUN/sensor-bag" "$RUN/stereo-quality.json" --fps 15
cat "$RUN/capture_summary.json"
cat "$RUN/stereo-quality.json"
```

The quality checker was run on the prior 150 s MCAP. It checks MCAP readability,
required image/CameraInfo topics, strict timestamp order, stereo header pairing,
CameraInfo matches and nominal 15 Hz gap estimates. It does **not** verify pixel
content, physical camera motion or hardware frames lost before ROS.

Then run the tested 20-second offline MapPoint replay on the Pi. This also
reprocesses images through ORB and preserves fresh poses/status with the cloud.
It is bounded to the first 20 source seconds at 0.3×; do not edit its duration or
rate during this lab session.

```bash
set +u # ROS setup scripts expect some environment variables to be unset.
source /opt/ros/jazzy/setup.bash
set -eo pipefail
RUN="$HOME/wbr-evidence/camera-day-20261022-01/A-stationary"
test -r "$RUN/stereo.yaml" || { echo "Runner did not preserve stereo.yaml; stop and keep this run" >&2; exit 1; }
python3 /home/richard/wbr-orb-map-points-20261021-01/source/ros2/wbr_orb_node/tests/replay_map_points.py \
  --node /home/richard/wbr-orb-map-points-20261021-01/install/wbr_orb_node/lib/wbr_orb_node/d435_node \
  --bag "$RUN/sensor-bag" \
  --settings "$RUN/stereo.yaml" \
  --vocabulary /home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt \
  --output "$RUN/map-replay-20s" --domain 187
cat "$RUN/map-replay-20s/validation.json"
```

Repeat with `RUN=.../B-slow-sweep` and `RUN=.../C-return-sweep` after each
scenario. The helper takes about 80 s for the verified 20-second segment on this
Pi. It checks finite actual landmarks, PointCloud2 XYZ layout, `slam_world`,
matching source stamps/pose/status/metadata, nonempty clouds and the 1 Hz cap.

**Operational result:**

- **PASS (pilot):** `capture_summary.errors` is empty; `camera`, `slam`, and
  `record` return codes are all `0`; bag-info exits `0`; quality JSON has
  `observed_target_met: true`, `identical_image_headers: true`, and
  `counts_equal: true`; replay validation has `passed: true`, nonempty clouds,
  and `source_stamps_match_input: true`.
- **REVIEW:** a tool completed but reports unequal/missing frames, estimated
  gaps, no observed tracking at a cloud timestamp, blank/frozen images, or
  expected scene motion is absent during B/C. A is intentionally stationary, so
  no scene motion is expected for that run. Retain the run; do not collect the
  next scenario until understood.
- **FAIL/BLOCKED:** process error/nonzero exit, unreadable bag, missing required
  topics, failed map validator, or missing preflight dependency/path. Stop and
  preserve the full run folder and logs; do not repair software during capture.

For **A, B, and C**, replay checks only the first 20 seconds. This leaves 5 s
of A, 55 s of B, and 25 s of C outside the verified map replay. **Tracking
continuity, pixel content, and map export for those remaining durations remain
UNVERIFIED.** Review scene content before starting the next run: copy the
sensor MCAP to the Mac using Section 6, open it in Foxglove, and inspect early,
middle, and late IR frames. A and B/C should show a valid image; B/C should show
the expected scene change. Until observed, record **REVIEW**, not PASS. This
visual gate has not been executed for today's new datasets.

## 6. Preserve data and view landmarks on the Mac

After each capture passes the automatic checks, make a SHA-256 manifest on the
Pi (new filenames; never overwrite an existing manifest), copy the run to the
Mac, and complete the visual review before starting the next moving scenario:

```bash
cd "$HOME/wbr-evidence/camera-day-20261022-01"
find A-stationary -type f -print0 | sort -z | xargs -0 sha256sum > A-stationary.sha256
```

On the Mac, copy the complete run folder and manifest. Replace `A-stationary`
with B or C after its own validation:

```bash
mkdir -p ~/wbr-evidence-archive/camera-day-20261022-01
rsync -av wbr-pi5:wbr-evidence/camera-day-20261022-01/A-stationary \
  wbr-pi5:wbr-evidence/camera-day-20261022-01/A-stationary.sha256 \
  ~/wbr-evidence-archive/camera-day-20261022-01/
cd ~/wbr-evidence-archive/camera-day-20261022-01
shasum -a 256 -c A-stationary.sha256
```

Each listed file should end in `: OK`; any `FAILED` line means a copy mismatch.
Keep both Pi and Mac originals. Copy `map-replay-20s/map-bag/` with the run so
the cloud remains available after the replay processes exit.

Open the derived `map-bag_0.mcap` on the Mac in Foxglove (Cmd-O or `open <path-to-map-bag_0.mcap>`). In a 3D panel, set the fixed frame to `slam_world`,
enable `/d435_orb/map_points`, set point decay to `0` (replacement snapshots),
and show `/d435_orb/pose` if useful. A screenshot can be saved alongside the
run's Mac archive. For a screenshot/video, create a `visualization/` folder next
to the archived run; use macOS Screenshot (`Shift-Command-5`) to choose that
folder as the save location and capture the Foxglove 3D panel. The screen-record
option is also available there. This capture workflow is **UNVERIFIED** in this
task. Local MCAP viewing is supported by Foxglove; the panel setup for this
particular cloud is **UNVERIFIED** until visually inspected. The cloud is a
sparse set of ORB landmarks, not a dense RealSense depth cloud; no depth point
cloud is enabled and poses alone do not reconstruct landmarks. No PLY export is
available.

## 7. Failure handling

| Symptom | Safe response |
|---|---|
| SSH unavailable | Check Pi power/Ethernet and address physically; retry the bounded command in Section 2 once. Stop if still unreachable. |
| Undervoltage/throttle | Stop capture with the runner's Ctrl-C; record raw `vcgencmd` output; check supply/cable before another run. |
| USB is `480M` / camera missing | Stop; reseat the blue USB 3 cable/port, then rerun enumeration. Do not start camera launch manually. |
| ROS topics absent / no first pose | Runner should fail before recording if pose does not arrive. Preserve logs and summary; do not begin the next scenario. |
| Frozen frames / image content not changing | Mark REVIEW; keep the bag. Verify the scene actually moved, then inspect early/middle/late frames on the Mac. |
| Dropped frames / mismatched stereo headers | Keep the MCAP and quality JSON; do not replay it as a clean stereo pair set or delete it. |
| Storage unexpectedly low | Stop before the next scenario; do not run write tests or delete files. Copy evidence only after its manifest is generated. |
| Tracking loss in offline replay | Preserve replay logs and MCAP. The 20 s validator may still pass if some snapshots are valid; report lost/untracked periods as REVIEW. |

Stop immediately on a hot/unsteady power condition, a loose camera mount, an
unsafe cart path, or any need to alter calibration, firmware, storage layout,
software installation, motors, or STM32. Keep every failed run.

## First command before capture

Run the **[MAC] SSH/read-only identity check** at the top of Section 2, then
repeat the power/USB/storage checks if anything has changed since today's
preflight. SSH and current device enumeration passed; active image streaming,
tracking, a new capture, and MapPoint replay remain to be tested.
