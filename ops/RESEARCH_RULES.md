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
- WBR-Control owns control work; WBR-Perception owns camera work. Control must
  not touch perception branches/files or the d/h/j accounts, even for pings.
- Before a new full training experiment, run one 10–20 minute pilot seed,
  targeting ~200k policy steps; report actual duration/steps. Print episode
  length, return and reward-term magnitudes. Plot episode length and return
  against steps; proceed only when the learning curve clearly improves.
- First sanity-check reward scale at the actual evaluation tolerances: a
  tolerance-sized error must cost a visible few percent of the alive reward.
  For a state term, $c_x = s Q_{xx} x_{\mathrm{tol}}^2$. With alive reward 1,
  $Q_{xx}=40$ and $x_{\mathrm{tol}}=0.02$ m, scale 0.1 costs 0.0016 (0.16%);
  scale 2 costs 0.032 (3.2%). This illustrates the check, not a v3 config change.
- Every RL result includes episode-length and return learning curves versus
  policy steps and a per-seed result table. Any future v3 full comparison uses
  at least five training seeds per arm after its one-seed pilot passes; no v3
  launch or frozen-v2 extension is implied. Keep evidence to config, commit, seeds, final metrics and
  those curves. Reports fit one page; no mass hashing or DECISIONS.md /
  DOCUMENTATION_LOG.md entries. Existing historical records remain intact.
- Claude explicitly requested that already-running PPO v2 seeds 3/4 finish
  unchanged. These pilot/reward requirements gate future experiments; they
  do not authorize v3 or modify the active batch.
- Legacy PPO v2 saved optimizer statistics but no episode-length/return
  histories. Mark those curves unavailable; do not fabricate them or relabel
  optimizer losses as returns. New pilots must record both histories.
