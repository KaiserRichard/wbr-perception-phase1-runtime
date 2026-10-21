# DM-jump foundations and study time

21 October 2026 · [Publication PR105](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/105)
Upstream main: `6855ef8c6da20246251cfd473467c04112bf800f`.
Static review; no firmware build, hardware test or authorship judgment.

**Assessment:** the three packs support reduced-model simulation and LQR/PPO
research. Calling them “most of the actual WBR mathematics” was too broad.

## What the source actually does

| Pinned source | Finding and missing foundation |
| --- | --- |
| [Controller helpers](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Controller/controller.c) | Advanced PID/fuzzy, feedforward, disturbance-observer and tracking-differentiator helpers exist. Across all41User C/H files, their public initialization/calculation functions have no external call sites. Balance instead calls `Algorithm/PID/pid.c::PID_Calc`. Library presence does not establish use. |
| [Right chassis](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisR_task.c#L180), [left chassis](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisL_task.c#L130) | Twelve feedback gains vary with leg length through cubic polynomials. Wheel/virtual-leg feedback combines with yaw, anti-splay, roll, leg-force PID and contact/jump branches. This requires gain scheduling and hybrid-control foundations. |
| [VMC](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/VMC/VMC_calc.c#L36) | Encoder angles determine five-bar geometry and leg length/angle/rates. `VMC_calc_2` maps axial force and virtual pitch torque to real joint torques. This extends the packs' virtual-work idea into Jacobian-transpose force mapping, workspace and singularities. |
| [Observer](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/observe_task.c#L70), [INS](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/INS_task.c#L57) | Wheel/leg kinematics and inertial acceleration feed a Kalman filter; position integrates filtered velocity. Active attitude updates call Mahony. Including an EKF header does not establish its use here. Coordinate transforms, estimation and noise need further study. |

## Transfer limits

- Firmware feedback order is `[leg angle, leg rate, position error, velocity error,
  body pitch, body rate]`, with side-dependent signs; the packs use a different
  order. Its translational observer also includes leg-motion terms, whereas the
  lesson defines x at the axle: physical coordinate equivalence needs checking,
  not merely column reordering. Gains/signs cannot be copied without that mapping.
- Firmware has changing five-bar legs, per-side virtual outputs and real joint
  torques. Packs use a fixed equivalent leg and aggregate pair inputs. Firmware
  wheel/joint clamps (±2/±7Nm) are not the lesson's aggregate limits.
- VMC uses nominal3ms; chassis iterations include three1-tick delays; observer
  uses3ms. These constants do not prove actual loop frequency/jitter. The lesson's
  2ms plant/LQR tick and delay-aware augmentation are separate simulation choices.
- Saved gains/polynomials are present; no MATLAB/Python gain-design script or
  recoverable A/B/Q/R derivation was found in the upstream tree. Artifacts may
  exist elsewhere. Optimality/stability cannot be verified from a gain table alone.
- No learned-policy integration was found in the reviewed application path.
  Static code/README claims do not establish balancing, jumping or sim-to-real success.

## Personalized estimate

Active study means derivations, worked examples, running scripts and explaining
results back—not passive reading. Estimates reflect the owner's EE background,
previous RL exposure and current questions about mechanics.

| Pack | Focused hours | Completion check |
| --- | ---: | --- |
| 1: mechanics/LQR | 10–16 | Derive virtual work/Bellman feedback; explain gain units and local stability |
| 2: RL→PPO | 6–10 | Compute GAE/clipping; distinguish actor, critic, observation and reward |
| 3: residual/experiment | 4–6 | Explain saturation, drift and fair delay-mismatch evaluation |
| **Total** | **20–32** | Roughly2–3weeks at2hours per study day, allowing review/rest |

First orientation:4–6hours. Optional spaced recall/code tracing: another5–8hours.
Research implementation/debugging is extra; these are estimates, not measurements.

**Recommendation:** retain the packs as the first foundation; bridge next to
five-bar/VMC, length-dependent gains/coordinates, estimation, and contact/timing.
Fuzzy PID/LDOB/TD can wait until an experiment actually needs them. No new lesson,
training, firmware change or hardware deployment is authorized by this review.

**Verification:** pinned source/task/call-site inspection; `git diff --check`.
Reproduction notes and limitations: session2026-10-21-team-foundation-reading.md.
