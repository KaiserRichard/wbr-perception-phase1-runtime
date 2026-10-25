CC := arm-none-eabi-gcc
OBJCOPY := arm-none-eabi-objcopy
SIZE := arm-none-eabi-size
SHA256 := shasum -a 256

ROOT := ..
LIBROOT := $(ROOT)/libbuild/micro_ros_stm32cubemx_utils/microros_static_library/libmicroros
INCLUDES := -I. -I$(LIBROOT)/microros_include
CPUFLAGS := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
CFLAGS := $(CPUFLAGS) -std=gnu11 -O2 -g -Wall -Wextra -Werror \
          -ffunction-sections -fdata-sections -fno-common -fno-unwind-tables \
          -fno-asynchronous-unwind-tables -DSTM32F446xx $(INCLUDES)
LDFLAGS := $(CPUFLAGS) -T f446.ld -nostartfiles --specs=nano.specs --specs=nosys.specs \
           -Wl,--gc-sections -Wl,--print-memory-usage \
           -Wl,-Map=build/microros_f446.map
SOURCES := startup.c main.c syscalls.c
ARCHIVE := $(LIBROOT)/libmicroros.a
ELF := build/microros_f446.elf
BIN := prebuilt/microros_f446.bin

.PHONY: all clean size checksum
all: $(BIN) checksum

$(ELF): $(SOURCES) f446.h f446.ld
	mkdir -p build
	$(CC) $(CFLAGS) $(SOURCES) $(LDFLAGS) -L$(LIBROOT) -Wl,--start-group -lmicroros -lc -lm -lgcc -Wl,--end-group -o $@
	$(SIZE) $@

$(BIN): $(ELF)
	mkdir -p prebuilt
	$(OBJCOPY) -O binary $< $@

size: $(ELF)
	$(SIZE) $(ELF)

checksum: $(BIN)
	$(SHA256) $(BIN) > prebuilt/SHA256SUMS
	cat prebuilt/SHA256SUMS

clean:
	rm -rf build $(BIN) prebuilt/SHA256SUMS
