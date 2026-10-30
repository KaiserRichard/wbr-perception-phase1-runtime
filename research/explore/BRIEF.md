# Explore brief (2026-10-30): visible capability upgrades for the WBR

The owner wants research that adds clearly visible **new capabilities** to the wheel-bipedal robot (WBR) using AI:
computer vision, reinforcement learning, learned SLAM, high-level autonomy. Not only protocol increments. Map the
landscape and what is **feasible for us**.

What we have:
- Hardware:
  - Pi 5 8 GB with no accelerator; RealSense D435i (lab loan) or Pi Camera v2; Intel MacBook (no NVIDIA GPU).
  - Nucleo-F446RE bench with MPU6050 + CAN.
  - The robot arrives in Nov 2026: STM32H723 + BMI088, DM-J4310 hip and DM-H6215 wheel motors over CAN, five-bar legs; Pi-to-MCU advisory over COBS+CRC UART, no micro-ROS.
- Software:
  - ORB-SLAM3 on the Pi.
  - Depth-geometry obstacle detector giving NONE / JUMP / STOP / UNCERTAIN advice to the MCU.
  - MuJoCo planar model + LQR; a weak PPO baseline; a 3D MuJoCo twin driven by the IMU.
  - Course work: RTP video streaming to an edge AI server (CN) and a freshness supervisor (OS).
- Recorded data: 24 Oct D435i RGB-D bags of boxes on a table (`~/wbr-evidence-archive/mobile-demo-20261024-01/`).

Rules:
- English.
- Cite papers and repos with title, year, venue and a link you opened; mark UNVERIFIED otherwise; never invent.
- Be concrete about compute: model size, FPS on Pi 5 CPU vs Hailo-8L vs Jetson Orin Nano, where published.
- Write ONE file `research/explore/<id>.md`, at most ~150 lines. Do not commit and do not edit other files.
- Sections:
  - (1) state of the art, 5–10 key works;
  - (2) what is visibly "wow" for a demo;
  - (3) what is actually researchable/novel for us;
  - (4) feasibility on our hardware now and after the robot arrives;
  - (5) what hardware/compute to request from the lab, and why;
  - (6) a 2-week prototype plan using our rig/data.

Topics:
- **X1** `x1-ai-perception.md`: AI perception for locomotion and traversability: semantic segmentation, learned elevation/traversability maps, stair/step/gap detection, RGB-D obstacle classification, edge accelerators (Raspberry Pi AI HAT+ / Hailo-8L, Coral, Jetson).
- **X2** `x2-rl-locomotion.md`: reinforcement learning for wheel-legged/wheel-bipedal robots: balance, jumping, stair climbing, sim-to-real, teacher–student with height maps, MuJoCo MJX / Isaac Lab / Genesis; GPU hours needed; how to go from our planar MuJoCo model to a trainable 3D model.
- **X3** `x3-learned-slam.md`: visual SLAM + AI: learned features (SuperPoint/LightGlue, XFeat), DROID-SLAM/DPV-SLAM, semantic and dynamic-object SLAM (YOLO masks + ORB-SLAM3), on-device vs edge-offloaded; which of these improves the WBR in practice.
- **X4** `x4-autonomy-hri.md`: high-level autonomy and interaction: vision-language models commanding robots ("go to the red box"), person following, object-goal navigation, Nav2 + elevation mapping; edge offload over our RTP pipeline with freshness guarantees (link to the CN/OS work).
