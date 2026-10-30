# Contact physics twin: T1

This is a MuJoCo **physics** twin with gravity, wheel torques, leg forces and
ground/box collisions. Motion is constrained to the sagittal plane by world
`slide x`, `slide z`, and `hinge pitch` joints. It has two independent virtual
legs, rather than a closed five-bar mechanism. Nothing sets the robot's pose
after initialization: takeoff, flight, impact and recovery come from `mj_step`.
This is a newly synthesized controller for an assumed plant, not the team's
controller and not a validated hardware twin.

## Status and evidence

The physics criteria passed in twelve saved runs: one 30 s stand, one drive,
and ten independently seeded jumps. Rendering was neither attempted nor
verified in the worker sandbox. The actual depth camera/detector/gate path is
implemented; its integration test uses a renderer stub and the real JumpGate.
That test does not establish rendered detector performance.

Corrected source-counter results are in [results/corrected_summary.json](results/corrected_summary.json).
The CSV files contain every 1 ms control tick. Earlier tuning evidence remains
under `~/wbr-evidence-archive/twin3d-20261030-01/runs/` (attempt01-04, final and
verified; summaries in `results/`). See [RUN_LOG.md](RUN_LOG.md) for failures and fixes.

| Criterion | Saved result | Status |
| --- | --- | --- |
| Stand, 30 s, pitch below 30 degrees, no base-ground contact | 30.000 s; peak pitch 0.528 degrees; no ground contact | PASS |
| Drive 1 m at 0.3 m/s; crossing time and final speed error | 1 m at 3.824 s, speed 0.30424 m/s; final error 0.0005234 m/s | PASS |
| Clear 8 cm box and land upright, at least 8/10 seeds | 10/10; minimum wheel clearance 42.36–46.04 mm; peak pitch ≤3.485 degrees | PASS |
| Rendered raw/gated advisory during jump | Conductor command below | UNVERIFIED |
| Non-rendering unit/integration tests | 11 tests, zero skipped | PASS |

## Model and parameter provenance

**SOURCE-SUPPORTED** means a repository/report/source value, not a physical
measurement. **ASSUMED** means a simulation/design choice. **CALCULATED** means
derived from those choices or from saved runs. No parameter is **MEASURED**.
All numerical settings not otherwise labelled in code are ASSUMED, including
visual colors, numerical thresholds, solver settings and test tolerances.

The model lives in [model.py](../../sim/twin3d/model.py). Each side contains a
hip pitch hinge, a downward prismatic length joint, and a wheel hinge. A wheel
is a contacting cylinder, with its axis along world y when upright. Self contact
is permitted by MuJoCo's usual parent filtering; the two leg capsules are
explicitly excluded from contacting each other. The body and legs can hit the
floor or box; those contacts are failures, not disabled collisions.

| Parameter | Value and meaning | Evidence |
| --- | --- | --- |
| Wheel radius | 0.0603 m | SOURCE-SUPPORTED: [visual generator](../../sim/models/make_wbr_3d_simple.py), DM-jump observer constant |
| Body mass | 3.5 kg total | SOURCE-SUPPORTED: same generator/team report |
| Leg mass | 0.2 kg per side; 0.001 kg hip, 0.199 kg slider | Total SOURCE-SUPPORTED from four 0.05 kg links; partition ASSUMED |
| Wheel mass | 0.7 kg each | SOURCE-SUPPORTED: same generator/team report |
| Total mass | 5.3 kg | CALCULATED from mass partition |
| Legacy planar mass set | 2.0/0.5/0.6 kg body/leg/wheel | NOT USED in this twin |
| Five-bar inventory, unused | Upper 0.075 m, lower 0.14 m, hip spacing 0.08 m | SOURCE-SUPPORTED: same generator, lesson 04; no linkage mechanics claim |
| Body half sizes / COM | (0.15, 0.10, 0.06) m; COM 0.03 m below hip | ASSUMED, reusing visual layout |
| Wheel lateral offset / half width | 0.162 m / 0.018 m | ASSUMED, reusing visual layout |
| Body/wheel inertia | MuJoCo uniform box/cylinder inertia from stated sizes/masses | CALCULATED under ASSUMED shapes |
| Hip inertia per axis | 0.000001 kg m² | ASSUMED |
| Slider leg COM | 0.06 m above axle, fixed in slider frame | ASSUMED; not a length-dependent five-bar COM |
| Slider leg inertia | (0.0003, 0.0003, 0.00002) kg m² | ASSUMED |
| Virtual leg collision shape | Capsule radius 0.008 m; endpoints 0.015 and 0.105 m above axle | ASSUMED proxy; it does not telescope visually |
| Length limits / standing length | 0.06–0.21 m / 0.12 m | Limits SOURCE-SUPPORTED source command range; stand ASSUMED |
| Per-wheel torque cap | ±1 N m | ASSUMED simulation cap; matches nominal H6215 rated value in repository audit |
| Per-hip torque cap | ±3 N m | ASSUMED virtual-axis cap; J4310 rated joint torque is not a virtual-hip rating |
| Per-leg axial force cap | ±100 N | ASSUMED ideal actuator; also source firmware axial clamp, no joint mapping |
| Gravity / timestep | 9.81 m/s² / 0.001 s | ASSUMED |
| Joint damping / armature | 0.001 SI / 0.00001 SI for each joint | ASSUMED; armature perturbs free-fall acceleration by about 0.000028 m/s² |
| Contact friction | Sliding 1.0, torsional 0.005 m, rolling 0.0001 m | ASSUMED; `condim=3` activates sliding friction only |
| Contact solver | `implicitfast`, elliptic cone, 60 iterations | ASSUMED |
| Contact softness | `solref=(0.004,1)`, `solimp=(0.95,0.99,0.001)` | ASSUMED; small penetration is possible |
| Box test fixture | Face x = 1.0 m, depth 0.12 m, width 1.2 m, height 0.08 m | ASSUMED requested 8 cm obstacle |
| Seed perturbations | Uniform box-face ±0.015 m, initial body pitch ±0.02 rad | ASSUMED distribution, NumPy `default_rng(seed)`; draw box offset first |
| Drive timing | Start at 0.5 s, continue at 0.3 m/s through 6 s | ASSUMED test protocol; it continues past the 1 m crossing |
| Jump approach | Command 0.9 m/s from 0.5 s through 7 s | ASSUMED; transient actual speed differs from command |
| Crouch request gap | 0.25 m from axle center to box front face | ASSUMED and tuned on seed 0, then tested on seeds 0–9 |

The existing [parameter source audit](../learning/MODEL_PARAMETER_SOURCES.md)
records H6215 **1 N m rated / 2 N m peak**, and J4310 **3 N m rated / 7 N m peak**.
Those are SOURCE-SUPPORTED supplier specifications in that audit. They do not
identify this robot's motors, establish continuous jump capability, or map
virtual leg force/hip torque to the two five-bar motor torques.

## Balance and leg control

[control.py](../../sim/twin3d/control.py) reuses the existing
[planar plant](../../sim/planar.py) and [DARE synthesis](../../sim/lqr.py), with
the twin's mass/inertia assumptions. It retains the baseline Q diagonal
`(40,200,200,8,8,8)` and R diagonal `(0.8,0.6)`, both ASSUMED design weights.
The reduced-model sample period is 1 ms. Its differentiation epsilon is the
existing ASSUMED 1e-6. That reduced model has ideal rolling contact and frozen
length, so its local stability result does not certify the nonlinear contact
plant, length transients or saturation.

The state is `[axle x, absolute leg pitch, body pitch, axle vx, leg rate, body rate]`.
Leg pitch is body pitch plus mean hip angle. Axle position/velocity include the
prismatic displacement and rate. Body COM is negative relative to the hip in
this model. Reusing the old model's positive COM would describe a different plant.

Four freshly calculated 2×6 gains at lengths `(0.08,0.12,0.16,0.20)` m are
interpolated componentwise; outside that design grid the endpoint gains are held.
The grid/interpolation are ASSUMED. [gains.json](gains.json) preserves all four
gains, A/B matrices, Riccati residuals and eigenvalues. The grid-point discrete
closed-loop spectral radii are 0.99875950, 0.99865915, 0.99859107 and 0.99854288
in ascending length order. This is local evidence only.

Velocity tracking moves the position reference by `v_command * dt` and subtracts
the velocity command from the state. Wheel torque is split equally between the
sides. Hip torque changes sign because the contact model actuates leg-relative-
to-body angle, while the reduced model actuates body-relative-to-leg angle.
ASSUMED differential hip feedback, 20 N m/rad and 0.8 N m s/rad, stabilizes the
independent antisymmetric leg mode absent from the aggregate LQR state.

Length control is per-side PD plus half the body weight while supporting:

$$
F_i=\operatorname{clip}\left(k_p(L_{set}-L_i)-k_d\dot L_i+\frac{3.5\,9.81}{2},-100,100\right).
$$

ASSUMED gains are 1800 N/m and 24 N s/m, except thrust uses 5000 N/m and
16 N s/m. For example, thrust at 0.10 m with zero length rate requests
`5000*(0.21-0.10)+17.1675 = 567.1675 N` per side, clipped to 100 N.
The large stiffness and ideal force cap are simulation choices, not motor tests.

## Jump and flight

The fixed length targets and strict thresholds follow
[lesson 05](../lessons/05_wbr_jump_sequence.md) and the DM-jump source:

| Phase | Length target | Transition |
| --- | --- | --- |
| CROUCH | 0.08 m | Each side accumulates a pass when its L0 < 0.10 m |
| THRUST | 0.21 m | Each side accumulates a pass when its L0 > 0.18 m |
| RETRACT | Saved stand setpoint, 0.12 m | Each side accumulates a pass when its L0 < setpoint + 0.01 m |
| SETTLE | 0.12 m | Remains in settle through end of run |

Targets/thresholds and the 10-pass per-side counters are SOURCE-SUPPORTED.
Counters accumulate qualifying passes; a nonqualifying pass does not reset
them. The right source implements this at
`/private/tmp/claude-501/dmjump-ref/chassisR_task.c:276–322`; the paired left-side
logic is at `/private/tmp/claude-501/dmjump-ref/chassisL_task.c:201–230`. Both sides must
reach 10; the phase change resets both counters. The right source sets
`CHASSR_TIME=1` (line 55) and delays by it in the task loop (lines 80–93); the
left source sets `CHASSL_TIME=1` (line 38) and delays by it (lines 61–75), but
neither source defines the RTOS tick duration. The twin uses its 1 ms control period per
pass, labelled ASSUMED. The source state machine has no duration, timeout or
contact-sensor transition; this emulation adds no timeout. SETTLE is a length
phase and can begin before touchdown. Actual flight is logged separately.

The main flight mode begins after thrust when both wheel contacts are absent.
It holds the stand length target and captures mean relative hip angle with an
ASSUMED 8 N m/rad, 0.3 N m s/rad hold controller. Differential hip feedback
remains active. Gravity feedforward is removed in that mode. All airborne
wheel torque is zero, including brief contact loss during crouch/thrust; the
source length trajectory continues through those brief transients.
There is no prescribed upward velocity, external jump force, pose animation,
contact override or phase-based gravity change.

The 0.25 m trigger gap allows the body nose to rise before reaching the box and
the trailing body edge to clear before impact. A 0.30 m gap cleared the wheels
but clipped the trailing body edge on landing. At only 0.3 m/s the original
trajectory could not traverse the fixture before descending. The separate
0.9 m/s jump approach is therefore explicit; the jump result is not a 0.3 m/s
jump claim. Tuning used seed 0; the final ten include seed 0 and are not a held-out
robustness test. The perturbations are small and no broad success probability is
inferred from 10/10.

## Runner, checks and perception

Run from the repository root with the existing MuJoCo environment:

```sh
export PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
export OPENBLAS_NUM_THREADS=1
"$PYTHON" -m sim.twin3d.run --scenario stand --seeds 1 --out docs/twin3d/runs/reproduction
"$PYTHON" -m sim.twin3d.run --scenario drive --seeds 1 --out docs/twin3d/runs/reproduction
"$PYTHON" -m sim.twin3d.run --scenario jump_box --seeds 10 --out docs/twin3d/runs/reproduction
python3 -m sim.twin3d.check docs/twin3d/runs/reproduction --out docs/twin3d/runs/reproduction/summary.json
"$PYTHON" .github/run_unittest.py sim/twin3d
python3 tools/lint_markdown.py docs/twin3d/README.md docs/twin3d/RUN_LOG.md docs/twin3d/REVIEW.md
```

`--scenario all --seeds 10` runs ten seeds for each scenario. Output filenames
are deterministic and will overwrite the same scenario/seed in that output
directory, so use a new output directory to preserve earlier evidence.
`check.py` uses the standard library only; it evaluates saved logs, not the plant.
Its CLI requires at least one passing stand and drive plus exactly ten distinct
jump seeds with at least eight successes. It exits 1 for an incomplete batch,
even when a single jump passes. `--require-perception` additionally requires
passing gate evidence in every supplied run.

Checks enforce pitch strictly below 30 degrees, no body-floor contact, full
stand duration, and no MuJoCo numerical warnings. Drive reports the first 1 m
crossing, crossing speed, total distance and final speed error (ASSUMED tolerance
0.03 m/s). Jump checks both wheels' bottom above the box top whenever their
radius-expanded footprint overlaps the box, complete traversal, zero wheel/
body/leg box contact, and upright for the saved interval beginning one second
after the final airborne interval. At least a full second after landing must
exist in the log. All runs also retain the global 30-degree pitch limit.
An ASSUMED 60-degree pitch abort leaves a failing partial CSV. Log continuity
and finite core values are checked; full 1 ms samples preserve short impacts.

CSV `x` is mean axle position; `z` is hip/base origin height. Angles/rates are
radians and radians/s. Efforts are the **sum** of the two applied actuator
commands in N m or N. `base_ground`, `bad_box`, and `wheel_box` are measured
MuJoCo geometry contact flags for that timestamp. Positive-distance proximity
contacts do not count. `mj_forward` refreshes kinematics/contact after each step
so position, camera and state timestamps agree.

With `--perception`, an actual body-mounted 640×480 camera renders metric depth
every 0.1 s. The implementation reuses `tools.simcam` projection/depth helpers,
the real obstacle detector/decision, and `tools.jump_gate.gate.JumpGate`.
Intrinsics, depth clipping (0.01–6 m), camera offset `(0.16,0,0.06)` m from the
hip and downward tilt 3 degrees are ASSUMED. Field of view is CALCULATED from
simcam's focal length 386.953 pixels. Camera pitch moves with the physics body.
There is no sensor noise or latency model beyond holding the 10 Hz observation.

The gate receives current simulated contact, FSM status and actual pitch rate
at every physics tick. Roll rate is zero because roll is constrained. Held
geometry keeps its original acquisition timestamp; it does not create fresh
plane votes. Detector cache and decision history reset on crouch entry and first
contact after airborne motion. Perception cannot trigger or alter the jump.
Per-tick gating captures the short crouch even when no 10 Hz image falls inside
it. Active phases must each contain gated `UNCERTAIN` with confidence zero.
Absent rendering evidence is reported as `gate_passed: null`, not a gate PASS.

## Exact conductor commands still needed

Run the following outside the worker's graphics sandbox, from this worktree:

```sh
export PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
export OPENBLAS_NUM_THREADS=1
"$PYTHON" -m sim.twin3d.run --scenario stand --seeds 1 --perception --out docs/twin3d/runs/perception
"$PYTHON" -m sim.twin3d.run --scenario drive --seeds 1 --perception --out docs/twin3d/runs/perception
"$PYTHON" -m sim.twin3d.run --scenario jump_box --seeds 10 --perception --out docs/twin3d/runs/perception
python3 -m sim.twin3d.check docs/twin3d/runs/perception --require-perception --out docs/twin3d/runs/perception/summary.json
```

These exercise MuJoCo depth rendering, the detector and gate; the worker made
no renderer/viewer calls. A green physics batch does not stand in for this run.
Commit/push/PR handling belongs to the conductor; no git metadata was changed
by this worker. [REVIEW.md](REVIEW.md) contains the review handoff and remaining
evidence boundary.

## Limits

No roll, yaw, lateral slip maneuver, full linkage, VMC joint-force mapping,
motor electrical/thermal dynamics, torque-speed envelope, sensor estimation,
controller delay, backlash or compliance is represented. Leg inertia and COM
do not change like a five-bar. Rigid ideal actuators and assumed friction can
make jumping easier than on hardware. Contact softness permits small ground
penetration; obstacle-clearance criteria require positive geometric clearance.
The existing planar baseline's 160/160 push result is motivation for reusing
its LQR approach; it is not a result of this contact model. No robot, Pi, serial
device or STM32 was accessed. Only `sim/twin3d/**` and `docs/twin3d/**` were written.

## Conductor perception run (2026-10-30)

Run outside the sandbox: stand ×1, drive ×1 and jump_box ×10 with `--perception`. Each run renders the body camera, then the detector, then JumpGate.

- `python3 -m sim.twin3d.check ... --require-perception`: **PASS**.
  - stand: 30 s, peak pitch 0.53°.
  - drive: 1.65 m in 6 s, which covers the required 1 m at 0.3 m/s.
  - jump_box: 10/10 seeds, minimum wheel clearance over the 8 cm box 42.4–46.0 mm (MEASURED in simulation).
- Gate check, seed 0: every CROUCH tick (35) and THRUST tick (81) is gated UNCERTAIN with confidence 0. RETRACT is also suppressed (63 ticks).
- Raw CSVs (56 files) moved to `~/wbr-evidence-archive/twin3d-20261030-01/` with SHA256SUMS. `results/perception_summary.json` is the checker output.
