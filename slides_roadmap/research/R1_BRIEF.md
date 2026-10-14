# R1: Algorithm and software path (read slides_roadmap/COMMON.md first)
Write `slides_roadmap/research/R1_algorithms.md` (aim 3–6 pages, dense, cited).
1. Is ORB-SLAM3 stereo-inertial the right production estimator for a D435i on a Pi 5 inside a
   wheel-biped robot? Compare briefly with OpenVINS, VINS-Fusion, Basalt, Kimera-VIO, RTAB-Map,
   and the "VIO + robot_localization with wheel odometry" pattern: ARM/Pi feasibility and reported
   CPU/latency, robustness to fast rotation and vibration, map reuse/relocalization, ROS 2 Jazzy
   support and maintenance status, licence. Recommend a default and a fallback, with switch triggers.
2. The ROS 2 integration path for ORB-SLAM3 (or the default): wrappers for ROS 2 Jazzy that exist,
   their state; or our own thin node around the SDK program we already have. Topics, TF
   (map→odom→base_link, camera frames), QoS, rosbag2, and what Nav2 / navigation needs as input.
3. Wheel odometry and the body IMU: when and how to add them (loose coupling via robot_localization
   or ORB-SLAM3's own options), what the STM32 must publish, timestamp/clock-sync method
   (e.g. PTP/chrony, hardware timestamp on UART frames), and why not to fuse IMUs naively.
4. Calibration toolchain in order: camera intrinsics check, Kalibr camera–IMU (AprilGrid), Allan
   variance tool for IMU noise, time offset; practical durations and pitfalls on D435i.
5. Performance plan on Pi 5: resolution/FPS choices, threads, CPU governor, cooling, what to
   measure (P50/P95/P99 latency, dropped frames, CPU, temperature), realistic targets with sources.
End with: recommended software stack per phase (table: phase | software | why | source).
