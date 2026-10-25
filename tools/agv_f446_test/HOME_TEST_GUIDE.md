# F446 AGV Home Test Guide

This guide brings up the Nucleo-F446RE base with the Raspberry Pi 5 as the ROS 2 host. At home, CAN2 runs a fake motor that receives the CAN1 motor frames and echoes the requested speed as feedback. Do not connect real motors during this acceptance test.

## Parts

- Nucleo-F446RE board and its USB cable
- Raspberry Pi 5 with ROS 2 Jazzy and `micro_ros_agent` already installed
- Two **3.3 V logic-compatible** SN65HVD230 CAN transceiver modules
- MPU6050 breakout configured for 3.3 V logic
- Jumper wires
- Two 120 Ω resistors
- 3.3 V and GND can come from the Nucleo headers; do not power a transceiver module from 5 V

## Before wiring

1. Disconnect USB and all external power from the Nucleo.
2. Check that the firmware README for the F446 port uses the pin assignments below. These MCU pins, the selected UART instance/baud, and the test node name **must match the firmware README**. The table follows the requested F446 mapping; firmware changes can move these functions.
3. Check the silkscreen names on each module. `CTX`/`TXD` is the module's CAN transmit input and goes to an STM32 CAN TX pin. `CRX`/`RXD` is the module's CAN receive output and goes to an STM32 CAN RX pin.

## Pin-by-pin wiring

### CAN1 transceiver (controller side)

| Nucleo-F446RE | SN65HVD230 module | Notes |
|---|---|---|
| 3V3 | VCC / 3V3 | **Must be a 3.3 V module.** |
| GND | GND | Shared signal ground. |
| PB9 (CAN1_TX) | CTX / TXD | MCU transmit to transceiver. **Must match the firmware README.** |
| PB8 (CAN1_RX) | CRX / RXD | Transceiver receive to MCU. **Must match the firmware README.** |
| CANH | CANH | Connect to CAN2 module CANH and the fake motor CANH. |
| CANL | CANL | Connect to CAN2 module CANL and the fake motor CANL. |

### CAN2 transceiver (fake-motor side)

| Nucleo-F446RE | SN65HVD230 module | Notes |
|---|---|---|
| 3V3 | VCC / 3V3 | Same 3.3 V rail is acceptable if supply capacity is sufficient. |
| GND | GND | Common ground with CAN1 module and Nucleo. |
| PB13 (CAN2_TX) | CTX / TXD | MCU transmit to transceiver. **Must match the firmware README.** |
| PB12 (CAN2_RX) | CRX / RXD | Transceiver receive to MCU. **Must match the firmware README.** |
| CANH | CANH | Join the same CANH line as CAN1. |
| CANL | CANL | Join the same CANL line as CAN1. |

Put one 120 Ω resistor across CANH and CANL at each physical end of the bus. For this short bench bus, place one across CANH/CANL near the CAN1 transceiver and one near the CAN2/fake-motor end. If a module has a built-in termination jumper/resistor, count it as one end resistor; do not accidentally add multiple terminators at one end. With power off, the resistance measured between CANH and CANL should be about 60 Ω when both 120 Ω end resistors are present.

```text
Nucleo PB9 TX -> CTX [CAN1 SN65HVD230] CANH ====+==== CANH [CAN2 SN65HVD230] CTX <- PB13 TX
Nucleo PB8 RX <- CRX [                 ] CANL ====+==== CANL [                 ] CRX -> PB12 RX
                           120R across H/L | 120R across H/L
Nucleo 3V3/GND ------------ VCC/GND -----+----- VCC/GND ------------ Nucleo 3V3/GND
                                                |
                                   CAN2 firmware fake motor echoes
                                   frames from the CAN1 motor link
```

CANH connects to CANH and CANL to CANL. Never cross them. Both transceivers and the Nucleo must share ground.

### MPU6050 on I2C1

| Nucleo-F446RE | MPU6050 breakout | Notes |
|---|---|---|
| 3V3 | VCC | Use 3.3 V logic/power unless the breakout explicitly supports another input range. |
| GND | GND | Common ground. |
| PB6 (I2C1_SCL) | SCL | **Must match the firmware README.** |
| PB7 (I2C1_SDA) | SDA | **Must match the firmware README.** |

Leave AD0 at its default level unless the firmware expects the alternate address. The IMU is not needed to judge wheel feedback, but the home board setup includes it for full firmware startup.

### UART between Nucleo and Pi 5

| Raspberry Pi 5 header pin | Pi signal | Nucleo-F446RE | Notes |
|---|---|---|---|
| 8 | GPIO14 / UART TXD | D2 / PA10 (USART1_RX) | Pi transmits to STM32 receive. |
| 10 | GPIO15 / UART RXD | D8 / PA9 (USART1_TX) | STM32 transmits to Pi receive. |
| 6 (or another GND) | GND | GND | Common signal reference. |

These UART pins and the baud rate are **must match the firmware README**. The acceptance guide's agent command uses `/dev/ttyAMA0` at 115200 baud. Cross TX to RX; do not connect 5 V power from the Pi header to the Nucleo UART pins. Pi GPIO is 3.3 V logic.

```text
Pi pin 8  GPIO14/TX  -----------------> Nucleo D2 / PA10 / USART1_RX
Pi pin 10 GPIO15/RX  <----------------- Nucleo D8 / PA9  / USART1_TX
Pi GND   ------------------------------ Nucleo GND
```

### Nucleo power

For first bring-up, power the Nucleo from its USB connector. Do not simultaneously apply an external 5 V source unless the Nucleo user manual's jumper configuration explicitly permits it. If the firmware setup requires E5V, use the Nucleo board manual to verify the `JP5` position and the correct E5V input before connecting power. **Do not guess the JP5 position.** Keep the Pi and Nucleo grounds connected through the UART ground wire.

## Common wiring mistakes

- Swapping UART TX and RX: Pi pin 8 goes to STM32 RX (D2/PA10); Pi pin 10 goes to STM32 TX (D8/PA9).
- Misreading `CTX`/`CRX`: TX from the MCU goes to transceiver TX input; transceiver RX output goes to MCU RX.
- Missing common ground or one of the two CAN end terminators.
- Reversing CANH and CANL.
- Using a 5 V-only CAN module or applying 5 V to an STM32/Pi logic pin. SN65HVD230 is a 3.3 V transceiver family.
- Installing three or more 120 Ω terminators on the short bus, or placing both resistors at the same physical end.
- Using different UART baud, CAN bitrate, CAN pins, or node/topic names than the F446 firmware build.
- Leaving the board in its system bootloader when intending to run the application.

## Flash the F446 firmware

Use the firmware image built by the F446 firmware worktree. Verify the image filename and board README before programming.

### ST-Link with `st-flash`

1. Connect the Nucleo USB/ST-Link connector to the computer and install `stlink` tools if needed.
2. Put the board into reset if required by the board and programmer.
3. From the firmware build output directory, program the application at the normal flash base:

   ```bash
   st-flash --connect-under-reset --freq=100k write build/agv_f446.bin 0x08000000
   ```

4. Confirm the tool reports a successful write, then reset/power-cycle the Nucleo. The actual binary path is build-system-specific; substitute the output path from the firmware README.

### STM32 UART system bootloader

Use this only if the firmware README confirms that the selected UART pins are supported by the F446 system-memory bootloader.

1. Disconnect power. Set BOOT0 high using the board's documented boot jumper/pad and reset the board.
2. Connect the supported bootloader UART adapter with crossed TX/RX and common GND. Use 3.3 V logic.
3. Use STM32CubeProgrammer in UART mode (select the documented bootloader UART and baud), connect, erase/program the firmware image, and verify the programming result.
4. Disconnect, restore BOOT0 low, and reset. If BOOT0 stays high the board will keep entering the system bootloader instead of starting the application.

## Start the micro-ROS agent on the Pi

Open a Pi terminal. Source the existing micro-ROS workspace, then run the serial agent:

```bash
source ~/microros_ws/install/local_setup.bash
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyAMA0 -b 115200
```

If the serial device is missing, check the Pi UART configuration, that the serial console is not occupying the port, and that the cable is on header pins 8/10/GND. If permission is denied, add the user to the appropriate serial-port group and log in again. The device and baud must match the firmware README.

In another Pi terminal, source ROS and run the acceptance test:

```bash
source /opt/ros/jazzy/setup.bash
source ~/microros_ws/install/local_setup.bash
python3 tools/agv_f446_test/agv_home_test.py --out ~/agv_f446_home_test
```

Run from the repository root or replace the script path with its absolute path. If the default mechanical dimensions/signs differ from the F446 configuration, pass `--wheel-radius`, `--wheel-base`, `--left-sign`, and `--right-sign` to match that firmware's `robot_config.h` and feedback convention. Tolerances are configurable with `--velocity-tolerance`, `--zero-tolerance`, and `--saturation-tolerance` (rad/s).

The test writes `motor_fb.csv` (every received position/velocity/effort sample with timestamps) and `summary.json` into `--out`. It does not require ROS to run its pure checking unit tests:

```bash
cd tools/agv_f446_test
python3 -m unittest discover -s tests -v
```

## What each result means

| Step | PASS means | If it fails, check |
|---|---|---|
| Node and four required topics discovered | `/stm32_agv_node` and `/cmd_vel`, `/motor_enable`, `/motor_fb`, `/motor_status` are visible in the ROS graph. | Agent terminal, UART crossed correctly, firmware node name/topics, UART device/baud, and firmware README pin mapping. |
| Disabled motors hold zero | With `motor_enable=false`, a repeated 0.3 m/s command leaves both fake wheel velocities near zero. | Reliable `/motor_enable` delivery, enable state logic, fake motor disabled behavior, CAN wiring, and check that feedback is truly from the fake motor. |
| Forward command wheel velocity and signs | At 0.3 m/s, both feedback values match the configured `v/R` magnitude and configured left/right feedback signs. | Wheel radius/sign defaults, CAN1-to-CAN2 fake-motor echo, CAN bit rate/IDs, and `/motor_fb` ordering. |
| Turning command differential wheel speeds | `{linear.x: 0.2, angular.z: 0.5}` produces the left/right speeds predicted by differential-drive geometry. | Wheel base, `linear.x`/`angular.z` interpretation, wheel array order, and motor signs. |
| 20 rad/s common-ratio saturation | A 2.0 m/s request caps each wheel at 20 rad/s while keeping the original wheel-speed ratio. | Firmware must use one common scale factor; check the fake motor echoes clamped CAN setpoints and geometry configuration. |
| Timeout stops wheels and sets `0x20` | After publishing stops, feedback returns to zero within the 500 ms watchdog plus the configured margin, and status has `MSTAT_CMD_TIMEOUT` bit 5 set. | Firmware timeout implementation, status bit allocation, status topic QoS/data, and CAN stop/zero echo. |
| NaN command is ignored | A valid nonzero baseline remains in feedback after NaN `linear.x` commands are sent. | Firmware finite-value validation; inspect UART diagnostics and ensure the test can still receive regular feedback. |
| Motors disabled at test end | Feedback is near zero and status bit 4 (`MSTAT_MOTORS_ENABLED`) is clear after `motor_enable=false`. | Check reliable enable delivery, motor stop handling, feedback settling, and the F446 status bit mapping. |

The test summarizes the overall run as `PASS` only when every step passes. A failure is retained in `summary.json`; inspect the CSV around the failing step to see actual wheel feedback and timing. The fake motor validates transport and setpoint handling, not real wheel mechanics, encoder calibration, or closed-loop motor performance.
