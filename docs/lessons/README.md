# WBR and micro-ROS firmware study pack

This pack is for a fourth-year electronics student who already knows STM32,
C, UART, and timers, and is learning CAN protocols, micro-ROS, LQR, and VMC.
It uses the lab AGV firmware and the previous WBR jump firmware as two separate
systems. Code facts include file and line citations; derived conclusions are
marked **INFERRED**. Planned tests are not presented as executed results.

## Reading order

1. [01 — CAN and RobStride](01_can_and_robstride.md)
2. [02 — micro-ROS on an STM32](02_micro_ros_on_stm32.md)
3. [03 — Differential-drive AGV base firmware](03_agv_base_firmware.md)
4. [04 — WBR balance control: LQR and VMC](04_wbr_balance_lqr_vmc.md)
5. [05 — WBR jump sequence and a perception gate](05_wbr_jump_sequence.md)
6. [06 — Bench test scenarios](06_test_scenarios.md)

## Lesson summaries

**01 — CAN and RobStride.** Introduces differential bus signaling, classic
CAN frame fields, arbitration, ACK and error confinement, termination, and the
monitor's exact 42 MHz / 1 Mbit/s silent-mode timing (`tools/can_monitor/firmware/can_rx.c:41-50`). It then decodes the
RobStride 29-bit identifier and shows how its 16-bit engineering values are
quantized with a worked zero-position and gain example.

**02 — micro-ROS on an STM32.** Explains the Agent/client split and XRCE-DDS
session lifecycle, then follows data through USB CDC or UART, handles, and the
rclc executor. It covers finite middleware pools, endpoint QoS compatibility,
the reported Reliable/Best Effort safety-filter mismatch, and MCU-local stale
data rules (`Microros_H723_USB/Core/Src/freertos.c:334-365`; `docs/interfaces/TERRAIN_ADVISORY_TOPIC.md:30-42`).

**03 — Differential-drive AGV base firmware.** Traces `/cmd_vel` through
inverse kinematics, common-factor saturation, and periodic motor setpoints.
Worked numeric examples use the stated 0.060 m wheel radius and 0.345 m track
width. The lesson also explains the 500 ms watchdog and SBUS manual, arm,
no-link, and latched E-stop behavior (`Microros_H723_USB/User/Algorithm/Kinematics/kinematics.c:8-23`; `Microros_H723_USB/User/APP/motor_task.c:479-530`; `Microros_H723_USB/User/Bsp/bsp_sbus.c:162-260`).

**04 — WBR balance control: LQR and VMC.** Interprets the six feedback signals
visible in each side's source, explains gain scheduling as cubic functions of
leg length, and derives the transpose-Jacobian effort map used by the five-bar
VMC. Nominal task rates are separated from measured timing guarantees (`DM-jump/User/APP/chassisR_task.c:180-212`; `DM-jump/User/Algorithm/VMC/VMC_calc.c:160-175,220-228`).

**05 — WBR jump sequence and a perception gate.** Describes the R1 hold trigger,
crouch/thrust/retract/land sequence, target lengths, and shared side-transition
counters. It proposes the operator AND fresh candidate AND approved distance
window logic as an advisory gate and identifies source ambiguities and safety
risks without granting perception actuator authority (`DM-jump/User/APP/ps2_task.c:303-322`; `docs/interfaces/TERRAIN_ADVISORY_TOPIC.md:30-42`).

**06 — Bench test scenarios.** Provides bottom-up procedures for isolated CAN
loopback, advisory LEDs, QoS compatibility, receive-only CAN monitoring, and an
H7 subscriber with motors disconnected. Each scenario states its purpose,
setup, steps, expected result, failure meaning, and debug order (`tools/can_monitor/firmware/can_rx.c:45-86`; `tools/microros_f446/README.md:81-99`). Missing named
tool directories and unrun work are called out explicitly.

## Source and scope notes

- `tools/agv_f446`, `tools/agv_f446_test`, and `tools/supervisor_demo` were not
  present in the requested worktree. The available AGV reference is the
  read-only `Microros_H723_USB` snapshot and the local `tools/microros_f446`
  receiver.
- The WBR reference is the read-only `DM-jump` snapshot. It is not the lab AGV
  and its source-level behavior is not evidence of what is currently flashed.
- No network access, firmware build, hardware test, or motor command was used to
  prepare these lessons.
