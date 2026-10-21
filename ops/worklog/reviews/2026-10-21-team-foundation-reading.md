# DM-jump foundation review and study estimate

Reviewed 21 October 2026. Upstream `main` resolved through GitHub to
`6855ef8c6da20246251cfd473467c04112bf800f`. Static source review, not a firmware
build, hardware test, safety certification or claim about who authored the code.

**Assessment:** the three packs are a sound entry to our reduced simulation and
LQR/PPO research. Calling them “most of the mathematics behind the actual WBR”
was too broad. The firmware contains further mechanics, estimation and hybrid
control. AI assistance does not remove the need to understand these interfaces.

## What the actual code does

| Layer and pinned source | Finding / implication for learning |
| --- | --- |
| [Controller helpers](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Controller/controller.c) | Advanced PID/fuzzy tuning, feedforward, linear disturbance observer and tracking differentiator are implemented. Searching all 41 User C/H files finds no calls to their public calculation/initialization entry points outside this helper library. The balancing tasks instead call `PID_Calc` from `User/Algorithm/PID/pid.c`. Presence in a folder does not establish use in balancing. |
| [Right chassis](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisR_task.c#L180) and [left chassis](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisL_task.c#L130) | Twelve feedback coefficients produce wheel torque and virtual leg torque, recomputed from a cubic table versus measured leg length. Added yaw/anti-splay/roll compensation, leg-force PID, contact/recovery branches and jump logic mean the whole controller is not simply one fixed LQR. |
| [Five-bar/VMC](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/VMC/VMC_calc.c#L36) | Joint encoders determine closed-chain geometry, virtual leg length/angle and their rates. `VMC_calc_2` maps virtual axial force and pitch torque into the two real joint torques. The virtual-work foundation becomes the Jacobian-transpose mapping here. Denominators involving leg length and linkage angles motivate workspace/singularity knowledge. |
| [State observer](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/observe_task.c#L70) and [INS](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/INS_task.c#L57) | Wheel/leg kinematics combine with inertial acceleration in a Kalman filter; position is integrated from filtered velocity. The active attitude loop calls Mahony; including the quaternion-EKF header is not evidence that the EKF supplies attitude in this loop. Noise and coordinate transforms cannot be replaced by perfect simulator state when transferring a policy. |

## Transfer limits worth knowing now

- Firmware feedback order is `[leg angle, leg rate, position error, velocity error,
  body pitch, body rate]`, with side-dependent error/sign conventions. The packs
  use `[x, theta, phi, xdot, thetadot, phidot]`. Neither column order nor an overall
  minus sign can be copied without mapping conventions.
- The firmware uses a changing five-bar leg, per-side wheel and virtual-leg
  outputs, then individual joint torques. Our planar lesson uses a fixed equivalent
  leg and aggregate pair inputs. Firmware wheel clamps are ±2 Nm per side and
  joint clamps ±7 Nm; those are not the lesson's aggregate input definitions.
- Firmware calls VMC with a nominal 3 ms interval and has three 1-tick delays in
  each chassis iteration. The observer uses a 3 ms constant. This is not evidence
  of an exact 500 Hz hardware loop; actual periods/jitter need measurement. The
  lesson's 2 ms plant/LQR tick is a separate simulation choice.
- I found the saved gain values/polynomial table, but no MATLAB/Python gain-design
  script or recoverable A/B/Q/R derivation in the upstream tree. This does not
  prove those design artifacts do not exist elsewhere. The table alone cannot
  establish optimality, stability over leg length, or parity with our new gains.
- Our delay-aware augmented LQR is a simulation comparator, not a demonstrated
  implementation of the upstream STM32 controller. No learned policy integration
  was found in the reviewed application path. Static code and README claims do
  not validate balancing, jumping or sim-to-real behaviour.

## Study time — personalized estimates, not measurements

These estimates assume the owner's EE/embedded background, prior RL exposure,
and current need to unpack virtual work. They cover derivation, worked examples,
script execution and explaining the result back, rather than passive reading.

| Pack | Focused study | Completion check |
| --- | ---: | --- |
| 1: mechanics/LQR | 10–16 h | Derive motor work and Bellman feedback; explain state order, gain units and local stability limits |
| 2: RL→PPO | 6–10 h | Calculate tiny-rollout GAE/clipping without looking; distinguish actor/critic, observations and rewards |
| 3: residual/experiment | 4–6 h | Explain effective correction after saturation, drift mechanism and a fair delay-mismatch comparison |
| Total | **20–32 h** | Approximately 2–3 weeks at 2 focused hours per study day, allowing rest/review |

A first orienting read may take 4–6 hours total; that is not derivation fluency.
Allow another 5–8 hours of spaced recall/code tracing if the goal is to retain the
material and work independently. Debugging a research implementation is extra.

**Recommendation:** retain the three packs as the first foundation. The next
bridge to this firmware should cover (1) five-bar geometry, Jacobians and VMC;
(2) length-dependent LQR gains and coordinates; (3) IMU/Kalman estimation; and
(4) contact/jump modes, saturation and actual timing. Fuzzy PID/LDOB/TD are lower
priority until a concrete experiment needs them. This review does not authorize
new lesson production, training, firmware changes or hardware deployment.
