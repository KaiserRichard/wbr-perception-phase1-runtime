# R1b: independent second opinion on the estimator (read slides_roadmap/COMMON.md first)
The owner asked us not to be biased or jump to conclusions. Another worker is writing R1 in parallel;
do NOT read research/R1_algorithms.md. Start from the requirements, not from ORB-SLAM3:
a wheel-biped robot, Pi 5 8 GB CPU only, D435i (stereo IR + IMU, also depth), indoor lab, later
navigation, balance owned by the STM32. Question: what is the best estimator/mapping approach to
reach a working robot demo soon and a credible system later?
Consider at least: ORB-SLAM3 (stereo-inertial, RGB-D), OpenVINS, VINS-Fusion, Basalt, Kimera-VIO,
RTAB-Map (with its own odometry or an external one), DROID/learning-based options (and why they
do or do not fit a Pi), and "no SLAM yet": wheel odometry + body IMU + D435i depth for obstacles.
For each: evidence on ARM/Pi performance, robustness for this platform, maintenance and ROS 2 Jazzy
support, licence, integration effort from where we are. Score them in a table with explicit
criteria and weights, show where the evidence is weak, and give a recommendation with what would
change it. Write `slides_roadmap/research/R1b_algorithms_independent.md`, cited.
