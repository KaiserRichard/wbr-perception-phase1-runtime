# Assumed-model leg-length LQR study

**Restricted study, 2026-10-21:** source `90e6e509e1446d99ee1d3021bdc526d636b4558b`
(clean implementation) completed **36 fresh designs, four degree-3 fits and all
32 midpoint pole checks PASS**. Fitted pole radii 0.997434974361–0.997676790315,
margin 0.002323209685–0.002565025639, slowest decay time 0.778719–0.859878 s.
**400 nonlinear cases remain UNRUN by this worker**, pending conductor verification.
Preparation commit `2d37726` (adopted as `9c03426`) contained no executed restricted
study. The original 76-design, 0.12–0.30 m run remains unchanged in
`~/wbr-evidence-archive/sim-gain-sweep-20261021-01`; its historical report is
`ops/worklog/reviews/2026-10-21-gain-sweep.md`. Those coefficients are not
reinterpreted or accepted by the restricted runner.

This separate experiment recomputes linear quadratic regulator (LQR) gains from
our assumed six-state planar MuJoCo model plus its causal actuator delay/lag
states. It does not import `sim.parity`, read DM-jump polynomial coefficients,
complete the owner's gain exercise, alter the existing configs, or affect PPO.
The input config includes the previous assumed-model frozen gain as historical
metadata; that gain is never used as this study's controller or fitting target.

## Assumed family and fresh synthesis

The study domain is $L \in [0.12,0.20]$ m. At each length, a deep copy of the reference
config changes only leg length, leg center of mass (COM), and COM inertia:

$$
s=L/L_0,\qquad c_\ell(L)=s c_{\ell,0},\qquad
I_\ell(L)=s^2 I_{\ell,0}.
$$

Leg mass is fixed. This is a geometrically scaled equivalent rigid leg, since
$I=\int r^2\,dm$ scales by $s^2$ for fixed mass and scaled mass distribution.
It is an explicit modeling assumption, not measured extension kinematics or a
five-bar mechanism. For example, $L_0=0.16$ m, $c_{\ell,0}=0.08$ m,
$I_{\ell,0}=0.0012$ kg m² imply at $L=0.20$ m that $s=1.25$,
$c_\ell=0.10$ m, and $I_\ell=0.001875$ kg m². These are parameter arithmetic,
not a simulation result. Body/wheel parameters, masses, controller weights,
torque caps, sample period, and protocol remain identical to the reference.

Default synthesis grid: nine lengths, 0.12, 0.13, …, 0.20 m. Default delay regimes:
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

## Why 0.12–0.20 m: geometry, not validated motion workspace

Pinned [geometry provenance](../fivebar/PROVENANCE.json) gives symmetric proximal
rods $a=0.075$ m, distal rods $b=0.14$ m and pin spacing $2h=0.08$ m.
[Existing kinematics](../fivebar/geometry.py) uses pins $A=(0,0)$, $E=(2h,0)$
and ankle $C=(h+L\cos\beta,L\sin\beta)$. The standing assembly has elbow
signs $(+1,-1)$ and closure branch $+1$. In [the five-bar model](../fivebar/model.py),
$\beta=\pi/2+\theta-\phi$; the unchanged start is leg $+8^\circ$, body
$-6^\circ$, so $\beta=104^\circ$, while upright is $90^\circ$.

Distances from the ankle to the pins satisfy

$$
r_{A,E}^2=L^2+h^2\pm2hL\cos\beta,\qquad |b-a|<r_{A,E}<a+b.
$$

Strict inequalities exclude folded/straight serial chains. The farther-pin
extension boundary on a fixed ray is

$$
L_{\mathrm{ext}}(\beta)=\sqrt{(a+b)^2-h^2\sin^2\beta}-h|\cos\beta|.
$$

For example, upright gives $\sqrt{0.215^2-0.04^2}=0.211246302$ m;
the declared start gives $0.201790951$ m. Thus 0.21 m is feasible upright but
unreachable at the initial tilt. At 0.20 m, length margins to these singular
boundaries are 11.246302 mm and 1.790951 mm respectively; the smaller direct
pin-radius margin is 1.761283 mm. The lower study limit 0.12 m is a conservative
research choice, not a measured minimum extension. Exact singular endpoints
are excluded.

The interval certificate in `geometry.py` also checks the outward closure.
Since $L>h|\cos\beta|$, both pin radii increase across the interval, so their
endpoint bounds suffice. Set $\alpha_A=\arg(C-A)$, $\alpha_E=\arg(C-E)$.
For $b>a$, each distal deviation satisfies
$0<\gamma\leq\arcsin(a/b)$. Distal directions are
$\alpha_A-\gamma_A$ and $\alpha_E+\gamma_E$; their separation lies between
$\min\alpha_E-\max\alpha_A$ and
$\max\alpha_E-\min\alpha_A+2\arcsin(a/b)$.
Endpoint bounds give [0.394791, 1.774208] rad upright and
[0.384199, 1.759797] rad at the start, strictly within $(0,\pi)$, excluding
parallel distal links. Existing inverse kinematics (IK), forward reconstruction
and Cartesian/virtual Jacobians are evaluated at every training length,
midpoint and evaluation length; determinants and singular values are saved.
Tests additionally compare analytic Jacobians to finite differences.

This certifies two **fixed posture rays** only. Hardware joint limits are
UNKNOWN; intermediate or disturbed poses, collisions and the motion workspace
are unvalidated. Restricting length does not make the reduced rigid-leg family
five-bar physics. `config_at_length` is a pure positive-length parameter
transform, permitting hypothetical lengths for separate model comparisons
(including g's 0.21 m point and geometry rejection cases). Study sweep, fit,
linear-check and evaluation enforce the restricted domain separately; there
is no silent clamp or extrapolation.

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

For a synthetic scalar entry with coefficients $(2,-1,0.5)$, at $L=0.14$ m
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

## Fresh midpoint checks and commands

`linear-check` derives **every interval midpoint from the actual saved fit's
training grid**, separately for every saved delay. The default nine samples
produce .125/.135/.145/.155/.165/.175/.185/.195 m × four delays = 32 checks.
For each, `synthesize_augmented` calls the existing
`sim.augmented_lqr.linearize` on the actual augmented runtime; no interpolated
A/B matrices enter the check. Fresh nominal/exact DARE records are retained as
references. The fitted gain is evaluated only for this offline research study;
this is not a solution or alternative implementation of the owner-only
`sim.parity.student.gain_schedule` exercise.

For $A_d-B_d\widehat K$, output includes every complex eigenvalue and paired
right eigenvector in the recorded state order, $\rho=\max_i|\lambda_i|$,
strict $\rho<1$ status, margin $1-\rho$ and
$\tau=-\Delta t/\log\rho$ when $0<\rho<1$ (otherwise null).
Mixed-unit vector components do not identify a physical mode. Gain-entry errors
are secondary diagnostics. Exceptions and unstable checks are retained without
degree/Q/R retuning; an unstable fitted case does not abort the remaining checks.
These are sampled local results, not continuum or nonlinear stability proofs.

The exact executed commands follow. Interpreter used read-only, one CPU thread;
no dependency installation. **First three paths already exist**; use new
exclusive paths to repeat them. The last command is the fixed 400-case handoff
for the conductor after independent verification, **not executed by this worker**.

```sh
cd /Users/quockaiser/.codex/worktrees/reachable-gain-study/wbr-lab-ops
WBR_GAIN_PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
WBR_GAIN_OUT=/Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1

# EXECUTED: nine lengths × four delays = 36 fresh designs (6.56 s).
nice -n 10 "$WBR_GAIN_PY" -m sim.gain_schedule sweep \
  --config sim/configs/assumed_actuator_noise.json \
  --lengths .12 .13 .14 .15 .16 .17 .18 .19 .20 \
  --delays .002 .003 .004 .005 --out "$WBR_GAIN_OUT/sweep-01"

# EXECUTED: four unchanged degree-3 Chebyshev fits (0.41 s).
nice -n 10 "$WBR_GAIN_PY" -m sim.gain_schedule fit \
  --sweep "$WBR_GAIN_OUT/sweep-01/sweep.json" --degree 3 \
  --out "$WBR_GAIN_OUT/fit-01"

# EXECUTED: 32 fresh off-grid local pole checks (7.75 s).
nice -n 10 "$WBR_GAIN_PY" -m sim.gain_schedule linear-check \
  --schedule "$WBR_GAIN_OUT/fit-01/schedule.json" \
  --out "$WBR_GAIN_OUT/midpoints-01"

# NOT RUN: only conductor launches after independent verification.
nice -n 10 "$WBR_GAIN_PY" -m sim.gain_schedule evaluate \
  --schedule "$WBR_GAIN_OUT/fit-01/schedule.json" \
  --lengths .12 .135 .16 .185 .20 --seeds 0 1 2 3 4 \
  --out "$WBR_GAIN_OUT/evaluation-01"

# Targeted tests (fixtures/geometry, no rollouts).
"$WBR_GAIN_PY" -m unittest discover -s sim/gain_schedule/tests -v
```

Evaluation keeps **400 identities**: five lengths × four delays × two controllers
(fresh DARE and fitted polynomial) × five seeds × balance/push. The endpoints
and .16 m are training points; .135/.185 m are off-grid. It recomputes exact
DARE gains and linearizations at all five lengths. Execution is serial with no
training, rendering, shortened episodes or relaxed criteria. Partial output is
preserved; the runner refuses existing directories and makes no unsafe resume
assumption from incomplete records.

Both controllers use `-K @ observation.vector()` on separate identical model
instances and matched seeds, through `sim.augmented_eval.evaluate`. Each case
holds its leg length constant throughout the unchanged 10 s protocol, including
the full 6 N, 0.15 s push at 3 s, initial tilts, 2/4 Nm caps, final settling
window and recovery deadline. It retains `control.csv`, `intervals.csv`, and
`metrics.json`, even for failed cases. This study has no varying-length dynamics
or scheduling-rate experiment, no open-loop negative-control phase, no
uncertainty analysis, and no hardware validation.

`sweep.json` contains the reference configs and actual sample matrices;
`geometry.json` retains the posture bounds and sampled IK/Jacobians;
per-length files retain the derived config/MJCF and full synthesis records.
`schedule.json` contains the fitted coefficients, diagnostics, runtime contexts,
and source sweep checksum. `linear_checks.json` indexes all midpoint artifacts
and failures. `evaluation.json` retains case identities, failures,
local checks, and artifact paths. Configs and schedule snapshots accompany runs.
The study identifier `reachable-posture-rays-0.12-0.20-v1` distinguishes this
new scope while the assumed-model family is unchanged. Source commit/dirty
status/package receipts are saved; no active evidence is edited.

Exit 0 / `status=COMPLETE` means the requested artifacts were produced.
Nonlinear `acceptance` and `polynomial_local_acceptance` separately retain
PASS/FAIL; a fully executed failing experiment still exits 0. Exceptions produce
exit 1 and `error.txt`, with earlier partial results retained. Check both
completion and acceptance. Low fitting residuals, synthetic tests, sampled
stable poles, or even successful fixed-length cases do not establish stability
for every length, a changing-length robot, or the real hardware.
