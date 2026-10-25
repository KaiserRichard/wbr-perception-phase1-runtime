# Nucleo-F446RE bare-metal micro-ROS advisory receiver

This firmware runs directly on the STM32F446RE, with no CubeMX HAL or
FreeRTOS. It links the local Jazzy `libmicroros.a` built for Cortex-M4F
hard-float. USART2 uses PA2/PA3 at **115200 baud, 8-N-1** through the Nucleo
ST-Link virtual COM port. RX is interrupt-driven into a 512-byte ring; TX is
blocking and polled. XRCE stream framing is enabled.

## Build

The static library must be present at
`libbuild/micro_ros_stm32cubemx_utils/microros_static_library/libmicroros/`.
Build from this firmware directory:

```sh
make clean
make
```

The Makefile uses `arm-none-eabi-gcc`, `--specs=nano.specs`, and the same
`-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard` ABI as the
archive. It emits `build/microros_f446.elf`, a map file,
`prebuilt/microros_f446.bin`, and `prebuilt/SHA256SUMS`. The linker reserves a
48 KiB newlib heap and an 8 KiB stack and fails if `.data + .bss + heap + stack`
would exceed 120 KiB. `_sbrk` enforces the heap boundary; standard output and
input syscalls return an error because this application has no console.

Verified build output on 2026-10-25:

```text
text    data    bss     dec      filename
74792   4384    11016   90192    build/microros_f446.elf
FLASH 79188 B / 512 KiB; linker RAM static usage 15392 B / 128 KiB
Conservative RAM total including heap and stack: 15400 + 49152 + 8192 = 72744 B
```

These values describe the built ELF and linker reservations; the actual peak
stack and heap use have not been measured on hardware.

## Application behavior

- Waits for the micro-ROS Agent using `rmw_uros_ping_agent`; red blinks at 2 Hz
  while disconnected. Creates `nucleo_advisory_node` after the Agent responds.
- Best-effort subscription `/terrain_advisory` (`std_msgs/msg/Float64MultiArray`)
  accepts exactly 8 finite doubles, with advisory code `data[0]` an integer in
  `0..3` and sequence `data[6]` an integer in the `uint32` range.
- Stores the accepted code, sequence, and TIM2 receive time. Publishes the most
  recently accepted sequence on `/terrain_advisory_ack`
  (`std_msgs/msg/UInt32`) every 100 ms.
- PB5 is green NONE, PB4 is yellow JUMP, PB10 is red STOP. UNCERTAIN turns on
  PC7 and blinks PB4 at 4 Hz. Missing valid data for over 300 ms blinks PB10 at
  2 Hz. LD2 (PA5) stays on while connected to the Agent.
- A failed Agent ping destroys the ROS entities and returns to the wait loop.
- Clock setup targets 84 MHz from the ST-Link 8 MHz MCO in HSE bypass mode,
  with the HSI PLL as the oscillator fallback. TIM2 is configured as a 1 MHz
  free-running counter and extended to 64-bit microseconds for transport
  timeouts and `clock_gettime`.

## Flash

This command is documented for the later bench step; it has **not** been run:

```sh
st-flash --connect-under-reset --freq=100k --reset write prebuilt/microros_f446.bin 0x08000000
```

## Pi Agent

Run on the Pi with ROS 2 Jazzy sourced:

```sh
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0 -b 115200
```

Container alternative:

```sh
docker run -it --rm --net=host -v /dev:/dev --privileged microros/micro-ros-agent:jazzy serial --dev /dev/ttyACM0 -b 115200
```

## Five-step bench test

1. With the board unpowered, verify USART2 PA2/PA3 connect to ST-Link VCP and
   identify the serial device on the Pi.
2. Power the board, start the Agent, and check LD2 turns on and
   `/nucleo_advisory_node` appears.
3. Publish valid 8-element arrays with `data[0]` set to 0, 1, then 2; check
   PB5, PB4, then PB10, and confirm `data[6]` appears on
   `/terrain_advisory_ack`.
4. Publish code 3 and confirm PC7 stays on while PB4 blinks at 4 Hz. Send an
   invalid-length or non-finite array and confirm the accepted state and
   sequence do not change.
5. Stop valid publishing for more than 300 ms, then stop the Agent. Confirm
   stale/UNCERTAIN indication, red blinking at 2 Hz, LD2 off, and reconnection
   after restarting the Agent.

No hardware was flashed or exercised for this build. USART timing, Agent
interoperability, LED behavior, reconnect behavior, and measured peak RAM remain
**UNVERIFIED**.
