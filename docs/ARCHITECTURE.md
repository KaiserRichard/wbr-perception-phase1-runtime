# WBR Phase-1 Perception Architecture

## Responsibility boundary

```text
Intel RealSense D435i
        |
        v
Raspberry Pi 5 / Linux / ROS 2
        |
        |  perception / VIO / SLAM / mapping / health
        v
Perception-state interface
        |
        v
STM32H7 real-time controller
        |
        |  body estimation / balance / LQR / VMC / FSM / safety
        v
Actuation
```

Critical principle:

> Loss of ROS, SLAM, or the Raspberry Pi must not directly imply immediate loss of balance.

## Sensor ownership

### D435i camera IMU

Primary role:

- camera-centric visual-inertial perception.

### Body IMU

Primary role:

- real-time robot body/control estimation on STM32.

Do not merge the two IMUs conceptually until clock, frame, calibration and ownership questions are explicitly resolved.

## Frames

Relevant frames may include:

- `world`
- `map`
- `odom`
- `base_link`
- `body`
- `imu_body`
- `camera`
- `camera_optical`
- `imu_camera`
- `left_camera`
- `right_camera`

Every pose/transform result should explicitly define:

- reference frame;
- child frame;
- axis convention;
- origin;
- timestamp.

## Timestamp chain

Potential timestamps include:

```text
physical capture
-> device/hardware timestamp
-> driver timestamp
-> ROS message header timestamp
-> ROS publish time
-> subscriber receipt
-> processing start/end
-> estimator output timestamp
```

Do not subtract timestamps from different clock domains until their relationship is established.

## Validation layers

```text
hardware
-> USB/device
-> raw sensor streams
-> timestamps
-> ROS wrapper
-> topics/QoS
-> rosbag record/replay
-> calibration
-> ORB-SLAM3
-> trajectory
-> quantitative evaluation
```
