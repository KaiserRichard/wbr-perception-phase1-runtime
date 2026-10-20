# Delay-aware LQR in plain C

This is a host-validated port of the existing **assumed six-state planar**
delay-aware controller. It embeds the archived augmented gains, reconstructs
motor torque from issued commands, and preserves clipping and causal history.
It contains no plant, sensor noise generator, gain synthesis, motor interface,
or hardware timing code. No STM32 build, deployment, timing measurement, or
hardware validation is claimed.

The four gain matrices are copied from `K_used` in
`~/wbr-evidence-archive/sim-actuator-20261020-01/augmented_linearization_{2,3,4,5}ms.json`.
`fixtures/recorded.json` retains their original float64 byte hashes and source
file hashes. No Q/R or gains were changed; the owner's `gain_schedule` exercise
is unrelated and untouched.

| Transport delay | Prior command pairs | Augmented dimension |
| --- | --- | --- |
| 2 ms | 1 | 10 |
| 3 ms | 2 | 12 |
| 4 ms | 2 | 12 |
| 5 ms | 3 | 14 |

All profiles retain the 2 ms control period, two 5 ms motor time constants, and
wheel-pair / virtual-hip-pair command limits of 2 / 4 N m. These are the existing
assumptions, not measured hardware parameters.

## Interface and ordering

Compile `wbr_lqr.c` as C99 with the standard math library (`-lm`).
The library uses fixed-size state, no allocation, and no I/O.

```c
#include "wbr_lqr.h"

wbr_lqr controller;
wbr_lqr_output output;
double measured[6] = {0};

/* Check return codes; pass the current cached measurement once per tick. */
int status = wbr_lqr_init(&controller, 5);
if (status == WBR_LQR_OK)
    status = wbr_lqr_step(&controller, measured, &output);
/* output.clipped is the issued command for this tick.
 * controller now holds the reconstructed state for the next 2 ms tick. */
```

Measurements are `[x, absolute leg pitch, absolute body pitch, x velocity,
leg pitch rate, body pitch rate]` in SI units. For tick $k$, with
$n=\lceil d/\Delta t\rceil$, the pre-update feedback vector is

$$
z_k=[y_k,\hat\tau_k,u_{k-1},\ldots,u_{k-n}],\qquad
u_k=\operatorname{clip}(-K_d z_k,\;-[2,4],\;[2,4]).
$$

`wbr_lqr_step` computes that command first, then advances the torque estimate
using **old** command history, then stores the newly clipped command at the
front of history. An integer-delay arrival at the interval end has no effect
on that interval's torque. For fractional delays the update splits exactly
at the arrival within the tick.

For delivered command $v$, the command-only filter is

$$
\dot{\hat\tau}=(v-\hat\tau)/T,\qquad
\hat\tau(t+h)=v+(\hat\tau(t)-v)e^{-h/T},\quad T=0.005\ \mathrm{s}.
$$

As a worked 5 ms example, a 1 N m command issued at time zero contributes
nothing to the estimates at 2 or 4 ms. During the 4–6 ms interval, the
prehistory command applies for the first 1 ms and the command issued at zero
applies for the last 1 ms. The 6 ms estimate is therefore
$1-e^{-0.001/0.005}=0.1812692469$ N m. At tick $k$, those two segments use
$u_{k-3}$, then $u_{k-2}$; the command $u_k$ cannot influence either.

`wbr_lqr_command` is read-only, so repeated reads do not advance history.
Call `wbr_lqr_advance` once with the actual issued command if using the split
API; it clips before recording history. Do not additionally call `step` for
that same tick. `reset` preserves the selected delay profile and zeros torque
and all command history, including commands that have not yet arrived.
Use reset only when the assumed zero initial actuator state is appropriate.

Initialize each state before use and keep its fields unmodified. Buffers must
not alias the state. Unsupported delay profiles, null arguments, nonfinite
inputs, and overflowed controller outputs return `WBR_LQR_INVALID` without
changing state/output. The caller owns timing and error handling.

## Numerical precision and validation

The port requires IEEE-754 binary64 `double`. The gain literals have 17
significant decimal digits. The host build disables floating-point contraction
and does not use fast math. `expm1` computes the decay, as in the Python filter.
The C estimator combines constant-command substeps analytically; Python uses
up to 0.25 ms mechanical substeps. The exponential composition is identical
mathematically, with small floating-point rounding differences. No float32,
fixed-point, or bitwise equivalence is claimed.

Run the assigned bounded check from the repository root:

```sh
PYTHON=${PYTHON:-python3}
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
"$PYTHON" \
  -m unittest discover -s sim/control_c/tests -v
```

Tests use only the Python standard library and a host C compiler. They compile
the actual library and replay the recorded six-coordinate measurements while
**C maintains its own torque/history across every tick**. They compare requested
commands, clipped commands, reconstructed torque and every history entry with
absolute tolerance $10^{-6}$, zero relative tolerance.

- 256 archived controller ticks: first 64 ticks of seed-0 balance, each delay.
- 56 additional Python-runtime ticks with synthetic sensor/action inputs:
  positive and negative saturation on both channels, pending-command reset,
  nonzero-torque reset, and seven zero-input ticks after reset.
- Independent analytical arrival/lag checks for all four delays, including
  the first nonzero 5 ms response; repeated reads and split/combined API parity;
  invalid-input checks and reset isolation.

On the assigned Mac backend, all six tests passed in 0.63 s. Maximum recorded
parity error was $1.86\times10^{-15}$; the analytical step-response maximum
was $4.44\times10^{-16}$. Builds, compiler logs and measured error summaries
remain under ignored `.build/parity-*` directories, including any failed runs.

Fixture extraction is explicit and separate from tests:

```sh
PYTHON=${PYTHON:-python3}
PYTHONDONTWRITEBYTECODE=1 \
"$PYTHON" \
  -m sim.control_c.record_fixtures \
  --archive "$HOME/wbr-evidence-archive/sim-actuator-20261020-01"
```

The extractor sets single-thread numerical-library limits before imports,
reads the archive without modifying it, and executes only the 56 synthetic
runtime ticks. It performs no gain synthesis or full simulation. The frozen
fixtures are independent of the current Python source during normal tests;
changes to the controller model require deliberate fixture review/regeneration.

This validates controller arithmetic and ordering against recorded inputs.
It does not establish a new closed-loop plant result, robustness to unknown
actuator dynamics, sensor realism, missed-tick behavior, or real-time execution.
No long simulation or training was run; no heavy work is needed for this
bounded port/parity task.
