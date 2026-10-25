#include "f446.h"

#include <math.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <rcutils/allocator.h>
#include <rmw_microros/rmw_microros.h>
#include <std_msgs/msg/float64_multi_array.h>
#include <std_msgs/msg/u_int32.h>
#include <uxr/client/transport.h>

#define BAUD 115200u
#define RX_RING_SIZE 512u
#define STALE_US 300000ull
#define ACK_PERIOD_US 100000ull

typedef enum { ADV_NONE = 0, ADV_JUMP = 1, ADV_STOP = 2, ADV_UNCERTAIN = 3 } advisory_t;
static volatile uint8_t rx_ring[RX_RING_SIZE];
static volatile uint16_t rx_head, rx_tail;
static volatile uint32_t rx_overflows;
static uint64_t last_valid_us;
static uint32_t last_sequence;
static advisory_t current_code = ADV_UNCERTAIN;
static bool have_advisory;
static uint32_t timer_clock_hz = 84000000u;
static uint32_t usart2_clock_hz = 42000000u;

static void *allocator_allocate(size_t size, void *state) { (void)state; return malloc(size); }
static void allocator_deallocate(void *ptr, void *state) { (void)state; free(ptr); }
static void *allocator_reallocate(void *ptr, size_t size, void *state) { (void)state; return realloc(ptr, size); }
static void *allocator_zero_allocate(size_t n, size_t size, void *state) { (void)state; return calloc(n, size); }

static uint64_t micros64(void) {
  static uint32_t last;
  static uint64_t high;
  uint32_t now = TIM2_CNT;
  if (now < last) high += 1ull << 32;
  last = now;
  return high | now;
}

int clock_gettime(clockid_t clock_id, struct timespec *ts) {
  (void)clock_id;
  uint64_t us = micros64();
  ts->tv_sec = (time_t)(us / 1000000ull);
  ts->tv_nsec = (long)((us % 1000000ull) * 1000ull);
  return 0;
}

static void clock_init(void) {
  uint32_t i;
  RCC_CR |= 1u << 18; /* ST-Link MCO is an 8 MHz clock, so use HSE bypass. */
  RCC_CR |= 1u << 16;
  for (i = 0; i < 200000u && !(RCC_CR & (1u << 17)); ++i) {}
  bool hse_ok = (RCC_CR & (1u << 17)) != 0;
  if (!hse_ok) { RCC_CR &= ~(1u << 16); RCC_CR &= ~(1u << 18); }
  uint32_t m = hse_ok ? 8u : 16u;
  uint32_t source = hse_ok ? 1u : 0u;
  RCC_PLLCFGR = m | (336u << 6) | (1u << 16) | (source << 22) | (7u << 24) | (2u << 28);
  RCC_CR |= 1u << 24;
  for (i = 0; i < 2000000u && !(RCC_CR & (1u << 25)); ++i) {}
  if (!(RCC_CR & (1u << 25))) {
    timer_clock_hz = 16000000u;
    usart2_clock_hz = 16000000u;
    return; /* remain on reset-default HSI if PLL fails */
  }
  FLASH_ACR = 2u | (1u << 8) | (1u << 9) | (1u << 10);
  RCC_CFGR = 4u << 10; /* APB1 /2, APB2 /1 */
  RCC_CFGR |= 2u;
  for (i = 0; i < 2000000u && (RCC_CFGR & (3u << 2)) != (2u << 2); ++i) {}
}

__attribute__((unused)) static void gpio_af7(unsigned pin) {
  GPIOA_MODER = (GPIOA_MODER & ~(3u << (2u * pin))) | (2u << (2u * pin));
  GPIOA_OSPEEDR |= 2u << (2u * pin);
  GPIOA_AFRL = (GPIOA_AFRL & ~(15u << (4u * pin))) | (7u << (4u * pin));
}

static void gpio_output(volatile uint32_t *moder, unsigned pin) {
  *moder = (*moder & ~(3u << (2u * pin))) | (1u << (2u * pin));
}

static void peripherals_init(void) {
  RCC_AHB1ENR |= 7u;
#ifdef UROS_USART1
  RCC_APB1ENR |= 1u << 0;            /* TIM2 */
  RCC_APB2ENR |= 1u << 4;            /* USART1 */
  (void)RCC_APB2ENR;
  for (unsigned pin = 9; pin <= 10; ++pin) {
    GPIOA_MODER = (GPIOA_MODER & ~(3u << (2u * pin))) | (2u << (2u * pin));
    GPIOA_AFRH = (GPIOA_AFRH & ~(15u << (4u * (pin - 8u)))) | (7u << (4u * (pin - 8u)));
  }
  GPIOA_PUPDR = (GPIOA_PUPDR & ~(3u << 20)) | (1u << 20); /* RX pull-up */
#else
  RCC_APB1ENR |= (1u << 0) | (1u << 17);
  (void)RCC_APB1ENR;
  gpio_af7(2); gpio_af7(3);
  GPIOA_PUPDR = (GPIOA_PUPDR & ~(3u << 6)) | (1u << 6);
#endif
  GPIOA_BSRR = 1u << (5u + 16u);
  gpio_output(&GPIOA_MODER, 5); /* LD2 */
  GPIOB_BSRR = (1u << 21) | (1u << 20) | (1u << 26);
  GPIOC_BSRR = 1u << 23;
  GPIOB_OTYPER &= ~((1u << 5) | (1u << 4) | (1u << 10));
  GPIOC_OTYPER &= ~(1u << 7);
  gpio_output(&GPIOB_MODER, 5); gpio_output(&GPIOB_MODER, 4); gpio_output(&GPIOB_MODER, 10);
  gpio_output(&GPIOC_MODER, 7);
  TIM2_PSC = timer_clock_hz / 1000000u - 1u;
  TIM2_ARR = 0xFFFFFFFFu;
  TIM2_EGR = 1u;
  TIM2_CR1 = 1u;
  /* PLL path: USART2 PCLK1=42 MHz. HSI fallback uses 16 MHz SYSCLK, APB1=8 MHz. */
#ifdef UROS_USART1
  USART_BRR = (usart2_clock_hz * 2u + BAUD / 2u) / BAUD; /* USART1 on PCLK2 = 2 x PCLK1 */
#else
  USART_BRR = (usart2_clock_hz + BAUD / 2u) / BAUD;
#endif
  USART_CR1 = (1u << 13) | (1u << 3) | (1u << 2) | (1u << 5);
#ifdef UROS_USART1
  NVIC_ISER1 = 1u << (37u - 32u);
#else
  NVIC_ISER1 = 1u << (38u - 32u);
#endif
}

void USART2_IRQHandler(void) {
  uint32_t sr = USART_SR;
  if (sr & (USART_SR_RXNE | USART_SR_ORE | USART_SR_FE | USART_SR_NF | USART_SR_PE)) {
    uint8_t byte = (uint8_t)USART_DR;
    if (sr & USART_SR_RXNE) {
      uint16_t next = (uint16_t)((rx_head + 1u) & (RX_RING_SIZE - 1u));
      if (next == rx_tail) ++rx_overflows;
      else { rx_ring[rx_head] = byte; rx_head = next; }
    }
  }
}

static bool transport_open(struct uxrCustomTransport *transport) { (void)transport; return true; }
static bool transport_close(struct uxrCustomTransport *transport) { (void)transport; return true; }

static size_t transport_write(struct uxrCustomTransport *transport, const uint8_t *buffer,
                              size_t length, uint8_t *err) {
  (void)transport;
  for (size_t i = 0; i < length; ++i) {
    while (!(USART_SR & USART_SR_TXE)) {}
    USART_DR = buffer[i];
  }
  while (!(USART_SR & USART_SR_TC)) {}
  if (err) *err = 0;
  return length;
}

static size_t transport_read(struct uxrCustomTransport *transport, uint8_t *buffer,
                             size_t length, int timeout_ms, uint8_t *err) {
  (void)transport;
  uint64_t start = micros64();
  uint64_t timeout = timeout_ms > 0 ? (uint64_t)timeout_ms * 1000ull : 0ull;
  size_t got = 0;
  while (got < length && micros64() - start < timeout) {
    if (rx_tail != rx_head) {
      buffer[got++] = rx_ring[rx_tail];
      rx_tail = (uint16_t)((rx_tail + 1u) & (RX_RING_SIZE - 1u));
    }
  }
  if (err) *err = 0; /* normal partial/empty read at timeout */
  return got;
}

static void set_leds(bool green, bool yellow, bool red, bool blue, bool ld2) {
  GPIOB_BSRR = (green ? 1u << 5 : 1u << 21) |
               (yellow ? 1u << 4 : 1u << 20) |
               (red ? 1u << 10 : 1u << 26);
  GPIOC_BSRR = blue ? 1u << 7 : 1u << 23;
  GPIOA_BSRR = ld2 ? 1u << 5 : 1u << 21;
}

static void advisory_callback(const void *message) {
  const std_msgs__msg__Float64MultiArray *msg = message;
  if (msg->data.data == NULL || msg->data.size != 8u) return;
  for (size_t i = 0; i < 8u; ++i) if (!isfinite(msg->data.data[i])) return;
  double raw_code = msg->data.data[0], raw_seq = msg->data.data[6];
  if (raw_code < 0.0 || raw_code > 3.0 || trunc(raw_code) != raw_code ||
      raw_seq < 0.0 || raw_seq > 4294967295.0 || trunc(raw_seq) != raw_seq) return;
  current_code = (advisory_t)(uint32_t)raw_code;
  last_sequence = (uint32_t)raw_seq;
  last_valid_us = micros64();
  have_advisory = true;
}

static bool entities_init(rcl_allocator_t *allocator, rclc_support_t *support,
                          rcl_node_t *node, rcl_subscription_t *sub,
                          rcl_publisher_t *pub, rclc_executor_t *executor,
                          std_msgs__msg__Float64MultiArray *input,
                          std_msgs__msg__UInt32 *ack) {
  if (rclc_support_init(support, 0, NULL, allocator) != RCL_RET_OK) return false;
  if (rclc_node_init_default(node, "nucleo_advisory_node", "", support) != RCL_RET_OK) return false;
  if (rclc_subscription_init_best_effort(sub, node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float64MultiArray),
      "/terrain_advisory") != RCL_RET_OK) return false;
  if (rclc_publisher_init_default(pub, node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, UInt32),
      "/terrain_advisory_ack") != RCL_RET_OK) return false;
  if (rclc_executor_init(executor, &support->context, 1u, allocator) != RCL_RET_OK) return false;
  input->data.data = calloc(8u, sizeof(double));
  if (input->data.data == NULL) return false;
  input->data.capacity = 8u;
  input->data.size = 0u;
  ack->data = 0;
  return rclc_executor_add_subscription(executor, sub, input, advisory_callback,
                                        ON_NEW_DATA) == RCL_RET_OK;
}

static void entities_fini(rclc_executor_t *executor, rcl_publisher_t *pub,
                          rcl_subscription_t *sub, rcl_node_t *node,
                          rclc_support_t *support) {
  rcl_ret_t rc;
  rc = rclc_executor_fini(executor); (void)rc;
  rc = rcl_publisher_fini(pub, node); (void)rc;
  rc = rcl_subscription_fini(sub, node); (void)rc;
  rc = rcl_node_fini(node); (void)rc;
  rc = rclc_support_fini(support); (void)rc;
}

static void input_fini(std_msgs__msg__Float64MultiArray *input) {
  std_msgs__msg__Float64MultiArray__fini(input);
}

static void wait_for_agent(void) {
  while (rmw_uros_ping_agent(100, 1) != RMW_RET_OK) {
    bool phase = ((micros64() / 250000ull) & 1u) != 0;
    set_leds(false, false, phase, false, false);
  }
}

int main(void) {
  clock_init();
  peripherals_init();
  rcutils_allocator_t rc_allocator = rcutils_get_zero_initialized_allocator();
  rc_allocator.allocate = allocator_allocate;
  rc_allocator.deallocate = allocator_deallocate;
  rc_allocator.reallocate = allocator_reallocate;
  rc_allocator.zero_allocate = allocator_zero_allocate;
  if (!rcutils_set_default_allocator(&rc_allocator)) for (;;) set_leds(false, false, true, false, false);
  if (rmw_uros_set_custom_transport(true, NULL, transport_open, transport_close,
                                    transport_write, transport_read) != RMW_RET_OK)
    for (;;) set_leds(false, false, true, false, false);

  for (;;) {
    wait_for_agent();
    rcl_allocator_t allocator = rcl_get_default_allocator();
    rclc_support_t support = {0};
    rcl_node_t node = rcl_get_zero_initialized_node();
    rcl_subscription_t sub = rcl_get_zero_initialized_subscription();
    rcl_publisher_t pub = rcl_get_zero_initialized_publisher();
    rclc_executor_t executor = rclc_executor_get_zero_initialized_executor();
    std_msgs__msg__Float64MultiArray input = {0};
    std_msgs__msg__UInt32 ack;
    if (!std_msgs__msg__Float64MultiArray__init(&input)) {
      input_fini(&input);
      continue;
    }
    if (!entities_init(&allocator, &support, &node, &sub, &pub, &executor, &input, &ack)) {
      entities_fini(&executor, &pub, &sub, &node, &support);
      input_fini(&input);
      continue;
    }
    uint64_t next_ack = micros64();
    uint64_t last_ping = next_ack;
    bool connected = true;
    while (connected) {
      (void)rclc_executor_spin_some(&executor, 10000000ull);
      uint64_t now = micros64();
      bool stale = !have_advisory || now - last_valid_us > STALE_US;
      bool uncertain = stale || current_code == ADV_UNCERTAIN;
      bool blink_yellow = ((now / 125000ull) & 1u) != 0;
      bool blink_red = stale && ((now / 250000ull) & 1u) != 0;
      set_leds(!stale && current_code == ADV_NONE,
               (!stale && current_code == ADV_JUMP) || (uncertain && blink_yellow),
               (!stale && current_code == ADV_STOP) || blink_red,
               uncertain, true);
      if (now >= next_ack) {
        ack.data = last_sequence;
        rcl_ret_t publish_rc = rcl_publish(&pub, &ack, NULL);
        (void)publish_rc;
        next_ack = now + ACK_PERIOD_US;
      }
      if (now - last_ping >= 1000000ull) {
        last_ping = now;
        if (rmw_uros_ping_agent(100, 1) != RMW_RET_OK) connected = false;
      }
    }
    set_leds(false, false, false, false, false);
    entities_fini(&executor, &pub, &sub, &node, &support);
    input_fini(&input);
  }
}
