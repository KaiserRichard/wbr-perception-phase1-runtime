# Current state

Last updated: 2026-10-20 12:20 +07 by Claude. Flow changed today: build first, fix
when it breaks (see `AGENTS.md`).

## Now
1. **Camera + ORB-SLAM3 on the Pi** (skill `wbr-orbslam3-bringup`): D435 (no IMU),
   so stereo or RGB-D. ORB-SLAM3 is built at `~/orbslam3/ORB_SLAM3` (it ran EuRoC
   stereo-inertial earlier); the RealSense examples may need building.
2. Then the ROS 2 wrapper (`third_party/ORB_SLAM3_ROS2`) and robot integration.
3. Parallel: MuJoCo sim of the WBR (DM-jump controller as reference,
   commit 6855ef8, MIT license) -> LQR baseline -> RL comparison.

## What works
- SSH: `ssh wbr-pi5` (192.168.50.2, direct Ethernet).
- Pi power on the 27 W supply: no throttling, 5.08–5.16 V, camera at USB 5000M.

## Known issues
- `pyrealsense2` not installed on the Pi (install it if a tool needs it).
- Root disk: 32 GB microSD, ~6 GB free. Move to the 128 GB card
  (`wbr-storage-migrate`) before recording long bags. A Windows backup image of the
  32 GB card was being made (`D:\wbr-backup\wbr-pi5-32gb-20261020.img`).
- Robot hardware not built yet; masses/inertias for the sim are guesses until the
  lab provides CAD mass properties.
- D435i (with IMU) is away; return date unknown.

## Next step
Plug in the camera and get `stereo_realsense_D435i` (or the RGB-D example) running
on the Pi.
