# A3 assumed-model gain sweep and fit

**Result:** both authorized procedural stages completed. Fresh delay-aware gain
synthesis produced 76/76 designs over 19 lengths (0.12–0.30 m) and four delays
(2, 3, 4, 5 ms), with zero recorded design errors. The separate degree-3
Chebyshev fit completed for each delay. These results belong to the assumed
fixed-mass, geometrically scaled rigid-leg model; this 0.12–0.30 m family is
hypothetical and is not the five-bar mechanism (maximum reach about 0.211 m).

## Run receipt

- Source commit: `140a11b45e035190d89f4af0905b70975dce9f7c`.
- Config: `sim/configs/assumed_actuator_noise.json`.
- Interpreter: read-only `/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python`; BLAS/thread variables set to 1; sweep ran at nice 10. Perl alarm capped sweep at 120 s and fit at 30 s.
- Sweep command: `python -m sim.gain_schedule sweep --config sim/configs/assumed_actuator_noise.json --delays .002 .003 .004 .005 --out /Users/quockaiser/wbr-evidence-archive/sim-gain-sweep-20261021-01/sweep` (exit 0, `COMPLETE`, 9.86 s).
- Fit command: `python -m sim.gain_schedule fit --sweep /Users/quockaiser/wbr-evidence-archive/sim-gain-sweep-20261021-01/sweep/sweep.json --degree 3 --out /Users/quockaiser/wbr-evidence-archive/sim-gain-sweep-20261021-01/fit` (exit 0, `COMPLETE`, 0.31 s).
- Artifacts: `sweep/sweep.json`, `fit/schedule.json`; initial command/setup errors retained under `attempts/`.

## Fit diagnostics

Each delay has 19 samples, rank 4, and Chebyshev design-matrix 2-norm
condition number 1.924 (raw metre power-basis comparison: 9,569.95). Coefficients
are finite, shaped `[degree=0..3, actuator, state]`; each regime keeps its own
state matrix and fit. Across the four fits, whole-matrix relative Frobenius error
is 0.000515–0.000531; largest individual entry RMSE is 0.01035–0.01085 and
largest absolute entry error is 0.02084–0.02215. These summaries mix gain-entry units; they are numerical fit diagnostics, not torque-error bounds.

Gain units are actuator torque per state unit. Input order is wheel-pair torque,
virtual-hip-pair torque (N·m). State order starts `x (m), leg angle (rad), body
angle (rad), x velocity (m/s), leg rate (rad/s), body rate (rad/s)`, then wheel
and hip reconstructed torque estimates (N·m), followed by clipped command
history as wheel/hip N·m pairs. Matrix sizes are 2×10, 2×12, 2×12, and 2×14
for delays 2, 3, 4, and 5 ms respectively.

Recorded sampled local closed-loop pole radii are 0.997212–0.997698; relative
DARE residuals are 1.77e-13–3.55e-12 across designs. These are assumed-model
linear design diagnostics only. They do not establish a good fit for control,
nonlinear balance, or stability between samples.

Conductor independently checked all 76 shapes/finite matrices, local-design records and every entry-wise fitted maximum error against direct Chebyshev reconstruction. No additional rollout.

**Limitations:** all 400 nonlinear balance/push cases remain **UNRUN**. No
nonlinear rollout or hardware validation was performed; no thresholds or polynomial
degree were tuned. The separate owner DM-jump polynomial exercise remains
untouched.

Claude review line: A3 procedural gain synthesis and degree-3 fits completed; review this note for numerical diagnostics and the explicit 400-case limitation.
