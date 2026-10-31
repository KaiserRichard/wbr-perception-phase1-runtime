#include "pil_core.h"

#include <string.h>

#include "link_proto.h" /* lp_crc32c, lp_cobs_encode/decode only */

static uint32_t get_u32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 |
           (uint32_t)p[3] << 24;
}

static void put_u32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24);
}

/* Little-endian IEEE-754 binary64 on the wire, independent of host order. */
static double get_f64(const uint8_t *p)
{
    uint64_t bits = (uint64_t)get_u32(p) | (uint64_t)get_u32(p + 4) << 32;
    double v;
    memcpy(&v, &bits, sizeof(v));
    return v;
}

static void put_f64(uint8_t *p, double v)
{
    uint64_t bits;
    memcpy(&bits, &v, sizeof(bits));
    put_u32(p, (uint32_t)bits);
    put_u32(p + 4, (uint32_t)(bits >> 32));
}

void pil_mcu_init(pil_mcu *m, const pil_hooks *hooks)
{
    memset(m, 0, sizeof(*m));
    m->hooks = *hooks;
}

static void reply(pil_mcu *m, uint32_t seq, pil_status status,
                  const wbr_lqr_output *out, uint32_t exec)
{
    uint8_t raw[PIL_REPLY_RAW], wire[PIL_MAX_ENCODED + 1];
    unsigned a;
    size_t n;
    memset(raw, 0, sizeof(raw));
    raw[0] = PIL_VERSION;
    raw[1] = PIL_TYPE_TORQUE;
    put_u32(raw + 2, seq);
    raw[6] = (uint8_t)status;
    for (a = 0; a < 2; ++a) {
        put_f64(raw + 8 + 8 * a, out ? out->requested[a] : 0.0);
        put_f64(raw + 24 + 8 * a, out ? out->clipped[a] : 0.0);
    }
    put_u32(raw + 40, exec);
    put_u32(raw + 44, m->hooks.cpu_hz);
    put_u32(raw + 48, lp_crc32c(raw, 48));
    n = lp_cobs_encode(raw, sizeof(raw), wire, PIL_MAX_ENCODED);
    if (!n)
        return;
    wire[n++] = 0;
    m->hooks.tx(m->hooks.ctx, wire, n);
}

static void handle(pil_mcu *m, const uint8_t *raw, size_t n)
{
    double y[WBR_LQR_MEASUREMENTS];
    wbr_lqr_output out;
    uint32_t seq, t0, t1;
    unsigned delay, i;
    int status;
    if (n != PIL_STATE_RAW || raw[0] != PIL_VERSION || raw[1] != PIL_TYPE_STATE ||
        (raw[6] & ~PIL_FLAG_RESET) || get_u32(raw + 56) != lp_crc32c(raw, 56)) {
        m->errors++;
        return;
    }
    seq = get_u32(raw + 2);
    delay = raw[7];
    for (i = 0; i < WBR_LQR_MEASUREMENTS; ++i)
        y[i] = get_f64(raw + 8 + 8 * i);
    m->frames++;
    if (raw[6] & PIL_FLAG_RESET) {
        m->ready = wbr_lqr_init(&m->lqr, delay) == WBR_LQR_OK;
        if (!m->ready) {
            reply(m, seq, PIL_BAD_DELAY, NULL, 0);
            return;
        }
    } else if (!m->ready) {
        reply(m, seq, PIL_NOT_READY, NULL, 0);
        return;
    } else if (delay != m->lqr.delay_ms) {
        reply(m, seq, PIL_BAD_DELAY, NULL, 0);
        return;
    }
    /* Timed region: exactly the controller step, nothing from the link. */
    if (m->hooks.mark)
        m->hooks.mark(m->hooks.ctx, 1);
    t0 = m->hooks.cycles(m->hooks.ctx);
    status = wbr_lqr_step(&m->lqr, y, &out);
    t1 = m->hooks.cycles(m->hooks.ctx);
    if (m->hooks.mark)
        m->hooks.mark(m->hooks.ctx, 0);
    m->last_exec = t1 - t0;
    if (status != WBR_LQR_OK)
        reply(m, seq, PIL_LQR_INVALID, NULL, m->last_exec);
    else
        reply(m, seq, PIL_OK, &out, m->last_exec);
}

void pil_mcu_feed(pil_mcu *m, const uint8_t *data, size_t n)
{
    uint8_t raw[PIL_MAX_ENCODED];
    size_t i, len;
    for (i = 0; i < n; ++i) {
        if (data[i] != 0) {
            if (m->dropping || m->used == sizeof(m->encoded)) {
                m->dropping = 1; /* oversize: discard until the next delimiter */
                continue;
            }
            m->encoded[m->used++] = data[i];
            continue;
        }
        if (m->dropping) {
            m->errors++;
        } else if (m->used) {
            len = lp_cobs_decode(m->encoded, m->used, raw, sizeof(raw));
            if (len)
                handle(m, raw, len);
            else
                m->errors++;
        }
        m->used = 0;
        m->dropping = 0;
    }
}
