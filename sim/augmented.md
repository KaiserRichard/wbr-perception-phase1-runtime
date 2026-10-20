# ASSUMED actuator/noise runtime

This extends the approved nominal planar plant for a later LQR/RL comparison.
It implements no RL and makes no hardware measurement or gain-parity claim.
`configs/assumed_actuator_noise.json` references and hash-locks the unchanged
`assumed_planar.json`: mechanics, 2 ms control period, 2/4 N m pair torque caps,
nominal Q/R, initial conditions, push and all acceptance thresholds stay fixed.

The added values are **ASSUMED illustrative parameters**, not measured STM32/CAN
latency, motor response or body IMU specifications: delays 2/3/4/5 ms, two 5 ms
motor time constants, independent zero-bias IID Gaussian body angle noise
0.1 degree standard deviation and body gyro noise 0.01 rad/s.

## Reusable API

```python
from dataclasses import replace
from sim.augmented import AugmentedRuntime, load_experiment

base, experiment, effects = load_experiment("sim/configs/assumed_actuator_noise.json")
runtime = AugmentedRuntime(base, replace(effects, delay_s=0.003))
obs = runtime.reset(seed=0)             # optional explicit six-state initial state
action = controller(obs)               # wheel pair, virtual hip pair, in N m
result = runtime.step(action, push_N=0) # exactly one 2 ms control interval
obs = result.observation
truth = runtime.truth()                # evaluator/reward ONLY, not policy feedback
```

- `RuntimeConfig`: delay seconds, two motor time constants, maximum mechanical
  substep, body angle/gyro noise standard deviations. All effects allow zero.
- `reset(state=None, seed=0)`: zero realized/estimated torque, zero command
  prehistory; same nominal initial state by default. Re-seeds both noise streams.
- `time`: actual MuJoCo time. `measurement()`: cached six-coordinate measurement.
  Only indices **2 (absolute BODY pitch)** and **5 (BODY gyro rate)** get noise.
  Translation, leg angle and their rates are explicitly ideal measurements, not
  claimed to be IMU outputs or realistic encoder/odometry estimators.
- `observation()`: returns copies of time, measurement, torque estimate,
  clipped command history (newest first), history timestamps and known delay.
  `obs.vector()` orders `[measured six-state, estimated wheel/hip torque,
  u[k-1], ..., u[k-n]]`, where `n=max(1, ceil(delay/control_dt))`.
  Dimensions at 2/3/4/5 ms are 10/12/12/14. A future policy covering several
  delays must explicitly pad/history-mask or otherwise handle these dimensions.
- `command_history()`: clipped commands with submission/arrival times; initial
  zero prehistory has negative submission times. Commands are clipped **before**
  entering transport, including the values available to either controller.
- `step(action_Nm, push_N=0)`: finite two-element action, held body COM push over
  this control interval; returns requested/clipped action, next observation and
  actual integration intervals. There is no internal acceptance termination or
  reward; `augmented_eval.evaluate` applies the frozen protocol.
- Each interval reports start time, actual dt, truth at its start, physical
  torque endpoints, MuJoCo-applied mean, exact torque-squared integral, delayed
  command/source timestamp and push. `truth()`, `torque()`, `sensor_noise()`,
  `evaluation_state()` and interval truth/noise fields are evaluation-only.
  **Do not feed StepResult diagnostic intervals or truth/noise into an RL policy.**
- `warning_counts` exposes numerical warnings for evaluation. No global
  callbacks or RNGs; each runtime owns its own mutable MuJoCo model/data.
  Returned arrays are copies. One runtime is sequential, not thread-shared.

Both controllers have exactly the same observation interface. The frozen LQR
uses only its first six measured coordinates. The conditional LQR uses the full
vector. Torque estimates are an independent, causal filter driven solely by
clipped command history and known delay/time constants from zero initial torque.
They never read mechanical truth or physical torque. In this exact assumed
actuator model they equal the physical filter state; this is not a torque sensor
or a robust estimator under unknown hardware dynamics.

Noise is sampled once at reset and once after each completed control interval.
Repeated reads do not draw again. Body angle/gyro use separate
`SeedSequence(seed).spawn(2)` PCG64 streams. Substeps, controller choice and
linearization cannot consume a rollout's stream. Matched seed/tick pairs thus
have identical noise; shorter failed rollouts share the same prefix.

## Timing and integration

At submission `t_k`, clip the action and schedule it for `t_k + delay`, with no
extra queue step. Split integration exactly at each arrival, so a 3 ms delay
arrives halfway through the second 2 ms control interval. An arrival exactly at
an interval end changes the next interval only. Comparisons allow 1e-12 s for
floating-point timestamp arithmetic; delay is never rounded to control ticks.

For each pair torque, with constant delivered command on an interval:

\[
\dot{\tau}=(u_d-\tau)/T,\qquad
\tau(t+h)=u_d+(\tau(t)-u_d)e^{-h/T}.
\]

The exact interval mean is
`u_d + (tau0-u_d)*(T/h)*(1-exp(-h/T))`. The runtime computes this mean, endpoint
and torque-squared integral analytically, with `expm1` for small arguments.
For zero T, torque changes instantaneously when transport delivers the command.
Clipped command and initial torque imply bounded endpoints/means; MuJoCo also
enforces its original physical caps.

MuJoCo RK4 integrates the original mechanics with that constant mean on
substeps no longer than 0.25 ms. This is an explicit approximation to continuous
torque/mechanics coupling, not an exact coupled solution. The torque impulse is
exact per segment, and refinement tests quantify mechanical convergence.
With delay and both lag constants zero, the runtime uses the exact original
2 ms held-control `mj_step` path, preserving bitwise nominal mechanics.

Primary source for the first-order filter and exponential update:
[MuJoCo 3.3.7 stateful actuators](https://mujoco.readthedocs.io/en/3.3.7/computation/index.html#stateful-actuators).
The lag here is external to MuJoCo's stateless torque motors to preserve the
nominal MJCF and expose exact causal reconstruction.

## Frozen-first experiment and conditional design

```sh
.venv/bin/python -m sim.run_augmented --config sim/configs/assumed_actuator_noise.json --out /private/tmp/wbr-actuator-NEW --jobs 4
.venv/bin/python .github/run_unittest.py sim/tests
```

Output must be a new directory outside the repository. The runner first verifies
the baseline synthesis against the committed frozen matrix, then **uses that
matrix**, never a gain recomputed for the augmented plant. The original Mac
matrix exactly matched the archived nominal K. Across BLAS/platforms the
verification permits only the predeclared small numeric tolerance; the used
matrix/hash remains fixed.

All 60 cases (four delays × five seeds × balance/push/zero-control) run first.
`--jobs` bounds the number of case processes (default 4; use 1 for serial).
Each spawned process creates its own runtime and noise streams and writes only
its assigned case directory. The parent aggregates in declared seed/scenario
order, preserving the serial CSV/JSON bytes, paths and gain hashes. Regimes
finish in delay order; the entire frozen phase finishes and is saved before any
conditional synthesis or rollout. Parallelism does not change substeps or truth/
interval capture. Short synthetic-fixture tests compare every artifact byte
between serial and four-process execution; they are not full-protocol results.
Only an observed FAIL triggers `augmented_lqr.synthesize_augmented`. It
finite-differences `AugmentedRuntime.transition_for_linearization`, the actual
same delayed/lagged substep map, using the augmented observation ordering.
Restored prior commands receive their real negative submission timestamps.
The DARE cost retains nominal six-state Q and command R, scaled by 2 ms; extra
torque/history states get zero cost. No weight, noise or threshold search occurs.
The command penalty is explicitly on issued command, not realized lagged torque.

For `z[k+1]=Az[k]+Bu[k]`, `u=-Kz`, the gain is
`K=(R+B.T@P@B)^(-1) B.T@P@A`. The runner records K/byte hash, A/B, Q/R, P,
Riccati residual, controllability singular values/rank/condition number and
open/frozen/augmented sampled poles. Reference:
[SciPy discrete algebraic Riccati equation](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.linalg.solve_discrete_are.html).
These are local, unsaturated, known-parameter conditions, not global guarantees.

Conditional design repeats all 60 cases with the same noise seeds and limits.
True states determine the original acceptance/recovery criteria; error integrals
and physical torque effort use actual substep dt. CSVs separate control/measurement
samples from integration intervals; push impulse is accumulated from actual dt.
The unchanged nominal final-window/recovery checks occur at control samples.
No acceptance claim about between-sample threshold crossings is added.

`result.json` uses `status=COMPLETE` for a complete experiment; `acceptance` and
every phase/regime/case carry separate PASS/FAIL labels. CLI exit 0 means all
required experiments and reports were retained, even when individual regimes
fail. Exit 1 means an incomplete/error run; `error.txt` and partial files remain.
There is no automatic retry, overwrite, acceptance relaxation, or failed-run
cleanup. Artifacts include configs, nominal/conditional designs, raw CSVs,
per-case JSON, source/package provenance and checksums. All large outputs stay
outside git.
