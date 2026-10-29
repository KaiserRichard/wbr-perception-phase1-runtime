/* Nucleo-F446RE PIL firmware (rungs 3 and 4). BENCH SKELETON: built, never
 * flashed or run by its author. The F446 stands in for the robot's STM32H7.
 *
 * Rung 4 (PIL): USART2 PA2 TX / PA3 RX = ST-Link virtual COM port over USB,
 *   460800 8N1. Each STATE frame (6 measurements) -> wbr_lqr_step -> TORQUE
 *   reply. Frames and statuses: sim/pil/c/pil_core.h, docs/pil/DESIGN.md.
 * Rung 3 (timing): PA8 (Arduino D7) is HIGH exactly around wbr_lqr_step.
 *   Measure the pulse width with a logic analyser; the reply also carries the
 *   DWT cycle count of the same region (cpu_hz = 84 MHz) as a cross-check.
 * LD2 (PA5) toggles once per valid frame (visible as a dim glow at 500 Hz).
 * Clock: 84 MHz from the ST-Link 8 MHz MCO (HSE bypass), HSI fallback, same
 *   configuration as tools/link_bench/firmware/main.c.
 * The F446 FPU is single precision; the binary64 LQR runs in software
 *   double-precision routines, unlike the H7's double-precision FPU.
 * No motor, CAN or actuator output exists in this firmware. */
#include "f446.h"
#include "pil_core.h"

#define BAUD 460800u
#define CPU_HZ 84000000u
#define RING 512u /* power of two; > 2 state frames */
#define DEMCR REG(0xE000EDFCu)
#define DWT_CTRL REG(0xE0001000u)
#define DWT_CYCCNT REG(0xE0001004u)

static volatile uint8_t rx[RING];
static volatile uint16_t rx_head, rx_tail;
static volatile uint32_t rx_overflow, rx_errors;
static pil_mcu mcu;

static void clock_init(void) {
 uint32_t i, src, hse_ok;
#ifdef PIL_EMU
 return; /* QEMU has no RCC model: the PLL never reports ready there */
#endif
 RCC_CR |= 1u << 18; /* HSEBYP: ST-Link MCO is a clock, not a crystal */
 RCC_CR |= 1u << 16;
 for (i = 0; i < 200000u && !(RCC_CR & (1u << 17)); i++) {}
 hse_ok = (RCC_CR & (1u << 17)) != 0;
 if (!hse_ok) { RCC_CR &= ~(1u << 16); RCC_CR &= ~(1u << 18); }
 src = hse_ok ? 1u : 0u;
 /* VCO in 1 MHz, VCO 336 MHz, SYSCLK /4 = 84 MHz. */
 RCC_PLLCFGR = (hse_ok ? 8u : 16u) | (336u << 6) | (1u << 16) | (src << 22) | (7u << 24) | (2u << 28);
 RCC_CR |= 1u << 24;
 while (!(RCC_CR & (1u << 25))) {}
 FLASH_ACR = 2u | (1u << 8) | (1u << 9) | (1u << 10); /* 2 WS, prefetch, I/D cache */
 RCC_CFGR = 4u << 10; /* APB1 /2 = 42 MHz */
 RCC_CFGR |= 2u;
 while ((RCC_CFGR & (3u << 2)) != (2u << 2)) {}
}

static void periph_init(void) {
 RCC_AHB1ENR |= 1u;       /* GPIOA */
 RCC_APB1ENR |= 1u << 17; /* USART2 */
 (void)RCC_APB1ENR;
 /* PA2/PA3 AF7 USART2. */
 GPIOA_MODER = (GPIOA_MODER & ~((3u << 4) | (3u << 6))) | (2u << 4) | (2u << 6);
 GPIOA_AFRL = (GPIOA_AFRL & ~((15u << 8) | (15u << 12))) | (7u << 8) | (7u << 12);
 GPIOA_PUPDR = (GPIOA_PUPDR & ~(3u << 6)) | (1u << 6); /* RX idles high */
 /* PA5 LD2 and PA8 timing marker: push-pull outputs, PA8 very high speed. */
 GPIOA_BSRR = (1u << (5 + 16)) | (1u << (8 + 16));
 GPIOA_MODER = (GPIOA_MODER & ~((3u << 10) | (3u << 16))) | (1u << 10) | (1u << 16);
 GPIOA_OSPEEDR |= 3u << 16;
 USART_BRR(USART2_BASE) = (42000000u + BAUD / 2) / BAUD; /* 91 -> 461538 baud, +0.16 % */
 USART_CR1(USART2_BASE) = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE | USART_CR1_RXNEIE;
 NVIC_ISER1 = 1u << (38 - 32);
 /* DWT cycle counter: TRCENA, then CYCCNTENA. */
#ifndef PIL_EMU
 DEMCR |= 1u << 24;
 DWT_CYCCNT = 0;
 DWT_CTRL |= 1u;
#endif
}

void USART2_IRQHandler(void) {
 uint32_t sr = USART_SR(USART2_BASE);
 if (sr & (USART_SR_RXNE | USART_SR_ORE | USART_SR_FE | USART_SR_NF | USART_SR_PE)) {
  uint8_t b = (uint8_t)USART_DR(USART2_BASE); /* SR then DR clears error flags */
  uint16_t next = (uint16_t)((rx_head + 1u) & (RING - 1u));
  if (sr & (USART_SR_ORE | USART_SR_FE | USART_SR_NF | USART_SR_PE)) rx_errors++;
  if (next == rx_tail) rx_overflow++;
  else { rx[rx_head] = b; rx_head = next; }
 }
}

/* Lockstep: the host waits for this reply, so a blocking write (54 B, about
 * 1.2 ms at 460800) loses nothing; RX keeps running in the interrupt. */
static void tx(void *ctx, const uint8_t *data, size_t n) {
 (void)ctx;
 while (n--) {
  while (!(USART_SR(USART2_BASE) & USART_SR_TXE)) {}
  USART_DR(USART2_BASE) = *data++;
 }
}

#ifdef PIL_EMU
static uint32_t cycles(void *ctx) { (void)ctx; return 0; } /* no DWT model in QEMU */
#else
static uint32_t cycles(void *ctx) { (void)ctx; return DWT_CYCCNT; }
#endif

static void mark(void *ctx, int high) {
 (void)ctx;
 GPIOA_BSRR = high ? (1u << 8) : (1u << (8 + 16));
}

int main(void) {
 const pil_hooks hooks = {tx, cycles, mark, 0, CPU_HZ};
 uint32_t seen = 0;
 clock_init();
 periph_init();
 pil_mcu_init(&mcu, &hooks);
 for (;;) {
  uint8_t chunk[64];
  size_t n = 0;
  while (rx_tail != rx_head && n < sizeof(chunk)) {
   chunk[n++] = rx[rx_tail];
   rx_tail = (uint16_t)((rx_tail + 1u) & (RING - 1u));
  }
  if (n) pil_mcu_feed(&mcu, chunk, n);
  if (mcu.frames != seen) { seen = mcu.frames; GPIOA_ODR ^= 1u << 5; }
 }
}
