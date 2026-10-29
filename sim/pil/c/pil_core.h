#ifndef PIL_CORE_H
#define PIL_CORE_H

/* Processor-in-the-loop (PIL) MCU side, transport independent.
 * Bytes in -> COBS/CRC-32C frame -> wbr_lqr_step -> reply frame out.
 * Shared by the host fake MCU (fake_mcu.c) and the Nucleo-F446RE firmware.
 * Frame layout: docs/pil/DESIGN.md. Bench prototype, not a robot interface.
 */
#include <stddef.h>
#include <stdint.h>

#include "wbr_lqr.h"

#define PIL_VERSION 1u
#define PIL_TYPE_STATE 0x10u
#define PIL_TYPE_TORQUE 0x11u
#define PIL_FLAG_RESET 0x01u
#define PIL_STATE_RAW 60u   /* 8 header + 6 f64 + CRC-32C */
#define PIL_REPLY_RAW 52u   /* 8 header + 4 f64 + 2 u32 + CRC-32C */
#define PIL_MAX_ENCODED 64u /* >= COBS(60) = 61 */

typedef enum {
    PIL_OK = 0,
    PIL_LQR_INVALID = 1, /* wbr_lqr_step rejected input (nonfinite...) */
    PIL_NOT_READY = 2,   /* no reset frame since boot */
    PIL_BAD_DELAY = 3    /* delay profile not 2..5 ms, or changed without reset */
} pil_status;

typedef struct {
    void (*tx)(void *ctx, const uint8_t *data, size_t n); /* whole frame */
    uint32_t (*cycles)(void *ctx); /* free-running counter, wraps mod 2^32 */
    void (*mark)(void *ctx, int high); /* GPIO around the controller step; may be NULL */
    void *ctx;
    uint32_t cpu_hz; /* counter rate reported to the host */
} pil_hooks;

typedef struct {
    pil_hooks hooks;
    uint8_t encoded[PIL_MAX_ENCODED];
    size_t used;
    int dropping;
    int ready;
    wbr_lqr lqr;
    uint32_t frames, errors, last_exec;
} pil_mcu;

void pil_mcu_init(pil_mcu *m, const pil_hooks *hooks);
/* Any chunking; one reply per valid STATE frame, none for a malformed frame. */
void pil_mcu_feed(pil_mcu *m, const uint8_t *data, size_t n);

#endif
