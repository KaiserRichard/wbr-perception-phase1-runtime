/* Host-only single-instance arithmetic replay; no clock, plant or motor I/O.
 * Link the actual A2 controller and one generated B2 policy. Not a public API.
 * A failed tick must terminate the replay; error recovery is not implemented.
 */
#include "wbr_lqr.h"
#include "policy.h"

#include <string.h>

static wbr_lqr controller;
static unsigned phase, policy_calls;
static float raw[2], bounded[2], held[2];

int host_reset(void)
{
    if (wbr_lqr_reset(&controller) != WBR_LQR_OK)
        return -1;
    phase = policy_calls = 0;
    memset(raw, 0, sizeof(raw));
    memset(bounded, 0, sizeof(bounded));
    memset(held, 0, sizeof(held));
    return 0;
}

int host_init(unsigned delay_ms)
{
    if (wbr_lqr_init(&controller, delay_ms) != WBR_LQR_OK)
        return -1;
    return host_reset();
}

/* out: encoded[15], raw[2], bounded[2], held[2], requested_LQR[2],
 * clipped_LQR[2], issued_total[2], post_torque[2], post_history[6],
 * next_phase, policy_calls. History is zero padded to three pairs.
 */
int host_tick(const double measurement[6], double out[37])
{
    double encoded[15], total[2], issued[2], history[6];
    float lqr32[2], command[2];
    wbr_lqr_output lqr;
    unsigned a, i, cursor = 0;
    for (i = 0; i < 3; ++i)
        for (a = 0; a < 2; ++a)
            history[2*i+a] = controller.history[i][a];
    if (wbr_lqr_command(&controller, measurement, &lqr) != WBR_LQR_OK ||
        wbr_encode(measurement, controller.torque_estimate, history,
                   controller.delay_ms / 1000.0, encoded) != 0)
        return -1;
    if (phase == 0) {
        if (wbr_policy(encoded, raw, bounded, held) != 0)
            return -1;
        ++policy_calls;
    }
    for (a = 0; a < 2; ++a)
        lqr32[a] = (float)lqr.requested[a]; /* NEVER use lqr.clipped here. */
    if (wbr_compose(held, lqr32, command) != 0)
        return -1;
    for (a = 0; a < 2; ++a)
        total[a] = command[a];
    /* Exactly one advance, using the TOTAL issued command, including direct. */
    if (wbr_lqr_advance(&controller, total, issued) != WBR_LQR_OK)
        return -1;
    phase = (phase + 1) % WBR_POLICY_HOLD_TICKS;
    for (i = 0; i < 15; ++i) out[cursor++] = encoded[i];
    for (a = 0; a < 2; ++a) out[cursor++] = raw[a];
    for (a = 0; a < 2; ++a) out[cursor++] = bounded[a];
    for (a = 0; a < 2; ++a) out[cursor++] = held[a];
    for (a = 0; a < 2; ++a) out[cursor++] = lqr.requested[a];
    for (a = 0; a < 2; ++a) out[cursor++] = lqr.clipped[a];
    for (a = 0; a < 2; ++a) out[cursor++] = issued[a];
    for (a = 0; a < 2; ++a) out[cursor++] = controller.torque_estimate[a];
    for (i = 0; i < 3; ++i)
        for (a = 0; a < 2; ++a)
            out[cursor++] = controller.history[i][a];
    out[cursor++] = phase;
    out[cursor] = policy_calls;
    return 0;
}
