# Camera research — short status report

Date: 2026-10-21, 07:58 +07. Status: IN PROGRESS; not a completed milestone.

## Goal
Run borrowed D435i with ORB-SLAM3 stereo and RGB-D on the Pi, then publish a
ROS 2 pose, record a 2–3 minute bag and compare three replay trajectories.

## Actual results
- SSH works: `ssh wbr-pi5` → `richard@192.168.50.2`.
- Pi reports aarch64, 3.9 GiB RAM. The larger SG128 card boots; EXT4 expanded
  successfully. Root filesystem: 113 GiB, 88 GiB free.
- Connected camera: RealSense D435i, serial `317422076650`, firmware
  `5.17.3.10`, USB 5000M. It is the borrowed IMU-equipped camera, not the D435.
- Read SDK calibration and generated local 640×480/30 Hz settings. No calibration
  routine, calibration write, firmware update or robot/RPLIDAR configuration change.
  Native stereo changes operating exposure/emitter options; those are distinct
  from calibration. Original robot driver settings should be reapplied on return.
- First native stereo attempt failed: `Pangolin X11: Failed to open X display`.
  Installed Xvfb; second attempt initialized a map with **733 points**.
- Native stereo currently receives/processes frames; repeated dropped-frame
  messages occur. This is initial map creation, not a validated moving trajectory
  or a measured real-time performance result. Run is bounded to 55 seconds.
- ROS wrapper worker g/Astra Ultra is compiling serially in an isolated checkout.
  First attempt omitted an archive header; copied unchanged header and retried.
  Second attempt failed on Pangolin/OpenGL compile definitions; CMake fix applied.
  Third build is pending. No ROS tracked pose demonstrated yet.

## Remaining work
1. Finish and independently verify ROS build; inspect stereo run outcome.
2. Run native RGB-D with SDK depth scale; then verify live ROS pose/status.
3. Agree a physical motion method that preserves the borrowed camera mount.
4. Record loop bag, replay three times, save and compare trajectories.

## Traceability
- Base: `8195d7f`; branch: `chatgpt/20261021-camera-day`.
- Pi evidence: `/home/richard/wbr-evidence/camera-day-20261021-01/`.
- Build: `/home/richard/wbr-camera-ros-build-20261021-03/`.
- Worker receipts: `/private/tmp/wbr-camera-day-20261021/ros-worker*`.
- Existing simulation/training and owner-only gain exercise were not modified.
- No camera milestone PR merged and no Claude review claimed for this session.
