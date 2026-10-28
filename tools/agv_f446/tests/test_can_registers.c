/* Host-side register model: validates addresses and frame format, not CAN timing. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint32_t can_regs[2][0x320 / 4];
static uint32_t gpio_regs[12], rcc_regs[2];

static volatile uint32_t *test_reg(uint32_t address)
{
    if (address >= 0x40006400u && address < 0x40006720u)
        return &can_regs[0][(address - 0x40006400u) / 4];
    if (address >= 0x40006800u && address < 0x40006b20u)
        return &can_regs[1][(address - 0x40006800u) / 4];
    assert(!"unexpected MMIO address");
    return NULL;
}

/* Simulate only MSR.INAK following MCR.INRQ, so can_init cannot hang on host. */
static volatile uint32_t *mmio(uint32_t address)
{
    if (address == 0x40006404u || address == 0x40006804u) {
        unsigned bus = address == 0x40006804u;
        can_regs[bus][1] = can_regs[bus][0] & 1u;
    }
    return test_reg(address);
}

#define AGV_F446_REGS_H
#define REG(a) (*mmio(a))
#define RCC_AHB1ENR rcc_regs[0]
#define RCC_APB1ENR rcc_regs[1]
#define GPIOB_MODER gpio_regs[0]
#define GPIOB_OSPEEDR gpio_regs[1]
#define GPIOB_PUPDR gpio_regs[2]
#define GPIOB_AFRH gpio_regs[3]
#include "../firmware/can.c"

static void reset_model(void)
{
    memset(can_regs, 0, sizeof(can_regs));
    memset(gpio_regs, 0, sizeof(gpio_regs));
    memset(rcc_regs, 0, sizeof(rcc_regs));
}

static void test_filters(void)
{
    reset_model();
    can_init();
    /* Offsets independently taken from ST's STM32F446 CMSIS register map. */
    assert(can_regs[0][0x200 / 4] == (14u << 8));
    assert(can_regs[0][0x204 / 4] == 0u);
    assert(can_regs[0][0x20c / 4] == ((1u << 0) | (1u << 14)));
    assert(can_regs[0][0x214 / 4] == 0u);
    assert(can_regs[0][0x21c / 4] == ((1u << 0) | (1u << 14)));
    assert(can_regs[0][0x240 / 4] == 0u);
    assert(can_regs[0][(0x240 + 14 * 8) / 4] == 0u);
    assert(can_regs[0][0] == (1u << 6));
    assert(can_regs[1][0] == (1u << 6));
    /* Filter configuration must never write CAN2's reserved register region. */
    for (unsigned i = 0x40 / 4; i < 0x320 / 4; ++i)
        assert(can_regs[1][i] == 0u);
}

static void test_data_frames(void)
{
    const uint8_t payload[8] = {0x0a, 0x70, 0, 0, 0, 0, 0xa0, 0x40};
    for (unsigned bus = 0; bus < 2; ++bus) {
        for (unsigned mailbox = 0; mailbox < 3; ++mailbox) {
            reset_model();
            can_regs[bus][0x08 / 4] = 1u << (26 + mailbox);
            assert(can_send(bus, 0x1200fd01u, payload) == 0);
            unsigned slot = (0x180 + mailbox * 0x10) / 4;
            uint32_t tir = can_regs[bus][slot];
            assert((tir >> 3) == 0x1200fd01u);
            assert((tir & 7u) == 5u); /* TXRQ=1, IDE=1, RTR=0 */
            assert(can_regs[bus][slot + 1] == 8u);
            assert(can_regs[bus][slot + 2] == 0x0000700au);
            assert(can_regs[bus][slot + 3] == 0x40a00000u);
        }
    }
    reset_model();
    assert(can_send(0, 0x1200fd01u, payload) == -1);
    assert(can_regs[0][0x180 / 4] == 0u);
}

int main(void)
{
    test_filters();
    test_data_frames();
    puts("PASS: shared filter register map, CAN2 split, data frames on both buses/all mailboxes, busy mailbox");
    return 0;
}
