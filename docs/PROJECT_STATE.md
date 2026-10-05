# Project State

> This file is the canonical short summary of current WBR Phase-1 state.
> Update it from repository/experiment evidence. Do not treat the historical draft below as automatically current.

## Hardware

- Raspberry Pi 5: 8 GB RAM.
- Intel RealSense D435i: available on long-term loan.
- System/project storage target: 128 GB NVMe.
- Large research-data storage target: separate 64 GB USB drive.
- Controller side: STM32H7 for hard-real-time balancing/control/safety.

## Primary software stack

- Ubuntu/Linux.
- ROS 2 Jazzy.
- Intel RealSense / realsense-ros.
- ORB-SLAM3.

## Historical gate picture — VERIFY BEFORE USE

| Gate | Historical status | Notes |
|---|---|---|
| N0 Platform | likely strong evidence | Verify current Pi state |
| N1 D435i physical access | likely strong evidence | Verify if environment changed |
| N2 Raw IR + IMU qualification | strong historical evidence | Calibration qualification remains distinct |
| N3 ROS 2 sensor pipeline | likely OPEN/current | Previous physical attempts exist; inspect them first |
| N4A upstream ORB-SLAM3 dataset baseline | UNKNOWN / not qualified here | Build artifacts are not PASS evidence |
| N4B D435i offline VIO | NOT ASSUMED | Requires trusted calibration/timing |
| N4C D435i live VIO | NOT ASSUMED | Do not skip earlier gates |

## Current verified gate

**OPEN — update after current repository/evidence audit.**

## Current blocking question

**OPEN — write one precise technical uncertainty here.**

Example:

> Determine exactly what prevented the previous N3 physical ROS 2 attempt from satisfying record/replay qualification.

## Evidence quality rule

A screenshot, successful build, or one successful launch is not enough to promote a gate to PASS.
