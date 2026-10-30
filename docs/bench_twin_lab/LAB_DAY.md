# T5 live bench twin — lab-day script

**Purpose:** prove the D435i-to-Pi visual pose and terrain advisory path on a
hand-carried rig, then record the IMU and isolated CAN bench checks. This is an
operator script, not a safety, accuracy, or motor-control qualification. Keep the
robot mechanically isolated; do not command motors or issue a jump command.

**Signal rule:** pitch and roll come from the GY-521 inertial measurement unit
(IMU), filtered by the complementary filter in `tools/imu_view`. Translation
comes from ORB-SLAM3 visual pose. Never estimate translation by double-integrating
accelerometer samples. A constant acceleration bias of **0.02 m/s² [ASSUMED]**
with zero initial velocity produces

$$
e_x(t)=\frac{1}{2}b_at^2.
$$

That is **1 m at 10 s [CALCULATED]** and **36 m at 60 s [CALCULATED]**. These
values are calculated from the stated constant-bias model; they illustrate why
the accelerometer is not a translation source.

## Evidence labels and parameter ledger

Use these labels in `measurements.csv`, notes, and every result summary:

| Label | Meaning |
|---|---|
| **ASSUMED** | chosen for the run or modelled; not measured on this rig |
| **SOURCE-SUPPORTED** | stated by a checked-in source or this ticket; cite the source |
| **MEASURED** | read from the physical setup or retained output during this run |
| **CALCULATED** | derived from named measured or assumed inputs; include the equation |

| Parameter | Value and provenance |
|---|---|
| SSH preflight timeout / retry count | `8 s` / `1 attempt` **[ASSUMED bounded check]** |
| D435i serial | `317422076650` **[SOURCE-SUPPORTED; recheck on Pi]** |
| RGB-D profile | `640×480 at 15 Hz` **[SOURCE-SUPPORTED; final-lab runbook and 26 Oct checklist]** |
| Required USB link | `5000M` **[SOURCE-SUPPORTED; preflight threshold in existing runbooks]** |
| Maximum advisory range | `3.0 m` **[SOURCE-SUPPORTED; advisory-link default]** |
| STOP target height | `0.132 m` **[SOURCE-SUPPORTED; ticket and `lab_box132`]** |
| JUMP target height | `0.046 m` or `0.080 m` **[SOURCE-SUPPORTED; ticket, `lab_books46` / `step080`]** |
| Target hand sway | about `±8°` **[ASSUMED target from ticket; record measured peak angles]** |
| Camera run duration | `30 s` per capture **[ASSUMED planning value]** |
| Camera recording rate | about `30 MB/s` **[SOURCE-SUPPORTED estimate in `live_chain.sh`; remeasure actual bytes]** |
| Camera evidence reserve | at least `8 GiB` free before the full day **[ASSUMED planning margin]** |
| Seven 30 s camera captures | `210 s × 30 MB/s ≈ 6.3 GB ≈ 5.87 GiB` **[CALCULATED planning estimate]** |
| Synthetic jump injection | `--jump-at 20 s` **[ASSUMED demonstration point; packet-relative crouch onset]** |
| Link-bench stale LED | red blink at `2 Hz` when no/stale advisory for `300 ms` **[SOURCE-SUPPORTED: `lab-day-20261025/LED_WIRING.md`]** |
| Terrain-topic stale receive | report `UNCERTAIN` after `300 ms` without a valid message **[SOURCE-SUPPORTED: `docs/interfaces/TERRAIN_ADVISORY_TOPIC.md`]** |
| Candidate link-protocol silence | `150000 µs` **[PROPOSED in `tools/link_proto/SPEC.md`; not a deployed MCU measurement]** |
| Link-bench baud | `460800`, binary advisory **[SOURCE-SUPPORTED: `LED_WIRING.md` and final-lab runbook]** |
| IMU-bench UART | `115200`, `8N1` **[SOURCE-SUPPORTED: `tools/imu_view/README.md`]** |
| IMU filter time constant | `0.5 s` **[SOURCE-SUPPORTED: `tools/imu_view/README.md`]** |
| IMU still calibration | `2 s` **[SOURCE-SUPPORTED: `tools/imu_view/README.md` default; keep still at start]** |
| IMU/CAN image clock / CAN rate | `16 MHz` / `500 kbit/s` **[SOURCE-SUPPORTED: historical `imu_can_bench` image]** |
| IMU/CAN samples / CAN pings | `100 Hz` / `100 Hz` **[SOURCE-SUPPORTED: historical `imu_can_bench` README]** |
| IMU/CAN `STAT` output | once per second **[SOURCE-SUPPORTED: historical `imu_can_bench` README]** |
| CAN checker window / round-trip floor | `20 s` / `99%` of due pings **[SOURCE-SUPPORTED: checker defaults and code]** |
| No-ACK diagnostic | TEC trends toward `128`, LEC `3`; bus-off is a separate fault **[SOURCE-SUPPORTED: historical `imu_can_bench` README]** |
| Run schedule | individual time boxes below **[ASSUMED]**; total is **155 min [CALCULATED]** |

No coordinate accuracy, depth accuracy, synchronized MCU/camera clocks, or safe
stopping distance is assumed by this script. Measure the actual physical result.

## Sim scenario map

| Bench proof | Matching simulation scenario |
|---|---|
| Clear-scene approach | `lab_empty` |
| 132 mm STOP box, static / approach | `lab_box132` / `lab_approach_box132` |
| 46 mm / 80 mm JUMP box | `lab_books46` / `step080` |
| Synthetic jump phase and gate inhibition | `jump_box110` (gate timeline); `range_entry_jump` if checking range-entry timing |
| Advisory link loss | No link-loss scenario exists in `tools/sim_scenarios`; protocol expectation below is specification-only |
| IMU sway | `lab_approach_box132` geometry through `tools/simcam_imu`; the IMU-driven body motion is still an assumed mapping |
| CANH loss | No CAN-loss scenario exists in `tools/sim_scenarios` |

Scenario expectations come from the assumed simulator library, not hardware
acceptance. The simulator library says `lab_box132` is a 132 mm box at 1 m,
`lab_approach_box132` starts 2 m away at 0.25 m/s, `lab_books46` is 46 mm, and
`step080` is 80 mm **[SOURCE-SUPPORTED simulation inputs]**. The measured tape
distances and hand-carried speed are separate **[MEASURED]** run values.

## Time-boxed schedule and roles

One owner operates the rig. The Pi runs ROS 2, the camera, ORB-SLAM3, and the
advisory process. The Nucleo displays the advisory only in the link-bench phase;
the GY-521 IMU/CAN phase requires the separately identified `imu_can_bench`
image. D435i streams RGB-D; its current wrapper disables its internal gyro and
accelerometer, so the IMU sway phase uses the GY-521 on the same carried mount.

| Step | Time box | Owner | Pi | Nucleo | D435i |
|---|---:|---|---|---|---|
| P0 preflight | 15 min **[ASSUMED]** | measure, photograph, confirm no active robot control | SSH, check free state/storage/USB/software | verify installed image and existing backup | enumerate serial/profile |
| P1 measurements | 10 min **[ASSUMED]** | measure mount, tape line, boxes, IMU axes | log clocks and setup | remain in verified image | fixed mount/profile |
| S1 clear approach | 15 min **[ASSUMED]** | carry slowly, no obstacle | capture RGB-D, pose, packets | link-bench LEDs | record scene |
| S2 STOP box | 15 min **[ASSUMED]** | measure 132 mm box and hand-stop | capture and log pose/advisory | red STOP display | fixed mount/profile |
| S3 JUMP box | 15 min **[ASSUMED]** | measure one target and hand-stop | capture and log pose/advisory | yellow JUMP advisory | fixed mount/profile |
| S4 jump gate replay | 20 min **[ASSUMED]** | carry camera only; no physical jump | replay captured packets with synthetic phase | no jump authority or command | capture source approach |
| S5 link loss | 10 min **[ASSUMED]** | unplug only the advisory UART signal at the Nucleo end | retain camera and packet capture | observe stale LED | keep stream running |
| S6 IMU sway | 20 min **[ASSUMED]** | hand-sway rig about ±8°, log motion | capture image/pose; forward UART text | `imu_can_bench` phase only | move only by hand |
| S7 CANH loss | 20 min **[ASSUMED; conditional on Pi checker/image verification]** | isolate and operate bench loop | capture serial/counter evidence | verified IMU/CAN image | not required for this isolated check |
| P2 closeout | 15 min **[ASSUMED]** | review and copy all evidence | stop processes and hash files | leave in verified state | power down after capture |
| **Planned total** | **155 min [CALCULATED sum of time boxes]** |  |  |  |  |

The two Nucleo images are different protocols. Do not change firmware during this
script. Run the link scenarios only with the identified link-bench image; run IMU
and CAN checks only with the identified IMU/CAN image. If the correct image is
not already installed, stop and schedule a separately authorized firmware
change. A backup is required before that decision.

## P0 — preflight before moving the rig

### P0.1 Pi free, SSH, storage and software

**COMMAND — Mac, then Pi:**

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o ConnectionAttempts=1 \
  -o StrictHostKeyChecking=yes wbr-pi5 \
  'set -euo pipefail; \
   RUN_ROOT="$HOME/wbr-evidence/bench-twin-$(date +%Y%m%d-%H%M%S)"; \
   mkdir -p "$RUN_ROOT/preflight" "$RUN_ROOT/scenarios" "$RUN_ROOT/closeout"; \
   printf "%s\n" "$RUN_ROOT" | tee "$RUN_ROOT/preflight/run-root.txt"; \
   printf "scenario,owner,utc_start,utc_end,result,limitations\\n" > "$RUN_ROOT/closeout/run-sheet.csv"; \
   { hostname; uname -m; free -h; df -h "$HOME"; \
     pgrep -af "[r]ealsense2_camera|[d]435_node|[m]icro_ros_agent|[a]dvisory_link.py" || true; \
   } | tee "$RUN_ROOT/preflight/pi-status.txt"; \
   printf "RUN_ROOT=%s\n" "$RUN_ROOT"'
```

The SSH command creates a new root and prints its path. Copy that exact printed
`RUN_ROOT` value into each Pi terminal. The directory timestamp is wall-clock
metadata **[MEASURED]**, not a cross-device clock mapping. If any old process is
listed or the Pi is not free, stop and retain this preflight record.

**PURPOSE:** confirm SSH identity, available RAM/storage, and that no old camera,
SLAM, UART agent, or advisory process owns the Pi. Do not kill unknown processes.

**EXPECTED:** `wbr-pi5`, `aarch64`, a responsive SSH session, at least `8 GiB`
free for the planned captures **[ASSUMED]**, and no conflicting processes.

**PASS/FAIL evidence:** save the full output as `preflight/pi-status.txt`.
PASS only when the host is correct, the Pi is free, and storage meets the stated
reserve. Otherwise stop before plugging in or starting the camera.

**RECORD:** Mac UTC time, SSH alias/address, Pi hostname/architecture, available
memory, filesystem and free space, and any process that caused a stop.

### P0.2 D435i enumeration and camera runtime

**COMMAND — Pi:**

```bash
{
  set +u
  source /opt/ros/jazzy/setup.bash
  set -euo pipefail
  rs-enumerate-devices -s
  lsusb -t
  vcgencmd get_throttled
  df -h "$HOME"
  ros2 pkg executables wbr_orb_node
  test -r /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
  test -r /home/richard/wbr-demo-20261026/lab-day-20261026/live_chain.sh
  test -r /home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt
  test -r /home/richard/wbr-evidence/mobile-demo-20261024-01/setup/rgbd-ros-15fps.yaml
} 2>&1 | tee "$RUN_ROOT/preflight/camera.txt"
```

**PURPOSE:** check the expected D435i and USB 3 link before a capture.

**EXPECTED:** serial `317422076650` **[SOURCE-SUPPORTED, verify MEASURED]**,
USB `5000M` **[SOURCE-SUPPORTED threshold]**, and no current undervoltage or
throttle event. Preserve the raw throttle value.

**PASS/FAIL evidence:** save output to `preflight/camera.txt`. PASS only if the
serial and link speed match and the camera is available to ROS. Enumeration is
not evidence of a working image stream; test that during S1. FAIL if absent,
wrong serial, or USB 2 speed.

**RECORD:** serial, firmware, USB topology, throttle value, power supply, free
space, and any cable/port change.

### P0.3 Nucleo image identity and flash backup

**COMMAND — owner on the isolated bench; read-only flash readback only if no
current backup exists.** The readback resets the Nucleo but does not write flash.
Keep the Pi UART disconnected from any other session first.

```bash
BACKUP="${BACKUP:-$HOME/wbr-evidence/lab-day-20261030/step0-readback/flash-backup.bin}"
if [ -z "${BACKUP:-}" ] || [ ! -s "$BACKUP" ]; then
  # Read-only image readback. At its prompt, the owner fits BOOT0 and presses RESET.
  cd ~/imu-can-bench
  python3 ./flash_safe.py --port /dev/ttyAMA0 --out "$RUN_ROOT/preflight/nucleo-readback"
  BACKUP="$RUN_ROOT/preflight/nucleo-readback/flash-backup.bin"
fi
test -s "$BACKUP"
sha256sum "$BACKUP" | tee "$RUN_ROOT/preflight/flash-backup.sha256"
for IMG in "$HOME/imu-can-bench/"*.bin "$HOME/course-stage/fw/"*.bin; do
  test -f "$IMG" || continue
  if cmp -s -n "$(stat -c %s "$IMG")" "$IMG" "$BACKUP"; then
    printf 'MATCH %s\n' "$IMG"
  fi
done | tee "$RUN_ROOT/preflight/nucleo-image.txt"
```

**PURPOSE:** prove a retained full-flash backup exists and identify the running
image by byte comparison with candidate images. The utility reads the full
512 KiB twice **[SOURCE-SUPPORTED behavior from the 30 Oct runbook]**. Its
BOOT0/RESET steps are physical owner actions; do not run it from the Mac.

**EXPECTED:** the current backup matches a known image. The link-bench image is
`link_bench_f446.bin`, SHA-256
`bf5721b44c0d9eafa4b5b53fb75f1ceec8c6e3c72a0c81d5a6bfd7635fe003ed`
**[SOURCE-SUPPORTED; checked-in checksum]**. The default 500 kbit/s IMU/CAN
image is `imu_can_bench.bin`, SHA-256
`937c2857c85afe31198a4ec42129d38a3410bcd92da759b10be5eb08721025a7`
**[SOURCE-SUPPORTED by historical commit `477b53f`; verify against the Pi
readback]**. A separate 1 Mbit/s image exists and is not the default target.

**PASS/FAIL evidence:** retain `preflight/flash-backup.sha256` and
`preflight/nucleo-image.txt`. PASS for link tests only when the exact link-bench
image is identified. PASS for IMU/CAN only when the full IMU/CAN image identity
and counter contract are verified. If no candidate matches, no backup exists,
or image age is older than the most recent firmware change, STOP. No LED pattern
alone identifies firmware.

**RECORD:** backup path, byte length, SHA-256, readback date, image match, image
SHA-256, baud, UART ownership and Nucleo reset state. The requested
`tools/imu_can_bench/README.md` is absent at this checkout's HEAD; its counter
contract was read from historical commit `477b53f`. Before S7, verify that the
Pi has that matching `bench_check.py` and firmware image; do not infer installed
files from Git history alone. For IMU/CAN, also require
`test -r ~/imu-can-bench/bench_check.py` on the Pi.

### P0.4 Time domains

**COMMAND — Mac and Pi:**

```bash
date -u
PI_RUN_ROOT=/home/richard/wbr-evidence/bench-twin-REPLACE_WITH_PRINTED_ID
RUN_ID=$(basename "$PI_RUN_ROOT")
LOCAL_PREFLIGHT="$HOME/Desktop/bench-twin-staging/$RUN_ID/preflight"
mkdir -p "$LOCAL_PREFLIGHT"
{ date -u; ssh wbr-pi5 'date -u; timedatectl show -p NTPSynchronized -p TimeUSec'; } \
  | tee "$LOCAL_PREFLIGHT/clocks.txt"
scp "$LOCAL_PREFLIGHT/clocks.txt" "wbr-pi5:$PI_RUN_ROOT/preflight/clocks.txt"
```

Replace `REPLACE_WITH_PRINTED_ID` with the run root printed by P0.1 before
running the copy command.

**PURPOSE:** annotate wall-clock state without claiming camera, Pi and Nucleo
monotonic clocks are synchronized.

**EXPECTED:** both wall-clock readings and Pi synchronization status are
retained. Camera/device stamps, Pi monotonic event times, and Nucleo boot timers
remain separate domains unless a reviewed mapping is supplied.

**PASS/FAIL evidence:** save as `preflight/clocks.txt`. Missing wall-clock
information is a failure for trace correlation, not a camera failure.

**RECORD:** timezone, UTC readings, Pi synchronization status, device timestamp
domain from logs, Nucleo reset/boot marker, and any observed offset. Never infer
sub-millisecond alignment from matching wall-clock strings.

## P1 — measurement checklist

Fill `measurements.csv` before the matching scenario. Use one row per scenario;
keep raw readings and units.

**COMMAND:** use a tape for the mount, box and floor marks. Perform the IMU
axis-check motions in S6 with the live `tools/imu_view` complementary-filter
viewer; write the result into each scenario's `measurements.csv`.

**PURPOSE:** establish the geometry and signs used to interpret perception and
pose evidence.

**EXPECTED:** every target dimension, mount measurement, tape distance, clock
domain and IMU axis response is entered with its evidence label.

**PASS/FAIL evidence:** PASS when all applicable rows have units and labels.
FAIL if a target is not measured, IMU signs are wrong, or a scenario lacks a
recorded start/stop distance.

**RECORD:** all rows below, the operator, instrument, units, resolution and
source or calculation used.

| Measurement | Method | Required entry and provenance |
|---|---|---|
| Camera serial / firmware / profile | Pi enumeration | exact strings **[MEASURED]**; expected serial/profile above **[SOURCE-SUPPORTED]** |
| Optical-center height and forward offset | tape from floor / mount reference | metres, tape uncertainty **[MEASURED]**; do not substitute mount-study model values |
| Camera pitch | level/inclinometer plus IMU viewer on fixed mount | degrees, sign and method **[MEASURED]**; pitch sign follows `imu_view` axis check |
| Camera mount and cable slack | overview and close-up photos | `setup.jpg` **[MEASURED evidence]** |
| STOP/JUMP boxes | ruler or caliper | height, width, depth in metres **[MEASURED]**; compare height against 0.132 / 0.046 / 0.080 m target **[SOURCE-SUPPORTED]** |
| Floor marks | tape from camera-front plane to box near face | start, stop, first advisory, last advisory distances **[MEASURED]**; record tape resolution **[MEASURED]** |
| Lane and lighting | tape/notes/photos | surface, texture, illumination, shadows, moving people **[MEASURED]** |
| IMU axes | `tools/imu_view` axis check below | observed model response for each move **[MEASURED]** |
| IMU hand sway | GY-521 fixed to carried mount | complementary-filter peak pitch/roll and rates **[MEASURED estimate; not orientation ground truth]** |
| Clocks | P0.4 and raw logs | timestamp source/domain per artifact **[MEASURED]**; offset **[CALCULATED only if mapping is defined]** |
| Software/configuration | Pi `git rev-parse HEAD`, launch output, YAML | commit, file SHA-256, ROS domain, profile **[MEASURED]** |
| Nucleo | readback and run notes | matched image, SHA-256, reset state, UART baud **[MEASURED]** |

The `imu_view` axis check from its README is:

| Physical move | Expected model response |
|---|---|
| Hold flat | upright; pitch and roll about `0° ±2°` **[SOURCE-SUPPORTED tolerance]** |
| Tip X-arrow end down | nose down; positive pitch **[SOURCE-SUPPORTED sign]** |
| Lift left edge / Y-arrow side | left wheel lifts; positive roll **[SOURCE-SUPPORTED sign]** |
| Hold tilted still for `5 s` | complementary-filter model stays put while gyro-only ghost creeps **[SOURCE-SUPPORTED demonstration]** |

Stop the sway test if signs are wrong or the flat reading is outside tolerance.
Record board orientation and any `--axes` mapping; do not silently flip signs.

## Shared capture card for live camera scenarios

Use a new scenario folder every time. The link-bench image is required. The
existing `lab-day-20261026/live_chain.sh` starts D435 RGB-D, the advisory sender,
and a camera MCAP. Start ORB-SLAM3 in a second terminal after the camera topics
appear, and bag pose/status in a third terminal. This keeps camera-to-advisory
and camera-to-visual-pose evidence in the same ROS session.

**Terminal A — Pi camera and advisory:**

```bash
set +u
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
cd ~/wbr-demo-20261026
# Set to the exact scenario folder ID before each run.
SCENARIO_ID=normal_approach
RUN="$RUN_ROOT/scenarios/$SCENARIO_ID"
mkdir -p "$RUN/orb"
test ! -e "$RUN/live" || { echo "Preserve existing run; choose a fresh folder" >&2; exit 1; }
RECORD=1 DURATION=30 MAX_FORWARD=3.0 \
  bash lab-day-20261026/live_chain.sh "$RUN/live"
```

**Terminal B — Pi visual pose:**

```bash
set +u
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
SCENARIO_ID=normal_approach
RUN="$RUN_ROOT/scenarios/$SCENARIO_ID"
ros2 launch wbr_orb_node d435_slam.launch.py mode:=rgbd \
  vocabulary:=/home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt \
  settings:=/home/richard/wbr-evidence/mobile-demo-20261024-01/setup/rgbd-ros-15fps.yaml \
  2>&1 | tee "$RUN/orb/slam.log"
```

**Terminal C — Pi ORB-SLAM3 pose/status evidence:**

```bash
set +u
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
SCENARIO_ID=normal_approach
RUN="$RUN_ROOT/scenarios/$SCENARIO_ID"
ros2 topic echo /d435_orb/status --once > "$RUN/orb/status.txt"
ros2 topic echo /d435_orb/pose --once > "$RUN/orb/pose-first.txt"
ros2 bag record -s mcap -o "$RUN/orb/pose-bag" \
  /d435_orb/pose /d435_orb/status 2>&1 | tee "$RUN/orb/record.log"
```

When Terminal A completes, press Ctrl-C once in Terminal C to finalize the pose
bag, then Ctrl-C once in Terminal B to stop SLAM. Preserve partial output on any
failure. Do not kill ROS processes globally.

**PURPOSE:** retain camera RGB-D, advisory packet/echo statistics, ORB visual
pose and tracking status together. The camera launch does not enable the D435i
IMU **[SOURCE-SUPPORTED in `d435_camera.launch.py`]**. Tilt is from the external
GY-521 complementary-filter trace.

**EXPECTED:** `summary.json`, `packets.csv`, `camera.log`, `record.log`, camera
MCAP, ORB `status.txt`, pose-first sample, `slam.log`, and pose/status MCAP.

**PASS/FAIL evidence:** all expected files are nonempty, the first pose exists,
and scene measurements/photos are retained. This is a completed capture, not an
accuracy claim. The validator script checks the expected output paths.

**RECORD:** exact commands, start/end UTC, camera and ORB rates, pose/status
counts, losses/resets, advisory labels, sent/echoed/lost packets, rejected/stale
events, LEDs, environment, measured route, and any stop or dropped frame.

## S1 — clear-scene hand-carried approach

**Time box:** 15 min **[ASSUMED]**. **SIM:** `lab_empty`.

**SETUP:** identify a clear lane with no obstacle inside the `3.0 m` advisory
range **[SOURCE-SUPPORTED default]**. Keep camera mount, profile, lighting and
floor fixed. Owner carries the rig by hand and walks the marked line; no motors.

**COMMAND:** run the shared capture card with `SCENARIO_ID=normal_approach`.

**PURPOSE:** establish a moving-camera baseline with visual translation and no
obstacle advisory.

**EXPECTED:** camera MCAP and live ORB pose/status; `NONE` while the visible
scene is clear. Translation evidence is the ORB-SLAM3 pose sequence only.

**PASS/FAIL evidence:** PASS if a new output is finalized, pose/status and packet
echoes are present, and no obstacle candidate is emitted in the measured clear
lane. FAIL if no pose, camera capture errors, stale link, or an unexplained
obstacle candidate appears. If an actual wall enters range, invalidate the
setup and record it rather than relabeling it as empty.

**RECORD:** `measurements.csv`, `notes.md`, setup photo, distance marks, carry
duration, ORB start/end pose, advisory counts, and `lab_empty` reference.

## S2 — 132 mm STOP box

**Time box:** 15 min **[ASSUMED]**. **SIM:** `lab_box132` and
`lab_approach_box132`.

**SETUP:** measure the box. Target height is `0.132 m` **[SOURCE-SUPPORTED;
actual height is MEASURED]**. Mark the measured gap from the camera front plane
to the box face. Keep the same mount and floor. Owner approaches by hand and
stops before contact.

**COMMAND:** run the shared capture card with `SCENARIO_ID=stop_box_0132`.

**PURPOSE:** prove that a physically measured high box yields a STOP advisory
while the camera moves and ORB-SLAM3 provides visual pose.

**EXPECTED:** `STOP_CANDIDATE` in `packets.csv` and red D6/PB10 LED on the
identified link-bench image **[SOURCE-SUPPORTED LED map]**.

**PASS/FAIL evidence:** PASS if STOP is received and the red LED is observed
before the operator's no-contact stop, with all artifacts retained. FAIL if
there is no STOP, the LED contradicts the received advisory, tracking is absent,
or the box is contacted. Record first/last STOP distances; do not claim a
validated stopping distance from this hand-carried test.

**RECORD:** all P1 box/floor/mount values, photo, packet/LED times, distance at
first and final STOP, route, ORB pose/status, and `lab_box132` / `lab_approach_box132`.

## S3 — low JUMP box

**Time box:** 15 min **[ASSUMED]**. **SIM:** `lab_books46` for 46 mm or
`step080` for 80 mm.

**SETUP:** choose exactly one box and measure its height. Target is `0.046 m` or
`0.080 m` **[SOURCE-SUPPORTED; actual height is MEASURED]**. Mark the box face
and a no-contact stop point. No physical jump is performed.

**COMMAND:** run the shared capture card with
`SCENARIO_ID=jump_box_0046_or_0080` and write the selected height in
`measurements.csv`.

**PURPOSE:** prove the perception advisory classification for a low obstacle;
the JUMP label never grants permission to jump.

**EXPECTED:** `JUMP_CANDIDATE` packet and steady yellow D5/PB4 indication. The
LED wiring also uses yellow blinking at `4 Hz` for UNCERTAIN **[SOURCE-SUPPORTED]**;
record video so blink and steady states are distinguishable.

**PASS/FAIL evidence:** PASS if the measured box yields a received
`JUMP_CANDIDATE`, the corresponding yellow display is observed, pose/status are
retained, and there is no contact. FAIL on missing/contradictory advisory,
uncertainty misread as JUMP, tracking loss without explanation, or contact.

**RECORD:** selected box, measured size, advisory/LED evidence, first/last
distances, route, ORB pose/status and matching simulation name.

## S4 — synthetic jump phase over carried-camera data

**Time box:** 20 min **[ASSUMED]**. **SIM:** `jump_box110`; optionally inspect
`range_entry_jump` timing.

**SETUP:** capture a low-box JUMP approach using the shared capture card and
carry the camera only along the floor route. Do not lift it to simulate flight,
jump the robot, or actuate motors. The phase injection is performed afterward
on the measured `packets.csv`; it is a synthetic timeline aligned by
packet-relative time, not a measured jump/contact event.

**COMMAND — Pi:** run the shared capture card with
`SCENARIO_ID=jump_gate_injected` and the measured low box. Carry the rig only
during this camera capture; the injected phase is an offline replay step below.

**COMMAND — Mac analysis, using the captured run:**

```bash
PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
RUN_PI="$RUN_ROOT/scenarios/jump_gate_injected"
RUN_ID=$(basename "$RUN_ROOT")
RUN_MAC="$HOME/Desktop/bench-twin-staging/$RUN_ID/scenarios/jump_gate_injected"
mkdir -p "$RUN_MAC/analysis"
scp "wbr-pi5:$RUN_PI/live/packets.csv" "$RUN_MAC/packets.csv"
"$PYTHON" -m tools.jump_gate.demo --packets "$RUN_MAC/packets.csv" \
  --csv-only "$RUN_MAC/analysis/jump-gate.csv" --jump-at 20
ssh wbr-pi5 "mkdir -p '$RUN_PI/analysis'"
scp "$RUN_MAC/analysis/jump-gate.csv" "wbr-pi5:$RUN_PI/analysis/jump-gate.csv"
```

**PURPOSE:** replay measured camera-derived advisories through the research gate
while injecting the synthetic CROUCH/PUSH/FLIGHT/LAND/SETTLE schedule at
`20 s` packet-relative time **[ASSUMED]**. `--csv-only` needs no renderer.

**EXPECTED:** `analysis/jump-gate.csv` records raw and gated advisories plus
synthetic phase. In CROUCH, PUSH, FLIGHT, LAND, SETTLE and UNKNOWN, gate output
is `UNCERTAIN`; no gated JUMP is permitted outside recovered STAND.

**PASS/FAIL evidence:** PASS if the CSV covers the injected phases, the gated
output never says JUMP during an inhibited phase, and the original packet file
is unchanged. FAIL on missing phase rows, any gated JUMP during an inhibited
phase, or missing source packets. This does not test a physical jump or MCU
gate integration.

**RECORD:** original packet SHA-256, injection time, phase intervals, raw/gated
counts, gate reasons, synthetic-input labels, and `jump_box110` result.

## S5 — advisory-link loss

**Time box:** 10 min **[ASSUMED]**. **SIM:** no link-loss scenario is present in
`tools/sim_scenarios`.

**SETUP:** only with the identified link-bench image and an isolated rig. Start
the shared camera/ORB capture. Owner briefly disconnects the Pi-TX-to-Nucleo-RX
advisory signal at the Nucleo end; leave ground, power, and camera USB alone.
Reconnect after the stale indication; never touch motor or actuator wiring.

**COMMAND:** run the shared capture card with `SCENARIO_ID=link_loss`, and
record the LED continuously. Do not stop unrelated UART agents or camera
processes to imitate link loss.

**PURPOSE:** observe advisory packet loss and stale-display behavior while the
camera and visual pose continue.

**EXPECTED:** the current LED wiring specifies external red blinking at `2 Hz`
after no/stale advisory for `300 ms` **[SOURCE-SUPPORTED for the link-bench
image]**; LD2 indicates accepted link. The terrain-topic receiver contract also
reports `UNCERTAIN` after `300 ms` without a valid message
**[SOURCE-SUPPORTED interface rule]**. Separately, the candidate `link_proto`
spec proposes `NO_LINK` after silence of at least `150000 µs`, withdrawal of
references, disabled authority, and a re-enable latch **[PROPOSED, not proven on
this image]**. The candidate library requests a controller-owned bounded ramp;
it does not implement a physical ramp.

**PASS/FAIL evidence:** PASS for the displayed-link test if red stale indication
appears during the UART break and link indication recovers after fresh packets.
Copy a phone video to `scenarios/link_loss/link-loss-video.mov`. Save
packet/echo loss and notes. Mark MCU `link_proto` receiver
state **NOT TESTED** unless the exact installed image exposes that receiver and
state telemetry. Do not report the LED result as proof of candidate receiver
state or motor behavior.

**RECORD:** unplug/reconnect UTC, LED onset/recovery, packets sent/echoed/lost,
camera/ORB continuity, image SHA, baud, and stale/re-enable telemetry if the
identified firmware actually provides it.

## S6 — IMU sway and wobble-gate comparison

**Time box:** 20 min **[ASSUMED]**. **SIM:** `lab_approach_box132` through
`tools/simcam_imu`.

**SETUP:** this phase requires the separately identified `imu_can_bench` image
and GY-521 mounted rigidly to the D435i carrier. Check the `imu_view` axes from
P1. Hold still for the `2 s` calibration **[SOURCE-SUPPORTED]**, then carry the
camera through the 132 mm box scene while hand-swaying about `±8°`
**[ASSUMED target; filter output is MEASURED estimate]**. Do not use the link
bench binary protocol in this phase.

**COMMAND — Mac viewer; the Pi streams the Nucleo text UART:**

```bash
RUN_ID=$(basename "$RUN_ROOT")
RUN="$RUN_ROOT/scenarios/imu_sway"
RUN_MAC="$HOME/Desktop/bench-twin-staging/$RUN_ID/scenarios/imu_sway"
mkdir -p "$RUN_MAC/analysis"
ssh wbr-pi5 'stty -F /dev/ttyAMA0 115200 raw -echo cs8 -parenb -cstopb && cat /dev/ttyAMA0' \
  | ~/Desktop/Research/wbr-lab-ops/.venv/bin/mjpython -m tools.imu_view.view \
      --stdin --save "$RUN_MAC/imu_view_run.csv"
```

At the same time, use these Pi terminals. The camera driver publishes RGB-D;
the SLAM launch subscribes to it. This phase deliberately omits `live_chain.sh`
because that script opens the Nucleo UART at the link-bench baud.

**Terminal A — Pi camera:**

```bash
set +u
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
RUN="$RUN_ROOT/scenarios/imu_sway"
mkdir -p "$RUN/camera"
ros2 launch wbr_orb_node d435_camera.launch.py mode:=rgbd \
  serial:=317422076650 width:=640 height:=480 fps:=15 \
  2>&1 | tee "$RUN/camera/camera.log"
```

**Terminal B — Pi ORB-SLAM3:**

```bash
set +u
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
RUN="$RUN_ROOT/scenarios/imu_sway"
ros2 launch wbr_orb_node d435_slam.launch.py mode:=rgbd \
  vocabulary:=/home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt \
  settings:=/home/richard/wbr-evidence/mobile-demo-20261024-01/setup/rgbd-ros-15fps.yaml \
  2>&1 | tee "$RUN/camera/slam.log"
```

**Terminal C — Pi combined camera and visual-pose bag:**

```bash
set +u
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
RUN="$RUN_ROOT/scenarios/imu_sway"
ros2 topic echo /d435_orb/status --once > "$RUN/camera/status.txt"
ros2 topic echo /d435_orb/pose --once > "$RUN/camera/pose-first.txt"
ros2 bag record -s mcap -o "$RUN/camera/session-bag" \
  /camera/camera/color/image_raw /camera/camera/color/camera_info \
  /camera/camera/aligned_depth_to_color/image_raw \
  /camera/camera/aligned_depth_to_color/camera_info \
  /d435_orb/pose /d435_orb/status /tf /tf_static \
  2>&1 | tee "$RUN/camera/record.log"
```

The owner carries and sways during this interval, then stops the IMU viewer and
presses Ctrl-C once in Terminal C and Terminal B. Copy the Mac-captured CSV to
the Pi evidence root before checksum:

```bash
scp "$RUN_MAC/imu_view_run.csv" "wbr-pi5:$RUN/imu_view_run.csv"
```

**COMMAND — analyze the retained IMU CSV on the Mac, outside this restricted
rendering sandbox:**

```bash
PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
"$PYTHON" -m tools.simcam_imu.tilt_source "$RUN_MAC/imu_view_run.csv" \
  > "$RUN_MAC/analysis/tilt-source.json"
# Set IMU_START to a measured elapsed-CSV time with a complete scenario window.
"$PYTHON" -m tools.simcam_imu.run docs/simcam/example_box132.json \
  --imu-csv "$RUN_MAC/imu_view_run.csv" --imu-start "$IMU_START" --scale 1.0 \
  --out "$RUN_MAC/analysis/timeline.csv" --record "$RUN_MAC/analysis/frames"
ssh wbr-pi5 "mkdir -p '$RUN/analysis'"
scp "$RUN_MAC/analysis/tilt-source.json" "wbr-pi5:$RUN/analysis/"
scp "$RUN_MAC/analysis/timeline.csv" "wbr-pi5:$RUN/analysis/"
scp "$RUN_MAC/analysis/timeline_zero_tilt.csv" "wbr-pi5:$RUN/analysis/"
scp "$RUN_MAC/analysis/timeline_comparison.csv" "wbr-pi5:$RUN/analysis/"
scp "$RUN_MAC/analysis/timeline_metadata.json" "wbr-pi5:$RUN/analysis/"
```

Write `analysis/wobble-fix-comparison.md` after inspecting the new CSVs. State
the new raw/gated/zero-tilt counts, reference the dated pre-fix/post-fix result
below, and explicitly say the new trace was not run through a same-trace
pre-fix implementation. Copy the report to the Pi alongside the analysis files.

```bash
scp "$RUN_MAC/analysis/wobble-fix-comparison.md" "wbr-pi5:$RUN/analysis/"
```

**PURPOSE:** collect raw acceleration/gyro, obtain tilt from the complementary
filter, then compare current raw/gated output with a zero-body-tilt comparator.
Translation in the physical capture remains ORB-SLAM3 visual pose.

**EXPECTED:** axis signs match the README table; CSV timestamps increase with
no gap above `0.1 s` **[SOURCE-SUPPORTED replay limit]**; current output contains
`timeline.csv`, `timeline_zero_tilt.csv`, `timeline_comparison.csv`, and
`timeline_metadata.json`. Inspect `raw_advisory`, `gated_advisory`, confidence,
gate reason, measured rates, and valid-plane rows.

**PASS/FAIL evidence:** PASS for collection if camera/pose and IMU files are
complete and the measured filter sway is near the target. PASS for current-gate
analysis only if the comparison is complete and no gated JUMP appears during a
synthetic inhibited phase. Report the pre-fix and post-fix reference below
separately: current `simcam_imu` has no CLI switch to replay the old wobble fix,
so do not label its zero-tilt/raw columns as a same-trace old-gate ablation.

**Wobble-fix source reference:** on the same 30 Oct 2026 historical hand trace,
the documented pre-fix simulation had raw STOP `8/48` and repeated gate
inhibition; after the fix it had raw STOP `40/48`, gated STOP `38/48`, and
zero-tilt gated STOP `34/48` **[SOURCE-SUPPORTED, measured in simulation; not
this lab's result]**. A same-new-trace old/new-gate comparison remains
**UNVERIFIED** until a pre-fix implementation is made available.

**RECORD:** raw CSV SHA-256, still-bias interval, axis mapping, filter output,
peak pitch/roll/rates, `IMU_START`, scale, paired timelines/metadata, valid plane
count, raw/gated advisory counts, and comparison limitation.

## S7 — CANH loss on the isolated bench loop

**Time box:** 20 min **[ASSUMED]**. **SIM:** no CAN-loss scenario is present in
`tools/sim_scenarios`.

**SETUP:** use only the identified `imu_can_bench.bin` image on its isolated
two-transceiver bench loop. Do not connect a motor bus. Confirm the Pi UART is
not owned by `micro_ros_agent`; the bench checker opens `/dev/ttyAMA0` at
`115200 8N1` **[SOURCE-SUPPORTED]**. The image sends a CAN1 `0x101` counter and
inverse at `100 Hz`, CAN2 echoes `0x202`, and CAN1 checks the return
**[SOURCE-SUPPORTED]**. Disconnect only the documented CANH break point; leave
CANL, ground and power unchanged. Do not add or change termination during the
run. D9 blue means a CAN round trip occurred within the last second; D6 red
means a fault **[SOURCE-SUPPORTED LED meanings]**.

**COMMAND — Pi, in `~/imu-can-bench`; create fresh output folders and run the
connected baseline first:**

```bash
cd ~/imu-can-bench
set -o pipefail
RUN="$RUN_ROOT/scenarios/can_loss"
mkdir -p "$RUN/baseline" "$RUN/canh-open" "$RUN/recovery"
cp "$RUN_ROOT/preflight/nucleo-image.txt" "$RUN/image.txt"
python3 bench_check.py --seconds 20 --out "$RUN/baseline" \
  2>&1 | tee "$RUN/baseline/checks.txt"
```

**COMMAND — Pi, fault-detection run:**

```bash
cd ~/imu-can-bench
set -o pipefail
RUN="$RUN_ROOT/scenarios/can_loss"
python3 bench_check.py --seconds 20 --out "$RUN/canh-open" --expect-can-fail \
  2>&1 | tee "$RUN/canh-open/checks.txt"
```

As soon as D9 blue confirms a round trip, the owner opens the shared CANH link
at the documented isolated-loop break point and holds it open until this command
finishes. Do not use the robot bus.

**COMMAND — owner reconnects CANH; Pi recovery run:**

```bash
cd ~/imu-can-bench
set -o pipefail
RUN="$RUN_ROOT/scenarios/can_loss"
python3 bench_check.py --seconds 20 --out "$RUN/recovery" \
  2>&1 | tee "$RUN/recovery/checks.txt"
```

The `20 s` window and `--expect-can-fail` option are **[SOURCE-SUPPORTED from
historical README/checker at `477b53f`]**. The checker estimates the actual
window from `STAT` counters; keep each output directory new.

**PURPOSE:** prove the firmware distinguishes healthy round trips, a broken
CANH path and recovery on the non-motor test loop.

**EXPECTED:** baseline and recovery each report `SUMMARY PASS`, at least `99%`
of due `100 Hz` pings round-tripped, `bad=0`, no new bus-off events, and no TEC
error **[SOURCE-SUPPORTED checker contract; values are run measurements]**.
During CANH loss the `can_fault_detected` check must report PASS because normal
round-trip acceptance fails. For a no-ACK break, the documented diagnostic is
CAN1 busy, TEC trending toward `128`, and LEC `3`; a bus-off event is a distinct
bit-error fault and must be recorded as a failure even if fault detection
itself passed. REC, overruns, bad frames and both controller ESRs are recorded
as observed values, not assigned fabricated targets. The historical 29 Oct
baseline measured `1900/1900` round trips, `bad=0`, busy `0`, TEC/REC `0`, and
no bus-off during its measured window **[SOURCE-SUPPORTED historical result]**;
it is a reference, not today's result.

**PASS/FAIL evidence:** PASS only if baseline passes, `can_fault_detected`
passes while CANH is open with the other checker conditions intact, no bus-off
counter increase occurs, and recovery passes after reconnect. FAIL if baseline
or recovery fails, no fault is detected, bus-off increases, or the wrong loop
or image was used. Retain all raw logs and `summary.json` files even on failure.

**RECORD:** full image SHA-256, checker source/version, board reset state, loop
topology, baseline/open/recovery `STAT` deltas (TX ok/busy/error, RX, overruns,
bus-off events, TEC/REC/LEC, sent/matched/bad, UART drops), actual duration,
CANH disconnect/reconnect time, photos and any termination measurement. The
historical README reports `120 Ω` termination as **UNKNOWN/not measured**;
do not treat it as verified here.

## P2 — stop, copy, checksum and close

**COMMAND — Pi:** stop camera, ORB and advisory processes with Ctrl-C in their
own terminals. Do not kill processes globally. Preserve failed outputs.

```bash
cd "$RUN_ROOT"
find . -type f ! -name SHA256SUMS -print0 | xargs -0 sha256sum > SHA256SUMS
```

**COMMAND — Mac:** copy the evidence root to a new destination, then verify the
Pi-generated manifest there.

```bash
mkdir -p "$HOME/Desktop/bench-twin-evidence"
scp -r "wbr-pi5:$RUN_ROOT" "$HOME/Desktop/bench-twin-evidence/"
LOCAL_ROOT="$HOME/Desktop/bench-twin-evidence/$(basename "$RUN_ROOT")"
cd "$LOCAL_ROOT"
shasum -a 256 -c SHA256SUMS
```

Include all `preflight/`, `scenarios/`, IMU raw CSV, bag metadata and MCAP files,
ORB status/pose bags, advisory `summary.json`/`packets.csv`, camera/SLAM/record
logs, CAN logs if unblocked, setup photos/videos, notes, analysis outputs and
the SHA-256 manifest. A copied file passes only when its digest matches the Pi
manifest. Do not delete the Pi copy until the owner has checked every result.

**PURPOSE:** preserve raw and failed runs and prove copy integrity.

**EXPECTED:** root `SHA256SUMS` covers every retained file except itself; Mac
verification reports `OK` for all entries.

**PASS/FAIL evidence:** PASS if all expected scenario artifacts exist and all
checksums verify. Missing output is FAIL for that scenario; hash mismatch is
FAIL for the copy and requires recopy to a new destination.

**RECORD:** append owner, UTC start/end, scenario result and limitations for
every scenario to `closeout/run-sheet.csv`; also retain command lines,
missing artifacts, source/copy paths, and SHA-256 outcomes. From the repository
root on the Mac, validate the copied folder:

```bash
python3 tools/bench_twin_lab/checklist.py --validate "$LOCAL_ROOT"
```

The validator reports missing artifacts; it does not interpret sensor data or
turn a captured file into a pass by itself.
