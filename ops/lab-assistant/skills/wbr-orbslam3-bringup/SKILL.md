---
name: wbr-orbslam3-bringup
description: Bring up ORB-SLAM3 on the Pi 5 using existing stereo data when no camera is available, or stereo/RGB-D with a connected D435. Use when starting camera/SLAM work or when it stops working.
---

# Camera + ORB-SLAM3 bring-up

Goal: real ORB-SLAM3 tracking on the Pi, then a ROS 2 pose from tracked input.
Fix errors as they come. Owner update on 2026-10-20: **no camera this afternoon**;
available Pi is **4 GB RAM with a slow 32 GB microSD**. Live evidence waits for a
camera. A D435 has no IMU; do not use an inertial example or the STM32 as a
replacement camera IMU.

Without a camera, follow [offline-stereo.md](offline-stereo.md) for the existing
EuRoC dataset and the actual ROS wrapper limitations. Make one bounded SSH
attempt; if unavailable, retain the error, run the host wrapper checks and report
the Pi/Ethernet/address blocker. Do not repeatedly reconnect. When connected,
verify hostname, architecture and RAM before building; use **`-j1`** on this Pi.
Preserve existing installs, checkouts and data. Do not free space by deleting,
disabling swap or changing storage partitions.

The following live steps apply only after a camera is available:

1. [PHYSICAL] Camera into a blue USB3 port on the Pi; 27 W supply.
2. Check the camera is seen and see what ORB-SLAM3 already has:
   ```sh
   ssh wbr-pi5 'rs-enumerate-devices -s; ls ~/orbslam3/ORB_SLAM3/Examples/Stereo ~/orbslam3/ORB_SLAM3/Examples/RGB-D | grep -i realsense'
   ```
   (`rs-enumerate-devices` needs `source /opt/ros/jazzy/setup.bash` if not on PATH.)
3. If `stereo_realsense_D435i` / `rgbd_realsense_D435i` are missing, rebuild them
   with RealSense found (install `ros-jazzy-librealsense2` or `librealsense2-dev`
   if CMake can't find `realsense2`):
   ```sh
   cd ~/orbslam3/ORB_SLAM3/build
   cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/opt/ros/jazzy
   make -j1 stereo_realsense_D435i rgbd_realsense_D435i
   ```
   Keep the complete build log; an out-of-memory failure is not permission to
   change storage or discard existing installs.
4. Settings file for this camera: copy `Examples/Stereo/RealSense_D435i.yaml` (or the
   RGB-D one) to `~/wbr-configs/`, and put this camera's intrinsics in it from
   `rs-enumerate-devices -c` (fx, fy, cx, cy, width/height; for stereo also the IR
   baseline -> `Stereo.b`). Match the resolution the example opens (see its
   `cfg.enable_stream(...)` line).
5. Display: ORB-SLAM3's viewer needs a screen. Plug a monitor into the Pi, or use
   `ssh -Y wbr-pi5` with XQuartz on the Mac. Then run, from `~/orbslam3/ORB_SLAM3`:
   ```sh
   ./Examples/Stereo/stereo_realsense_D435i Vocabulary/ORBvoc.txt ~/wbr-configs/d435_stereo.yaml
   ```
   or the RGB-D example with its yaml. Move the camera slowly around a textured
   scene; you should see map points and a trajectory.
6. When it fails, fix the actual error and re-run. Common ones: realsense not found
   at build, no display (Pangolin), wrong resolution in the yaml, "not initialized"
   because the scene has little texture, camera at USB 2 (480M) from a bad
   cable/port, under-voltage (`vcgencmd get_throttled` not 0x0).
7. Note in the session log: which example worked, the yaml used, rough frame rate,
   what you fixed. The pinned `third_party/ORB_SLAM3_ROS2` wrapper currently has
   no stereo mode; see the offline guide before attempting ROS integration.
   A topic message alone does not prove tracking, and a camera pose is not a
   calibrated robot body pose.
