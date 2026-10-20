---
name: wbr-orbslam3-bringup
description: Plug in the RealSense camera and get ORB-SLAM3 running live on the Pi 5 (stereo or RGB-D for the D435). Use when starting camera/SLAM work or when it stops working.
---

# Camera + ORB-SLAM3 bring-up

Goal: live ORB-SLAM3 tracking from the D435 on the Pi, with a viewer showing the
map. Fix errors as they come.

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
   make -j3 stereo_realsense_D435i rgbd_realsense_D435i
   ```
   (`-j3` leaves headroom on the Pi's 8 GB; go back to `-j2` if it runs out of memory.)
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
   what you fixed. Next: the ROS 2 wrapper in `third_party/ORB_SLAM3_ROS2` so poses
   are published for the robot.
