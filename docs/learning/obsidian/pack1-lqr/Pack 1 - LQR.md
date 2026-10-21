---
title: "Pack 1 — LQR: from Bellman to our WBR"
aliases: [WBR LQR foundations]
tags: [wbr, control, optimal-control, lqr, bellman, mathematics]
created: 2026-10-21
status: learning-pack
next: "[[Pack 2 - RL to PPO]]"
---

# LQR — from Bellman to our WBR

**Illustrated revision — 21 October 2026.** Read the plates and their mathematical walkthroughs together.

**What you should be able to explain afterwards:** how geometry becomes dynamics, where $u=-Ks$ comes from,
what the Riccati equation solves, what a stability check does and does not prove,
and which gain matrix our robot simulation actually uses.

You already know embedded systems and some reinforcement learning (RL). This
pack develops the missing control mathematics; it does not assume prior mastery
of Linear Quadratic Regulation (LQR). Keep [[Toolkit]] beside you if needed.

## Reading map

1. [[#1. What is being controlled?|What is being controlled?]]
2. [[#2. From nonlinear dynamics to a sampled model|From nonlinear dynamics to a sampled model]]
3. [[#3. Specify the optimization problem|Specify the optimization problem]]
4. [[#4. Derive feedback using Bellman|Derive feedback using Bellman]]
5. [[#5. Work a scalar example by hand|Work a scalar example by hand]]
6. [[#6. What stability means|What stability means]]
7. [[#7. Continuous versus discrete LQR|Continuous versus discrete LQR]]
8. [[#8. Apply DARE to a cart-pole|Apply DARE to a cart-pole]]
9. [[#9. Read the real WBR simulation gains|Read the real WBR simulation gains]]
10. [[#10. Run the exercise|Run the exercise]]
11. [[#11. Questions, answers and the next experiment|Questions, answers and the next experiment]]

> [!important] Scope
> **SIMULATION / ASSUMED.** Our reduced WBR is an illustrative planar model,
> not an identified CAD digital twin. The cart-pole and scalar system below are
> teaching examples. None of these results authorizes deployment to the robot.

## 1. What is being controlled?

A balancing robot must move its support to manage the motion of an unstable
body. Correcting tilt alone is insufficient: it can remain upright while
travelling away from its desired position. We want **balance and settling**.

Our reduced model uses

$$
s=
\begin{bmatrix}
x & \theta & \phi & \dot x & \dot\theta & \dot\phi
\end{bmatrix}^{T},
\qquad
u=\begin{bmatrix}\tau_w & \tau_h\end{bmatrix}^{T}.
$$

| Symbol | Meaning | Unit |
| --- | --- | --- |
| $x$ | Horizontal axle displacement from target | m |
| $\theta$ | Equivalent leg pitch from upright, absolute | rad |
| $\phi$ | Body pitch from upright, absolute | rad |
| $\dot x,\dot\theta,\dot\phi$ | Corresponding velocities | m/s, rad/s, rad/s |
| $\tau_w$ | Aggregate wheel-pair torque | N m |
| $\tau_h$ | Aggregate virtual hip-pair torque | N m |

The simulator's hip joint angle is $\phi-\theta$, although the controller state
contains **absolute** body pitch $\phi$. Confusing those coordinates changes the
meaning of the gain columns. Aggregate pair torques are not per-motor commands.

![Coordinates, independent pitch angles and relative hip rotation](assets/01_coordinates_and_angles.png)

*Plate 01, supplied by the owner. Read panels A and C for the independent absolute angles. Panel B needs a caution: the relative arc is between the leg and body axes, although the nearby vertical ray can be mistaken for its starting ray. The text equation $q_h=\phi-\theta$ defines the angle; do not measure the pixel arc.*

For a stationary upright target, $s^\star=0$ and the ideal model has
$u^\star=0$. More generally use errors $e=s-s^\star$ and $v=u-u^\star$.
The feedback law then becomes $u=u^\star-Ke$.

> [!note] Must Know
> LQR needs a **state**, not just the angle visible in an animation. In the
> ideal derivation the state is available exactly. Actual controllers use noisy
> measurements or estimates; that extra problem is not solved by calculating $K$.

For the mechanical foundation, follow Sections 1.1–1.6 in order: coordinates →
COM geometry → velocities → energy → motor work → dynamics. Each plate is
embedded at the step it explains; enlarge it in Obsidian to read the details.

### 1.1 Read the drawing before reading a matrix

Use **$x$ for the scalar axle displacement** and **$s$ for the full state vector**.
This matches the supplied plates. A textbook may call its whole vector $x$;
that is another notation, not another physical coordinate. In this lesson
$q=[x,\theta,\phi]^T$ and $s=[q^T,\dot q^T]^T$.

In Plate 01, start at the ground contact, go to axle centre $O$, then hip $H$,
then the body. The rolling constraint keeps $O$ at height $r$. The rod between
$O$ and $H$ represents the **combined equivalent legs**, not a literal one-legged
machine. The wheel disk represents the wheel pair. This sagittal reduction
cannot display left/right articulation, five-bar closure, yaw, hopping or slip.

Read panel C: keeping $\theta$ fixed does not keep $\phi$ fixed. The independent
coordinates are the axle translation and two absolute pitches. A hip encoder
instead measures a relative joint angle. For example,
$\theta=8^\circ$, $\phi=-6^\circ$ gives $q_h=-14^\circ$.
If the leg moves to $10^\circ$ while the body stays at $-6^\circ$, the hip angle
becomes $-16^\circ$. Treating hip angle as body pitch would create a fictitious
body motion in the controller.

> [!example] Read the same robot in two coordinate systems
> Physical coordinates: $[x,\theta,\phi]$. MuJoCo joints:
> $[x,\theta,\phi-\theta]$. Recover $\phi$ by adding the two joint angles.
> No extra degree of freedom is created by changing coordinates.

### 1.2 Geometry: where are the masses?

![Dimensions and centres of mass](assets/02_geometry_and_com.png)

*Plate 02. Follow $O\to C_l$, $O\to H$, then $H\to C_b$. The geometry is
illustrative. $r$ is source-code-supported, while $L,a,b$ are assumptions, not CAD measurements.*

Here $L$ is axle-to-hip length, $a$ the axle-to-leg-COM distance, and $b$ the
hip-to-body-COM distance. The centre of mass (COM) locates translational mass;
rotational inertia still matters and is not determined just by that point.
Angles measured from vertical give a **sine horizontal component** and a
**cosine vertical component**:

$$
p_l(q)=\begin{bmatrix}x+a\sin\theta\\r+a\cos\theta\end{bmatrix},
\qquad
p_b(q)=\begin{bmatrix}x+L\sin\theta+b\sin\phi\\r+L\cos\theta+b\cos\phi\end{bmatrix}.
$$

Build the body position by adding vectors rather than guessing a drawing angle.
At upright, $p_l=[x,r+a]^T$ and $p_b=[x,r+L+b]^T$. At zero leg tilt but nonzero
body tilt, the hip remains above the axle while the body COM moves relative to it.

| Parameter | Teaching-model value | Meaning |
| --- | ---: | --- |
| $r,L,a,b$ | 0.0603, 0.16, 0.08, 0.06 m | Rolling radius; axle–hip; leg COM offset; body COM offset |
| $m_w,m_l,m_b$ | 0.6, 0.5, 2.0 kg | Aggregate equivalent masses |
| $I_w,I_l,I_b$ | 0.0011, 0.0012, 0.018 kg m² | Respective COM pitch/rolling-axis inertias |

These are the existing assumed simulation parameters. They do not identify
your team's future CAD assembly. For the illustrated $8^\circ/-6^\circ$ state
with $x=0$, substituting numbers gives approximately
$p_l=[0.01113,0.13952]^T$ m and $p_b=[0.01600,0.27841]^T$ m.

**Checkpoint:** if an equation gives $z_l=r+a\sin\theta$, it predicts the wrong
upright COM height. Use the drawing to catch the algebraic mistake.

### 1.3 Differentiate the geometry to obtain velocities

Differentiation must include every moving link:

$$
v_l=\begin{bmatrix}
\dot x+a\cos\theta\dot\theta\\-a\sin\theta\dot\theta
\end{bmatrix},
\quad
v_b=\begin{bmatrix}
\dot x+L\cos\theta\dot\theta+b\cos\phi\dot\phi\\
-L\sin\theta\dot\theta-b\sin\phi\dot\phi
\end{bmatrix}.
$$

The body can move because the axle translates, the leg rotates, **and** the
body rotates. Those three contributions create coupling when we square speed.
For instance,

$$
\|v_l\|^2=\dot x^2+2a\cos\theta\dot x\dot\theta+a^2\dot\theta^2.
$$

The middle term is why the cart and the upright structure cannot be analysed
as unrelated masses. Equivalently $v_l=J_{p_l}(q)\dot q$,
$v_b=J_{p_b}(q)\dot q$; each Jacobian is the derivative of the corresponding COM
position with respect to the three coordinates.

### 1.4 Energy: keep both translation and rotation

![Kinetic and gravitational energy](assets/03_energy_terms.png)

*Plate 03. The separated component panels explain energy terms. Their lower
pivots/ground strokes are illustration references: the real leg root moves
with $O$ and the body pivot moves with $H$; neither is anchored to the floor.*

Add each component's translational and rotational kinetic energy:

$$
\begin{aligned}
T={}&\frac12\left(m_w+\frac{I_w}{r^2}\right)\dot x^2
+\frac12m_l\|v_l\|^2+\frac12I_l\dot\theta^2\\
&+\frac12m_b\|v_b\|^2+\frac12I_b\dot\phi^2.
\end{aligned}
$$

Ideal rolling gives wheel angle $\beta=x/r$, so its rotational term is
$\tfrac12 I_w(\dot x/r)^2$. Removing $\beta$ from the independent coordinates
does not remove that energy. Numerically $I_w/r^2\approx0.30253$ kg:
the effective horizontal inertia is larger than $m_w+m_l+m_b=3.1$ kg.

Take $I_l,I_b$ about each COM. Using inertia already shifted to a pivot **and**
adding the same COM translational term would double-count part of the energy.
This distinction will matter when importing CAD inertia tensors later.

Ignoring constant height terms, physical potential energy is $V_{\mathrm{mech}}$
(the plates shorten this to $V$; later $V_k$ means optimal remaining cost):

$$
V_{\mathrm{mech}}=g(m_la+m_bL)\cos\theta+gm_bb\cos\phi.
$$

Near upright, $\cos\theta\approx1-\theta^2/2$. Thus a small tilt lowers
potential energy: upright is a local maximum in the two pitch directions.
Horizontal translation changes no height, so it is a flat direction in $V_{\mathrm{mech}}$.
The open-loop instability is a property to control, not a simulation defect.

> [!note] Energy versus design cost
> $T,V_{\mathrm{mech}}$ have physical units of joules. The LQR objective $J$ is a chosen weighted
> error/effort measure; it is not necessarily energy. Likewise $\int\tau^2dt$
> is not electrical energy consumption.

### 1.5 Motor reactions: obtain generalized force from virtual work

![Motor reaction torques and external push](assets/04_motor_reactions_and_push.png)

*Plate 04. Read the equal-and-opposite motor reactions, not just the forward
wheel drive. Its printed generalized-force symbol $Q$ is renamed $\mathcal Q$
below to avoid confusing it with the LQR state-weight matrix.*

A motor acts **between two bodies**. Relative wheel-motor rotation is
$\beta-\theta=x/r-\theta$. Relative hip rotation is $\phi-\theta$.
The virtual work is

$$
\delta W=\tau_w\left(\frac{\delta x}{r}-\delta\theta\right)
+\tau_h(\delta\phi-\delta\theta)
=\mathcal Q_{\mathrm{mot}}^T\delta q.
$$

Collect coefficients of each virtual displacement:

$$
\mathcal Q_{\mathrm{mot}}=
\begin{bmatrix}\tau_w/r\\-\tau_w-\tau_h\\\tau_h\end{bmatrix}
=Gu,\qquad
G=\begin{bmatrix}1/r&0\\-1&-1\\0&1\end{bmatrix}.
$$

The first entry is a generalized horizontal force (N); the last two are
generalized torques (N m). They are not three motor outputs. In particular,
$\tau_w/r$ is not an extra contact force to add again in this reduced model.
Deleting the negative leg reactions changes the plant and the required $K$.

A horizontal force $F$ at the body COM performs work
$F\,\delta(p_b)_x$. Hence

$$
\mathcal Q_F=j_F(q)F,\qquad
j_F(q)=\begin{bmatrix}1\\L\cos\theta\\b\cos\phi\end{bmatrix}.
$$

The force has no separate applied couple at the COM, yet contributes generalized
pitch moments because that point moves when the coordinates rotate.
A 6 N pulse lasting 0.15 s has impulse 0.9 N s. It is neither 6 N m nor a
constant force over the entire episode.

### 1.6 From energy to nonlinear equations of motion

![Mechanical derivation into first-order state dynamics](assets/05_mechanics_to_state_space.png)

*Plate 05. Read left to right: geometry → position/velocity → energy →
Euler–Lagrange → first-order dynamics. The footnote in the plate agrees with our
notation: $s$ is six-dimensional; $x$ alone is axle displacement.*

Form the Lagrangian $\mathscr L=T-V_{\mathrm{mech}}$ and use

$$
\frac{d}{dt}\frac{\partial\mathscr L}{\partial\dot q}
-\frac{\partial\mathscr L}{\partial q}=Gu+j_FF.
$$

This is Newton's law expressed in the chosen coordinates. Define compact
coefficients, with new names to avoid overloading the state $s$:

$$
\begin{aligned}
\mu&=m_w+m_l+m_b+I_w/r^2,&
\alpha&=m_la+m_bL,&\sigma&=m_bb,\\
\kappa&=m_bLb,&
J_l&=I_l+m_la^2+m_bL^2,&J_b&=I_b+m_bb^2.
\end{aligned}
$$

Collect acceleration coefficients in $M$ and the remaining velocity/gravity
terms in $h$:

$$
M(q)=\begin{bmatrix}
\mu&\alpha\cos\theta&\sigma\cos\phi\\
\alpha\cos\theta&J_l&\kappa\cos(\theta-\phi)\\
\sigma\cos\phi&\kappa\cos(\theta-\phi)&J_b
\end{bmatrix},
$$

$$
h(q,\dot q)=\begin{bmatrix}
-\alpha\sin\theta\dot\theta^2-\sigma\sin\phi\dot\phi^2\\
\kappa\sin(\theta-\phi)\dot\phi^2-\alpha g\sin\theta\\
-\kappa\sin(\theta-\phi)\dot\theta^2-\sigma g\sin\phi
\end{bmatrix}.
$$

Thus $M(q)\ddot q+h=Gu+j_FF$. Off-diagonal inertia terms express coupling;
the sine/rate-squared terms arise from changing geometry; the negative gravity
terms reflect the upright energy maximum. These are equations for the assumed
rigid-leg surrogate, not a full five-bar multibody model.

To see one derivation rather than just receive a matrix, the translation row is

$$
\mu\ddot x+\alpha\cos\theta\ddot\theta+\sigma\cos\phi\ddot\phi
-\alpha\sin\theta\dot\theta^2-\sigma\sin\phi\dot\phi^2
=\tau_w/r+F.
$$

It follows by differentiating
$\partial T/\partial\dot x=\mu\dot x+\alpha\cos\theta\dot\theta+
\sigma\cos\phi\dot\phi$. There is no $\partial V_{\mathrm{mech}}/\partial x$ term:
translation does not change the heights.

Finally, first-order state dynamics mean stacking velocity and acceleration:

$$
\dot s=f(s,u,F)=
\begin{bmatrix}\dot q\\M(q)^{-1}[Gu+j_F(q)F-h(q,\dot q)]\end{bmatrix}.
$$

In numerical code, solve the linear system in $M$ instead of forming its inverse.
This equation is the nonlinear plant. **LQR is the next step**, not a substitute
for deriving the plant in the first place.

## 2. From nonlinear dynamics to a sampled model

![Local linearization and sampled held commands](assets/06_linearization_and_sampling.png)

*Plate 06. The curves are a teaching sketch, not recorded robot traces. The
2 ms timing is the nominal plant/LQR tick; the later PPO v2 policy is 100 Hz.*

Write the nonlinear dynamics as

$$
\dot s=f(s,u).
$$

At an equilibrium, $f(s^\star,u^\star)=0$. A first-order Taylor expansion gives

$$
\dot e\approx A_c e+B_c v,
\qquad
A_c=\left.\frac{\partial f}{\partial s}\right|_\star,
\quad B_c=\left.\frac{\partial f}{\partial u}\right|_\star.
$$

The subscript $c$ means continuous time. Terms quadratic and higher in the
deviations are omitted. That is why a controller derived near upright cannot
automatically swing up a fallen robot.

For the mechanical model just derived, $M_0=M(0)$ and
$D=\operatorname{diag}(0,\alpha g,\sigma g)$ give

$$
A_c=\begin{bmatrix}0_{3\times3}&I_3\\M_0^{-1}D&0_{3\times3}\end{bmatrix},
\qquad B_c=\begin{bmatrix}0_{3\times2}\\M_0^{-1}G\end{bmatrix}.
$$

The upper rows say that derivatives of coordinates are velocities. The lower
rows follow from moving the first-order gravity terms to the right-hand side.
Do not put the nominal torque into $A_c$: input sensitivity belongs in $B_c$.

For a digital controller with sample period $h$ and constant command within
each interval, the exact sampled **linear** dynamics are

$$
e_{k+1}=A_d e_k+B_d v_k,
\qquad
A_d=e^{A_ch},
\quad
B_d=\int_0^h e^{A_c\tau}B_c\,d\tau.
$$

This is zero-order hold (ZOH). It is not the same as assuming
$A_d=I+hA_c$, $B_d=hB_c$; those are first-order approximations.

Our nominal WBR synthesis also differentiates the simulator's actual held-input
transition $F_h(s,u)$ to obtain $A_d,B_d$. It compares those matrices with ZOH.
Differentiating the actual transition matches the numerical dynamics being
controlled, including its integration method. We **read** existing gains here;
we do not launch another synthesis or simulation campaign.

From now on, write $A=A_d$, $B=B_d$, and $s=e$ to simplify notation.

## 3. Specify the optimization problem

Choose a finite horizon $N$ and minimize

$$
J=\sum_{k=0}^{N-1}
\left(s_k^TQs_k+u_k^TRu_k\right)+s_N^TP_Ns_N,
\qquad s_{k+1}=As_k+Bu_k.
$$

Assume $Q=Q^T\succeq0$, $R=R^T\succ0$ and terminal weight
$P_N=P_N^T\succeq0$. The input is unconstrained in this derivation.

| Quantity | Shape | Meaning |
| --- | --- | --- |
| $s,u$ | $n\times1$, $m\times1$ | State and action |
| $A,B$ | $n\times n$, $n\times m$ | Sampled dynamics |
| $Q,R$ | $n\times n$, $m\times m$ | Immediate state/action cost weights |
| $P_k$ | $n\times n$ | Optimal remaining-cost matrix |
| $K_k$ | $m\times n$ | Feedback gain |

**Why quadratic?** It penalizes both signs of an error, strongly penalizes large
errors, and gives a tractable optimization. It is a design choice, not a law of
robotics. The weights encode the trade-off between tracking and effort.

For our nominal WBR configuration,

$$
Q_c=\operatorname{diag}(40,200,200,8,8,8),
\qquad R_c=\operatorname{diag}(0.8,0.6).
$$

These weights act on SI-valued states/torques. The code uses
$Q_d=hQ_c$, $R_d=hR_c$ with $h=0.002\,\mathrm{s}$; it declares a sampled
cost, not exact integration of the continuous-time cost.

Example: a $2\,\mathrm{cm}$ position error contributes
$40(0.02)^2=0.016$ to the instantaneous quadratic expression. A
$1^\circ$ leg error contributes $200(\pi/180)^2\approx0.0609$.
Numbers such as 40 and 200 cannot be compared without the state units/scales.

Multiplying **both** $Q$ and $R$ by the same positive constant scales $P$ and
$J$, but leaves the unconstrained optimal $K$ unchanged. Changing only $Q$ or
only $R$ changes the trade-off. A scalar RL reward rescaling need not behave
identically because its optimizer and critic introduce additional effects.

## 4. Derive feedback using Bellman

![Offline LQR synthesis and online feedback](assets/07_lqr_feedback_loop.png)

*Plate 07. Follow the top row to find where $K$ is computed; follow the middle
loop to find where it is used. This plate is the **nominal six-state** loop.
Delay-aware LQR later has extra actuator/history states and more gain columns.*

The controller is calculated offline, then repeatedly reads a state, multiplies
by $-K$, clips the pair commands and sends them to the nonlinear plant. This is
feedback, not a precomputed movie. The derivation below explains the offline box.

### 4.1 The value function

Define $V_k(s)$ as the minimum cost still to come when we start at state $s$
at sample $k$. Terminal condition: $V_N(s)=s^TP_Ns$.

The principle of optimality says: choose today's action, pay today's cost,
then act optimally from tomorrow's resulting state:

$$
V_k(s)=\min_u\left[
s^TQs+u^TRu+V_{k+1}(As+Bu)
\right].
$$

This is the **Bellman equation**. It is the bridge to RL: the definition of
future value exists before a neural network is involved.

### 4.2 Substitute a quadratic future value

Suppose $V_{k+1}(s)=s^TP_{k+1}s$. Let $P=P_{k+1}$ temporarily.
Expanding the expression inside the minimum gives

$$
\begin{aligned}
&s^TQs+u^TRu+(As+Bu)^TP(As+Bu)\\
&=s^T(Q+A^TPA)s
  +2u^TB^TPAs
  +u^T(R+B^TPB)u.
\end{aligned}
$$

For fixed $s$, this is a quadratic function of $u$. Its Hessian is
$2(R+B^TPB)\succ0$, so setting the gradient to zero gives the unique minimum:

$$
2(R+B^TPB)u+2B^TPAs=0.
$$

Therefore

$$
\boxed{u_k^\star=-K_ks_k},
\qquad
\boxed{K_k=(R+B^TP_{k+1}B)^{-1}B^TP_{k+1}A}.
$$

**Interpretation:** action has two costs: immediate effort $R$ and the future
state cost it creates, $B^TPB$. The term $B^TPA$ measures how action can counter
the state's natural evolution. The feedback gain balances those effects.

### 4.3 Substitute the minimum back

Putting $u=-K_ks$ into Bellman gives a quadratic value again:

$$
\boxed{
P_k=Q+A^TP_{k+1}A
-A^TP_{k+1}B(R+B^TP_{k+1}B)^{-1}B^TP_{k+1}A
}.
$$

That is the **Riccati recursion**. Start with $P_N$, work backwards, and obtain
$P_k,K_k$. The quadratic assumption is self-consistent: the terminal value is
quadratic and every preceding Bellman step preserves that form.

### 4.4 Infinite horizon

For a time-invariant problem, under appropriate conditions the backwards
recursion converges to a constant stabilizing solution $P$. Its fixed-point
equation is the discrete algebraic Riccati equation (**DARE**):

$$
\boxed{
P=Q+A^TPA-A^TPB(R+B^TPB)^{-1}B^TPA
}.
$$

Then $K=(R+B^TPB)^{-1}B^TPA$ is constant. **Offline**: solve for $P,K$.
**At each control tick**: compute $-Ks$. You do not solve an optimization
problem again at every tick of a fixed-gain LQR controller.

> [!tip] A way to test your understanding
> Cover the boxed equations. Starting with Bellman and $V(s)=s^TPs$, recover
> the coefficient of $u^Tu$, differentiate with respect to $u$, and derive $K$.
> If you can do this, DARE is no longer a mysterious library call.

## 5. Work a scalar example by hand

Use an intentionally dimensionless system:

$$
x_{k+1}=x_k+u_k,
\qquad J=\sum_{k=0}^{\infty}(x_k^2+u_k^2).
$$

Here $A=B=Q=R=1$. DARE becomes

$$
P=1+P-\frac{P^2}{1+P}
\quad\Rightarrow\quad P^2-P-1=0.
$$

Choose the positive stabilizing root:

$$
P=\frac{1+\sqrt5}{2}\approx1.618034,
\quad K=\frac{P}{1+P}\approx0.618034,
\quad A-BK\approx0.381966.
$$

With $x_0=1$, the first action is $u_0=-0.618034$ and the next state is
$x_1=0.381966$. Bellman numerically checks out:

$$
\underbrace{x_0^2+u_0^2}_{1.381966}
+\underbrace{P x_1^2}_{0.236068}
=\underbrace{P x_0^2}_{1.618034}.
$$

Why not apply $u_0=-1$ and reach zero immediately? That costs 2 in one step.
The LQR solution accepts a small remaining error to spend less total effort.
The negative Riccati root is not the desired value function; it produces an
unstable closed-loop pole. Merely satisfying a polynomial equation is insufficient.

![Scalar value and feedback response](assets/scalar-value-feedback.svg)

*Calculated plot A. Computed from the scalar example by the included script. The parabola
is remaining optimal cost, not a learned reward curve. The right panel uses samples, not seconds.*

## 6. What stability means

With feedback, $s_{k+1}=(A-BK)s_k$. Discrete asymptotic stability requires

$$
\rho(A-BK)=\max_i|\lambda_i(A-BK)|<1.
$$

For infinite-horizon LQR, standard sufficient conditions are:

- $(A,B)$ is **stabilizable**: every unstable or marginal mode can be influenced by the input.
- $(Q^{1/2},A)$ is **detectable**: any mode invisible to the state cost is already stable.
- $Q\succeq0$ and $R\succ0$.

Full controllability is stronger than stabilizability. Its matrix is
$\mathcal C=[B\;AB\;\cdots\;A^{n-1}B]$; rank $n$ means all modes are
controllable. Raw rank is sensitive to scaling/tolerance, so inspect conditioning
on a serious robot model. The tiny teaching system is well behaved.

There is also a value-function explanation. DARE implies

$$
(A-BK)^TP(A-BK)-P=-(Q+K^TRK).
$$

Thus along the ideal closed loop,

$$
V(s_{k+1})-V(s_k)=-s_k^TQs_k-u_k^TRu_k\le0.
$$

The optimal remaining cost decreases by exactly the cost just paid. When $P$
is positive definite and the decrement is strictly positive away from zero,
this is a direct Lyapunov argument. Semidefinite cases require the extra
detectability/invariance reasoning; nonincrease alone is not always enough.

> [!warning] The boundary of the result
> This concerns the specified linear, unconstrained system. Saturation, delay,
> a different sign convention, modelling errors or a large nonlinear excursion
> can invalidate its assumptions. Stable poles are not proof of global WBR balance.

## 7. Continuous versus discrete LQR

For the continuous-time problem,

$$
\dot s=A_cs+B_cu,
\qquad J_c=\int_0^\infty(s^TQ_cs+u^TR_cu)\,dt,
$$

the Hamilton–Jacobi–Bellman equation is

$$
0=\min_u\left[s^TQ_cs+u^TR_cu+
(\nabla_sV)^T(A_cs+B_cu)\right].
$$

With $V=s^TP_cs$, differentiating with respect to $u$ gives
$u=-R_c^{-1}B_c^TP_cs$. Substitution gives the continuous algebraic Riccati
equation (**CARE**):

$$
A_c^TP_c+P_cA_c-P_cB_cR_c^{-1}B_c^TP_c+Q_c=0.
$$

This is a different equation from DARE, with a different gain formula.
Continuous stability uses negative real parts of poles; sampled stability uses
pole magnitudes below one. Under ZOH, open-loop modes map as
$\lambda_d=e^{\lambda_ch}$, but a continuously varying feedback command and
a sampled-and-held feedback command are different implementations.

**Good to Know:** exact discretization of the continuous cost generally produces
$Q_d,R_d$ **and a state–input cross term**. Setting $Q_d=hQ_c$, $R_d=hR_c$
is a simple rectangle approximation, not that exact transformation. The exercise
explicitly chooses this approximate sampled cost, matching our nominal WBR convention.

## 8. Apply DARE to a cart-pole

To see a real matrix without WBR complexity, use a cart of mass $M$, a point
mass $m$ at the end of a massless rod of length $l$, and horizontal force $F$.
Choose $\alpha=0$ upright, positive when the pole leans **right**. The tip has
horizontal coordinate $x+l\sin\alpha$.

Near upright, the coupled equations are

$$
(M+m)\ddot x+ml\ddot\alpha=F,
\qquad ml\ddot x+ml^2\ddot\alpha-mgl\alpha=0.
$$

Solving them gives

$$
\ddot x=\frac{F}{M}-\frac{mg}{M}\alpha,
\qquad
\ddot\alpha=-\frac{F}{Ml}+\frac{(M+m)g}{Ml}\alpha.
$$

Notice the unstable gravitational term and the negative force-to-angle sign:
moving the support right can reduce a rightward lean.
With $s=[x,\dot x,\alpha,\dot\alpha]^T$,

$$
A_c=\begin{bmatrix}
0&1&0&0\\
0&0&-mg/M&0\\
0&0&0&1\\
0&0&(M+m)g/(Ml)&0
\end{bmatrix},
\qquad
B_c=\begin{bmatrix}0\\1/M\\0\\-1/(Ml)\end{bmatrix}.
$$

The script uses $M=1\,\mathrm{kg}$, $m=0.1\,\mathrm{kg}$,
$l=0.5\,\mathrm{m}$, $g=9.81\,\mathrm{m/s^2}$, $h=0.02\,\mathrm{s}$,
$Q_d=h\operatorname{diag}(10,1,100,1)$ and $R_d=0.1h$.
It performs ZOH discretization, solves DARE, checks controllability and poles,
then propagates only 400 linear steps from a $5^\circ$ tilt.

![Linear cart-pole calculation](assets/cartpole-response.svg)

*Calculated plot B. The actual calculated response of the included linear toy model.
There is no force limit, contact model, delay or sensor noise. These are not
experimental WBR traces or a nonlinear swing-up demonstration.*

The gain's sign depends on the coordinate convention. A website using positive
leftward tilt can have different angle-column signs and still describe the same
physical controller. Never copy gains without copying their state/input definitions.

## 9. Read the real WBR simulation gains

The nominal frozen DARE gain in `sim/configs/assumed_actuator_noise.json` is

$$
K_{\mathrm{nom}}\approx
\begin{bmatrix}
-4.529102&-15.788951&-7.401367&-5.582295&-2.677155&-1.481871\\
1.191661&-0.430952&15.023835&1.548874&-0.036645&2.899251
\end{bmatrix}.
$$

This displayed matrix is rounded for reading. The script reads full saved
precision from [the included snapshot](data/wbr_gains.json).
Row 1 produces wheel-pair torque; row 2 produces virtual hip-pair torque.
Column order is the six-state order in Section 1. Each column has the torque
units divided by the corresponding state unit; $K$ is not dimensionless.

For leg tilt alone, $\theta=5^\circ=0.0872665\,\mathrm{rad}$,

$$
-K_{\mathrm{nom}}
\begin{bmatrix}0&0.0872665&0&0&0&0\end{bmatrix}^T
\approx\begin{bmatrix}1.377846\\0.037608\end{bmatrix}\,\mathrm{N\,m}.
$$

That is one matrix multiplication, **not evidence that this state will recover**.
The issued command is also clipped to the assumed pair limits $[2,4]\,\mathrm{N\,m}$.

### Delay-aware LQR is a different state-space controller

![Transport delay, actuator lag and measurement noise](assets/08_delay_lag_and_noise.png)

*Plate 08. The mechanical state stays six-dimensional, but the controller can
also receive estimates/history. Its “evaluation metrics only” label is limited:
in RL training, true state also supplies the reward/termination calculation;
neither actor nor critic receives that privileged truth as an observation.*

The robot does not instantly receive a newly issued command. With transport
delay and motor lag, six mechanical coordinates are insufficient to predict
the future: queued commands and current motor torque matter.

The augmented state has the structure

$$
z_k=\begin{bmatrix}
\hat s_k\\\hat\tau_k\\u_{k-1}\\\vdots\\u_{k-H}
\end{bmatrix},
\qquad \dim z=6+2+2H.
$$

Here $\hat s$ is measured, $\hat\tau$ is reconstructed causally from commands
using the assumed actuator model, and command history is clipped issued history.
It is not a torque sensor or privileged simulator truth.

Read the lower timing panels separately. A command issued at 0 ms with 3 ms
transport delay arrives at 3 ms, between the 2 ms and 4 ms controller updates.
After arrival, first-order motor lag starts changing realized torque:

$$
T_m\dot\tau+\tau=u(t-d),\qquad
\tau(t)=u_0[1-\exp(-(t-d)/T_m)]\quad(t\ge d)
$$

for a held step from zero; before arrival, torque stays zero. At $t=d+T_m$ it
reaches 63.2% of the step. Transport delay shifts the response onset; lag changes
its rise. Adding their numerical values and calling the sum “delay” loses that
distinction. Sensor noise is a third mechanism, acting on feedback rather than
the motor input. Noise here affects only body angle and body rate, not all six
coordinates equally.
For 2/3/4/5 ms transport delays and a 2 ms control tick, saved matrices have
respectively 10/12/12/14 columns. The runtime represents fractional-tick arrivals;
it does not round a 3 ms delay to 2 or 4 ms.

The historical comparison first observed nominal-gain failures with imperfections,
then froze delay-specific augmented gains with unchanged Q/R. **That delay-aware
controller is the LQR baseline in our PPO comparison.** The script only reads its
archived gain matrices from the committed host-controller fixture. It does not
recreate the protected gain schedule or claim those matrices match firmware.

Source map, pinned at the commit in [[Sources]]:

| Repository file | What to inspect later |
| --- | --- |
| `sim/planar.py` | State order, coordinate transformation and assumed reduced plant |
| `sim/lqr.py` | Nominal CARE/DARE, finite differences, residuals and poles |
| `sim/augmented_lqr.py` | DARE on the delay/lag augmented runtime state |
| `sim/configs/assumed_actuator_noise.json` | Saved nominal gain and actuator assumptions |
| `sim/control_c/fixtures/recorded.json` | Archived delay-aware gains and recorded arithmetic fixtures |
| `sim/rl/v2.py` | 100 Hz policy, 500 Hz plant/LQR; recomputes LQR feedback on each plant tick |

Do not edit `sim/parity/student.py::gain_schedule`; it remains the owner's exercise.

## 10. Run the exercise

Use a separate environment; do not alter an active PPO environment. From the
extracted `pack1-lqr/` directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install numpy==1.26.4 scipy==1.15.3 matplotlib==3.10.3
python lqr_exercise.py
```

Python 3.11 or 3.12 is suitable for these pinned dependencies. There is no need
for PyTorch, MuJoCo, CUDA, ROS or a GPU. Default execution uses only NumPy/SciPy;
Matplotlib is used only when regenerating the two numerical plots:

```sh
python lqr_exercise.py --figures assets
```

Compare the console output with [expected-output.txt](expected-output.txt).
The scalar values should match to six decimals; the cart-pole gain and radius
should be close to the printed reference, and the relative DARE residual must
be below $10^{-9}$. Small last-digit differences across numerical libraries are
normal. Missing dependencies, failed assertions, a nonfinite gain or a pole
outside the unit circle are failures to investigate, not results to hide.

The script checks the scalar Bellman identity, solves a real 4-state DARE,
checks decay of the toy trajectory, and checks the dimensions of the saved WBR
matrices. It does **not** verify the WBR's nonlinear stability, hardware parameters
or delay robustness. The tiny CPU work has no training loop or rendering window.

It also evaluates the COM geometry and checks virtual-work/power consistency:
$(Gu)^T\dot q=\tau_w(\dot x/r-\dot\theta)+
\tau_h(\dot\phi-\dot\theta)$. Predict the leg reaction signs before running it.
The supplied mechanical plates are preserved image files; the `--figures` option
regenerates only the two computed scalar/cart-pole plots, not those plates.

> [!example] Learn by changing one thing
> On a personal copy, increase only cart-pole $R$ tenfold and rerun. Compare
> peak force and settling with the original. Then multiply both $Q$ and $R$
> tenfold: the gain should stay equal within numerical precision. Predict each
> outcome first; a larger $R$ does not guarantee every individual peak decreases.

## 11. Questions, answers and the next experiment

### Self-check

1. Which equation tells you why $u=-Ks$ is optimal?
2. What is the distinction between $Q$ and $P$?
3. Why does a stable $A-BK$ not prove recovery from a $60^\circ$ tilt?
4. Would a $2\times6$ gain multiply our 14-element augmented state correctly?
5. If commands arrive late, why does position/tilt alone not determine the next state?
6. Is an LQR solved with negative reward automatically equivalent to discounted PPO?

> [!success]- Answers
> 1. Bellman minimization: expand the quadratic future value and set its action gradient to zero.
> 2. $Q$ is an immediate design penalty; $P$ is the optimal total remaining-cost matrix obtained from the dynamics and weights.
> 3. The proof concerns local linear dynamics with unconstrained input, not the saturated nonlinear robot far from upright.
> 4. No. The dimensions and state meanings differ; truncating or padding silently invents another controller.
> 5. Two mechanically identical robots with different queued commands or realized motor torques can evolve differently.
> 6. No. Discount, time discretization, reward terms, horizon, action constraints, observations and optimization differ.

### The path into our project

**Now:** finish the hand derivation, run the exercise, and explain one row of
the WBR matrix in physical units. **Next:** [[Pack 2 - RL to PPO]] replaces known
quadratic value optimization with learned values and sampled policy updates.
Then [[Pack 3 - Residual and experiment]] connects a learned correction to LQR.

The approved candidate question is **residual PPO versus delay-aware LQR under
delay mismatch: train on 2–5 ms, test on 6–10 ms**. It is not a research-gap claim.
Before a later experiment, define what delay the controller is told and which
delay-specific gain is used outside the training range. Retuning an oracle LQR
for every test delay changes the question. The current frozen v2 panel does not
by itself test this new mismatch design.

Pack 3 specifies paired disturbances, seeds, strict settling versus
survival, recovery time, tracking RMSE, commanded/applied torque effort, saturation
and compute. New training must follow the current project pilot rule; this pack
does not launch it. Saved legacy v2 optimizer losses are not return/episode-length
curves, and unavailable learning curves must remain labelled unavailable.

### What you must know versus what can wait

| Must Know | Good to Know | Skip For Now |
| --- | --- | --- |
| State definitions, sampled dynamics, Bellman expansion, DARE, gain multiplication, poles, units and limits | CARE/HJB, exact cost discretization, Lyapunov details and numerical conditioning | MPC implementation, global swing-up design, drone dynamics and hardware deployment |

Read [[Sources]] for primary references, figure provenance and the exact source
snapshot. The lesson's mathematical derivations are educational explanations;
the saved WBR gains remain facts about an assumed simulation, not measured hardware.

Optional further mechanical plates: [English prompts and figure review](FIGURE_REVIEW_AND_PROMPTS.md), including each intended filename.
