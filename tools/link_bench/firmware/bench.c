/* See bench.h. Status fields follow SPEC.md McuStatus; controller-owned fields
 * (faults, fsm, armed, operator_enable, battery) are zero/invalid because this
 * bench MCU has no controller. */
#include "bench.h"
#include <string.h>

static void send_status(bench_port *p) {
 lp_message m; lp_status *s = &m.data.status; uint8_t wire[LP_MAX_WIRE]; size_t n;
 memset(&m, 0, sizeof(m));
 m.type = LP_MCU_STATUS; m.session = p->boot_id; m.seq = ++p->status_seq;
 s->sample_mcu_ns = p->now_us * 1000u;
 s->last_health_seq = p->rx.health_seq;
 s->last_estimate_seq = p->rx.estimate_seq;
 s->last_ref_seq = p->rx.ref_seq;
 s->action_mcu_ns = p->action_us * 1000u;
 s->state = (uint8_t)p->rx.state;
 s->reason = (uint8_t)p->rx.reason;
 n = lp_pack(&m, wire, sizeof(wire));
 if (n == 0) { p->tx_dropped++; return; }
 p->tx(p->tx_ctx, wire, n);
 p->status_sent++;
 p->last_status_us = p->now_us;
 p->reported_state = p->rx.state;
}

static int withdrawn(lp_state s) { return s == LP_NO_LINK || s == LP_STALE || s == LP_REJECTED; }

static void on_packet(void *ctx, const lp_message *m) {
 bench_port *p = ctx;
 if (p->mark) p->mark(p->tx_ctx);
 if (lp_receiver_accept(&p->rx, (uint32_t)p->now_us, m)) p->accepted++;
 else { p->rejected++; p->action_us = p->now_us; }
 send_status(p);
}

static void on_error(void *ctx) {
 bench_port *p = ctx;
 lp_receiver_reject(&p->rx, LP_REASON_WIRE);
 p->rejected++; p->action_us = p->now_us;
 send_status(p);
}

void bench_init(bench_port *p, uint64_t boot_id, bench_tx_fn tx, void *tx_ctx) {
 memset(p, 0, sizeof(*p));
 p->boot_id = boot_id; p->tx = tx; p->tx_ctx = tx_ctx;
 lp_stream_init(&p->stream);
 lp_receiver_bind(&p->rx, BENCH_SESSION, BENCH_MAPPING_REVISION, BENCH_TRANSFORM_REVISION);
 p->reported_state = p->rx.state;
}

void bench_rx(bench_port *p, const uint8_t *data, size_t n, uint64_t now_us) {
 p->now_us = now_us;
 lp_stream_feed(&p->stream, data, n, on_packet, on_error, p);
}

void bench_poll(bench_port *p, uint64_t now_us) {
 lp_state before = p->rx.state;
 p->now_us = now_us;
 lp_receiver_update(&p->rx, (uint32_t)now_us);
 if (p->rx.state != before && withdrawn(p->rx.state)) p->action_us = now_us;
 if (p->rx.state != p->reported_state || now_us - p->last_status_us >= BENCH_STATUS_PERIOD_US)
  send_status(p);
}

int bench_linked(const bench_port *p) { return p->rx.state != LP_NO_LINK; }
