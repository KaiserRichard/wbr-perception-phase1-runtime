# D435 camera day: existing `wbr_orb_node` package

**2026-10-21: native Pi build/install and camera-free linking verified.**
Serial `WITH_ORB_SLAM3=ON` colcon build exited 0; installed `d435_node` reached
its expected missing-settings error with immediate symbol binding enabled.
Camera absent: no live launch, tracking, pose or throughput claim.
See the [build session and preserved failures](../../ops/worklog/sessions/2026-10-21-camera-ros-build.md).
The initial 2026-10-20 preparation was offline because SSH timed out.

`d435_node` is a visual-only executable in the existing `ros2/wbr_orb_node`
package. It uses native ORB-SLAM3 `STEREO` or `RGBD`, disables the viewer and
never subscribes to an IMU. The original `orb_node` stereo-inertial path is
unchanged. The pinned `third_party/ORB_SLAM3_ROS2` package is not modified.
No third wrapper package is introduced.

## Private Pi build

Run these commands **on the Pi in its dedicated task source directory**.
Do not use the shared runtime checkout. The existing ORB library root below
was verified on 2026-10-21; this script does not rebuild that shared ORB tree.
The native wrapper imports the installed Pangolin CMake targets and retains
external library paths in the installed executables' runtime search path.

```bash
cd /home/richard/wbr-pi-camera-day-20261021
source /opt/ros/jazzy/setup.bash
bash scripts/camera_day/build_pi.sh \
  /home/richard/orbslam3/ORB_SLAM3 \
  "$HOME/wbr-camera-build-$(date -u +%Y%m%dT%H%M%SZ)"
```

The script records identity, RAM, installed RealSense packages and the actual
colcon output in a new directory; it builds serially with `-j1`. If dependencies
are actually missing, install ordinary packages and retry into a new directory:

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-librealsense2 ros-jazzy-realsense2-camera \
  ros-jazzy-cv-bridge ros-jazzy-yaml-cpp-vendor \
  ros-jazzy-rosbag2-storage-default-plugins python3-colcon-common-extensions
```

`rosdep install --from-paths ros2/wbr_orb_node --ignore-src -r -y` can resolve
remaining declared ROS dependencies from this private checkout. The 2026-10-21
build needed no new apt/pip packages. `WITH_ORB_SLAM3=OFF` intentionally does **not**
install `d435_node`: there is no fake camera-day estimator.

Verified install: `/home/richard/wbr-camera-ros-build-20261021-04/install`.
After sourcing its `setup.bash`, `ros2 pkg executables wbr_orb_node` lists both
nodes. Camera-free startup with `timeout 15s env LD_BIND_NOW=1` and the installed
`d435_node` exits 1 with `existing orb_vocabulary and orb_settings files required`;
no timeout or missing library. This stops before constructing the ORB system.

## Save SDK intrinsics and generate device-specific YAML

With the D435 on USB3, source the new build's `install/setup.bash`. Create a new
evidence directory, save the actual SDK output, and supply its serial explicitly:

```bash
export CAMERA_RUN="$HOME/wbr-camera-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$CAMERA_RUN"
rs-enumerate-devices -c > "$CAMERA_RUN/rs-enumerate.txt" \
  2> "$CAMERA_RUN/rs-enumerate.stderr"
export CAMERA_SERIAL=ACTUAL_SERIAL_FROM_READBACK
python3 scripts/camera_day/sdk_to_yaml.py "$CAMERA_RUN/rs-enumerate.txt" \
  "$CAMERA_RUN/stereo.yaml" --serial "$CAMERA_SERIAL" --mode stereo
python3 scripts/camera_day/sdk_to_yaml.py "$CAMERA_RUN/rs-enumerate.txt" \
  "$CAMERA_RUN/rgbd.yaml" --serial "$CAMERA_SERIAL" --mode rgbd
```

Default profile is **640×480 at 30 Hz**, an operating choice, not a measured Pi
rate. `--width`, `--height`, `--fps` must match the launch profile. SDK intrinsics
blocks are indexed by resolution/format, not rate; supported FPS must still be
confirmed in the actual driver output. Multiple devices require an exact serial.
Outputs are exclusive-created; existing calibration files are never overwritten.

Stereo conversion uses both Y8 IR intrinsic blocks and the SDK's printed
IR1→IR2 extrinsic. For `p_ir2 = R p_ir1 + t`, an identity rotation and negative
x translation give `Stereo.b = -t_x` metres. Nonzero distortion, mismatched
intrinsics, non-horizontal geometry, missing/ambiguous blocks and nonfinite
values are rejected. The converter does not silently rectify pixels.

RGB-D uses **color** intrinsics and depth aligned to the color optical frame.
Brown-Conrady coefficients can be copied to ORB; nonzero inverse/modified Brown
coefficients are rejected because they need a model conversion. ROS RealSense
publishes 16UC1 depth in millimetres. `d435_node` converts that to float metres,
so its settings require `RGBD.DepthMapFactor: 1.0`. Native SDK Z16 values are
not automatically millimetres and must not be fed into this path unchanged.
The measured IR baseline supplies ORB's RGB-D close/far threshold scale.

The fixture is a short excerpt (trailing whitespace trimmed) of the repository's **historical D435i
243322073847 readback from 2026-09-13**, solely to test SDK text formatting and
conversion. It is not the current D435 calibration:
`experiments/2026-09-13-d435i-camera-capture-20260913T015621Z/pi/CAMERA_METADATA_SNAPSHOT/rs-enumerate-complete.txt`.

## Launch camera and SLAM

Terminal 1, stereo IR1/IR2 plus raw depth:

```bash
ros2 launch wbr_orb_node d435_camera.launch.py \
  mode:=stereo serial:="$CAMERA_SERIAL"
```

Terminal 2, after sourcing the same build and setting the same environment:

```bash
ros2 launch wbr_orb_node d435_slam.launch.py mode:=stereo \
  vocabulary:=/home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt \
  settings:="$CAMERA_RUN/stereo.yaml"
```

For RGB-D, stop both launches and start them with `mode:=rgbd` and
`settings:="$CAMERA_RUN/rgbd.yaml"`. RGB-D enables color, depth and alignment;
stereo enables infra1/infra2 and depth. Neither enables gyro/accel. Both use
synchronized framesets, Y8 IR, RGB8 color, Z16 depth, and no point cloud.
Stereo requests emitter off; RGB-D requests it on. The launch passes typed
parameters directly to `realsense2_camera_node`, including dynamic SDK emitter
options. The installed driver version and actual option readback remain untested.

Camera launch accepts `width:=640 height:=480 fps:=30`. Check live CameraInfo
against the generated settings and retain actual parameter readback:

```bash
ros2 param dump /camera/camera > "$CAMERA_RUN/camera-parameters.yaml"
ros2 topic echo /camera/camera/infra1/camera_info --once  # stereo
ros2 topic echo /camera/camera/color/camera_info --once   # RGB-D
ros2 topic echo /d435_orb/status --once
ros2 topic echo /d435_orb/pose --once
```

Only freshly processed, finite ORB tracking poses are published on
`/d435_orb/pose` (`geometry_msgs/PoseStamped`). The stamp is the left image's
stamp for stereo, or color stamp for RGB-D; it is never replaced with `now()`.
`/d435_orb/status` is JSON in `std_msgs/String`, with both source nanosecond
stamps, ORB tracking state, publication flag and application drop count. A status
message while initializing/lost does not establish tracking.

Stereo pairing requires equal source stamps. RGB-D permits at most 10 ms skew
(an unvalidated operating tolerance); both epochs are recorded in status. Input
queues and DDS history default to five frames. ORB executes synchronously in a
single-threaded executor, so slow processing can drop input; no throughput or
latency promise follows. Repeated stamps drop; backward stamps terminate the
process and require a new session. Malformed input and a wrong profile fail
explicitly.

Poses describe the left/color **camera optical frame** in `slam_world` through
`T_world_camera = T_camera_world.inverse()`. ORB map resets, loop closures and
relocalization can change this world frame; no continuous odometry, gravity
alignment, covariance, body calibration or motor-ready output is claimed.
No TF is broadcast by the estimator. The RealSense driver may broadcast its
own sensor geometry.

## Record and replay

In another terminal, record foreground into a new path (Ctrl-C finalizes the bag):

```bash
bash scripts/camera_day/record.sh stereo "$CAMERA_RUN/stereo-bag"
# Or, while running the RGB-D launches:
bash scripts/camera_day/record.sh rgbd "$CAMERA_RUN/rgbd-bag"
```

Records selected raw images, CameraInfo, metadata, raw depth, TF, tracked poses
and status; RGB-D also records aligned depth. Camera images use explicit
best-effort subscriptions and `/tf_static` uses transient-local durability.
No image compression or point-cloud processing is added. Bag throughput,
storage capacity, camera rate and USB behavior need live verification.

For replay, stop the live camera and SLAM, then start a new SLAM process using
the saved matching calibration and `use_sim_time:=true`. Play **only sensor
topics**, excluding recorded estimator output; otherwise old poses/status
would mix with the new run. Example stereo:

```bash
ros2 launch wbr_orb_node d435_slam.launch.py mode:=stereo use_sim_time:=true \
  vocabulary:=/home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt \
  settings:="$CAMERA_RUN/stereo.yaml"
# Other terminal:
ros2 bag play "$CAMERA_RUN/stereo-bag" --clock --topics \
  /camera/camera/infra1/image_rect_raw /camera/camera/infra2/image_rect_raw \
  /camera/camera/infra1/camera_info /camera/camera/infra2/camera_info /tf_static
```

For RGB-D use color and aligned-depth image/CameraInfo topics instead. No looping
or backward seek within one estimator session. ROS header epochs are preserved;
their relationship to camera hardware time and fresh Pi monotonic time remains
unqualified.

## Actual offline validation

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 -m unittest discover -s scripts/camera_day/tests -v
bash -n scripts/camera_day/record.sh scripts/camera_day/build_pi.sh
```

12 fixture tests passed in 0.54 s at initial implementation. Tests exercise SDK
parsing/rejections, exclusive output creation, pure launch parameter selection
and recording arguments with a stub `ros2`. They do not import ROS or compile
the C++ node. The native Pi build and installed camera-free startup passed on
2026-10-21. Installed driver launch, rosbag write/replay, image pairing behavior
under DDS load and live tracked poses remain pending.

Source contracts inspected:
[ORB stereo settings](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/Examples/Stereo/RealSense_D435i.yaml),
[ORB RGB-D settings](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/Examples/RGB-D/RealSense_D435i.yaml),
[SDK enumeration format](https://github.com/realsenseai/librealsense/blob/master/tools/enumerate-devices/rs-enumerate-devices.cpp),
[ROS depth scaling and aligned frames](https://github.com/realsenseai/realsense-ros/blob/ros2-master/realsense2_camera/src/base_realsense_node.cpp),
[ROS camera parameters](https://github.com/realsenseai/realsense-ros/blob/ros2-master/realsense2_camera/launch/rs_launch.py).
RealSense branch sources were inspected on 2026-10-20; live launch compatibility
with the Pi's installed driver version has not been established.
