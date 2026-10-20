#ifndef WBR_LQR_H
#define WBR_LQR_H

/* Host-validated assumed planar controller. No hardware or motor interface.
 * All values use double and SI units. One call to step/advance = 2 ms.
 * A state belongs to one caller; initialize before use, do not edit its fields.
 */
#define WBR_LQR_MEASUREMENTS 6
#define WBR_LQR_INPUTS 2
#define WBR_LQR_MAX_HISTORY 3
#define WBR_LQR_MAX_STATE 14
#define WBR_LQR_OK 0
#define WBR_LQR_INVALID -1

typedef struct {
    unsigned delay_ms;
    double torque_estimate[WBR_LQR_INPUTS];
    /* Clipped issued commands, newest first; unused rows remain zero. */
    double history[WBR_LQR_MAX_HISTORY][WBR_LQR_INPUTS];
} wbr_lqr;

typedef struct {
    double requested[WBR_LQR_INPUTS];
    double clipped[WBR_LQR_INPUTS];
} wbr_lqr_output;

/* Supported profiles are exactly 2, 3, 4, 5 ms; immutable archived gains.
 * Failed calls do not change state or output. Buffers must not alias state.
 */
int wbr_lqr_init(wbr_lqr *state, unsigned delay_ms);
int wbr_lqr_reset(wbr_lqr *state);
unsigned wbr_lqr_history_steps(const wbr_lqr *state);

/* Read-only u = -K [measurement, torque_estimate, history].
 * Measurement order: x, absolute leg pitch, absolute body pitch,
 * x velocity, leg pitch rate, body pitch rate (m, rad, m/s, rad/s).
 * Output order: wheel-pair torque, virtual hip-pair torque (N m).
 */
int wbr_lqr_command(const wbr_lqr *state,
                    const double measurement[WBR_LQR_MEASUREMENTS],
                    wbr_lqr_output *output);

/* Clip an issued command to +/-[2,4] N m, advance the causal torque
 * reconstruction by 2 ms, then prepend that clipped command to history.
 * This supports callers that combine the LQR output with an external command.
 * Call exactly once per tick, after command(), with the actual issued command.
 */
int wbr_lqr_advance(wbr_lqr *state, const double requested[WBR_LQR_INPUTS],
                   double clipped[WBR_LQR_INPUTS]);

/* command() then advance(), using the pre-tick state for feedback. After
 * success the state is ready for the next measurement, 2 ms later.
 */
int wbr_lqr_step(wbr_lqr *state,
                const double measurement[WBR_LQR_MEASUREMENTS],
                wbr_lqr_output *output);

#endif
