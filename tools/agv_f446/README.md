# Nucleo-F446RE AGV velocity base

Bare-metal STM32F446RE port of the H723 velocity-mode base. It reuses the
existing F446 clock/startup, USART transport, syscall layer, linker script, and
Jazzy archive. Protocol and topic behavior are based on the read-only reference
`Microros_H723_USB`; cited reference locations are preserved beside the ported
kinematics and frame parser. The optional MPU6050 path is omitted to keep this
first base image small; `/imu/data` is not published.

## ROS 2 interface

- Node: `stm32_agv_node`
- Best-effort `/cmd_vel` (`geometry_msgs/msg/Twist`): `linear.x` m/s and
  `angular.z` rad/s. Uses R=0.060 m and W=0.345 m, with left/right motor signs
  −1/+1. Both wheel commands scale together at 20 rad/s to preserve curvature.
- Reliable `/motor_enable` (`std_msgs/msg/Bool`). Motors start disabled. B1
  (PC13, active-low on Nucleo-64: pressed = 0) latches E-stop until reset.
- Best-effort `/motor_fb` (`sensor_msgs/msg/JointState`) at 20 Hz, with
  `left_wheel` and `right_wheel` position (rad), velocity (rad/s), effort
  (Nm), and `base_link` frame with agent-synchronized ROS timestamps.
- Reliable `/motor_status` (`std_msgs/msg/UInt8`) at 5 Hz: bits 0/1 fresh
  left/right feedback (<250 ms), bits 2/3 CAN1/CAN2 bus-off, bit 4 enabled,
  bit 5 command timeout (>500 ms), bit 6 MIT mode (always zero in this
  velocity-only build).
- Command timeout sets both velocity references to zero. LD2 (PA5) is lit while
  the micro-ROS agent session is active.

Topic units, geometry, signs, saturation and timeout follow
`Microros_H723_USB/docs/topics.md:54-64, 131-151` and
`User/Config/robot_config.h:17-37`. Extended protocol enable/stop/feedback and
parameter packing follow `User/Devices/DRV_Motor/robstride_drv.c:34-65, 187-214`.

## CAN wiring

Use 3.3 V compatible CAN transceivers; the MCU pins are logic-level CAN and
must not connect directly to CANH/CANL.

| Nucleo pin | Function | Connect to |
|---|---|---|
| PB8 | CAN1 RX, AF9 | CAN transceiver 1 RXD |
| PB9 | CAN1 TX, AF9 | CAN transceiver 1 TXD |
| PB12 | CAN2 RX, AF9 | CAN transceiver 2 RXD |
| PB13 | CAN2 TX, AF9 | CAN transceiver 2 TXD |
| GND | common reference | both transceivers and robot logic ground |

Both buses run bxCAN extended frames at 1 Mbit/s from APB1=42 MHz. The left
RobStride ID 1 is on CAN1; the right RobStride ID 1 is on CAN2. Give each
physical bus a 120 ohm termination at both ends. CAN2 filter banks start at
CAN2SB=14, sharing the bxCAN filter block with CAN1.

### Motor-free CAN loopback

Build with `DEFS=-DCAN_LOOPBACK_TEST` (see Build). With no motors attached, connect
one SN65HVD230 module to CAN1 PB8/PB9 and another to CAN2 PB12/PB13. Connect the
modules' CANH-to-CANH and CANL-to-CANL, share GND, and put 120 ohm across H/L at
each physical end (two resistors total). CAN2 receives CAN1 requests and sends
plausible feedback as a fake RobStride ID 1. Do not add motors to this test bus.

## Build

The supplied `libmicroros.a` was built with maximum 1 publisher, 1 subscription,
and history 1. This application uses 2 publishers and 2 subscriptions, so it
links but cannot create all entities at runtime with that archive. Rebuild the
library with the limits in `colcon.meta` before a ROS session.

Build normal and loopback images (both use the existing archive by default):

```sh
cd tools/agv_f446/firmware
make clean all
arm-none-eabi-size build/agv_f446.elf
make clean all DEFS=-DCAN_LOOPBACK_TEST
arm-none-eabi-size build/agv_f446.elf
```

Verified on 2026-10-25 against the existing archive:

```text
variant             text    data    bss     dec
normal              83372   6352    11240   100964
CAN_LOOPBACK_TEST   83644   6352    11248   101244
```

The linker reports 89,736 B flash for normal and 90,008 B flash for loopback.
The linker reserves a 48 KiB heap and an 8 KiB stack; peak runtime use is not
measured.

Rebuild the micro-ROS Jazzy static library with the bundled builder image,
following the local STM32CubeMX utility instructions. Run from `tools/agv_f446`;
the builder reads this project's `colcon.meta` and writes `libmicroros/` here:

```sh
docker pull microros/micro_ros_static_library_builder:jazzy
docker run -it --rm -v "$(pwd)":/project \
  --env MICROROS_LIBRARY_FOLDER=. \
  microros/micro_ros_static_library_builder:jazzy
```

Then build using the generated archive:

```sh
make -C firmware clean all \
  LIBROOT=../libmicroros
```

The in-tree archive remains the default when `LIBROOT` is not overridden.

## Transport, flash and Pi agent

USART1 uses PA9/PA10 at 115200 8-N-1 for Pi GPIO serial (`/dev/ttyAMA0` on the
Pi); build with `DEFS=-DUROS_USART1`. Default USART2 uses PA2/PA3 through the
Nucleo ST-Link VCP (`/dev/ttyACM0`). The Pi and Nucleo need a common ground and
crossed TX/RX; use 3.3 V UART levels.

After choosing the transport and build variant, flash the resulting ELF-derived
binary only when ready for hardware commissioning. Example with ST-Link:

```sh
arm-none-eabi-objcopy -O binary build/agv_f446.elf build/agv_f446.bin
st-flash --connect-under-reset --freq=100k --reset write build/agv_f446.bin 0x08000000
```

Start the agent on the Pi (select the serial device matching the build):

```sh
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyAMA0 -b 115200
# or, for USART2/ST-Link VCP:
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0 -b 115200
```

## Home test plan (loopback image)

1. Wire the two CAN transceiver modules as above, power the Nucleo, start the
   serial agent, and confirm LD2 and `/stm32_agv_node` appear. Check that
   `/motor_status` remains disabled until explicitly enabled.
2. In a second terminal, enable the base and command low linear speed. Check
   that `/motor_fb` shows a changing left-wheel velocity from the fake response.
   The loopback models one motor response; host-side tests cover saturation and
   curvature preservation.

   ```sh
   ros2 topic pub --once /motor_enable std_msgs/msg/Bool '{data: true}'
   ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist \
     '{linear: {x: 0.3}, angular: {z: 0.0}}'
   ```

   In another terminal, inspect feedback with matching best-effort QoS:

   ```sh
   ros2 topic echo /motor_fb --qos-reliability best_effort
   ```

3. Stop `/cmd_vel` publishing for >500 ms. Check status bit 5 and that fake
   feedback velocity returns to zero after the timeout stop reference.
4. Press B1. Check enabled bit 4 clears and remains cleared after releasing the
   button; reset the board to clear the latch.
5. MPU6050 test is not available in this build: the optional IMU driver and
   `/imu/data` publisher are omitted. Wiring support uses I2C1 PB6/PB7 at 400
   kHz if added in a later revision.

Run host-side logic tests with:

```sh
./tools/agv_f446/tests/run.sh
```

## Verification status

Builds and host unit tests are reported in the session worklog and final change
summary. CAN electrical timing, bus topology, actual RobStride responses, ROS
QoS interoperability, UART link, physical E-stop response, and on-board peak
stack/heap remain **UNVERIFIED** until bench testing. No hardware has been
flashed as part of this port.

## Prebuilt images (25 Oct, Claude 2)

Built against the rebuilt library (4 publishers, 3 subscriptions, history 2; `LIBROOT` defaults to
`~/Desktop/Research/agv-libbuild/...`), micro-ROS over USART1 (Pi pins 8/10, `/dev/ttyAMA0`, 115200):
- `firmware/prebuilt/agv_f446_home_loopback.bin`: CAN2 acts as a fake RobStride motor (home test, no motors).
- `firmware/prebuilt/agv_f446_robot.bin`: real motors on CAN1/CAN2.
Fixed after Codex: the Nucleo-64 B1 button (PC13) is active-low; the first draft treated it as active-high,
which would have latched the E-stop at boot.
