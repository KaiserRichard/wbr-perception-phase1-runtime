# Separate planar five-bar scaffold

This is an **ASSUMED research model**, separate from `sim/planar.py`, the
delay-aware LQR, and PPO v2. It consumes the existing read-only
`source_geometry_inventory_unused` dimensions. It loads and steps in MuJoCo;
quick tests check geometry, Jacobians, XML, reactions and fixed-length mappings.
It has no policy, hardware interface, motor calibration or measured dynamics.

The pinned reference is [DM-jump VMC_calc.c at
6855ef8](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/VMC/VMC_calc.c),
by Trần Nguyên Bình, copyright 2024–2026, MIT. `LICENSE` preserves the complete
upstream notice; `PROVENANCE.json` records commit and source hashes. Geometry is
implemented using circle intersection and implicit differentiation. The optional
parity test reads the existing compiled upstream C library without rebuilding it.
No gain schedule is implemented, imported or modified here.

## Coordinates and assembly branches

All lengths are metres, angles radians, forces newtons and torques newton metres.
Source body coordinates $(u,v)$ use $A=(0,0)$, $E=(l_5,0)$ and chassis midpoint
$O=(l_5/2,0)$. At upright body pitch, $u$ points world $+x$ and $v$ points world
$-z$. Positive angles turn $u$ toward $v$, physically about world $+y$.

| Symbol | Meaning | Value or convention |
|---|---|---|
| $l_1,l_4$ | $AB,ED$ proximal links | 0.075 m, SOURCE-SUPPORTED |
| $l_2,l_3$ | $BC,DC$ distal links | 0.14 m, SOURCE-SUPPORTED |
| $l_5$ | Motor separation $AE$ | 0.08 m, SOURCE-SUPPORTED |
| $q_1,q_4$ | Motor angles relative to body $+u$ | MuJoCo `motor_A`, `motor_E` |
| $β$ | Angle of $O\rightarrow C$ from $+u$ | Pinned source `phi0` |
| $L$ | Virtual length $\lVert C-O\rVert$ | Nominal 0.16 m, ASSUMED |
| $θ$ | Absolute axle-to-hip angle from world $+z$ toward $+x$ | Existing reduced model leg angle |
| $φ$ | Absolute body pitch about world $+y$ | Existing reduced model body angle |

Forward kinematics intersects the circles about knees $B,D$. `branch=+1`
places $C$ to the left of directed $B\rightarrow D$ in $(u,v)$ coordinates;
it agrees with the pinned positive-square-root solution in the tested workspace.
`branch=-1` selects the other intersection. Coincident knees, tangent or
unreachable circles, zero virtual length and singular Jacobians raise
`GeometryError`; there is no automatic branch switch or singularity clamp.

Inverse kinematics uses independently declared elbow signs. The default
`elbows=(+1,-1)` is the outward standing assembly:
$q_1=\operatorname{atan2}(C_v,C_u)+\arccos(c_A)$ and
$q_4=\operatorname{atan2}(C_v,C_u-l_5)-\arccos(c_E)$, with each cosine
from the law of cosines. The requested closure branch is checked afterward.
The model and local finite-difference projection use this standing branch;
their valid workspace does not include angle wrapping or branch transitions.

The world/body mapping is

$$
\beta=\theta-\phi+\frac{\pi}{2},\qquad
\begin{bmatrix}x_O\\z_O\end{bmatrix}
=\begin{bmatrix}x_C+L\sin\theta\\r+L\cos\theta\end{bmatrix}.
$$

For the source right-leg convention with `Pitch` $=\phi$, its `theta` is
$\pi/2-\phi-\beta=-\theta$. The source left-leg code negates IMU pitch
first; it is not a second independent leg in this aggregate planar model.
No encoder zeros or hardware left/right motor signs are inferred.

## Virtual model control and reactions

Let $q=[q_1,q_4]^T$, $c=C-O$ and $J_C=\partial C/\partial q$.
Differentiating the two circle constraints gives

$$
\begin{bmatrix}(C-B)^T\\(C-D)^T\end{bmatrix}J_C
=\begin{bmatrix}(C-B)^T B'&0\\0&(C-D)^T D'\end{bmatrix}.
$$

The virtual Jacobian and torque mapping are

$$
J=\frac{\partial(L,\beta)}{\partial q}
=\begin{bmatrix}c_u/L&c_v/L\\-c_v/L^2&c_u/L^2\end{bmatrix}J_C,
\qquad
\tau=J^T\begin{bmatrix}F_L\\T_\beta\end{bmatrix}.
$$

Thus $\tau^T\dot q=F_L\dot L+T_\beta\dot\beta$.
Positive $F_L$ extends the leg; positive $T_\beta$ increases $\beta$.
The endpoint force is $f_C=F_L e_r+(T_\beta/L)e_t$, where
$e_r=[\cos\beta,\sin\beta]^T$ and
$e_t=[-\sin\beta,\cos\beta]^T$.
For quasistatic massless-link wrench transfer, the chassis receives $-f_C$
and moment $-T_\beta$ about $O$. The **direct stator moment** is
$-(\tau_1+\tau_4)$; separated pin forces also contribute moment, so the
direct stator moment alone is not the complete chassis wrench. Massive-link
inertial and gravity loads require the dynamics model.

Positive reduced hip input $T_h$ does work
$T_h(\dot\phi-\dot\theta)$. Since
$\dot\beta=\dot\theta-\dot\phi$, `controls` uses $T_\beta=-T_h$.
MuJoCo motors apply hinge torques between each upper link and the chassis;
their reactions are already included. Do not add `wrench` reactions again.
At fixed length the mapped generalized hip force is exactly
$[0,-T_h,+T_h]^T$ in $(x,\theta,\phi)$ coordinates.

Worked example: $q=[2.3,0.8]$ gives $L=0.16116486$ m,
$\beta=1.55602052$ rad and approximately

$$
J=\begin{bmatrix}-0.04920833&0.04895329\\0.35393572&0.35655912\end{bmatrix}.
$$

For $F_L=30$ N and $T_\beta=0.2$ N m,
$\tau=[-1.4054628,1.5399105]^T$ N m. Direct stator moment is about
$-0.13445$ N m; the total transferred chassis moment about $O$ is
$-0.2$ N m. The quick suite compares the mapping with the pinned C reference
when `WBR_FIVEBAR_C_REFERENCE` names a prebuilt library directory.

## MuJoCo assumptions and the reduced-model comparison

The tree has independent chassis $x,z,\phi$, four link hinges and axle $x$:
eight tree coordinates. Two ankle-to-axle `connect` equalities impose four
independent planar constraints, leaving $(x,\theta,\phi,L)$. The two redundant
out-of-plane equality rows have zero Jacobian. Axle height stays $r$; collision
is disabled. This preserves the existing ideal rolling/no-slip assumption,
without pretending to model ground contact or jumping.

One mechanism represents the symmetric aggregate pair. Body/wheel masses,
body COM/inertia, wheel radius and rolling armature are reused from the
read-only reduced configuration. The 0.5 kg equivalent leg mass is split
equally among four assumed uniform rods with 6 mm inertial radius. These are
aggregate link masses, and each simulated hip motor torque is the corresponding
aggregate across both sides. Link COMs/inertias are **not matched** to the
existing rigid equivalent leg or measured hardware. No independent leg, roll,
yaw, foot contact, actuator delay/lag, noise, saturation or controller is added.
Unbounded actuators expose the mapping; motor capability remains unknown.

The wheel bearing is assumed mounted on the distal left link. Ideal rolling
eliminates wheel spin, preserving armature $I_w/r^2$ and using the relative
rotation tendon

$$
\psi=x_C/r-(\phi+q_1+q_B).
$$

Here $q_B$ is the relative knee hinge angle. Wheel torque therefore produces
$T_w/r$ axle force and a reaction $-T_w$ on the **physical distal link**.
The reduced model instead reacts wheel torque on its rigid virtual leg.
Even at fixed length, distal-link angle need not track virtual-leg angle.
This mounting choice is an assumption, not recovered CAD provenance.

`python -m sim.fivebar.compare` performs only a quick matrix snapshot.
For $(x,\theta,\phi,L)=(0,0.08,-0.05,0.16)$, the executed snapshot shows:

- Hip position agrees with the reduced model to below $10^{-15}$ m.
- Virtual hip input map agrees within $10^{-9}$.
- Wheel input map is approximately $[16.58375,-0.83298,-0.16702]^T$,
  versus reduced $[16.58375,-1,0]^T$; first component has units $1/\mathrm m$.
- The angular mass-matrix entry $H_{\theta\theta}$ is approximately
  $0.05653175$ versus $0.05560000$ kg m$^2$.

These establish fixed-length **kinematic and virtual-hip mapping agreement**,
and demonstrate why full dynamics equality is not established. They do not
justify replacing the reduced model or evaluating trained policies here.

## Commands and fixed-length study

Quick checks, with single-thread BLAS and no dependency changes:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
"$PY" -m sim.fivebar.model
WBR_FIVEBAR_C_REFERENCE=/private/tmp/wbr-parity-c-reference-20261020-01 \
  "$PY" -m unittest discover -s sim/fivebar/tests -v
"$PY" -m sim.fivebar.compare
```

Without the optional prebuilt C path, the C test explicitly skips. There is no
compiler/dependency installation or modification of that prior build. The XML
test includes just one physical integration step, not a stability experiment.

**Executed on 2026-10-21 after owner resumption:** the fixed-length dynamics
comparison uses the assumed link mass matrix and bias from MuJoCo, with analytic
loop/length elimination and local finite-difference coordinate derivatives.
For $q_{\rm tree}=f(q)$, $T=\partial f/\partial q$, it integrates

$$
(T^T M T)\ddot q=T^T\left(Q-b-M\dot T\dot q\right).
$$

An ideal length reaction does no allowed virtual work and is eliminated. This
is a constrained comparison, not a physical length servo or soft-XML simulation.
The unit test checks nonzero-velocity energy rate against actuator power,
including the passive-joint curvature term. The executed study ran all nine
combinations of timestep and projection epsilon, preserving physical
parameters and pulse inputs; output reports differences without a parity PASS.
It stops explicitly on 45-degree tilt, workspace exit or numeric failure.

```sh
# Recorded child command; the external wrapper set nice=10, the single-thread
# environment above, and Popen.wait(timeout=600). This output now exists.
"$PY" -m sim.fivebar.compare --run-dynamics \
  --duration 5 --timesteps .001 .0005 .00025 --epsilons 1e-5 3e-6 1e-6 \
  --output /Users/quockaiser/wbr-evidence-archive/sim-fivebar-dynamics-20261021-01/fixed-length-dynamics.json
```

At source commit `140a11b45e035190d89f4af0905b70975dce9f7c`, the one study
exited 0 in **150.709 wall seconds**. Independent parsing confirmed nine unique
timestep/epsilon pairs, finite saved numeric values, and consistent status,
step count and simulated time. Every case reported `45_degree_stop`, with no
failure message: the **reduced model's leg angle** crossed the threshold first.
The 1 ms and 0.5 ms cases stopped at 0.296 s; the 0.25 ms cases at 0.29575 s.
These are short open-loop falls, **not five seconds of valid dynamics or
balance tests**. Inputs were the existing 0.1 s wheel/hip pulse
`[0.02, -0.05]` N m followed by zero, from
`[x, theta, phi, xdot, thetadot, phidot] = [0, 0.02, -0.015, 0, 0, 0]`.

At 0.25 ms and epsilon $10^{-6}$, maximum absolute five-bar/reduced differences
over the sampled interval were
`[0.00341824 m, 0.0625922 rad, 0.0297757 rad, 0.0315746 m/s,
0.479236 rad/s, 0.298670 rad/s]`. Across epsilon choices at any fixed timestep,
the largest five-bar terminal leg-angle spread was $5.66\times10^{-8}$ rad
and leg-rate spread $1.13\times10^{-6}$ rad/s. Halving 1 ms to 0.5 ms compared
the same 0.296 s endpoint; terminal leg-angle changes across both models and
all epsilons were at most $6.19\times10^{-10}$ rad. Halving again changed the
stop time by 0.25 ms, so those endpoint differences also contain time offset.
No common-time trajectories were saved, convergence order estimated, tolerance
invented, or dynamics-equivalence PASS assigned.

The differences persist under these refinements and are consistent with the
unmatched **ASSUMED link mass distribution and distal-link wheel reaction**
described above; this run does not isolate their separate contributions.
Kinematic and virtual-hip mapping agreement does not establish matched
dynamics. The earlier 120 s attempt was resource-limited with no final JSON,
not an established numerical failure. Per-case facts, exact execution receipts
and limitations are in the [one-page review](../../ops/worklog/reviews/2026-10-21-fivebar-dynamics.md).

Long free-length XML simulations, closure/solver refinement, length-servo
behavior, full dynamics equivalence analysis, matched mass identification,
contacts and physical validation remain unrun. The fixed-length projected
study does not validate full five-bar closed-loop control, contact/jumping or
policy transfer. Pi execution is also unverified.

## Prescribed-length ramp (22 October 2026)

`python -m sim.fivebar.ramp --schedule <accepted-schedule.json> --out <new-directory>`
uses the accepted fitted 2 ms reduced-model gain schedule while prescribing
$L(t)$ from 0.12 m to 0.20 m: hold for 2 s, use an 8 s C2 quintic ramp, then
hold 5 s. Initial state, noise, 5 ms lag, 2 ms command delay, and 2/4 N m caps
come from the unchanged reference config. Feedback is noisy body pitch/rate,
ideal other six-state entries, exact prescribed $L$, and the controller's own
causal nominal command-only torque observer. The schedule is transferred from
the reduced fitted family to different **ASSUMED** nonlinear five-bar mechanics.

The tree is built once. At each RK4 stage the four-coordinate projection uses
the native MuJoCo mass, bias and actuator forces. The ideal extension reaction
balances the fourth generalized equation and its work is recorded; this is a
prescribed coordinate, **not a physical extension servo**. Link properties and
gains are not changed. The default mechanics step is 1 ms (two substeps per
2 ms controller tick); saved stage closures, extension force/work, states,
commands, torques and length derivatives support review. Motor feasibility is
unknown. The run is an assumed-model transfer experiment, not a hardware claim.

Focused checks: `python -m unittest sim.fivebar.tests.test_ramp -v` covers the
profile and derivatives, constant-length equality with `FixedLength`, ideal
four-coordinate force balance, equal-duration timestep refinement, closure,
cached sensor noise and causal clipped-command feedback. Run outputs and exact
receipts are stored outside Git under the dated `sim-control-margins` evidence
archive. At source `7aeb34b`, seed 0 exited 0 after 235.449 s and completed
15,000 mechanics steps; all eight acceptance checks passed. Peak displacement
was 0.029149 m, peak tilt 8.00734°, sampled closure error $2.30\times10^{-16}$ m,
peak ideal extension reaction 28.639 N and signed/absolute work 1.762 J. Peak
physical wheel/hip torque was 0.577/0.847 N m, peak clipped command 1.750/2.337
N m, with no saturation. Recovery was already inside tolerance at ramp end
(reported $-1.8\times10^{-15}$ s from floating-point subtraction). The full
trace and supervisor receipts are in
`/Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/fivebar-ramp/run-03/`
and its sibling `run-03-supervisor.json`. Run-02 retains the completed mechanics
trace whose metrics initially failed serialization; the native-boolean fix and
7/7 rerun suite are documented in the session note. This single seed and
assumed-model result do not establish a physical extension actuator, motor
feasibility, five-bar hardware performance or general stability.

## Local linear comparison (21 October 2026)

`python -m sim.fivebar.linearize --out <fresh-directory>` compares upright
continuous derivatives at L=0.12, 0.16, 0.20, 0.21 m, then applies each fresh
**reduced-model** `sim.lqr.synthesize` DARE gain with `u=-Kx`. Both continuous
plants use matched zero-order hold at 2 ms; the reduced actual held-control
MuJoCo RK4 step/DARE record stays separate. No fivebar gains or rollouts are
generated. Use the single-thread environment and interpreter above, with
`nice -n 10`; the same interpreter runs `-m unittest sim.fivebar.tests.test_linearize -v`.

`config_at_length` preserves masses and scales only the equivalent rigid-leg
COM and inertia. Fivebar link geometry and four equal rod masses/inertias retain
their existing assumptions. The output separates generalized torque map G,
mass M, and actual acceleration input Jacobian `B[3:]=solve(M,G)`; the earlier
17% wheel-reaction observation is **not** a 17% full B-matrix discrepancy.

The executed comparison accepts all four lengths: fivebar pole radii are
0.997674099, 0.997549295, 0.997490806, 0.997663634 (local sampled stability only).
JSON retains all matrices, six poles per model, radial margin, decay time,
equilibrium residuals and separate projection/state/input epsilon refinements.
Geometry or equilibrium failures remain explicit; no bias is subtracted.
Raw relative/max matrix norms mix units and depend on coordinate scaling.
`report.md`, `metrics.csv` and `acceleration-inputs.csv` accompany the JSON.
See the [worker run note](../../ops/worklog/sessions/2026-10-21-fivebar-linear-worker.md)
for exact commands, source and evidence paths. No nonlinear/hardware transfer claim.
