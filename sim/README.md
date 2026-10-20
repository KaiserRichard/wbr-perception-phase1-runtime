# Assumed reduced planar WBR

This is a running **SIMULATION / ASSUMED** three-coordinate, six-state
wheel-biped model. MuJoCo integrates the nonlinear dynamics under gravity.
The controller is a **new matched LQR**. It is not a reproduction of DM-jump,
an identified robot model, or evidence of sim-to-real performance.
Gain parity remains pending independent learning work. No gain schedule,
protected parity exercise, fivebar controller or RL training is implemented here.

## Run

From the repository root, use Python 3.12:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r sim/requirements.lock
.venv/bin/python -m sim.run_planar \
  --config sim/configs/assumed_planar.json \
  --out /private/tmp/wbr-planar-reproduction-01
.venv/bin/python -m unittest discover -s sim/tests -v
```

Use a **new output directory** on each run; existing output is never overwritten.
The runner rejects output paths inside this repository. Linux may use `/tmp/`.
The output includes full per-step CSVs, per-scenario JSON, `result.json`,
`linearization.json`, the generated `model.xml`, the config snapshot and
`trajectories.png`. Failed simulations retain the same files; unexpected errors
retain `error.txt` and any preceding CSV samples. Exit 0 requires BALANCE PASS,
PUSH PASS and OPEN_LOOP PASS (the last means the unactuated model falls).
The result records commit, dirty status, Python/package versions, config/model/
source-file SHA-256 hashes and artifact hashes. A dirty run is explicitly labeled.

## Mechanical reduction

World x is horizontal, world z is up, pitch is about +y (positive pitch leans
toward +x). The state is `[x, theta, phi, xdot, thetadot, phidot]`: axle
translation, **absolute leg pitch**, **absolute body pitch**, and their rates.
The inputs are aggregate wheel-pair torque and aggregate virtual hip-pair torque,
in N m. The two physical sides are lumped into one sagittal mechanism.
MuJoCo coordinates are `[x, theta, phi-theta]`; the hip hinge leaves body pitch
independent of leg pitch. Both pitches are unconstrained.

The axle has an ideal horizontal prismatic coordinate at wheel-radius height.
The reduction imposes no heave, lateral motion, yaw, roll, slip or loss of ground
contact. Wheel absolute rotation is eliminated using `beta=x/r`; its kinetic
energy is retained exactly as translation armature `I_w/r²`. The wheel visual
does not spin; CSV records the reconstructed rolling angle. This is an explicit
ideal rolling constraint, not a friction/contact simulation.

The wheel motor's relative coordinate is `x/r-theta`, represented by a fixed
MuJoCo tendon. Its work is `tau_w*(dx/r-dtheta)`, including the reaction on the
leg. Hip motor work is `tau_h*(dphi-dtheta)`. Thus in absolute coordinates:

```text
generalized force = [tau_w/r, -tau_w-tau_h, tau_h]
```

The trunk translates with the leg endpoint and rotates independently at the hip.
A world +x force is applied at its COM using `xfrc_applied`, with no extra moment.
Its generalized force is `F*[1, L*cos(theta), c_b*cos(phi)]`. Tests independently
check this mapping, both actuator reactions, and the nonlinear Lagrange equations.

There are exactly 3 positions, 3 velocities and 2 torque motors; no springs,
damping, position servos, gravity compensation, state resets during rollout,
joint-limit supports or equality stabilizers. Visual geoms do not collide.
The model is valid for balancing before the declared fall threshold; it does
not simulate ground impact, jumping, fivebar kinematics or variable leg length.
The isotropic inertia tensors use the configured pitch inertia on all axes;
only the pitch component enters this constrained planar dynamics.

## Parameters and synthesis

`configs/assumed_planar.json` is the single editable parameter/protocol source.
Each physical parameter has a value, SI unit, evidence label and source.
Only wheel radius 0.0603 m is used from the pinned
[DM-jump observer](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/observe_task.c#L74).
The config also preserves an **unused** source-geometry inventory from the pinned
[VMC source](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/VMC/VMC_calc.c).
These are code constants, not verified physical dimensions. All masses, COMs,
inertias, aggregate torque caps and the 0.16 m rigid leg are assumptions.
No upstream controller implementation is copied.

The runner generates MJCF from that config; geometry sizes are only visual.
It finite-differences `mj_forward` for continuous A/B and **actual held-control
`mj_step`** for discrete A/B at the configured 2 ms RK4 timestep. It independently
compares the latter with SciPy zero-order-hold discretization. Direct centered
differences are used because MuJoCo's `mjd_transitionFD` does not support RK4.
The trajectory uses the same model, timestep, state transform and input semantics.
See the primary [MuJoCo integration documentation](https://mujoco.readthedocs.io/en/3.3.7/computation/index.html)
and [XML actuator/joint reference](https://mujoco.readthedocs.io/en/3.3.7/XMLreference.html).

Both [CARE](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_continuous_are.html)
and [DARE](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_discrete_are.html)
are solved; the default controller uses DARE, `u=clip(-K*state)`.
The config declares dimensional Q/R weights and a discrete stage cost
`dt*(state.T*Q*state + torque.T*R*torque)`. This is a chosen sampled cost, not
an exact discretization of the continuous cost integral. All A/B, Q/R, P/K,
Riccati residuals, open/closed-loop eigenvalues and controllability singular
values/ranks are saved. The continuous and discrete gains are newly synthesized.
[SciPy cont2discrete](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.cont2discrete.html)
provides the independent dynamics discretization comparison.

## Predeclared protocol and observed run

Protocol v1 was written before the first simulation:

- All scenarios start at leg +8°, body −6°, zero translation and rates.
- Balance: 10 s with LQR. Push: identical run plus 6 N at the body COM during
  `[3.00, 3.15)` s, totaling 0.9 N s. Every CSV row's input acts over the following
  `interval_dt_s`; the final row has zero interval.
- A fall is either absolute pitch reaching 45°. Displacement must stay ≤1.5 m.
  Torque caps are 2 N m wheel pair / 4 N m virtual hip pair.
- Balance and push require no numerical warnings/reset, full duration, bounded
  torques, the full declared pulse, and all six errors within
  `[0.02 m, 1°, 1°, 0.03 m/s, 0.05 rad/s, 0.05 rad/s]` throughout the final second.
  Recovery is the start of the uninterrupted in-tolerance suffix, measured after
  initialization or pulse end; it must occur within 5 s.
- Open loop uses the identical model/initial state with exactly zero torque.
  It must grow tilt at least 5× and reach 45° within 5 s. This is a required
  negative control; a stable unassisted model cannot pass the protocol.

The first actual run passed without tuning or threshold changes: balance
recovered in 1.732 s; push recovered 2.714 s after pulse end; open loop fell at
0.182 s with 45.164° peak tilt. Neither controlled run saturated. Peak translation
was 0.0391 m for balance and 0.1596 m for push. The total peak tilt of 8° includes
the initial condition. Both controllability ranks were 6, and the maximum
discrete closed-loop eigenvalue magnitude was about 0.997544. These observations
apply only to this deterministic assumed nominal model and declared disturbance.

The tests cover independent nonlinear mechanics, actuator work/reactions and
MuJoCo clipping, COM push mapping, passive energy, unstable open loop, a
deliberately zeroed controller failing balance, Riccati residuals, finite-difference
convergence, local trajectory prediction, timestep consistency, and full protocol/
CSV impulse accounting. No tests are skipped. CI explicitly discovers this suite
and runs the CLI; the shell suite discovers parity infrastructure; `sim/tests` is run explicitly by CI.

Physical blockers: no assembled robot/CAD mass properties, validated COM/inertia,
motor torque-speed/bandwidth/friction/delay or contact data. Full fivebar VMC and
hardware validation remain future work. Ideal state feedback and simultaneous
torque updates are assumed. This result does not complete gain parity or a
hardware milestone.

**Recommendation:** review the reduced mechanics and replace assumed physical
parameters with CAD/lab evidence before extending to fivebar VMC or comparing RL.

## Protected learning exercise and milestone boundary

The compiled reference and owner gain-schedule TODO are documented separately
in [parity/README.md](parity/README.md). Do not edit or bypass
`parity/student.py::gain_schedule`: the owner writes it and the conductor reviews.
Native C checks do not complete Python VMC parity. The owner explicitly
prioritized a running ASSUMED MuJoCo baseline in parallel; this new LQR synthesis
does not claim the pending gain-parity milestone passed.

A/B and solver code in this run are implementation authorized by the latest
conducting request. RL reward design/training remain later work. For each next
milestone explain the idea/key equation briefly with a primary source, ask two
understanding questions, and log actual runs and pending answers. All meaningful
documentation changes are recorded in ops/worklog/DOCUMENTATION_LOG.md.
