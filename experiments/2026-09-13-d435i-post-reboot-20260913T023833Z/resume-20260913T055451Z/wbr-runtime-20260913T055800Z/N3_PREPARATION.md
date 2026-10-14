# N3 preparation only — not executed

> **Takeover update:** The Pi inventory confirms the wrapper is still absent.
> Prepared `n3_baseline.yaml`, explicit topics/QoS, observer, gated recorder and
> finalized-bag/isolated-replay tooling are in this directory. Use
> [PHASE_A_RUNBOOK.md](PHASE_A_RUNBOOK.md), not the historical installation
> suggestions below. Parameter names were checked against pinned source
> 4.58.4; `wrapper_inspect.py` checks an installed package without creating a
> node, and `n3_record.py` requires live parameter readback after N2 acceptance.
> Installation of the wrapper and its message dependencies remains a separately
> reviewed action. No physical N2, storage or N3 gate passed during preparation.

Camera-free takeover package inspection on the Pi found candidate wrapper
`4.58.4-1noble.20260902.181721` and messages
`4.58.4-1noble.20260902.134137`. Resolving the wrapper without recommends would
download 137,372,870 bytes and add 565,048,320 installed bytes: **221 new
packages, one upgrade, zero removals** with that cache state. Recalculate
before approval; do not run an old transaction blindly. `inspect_dependencies.py`
only reads the apt cache. Neither package was installed by this takeover.

Two small candidate archives were downloaded and unpacked in an isolated Pi
inspection directory. Their parameter declarations and generated message
types were checked without running the camera node. The full ten-topic
synthetic replay used those message libraries; this validates tooling/API
compatibility, not installed-wrapper readiness, physical ROS delivery or VIO.

N2 in this live session means camera-side raw SDK validation, per the user's
explicit checklist. ROS delivery and rosbag record/replay are the next gate.
No ROS camera wrapper was installed or launched during these measurements.

The required next package is `ros-jazzy-realsense2-camera`, including its
automatically resolved message, image transport and cv_bridge dependencies.
Candidate inspected earlier this session:
`4.58.4-1noble.20260902.181721` (ARM64). The already installed SDK is
`ros-jazzy-librealsense2=2.58.4-1noble.20260831.020056`.
The description/mesh package is not required for a direct headless node
launch. ROS Jazzy, rosbag2 and SQLite3/MCAP storage plugins were already
present in the platform inspection; do not reinstall them by default.

After a clean N2 result and storage correction, review the remaining apt
transaction before the user installs the wrapper. The earlier 805 MB
camera-stack total included the now-installed SDK and its dependencies;
it is not the remaining installation cost. No installation command was run
as part of N3 preparation.

Use SDK **device serial 243322073847** in wrapper selection; the ASIC/USB
serial **251843061466** belongs in sysfs/udev identity checks. Preserve the
validated IR1 Y8 640×480/15, raw gyro/200, raw accel/100 profile, disable other
images, sync, align and point clouds, and set `unite_imu_method=0`.
Use project ROS domain 42 and one normal-user camera publisher.

Suggested future native node parameters (not a tested ROS configuration):

```yaml
camera:
  ros__parameters:
    serial_no: "243322073847"
    enable_color: false
    enable_depth: false
    enable_infra: false
    enable_infra1: true
    enable_infra2: false
    depth_module.infra_profile: "640,480,15"
    depth_module.infra1_format: "Y8"
    enable_gyro: true
    enable_accel: true
    gyro_fps: 200
    accel_fps: 100
    unite_imu_method: 0
    enable_sync: false
    pointcloud.enable: false
    align_depth.enable: false
```

Confirm actual parameter readback, opened profiles, topic names and QoS.
Measure IR1, gyro and accel through ROS before recording. Record the required
image, camera_info, gyro, accel, IMU info, extrinsics and transient-local TF
topics explicitly. Use a short diagnostic bag, inspect finalized bag metadata,
stop the live camera, then replay in a separate ROS domain. Compare stored
counts, original stamps and calibration/context topics with complete replay.
Do not use combined IMU until its semantics have a separate validation.

**Storage is currently unsuitable for uncompressed baseline recording:**
64 MiB sequential write plus fsync achieved only 0.944 MB/s. IR1 pixels alone
require 640×480×15 = 4.608 MB/s. The test is a single small buffered write,
not a sustained bag benchmark, but it does not establish sufficient capacity
for the required write rate. Use faster storage or investigate this drive,
then measure recording throughput with margin. Do not redirect large bags
to the microSD or silently change the sensor profile/compression to hide this.

No ORB-SLAM3 work is part of N2 or this N3 preparation.
