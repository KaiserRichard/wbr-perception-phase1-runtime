# Revision 3 reading provenance

Checked on 2026-10-14. Readings teach concepts; the project gate meanings come
from the existing learning/course/progress decks and project preparation docs.
No gate criteria, sensor profile, runtime behavior or safety policy changed.

| Use | Primary source |
|---|---|
| N0 | [Raspberry Pi hardware: power and cooling](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html) |
| N1 | [librealsense Troubleshooting Q&A: camera USB access](https://github.com/realsenseai/librealsense/wiki/Troubleshooting-Q%26A) |
| N2 | [Kalibr IMU noise model: noise, bias and Allan analysis](https://github.com/ethz-asl/kalibr/wiki/IMU-Noise-Model) |
| N3 | [Official ROS 2 Jazzy tutorials](https://docs.ros.org/en/jazzy/Tutorials.html) |
| N4 | [Campos et al., ORB-SLAM3 (2021)](https://arxiv.org/abs/2007.11898) |
| N5 | [Official ROS 2 tracing tutorial](https://docs.ros.org/en/jazzy/Tutorials/Advanced/ROS2-Tracing-Trace-and-Analyze.html) |
| N6 | [Barfoot, State Estimation for Robotics, second edition](https://asrl.utias.utoronto.ca/~tdb/bib/barfoot_ser24.pdf) |
| N7 | [STMicroelectronics STM32H7 online training: Independent watchdog](https://www.st.com/content/st_com/en/support/learning/stm32-online-training/stm32h7-online-training.html) |

Supplementary method readings on the references page:

- [Burri et al., EuRoC datasets (2016)](https://projects.asl.ethz.ch/datasets/).
- [Furgale, Rehder and Siegwart, Unified Temporal and Spatial Calibration for Multi-Sensor Systems (2013), listed in Kalibr's bibliography](https://github.com/ethz-asl/kalibr/wiki).
- [Kalibr camera–IMU guide](https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration).
- [Forster et al., On-Manifold Preintegration (T-RO 2017; preprint submitted 2015)](https://arxiv.org/abs/1512.02363).
- [Sturm et al., RGB-D SLAM benchmark (2012)](https://cvg.cit.tum.de/data/datasets/rgbd-dataset).
- [Zhang and Scaramuzza, trajectory evaluation tutorial (2018)](https://rpg.ifi.uzh.ch/docs/IROS18_Zhang.pdf).
- [Maintainer's evo metric documentation](https://github.com/MichaelGrupp/evo/wiki/Metrics).

The ROS documentation website denied automated browsing through Anubis. Verified
its content through the official ROS documentation source and a ROS documentation
mirror, while retaining the normal reader-facing documentation links:

- [Official Jazzy tutorials source](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials.rst).
- [Official Jazzy tracing tutorial source](https://raw.githubusercontent.com/ros2/ros2_documentation/jazzy/source/Tutorials/Advanced/ROS2-Tracing-Trace-and-Analyze.rst).
- [ROS documentation mirror](https://repo.test.ros2.org/en/jazzy/Tutorials.html).

Barfoot's linked author copy is an updated September 2026 draft of the second
edition published in 2024. These are reading recommendations, not tool-version
or platform-compatibility endorsements. Allan analysis does not replace the N2
soak. ROS tracing's callback duration does not establish complete pose latency.
Barfoot covers transforms, not the project's health protocol. A watchdog reset
is not a demonstrated balancing fallback. Notes retain these distinctions.
