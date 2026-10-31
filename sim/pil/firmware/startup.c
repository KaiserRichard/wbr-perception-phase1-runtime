/* Minimal Cortex-M4F startup for the PIL firmware: vector table, FPU enable,
 * .data/.bss init, then main(). Based on tools/link_bench/firmware/startup.c;
 * differs only in enabling the FPU (hard-float build) and using newlib-nano
 * for memset/memcpy and the math library. */
#include <stdint.h>
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss, _estack;
int main(void);
void Reset_Handler(void);
void USART2_IRQHandler(void);
static void default_handler(void) { for (;;) {} }
#define IRQS 97
__attribute__((section(".isr_vector"), used))
static void (*const vectors[16 + IRQS])(void) = {
 [0] = (void (*)(void))&_estack,
 [1] = Reset_Handler,
 [2 ... 15] = default_handler,
 [16 ... 16 + 37] = default_handler,
 [16 + 38] = USART2_IRQHandler,
 [16 + 39 ... 16 + IRQS - 1] = default_handler,
};
void Reset_Handler(void) {
#ifndef PIL_EMU
 /* VTOR for the ROM bootloader GO path, as in link_bench. */
 *(volatile uint32_t *)0xE000ED08u = 0x08000000u;
#endif
 /* CPACR: full access to CP10/CP11 before any floating-point instruction. */
 *(volatile uint32_t *)0xE000ED88u |= 0xFu << 20;
 __asm volatile ("dsb" ::: "memory");
 __asm volatile ("isb" ::: "memory");
 uint32_t *s = &_sidata, *d = &_sdata;
 while (d < &_edata) *d++ = *s++;
 for (d = &_sbss; d < &_ebss; ) *d++ = 0;
 main();
 for (;;) {}
}
