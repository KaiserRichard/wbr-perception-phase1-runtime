# Assumed-model leg-length LQR study

**Implementation and synthetic tests only as of 2026-10-20. Real gain synthesis,
fitting of real gains, pole measurements, and nonlinear evaluations are pending
heavy jobs. No computed stability result is claimed.** Mac execution of those
jobs must wait until active PPO v2 ends. A reachable Pi may run them only in its
own assigned checkout/environment. This runner does not launch jobs remotely or
modify a job queue.

This separate experiment recomputes linear quadratic regulator (LQR) gains from
our assumed six-state planar MuJoCo model plus its causal actuator delay/lag
states. It does not import `sim.parity`, read DM-jump polynomial coefficients,
complete the owner's gain exercise, alter the existing configs, or affect PPO.
The input config includes the previous assumed-model frozen gain as historical
metadata; that gain is never used as this study's controller or fitting target.

## Assumed family and fresh synthesis

The domain is $L \in [0.12,0.30]$ m. At each length, a deep copy of the reference
config changes only leg length, leg center of mass (COM), and COM inertia:

$$
s=L/L_0,\qquad c_\ell(L)=s c_{\ell,0},\qquad
I_\ell(L)=s^2 I_{\ell,0}.
$$

Leg mass is fixed. This is a geometrically scaled equivalent rigid leg, since
$I=\int r^2\,dm$ scales by $s^2$ for fixed mass and scaled mass distribution.
It is an explicit modeling assumption, not measured extension kinematics or a
five-bar mechanism. For example, $L_0=0.16$ m, $c_{\ell,0}=0.08$ m,
$I_{\ell,0}=0.0012$ kg m² imply at $L=0.24$ m that $s=1.5$,
$c_\ell=0.12$ m, and $I_\ell=0.0027$ kg m². These are parameter arithmetic,
not a simulation result. Body/wheel parameters, masses, controller weights,
torque caps, sample period, and protocol remain identical to the reference.

Default synthesis grid: 19 lengths, 0.12, 0.13, …, 0.30 m. Default delay regimes:
2, 3, 4, and 5 ms, with the existing two 5 ms motor time constants, 0.25 ms
integration substeps, and body angle/gyro noise. Each length first gets a fresh
nominal design via `sim.lqr.synthesize`; its matrix is only the diagnostic
reference supplied to `sim.augmented_lqr.synthesize_augmented`. The latter
finite-differences the actual delayed/lagged transition and solves a fresh
discrete algebraic Riccati equation (DARE):

$$
z_{k+1}=A(L,d)z_k+B(L,d)u_k,\quad
K=(R_d+B^\top P B)^{-1}B^\top P A,\quad u_k=-Kz_k.
$$

Here $Q_d=\Delta t\,\mathrm{diag}(Q_6,0,\ldots,0)$ and
$R_d=\Delta t R$ use the unchanged reference weights. Extra states are two
causally reconstructed torques and clipped command history, not privileged
physical observations. Exact known delay/lag and zero initial torque remain
assumptions. State dimensions at 2/3/4/5 ms are 10/12/12/14; **each delay gets
its own matrix polynomial with explicit state/input ordering**. There is no
interpolation between delays, and the 3 and 4 ms designs remain separate.

The reused synthesis routine calls its original design “CONDITIONAL” in its
record; this runner adds a `study` field identifying the separately requested
length experiment. It does not rerun or rewrite the earlier frozen-first
experiment. It records fresh local poles and Riccati residuals only when run.
An unsynthesizable length/delay retains its traceback and makes the sweep
incomplete; the fitter refuses incomplete sweeps.

## Polynomial basis, conditioning, and bounds

For every gain entry, use an unweighted least-squares polynomial of degree 3
by default. Let

$$
x=\frac{2L-L_{\min}-L_{\max}}{L_{\max}-L_{\min}},\qquad
\widehat K_{ab}(L)=\sum_{j=0}^{p}C_{jab}T_j(x),
$$

where $T_0=1$, $T_1=x$, and $T_{j+1}=2xT_j-T_{j-1}$.
`coefficients[j][actuator][state]` stores increasing **Chebyshev** degree,
not powers of metres. `numpy.linalg.lstsq(..., rcond=None)` solves $VC=K$
with $V_{ij}=T_j(x_i)$; it does not form normal equations. Mapping metres to
$[-1,1]$ and using bounded basis functions avoids the poor scaling of direct
$1,L,L^2,\ldots$ columns. This improves numerical conditioning; it does not
guarantee a low approximation error or a stable controller.

For a synthetic scalar entry with coefficients $(2,-1,0.5)$, at $L=0.165$ m
we get $x=-0.5$, $T_2=-0.5$, and
$\widehat K=2+(-1)(-0.5)+0.5(-0.5)=2.25$.
This example is unrelated to either robot's gains.

Saved diagnostics include singular values, rank, 2-norm condition number,
the raw metre power-basis condition number for comparison, per-entry RMSE and
maximum absolute error, and a whole-matrix relative Frobenius residual.
The fit rejects duplicate/nonfinite samples, insufficient samples, absent
endpoints, mixed matrix ordering/shapes, rank loss, or condition number above
`1e8`. The raw power-basis condition is `null` if nonfinite; it is diagnostic
only. The default degree and cutoff are numerical design choices, not measured
controller acceptance thresholds. There is no automatic degree/weight tuning.

Scalar and vector queries both reject NaN, infinity, and lengths outside the
closed fitted interval. **No silent clamping or extrapolation is allowed.**
Endpoints are accepted. An error must not be interpreted as a fallback motor
command; this package is an offline simulation study.

## Commands and queued heavy work

From the assigned checkout, examples default to `python3`; set `WBR_GAIN_PY` to
an explicit interpreter when needed. Do not install into or change the active Mac
backend environment. On a Pi, point `WBR_GAIN_PY` to its own prepared environment.
Use a new output root for every attempt; old outputs are never overwritten. These
commands are **pending**, except the synthetic tests.

```sh
WBR_GAIN_PY="${WBR_GAIN_PY:-python3}"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export WBR_GAIN_OUT=/private/tmp/wbr-A3-gains-NEW

# HEAVY: queue until PPO ends on Mac; 19 lengths × 4 delay regimes = 76 designs.
nice -n 10 "$WBR_GAIN_PY" -m sim.gain_schedule sweep \
  --config sim/configs/assumed_actuator_noise.json \
  --delays 0.002 0.003 0.004 0.005 --out "$WBR_GAIN_OUT/sweep"

# Small, but depends on the unrun real sweep; fits one polynomial per delay.
"$WBR_GAIN_PY" -m sim.gain_schedule fit \
  --sweep "$WBR_GAIN_OUT/sweep/sweep.json" --degree 3 \
  --out "$WBR_GAIN_OUT/fit"

# HEAVY: queue; BOTH balance and push at FIVE lengths, with five matched seeds.
nice -n 10 "$WBR_GAIN_PY" -m sim.gain_schedule evaluate \
  --schedule "$WBR_GAIN_OUT/fit/schedule.json" \
  --lengths 0.12 0.165 0.21 0.255 0.30 --seeds 0 1 2 3 4 \
  --out "$WBR_GAIN_OUT/evaluation"

# Permitted quick check: synthetic fitting/config/runner fixtures only, <15 s.
"$WBR_GAIN_PY" -m unittest discover -s sim/gain_schedule/tests -v
```

Evaluation uses **400 full-protocol cases**: five lengths × four delays ×
two controllers (fresh DARE and fitted polynomial) × five seeds × balance/push.
At 0.165 and 0.255 m it tests lengths absent from the default fitting grid;
the endpoints and 0.21 m are in-grid checks. It recomputes exact DARE gains and
linearizations at all five lengths. The evaluator records fitted versus exact
gain errors and local spectral radii separately from nonlinear acceptance.
All jobs run serially; no training, parallel workers, rendering, shortened
episodes, or relaxed criteria are hidden in these commands.

Both controllers use `-K @ observation.vector()` on separate identical model
instances and matched seeds, through `sim.augmented_eval.evaluate`. Each case
holds its leg length constant throughout the unchanged 10 s protocol, including
the full 6 N, 0.15 s push at 3 s, initial tilts, 2/4 Nm caps, final settling
window and recovery deadline. It retains `control.csv`, `intervals.csv`, and
`metrics.json`, even for failed cases. This study has no varying-length dynamics
or scheduling-rate experiment, no open-loop negative-control phase, no
uncertainty analysis, and no hardware validation.

`sweep.json` contains the reference configs and actual sample matrices;
per-length files retain the derived config/MJCF and full synthesis records.
`schedule.json` contains the fitted coefficients, diagnostics, runtime contexts,
and source sweep checksum. `evaluation.json` retains case identities, failures,
local checks, and artifact paths. Configs and schedule snapshots accompany runs.
A short source commit/package receipt is saved; no active evidence is edited.

Exit 0 / `status=COMPLETE` means the requested artifacts were produced.
Nonlinear `acceptance` and `polynomial_local_acceptance` separately retain
PASS/FAIL; a fully executed failing experiment still exits 0. Exceptions produce
exit 1 and `error.txt`, with earlier partial results retained. Check both
completion and acceptance. Low fitting residuals, synthetic tests, sampled
stable poles, or even successful fixed-length cases do not establish stability
for every length, a changing-length robot, or the real hardware.
