CC := arm-none-eabi-gcc
SIZE := arm-none-eabi-size
ROOT := ../..
LIBROOT ?= $(HOME)/Desktop/Research/agv-libbuild/micro_ros_stm32cubemx_utils/microros_static_library/libmicroros
CPUFLAGS := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
CFLAGS := $(CPUFLAGS) $(DEFS) -std=gnu11 -O2 -g -Wall -Wextra -Werror -ffunction-sections -fdata-sections -fno-common -fno-unwind-tables -fno-asynchronous-unwind-tables -DSTM32F446xx -I. -I$(LIBROOT)/microros_include
LDFLAGS := $(CPUFLAGS) -T f446.ld -nostartfiles --specs=nano.specs --specs=nosys.specs -Wl,--gc-sections -Wl,--print-memory-usage -Wl,-Map=build/agv_f446.map
SOURCES := startup.c main.c can.c syscalls.c
ARCHIVE := $(LIBROOT)/libmicroros.a
ELF := build/agv_f446.elf
.PHONY: all clean size print_cflags
all: $(ELF) size
$(ELF): $(SOURCES) f446.h can.h agv_logic.h f446.ld
	mkdir -p build
	$(CC) $(CFLAGS) $(SOURCES) $(LDFLAGS) -L$(LIBROOT) -Wl,--start-group -lmicroros -lc -lm -lgcc -Wl,--end-group -o $@
print_cflags:
	@echo $(CFLAGS)
size: $(ELF)
	$(SIZE) $(ELF)
clean:
	rm -rf build
