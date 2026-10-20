#include "wbr_lqr.h"

#include <float.h>
#include <math.h>
#include <stddef.h>
#include <string.h>

#if FLT_RADIX != 2 || DBL_MANT_DIG != 53 || DBL_MAX_EXP != 1024
#error "This port requires IEEE-754 binary64 double precision."
#endif

#include "gains.inc"

static const double limits[WBR_LQR_INPUTS] = {2.0, 4.0};

unsigned wbr_lqr_history_steps(const wbr_lqr *state)
{
    if (state == NULL || state->delay_ms < 2 || state->delay_ms > 5)
        return 0;
    return (state->delay_ms + 1) / 2;
}

int wbr_lqr_init(wbr_lqr *state, unsigned delay_ms)
{
    if (state == NULL || delay_ms < 2 || delay_ms > 5)
        return WBR_LQR_INVALID;
    memset(state, 0, sizeof(*state));
    state->delay_ms = delay_ms;
    return WBR_LQR_OK;
}

int wbr_lqr_reset(wbr_lqr *state)
{
    if (!wbr_lqr_history_steps(state))
        return WBR_LQR_INVALID;
    return wbr_lqr_init(state, state->delay_ms);
}

static int clip(const double requested[2], double clipped[2])
{
    unsigned a;
    if (requested == NULL)
        return WBR_LQR_INVALID;
    for (a = 0; a < 2; ++a) {
        if (!isfinite(requested[a]))
            return WBR_LQR_INVALID;
        clipped[a] = fmax(-limits[a], fmin(limits[a], requested[a]));
    }
    return WBR_LQR_OK;
}

int wbr_lqr_command(const wbr_lqr *state, const double measurement[6],
                    wbr_lqr_output *output)
{
    double z[WBR_LQR_MAX_STATE] = {0};
    wbr_lqr_output next;
    unsigned a, i, n = wbr_lqr_history_steps(state);
    if (!n || measurement == NULL || output == NULL)
        return WBR_LQR_INVALID;
    for (i = 0; i < 6; ++i) {
        if (!isfinite(measurement[i]))
            return WBR_LQR_INVALID;
        z[i] = measurement[i];
    }
    for (a = 0; a < 2; ++a) {
        z[6 + a] = state->torque_estimate[a];
        for (i = 0; i < n; ++i)
            z[8 + 2 * i + a] = state->history[i][a];
    }
    for (a = 0; a < 2; ++a) {
        next.requested[a] = 0.0;
        for (i = 0; i < 8 + 2 * n; ++i)
            next.requested[a] -= gains[state->delay_ms - 2][a][i] * z[i];
    }
    if (clip(next.requested, next.clipped) != WBR_LQR_OK)
        return WBR_LQR_INVALID;
    *output = next;
    return WBR_LQR_OK;
}

static void lag(double torque[2], const double delivered[2], double duration)
{
    /* Same exact endpoint as sim.augmented.lag_interval, T = 5 ms.
     * Constant-command substeps can be combined without changing the model.
     */
    const double decay = 1.0 + expm1(-duration / 0.005);
    unsigned a;
    for (a = 0; a < 2; ++a)
        torque[a] = delivered[a] + (torque[a] - delivered[a]) * decay;
}

int wbr_lqr_advance(wbr_lqr *state, const double requested[2], double clipped[2])
{
    double issued[2];
    unsigned a, i, n = wbr_lqr_history_steps(state);
    if (!n || clipped == NULL || clip(requested, issued) != WBR_LQR_OK)
        return WBR_LQR_INVALID;

    /* Use OLD history throughout the prediction. At integer delay n*dt,
     * u[k-n] is delivered for this whole interval. At fractional delay
     * (n-1)*dt + 1 ms, u[k-n] applies for 1 ms, then u[k-n+1] for 1 ms.
     * In particular 5 ms is not rounded to either 4 or 6 ms.
     * An arrival at the end has zero duration here and acts next tick.
     */
    if (state->delay_ms % 2) {
        lag(state->torque_estimate, state->history[n - 1], 0.001);
        lag(state->torque_estimate, state->history[n - 2], 0.001);
    } else {
        lag(state->torque_estimate, state->history[n - 1], 0.002);
    }
    for (i = n - 1; i > 0; --i)
        for (a = 0; a < 2; ++a)
            state->history[i][a] = state->history[i - 1][a];
    for (a = 0; a < 2; ++a)
        state->history[0][a] = clipped[a] = issued[a];
    return WBR_LQR_OK;
}

int wbr_lqr_step(wbr_lqr *state, const double measurement[6],
                wbr_lqr_output *output)
{
    wbr_lqr_output next;
    if (output == NULL ||
        wbr_lqr_command(state, measurement, &next) != WBR_LQR_OK)
        return WBR_LQR_INVALID;
    if (wbr_lqr_advance(state, next.requested, next.clipped) != WBR_LQR_OK)
        return WBR_LQR_INVALID;
    *output = next;
    return WBR_LQR_OK;
}
