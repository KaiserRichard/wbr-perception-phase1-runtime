# Ordered perception-stack bring-up (T27)

**INFERRED implementation; ROS 2 Jazzy and colcon execution UNVERIFIED.** This
`ament_python` package starts a headless native perception stack. **MEASURED
host tests** exercise the planner, real child processes, the existing converter
and health sender, and a launch API double. A fixture PASS is **not a Pi,
sensor, VIO, UART, recording, performance, or safety gate PASS**.

The pure-Python planner has no ROS imports. The launch file calls that planner
and starts one supervisor with `ExecuteProcess`. Its `OnProcessExit` handler
shuts down ROS launch when the supervisor exits. The supervisor owns separate
POSIX process groups so it can drain them sequentially; independent ROS launch
process actions would receive shutdown signals concurrently.

## Arguments and order

| Argument | Meaning |
| --- | --- |
| `mode:=live` | Only `wbr_d435i_bringup/d435i_stereo_inertial.launch.py` starts. |
| `mode:=replay bag:=/absolute/bag` | Only `ros2 bag play ... --clock` starts. No camera action exists in this plan. Live with a bag argument is rejected. |
| `orb:=true\|false` | Start ORB and health, or only sensor/readiness and optional recording. Default true. |
| `health_uart:=none` | Default: binary v3 frames in `run_dir/health_frames.bin`; no UART opens. |
| `health_uart:=/dev/ttyAMA0` | Existing sender opens that device at the configured baud. Requires ORB. |
| `record:=none\|/absolute/NEW_BAG` | Optional whole-session rosbag recorder; destination must be new and disjoint from `run_dir`. |
| `profile:=true\|false` | Existing profiler sampler attached to the directly launched ORB executable's PID. Requires ORB. Default false. |
| `repo_root:=/absolute/repository` | Full repository needed for existing tools. Defaults to `$WBR_ROOT`, otherwise launch working directory. |
| `run_dir:=/absolute/NEW_RUN` | New orchestration evidence directory, default unique `/tmp/wbr-stack-...`. |
| `orb_params:=/absolute/params.yaml` | Optional existing ROS parameter file containing qualified ORB vocabulary/settings and camera geometry. |

Startup steps are:

1. Create readiness subscriptions, then wait for their armed receipt.
2. Start exactly one source: camera or bag.
3. Wait for first combined **D435i camera IMU**, IR1 and IR2 messages, using
   best-effort volatile sensor QoS. No fixed sleep substitutes for these arrivals.
4. Start ORB directly from its ament package executable, then the health process.
5. Start optional recording, then the profiler with the actual ORB PID.

Readiness remains alive as a required process. Any required process exiting,
including a successful exit or ordinary bag EOF, triggers supervisor teardown.
The exit is recorded as FAIL to distinguish it from an operator-requested clean
stop. This prevents a finished/crashed source leaving ORB processing stale data.
Ctrl-C or SIGTERM requests clean shutdown. Groups stop in reverse order:
profiler, recorder, health, ORB, source, readiness (omitting disabled steps).
Each gets SIGINT and a drain deadline, then SIGTERM, then SIGKILL if necessary.
SIGKILL escalation makes the teardown criterion FAIL. The outer launch grace
allows all sequential deadlines to finish before killing the supervisor.

All package numeric bounds and their sources are in [config/stack.json](config/stack.json).
They are PROPOSED operational bounds, not accepted sensor or safety budgets.
The existing sender and profiler keep their own existing configuration files;
this package does not duplicate their thresholds.

## Provisioned Pi commands (not executed here)

The Pi must already have Ubuntu 24.04, ROS 2 Jazzy, the selected native
`wbr_orb_node` installation, and (live only) `wbr_d435i_bringup` installed and
sourced. Do not install dependencies as part of this procedure. Source the
actual existing camera and ORB overlays before this build. For example, if
those installations were named `install-camera` and `install-orb`:

```bash
export WBR_ROOT=/home/richard/wbr-perception-phase1-runtime
cd "$WBR_ROOT"
source /opt/ros/jazzy/setup.bash
source "$WBR_ROOT/install-orb/setup.bash"
# Live only, once the camera branch has been merged/built:
source "$WBR_ROOT/install-camera/setup.bash"
colcon --log-base log-stack build --base-paths ros2/wbr_perception_bringup \
  --packages-select wbr_perception_bringup \
  --build-base build-stack --install-base install-stack
source install-stack/setup.bash
```

The default `wbr_orb_node` build uses a fake engine. Select its separately built
`WITH_ORB_SLAM3=ON` installation for actual ORB; see
[the node README](../wbr_orb_node/README.md). No launch argument changes a fake
binary into real ORB. An existing ROS parameter file can contain:

```yaml
wbr_orb_node:
  ros__parameters:
    orb_vocabulary: /home/richard/ORB_SLAM3/Vocabulary/ORBvoc.txt
    orb_settings: /home/richard/wbr-config/qualified-D435i-stereoi.yaml
    # Add only the actual measured optical-to-camera-IMU transform and its
    # extrinsic_provenance, as specified in the node README.
```

Save that ROS parameter file at the `orb_params` path below, pointing to the
actual qualified ORB settings. Do not use an example calibration as device
truth. Missing geometry withholds diagnostic Odometry in the existing node.

Live, with file inspection rather than physical UART:

```bash
ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 ros2 launch wbr_perception_bringup perception_stack.launch.py \
  mode:=live orb:=true health_uart:=none profile:=true \
  repo_root:="$WBR_ROOT" run_dir:=/home/richard/wbr-evidence/NEW-stack-live \
  orb_params:=/home/richard/wbr-config/orb-ros-params.yaml \
  record:=/home/richard/wbr-evidence/NEW-stack-live-bag
# Ctrl-C requests reverse-order teardown. Inspect the saved result.json.
```

Replay, after stopping live publishers, using an isolated replay ROS domain:

```bash
ROS_DOMAIN_ID=43 ROS_LOCALHOST_ONLY=1 ros2 launch wbr_perception_bringup perception_stack.launch.py \
  mode:=replay bag:=/home/richard/wbr-evidence/ACCEPTED_BAG \
  orb:=true health_uart:=none record:=none profile:=true \
  repo_root:="$WBR_ROOT" run_dir:=/home/richard/wbr-evidence/NEW-stack-replay \
  orb_params:=/home/richard/wbr-config/orb-ros-params.yaml
```

Use a new directory for every run. Replay needs combined `/camera/camera/imu`
in addition to both IR streams; separate gyro/accel cannot feed this ORB node.
The camera package's pinned launch is expected to provide `d435i_vio_v1`,
640x480@30 IR, emitter off, gyro 200 and accel 100. **UNKNOWN:** that unmerged
launch's argument API, actual topics and combined-IMU publication. We call its
specified launch without inventing a `profile` argument or duplicating driver
parameters. Missing package blocks startup; absent required topics times out
before ORB starts. Verify the pin and readbacks once that branch is available.

For camera/bag-only inspection, set `orb:=false profile:=false health_uart:=none`.
For UART use, replace `health_uart:=none` with the agreed device only after the
protocol/firmware owner has authorized that physical link. This ticket did not
open any camera, serial device or remote connection.

## Health, clocks, and recording

The health helper follows ORB's growing `orb/pose_events.jsonl`, buffers partial
lines, preserves integer source epochs, and rejects replacement, truncation,
source reversal or producer-session change. It adapts the T14 event into a T9
snapshot and calls the existing `Converter`, retaining collapsed tracking-state
uncertainty. The existing `sender.process` sends heartbeats and health frames;
for `none`, only its transport is replaced by a flushing binary file writer.
Converted JSONL is also saved as `health_events.jsonl`. Device mode uses the
sender's existing serial transport, never a new UART implementation.

This package supplies no camera-to-current-Pi clock mapping. The launch binds a
unique producer session, keeps the source domain `ros_header`, forces the
source-header-is-D435i-time claim false, and disables clockmap files. Health age
therefore remains unavailable (saturating sentinel), with mapping flags clear.
Camera IMU initialization and feature counts remain the existing node's
UNKNOWN sentinels. Health frames cannot grant control eligibility. The STM32
body IMU is a separate sensor and is never substituted for the camera IMU.

ROS `header.stamp`, readiness `CLOCK_MONOTONIC` receipt epochs, profiler
`CLOCK_MONOTONIC`, sender `CLOCK_MONOTONIC_RAW`, and descriptive UTC timestamps
remain distinct. They are never subtracted across domains. Replay sets
`use_sim_time=true` and publishes `/clock`; live sets it false. Parameter-file
values for session, topics, output directory and these clock policies are
overridden by the planner. Backward bag seek/loop is unsupported; restart the
entire stack with a new session.

Recording reuses `lab/rosbag_qual/config.json` topics/storage and its verbatim
QoS file, adding the combined camera IMU and its explicit best-effort override
in saved `sensor_qos.yaml`. The same saved QoS file is used for playback.
Recording starts after sensor readiness and health startup, so it omits startup
traffic. Replay likewise consumes initial messages before ORB subscribes; short
bags can end before ORB starts. This is whole-session orchestration, not a
lossless replay/recording qualification. Reuse `lab/rosbag_qual` independently
with a reviewed profile-specific config; its current default rates are for
an older profile and must not be treated as acceptance for this camera pin.

## Results and host verification

Each run saves `run_raw.json`, `config.json`, verbatim combined stdout/stderr
logs per child, readiness receipts, effective QoS and `result.json`. ORB,
health and profiling outputs stay in the same run directory; the bag is at its
separate requested destination. Result criteria are:

| Criterion | Meaning |
| --- | --- |
| `startup` | All planned steps completed in order, including both readiness barriers. |
| `required_processes` | No required process exited or supervisor runtime error occurred before requested shutdown. |
| `teardown` | All started process groups stopped in reverse order, without SIGKILL. |
| `saved_evidence` | Raw logs, configuration and readiness evidence match the final receipt's SHA-256 inventory. Missing/changed evidence is BLOCKED. |

Status precedence is FAIL, then BLOCKED, then PASS. Supervisor/analyzer exits
are 0 PASS, 1 FAIL, 2 BLOCKED, 3 usage/internal error. ROS launch's own exit
code is not the result contract: inspect `result.json` or invoke the analyzer.
The criteria describe orchestration only, not estimator validity or gate status.
Re-evaluate saved output on either host without ROS or devices:

```bash
PYTHONPATH=ros2/wbr_perception_bringup PYTHONDONTWRITEBYTECODE=1 \
  python3 -m wbr_perception_bringup.supervisor \
  --analyze-only /home/richard/wbr-evidence/NEW-stack-live
```

Host tests from the repository root (Python 3.11+, stdlib; no ROS required):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s ros2/wbr_perception_bringup/tests -v \
  > ros2/wbr_perception_bringup/tests/last-run.log 2>&1
```

The portable real fixture preserves four MEASURED D435i source epochs from
saved association evidence; [provenance](tests/fixtures/provenance.json) records
its hashes. Poses and test health remain SYNTHETIC/UNKNOWN. Tests launch fake
processes, execute the real sender in file mode, and cover PASS/FAIL/BLOCKED,
every required process exit, bag EOF, readiness timeout, signal escalation,
reverse teardown, PID attachment, partial writes and saved-evidence reanalysis.

**Not verified:** colcon packaging on ROS, the real launch event API, DDS QoS
and discovery, the unmerged camera package, native ORB linking, physical UART,
bag integrity, Pi performance/power/thermal state, and hardware acceptance.
First-message readiness does not prove rates, timestamp continuity, calibration
or freshness after startup. A frozen-but-alive publisher needs separate stream
health monitoring. This package does not control publishers started elsewhere;
use an isolated domain with the live camera stopped for replay. SIGKILL of the
supervisor, host failure, and descendants escaping their process groups cannot
be guaranteed clean teardown. See [REPORT.md](REPORT.md) for remaining risks.
