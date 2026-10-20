# Deterministic PPO export (offline only)

Exports a **trusted completed** SB3 v2 seed folder (`final.zip`,
`vecnormalize.pkl`, `status.json`) to C99 weights/inference and optionally ONNX.
No training, MuJoCo construction, hardware interface, or backend installation.
Checkpoint pickles are executable Python inputs: only use owner-trusted artifacts.
Incomplete folders are rejected; source files are hashed before/after loading.
The source policy/statistics are read only. Use a new output directory each time.

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1
PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
$PY -m sim.policy_export.export --checkpoint-dir /path/to/completed/direct/seed-0 --out /new/export-directory
$PY -m sim.policy_export.validate --checkpoint-dir /path/to/completed/direct/seed-0 --export-dir /new/export-directory
$PY -m unittest discover -s sim/policy_export/tests -v
```

Generated `policy.c` contains immutable weights/statistics and allocation-free
host plain-C functions; `policy.h` declares the interface. `manifest.json` records
source hashes, normalization, architecture and timing contract. `parity.json`
records actual validation; `policy_host.so` is a host-only temporary shared
library. Keep generated checkpoint-derived artifacts out of git.

Supported actor: flat 15-input MlpPolicy, unsquashed diagonal Gaussian, Linear /
Tanh / ReLU / Identity, two Box[-1,1] actions. Unsupported actors fail explicitly.
Only the deterministic Gaussian mean is exported; no sampling, critic, optimizer,
reward normalization, or learned log-standard-deviation is needed at inference.

## Preprocessing and composition

`wbr_encode` takes six **causal measurements** in this order:
`[x, leg_angle, body_angle, xdot, leg_rate, body_rate]`, two causal estimated
motor torques, three newest-first issued-command pairs, and known delay.
Right-pad history with zero pairs to length three. Divisors are
`[1.5, pi/4, pi/4, 1, 5, 5]`, `[2,4]`, `[2,4]` per history pair, and `0.005 s`.
The caller maintains history/torque estimates exactly as in the existing runtime;
these functions do not implement a sensor or actuator observer.

For this encoded vector $e$, frozen VecNormalize statistics give

$$
z_i=\operatorname{float32}\left(\operatorname{clip}\left(
\frac{e_i-\mu_i}{\sqrt{\sigma_i^2+\epsilon}},-c,c\right)\right).
$$

Normalization uses float64 arithmetic then casts to float32, matching saved
VecNormalize, including epsilon **inside** the square root. Statistics are never
updated. The network gives raw Gaussian mean $a$, then

$$
b=\operatorname{clip}(a,-1,1),\qquad
h=b\odot[2,4]\times\begin{cases}1&\text{direct}\\0.2&\text{residual}.\end{cases}
$$

`wbr_policy` returns raw, bounded and held values. Call it at **100 Hz** on the
current encoded observation; hold `h` for five 2 ms control ticks. On **every
500 Hz tick**, call `wbr_compose`:

$$
u_k=\operatorname{clip}\left(
\begin{cases}h&\text{direct}\\-K(d)\hat x_{\mathrm{aug},k}+h&\text{residual},\end{cases}
-[2,4],[2,4]\right).
$$

Supply current **unclipped** causal LQR output as `lqr_Nm`; the caller computes it
with the existing delay-aware controller each tick. Do not clip the LQR term
before adding the correction. Direct ignores the finite supplied LQR values.
Residual correction caps are `[0.4,0.8] Nm`; total caps remain `[2,4] Nm`.
`wbr_compose` also clamps externally supplied held values to the correction caps.
Example: residual mean `[2,-0.5]` clips to `[1,-0.5]`, giving held correction
`[0.4,-0.4] Nm`. Current LQR `[1.8,-3.9]` gives total `[2,-4] Nm` after clipping.
This command goes through the existing actuator delay/lag model; it is not an
applied motor torque. LQR synthesis, estimator state, actuator state, reset/
termination, and motor safety remain external and are not deployment-validated.
The actor and composition use float32; the simulation performs its external
torque scaling/LQR composition in float64. C/PyTorch parity uses the stated
float32 interface, not bitwise equality with every simulator control operation.

C returns `-1` on nonfinite inputs; outputs on error are unspecified and must
never be consumed. Finite bounded-vector parity does not certify arbitrary
inputs, closed-loop stability, real hardware, or worst-case execution time.

## ONNX validation and isolated dependencies

The first B2 run had no ONNX dependencies and reported PENDING with one test
skip; that historical result remains in the session log and `direct-export/`.
The follow-up **produced a real ONNX graph**, passed `onnx.checker`, and passed
ONNX Runtime CPU parity against PyTorch and compiled C using the read-only
completed direct seed-0 checkpoint. The active backend remains unchanged:
only six missing binary-wheel dependencies were installed into an external
target, reusing its NumPy **1.26.4** and Torch **2.2.2**.

Exact dependency command used (no dependency resolution, source compilation,
Torch reinstall, or writes into the backend environment):

```sh
PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
ONNX_DEPS=/private/tmp/wbr-overnight-20261020/B2/onnx-deps
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1
nice -n 10 "$PY" -m pip install --only-binary=:all: --no-deps --target "$ONNX_DEPS" \
  onnx==1.16.2 onnxruntime==1.19.2 protobuf==5.28.3 \
  coloredlogs==15.0.1 humanfriendly==10.0 flatbuffers==24.3.25
```

Existing backend `packaging==26.3` and `sympy==1.14.0` satisfy the remaining
runtime imports. Use a fresh target for a new installation. Scoped `PYTHONPATH`
makes the dependencies visible only to these commands:

```sh
CHECKPOINT=/Users/quockaiser/wbr-evidence-archive/sim-ppo-v2-20261020-01/direct/seed-0
OUT=/private/tmp/wbr-overnight-20261020/B2/direct-onnx-export
PYTHONPATH="$ONNX_DEPS" nice -n 10 "$PY" -m sim.policy_export.export --checkpoint-dir "$CHECKPOINT" --out "$OUT"
PYTHONPATH="$ONNX_DEPS" nice -n 10 "$PY" -m sim.policy_export.validate --checkpoint-dir "$CHECKPOINT" --export-dir "$OUT"
PYTHONPATH="$ONNX_DEPS" nice -n 10 "$PY" -m unittest discover -s sim/policy_export/tests -v
```

`OUT` above contains the actual artifacts; choose a new output directory to
repeat export. The final suite ran **5 tests in 4.989 s, all passed, no skips**,
including saved tiny direct/residual fixtures with nondefault epsilon, zero
variance, observation/action clipping, correction scaling and LQR composition.
The optional test still skips explicitly when dependencies are absent.

Real-checkpoint validation uses 64 bounded vectors (encoded absolute values at
most 1000, supplied LQR within 8 Nm), including both observation-clipping
boundaries, and checks dynamic batches of 64 and 1. Frozen SB3 VecNormalize and
action composition independently match the reference. At atol/rtol `3e-5`,
ONNX/PyTorch max action error is `8.94e-8` and max torque error `1.79e-7 Nm`;
ONNX/C errors are `5.96e-8` and `1.19e-7 Nm`, respectively. C/PyTorch torque
error is `1.79e-7 Nm`. Exact per-output errors are in `parity.json`.

The exporter uses PyTorch 2.2's legacy ONNX exporter (opset 17), which does not
need `onnxscript`; other exporter versions require fresh validation.
ONNX includes float64 normalization, float32 actor and
composition; inputs are batched `encoded` float64 and `lqr_Nm` float32. Outputs
are raw/bounded actions, held correction/torque, and composed torque. Its composed
output is a convenience for one tick: hold the correction and recompute LQR at
500 Hz externally. `onnx.checker` validates graph structure; the validator reports
runtime parity separately and only passes it after ONNX Runtime actually runs.
Completed real residual weights were not loaded; residual ONNX/C semantics were
validated with the saved tiny fixture. No rollout or hardware validation ran.

## Bounded integration with the C LQR controller

Run from the repository root with the existing backend (no ONNX dependencies
needed for this integration check):

```sh
PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 nice -n 10 "$PY" \
  -m unittest discover -s sim/policy_export/integration/tests -v
```

The [host harness](integration/host.c) links actual
[A2 C LQR](../control_c/wbr_lqr.h) with generated B2 policy C. Each 2 ms tick
reads the current unclipped LQR request; every fifth tick it evaluates the
policy from pre-tick measurements and C-owned torque/history. It composes the
held correction with the **unclipped** request, clips the total, and calls
`wbr_lqr_advance` exactly once with that total. Direct mode also advances history
using its total issued command. The harness has one controller instance per
loaded library and is only a synchronous host replay, without a timing loop.

Tests save/reload five deterministic **untrained tiny fixtures**, freeze saved
VecNormalize statistics (including nondefault epsilon/clipping and zero variance),
and compile each with the real controller. They replay 64 archived six-coordinate
measurement vectors per delay, separately for direct, residual and zero-correction
cases. Additional bounded sensor inputs distinguish addition before clipping from
addition after clipping on both channels/signs. Resets after 1/2/6/9 ticks check
pending commands, nonzero torque, held actions and the five-tick phase. No seed
selection or policy performance result is involved.

The Python oracle owns its own history, uses archived gains, saved SB3
normalization/deterministic means, declared float32 export composition, and exact
analytical command-only lag endpoints. It never imports or runs the plant.
A2 absolute tolerance remains $10^{-6}$ with zero relative tolerance for LQR,
torque/history and encoded observations; B2 remains atol/rtol $3\times10^{-5}$
for policy outputs and composed commands. A separate oracle retains simulator-style
float64 external scaling/composition and reports its differences explicitly;
it does not claim bitwise simulator equivalence. Host compilation disables
floating-point contraction and fast math.

Actual final integration run: four tests, five compiled fixtures and 1,464 replay
ticks passed in 7.700 s (first run 7.477 s); maximum C/oracle
errors were `7.88e-7 Nm` for LQR, `7.15e-7` for policy outputs and
`4.77e-7 Nm` for issued commands/torque/history. Export float32 versus
simulator-style float64 oracle command/history difference was `1.43e-7 Nm`.
Actual C versus that float64 oracle differed by at most `4.77e-7 Nm` in issued
commands/torque/history and `7.88e-7 Nm` in LQR requests on these inputs.
Tests print a preserved external artifact directory containing generated sources,
saved fixtures, exact compiler commands/logs and a numerical `report.json`.
This is **controller arithmetic replay**, with measured vectors reused as inputs;
full closed-loop simulation, hardware timing and hardware validation remain queued.

## Analytical STM32H7 cycle estimate — not measured

The completed directseed0 actor is **15 → 64 → 64 → 2**, with two tanh layers:
5,184 multiply-accumulate (MAC) operations, 5,314 float32 parameters (21,256 bytes),
128 tanh evaluations, and 512 bytes of C scratch arrays, excluding stack spills.
Normalization/divisor constants add 360 bytes of doubles and limits add 8 bytes.
Code, runtime libraries, caller state and compiler alignment add storage.

Illustrative assumptions: one Cortex-M7 core at an **assumed 400 MHz**; weights
and working state in fast internal memory or warm cache; scalar optimized C,
no interrupts/DMA contention, no accelerator, float32 MACs, and the exact
float64 normalization retained. Assume 3–8 cycles per MAC including loop/load,
80–300 cycles per tanh, 50–200 cycles per normalized observation (including
sqrt/division), and 1,000–4,000 cycles for remaining work. These are modeling
inputs, **not STM32/library measurements or worst-case bounds**; soft double,
libm implementation, flash/cache misses and interrupt load can exceed them.

$$
C=5184c_{\mathrm{MAC}}+128c_{\tanh}+15c_{\mathrm{norm}}+C_{\mathrm{other}}
=27{,}542\ldots86{,}872\text{ cycles}.
$$

At the assumed clock this is **68.9–217.2 µs per 100 Hz policy call**, or
0.69–2.17% of its 10 ms period. Worked midpoint example: coefficients
`5, 150, 100, 2000` give `48,620 cycles / 400 MHz = 121.6 µs`.
Per-tick two-action composition is additional; an assumed 100–500 cycles would
be 0.25–1.25 µs, excluding LQR, observer, encoding and all other control work.
This estimate supplies no hard real-time guarantee. No STM32 build, cycle-counter
measurement, flash or motor action was performed.
