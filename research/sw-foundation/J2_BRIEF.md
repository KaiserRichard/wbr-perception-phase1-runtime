# J2 — Architecture alternatives and prior art for the runtime around VIO

Read COMMON.md in this directory first and follow it. Output: J2_architecture.md (this directory).

A hypothesis on the table (NOT a decision): build first (a) a ROS 2 pose/health node, (b) a Pi->STM32
message contract, (c) a latency/CPU logger. Evaluate it against alternatives, adversarially:
A. ROS 2-first: thin rclcpp node around the engine, everything as topics, rosbag2 as the data format.
B. Native-first: keep a librealsense->engine native process (no ROS in the hot path) with a small C++
   adapter library; add ROS 2 only as an output/visualisation bridge later.
C. Data-first: build the dataset/replay/conversion + evaluation harness before any runtime node, so every
   engine (ORB, OpenVINS, Basalt) can be run on the same retained D435i takes.
D. Off-the-shelf wrapper stacks (realsense-ros + community ORB-SLAM3 ROS 2 wrappers, Isaac ROS visual
   SLAM — check if it is relevant on Pi/ARM without GPU, OpenVINS ros2 node, RTAB-Map with external odom).
For each: what must be written, what is reused, risk, what it blocks/unblocks, and how it handles the
"Pi fails -> robot keeps balance" boundary. Use prior art for the Pi->controller state message:
MAVLink ODOMETRY (reset_counter, quality, estimator_type, covariance) and PX4's external-vision/VIO
interface (EKF2 rejection, timestamps), ArduPilot VISION_POSITION_ESTIMATE/visual odometry, ROS
diagnostic_msgs/diagnostic_updater, nav_msgs/Odometry covariance conventions. Cite spec pages/source.
Also: is ROS 2 latency/jitter on Pi 5 a measured concern (cite measurements: e.g. ros2 performance_test,
ros2_tracing papers) or not; what executor/QoS pitfalls matter for 30 Hz stereo + 200 Hz IMU.
Finish with: a recommended build order (first 3-5 components), why, what you are least sure of, and the
experiment that would overturn the recommendation.
