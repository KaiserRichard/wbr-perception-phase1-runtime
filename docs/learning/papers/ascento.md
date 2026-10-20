# Ascento: a two-wheeled jumping robot

**Primary source.** Victor Klemm et al., “Ascento: A Two-Wheeled Jumping Robot,”
ICRA 2019, [arXiv paper](https://arxiv.org/abs/2005.11435),
[ETH Research Collection PDF](https://www.research-collection.ethz.ch/server/api/core/bitstreams/be65ada4-fd2b-47d8-a97c-a7591183749e/content).
The paper is openly readable. It describes the prototype and controller, but
does not establish that a complete CAD, bill of materials, or firmware release
is available; do not treat the paper as a reproducible hardware package.

## Mechanism and model

Ascento has two independently driven wheels on extendable legs. A three-bar
linkage makes wheel motion approximately vertical; the design aims to pass that
motion through the center of mass so leg extension perturbs body pitch less.
Parallel torsion springs offset weight and reduce hip-motor effort. The reported
height range is 31–66 cm. For balance control, the paper fixes leg geometry at a
chosen height and reduces the robot to two wheels plus one equivalent inverted
pendulum. Rigid-body kinetic and potential energies form the Lagrangian
$\mathcal L=T-V$; constrained equations are
$\frac{d}{dt}(\partial\mathcal L/\partial\dot q)-\partial\mathcal L/\partial q =J^T c$, where $q$ are generalized coordinates, $J$ maps generalized
motion to contact coordinates, and $c$ contains applied forces/torques.
Parameters are reported as measured component masses plus CAD-derived inertias
under a constant-density assumption.

## Control and evidence

Stabilizing/driving uses a discrete linear-quadratic regulator (LQR):
$u=-K(\hat h)\hat x$, with $\hat x=[\theta,\dot\theta,v,\omega]^T$,
and $u$ the left/right wheel torques. Position is handled outside the LQR by
velocity setpoints. Ten linearizations at evenly spaced leg heights provide
gains interpolated by estimated height. The gains' diagonal state/input weights
were tuned through tests on the prototype; this is a source description, not an
independent reproduction of their tuning.

Jumping is a phase sequence, not simply the balance LQR: retract legs while
balancing, accelerate, trigger leg extension from time-of-flight range, extend
with synchronized proportional-integral-derivative (PID) control, use a
position-controlled virtual spring-damper in flight, then detect landing from
hip torque and resume stabilization. Fall recovery is another sequence.

**Paper-reported prototype evidence:** 10 cm step ascent; the authors report
about 90 cm clear approach and landing space, maximum jump height 0.4 m, maximum
linear speed 8 km/h, and a 10.4 kg robot. These are platform-specific reported
figures, not matched benchmark trials. The jump controller's dependence on
available run-up and discrete phases matters when comparing with continuous
balance policies.

## Relevance and limits for this lab

The useful design lesson is a separation of fast wheel balance from leg/jump
phases, plus height-scheduled feedback when geometry changes. The fixed-height
linearization omits the dynamics during leg motion; gain interpolation only
approximates that variation. The paper tests its own prototype and sensing stack.
Its parameters, gains, actuator response, contact behavior, and jump results
cannot be transferred to the lab robot without identification. The current
assumed MuJoCo model has neither articulated five-bar legs nor jump/contact
transitions, so it represents only a narrower balance question.
