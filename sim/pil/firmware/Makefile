# Nucleo-F446RE PIL firmware (rungs 3 and 4). Needs arm-none-eabi-gcc with newlib-nano.
# Flash (owner, on the bench): copy build/pil_f446.bin onto the NOD_F446RE drive, or `make flash`.
CC = arm-none-eabi-gcc
OBJCOPY = arm-none-eabi-objcopy
SIZE = arm-none-eabi-size
BENCH = ../../../tools/link_bench/firmware
PROTO = ../../../tools/link_proto
LQR = ../../control_c
CORE = ../c
# Hard-float ABI with the single-precision FPU. binary64 still runs in libgcc
# soft-double routines on the M4; -ffp-contract=off matches the host parity build.
CFLAGS = -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -std=c99 -O2 -g \
 -Wall -Wextra -Werror -ffp-contract=off -ffunction-sections -fdata-sections \
 -I$(BENCH) -I$(PROTO) -I$(LQR) -I$(CORE)
LDFLAGS = -T $(BENCH)/f446.ld -nostartfiles --specs=nano.specs --specs=nosys.specs \
 -Wl,--gc-sections -Wl,-Map=build/pil_f446.map
SRC = startup.c main.c $(CORE)/pil_core.c $(LQR)/wbr_lqr.c $(PROTO)/link_proto.c
.PHONY: all flash clean
all: build/pil_f446.bin
build/pil_f446.elf: $(SRC) $(CORE)/pil_core.h $(LQR)/wbr_lqr.h $(LQR)/gains.inc $(BENCH)/f446.h
	mkdir -p build
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) -lm -o $@
	$(SIZE) $@
build/pil_f446.bin: build/pil_f446.elf
	$(OBJCOPY) -O binary $< $@
flash: build/pil_f446.bin
	st-flash --reset write $< 0x08000000
clean:
	rm -rf build
# Emulator build (QEMU netduinoplus2 = STM32F405, same USART2 address/IRQ, M4F):
# skips RCC, VTOR and DWT. Checks the cross-compiled numerics, not timing:
#   qemu-system-arm -M netduinoplus2 -nographic -serial null -serial pty -kernel build/pil_emu.elf
build/pil_emu.elf: $(SRC) $(CORE)/pil_core.h $(LQR)/wbr_lqr.h $(LQR)/gains.inc $(BENCH)/f446.h
	mkdir -p build
	$(CC) $(CFLAGS) -DPIL_EMU $(SRC) -T $(BENCH)/f446.ld -nostartfiles --specs=nano.specs \
	 --specs=nosys.specs -Wl,--gc-sections -lm -o $@
