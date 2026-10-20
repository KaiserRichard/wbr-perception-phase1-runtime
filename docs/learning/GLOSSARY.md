# WBR controls and perception glossary

Plain-language reference for the terms used in the [LQR and RL guide](LQR_RL_GUIDE.md).
The control examples refer to this repository's reduced, assumed six-state planar
MuJoCo model. It is a teaching and comparison model, not a validated digital twin
or a statement about hardware performance. See the [parameter source table](MODEL_PARAMETER_SOURCES.md)
for which values are measured, assumed, or still unknown.

## Control and learning

### LQR — linear quadratic regulator

LQR is a feedback controller designed from a linear model near a chosen operating
point. For the WBR model, the state is
\(x=[x,\theta,\phi,\dot x,\dot\theta,\dot\phi]^T\): axle position in metres,
leg and body pitch in radians, and their rates in metres per second or radians per
second. The action \(u=[\tau_w,\tau_h]^T\) is the wheel-pair and hip-pair torque
command in newton-metres (N m). LQR uses

$$
u_k=-Kx_k
$$

to trade state error against effort using selected weight matrices \(Q\) and
\(R\). A, B, Q, and R must use consistent state, input, and time units; their
entries do not all have the same units because the state mixes metres, radians,
and rates. The gain \(K\) is therefore tied to this state definition, model,
sample period, and cost. It is a local design: torque clipping, large tilts,
transport delay, and motor lag can invalidate what the linear model predicts.

**WBR example:** the nominal controller updates every 2 ms and commands two
aggregate torques, limited in the simulation to 2 N m at the wheels and 4 N m at
the hip. With delay and motor lag, the project uses a conditional delay-aware
design that includes past commands and actuator state. These are simulation
settings, not measured robot limits. The derivation and a numerical recovery
example are in the [guide](LQR_RL_GUIDE.md#4-where-a-b-and-the-lqr-gain-come-from).

### CARE and DARE — continuous- and discrete-time Riccati equations

The algebraic Riccati equation (ARE) is the matrix equation whose stabilizing
solution \(P\) gives the optimal infinite-horizon LQR feedback for a specified
linear model and quadratic cost. It is not the robot's nonlinear equation of
motion. CARE is the continuous-time ARE, used with \(\dot x=A_cx+B_cu\); DARE is
the discrete-time ARE, used with \(x_{k+1}=A_dx_k+B_du_k\). The corresponding
optimal gains are computed from \(P\). CARE and DARE are related through
sampling, but a sampled controller should use a model and cost consistent with
its actual sample interval; simply copying a continuous-time gain is not
generally equivalent.

**WBR example:** the default controller is sampled every 0.002 s, so its gain is
computed with DARE from the sampled MuJoCo dynamics. Changing the sample period
changes the discrete model and can change the gain. See SciPy's definitions of
[`solve_continuous_are`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_continuous_are.html)
and [`solve_discrete_are`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_discrete_are.html).

### VMC — virtual model control

Virtual model control makes a controller behave as if imagined mechanical
elements—such as a spring, damper, or virtual force at a body point—were attached
to the robot. The controller calculates the desired virtual force or torque,
then maps it through the robot's kinematics (often a Jacobian transpose) to
real actuator commands. The spring is a control rule, not necessarily a
physical spring. VMC is an intuitive way to specify a desired interaction; it
does not by itself guarantee stability, account for actuator limits, or replace
the mechanism's dynamics.

**WBR example:** a virtual spring-damper could ask the body to return upright
after a push, and the mapping would distribute the resulting wrench to wheel and
hip actuators. The current project comparison instead uses a specific LQR
baseline and PPO torque policies; do not infer that VMC is implemented in that
comparison. See the original [virtual model control paper](https://doi.org/10.1109/ROBOT.1997.620037)
and the project's [controller guide](LQR_RL_GUIDE.md).

### PPO — proximal policy optimization

Proximal policy optimization is a policy-gradient reinforcement learning method.
It gathers transitions from a policy, estimates which actions were better than
expected (advantages), then performs several minibatch updates with a clipped
probability ratio. Clipping discourages one update from changing the sampled
action probabilities too far; it is not a hard safety constraint on the robot's
torque. Action limits, termination handling, observation design, reward design,
and evaluation still matter.

**WBR example:** the action has two torque components, and evaluation compares
policies with the same simulated plant, observations, delay, lag, limits, and
disturbance protocol as the LQR baseline. A completed run is needed before
claiming that a policy learned to balance. The prior frozen direct-torque PPO
comparison completed but achieved 0/800 strict successes, while delay-aware LQR
achieved 160/160 in the assumed simulation; this result applies only to that
recipe and budget ([report](../../sim/rl/RESULTS_2026-10-20.md)). The ongoing v2
comparison has no result stated here. See the [PPO paper](https://arxiv.org/abs/1707.06347)
and [Stable-Baselines3 PPO documentation](https://stable-baselines3.readthedocs.io/en/v2.3.2/modules/ppo.html).

### Residual reinforcement learning

Residual RL trains a learned correction on top of an existing controller. A
common form is

$$
u=\operatorname{clip}(u_{\mathrm{base}}+\Delta u_{\mathrm{policy}},u_{\min},u_{\max}),
$$

where the baseline provides a useful starting behavior and the policy learns
\(\Delta u\). The final behavior still depends on the correction scale, action
limits, observations, training distribution, and baseline quality. A residual
policy can make performance worse; the baseline is not automatically a safety
shield.

**WBR example:** the v2 queue compares a direct-torque PPO arm with a
delay-aware-LQR-plus-residual arm under the declared simulation protocol. That
design is being evaluated; it is not evidence that the residual improves LQR.
The research example is Johannink et al., [Residual Reinforcement Learning for
Robot Control](https://arxiv.org/abs/1812.03201).

### \(\gamma\) and effective horizon

The discount factor \(\gamma\) (unitless, from 0 to 1) weights future reward in
the return \(G_t=\sum_{j=0}^{\infty}\gamma^j r_{t+j}\). A reward \(j\) steps
ahead is weighted by \(\gamma^j\). For \(\gamma\) near 1, a useful rough
discount horizon is \(1/(1-\gamma)\) steps; it is an interpretation of
discounting, not a hard episode length. With control interval \(T_s\) seconds,
the rough horizon in time is \(T_s/(1-\gamma)\). The e-folding time is more
exactly \(-T_s/\ln\gamma\).

**Worked example:** at 500 Hz, \(T_s=0.002\) s. For \(\gamma=0.9995\), the
rough horizon is 2,000 steps, or 4 s; for \(\gamma=0.99\), it is 100 steps, or
0.2 s. These are discount scales, not the 10 s episode limit and not a promise
that PPO will learn behavior over the whole interval. The first comparison used
\(\gamma=0.9995\); the separate v2 protocol specifies 0.99.

### VecNormalize with frozen evaluation statistics

`VecNormalize` (Stable-Baselines3) maintains running statistics to normalize
observations and, optionally, rewards across vectorized environments. During
evaluation, load the statistics saved with the trained policy and freeze
updates (`training=False`); typically disable reward normalization when
reporting physical task metrics (`norm_reward=False`). Otherwise evaluation
observations can be transformed differently from training, or the statistics
can drift as test episodes are processed. Normalization changes numerical
scaling; it does not add sensor information or improve the underlying policy by
itself.

**WBR example:** the ongoing PPO v2 protocol uses observation normalization.
Each policy must be evaluated with its own saved training statistics, frozen
for the held-out episode panel. This is evaluation procedure, not a reported
v2 outcome. See the [VecNormalize API](https://stable-baselines3.readthedocs.io/en/v2.3.2/guide/vec_envs.html#vecnormalize).

### Survival versus strict success

Survival is a narrow outcome: in this project's current v2 evaluator, an episode
survives when it runs the full horizon without a fall, displacement-limit exit,
or numerical reset. Strict success adds the task's full acceptance checks. For
example, WBR v2 requires the complete 10 s episode, no cap violation, a full
push impulse in push trials, all six true state errors inside their specified
tolerances throughout the final 1 s, and recovery within the 5 s deadline.
Thus, an upright robot can survive but fail strict success by drifting, failing
to settle, missing part of the disturbance, or exceeding an acceptance limit.
Conversely, a shortened run is not a successful disturbance-rejection trial.

This distinction is metric bookkeeping, not a result claim. Consult the
[protocol acceptance rule](../../sim/rl/protocol.json) and each experiment's
report for the exact criteria in force.

## Visual SLAM

### ORB-SLAM3

ORB-SLAM3 is a feature-based visual simultaneous localization and mapping (SLAM)
system. It detects and matches image features, estimates camera motion, and
builds or reuses a map. The library supports monocular, stereo, and RGB-D
camera configurations, with optional inertial modes when a suitable
camera-synchronized inertial measurement unit (IMU) is available. Stereo and
RGB-D provide depth information and metric scale from the calibrated sensor;
monocular vision alone has unknown absolute scale unless another source anchors
it.

**WBR example:** the current Intel RealSense D435 has no IMU, so this project
targets stereo or RGB-D mode. A camera pose is expressed in the SLAM camera/map
frames. Using it as robot-body pose also requires calibrated camera-to-body
extrinsics and careful frame/time handling; a pose message alone does not prove
tracking quality or make that transform.

Primary references: [ORB-SLAM3 paper](https://arxiv.org/abs/2007.11898) and the
[authors' implementation and examples](https://github.com/UZ-SLAMLab/ORB_SLAM3).
The local [bring-up instructions](../../ops/lab-assistant/skills/wbr-orbslam3-bringup/SKILL.md)
record the D435-specific path and current wrapper limitation.

### Keyframe

A keyframe is a selected camera image with its estimated pose and feature
observations, retained as a useful reference for tracking and map optimization.
The system does not need to store every incoming frame as a keyframe. Selecting
keyframes with useful new viewpoints and overlap helps constrain motion and
mapping. In ORB-SLAM3, co-visible keyframes can contribute observations to
bundle adjustment.

**WBR example:** while moving the D435 around a textured room, successive frames
may be tracked against nearby map features; frames with enough new information
can become keyframes. A feature-poor wall or rapid motion can weaken tracking.
See the [ORB-SLAM3 paper](https://arxiv.org/abs/2007.11898).

### Map and map points

The map is the SLAM system's persistent geometric and visual reference for
localizing later frames. In a feature-based map, map points represent estimated
3D locations associated with observed image features; keyframes store views and
poses that constrain those points. These are estimates with uncertainty and can
drift or be revised during optimization. They are not automatically a surveyed,
globally georeferenced map.

**WBR example:** a visualization of points around a room and a camera trajectory
is useful evidence that tracking and mapping are active, but it is not a metric
accuracy result. Compare against ground truth or an independent reference to
measure accuracy.

### Pose

Pose means position and orientation together. A camera pose is a rigid transform
between named coordinate frames, not just three position values; software may
report camera-in-map or map-in-camera, so check the convention. Rotation may be
stored as a matrix or quaternion. Translation uses the map's units (metric in
calibrated stereo/RGB-D operation); orientation is dimensionless but is commonly
interpreted in radians.

**WBR example:** controller state \(x\) in the planar model is not the same
thing as a six-degree-of-freedom SLAM pose. To feed camera motion to robot
navigation or control, establish the transform chain, timestamp clock, and
failure behavior. The STM32 remains responsible for balance and motor safety.

### Loop closure

Loop closure is recognizing that the camera has returned to a previously mapped
place. The SLAM system adds a constraint between the current and earlier views
and optimizes the pose/map graph to reduce accumulated drift. It is not merely
the camera following a closed visual path, and it does not guarantee zero drift
or correct recognition in every scene.

**WBR example:** revisiting a textured room region may let ORB-SLAM3 correct the
trajectory accumulated while walking around the room. Repeated-looking corridors
or poor lighting can make place recognition difficult. The [ORB-SLAM3 paper](https://arxiv.org/abs/2007.11898)
describes place recognition and multi-map reuse.

## Primary references and project guides

- [LQR and RL guide](LQR_RL_GUIDE.md) — model, units, equations, worked LQR
  example, delay and first measured comparison.
- [Parameter source table](MODEL_PARAMETER_SOURCES.md) — provenance and status
  of physical parameters.
- [PPO paper](https://arxiv.org/abs/1707.06347) and [SB3 PPO / VecNormalize
  documentation](https://stable-baselines3.readthedocs.io/en/v2.3.2/).
- [ORB-SLAM3 paper](https://arxiv.org/abs/2007.11898) and [reference
  implementation](https://github.com/UZ-SLAMLab/ORB_SLAM3).
