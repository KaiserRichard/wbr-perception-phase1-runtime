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

## Commands and deferred work

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

**Queued, not run during active training:** the following fixed-length dynamics
comparison uses the actual link mass matrix and bias from MuJoCo, with analytic
loop/length elimination and local finite-difference coordinate derivatives.
For $q_{\rm tree}=f(q)$, $T=\partial f/\partial q$, it integrates

$$
(T^T M T)\ddot q=T^T\left(Q-b-M\dot T\dot q\right).
$$

An ideal length reaction does no allowed virtual work and is eliminated. This
is a constrained comparison, not a physical length servo or soft-XML simulation.
The unit test checks nonzero-velocity energy rate against actuator power,
including the passive-joint curvature term. The queued study runs all nine
combinations of timestep and projection epsilon, preserving physical
parameters and pulse inputs; output reports differences without a parity PASS.
It stops explicitly on 45-degree tilt, workspace exit or numeric failure.

```sh
# Only after PPO ends, or on a separately provisioned Pi with MuJoCo.
# Use a new output path; the command refuses to overwrite evidence.
nice -n 10 "$PY" -m sim.fivebar.compare --run-dynamics \
  --duration 5 --timesteps .001 .0005 .00025 --epsilons 1e-5 3e-6 1e-6 \
  --output /private/tmp/wbr-overnight-20261020/A4/fixed-length-dynamics.json
```

Long free-length XML simulations, closure/solver refinement, length-servo
behavior, full dynamics equivalence analysis, matched mass identification,
contacts and physical validation remain unrun. The fixed-length projected
study does not replace those experiments. Pi execution is also unverified.
