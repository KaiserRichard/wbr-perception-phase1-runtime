# Camera-free stereo continuation on the 4 GB Pi

Prepared 2026-10-20; **Pi execution and ROS pose remain blocked**. One SSH attempt
to `wbr-pi5` (`192.168.50.2`) timed out. The owner must restore Pi power/Ethernet
and confirm its reachable address. No camera is available for live verification.

## Existing input and executable

Use the existing EuRoC **MH_01_easy / MH01** sequence. On the Mac,
`/Users/quockaiser/datasets/euroc/MH01/mav0/{cam0,cam1}/data.csv` each contains
3,682 rows; the first image exists on both sides. Each CSV has SHA-256
`62db628a8e6358f43df81e66ddb4597ab40b19a10f3d6cd80cc04d590b5adb12`.
This is a metadata inspection, not a full pixel integrity check or a SLAM run.

The earlier [Pi MH01 run record](../../../../experiments/2026-10-13-n4a-euroc-mh01/REPORT.md)
places the dataset at `/home/richard/datasets/euroc/MH01` and ORB at
`/home/richard/orbslam3/ORB_SLAM3`. Those Pi paths are **historical, not reverified**.
Reuse them if present; do not download another multi-GB dataset or copy it into
git. Ask the conductor if the data are absent.

The pinned upstream
[`stereo_euroc`](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/Examples/Stereo/stereo_euroc.cc)
uses `System::STEREO`, reads `mav0/cam0/data` and `mav0/cam1/data`, and takes an
integer-nanosecond timestamp list. Use `Examples/Stereo/EuRoC.yaml`, not the
inertial or RealSense calibration. The stock example enables its Pangolin viewer.

## First real attempt after connectivity is restored

Run in **bash on the Pi**, with a local display or working X forwarding.
Record identity and memory first. Keep source/build paths as they already exist;
the output directory below is new. This does not touch the shared runtime
checkout, motors, STM32 or storage configuration.

```bash
set -o pipefail
hostname
uname -m
head -5 /proc/meminfo
df -h /
source /opt/ros/jazzy/setup.bash
export PI_ORB="$HOME/orbslam3/ORB_SLAM3"
export PI_DATA="$HOME/datasets/euroc/MH01"
export PI_RUN="$HOME/wbr-evidence/stereo-mh01-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$HOME/wbr-evidence"
mkdir "$PI_RUN" || exit 1
export PI_TIMES="$PI_ORB/Examples/Stereo/EuRoC_TimeStamps/MH01.txt"
export PI_SETTINGS="$PI_ORB/Examples/Stereo/EuRoC.yaml"

# Build only if the existing example is absent. Do not invoke build.sh's
# unrestricted parallel build on this 4 GB Pi.
if ! test -x "$PI_ORB/Examples/Stereo/stereo_euroc"; then
  cmake --build "$PI_ORB/build" --target stereo_euroc --parallel 1 \
    2>&1 | tee "$PI_RUN/build.log" || exit 1
fi

cd "$PI_RUN" || exit 1
"$PI_ORB/Examples/Stereo/stereo_euroc" \
  "$PI_ORB/Vocabulary/ORBvoc.txt" "$PI_SETTINGS" \
  "$PI_DATA" "$PI_TIMES" mh01_stereo \
  2>&1 | tee stereo.log
stereo_status=${PIPESTATUS[0]}
printf '%s\n' "$stereo_status" > stereo.exit
```

If the actual failure is a missing display, preserve `stereo.log`, create a new
run directory and retry with a working display. Alternatively install ordinary
`xvfb`/`xauth` dependencies and prefix the same executable with `xvfb-run -a`;
OpenGL/Pangolin compatibility on this Pi remains untested. Do not claim that
setting an environment variable disables the viewer in the stock source.

If the build directory is absent, retain that error. Configure the existing ORB
checkout with `cmake -S "$PI_ORB" -B "$PI_ORB/build" -DCMAKE_BUILD_TYPE=Release`
and retry the single target with `--parallel 1`. Preserve existing compatibility
patches and dependency builds. Fix only the concrete configuration/compiler
error encountered; do not replace the installed ORB checkout.

The optional suffix above produces `f_mh01_stereo.txt` and
`kf_mh01_stereo.txt` in `PI_RUN`. After the attempt, retain these files and logs
outside git and capture:

```bash
git -C "$PI_ORB" rev-parse HEAD > "$PI_RUN/orb-revision.txt"
git -C "$PI_ORB" diff --binary > "$PI_RUN/orb-local.patch"
sha256sum "$PI_ORB/Examples/Stereo/stereo_euroc" \
  "$PI_ORB/lib/libORB_SLAM3.so" "$PI_ORB/Vocabulary/ORBvoc.txt" \
  "$PI_SETTINGS" "$PI_TIMES" "$PI_DATA/mav0/cam0/data.csv" \
  "$PI_DATA/mav0/cam1/data.csv" > "$PI_RUN/inputs.sha256"
ldd "$PI_ORB/Examples/Stereo/stereo_euroc" > "$PI_RUN/linked-libraries.txt"
```

A zero exit code alone is insufficient. Inspect the actual trajectory for
nonempty finite timestamp/translation/quaternion rows and tracking/loss output.
Report the real input identity, exit status and pose count. Stereo output uses
the camera pose; previous inertial MH01 accuracy numbers use a different frame
and are not new stereo results. No live rate or accuracy claim follows.

## ROS continuation: existing packages and the remaining gap

Two existing wrappers were inspected before any ROS changes:

| Package | Actual interface at this revision | Limitation |
| --- | --- | --- |
| `orb_slam3_ros2` in `third_party/ORB_SLAM3_ROS2` | `imu_mono_node_cpp`; image `camera/infra1/image_rect_raw`, IMU `camera/imu`; `orb_odom` (`nav_msgs/Odometry`) | Only `monocular` and `imu-monocular`; no right-image subscription or `TrackStereo` |
| `wbr_orb_node` in `ros2/wbr_orb_node` | `orb_node`; configurable left/right/combined camera IMU topics; `diagnostic_odometry` | Real build constructs `IMU_STEREO`; requires IMU coverage and measured optical-to-camera-IMU geometry; default build is synthetic |

Upstream wrapper pin: `efd7acd9ea31bfdbcd843a4c90eeaa85f7e80dd8`.
Its [node source](https://github.com/gjcliff/ORB_SLAM3_ROS2/blob/efd7acd9ea31bfdbcd843a4c90eeaa85f7e80dd8/src/imu_mono_realsense.cpp)
hardcodes RealSense settings and publishes its stored transform on a wall timer
with `now()`, without a tracking-state check. Thus `timeout 10 ros2 topic echo
/orb_odom --once` can succeed without a freshly tracked input. Do not use that
alone as milestone evidence. EuRoC cannot simply be remapped into its RealSense
calibration.

Its [CMake configuration](https://github.com/gjcliff/ORB_SLAM3_ROS2/blob/efd7acd9ea31bfdbcd843a4c90eeaa85f7e80dd8/CMakeLists.txt)
expects the nested **gjcliff ORB fork**, including its CMake package and custom
map APIs; it is not a drop-in consumer of the existing stock ORB library.
The nested pin is `0f29ad5f563269a13109d81eb886916cc5960136`. The submodule is
unpopulated in this Mac worktree; source inspection used the pinned GitHub files.

On the Pi, use a conductor-provisioned **dedicated task checkout**, never the
shared `wbr-perception-phase1-runtime` checkout. Once that checkout and the
upstream wrapper's existing fork/dependencies are present, the precise package
build attempt is:

```bash
source /opt/ros/jazzy/setup.bash
export WBR_PI_TASK="$HOME/wbr-pi-orbslam-pose" # proposed dedicated path, not verified
export CMAKE_BUILD_PARALLEL_LEVEL=1
export MAKEFLAGS=-j1
colcon --log-base "$PI_RUN/ros-log" build \
  --base-paths "$WBR_PI_TASK/third_party/ORB_SLAM3_ROS2" \
  --packages-select orb_slam3_ros2 --executor sequential --parallel-workers 1 \
  --build-base "$PI_RUN/ros-build" --install-base "$PI_RUN/ros-install" \
  2>&1 | tee "$PI_RUN/ros-build.log"
```

This builds the existing package; it does **not** add stereo support. The next
integration change must add stereo input to that wrapper and publish only
tracked finite poses stamped with their source image epoch. Preserve its
architecture and avoid creating a third wrapper. Such upstream edits are outside
this track's allowed files and were not attempted while the Pi was unreachable.
After implementation, start its actual stereo executable with matching dataset
calibration, replay real stereo input, and capture a bounded
`timeout 10 ros2 topic echo <actual-pose-topic> --once` alongside tracking and
source-stamp evidence. No working stereo ROS command is claimed at this revision.

The existing host check is:

```sh
make -C ros2/wbr_orb_node test
```

All 19 tests passed on the Mac on 2026-10-20. This compiles the ROS-free core with
the fake engine; it does not compile `src/node.cpp`, ament, ORB or the upstream
wrapper, and no synthetic pose counts as SLAM. The local wrapper's
[README](../../../../ros2/wbr_orb_node/README.md) retains its separate
stereo-inertial build/replay instructions for recordings with real camera IMU.

**Recommendation:** restore Pi connectivity, run the existing native MH01 stereo
example with serial builds, then have the conductor allocate the upstream
wrapper changes needed for stereo and source-stamped tracked poses. Live D435
evidence waits for the camera.
