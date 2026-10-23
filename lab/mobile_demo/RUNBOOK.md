# Mobile robot camera demo: lab runbook

**Purpose:** collect an ORB-SLAM3 stereo lab-map sample (L1) and RGB-D box/depth
captures (L2) with the D435i, serial `317422076650`, firmware `5.17.3.10`.
The mobile robot is an operator-driven stand-in. Nothing here sends motor
commands. Dates, profile rates, and output names are run records, not guarantees
of camera or estimator performance.

## Known capture limits

- The verified Pi runner is
  `/home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py`.
  It accepts 1–180 seconds, records stereo IR and CameraInfo, and saves runner
  logs/summary. Its recorded sensor bag does **not** include live pose/status or
  map points.
- The separately verified map-point replay is limited to the first 20 source
  seconds at 0.3×. It saves a derived map MCAP with fresh pose/status/map-points
  output. Whole-duration map replay/export and live map-point recording are
  **UNVERIFIED**. Thus this is a 3-minute maximum verified stereo segment plus
  a 20-second verified map-output sample, not a validated several-minute
  continuous reusable map. Keep the raw sensor MCAP for any later full replay.
- `d435_camera.launch.py` RGB-D mode enables color, raw depth, and aligned depth,
  and requests emitter on. It explicitly disables gyro and accel. The existing
  RGB-D recorder does not request IMU topics, so IMU capture is **UNVERIFIED**
  and omitted from this runbook.
- Root cause of the 2026-10-22 Scenario C disconnects is **UNKNOWN**. The 131
  stereo pairs in 42.5 seconds (~3 Hz) do not identify whether cable strain,
  port, power, or bandwidth caused the problem.

## Safety and stop rules

- The operator drives the mobile robot. Do not send motor commands from the Pi.
- Do not flash the STM32, change camera firmware, or change calibration.
- Secure the camera cable with strain relief on the moving chassis; leave slack
  at the camera connector and verify the cable cannot snag a wheel or joint.
- Stop before capture if the D435i is absent, serial differs, `lsusb -t` does
  not show `5000M`, power/throttle indicates a current fault, the evidence path
  is missing or has under 3 GiB free, or any verified binary/settings/runner
  path below fails its guard. Preserve output and ask the owner for a decision.
- Stop a run on a USB disconnect/re-enumeration, repeated camera stream loss,
  unexpected mount movement, unsafe surroundings, or operator discomfort. Use
  Ctrl-C once in the foreground capture process and let it close its bag. Do
  not kill ROS globally or overwrite a failed run. Retain the run and logs.
- After the 30-second motion check, continue only if camera/SLAM/recorder exits
  are clean, expected topics are present, and the bag has plausible counts and
  no disconnect in the saved kernel log. A repeated disconnect means stop the
  long map attempt and preserve evidence; do not diagnose by changing firmware,
  calibration, or system configuration in the session.

## 1. Preflight and Scenario-C mitigation [PI]

Mount and cable the camera before powering the mobile robot. Keep the robot
stationary during setup. Create a fresh run root; use a new suffix if this path
already exists.

```bash
set +u # ROS setup scripts expect unset variables.
source /opt/ros/jazzy/setup.bash
set -eo pipefail
RUNROOT="$HOME/wbr-evidence/mobile-demo-20261023-01"
test ! -e "$RUNROOT" || { echo "Run root exists; choose a new name" >&2; exit 1; }
mkdir -p "$RUNROOT"
vcgencmd pmic_read_adc EXT5V | tee "$RUNROOT/power.txt"
vcgencmd get_throttled | tee "$RUNROOT/throttled.txt"
vcgencmd measure_temp | tee "$RUNROOT/temperature.txt"
lsusb -t | tee "$RUNROOT/lsusb-tree.txt"
rs-enumerate-devices -s | tee "$RUNROOT/rs-enumerate.txt"
df -h / "$HOME/wbr-evidence" | tee "$RUNROOT/storage.txt"
```

Confirm serial `317422076650`, firmware `5.17.3.10`, USB `5000M`, at least
3 GiB free, and no current throttling/undervoltage. Prior 2026-10-22 values
(USB 5000M, EXT5V 5.167 V, throttled `0x0`) are historical; recheck today.
Do not clear a latched throttle bit. Keep the raw output.

Check the existing ROS and capture assets without building or installing:

```bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
ros2 pkg executables wbr_orb_node | tee "$RUNROOT/ros-executables.txt"
test -r /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py
test -r /home/richard/wbr-camera-native-20261021/settings/stereo-15fps-800features.yaml
test -r /home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt
test -x /home/richard/wbr-orb-map-points-20261021-01/install/wbr_orb_node/lib/wbr_orb_node/d435_node
test -r /home/richard/wbr-orb-map-points-20261021-01/source/ros2/wbr_orb_node/tests/replay_map_points.py
```

Path checks are against assets verified on 2026-10-22; a failed check is a
**STOP**, not a prompt to substitute an unverified path. Keep `dmesg` running
from a second terminal for every camera/robot capture (save its complete output
inside the run folder):

```bash
sudo dmesg -w | tee "$RUNROOT/dmesg-live.log"
```

Stop this watcher with Ctrl-C after the last capture. Record any USB disconnect,
reset, or re-enumeration time against the run ID. The saved log is evidence; no
single kernel message establishes the disconnect root cause.

## 2. L1 stereo map segment

Keep 640×480 / 15 Hz settings from the verified runner, keep the mount fixed,
and drive slowly with textured overlapping views and one return loop. The
verified runner starts camera and ORB, waits for a pose, records a sensor MCAP,
and saves `capture_summary.json`, `slam.log`, and process logs. The run path
must be new. Start with the short 30-second motion check:

```bash
RUN="$RUNROOT/L1-motion-check"
python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py "$RUN" 30
```

Review `$RUN/capture_summary.json`, `$RUN/sensor-bag`, and
`$RUNROOT/dmesg-live.log`. This brief check tests the current cable/motion
setup; it is not proof of sustained reliability. If clear, collect one maximum
duration verified stereo segment (180 seconds):

```bash
RUN="$RUNROOT/L1-lab-map-01"
python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py "$RUN" 180
```

The 180-second duration is the runner's verified maximum. **UNVERIFIED:**
capture of a continuous map for longer than 3 minutes, multi-run map
continuation, and full-segment map-point export. Do not concatenate separate
ORB sessions and call them one map. For the verified sample map output, run the
existing 20-second replay into its own new output directory:

```bash
test -r "$RUN/stereo.yaml" || { echo "Runner did not preserve settings; retain run and stop" >&2; exit 1; }
python3 /home/richard/wbr-orb-map-points-20261021-01/source/ros2/wbr_orb_node/tests/replay_map_points.py \
  --node /home/richard/wbr-orb-map-points-20261021-01/install/wbr_orb_node/lib/wbr_orb_node/d435_node \
  --bag "$RUN/sensor-bag" --settings "$RUN/stereo.yaml" \
  --vocabulary /home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt \
  --output "$RUN/map-replay-20s" --domain 187
cat "$RUN/map-replay-20s/validation.json"
```

Per-run checks before moving on:

1. `capture_summary.json`: empty `errors`; camera, SLAM, and recorder return
   codes are all 0. Keep all logs even on failure.
2. `ros2 bag info "$RUN/sensor-bag"` exits 0. On this stereo sensor MCAP,
   expect IR1/IR2 image and CameraInfo topics. The previously verified 15 Hz
   short capture produced 362 each; that count is not a guarantee for 180 s.
3. Run the existing stereo validator, then inspect JSON and live kernel log:

   ```bash
   python3 /home/richard/wbr-pi-camera-day-20261021/scripts/camera_day/stereo_bag_quality.py \
     "$RUN/sensor-bag" "$RUN/stereo-quality.json" --fps 15
   ```

   The validator path above is **UNVERIFIED on this Pi** (the source script is
   in the repository; its presence at this absolute Pi path was not checked).
   If absent, retain the capture and report that check as unavailable; do not
   substitute a guessed path. The checker tests headers, CameraInfo association,
   and nominal gaps, not visual quality or frames lost before ROS.
4. Replay validation should have `passed: true`, nonempty actual map-point
   clouds, and source stamps matching the input. It covers only the first 20 s.
   Inspect early/middle/late sensor images on the Mac; visual appearance and
   whole-run tracking continuity remain **UNVERIFIED** until reviewed.

## 3. L2 RGB-D box captures

### Set up RGB-D mode [PI]

Use a fresh per-run output path. This uses the documented SDK readback converter;
its path under the current Pi checkout is **UNVERIFIED**. If the file is not
present, stop and retain the `rs-enumerate` output rather than guessing a
different script location. The profile below is 640×480 at 30 Hz as in the
documented camera defaults; actual supported rate and stream delivery must be
confirmed live.

```bash
L2="$RUNROOT/L2-boxes-01"
mkdir "$L2"
set +u
source /opt/ros/jazzy/setup.bash
cd /home/richard/wbr-pi-camera-day-20261021 # UNVERIFIED checkout location; confirm the existing repository before using
test -r scripts/camera_day/sdk_to_yaml.py || { echo "SDK converter unavailable at this checkout" >&2; exit 1; }
rs-enumerate-devices -c > "$L2/rs-enumerate-complete.txt" 2> "$L2/rs-enumerate.stderr"
python3 scripts/camera_day/sdk_to_yaml.py "$L2/rs-enumerate-complete.txt" \
  "$L2/rgbd.yaml" --serial 317422076650 --mode rgbd --width 640 --height 480 --fps 30
```

Check the generated file and keep it with the evidence. No camera calibration
is changed; the converter writes run-specific settings from SDK readback.
Source Jazzy and the existing wrapper, then use two terminals:

```bash
# Terminal 1: RGB-D camera (color + raw depth + aligned depth; emitter requested ON)
set +u
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
ros2 launch wbr_orb_node d435_camera.launch.py mode:=rgbd serial:=317422076650 \
  width:=640 height:=480 fps:=30
```

```bash
# Terminal 2: RGB-D ORB pose/status
set +u
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
L2="$HOME/wbr-evidence/mobile-demo-20261023-01/L2-boxes-01"
ros2 launch wbr_orb_node d435_slam.launch.py mode:=rgbd \
  vocabulary:=/home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt \
  settings:="$L2/rgbd.yaml"
```

Confirm color CameraInfo, aligned depth CameraInfo, and `/d435_orb/status`;
retain camera parameter readback and one pose/status example:

```bash
L2="$HOME/wbr-evidence/mobile-demo-20261023-01/L2-boxes-01"
ros2 param dump /camera/camera > "$L2/camera-parameters.yaml"
ros2 topic echo /camera/camera/color/camera_info --once > "$L2/color-camera-info.txt"
ros2 topic echo /camera/camera/aligned_depth_to_color/camera_info --once > "$L2/aligned-depth-camera-info.txt"
ros2 topic echo /d435_orb/status --once > "$L2/initial-status.txt"
ros2 topic echo /d435_orb/pose --once > "$L2/initial-pose.txt"
```

The camera launch explicitly sets `enable_gyro` and `enable_accel` false; do
not turn them on by editing launch/config during this demo. IMU recording is
not part of this capture.

### Box matrix and tape measurements

Use `lab/mobile_demo/run_sheet.csv` as the per-run template (print it or keep a
working copy with the evidence). Availability of this newly added template on
the Pi is **UNVERIFIED**. Record each of the 20 height/distance combinations as
one static ~5-second capture and a separate slow approach from a safe start
distance.

Place boxes on the floor with their target face toward the camera. Keep lighting,
mount, and camera profile steady. Record every run in `run_sheet.csv` (copy the
template to the run folder and append one row per capture).

| Box height | Tape distances from camera front plane |
|---:|---|
| 3 cm | 0.5, 1.0, 1.5, 2.0 m |
| 5 cm | 0.5, 1.0, 1.5, 2.0 m |
| 8 cm | 0.5, 1.0, 1.5, 2.0 m |
| 12 cm | 0.5, 1.0, 1.5, 2.0 m |
| 20 cm | 0.5, 1.0, 1.5, 2.0 m |

Use a tape to record (a) box height, (b) distance from the camera front plane
to the nearest vertical box face, and (c) camera height from floor to the
camera optical center. Measure camera tilt relative to horizontal with a
protractor/inclinometer; log downward tilt as positive degrees. Repeat camera
height/tilt for every run, even if unchanged. Note box material/color, floor,
lighting, motion, occlusion, and visible tracking/depth artifacts. These are
operator measurements, not surveyed ground truth.

Start each capture from the same physical pose where practical. New output path
for each capture; never overwrite. Example for a 5 cm box at 1.0 m:

```bash
L2="$HOME/wbr-evidence/mobile-demo-20261023-01/L2-boxes-01"
RUN="$L2/H05-D1p0-static"
mkdir "$RUN"
bash /home/richard/wbr-pi-camera-day-20261021/scripts/camera_day/record.sh rgbd "$RUN/rgbd-bag"
```

The existing recorder writes rosbag2 SQLite and records color, raw depth,
aligned depth, CameraInfo, metadata, TF, and fresh `/d435_orb/pose` and
`/d435_orb/status`. It uses `scripts/camera_day/record_qos.yaml` (best-effort
image readers, transient-local `/tf_static`). Let it run about 5 seconds, then
Ctrl-C once and wait for bag metadata. For the slow approach use a distinct
folder and the same command, moving only under operator control. **UNVERIFIED:**
per-topic 5-second throughput and aligned depth/ORB pairing at this profile.

After the copy/checksum steps below, run the offline checker on the Mac against
the copied bag (the checker is part of this repository; it is not assumed to
exist on the Pi):

```bash
~/Desktop/Research/wbr-venvs/perception/bin/python lab/mobile_demo/check_capture.py \
  "$HOME/wbr-evidence-archive/mobile-demo-20261023-01/mobile-demo-20261023-01/L2-boxes-01/H05-D1p0-static/rgbd-bag"
```

Require all six color/depth image and CameraInfo topics, nonzero depth samples,
and no decode errors. Review per-topic count/rate and raw/aligned valid-depth
fractions; rates use bag receive time. A passed check does not prove depth
accuracy, synchronization quality, complete hardware delivery, or tracking
quality. If a required stream is absent, retain the bag and stop the next box
capture until the cause is understood.

## 4. Copy evidence and verify checksums [PI, then MAC]

Make one manifest beside the whole visit folder so the motion-test run, L1/L2
outputs, and saved `dmesg` log are included. Use a new manifest name if one
already exists. This follows the evidence-copy procedure in
`ops/lab-assistant/skills/wbr-evidence-copy/SKILL.md`:

```bash
cd "$HOME/wbr-evidence"
find mobile-demo-20261023-01 -type f -print0 | sort -z | xargs -0 sha256sum > mobile-demo-20261023-01.sha256
```

On the Mac, copy the whole folder and manifest; keep the Pi original:

```bash
mkdir -p ~/wbr-evidence-archive/mobile-demo-20261023-01
rsync -av wbr-pi5:wbr-evidence/mobile-demo-20261023-01 \
  wbr-pi5:wbr-evidence/mobile-demo-20261023-01.sha256 \
  ~/wbr-evidence-archive/mobile-demo-20261023-01/
cd ~/wbr-evidence-archive/mobile-demo-20261023-01
shasum -a 256 -c mobile-demo-20261023-01.sha256
```

All listed files must report `OK`. Then validate each copied L2 bag with
`check_capture.py` as shown above.
Copy failed runs too; never delete the Pi source as part of this workflow.

## What to bring

- D435i, verified USB 3 cable, and strain relief/Velcro ties; Pi 27 W supply.
- Mobile robot, operator controls, and a spotter; no Pi motor-control setup.
- Measuring tape, ruler/calipers for box heights, angle gauge/inclinometer,
  floor tape/markers, and the measured boxes.
- Mac with Ethernet/SSH path, power, enough evidence archive space, and the
  `perception` virtualenv available.
- Printed run sheet, marker/labels, and basic cable/connector inspection light.

## One-visit timeline (about 2–3 hours)

| Elapsed | Activity |
|---|---|
| 0:00–0:20 | Mount/strain-relief check, preflight, verify 5000M and free space, start saved `dmesg -w` watcher. |
| 0:20–0:35 | 30-second motion check; inspect summary, bag and disconnect log. Stop if any fault appears. |
| 0:35–1:05 | One 180-second L1 stereo segment; run the bounded 20-second map replay and inspect validation. |
| 1:05–1:20 | Set RGB-D settings from device readback; verify color/depth topics and camera parameters. |
| 1:20–2:20 | L2 static + slow-approach captures across box matrix; enter measurements and check each bag. Prioritize coverage if time is short; log skipped cells. |
| 2:20–2:45 | Close processes cleanly, stop kernel watcher, create checksums, copy evidence to Mac, verify manifests. |

The timeline is a planning estimate. It does not include troubleshooting,
repeated captures, or the several-minute continuous map feature that remains
unverified. End with a list of completed/skipped runs and unresolved issues.
