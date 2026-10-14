# J1 — Component inventory: engine-agnostic vs engine-specific

Read COMMON.md in this directory first and follow it. Output: J1_components.md (this directory).

Produce a component inventory of the software between "today" (native librealsense recorder writing .db3,
patched ORB-SLAM3 D435i example, numpy ATE/RPE tool, demo plot) and "VIO running on the robot and
reporting usable state to the STM32". Candidate components to assess (add/remove as evidence demands):
1. Recording/replay format and converters: librealsense .db3 (rosbag2 since librealsense 2.56?) -> EuRoC ASL
   folder, TUM, ROS 2 bag with standard sensor_msgs, ROS 1 bag for Kalibr. Which existing tools already do
   each conversion (rosbags library, kalibr_bagcreater, rs-convert, etc.)? Verify the .db3 schema claim
   from librealsense source.
2. Input association / timestamp validation (stereo pairing, IMU bracket checks, accel->gyro interpolation,
   gap/reversal detection, global-time vs hardware-time domains in librealsense). Is d435i_input.h reusable
   across engines? What does each engine expect (ORB: per-frame IMU vector; OpenVINS/VINS: ROS topics or
   per-sample feed; Basalt)?
3. Calibration conversion: Kalibr camchain/imu yaml -> ORB-SLAM3 settings yaml, OpenVINS yaml, VINS-Fusion,
   Basalt json. Conventions (T_cam_imu direction, timeshift sign, noise density vs discrete). Does any
   maintained converter exist?
4. Estimator adapter boundary: a thin engine interface (feed images/IMU, get pose + state + reset/map epoch).
   What state/health information does each engine actually expose (ORB GetTrackingState, map changes via
   MapChanged/GetLastBigChangeIdx, Atlas; OpenVINS state/initialized; VINS failure detection)? Cite headers.
5. Pose output and frame transform (camera/IMU-camera frame -> base_link), REP-103/105, map vs odom.
6. Health/state monitor and the Pi->STM32 message (R2 already proposes a contract; only assess what is
   engine-specific inside it, e.g. covariance availability, reset semantics).
7. Runtime profiling: per-stage latency P50/P95/P99, queue depth, drops, CPU/freq/temp/throttle. Which
   existing tools (ros2_tracing, perf, psutil, vcgencmd, rs frame metadata) suffice?
8. Evaluation: ATE/RPE (exists), reference-free checks, repeatability harness; dataset regression runner.
9. Pi<->STM32 link codec/receiver reference (host-side encoder/decoder + fault-injection fixtures).
For each: purpose; engine-agnostic? (yes/no/partly and why); exists in repo (path) / exists upstream
(link) / must be written; depends on hardware or lab access?; minimal test that proves it without hardware.
End with a table and a dependency graph (text) showing which components block which gates (N3..N7).
