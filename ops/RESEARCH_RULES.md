# WBR working rules

Build first, fix when it breaks. These are the few rules that still apply.

## System
- Raspberry Pi 5 (Ubuntu 24.04, ROS 2 Jazzy) runs perception: camera, ORB-SLAM3,
  mapping. ORB-SLAM3 is built at `~/orbslam3/ORB_SLAM3` on the Pi.
- The STM32H7 runs balance, LQR, VMC, the state machine and motor safety. If the Pi
  or SLAM fails, the robot must keep balancing, so the Pi's pose is optional input
  to the controller, never a hard dependency.
- Camera now: Intel RealSense D435 (no IMU), so use stereo or RGB-D ORB-SLAM3.
  The D435i (with IMU) is away; stereo-inertial waits for it.

## Practical habits
- When numbers come from different clocks (camera, ROS, Pi system time), don't
  subtract them directly; convert to one clock first. Bugs here look like huge or
  negative latencies.
- Keep the camera IMU and the robot's body IMU separate unless you have a reason.
- When reporting a result, say whether it was actually run or is a guess.

## Simulation and learned control (MuJoCo, RL vs LQR)
- Simulation only; nothing goes to the real robot without the owner asking.
- Get the LQR baseline working in MuJoCo first, then train RL and compare on the
  same model and the same pushes/disturbances. Use a few random seeds.
- Code under `sim/`; checkpoints, logs and videos stay out of git.
