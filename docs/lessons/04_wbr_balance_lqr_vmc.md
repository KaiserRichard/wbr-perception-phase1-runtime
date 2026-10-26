# 04 — WBR balance control: LQR and VMC

## Learning goals

This lesson reads the previous team's balance loop as a chain:
state estimation → gain scheduling → virtual wheel/leg effort → five-bar
mapping → joint torques.

The code is a useful implementation study, not proof that the old firmware is
safe to deploy on the current robot. Hardware and source assumptions must be
checked before any reuse.

## 1. Plant and control objective

A wheeled-biped balances an inverted body while the wheels move its support
point. The leg can change length and transmit force through a linkage.
The balance controller must react to body/leg tilt and motion before the center
of mass falls outside the recoverable region.

Linear Quadratic Regulator (LQR) assumes a linearized discrete-time model
$x_{k+1}=Ax_k+Bu_k$ and minimizes a quadratic cost

$$
J=\sum_{k=0}^{\infty}(x_k^TQx_k+u_k^TRu_k).
$$

For a stabilizable model and suitable positive-semidefinite $Q$ and positive
$R$, the solution yields a feedback matrix $K$. The common control form is
$u=-Kx$; sign conventions may instead be embedded in stored gains or error
terms. Never infer the sign from the word “LQR” alone.

The DM-jump source has a six-signal feedback contribution for wheel torque and
another six-signal contribution for virtual tangential leg effort
(`User/APP/chassisR_task.c:195-209`; left-side equivalent at
`User/APP/chassisL_task.c:140-154`).

## 2. State vector as implemented

The right-side feedback terms correspond approximately to

$$
x_R = [\theta,\dot\theta,\tilde{x},\tilde{v},\phi_R,\dot\phi_R]^T,
$$

where $\theta$ and $\dot\theta$ are the effective leg/body angle and rate;
$\tilde{x}=x_{filter}-x_{set}$; $\tilde{v}=v_{filter}-v_{set}$;
$\phi_R$ is the right pitch-related state `myPithR`; and $\dot\phi_R$ is
`myPithGyroR`.
The left side uses opposite position/velocity error order in its source
(`chassisL_task.c:141-154`), so compare sign conventions carefully.

This state interpretation is inferred from the variables multiplied by each
gain; it is not a claim that all six entries are a canonical textbook state
vector. **INFERRED:** the final two signals represent a body pitch/gyro correction
because their names and data path indicate pitch and pitch-rate feedback.

The VMC estimator computes linkage geometry, virtual leg length $L_0$, angle
$\phi_0$, and effective angle/rate. On the right,
$\theta=\pi/2-Pitch_R-\phi_0$ and
$\dot\theta=-Gyro_R-\dot\phi_0$
(`User/Algorithm/VMC/VMC_calc.c:65-84`). The left implementation negates the
IMU pitch and gyro first (`VMC_calc.c:105-110, 129-146`).

```text
wheel encoders + IMU
        ↓
five-bar joint angles → ankle point C → (L0, phi0)
        ↓
            theta, dtheta + body/position signals
                         ↓
                     LQR gains
                    /        \
          wheel torque      virtual leg force/torque
```

## 3. Gain scheduling with leg length

A fixed linear feedback matrix is locally designed around one configuration.
As the five-bar leg changes length, geometry and effective dynamics change.
The previous implementation schedules its 12 gains with a cubic polynomial in
measured leg length.

Each row is evaluated as

$$
K_i(L_0)=a_{i3}L_0^3+a_{i2}L_0^2+a_{i1}L_0+a_{i0}.
$$

The polynomial helper implements this expression directly
(`User/Algorithm/VMC/VMC_calc.c:220-228`). The coefficient table has 12 rows
(`User/APP/chassisR_task.c:28-42`). The right control loop recalculates all
gains from current `vmcr->L0` every pass (`chassisR_task.c:180-187`); the left
uses the shared table similarly (`chassisL_task.c:130-138`).

This is polynomial interpolation, not interpolation between two stored matrices.
It assumes the polynomial fits the intended length interval. Outside that
interval it can extrapolate into unreasonable gains. The source excerpt does
not itself provide a validated operating interval, so do not treat the
polynomial as safe for arbitrary $L_0$.

The wheel torque combines the first six terms; the virtual tangential effort
uses the next six (`chassisR_task.c:195-209`). In matrix notation, ignoring
side-specific signs and extra corrections:

$$
\tau_w=K_{w}(L_0)^T x,\qquad T_p=K_p(L_0)^T x.
$$

Stored gains already include their signs. The equations above describe the
sum seen in source, not a universally portable `-Kx` convention.

The WBR source also applies a separate yaw correction and clips wheel torque
to ±2, leg axial force to ±100, and joint torques to ±7
(`chassisR_task.c:189-214, 244-249`; left clipping at
`chassisL_task.c:156-194`). Saturation changes the realized feedback law when
limits are active.

## 4. Virtual Model Control (VMC)

Virtual Model Control maps desired effort in task coordinates into actuator
joint torques. The five-bar linkage gives a nonlinear geometric relationship
between two motor joint angles and the ankle/virtual-leg coordinates.

Let $q=[q_1,q_2]^T$ be actuated joint angles and let
$y=[L_0,\alpha]^T$ be virtual leg length and orientation. Around a pose, the
kinematic Jacobian is

$$
J(q)=\frac{\partial y}{\partial q},\qquad \dot y=J\dot q.
$$

Power consistency requires $\tau_q^T\dot q=F_y^T\dot y$.
Since $\dot y=J\dot q$, this yields

$$
\tau_q=J^TF_y.
$$

The code expresses this mapping as two by two coefficients multiplying
virtual axial effort $F_0$ and tangential effort $T_p$
(`User/Algorithm/VMC/VMC_calc.c:160-175`). The explicit formulas include
five-bar angles, link lengths, and a denominator proportional to
$\sin(\phi_3-\phi_2)$ (`VMC_calc.c:165-175`).

```text
(F0 along virtual leg, Tp perpendicular to leg)
                       ↓ Jᵀ
             (joint torque 1, joint torque 2)
                       ↓
                    actuators
```

Near a singular or poorly conditioned pose, the denominator can become small.
That can amplify noise and required torque. **INFERRED:** this warrants checking
Jacobian conditioning across the allowed leg range; the code formulas alone do
not prove where singularities occur.

The source computes ankle point $C$, $L_0$, and $\phi_0$ from motor angles and
link lengths (`VMC_calc.c:47-72`). It estimates rates by finite difference over
the supplied `dt` (`VMC_calc.c:74-90`). Since differentiation amplifies
measurement noise, encoder quantization and sample timing affect $\dot\phi_0$
and thus the LQR state.

## 5. Loop rates and timing

The IMU task comment says 1 kHz, nominal 1 ms period
(`User/APP/INS_task.c:58-66`). The observer declares a 3 ms update interval,
nominally 333 Hz (`User/APP/observe_task.c:47-56, 70-97`).

Each chassis task computes control and then transmits three motor frames with a
1 ms delay between sends. The integration analysis calculates a nominal
approximately 333 control passes per second from these delays, before
computation and scheduling overhead (`User/APP/chassisR_task.c:71-95`;
`chassisL_task.c:52-78`; `docs/proposals/DM_JUMP_INTEGRATION_ANALYSIS.md:13-21`).
This is not a measured worst-case rate or jitter bound.

The control code passes `CHASSR_TIME * 3 / 1000` as its estimator timestep
(`chassisR_task.c:180-183`); the left does likewise
(`chassisL_task.c:130-133`). That corresponds to nominal 3 ms if the configured
per-frame delay is 1 ms. A delayed or skipped cycle makes finite-difference
rates and discrete-time assumptions less accurate.

## 6. Interpreting the implementation safely

A cubic gain schedule does not automatically make an LQR robust to rapid leg
motion, saturations, sensor delay, linkage backlash, or contact transitions.
A locally stabilizing model may become inaccurate away from its linearization
point.

Before comparing gains, record coordinate frames, positive directions, units,
state order, equilibrium, sample time, and whether gains are row or column
vectors. Match those details in the C implementation and any simulation.

The jump FSM changes the virtual leg target and may suppress wheel effort in
flight (`chassisR_task.c:272-337`; `chassisL_task.c:201-241`). Therefore the
ordinary standing balance loop is only one operating mode of a hybrid controller.

## How this applies in our project

Use this source to understand the legacy balance architecture and to design
read-only parity checks. Treat gain coefficients and timing as source facts,
not as validated gains for today's hardware. Preserve state order and side
signs in any port. Check linkage range, Jacobian conditioning, saturation, and
measured loop timing before making performance claims.

<details>
<summary>Self-check questions and answers</summary>

1. **Which signals form the six apparent feedback components?**
   Leg/body angle and rate, position and velocity errors, and pitch-related angle/rate terms.
2. **Why schedule gains by $L_0$?**
   The linkage geometry and effective dynamics change with leg length.
3. **What does the transpose Jacobian do to virtual force?**
   It maps task-space effort into joint torques while preserving instantaneous power.
4. **What happens near a small Jacobian denominator?**
   The mapping can become ill-conditioned and amplify effort or noise.
5. **Does the 1 kHz INS comment establish a 1 kHz balance loop?**
   No. The chassis loop includes sequential CAN sends and delays; its actual rate must be measured.

</details>
