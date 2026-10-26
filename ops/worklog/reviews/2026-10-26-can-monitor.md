# Passive CAN monitor implementation review

## Scope and files

Local uncommitted implementation on `claude2/20261026-can-monitor`; no PRs or merged commits.

- `tools/can_monitor/firmware/`: F446 micro-ROS app, silent dual bxCAN receive driver, RobStride decoder, copied startup/linker/syscall support, prebuilt binary and SHA256SUMS.
- `tools/can_monitor/tests/test_decoder.c`, `tools/can_monitor/Makefile`, `.gitignore`.
- `tools/can_monitor/view_can_monitor.py` and `tools/can_monitor/README.md`.

## Evidence

- `make test`: PASS, `decoder: 6 cases passed`.
- `make LIBROOT="$HOME/Desktop/Research/agv-libbuild/micro_ros_stm32cubemx_utils/microros_static_library/libmicroros"`: PASS.
- `arm-none-eabi-size build/can_monitor.elf`: text 62,728; data 7,432; bss 14,504; total 84,664 bytes.
- `firmware/prebuilt/can_monitor.bin`: 70,172 bytes; SHA256 `db346167ea8f3c0f4da2c891f9310065721f9df57e7001bf480e8ecab8adb039`.
- `python3 -m py_compile view_can_monitor.py`: PASS; `git diff --check`: PASS.
- Static source check: `can_rx.c` sets CAN_BTR SILM bit 31 on both bxCAN controllers and has no CAN transmit function. This verifies the implementation source, not physical transceiver behavior.

## Limitations

No flash, physical wiring, network access, Pi agent execution, or runtime CAN capture occurred. USART1 transport, Foxglove display, 20/5 Hz rates, 1 Mbit/s timing, silent electrical behavior, and decoded values on real H7 traffic remain unverified. Type-21 fault-frame payload is exposed as its raw first four bytes because the H7 source does not define a further decoding here. No change is committed or pushed.

## Claude review line

Please review the local passive CAN monitor implementation and its static SILENT-mode configuration; hardware behavior remains explicitly unverified.
