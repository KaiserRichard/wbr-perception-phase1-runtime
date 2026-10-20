# DIABLO: direct-drive wheeled biped

**Primary sources.** Dingchuan Liu et al., “DIABLO: A 6-DoF Wheeled Bipedal
Robot Composed Entirely of Direct-Drive Joints,” IROS 2024, [open paper on
arXiv](https://arxiv.org/abs/2407.21500); manufacturer’s [DIABLO ROS 2 SDK
repository](https://github.com/DDTRobot/diablo_ros2) (Apache-2.0); manufacturer
[product-document index](https://shop.directdrive.com/pages/list-of-product-documents).
The SDK and ROS interface are open. The paper is open access. The linked public
materials do not establish that all mechanical CAD, motor internals, or the
complete embedded balance firmware are open.

## Platform and reduced dynamics

The six-degree-of-freedom design uses direct-drive joints, with no reduction
gearboxes; the paper motivates this with reduced transmission complexity and
potentially higher bandwidth. It has a head/body, two wheel-leg assemblies,
three actuators per side, an onboard inertial measurement unit (IMU), encoders,
and a complementary-filter state estimator. A 2-D sagittal reduction treats the
legs as rods and the system as a two-link inverted pendulum on driven wheels.
The generalized positions are $q=[\gamma,\theta,x]^T$: head pitch, leg
pendulum angle, and wheel translation. Inputs are hip and wheel torques
$u=[\tau_H,\tau_w]^T$. Its linearized model is written
$a\ddot q+bq=cu$, then converted to state-space for LQR synthesis. The
controller state expands to pitch/leg angle/translation and rates plus integral
terms for head angle and position. The paper reports using DARE-based feedback
and separate height, roll, yaw, and leg-split controllers.

The ROS 2 project exposes motion commands and telemetry (including IMU, motor
positions/velocities/currents, and leg length). Its README describes a serial
interface and ROS Foxy setup; this describes the published SDK, not a verified
installation on the lab's Ubuntu/ROS release.

## Results and interpretation

**Paper-reported simulation and prototype demonstrations:** the paper shows
balance, velocity tracking, body/head tilt, leg split, and traversal behaviors.
It reports a simulation target of 2 m/s for 2 s with the modeled leg angle
within 0.5 rad and head pitch within 0.02 rad; the prototype section reports
different angle ranges. Keep those settings and evidence types separate. These
are not common-protocol comparisons against Ascento, DM-jump, or this lab's
robot. The paper's model and prototype experiments support the feasibility of
that particular architecture, not general direct-drive superiority.

## Relevance and limits

DIABLO is a useful direct-drive contrast to robots designed around geared
actuators: motor bandwidth and torque control can change the balance plant and
the value of delay/lag models. The simplified planar LQR does not by itself
cover all six mechanical degrees of freedom, wheel-ground impacts, or the full
whole-body controller. Neither its coefficients nor commercial model
specifications are measurements of the lab hardware. Reproduce only after
matching actuator semantics, state definitions, and timing; do not equate the
paper's $q$, signs, and control limits with local conventions by name alone.
