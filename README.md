# WBR Perception Phase 1 Runtime

Runtime and experiment workspace for the wheel-biped robot perception project.

Current Phase-1 goal:

1. understand and benchmark official ORB-SLAM3;
2. validate Intel RealSense D435i sensing;
3. record repeatable ROS 2 sensor datasets;
4. validate ORB_SLAM3_ROS2 offline and live;
5. characterize failure modes before WBR integration.

Architecture:

D435i
→ ORB-SLAM3 / VIO
→ ROS 2
→ state estimation / autonomy
→ high-level references
→ STM32H7

STM32H7 retains ownership of hard-real-time balance, LQR, VMC, PID/PD,
jump control, actuator torque, CAN, and safety.
