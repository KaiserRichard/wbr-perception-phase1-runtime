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

For this encoded vector \(e\), frozen VecNormalize statistics give

\[
z_i=\operatorname{float32}\left(\operatorname{clip}\left(
\frac{e_i-\mu_i}{\sqrt{\sigma_i^2+\epsilon}},-c,c\right)\right).
\]

Normalization uses float64 arithmetic then casts to float32, matching saved
VecNormalize, including epsilon **inside** the square root. Statistics are never
updated. The network gives raw Gaussian mean \(a\), then

\[
b=\operatorname{clip}(a,-1,1),\qquad
h=b\odot[2,4]\times\begin{cases}1&\text{direct}\\0.2&\text{residual}.\end{cases}
\]

`wbr_policy` returns raw, bounded and held values. Call it at **100 Hz** on the
current encoded observation; hold `h` for five 2 ms control ticks. On **every
500 Hz tick**, call `wbr_compose`:

\[
u_k=\operatorname{clip}\left(
\begin{cases}h&\text{direct}\\-K(d)\hat x_{\mathrm{aug},k}+h&\text{residual},\end{cases}
-[2,4],[2,4]\right).
\]

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

## ONNX status and isolated dependency work

The supplied backend lacks `onnx`, `onnxruntime`, and `onnxscript` as of this run.
**No ONNX file was produced or validated.** Export records `PENDING`; the optional
ONNX unit test skips explicitly. C/SB3 tests still execute. No dependency install
was attempted while PPO was active.

Queued work: create an isolated environment with a compatible CPU PyTorch/SB3,
NumPy, ONNX and ONNX Runtime stack, then repeat the commands above and run the
optional test. Never install into the active PPO environment. The exporter uses
PyTorch 2.2's legacy ONNX exporter (opset 17); other exporter versions require a
fresh validation. ONNX includes float64 normalization, float32 actor and
composition; inputs are batched `encoded` float64 and `lqr_Nm` float32. Outputs
are raw/bounded actions, held correction/torque, and composed torque. Its composed
output is a convenience for one tick: hold the correction and recompute LQR at
500 Hz externally. `onnx.checker` validates graph structure; the validator reports
runtime parity separately and only passes it after ONNX Runtime actually runs.

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

\[
C=5184c_{\mathrm{MAC}}+128c_{\tanh}+15c_{\mathrm{norm}}+C_{\mathrm{other}}
=27{,}542\ldots86{,}872\text{ cycles}.
\]

At the assumed clock this is **68.9–217.2 µs per 100 Hz policy call**, or
0.69–2.17% of its 10 ms period. Worked midpoint example: coefficients
`5, 150, 100, 2000` give `48,620 cycles / 400 MHz = 121.6 µs`.
Per-tick two-action composition is additional; an assumed 100–500 cycles would
be 0.25–1.25 µs, excluding LQR, observer, encoding and all other control work.
This estimate supplies no hard real-time guarantee. No STM32 build, cycle-counter
measurement, flash or motor action was performed.
