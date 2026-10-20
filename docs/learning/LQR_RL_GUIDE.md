# Understand the WBR model, then LQR, then RL

This guide explains the **running, reduced planar model** in this repository.
It is an assumed teaching model: not the full five-bar robot or a validated digital twin.
Read Sections 1–4 first; Section 5 explains the current delay/noise work, and Section 6 connects it to RL.
The [parameter source table](MODEL_PARAMETER_SOURCES.md) separates current assumptions,
firmware constants and supplier specifications; matching assembly masses and COM remain unknown.

## 1. What moves, and what are the states?

We combine the two wheels and two legs into one sagittal mechanism. The axle moves horizontally;
the equivalent leg and body can tilt independently. World $x$ points forward, $z$ upward.
Positive pitch about $+y$ leans forward. Angles are in **radians**.

$$
\mathbf q=\begin{bmatrix}x&\theta&\phi\end{bmatrix}^{\!T},
\qquad
\mathbf x=\begin{bmatrix}x&\theta&\phi&\dot x&\dot\theta&\dot\phi\end{bmatrix}^{\!T}.
$$

Here $\theta$ is the **absolute leg angle**, and $\phi$ the **absolute body angle**.
The hip joint angle is their difference, $\phi-\theta$; setting $\phi=\theta$ would incorrectly weld the body to the leg.
MuJoCo therefore uses joint coordinates $[x,\theta,\phi-\theta]$, then converts them into the state above.

| Symbol | Meaning | Value in our configuration |
|---|---|---|
| $r,L$ | Wheel radius; axle-to-hip length | 0.0603 m; 0.16 m |
| $a,b$ | Leg COM above axle; body COM above hip | 0.08 m; 0.06 m |
| $m_w,m_l,m_b$ | Combined wheel, leg and body masses | 0.6, 0.5, 2.0 kg |
| $I_w,I_l,I_b$ | Wheel rolling inertia; leg/body COM pitch inertia | 0.0011, 0.0012, 0.018 kg·m² |

All physical values are **ASSUMED**, except $r$, which is a source-code constant and still not a physical measurement.
There is no slip, heave, roll, yaw or contact loss: the axle stays at height $r$, and wheel rotation is $\beta=x/r$.
This reduction simplifies balancing; it cannot test terrain contact or jumping.

## 2. From geometry and energy to the nonlinear equations

The leg and body centers of mass follow from the geometry:

$$
\mathbf p_l=\begin{bmatrix}x+a\sin\theta\\r+a\cos\theta\end{bmatrix},
\qquad
\mathbf p_b=\begin{bmatrix}x+L\sin\theta+b\sin\phi\\r+L\cos\theta+b\cos\phi\end{bmatrix}.
$$

Differentiate these positions to obtain COM velocities. Add their translational energies and each component's rotational energy:

$$
\begin{aligned}
T={}&\tfrac12\left(m_w+\frac{I_w}{r^2}\right)\dot x^2\\
&+\tfrac12 m_l\|\dot{\mathbf p}_l\|^2+\tfrac12 I_l\dot\theta^2\\
&+\tfrac12 m_b\|\dot{\mathbf p}_b\|^2+\tfrac12 I_b\dot\phi^2.
\end{aligned}
$$

The wheel term $I_w/r^2$ is essential: rolling wheels store rotational energy even though their rotation was eliminated as an independent coordinate.
Ignoring a constant height term, gravitational potential energy is

$$
V=g(m_la+m_bL)\cos\theta+gm_bb\cos\phi.
$$

Upright is a maximum of this potential energy, so a small tilt tends to grow without control.
The Euler–Lagrange equation balances energy changes against generalized applied forces:

$$
\frac{d}{dt}\frac{\partial T}{\partial\dot{\mathbf q}}
-\frac{\partial T}{\partial\mathbf q}+\frac{\partial V}{\partial\mathbf q}
=\mathbf G\boldsymbol\tau+\mathbf j_FF.
$$

Substituting the energies above and collecting the acceleration terms gives

$$
\boxed{\mathbf M(\mathbf q)\ddot{\mathbf q}+\mathbf h(\mathbf q,\dot{\mathbf q})
=\mathbf G\boldsymbol\tau+\mathbf j_F(\mathbf q)F.}
$$

To keep the expressions readable, define
$m=m_w+m_l+m_b+I_w/r^2$, $p=m_la+m_bL$, $s=m_bb$,
$c=m_bLb$, $j_l=I_l+m_la^2+m_bL^2$, and $j_b=I_b+m_bb^2$.
Then

$$
\mathbf M=\begin{bmatrix}
m&p\cos\theta&s\cos\phi\\
p\cos\theta&j_l&c\cos(\theta-\phi)\\
s\cos\phi&c\cos(\theta-\phi)&j_b
\end{bmatrix},
$$

$$
\mathbf h=\begin{bmatrix}
-p\sin\theta\,\dot\theta^2-s\sin\phi\,\dot\phi^2\\
c\sin(\theta-\phi)\dot\phi^2-pg\sin\theta\\
-c\sin(\theta-\phi)\dot\theta^2-sg\sin\phi
\end{bmatrix}.
$$

**Meaning:** $\mathbf M$ describes inertia and coupling; $\mathbf h$ contains velocity-dependent and gravity terms.
Moving the wheels accelerates the body, and rotating the body reacts on the leg—these are coupled motions, not three separate controllers.
The nonlinear acceleration is $\ddot{\mathbf q}=\mathbf M^{-1}(\mathbf G\boldsymbol\tau+\mathbf j_FF-\mathbf h)$.
MuJoCo integrates this mechanics; an independent Lagrange calculation in the tests checks it at nonzero states.

## 3. Why the motor torque also pushes the leg

The action has **two** components: $\boldsymbol\tau=[\tau_w,\tau_h]^T$, the aggregate wheel-pair and hip-pair torques.
A wheel motor acts between wheel and leg, so its relative rotation is $x/r-\theta$.
A hip motor acts between body and leg, so its relative rotation is $\phi-\theta$.
Their virtual work is

$$
\delta W=\tau_w\left(\frac{\delta x}{r}-\delta\theta\right)
+\tau_h(\delta\phi-\delta\theta),\qquad
\mathbf G=\begin{bmatrix}1/r&0\\-1&-1\\0&1\end{bmatrix}.
$$

Thus a positive wheel torque drives translation **and** applies the opposite torque to the leg.
A positive hip torque rotates the body forward and reacts backward on the leg. Omitting those reactions would change the robot.
Our wheel tendon and hip joint implement these relationships directly.
For a horizontal push $F$ at the body COM, virtual work gives

$$
\mathbf j_F=\begin{bmatrix}1&L\cos\theta&b\cos\phi\end{bmatrix}^{\!T}.
$$

The declared pulse is 6 N for 0.15 s, hence impulse $6\times0.15=0.9\ \mathrm{N\,s}$.
Torque caps are $|\tau_w|\le2$ and $|\tau_h|\le4\ \mathrm{N\,m}$, both assumed aggregate limits.

## 4. Where A, B and the LQR gain come from

Write the nonlinear state dynamics as $\dot{\mathbf x}=f(\mathbf x,\boldsymbol\tau)$.
Linearization means keeping first-order changes around upright, $\mathbf x=0,\boldsymbol\tau=0,F=0$:

$$
\dot{\mathbf x}\approx\mathbf A_c\mathbf x+\mathbf B_c\boldsymbol\tau.
$$

$$
\mathbf A_c=\begin{bmatrix}\mathbf0&\mathbf I\\\mathbf M_0^{-1}\operatorname{diag}(0,pg,sg)&\mathbf0\end{bmatrix},\qquad
\mathbf B_c=\begin{bmatrix}\mathbf0_{3\times2}\\\mathbf M_0^{-1}\mathbf G\end{bmatrix}.
$$

The upper blocks say position derivatives are velocities. The lower blocks say gravity amplifies tilt while motor torques create acceleration.
This is a **local approximation**: it does not replace the nonlinear plant used to test the controller.
Our code finite-differences MuJoCo to obtain these derivatives and the actual held-control RK4 step at $T_s=0.002$ s:

$$
\mathbf x_{k+1}\approx\mathbf A_d\mathbf x_k+\mathbf B_d\mathbf u_k.
$$

LQR chooses feedback to minimize a specified quadratic cost—not to learn from episodes:

$$
J=\sum_{k=0}^{\infty}\left(\mathbf x_k^T\mathbf Q_d\mathbf x_k+\mathbf u_k^T\mathbf R_d\mathbf u_k\right),\qquad
\mathbf u_k=-\mathbf K\mathbf x_k.
$$

We choose $\mathbf Q_d=T_s\operatorname{diag}(40,200,200,8,8,8)$ and
$\mathbf R_d=T_s\operatorname{diag}(0.8,0.6)$. Larger state weights penalize error more; larger input weights penalize effort more.
States have different physical units, so weight magnitudes alone are not directly comparable.
For the sampled system, DARE finds $\mathbf P$, then

$$
\begin{aligned}
\mathbf P={}&\mathbf Q_d+\mathbf A_d^T\mathbf P\mathbf A_d\\
&-\mathbf A_d^T\mathbf P\mathbf B_d(\mathbf R_d+\mathbf B_d^T\mathbf P\mathbf B_d)^{-1}\mathbf B_d^T\mathbf P\mathbf A_d,\\[4pt]
\mathbf K={}&(\mathbf R_d+\mathbf B_d^T\mathbf P\mathbf B_d)^{-1}\mathbf B_d^T\mathbf P\mathbf A_d.
\end{aligned}
$$

We clip the commanded torques to the physical limits afterward.
Discrete closed-loop poles must satisfy $|\lambda(\mathbf A_d-\mathbf B_d\mathbf K)|<1$.
That local condition does **not** guarantee recovery after saturation, added delay or a large nonlinear disturbance; the rollout tests matter.
CARE is the continuous-time alternative; our default uses DARE because the controller updates every 2 ms.

**Worked example:** start with leg $+8^\circ$, body $-6^\circ$, all other states zero.
After conversion to radians, the approved gain gives
$\mathbf u_0=[1.4295,\ 1.6335]^T\ \mathrm{N\,m}$, within both caps.
The nominal nonlinear simulation recovers in 1.732 s; with zero control, the same initial state falls.

## 5. Why delay, motor lag and IMU noise change this result

Commanded torque is not necessarily the torque applied now. The new layer models

$$
T_m\dot{\boldsymbol\tau}(t)+\boldsymbol\tau(t)=\mathbf u(t-d),\qquad
\hat{\mathbf x}_k=\mathbf x_k+\begin{bmatrix}0&0&\eta_\phi&0&0&\eta_\omega\end{bmatrix}^{\!T}.
$$

- **Transport delay $d$:** an old command arrives later; 3 ms must not be rounded to a 2 ms step.
- **Torque lag $T_m$:** after a delivered step from zero, $\tau(t)=u(1-e^{-t/T_m})$; it reaches about 63.2% after one time constant.
- **IMU noise:** the controller sees noisy body angle/rate. Wheel/leg measurements remain ideal assumptions; truth is reserved for evaluation.

Current illustrative settings are 2–5 ms delay, 5 ms motor time constant, body-angle noise SD 0.1° and gyro noise SD 0.01 rad/s.
These are **not measured hardware specifications**. First test the same frozen K, limits, initial states and pulse.
Only an observed failure permits re-synthesis, adding motor state and past commands to the controller's state.
Otherwise a newly tuned controller would hide how the original baseline responds to the changed plant.

## 6. How RL will be compared

RL replaces the fixed gain law with a policy $\mathbf u_k=\pi_\psi(\mathbf o_k)$, trained to maximize expected return:

$$
\max_\psi\;\mathbb E\!\left[\sum_k\gamma^k r_k\right].
$$

The observation $\mathbf o_k$ contains available measurements and causal action history, not hidden perfect state.
Actions remain the same two bounded torques. A reward can penalize state error and effort, but its termination treatment must not make falling attractive.
A fall terminates an episode; the time limit truncates it. Higher reward alone is not evidence of better recovery.

Use the **same augmented plant, sensor information, control rate, torque caps, pushes and evaluation initial states** for both controllers.
Keep at least five training seeds and held-out paired noise seeds; report failures, recovery, peak tilt, tracking and effort with uncertainty.
Training seeds are independent learning runs; many evaluation episodes from one policy do not become many independent training runs.
The [first completed PPO comparison](../../sim/rl/RESULTS_2026-10-20.md) used five seeds,
150,000 steps each: delay-aware LQR passed160/160 episodes; PPO passed0/800.
This is a measured negative result for one fixed recipe on the assumed model.
At a2ms action period,150,000 steps are300 simulated seconds: step count alone does not establish learning.
The [implementation notes](../../sim/rl/README.md) explain the fixed reward, policy update,
recorded failures and why the seed-level interval does not imply universal certainty.

## Read and try next

1. Read [plant](../../sim/planar.py), then [LQR synthesis](../../sim/lqr.py); locate the state transform, motor tendon and K calculation.
2. Open a saved `linearization.json`: check K is 2×6 and find the sampled closed-loop poles. Predict a Q/R change before testing it in a **new** run.
3. Explain why body angle is not hip angle, and why a stable ideal LQR can fail after adding delay.

**Must Know:** Sections 1–5 and fair evaluation. **Good to Know:** delay-state augmentation and PPO updates.
**Skip For Now:** full five-bar/contact dynamics and real motor deployment. Your [gain_schedule exercise](../../sim/parity/student.py) stays untouched.

Sources: [MuJoCo dynamics](https://mujoco.readthedocs.io/en/3.3.7/computation/index.html),
[SciPy DARE](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_discrete_are.html),
[Gymnasium](https://gymnasium.farama.org/introduction/create_custom_env/), [PPO](https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html).
