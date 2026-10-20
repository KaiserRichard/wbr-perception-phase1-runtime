# Session 2026-10-20 10:35 +07: simulation/control inventory

Agent: Codex. Mode: Simulation / control. Status: documentation audit reviewed; publication in progress, implementation not started.
Branch: chatgpt/20261020-simulation-control. Base commit: 6929fb4.

Latest update, 2026-10-20 10:53 +07: owner supplied DM-jump controller source. The audit below identifies its six-state/two-output scheduled feedback. Earlier UNKNOWN inventory describes the initial local search; it is superseded where the new source supplies values. No hardware parameters have become MEASURED, and the earlier four-state scope has not been implemented.

## Goal (owner request)
Locate or build a MuJoCo WBR model, reproduce the linear quadratic regulator (LQR) balance baseline, then prepare a reinforcement learning (RL) comparison. All results must be labeled SIMULATION; no hardware deployment is authorized.

## Loaded state and rules
- Read AGENTS.md, CURRENT.md, all six existing DECISIONS.md entries, latest lab session, reviews/README.md, RESEARCH_RULES.md, PROJECT_STATE.md and NEXT_GATE.md.
- No review request files exist at session start; reviews/ contains its README only.
- MEASURED: origin/main is 6929fb4, PR #35; working tree was clean before starting this branch.
- SOURCE-SUPPORTED: main's RESEARCH_RULES.md has no "Simulation and learned control" section yet. The owner-requested section exists in OPEN PR #36, head cdfb4c056fa6c50195391ec87ec81f3f64e566dd; reviewed through GitHub API without checking out its code. CI was in progress when inspected.
- Read PR #36's proposed USER_PROFILE.md. Applying the requested simulation protocol: LQR first, fair actuator/rate/observation/disturbance conditions, predeclared metrics, at least five RL training seeds, retained failures and confidence intervals.

## Existing architecture and search scope
- SOURCE-SUPPORTED: this repository is a perception/runtime workspace. README and RESEARCH_RULES assign hardware balance/LQR/VMC/safety to STM32H7 and perception to the Pi.
- Searched tracked paths and local filenames/content for MuJoCo/MJCF/URDF/Xacro/MATLAB models, LQR/Riccati code, masses, inertias and geometry. No WBR physical model or numerical LQR implementation found in this checkout.
- Also searched /Users/quockaiser/Desktop/Research/{docs,config,scripts,wbr-data,wbr-sw-foundation} for relevant filenames; searched docs/config/scripts contents for model/controller terms. No matching source found in those searches. This does not establish absence from other repositories or unshared files.
- tools/link_bench/firmware is communication-benchmark firmware, not a balance controller.

## Initial local inventory (historical, before DM-jump was supplied)
This table records the initial local search only. The current inventory is in the DM-jump audit below: upstream gain schedule, state map, geometry constants, command clamps and nominal timing are now SOURCE-SUPPORTED. Physical verification and original synthesis remain unavailable.
| Input | Status in inspected material |
|---|---|
| WBR CAD, URDF or MJCF model and provenance | UNKNOWN; not located |
| Body/link/wheel masses and inertia tensors | UNKNOWN |
| Wheel radius/track width, leg geometry and joint axes/limits | UNKNOWN |
| Center of mass and balance operating pose/leg height | UNKNOWN |
| Motor gearing, torque/speed limits, damping/friction and delay | UNKNOWN |
| State ordering, frames, units, signs and input convention | UNKNOWN |
| Linearized A/B matrices and equilibrium | UNKNOWN |
| Q/R weights, K gains and continuous/discrete design convention | UNKNOWN |
| Control/sample period, observer, saturation and existing recovery traces | UNKNOWN |
| Runtime ownership boundary | SOURCE-SUPPORTED: STM32 owns hardware balance; no hardware changes |

## Decisions and next steps
- Initially the owner reported mechanical/controller sources unavailable. The owner subsequently supplied DM-jump; its source audit supersedes those unavailable-controller claims. The flashed revision, physical parameters and original gain synthesis still need lab confirmation.
- Do not invent numeric physical parameters or claim reproduction of an unavailable controller.
- Owner authorizes scoping an explicitly ASSUMED wheel-legged inverted-pendulum teaching model and deriving a new LQR baseline, with one config file for replaceable parameters (D-20261020-6).
- Owner relayed Claude approval of the two-stage source-informed scope: reduced planar six-state model for parity/re-synthesis, then full planar five-bar MuJoCo/VMC. Four-state scope stays archived. No model has been implemented.
- After a model is agreed: validate its physics/signs/units; reproduce or explicitly derive an LQR; evaluate recovery and saturation; only then prepare a matched RL comparison.
- No model implementation, dependency installation, controller run or RL training performed yet. No claim that RL outperforms LQR.

## Parallel lab task carried forward
- USER-REPORTED: 32 GB microSD imaging is running on brother's Windows computer at about 8.5-8.8 MB/s; image D:\wbr-backup\wbr-pi5-32gb-20261020.img. Completion/byte verification UNKNOWN.
- USER-REPORTED: D: is NTFS with 68.3 GB free. Disk enumeration showed 29.12 GiB USB device; card reader later used in Win32 Disk Imager. Prior Windows volume queries timed out even without reader; cause UNKNOWN.
- Mac SSH alias wbr-pi5 now resolves to richard@192.168.50.2 (configuration verified, live connectivity not retested after card removal).

## Current source-informed scope (two stages approved; implementation not started)
- Stage 1: reduced planar six-state model for gain parity and explicitly new LQR synthesis. Stage 2: full planar five-bar MuJoCo with VMC. Architecture approval relayed by owner; see D-20261020-10. Original LQR Q/R/dynamics remain unavailable.
- Required parity milestone compiles pinned upstream C gain-schedule/VMC functions locally, with a host-only harness and shared C/Python vectors; record compiler/version/options, float semantics, tolerances and fixtures. Formula-to-formula agreement alone is insufficient.
- Target the source's six-state feedback per leg: virtual-leg angle/rate, estimated body displacement/velocity error and body pitch/rate, with mirrored left/right signs. Outputs are wheel torque and virtual hip torque Tp, with a separate axial-force/height channel.
- First milestone is source-parity math and fixtures: exact cubic scheduling, state mapping, per-step PID semantics, VMC, output clamps and intentional source differences. A replayable feedback map can be tested before physical masses are known.
- For the first physics model, propose fixed virtual-leg LENGTH with independent leg orientation and body pitch; do not weld the leg orientation to the torso. Preserve motor reaction torque. Five-bar length dynamics, VMC realization and estimator/timing fidelity are later explicit stages, not silently omitted reproduction claims.
- One human-edited config, proposed `sim/configs/wbr_balance.json`, contains upstream commit/provenance, source gain coefficients and conventions, and all replaceable physical/numerical/evaluation parameters. Source constants carry SOURCE-SUPPORTED and pinned file/line references; unknown physical choices carry ASSUMED and honest design-choice provenance; derived values carry CALCULATED and their inputs.
- Use the source wheel radius 0.0603 m and linkage geometry as code-supported model inputs when relevant, without relabeling them as physical measurements. Keep masses/COM/inertias, motor dynamics and contact/timing uncertainty explicit. Q/R for any new controller must be declared new choices; the upstream LQR Q/R were not found.
- Compare upstream feedback on the assumed plant before tuning. Failure establishes model/controller incompatibility, not that the original robot controller is defective. Keep any corrected or newly synthesized controller separate from the source-parity reference.
- Proposed package responsibilities remain config/model/controller/evaluation/tests, with a pure `controller_reference.py` for upstream semantics and `lqr.py` only for explicitly new synthesis. No code paths or files have been created.
- Validation order: source parity -> physics/equilibrium/signs -> closed-loop compatibility and saturation -> timing/estimator uncertainty -> fair RL comparison. All dynamics results remain SIMULATION; no hardware deployment is authorized.
- Risk and rollback: six-state/contact mapping, physical assumptions and source defects can invalidate reproduction. Keep work isolated on this branch; preserve every failed run and intentional deviation. Roll back a later implementation through its small commits without touching perception or firmware.

## Archived four-state teaching-model proposal (unimplemented, not current recommendation)
This earlier scope is retained as history and an optional lesson. It is not an approved DM-jump model, and its arbitrary values are not current source-informed parameters. Use the current scope and audit above/below when deciding next work.

### Scope and current architecture
- At initial inspection, this local repository was perception/runtime tooling; no simulation package, mechanical model or balance controller was found in this checkout. DM-jump was supplied later.
- Add an isolated Python package under sim/, without coupling to ROS, Pi runtime, STM32 or motors.
- First plant: planar, fixed-height wheel-legged inverted pendulum, two symmetric driven wheels, legs locked rigidly and their mass lumped with the body. This models sagittal balance, not actively articulated legs, yaw, jumping or rough terrain.
- Preserve wheel/body motor reaction torque via wheel-hinge actuators and actual ground contact. Do not substitute a cart-pole world-force actuator and call it wheel torque.
- World frame: +x forward, +y lateral, +z up; pitch around +y, positive forward lean. State contract: [axle_x_m, axle_vx_m_s, pitch_rad, pitch_rate_rad_s].
- Scalar action is TOTAL axle torque in N m; each wheel receives half. Initial total bound is +/-4 N m (equivalent +/-2 N m per wheel), explicitly ASSUMED.
- MuJoCo retains vertical/contact/wheel states internally. Initialize reduced-state rollouts consistently with rolling, including wheel relative rate approximately vx/r - pitch_rate; verify this sign in tests.
- Derive the discrete control-period linearization from the complete, consistently initialized MuJoCo rollout. Do not simply slice its full-state Jacobian. Check perturbation-size convergence and reduced-model prediction; if four-state reduction fails, stop and propose the necessary state extension rather than silently claiming a valid four-state model.
- Use ideal simulator state observations initially for both LQR and future RL. Sensor noise/delay are zero in the nominal model and explicitly ASSUMED omissions, later tested as perturbations.

### One human-edited config
- Proposed config: sim/configs/assumed_wbr.json. Each parameter carries value, unit, status and source; source for chosen values is "agent-selected teaching-model assumption; not measured, not from CAD or a hardware datasheet". No fabricated literature provenance.
- Geometry/mass, contact/numerical settings, torque limit, control period, Q/R, initial conditions and evaluation cases all live in this file. Code refuses missing provenance, invalid inertia or inconsistent timing.
- Generated MJCF, A/B/K and effective config are run artifacts; there is no second manually maintained numeric model file.
- Values inferred from assumed primitives remain explicitly dependent on those assumptions. Derived inertia/gains are labeled CALCULATED, with formulas and config hash; never MEASURED hardware data.
- Replacement guarantee is limited to scalar parameters within this topology. Real articulated CAD, additional actuators or a different state/input convention may need a reviewed model change.

| Proposed parameter | Value | Unit | Status | Source |
|---|---:|---|---|---|
| Body including lumped locked legs | 5.0 | kg | ASSUMED | Teaching-model design choice; no real mass known |
| Body box full dimensions x/y/z | [0.24, 0.18, 0.12] | m | ASSUMED | Teaching-model primitive shape, not CAD |
| Body center of mass above wheel axle | 0.28 | m | ASSUMED | Teaching-model fixed pose, not measured leg length |
| Wheel mass, each | 0.30 | kg | ASSUMED | Teaching-model design choice |
| Wheel radius | 0.07 | m | ASSUMED | Teaching-model design choice |
| Wheel width | 0.03 | m | ASSUMED | Teaching-model design choice |
| Wheel center-to-center track | 0.32 | m | ASSUMED | Teaching-model design choice; yaw/roll constrained |
| Gravity magnitude | 9.81 | m/s^2 | ASSUMED | Nominal Earth-gravity setting, not site measurement |
| Sliding friction coefficient | 0.8 | dimensionless | ASSUMED | Nominal contact assumption, not tire identification |
| Total axle torque clamp | 4.0 | N m | ASSUMED | Symmetric +/- limit; no motor data available |
| Physics timestep | 0.002 | s | ASSUMED | Proposed numerical setting; sensitivity to be tested |
| Control period | 0.010 | s | ASSUMED | Proposed 100 Hz teaching controller, not STM32 rate |
| Nominal sensor delay/noise | 0 | s / state-dependent units | ASSUMED | Ideal sensing assumption; not measured |
| Evaluation duration | 10 | s | ASSUMED | Predeclared teaching-test duration |

- CALCULATED homogeneous-box inertias about its COM: [0.0195, 0.0300, 0.0375] kg m^2, from m/12 times sums of squared perpendicular full dimensions.
- CALCULATED solid-cylinder wheel inertia: axial 0.000735 kg m^2, transverse 0.000390 kg m^2, from 0.5*m*r^2 and m*(3*r^2+w^2)/12. These calculations do not validate the assumed shapes.
- Remaining contact solver settings, joint damping/armature, Q/R weights, fall/recovery criteria and perturbation magnitudes must be explicit labeled config entries before any run; they will not be hidden library defaults or presented as hardware limits.

### Affected modules and responsibilities
Proposed paths (none implemented yet):
- sim/README.md: assumptions, conventions, setup/run/test instructions, limits and sources.
- sim/requirements.txt: baseline dependency pins only, isolated from existing runtime tools.
- sim/configs/assumed_wbr.json: single replaceable configuration with provenance.
- sim/wbr_balance/config.py: validation and config hashing.
- sim/wbr_balance/model.py: parameter-to-MJCF generation, loading, consistent reset/state mapping, torque action and control-period stepping.
- sim/wbr_balance/lqr.py: operating point, finite differences, discrete Riccati design, gains and stability diagnostics.
- sim/wbr_balance/evaluate.py and __main__.py: bounded episodes, disturbances, metrics and argparse entry point, with an explicitly supplied output path.
- sim/tests/: nonempty stdlib unittest suite; current tools/run_all_tests.sh does not automatically discover root sim/ tests. Any CI integration change is a separate reviewed change.
- Only ops/worklog/ has changed during scoping. No runtime, ROS interfaces or firmware changes are proposed.

### Test plan and reproduction contract
Proposed commands after architecture approval and dependency setup (NOT executed):
```sh
/usr/local/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -r sim/requirements.txt
.venv/bin/python .github/run_unittest.py sim/tests
.venv/bin/python -m sim.wbr_balance --config sim/configs/assumed_wbr.json --out /private/tmp/wbr-sim-lqr-run-01
```
- Model validity: positive masses, positive physically valid inertias, consistent dimensions/units, torque conventions and an integer number of physics steps per control step.
- Physics: stationary upright equilibrium, symmetric uncontrolled fall under small signed tilt, expected wheel/body torque reaction, plausible rolling and contact support.
- Linearization: compare multiple perturbation sizes, reduced-state prediction against nonlinear rollouts, controllability and discrete closed-loop eigenvalues inside unit circle before saturation.
- Closed-loop evaluation: predeclared signed initial tilts (proposed +/-1, +/-3 and +/-5 deg), plus a separately specified repeatable push. Retain failed episodes and saturation counts; no automatic retuning to hide failures.
- Numerical sensitivity: halve timestep while retaining controller period and compare representative trajectories/metrics. Repeat identical config/seed to assess reproducibility.
- Metrics: success/fall and recovery time, peak tilt, position/speed error, integral squared applied torque and peak torque, saturation fraction, rollout time and relevant host/software versions. RL later receives identical observations/actions/rates/conditions with at least five training seeds and held-out evaluation cases.
- Expected output: new-folder SIMULATION result and trajectory, effective labeled config and generated model, config/model hash, A/B/Q/R/K, equilibrium, eigenvalues, source commit plus dirty-source receipt if needed, versions, command, conditions and failure reasons. No checkpoints or videos in git.
- Failure symptoms: no equilibrium, wrong torque sign, slipping/reset transients, derivative instability, uncontrollability, Riccati failure, unstable closed-loop modes or saturated/falling episodes. Report the first failed validation; do not claim a reproduced baseline or start RL.

### Runtime inventory, risks and rollback
- MEASURED by read-only runtime check: stable Python 3.12.13 exists at /usr/local/bin/python3.12; MuJoCo, SciPy and RL packages are absent. Default python3 is Python 3.11.0rc2 with NumPy 1.26.4. No dependencies installed.
- Use an isolated Python 3.12 venv, baseline NumPy/SciPy/MuJoCo only. Defer Gymnasium/Stable-Baselines3 until LQR validation.
- Risks: reduced-order model/contact mismatch, misleading assumptions, saturation and derivative numerical errors. No conclusion about the real WBR follows from nominal simulation.
- Rollback: scope currently touches worklog files only. A later simulation implementation remains isolated under sim/ on this feature branch; reverting its small commits can remove it without changing perception/firmware. Preserve run failures and logs.

### Primary implementation references
- MuJoCo model/actuator reference: https://mujoco.readthedocs.io/en/stable/XMLreference.html
- MuJoCo simulation/derivative APIs: https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html
- SciPy discrete algebraic Riccati solver: https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_discrete_are.html
- These references support implementation mechanisms; none supplies this robot's parameter values.

## Earlier sim-to-real discussion (historical recommendation, not deployment approval)
- Owner asks whether sim-to-real is the most important issue and requests a beginner-accessible direction. Proposed priority: learn/validate the assumed-model pipeline now; obtain credible model/actuator/observation/timing evidence before making transfer claims.
- The assumed model is a teaching baseline. Neither an attractive animation nor an RL advantage on this model establishes transfer to the physical WBR. Update after source audit: upstream gains and command semantics are recovered; actual flashed implementation, physical parameters and original synthesis remain UNKNOWN.
- Earlier discussion proposed a locked-leg teaching baseline followed by calibration and robustness tests. The current recommendation now starts with the source-informed six-state feedback contract above. Validation against separately approved physical traces, held-out comparisons and a separately reviewed deployment plan remain necessary for later transfer claims.
- Request from lab: mechanical topology/locked-leg pose, masses/COM/inertias, wheel geometry, motor interface (current/torque/velocity), torque-speed/current limits and delay, state estimator/axes/units/filtering, sample period/jitter, baseline gain/state order and representative time-aligned logs.
- First transfer priorities for balance are hypothesized to be body inertia/COM, actuator response/saturation, observation conventions/filtering/delay, control timing and contact/slip. Verify sensitivity rather than assume their relative importance for this robot.
- Domain randomization means training/evaluating across a declared distribution of uncertain model parameters. Choose ranges from measurements/identification uncertainty; arbitrary ranges do not repair missing physics or guarantee transfer. Evaluation includes held-out combinations and failure/saturation reporting.
- Illustrative timing calculation only: at a 100 Hz control period, an assumed 20 ms delay is two control periods. These are teaching values, not measured WBR timing.
- If later comparing residual RL, define u=clip(u_LQR+delta_u_RL) with a declared correction bound and identical final actuator limits. A residual controller is not automatically safe and can destabilize a stable baseline. Its use is only a proposal until comparison architecture is approved.
- Keep RL observations available on the real robot; privileged simulator state used as a baseline must be declared, and must not give only one compared controller extra information.
- SOURCE-SUPPORTED: Peng et al., Sim-to-Real Transfer of Robotic Control with Dynamics Randomization, ICRA 2018, https://arxiv.org/abs/1710.06537 (robotic manipulation evidence, not WBR evidence).
- SOURCE-SUPPORTED: Chebotar et al., Closing the Sim-to-Real Loop: Adapting Simulation Randomization with Real World Experience, 2019, https://arxiv.org/abs/1810.05687 (uses real rollouts to adapt simulation distributions; no WBR transfer claim).
- No new model code, RL training, dependency installation or hardware action in this discussion. No model architecture is approved; the current source-informed proposal supersedes the earlier four-state recommendation.

## DM-jump controller source audit, 2026-10-20 10:53 +07

### Provenance, scope and limits
- Owner supplied https://github.com/nguyenbinh-shark/DM-jump and its User/Controller folder, asking for thorough study.
- Pinned upstream main: 6855ef8c6da20246251cfd473467c04112bf800f, commit date 2026-09-12T15:39:25Z. The lab's flashed commit is UNKNOWN.
- Downloaded 51 application/core/build/mechanical-note source files, 465410 bytes, into /private/tmp/wbr-dm-jump-audit-6855ef8. Auditors also inspected a full clone at /private/tmp/wbr-dm-jump-audit-runtime-20261020.
- Source manifest: audit-source-manifest.json, SHA-256 bc61c855177c51c4799dd864d9b3ffcc772d2f3d7f6578deaf102ffcbfc91206.
- Arithmetic receipt: calculated-checks.json, SHA-256 c33843c8a62e977020df8cf31ba3a925f41a53cbfd63dfd24a054382cb147572.
- These snapshots are temporary caches, not committed evidence data. Pinned upstream links and the numeric checks below preserve the audit's reproducible source reference. Source was read, not built/flashed/executed on a robot. No hardware control command was sent.
- Labels: implementation facts are SOURCE-SUPPORTED; independent arithmetic is CALCULATED; possible runtime consequences are INFERRED until tested.

### Main conclusion and architecture
- The linked User/Controller folder is a generic fuzzy PID/feedforward/disturbance-observer/tracking-differentiator library. Application-call search finds no use of those controller APIs in the chassis baseline.
- The baseline is implemented in User/APP/chassisR_task.c and chassisL_task.c, User/Algorithm/VMC/VMC_calc.c, and the distinct User/Algorithm/PID/pid.c.
- Source flow: BMI088 -> Mahony INS -> shared attitude/gyro; wheel/leg kinematics + acceleration -> velocity KF -> integrated position; per-leg feedback -> cubic gain schedule -> wheel torque and virtual hip torque; height PID/gravity and roll compensation -> axial force; virtual force/hip torque -> VMC Jacobian -> two joint torques; source clamps -> staggered torque-mode CAN commands.
- Leg theta and body pitch are separate states. A rigidly welded leg/body four-state plant cannot reproduce this two-output six-state feedback by copying its gains.
- A source-informed alternative would retain independent virtual-leg angle and body pitch (six-state balance, wheel and hip inputs), initially at fixed leg LENGTH, later adding five-bar length/VMC dynamics. This differs from rigidly locking leg ORIENTATION to the body. This is a proposal, not an approved/implemented model change.

### Exact feedback contracts
For right leg:
```text
e_R = [theta_R, dtheta_R, x_filter-x_set, v_filter-v_set, Pitch, Gyro[0]]
theta_R = pi/2 - Pitch - phi0_R
dtheta_R = -Gyro[0] - dphi0_R
```
For left leg:
```text
e_L = [theta_L, dtheta_L, x_set-x_filter, v_set-v_filter, -Pitch, -Gyro[0]]
theta_L = pi/2 + Pitch - phi0_L
dtheta_L = +Gyro[0] - dphi0_L
```
- State units: rad, rad/s, m, m/s, rad, rad/s. x_filter is integrated estimated body forward velocity, including leg/gyro kinematic compensation, not simply raw wheel travel or an unqualified axle coordinate.
- Each leg computes wheel_T=sum(K[0:6]*e) and Tp=sum(K[6:12]*e). The coefficients already contain signs; inserting a further generic minus changes the implemented law.
- Left/right signs, joint encoder offsets phi1/phi4=pi/2+encoder_position, and mirrored actuator mapping must be preserved explicitly in any port.
- INS.Pitch is assigned mahony.roll and pitch rate uses gyro index 0; INS.Roll is mahony.pitch. MuJoCo axes cannot be equated by variable name alone. Declared -2 deg pitch-offset macros have no usage in the inspected application code.
- State definitions: [R feedback/control][DM-R], [L feedback/control][DM-L], [VMC][DM-VMC], [INS][DM-INS], [observer][DM-OBS].

### Gains: recovered schedule, not original synthesis
- Both initialized 12-value gain arrays are overwritten every control iteration.
- Twelve shared polynomial rows in chassisR_task.c:29-42 define Ki(L0)=a3*L0^3+a2*L0^2+a1*L0+a0; runtime evaluation R184-187, L135-138; evaluator VMC225-227. Scheduling uses each leg's computed L0, not a fixed global height.
- CALCULATED at L0=0.08 m, evaluating the committed coefficients with Python double arithmetic:
```text
Kwheel = [-2.991299182, -0.281341094, -2.019484978, -1.769854125, 4.447751542, 0.369570803]
KTp    = [ 2.124713169,  0.217028212,  2.117582585,  1.757675935,17.944879119, 0.549361960]
```
- CALCULATED at L0=0.12 m:
```text
Kwheel = [-3.957434394, -0.426178154, -2.153433448, -1.885504230, 3.036663545, 0.303526434]
KTp    = [ 1.737066795,  0.188598879,  1.373700155,  1.112688642,19.371249470, 0.634647600]
```
- Also evaluated at L0=0.16 and 0.21 m; receipt holds all four matrices. These are not ARM float32 parity results, physical performance measurements or proof of the schedule's validity over that range.
- UNKNOWN: plant A/B, LQR Q/R, equilibrium/model convention used for synthesis, continuous/discrete design, synthesis period, fitting script, parameter provenance and fit-validity interval. Observer matrices named Q/R are Kalman noise covariances, not LQR costs.
- We can reproduce the implemented feedback map; we cannot yet reproduce the original optimal-control derivation or establish its robot performance.

### Source-supported parameter inventory
| Parameter | Code value | Evidence/interpretation |
|---|---|---|
| Five-bar links l1,l4 | 0.075 m | VMC_init; geometry constants, not verified CAD dimensions |
| Five-bar links l2,l3 | 0.14 m | VMC_init |
| Base pivot spacing l5 | 0.08 m | VMC_init |
| Wheel radius used by observer | 0.0603 m | observe_task.c:74,78; replaces an arbitrary radius only for a source-informed model |
| Leg command range | 0.060 to 0.21 m | PS2 leg setpoint clamps; PS2 target itself 0.08 to 0.21 m |
| Wheel torque clamp | +/-2 N m per wheel | R212/L157, after yaw compensation |
| Joint torque clamp | +/-7 N m per joint | R248-249/L193-194, after VMC mapping |
| Axial force clamp | +/-100 N per leg | R244/L188 |
| Leg PID | Kp=700, Ki=0, Kd=2500, max output=130 | VMC_calc.h:30-34; final F0 still capped at100 |
| Gravity compensation constant | Mg=17.658 N | chassisR_task.h:52; used on BOTH legs, not a measured total weight |
| Anti-splay PID | [10,0,0.1], cap2 | chassisR_task.h:32-36 |
| Yaw direct PD | 2*(yaw_set-yaw)-0.2*Gyro[2] | R190; direct formula bypasses the initialized PID output cap |
| Roll P | 100, output cap100 | chassisR_task.h:46-50 |
| Protocol torque ranges | joint +/-10, wheel +/-18 N m | Driver encoding ranges, not active controller limits or measured motor capability |
- Mg/9.81=1.8 kg is only a CALCULATED force equivalent per application of this constant; neither 1.8 kg total mass nor 3.6 kg total mass is established.
- UNKNOWN: actual body/link/wheel mass and COM/inertia, track width, transmission ratio/efficiency, motor torque-speed curve/bandwidth/friction/delay, contact properties. docs/mechanical/shaft_analysis_notes.md is textbook shaft/flywheel analysis, not a WBR CAD/inertia model.

### Timing and estimation: source versus measurement
- RTOS tick configured 1000 Hz. INS uses DWT elapsed time and osDelay(1); calling this an achieved 1000 Hz measurement is unsupported.
- Each chassis iteration contains THREE osDelay(1) calls, one after each joint/joint/wheel command. VMC is explicitly passed 0.003 s; nominal scheduling assumption is about333 Hz per leg with staggered actuator updates, not a simultaneous 1000 Hz torque vector.
- Observer uses OBSERVE_TIME=3 ms and fixed0.003 KF transition plus position integration. README's 500 Hz observer claim does not match this code.
- INS task is highest priority and transmits diagnostic text every20 ms using blocking HAL_UART_Transmit(...,HAL_MAX_DELAY) at115200 baud. INFERRED: serialization can delay lower-priority control; VMC/observer still use fixed dt. Actual periods, jitter and input-to-torque latency are UNKNOWN.
- Actual attitude filter calls Mahony. EKF update function has no application caller found; compiled presence is not execution evidence.
- Observer uses velocity/acceleration Kalman state and separately integrates position. Left/right wheel rates include gyro and leg angular/length rate terms; preserve these if testing the source estimator.
- Source main initializes BMI088 with hspi2 and DWT_Init(480); README says SPI1/550 MHz. Resolve against actual hardware and RCC/DWT calibration before timing claims; do not assume README values.

### Porting and implementation findings
1. Active leg PID computes integral+=Ki*error and derivative=Kd*(error-error_previous), without dt factors (pid.c:74-89). At an assumed3 ms, Kd2500 corresponds to7.5 against continuous error-rate only under that fixed-step equivalence; direct reuse as a continuous Kd is incorrect. Keep source-parity and redesigned PID separate.
2. VMC_calc.h describes the leg PID cap130 as torque; usage adds its output to F0, a force. Signal flow/dimensional analysis contradicts that comment.
3. UART parser stores uart_cmd values, but UART_Control_Task is an empty delay loop. No forwarding of those parsed commands to chassis was found. Its documented host-control functionality is not implemented in this snapshot.
4. PS2_data_process sets start_flag=1 on every call before START handling. INFERRED from source: stop can be undone on the next PS2 update and the ordinary start/recovery condition requiring flag0 is bypassed. This deserves a separate firmware review; no hardware test or fix performed.
5. Stop path sends zero feedforward torque with zero damping, rather than invoking the driver's disable function.
6. Ground detector estimates FN=F0*cos(theta)+Tp*sin(theta)/L0+6 from commanded virtual forces and declares airborne at FN<5. It does not read measured contact/motor torque; INS argument is unused. Keep simulator truth for evaluation separate from this estimated detector.
7. Jump transitions use length thresholds and cumulative counters; no distinct contact-validated soft-landing stage or phase timeout found in the examined jump functions.
8. VMC forward solve and Jacobian contain square roots/divisions without explicit domain/finite/singularity guards. Numeric invalidity is not repaired by ordinary min/max comparisons.
9. Shared INS/chassis/leg structs are read/written by multiple tasks without a coherent timestamped snapshot. Timing/state age must be established before claiming synchronized observations.
- These are code-reading results and hypotheses about consequences; no claimed hardware failure, firmware build success or safety qualification.

### Independent arithmetic verification
- Re-evaluated all12 cubic gain functions at0.08,0.12,0.16,0.21 m; no controller tuning performed.
- Independently finite-differenced forward kinematics to check the implemented VMC J^T entries dL0/dq and dphi0/dq at three valid nonsingular motor-angle pairs, perturbation1e-6 rad.
- CALCULATED max absolute error versus the analytic expressions:6.94e-11 at(q1,q4)=(pi/2,pi/2),4.21e-11 at(1.3,1.8),6.90e-9 at(1.0,2.1). This checks the formulas locally at those poses, not global nonsingularity, encoder calibration or physical geometry.
- Arithmetic used Python double precision. No closed-loop MuJoCo rollout, embedded compilation or real-world balancing was performed.

### Implementation sequence (two-stage architecture approved; no execution yet)
1. Extract a pure source-parity controller reference: gain schedule, mirrored state maps, PID update semantics, torque/force clamps and VMC; compare outputs with host-compiled upstream pure functions on fixed fixtures, without hardware drivers.
2. Propose a source-informed sagittal model retaining virtual-leg lean and body pitch with the two generalized torque inputs. Keep unknown mass/inertia assumptions explicit; retain the four-state model only if useful as a separately named lesson.
3. Validate equilibrium, signs and contact; test the existing scheduled controller before redesigning/tuning it. Do not hide a mismatch by silently replacing gains. Failure of upstream gains on ASSUMED dynamics establishes model/controller incompatibility, not defective original hardware control.
4. Add source-estimator/timing approximations separately, with measured traces when supplied. Record every intentional difference from source; do not silently port firmware defects as intended behavior.
5. Only then compare RL against the matched source-informed LQR/VMC baseline, with identical observations/actuator limits/control timing, failure cases, multiple seeds and held-out perturbations.
- Updated lab follow-up: the owner clarified physical WBR assemblies are not yet available. Request CAD/mass properties, body/leg BOM, component specifications and LQR-generation files if available; defer weighing, supported balance-test COM and hardware traces until assemblies exist. Mass sweeps are sensitivity only, not identification. Actual flashed-revision/performance claims remain unavailable.

### Pinned primary-source references
[DM-R]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisR_task.c
[DM-L]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisL_task.c
[DM-VMC]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/VMC/VMC_calc.c
[DM-INS]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/INS_task.c
[DM-OBS]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/observe_task.c
[DM-PID]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/PID/pid.c
[DM-PS2]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/ps2_task.c
[DM-UART]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/uart_control_task.c
[DM-DRV]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Devices/DM_Motor/dm4310_drv.c

## Documentation change tracking
- Owner requires a log whenever any document is created or revised, so Claude can audit the changes later. Rule recorded in AGENTS.md and ops/worklog/README.md; decision D-20261020-8.
- This session's documentation changes are enumerated in ops/worklog/DOCUMENTATION_LOG.md, DOC-20261020-1, including the initial inventory, scope, sim-to-real discussion, source audit and corrections.
- Review status: local working changes, uncommitted and not pushed; no PR or Claude approval yet. Source audit uses a pinned public commit, not a confirmed flashed revision.
- Final independent review confirmed scope/evidence consistency and flagged D-20261020-7's "executed" wording; append-only correction D-20261020-9 clarifies source implementation, not controller execution.

## Claude review and publication milestone, 2026-10-20 11:02 +07
### Done
1. SOURCE-SUPPORTED: owner relayed Claude approval of DOC-20261020-1 and five review decisions; appended D-20261020-10 through -14, preserving old entries. Owner clarified physical WBR assemblies unavailable; added D-20261020-15 and corrected the premature measurement request.
2. SOURCE-SUPPORTED: pinned DM-jump LICENSE states MIT terms requiring copyright/permission notice retention; license SHA-256 e530433beec8b250e0b5cc9668b378875fb58ce904b90268e0ea4df86edcf524. Check copied-file/upstream provenance before implementation. No controller code copied into this repository.
3. MEASURED: fetched origin/main, now 0dc029a (merged PR #36), containing owner profile and simulation/control rules. AGENTS.md overlaps local documentation edits; plan is a reviewed-doc checkpoint commit followed by a normal merge, preserving both instruction changes without stashing or resetting.
### Notes
- Review approval is relayed directly by the owner in this chat, not read from a Claude-authored review file. Publication scope is DOC-20261020-1 plus the review decisions and directly required status/log updates; no simulation implementation, dependency change or firmware edit.
- New DOC entries target about 15 lines; the earlier reviewed DOC entry stays intact as historical evidence. Logging is not a claim of test execution.
### Decisions
- D-20261020-10: two-stage architecture; -11: compiled upstream C/Python parity; -12: mass/COM priority; -13: licensing; -14: bounded publication/logging; -15: hardware unavailable, physical measurements deferred.
### Not done / blocked
- No C/Python parity harness, MuJoCo model, closed-loop experiment, RL training or hardware deployment.
- Body/leg measurements cannot be performed now; estimates stay ASSUMED/CAD-derived as appropriate, and sweeps are sensitivity only.
- Windows microSD imaging completion/verification remains UNKNOWN; earlier card A evidence was archived and verified 731/731 files.
- Publication receipts below supersede the earlier pending/local-only publication state; CI/PR state is recorded separately from completed local checks.

### Publication receipts
- Documentation assertions exited 0: exactly six approved Markdown paths, no extra files, all paths logged, pre-session decisions preserved, CURRENT.md 38 lines, DOC-20261020-2 12 lines. `git diff --check` exited 0.
- Checkpoint commit 39cd6ac (`docs: record controller audit and approved simulation plan`) preserved the six reviewed documents before merging overlapping AGENTS.md changes.
- Merge commit f1a7fa6 brought origin/main 0dc029a into the feature branch without conflicts; git merge exited 0 and the tree was clean. No stash/reset/force operation used.
- Re-read merged AGENTS.md, RESEARCH_RULES.md and USER_PROFILE.md. PR #36 simulation rules are now present locally; its earlier open-PR status remains historical in the initial session notes.
- Verified PR delta against origin/main contains only AGENTS.md and the five approved worklog documents. No sim/, firmware, package, threshold or canonical gate-document changes.
- Owner approved publication and conditional merge for this exact documentation/review scope. Push, PR and CI receipts will be available in GitHub history; no green CI or PR merge claimed before those operations complete.
