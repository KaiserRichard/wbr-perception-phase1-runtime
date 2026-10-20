/* Small host protocol: I delay_ms, R, S measurement[6], C measurement[6],
 * A requested[2]. Every successful line prints requested[2], clipped[2],
 * then post-operation torque[2] and newest-first history (unpadded).
 */
#include "../wbr_lqr.h"

#include <assert.h>
#include <float.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static void units(void)
{
    wbr_lqr state, before, other;
    wbr_lqr_output out = {{17, 19}, {23, 29}}, saved;
    double measurement[6] = {0}, clipped[2] = {31, 37};
    const double invalid[2] = {1, NAN}, issued[2] = {8, -9};
    unsigned delay;
    assert(wbr_lqr_init(NULL, 2) == WBR_LQR_INVALID);
    assert(wbr_lqr_init(&state, 5) == WBR_LQR_OK);
    before = state;
    assert(wbr_lqr_init(&state, 6) == WBR_LQR_INVALID);
    assert(memcmp(&state, &before, sizeof(state)) == 0);
    assert(wbr_lqr_advance(&state, invalid, clipped) == WBR_LQR_INVALID);
    assert(clipped[0] == 31 && clipped[1] == 37);
    assert(memcmp(&state, &before, sizeof(state)) == 0);
    saved = out;
    measurement[2] = INFINITY;
    assert(wbr_lqr_step(&state, measurement, &out) == WBR_LQR_INVALID);
    assert(memcmp(&out, &saved, sizeof(out)) == 0);
    assert(memcmp(&state, &before, sizeof(state)) == 0);
    measurement[2] = DBL_MAX; /* Finite input, overflowing requested command. */
    assert(wbr_lqr_step(&state, measurement, &out) == WBR_LQR_INVALID);
    assert(memcmp(&out, &saved, sizeof(out)) == 0);
    assert(memcmp(&state, &before, sizeof(state)) == 0);
    measurement[2] = 0.1;
    assert(wbr_lqr_command(&state, measurement, &out) == WBR_LQR_OK);
    assert(memcmp(&state, &before, sizeof(state)) == 0);
    for (delay = 2; delay <= 5; ++delay) {
        assert(wbr_lqr_init(&state, delay) == WBR_LQR_OK);
        assert(wbr_lqr_init(&other, delay) == WBR_LQR_OK);
        assert(wbr_lqr_step(&state, measurement, &out) == WBR_LQR_OK);
        assert(wbr_lqr_command(&other, measurement, &saved) == WBR_LQR_OK);
        assert(wbr_lqr_advance(&other, saved.requested, clipped) == WBR_LQR_OK);
        assert(memcmp(&state, &other, sizeof(state)) == 0);
        assert(memcmp(&out, &saved, sizeof(out)) == 0);
        assert(wbr_lqr_advance(&state, issued, clipped) == WBR_LQR_OK);
        assert(clipped[0] == 2 && clipped[1] == -4);
        assert(wbr_lqr_reset(&state) == WBR_LQR_OK);
        assert(wbr_lqr_init(&other, delay) == WBR_LQR_OK);
        assert(memcmp(&state, &other, sizeof(state)) == 0);
    }
    puts("host unit checks passed");
}

int main(int argc, char **argv)
{
    wbr_lqr state;
    char op;
    unsigned delay, a, i;
    double measurement[6];
    if (argc == 2 && strcmp(argv[1], "--unit") == 0) {
        units();
        return 0;
    }
    if (wbr_lqr_init(&state, 2) != WBR_LQR_OK)
        return 1;
    while (scanf(" %c", &op) == 1) {
        wbr_lqr_output out = {{0, 0}, {0, 0}};
        int status = WBR_LQR_INVALID;
        if (op == 'I' && scanf("%u", &delay) == 1)
            status = wbr_lqr_init(&state, delay);
        else if (op == 'R')
            status = wbr_lqr_reset(&state);
        else if (op == 'S' || op == 'C') {
            for (i = 0; i < 6; ++i)
                if (scanf("%lf", &measurement[i]) != 1)
                    return 2;
            status = op == 'S' ? wbr_lqr_step(&state, measurement, &out)
                              : wbr_lqr_command(&state, measurement, &out);
        } else if (op == 'A' &&
                   scanf("%lf %lf", &out.requested[0], &out.requested[1]) == 2) {
            status = wbr_lqr_advance(&state, out.requested, out.clipped);
        }
        if (status != WBR_LQR_OK)
            return 3;
        printf("%.17g %.17g %.17g %.17g %.17g %.17g",
               out.requested[0], out.requested[1], out.clipped[0], out.clipped[1],
               state.torque_estimate[0], state.torque_estimate[1]);
        for (i = 0; i < wbr_lqr_history_steps(&state); ++i)
            for (a = 0; a < 2; ++a)
                printf(" %.17g", state.history[i][a]);
        putchar('\n');
    }
    return 0;
}
