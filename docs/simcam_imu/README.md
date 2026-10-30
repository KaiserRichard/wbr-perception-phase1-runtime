# Real bench IMU tilt in the simulated camera

This replay drives the simulated robot's body pitch and roll from the **measured**
GY-521 recording made by hand on 30 October 2026. The body-mounted camera tilts
with it. Ideal optical depth goes through the existing, unmodified obstacle
detector, decision policy and research jump gate. A second, independent run uses
the same scene, approach and jump schedule with zero body pitch/roll. CSVs join
the runs by scenario time, and optional paired PNGs show visibility changes.

| Component | Evidence status |
|---|---|
| Raw accelerometer and gyro recording | **MEASURED**, board on the bench, tilted by hand; not robot motion |
| Complementary-filter attitude | Estimate from measured inputs; not orientation ground truth |
| Board axes mapped directly to robot axes, attitude scale | **ASSUMED**; no measured robot mounting transform |
| Scene, robot geometry, camera mount, approach and jump/contact schedule | **ASSUMED**, prescribed kinematics |
| Depth | **IDEAL**, rendered optical depth; no disparity noise or hardware camera artifacts |
| Detector, decision and gate | Actual existing algorithms; no IMU/oracle plane supplied to the detector |
| Paired render outcome | Pending conductor execution outside the sandbox |

The hypothesis is that **per-frame plane fitting keeps height error small under
real tilt, while pitch changes target visibility and the camera blind zone**.
The task brief reports mean absolute error (MAE) of 0.21 mm for static tilt in
`tilt_sweep` PR #170. That result is motivation, not a result reproduced here or
a threshold validated for this dynamic hand recording. Angular rate can inhibit
the gate even when a target remains visible and the fitted height stays accurate.

## Commands

Run from the repository root, using the existing Python environment:

```bash
~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m tools.simcam_imu.tilt_source ~/wbr-evidence-archive/imu-view-live-20261030/imu_view_run.csv
```

This lists source metadata and continuous sampled windows where absolute pitch
**or** roll is strictly greater than 3 degrees for strictly more than 2 seconds.
Angles are absolute to gravity, without subtracting the initial bench tilt.
Long stationary but tilted spans can qualify; this helper does not claim every
listed window contains motion. Sample gaps longer than 0.1 s split windows.

Rendering must be run by the conductor outside the restricted sandbox:

```bash
~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m tools.simcam_imu.run docs/simcam/example_box132.json --imu-csv ~/wbr-evidence-archive/imu-view-live-20261030/imu_view_run.csv --imu-start 12 --record /tmp/wbr-simcam-imu-12s/frames --out /tmp/wbr-simcam-imu-12s/timeline.csv
```

The scenario positional argument is optional and defaults to
`docs/simcam/example_box132.json`. The minimal invocation is:

```bash
~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m tools.simcam_imu.run --imu-csv ~/wbr-evidence-archive/imu-view-live-20261030/imu_view_run.csv
```

`--record OUT` requires an empty or absent directory. It creates `imu_tilt/` and
`zero_tilt/`, each with annotated camera/depth PNGs. Without it the depth still
requires MuJoCo rendering, but no PNGs are written. Both runs process 10 Hz detector
ticks, including the duration endpoint only when it lies on that grid. They use
separate detector caches, decision histories and gates.

| Option | Meaning |
|---|---|
| `--imu-start S` | Scenario time zero samples elapsed CSV time S; default 0 |
| `--bias-window START END` | Inclusive elapsed CSV interval assumed still for gyro-bias calibration; default 0–2 s |
| `--scale K` | Multiply filtered pitch, roll and their rates by nonnegative K; default **1.0** |
| `--out CSV` | Tilted timeline path; default `timeline.csv`; paired paths share its stem |
| `--record OUT` | Empty directory for camera/depth PNGs from both runs |

Scale is an explicitly assumed way to reduce large hand rotations to a candidate
robot body tilt. For example, `--scale 0.25` maps an estimated 20-degree hand tilt
to 5 degrees and 40 deg/s to 10 deg/s. The raw evidence and estimated gyro bias
stay unchanged. It does not turn the hand trajectory into measured robot motion.

## Time, filter and geometry

All CLI times are **elapsed from the first CSV timestamp**, not wall time or raw
board time. For this recording the first timestamp is 138.488 s, so
`--imu-start 12` begins at board timestamp 150.488 s. The full file is filtered
before selecting the scenario interval; a later start does not reset the filter.
The original CSV remains read-only. There is no looping, endpoint hold or
extrapolation when a scenario would overrun the evidence. Interpolation across
a gap longer than 0.1 s is rejected.

The loader reuses `tools.imu_view.stream.from_csv` and `filter.TiltFilters` with
time constant 0.5 s. Gyro bias is the three-axis arithmetic mean over the assumed
still calibration interval, converted from CSV deg/s to rad/s by the existing
loader. Unlike a live pipeline, offline replay can estimate this bias first and
then filter **all** samples, including the calibration interval. Initialization
uses the accelerometer angle; calibration does not zero the initial tilt. The
sample-time clamp matches `imu_view.Pipeline`: 0.0001–0.1 s, with a 0.01 s first
update. At 100 Hz the blend weight is 0.5 / (0.5 + 0.01), approximately 0.9804.

Linear interpolation returns angles and the slope of that same segment as Euler
pitch/roll rates in deg/s. These rates replace simcam's hard-coded zero rates
before the existing gate runs. Its unchanged stable-rate bound is strictly
below 5 deg/s on each axis. Rates come from the filtered trajectory, not raw
body-axis gyro channels and not 10 Hz finite differences. Filtering has no
orientation ground truth; translational hand acceleration can corrupt gravity
tilt estimates. Yaw is fixed at zero.

The frame is x forward, y left, z up. Positive pitch is nose down; positive roll
lifts the left side. Rotation is pitch about y followed by roll in the ZYX Euler
convention, with rotation matrix `Ry(pitch) Rx(roll)`.
`tools.wbr_pose.model.set_pose` already implements this rotation about the axle,
the leg geometry and the lower wheel's finite-cylinder floor clearance. This
wrapper reuses it, adds scenario x translation, and retains the camera as a
rigid child of the body. The reported axle height reuses `imu_view.view.axle_height`.
With pitch alone the axle remains at the wheel radius, 0.0603 m; at nonzero roll
the axle rises to keep the lower wheel on the floor and the other wheel lifts.
Synthetic jump height is added to that clearance.

Gate contact/status and jump timing remain simcam's **synthetic schedule**, even
when roll visibly lifts one wheel. They are not inferred from kinematic wheel
clearance or measured by the IMU. The run metadata records this distinction.

## Outputs and comparison

With `--out /tmp/example/timeline.csv`, the outputs are:

| File | Content |
|---|---|
| `timeline.csv` | Tilted run, one row per scenario tick |
| `timeline_zero_tilt.csv` | Independent zero-body-tilt run; fixed camera mounting pitch remains |
| `timeline_comparison.csv` | Exact one-to-one time join; baseline columns prefixed `zero_` |
| `timeline_metadata.json` | Full scenario, source path/SHA-256, bias interval/mean/std, scale, timestamp origin and assumptions |

The timeline retains simcam's columns, including decision `height_m`, `distance_m`,
`raw_advisory`, `plane_valid`, `gated_advisory`, gate reason/phase and history resets.
Additional columns include body pitch/roll, filtered rates, raw/elapsed IMU time,
axle height, scale and evidence labels. `detector_height_m` and
`detector_distance_m` are the **current nearest cluster**; `obstacle_detected`
records its presence. Decision dimensions may be remembered exponentially
smoothed values when the current target is absent, so use the current-cluster
columns for geometry/visibility analysis.

For a scenario with exactly one box or step, `reference_height_m` is its assumed
input height. `height_error_m` is current-cluster height minus reference height,
and `abs_height_error_m` is its absolute value. Both are NaN without a current
cluster or a valid newly fitted plane. Multiple-target and ramp scenes have no
single reference height, so their errors are NaN. The harness does not associate
cluster identity with a particular object or certify that the detected plane is
the physical floor.

In the comparison, `height_error_delta_m` is tilted signed error minus baseline
signed error; `abs_height_error_delta_m` is the difference in absolute errors
(positive means worse under tilt). `detector_height_delta_m` compares current
cluster estimates directly, including when no reference height is defined.
`raw_advisory_agreement` and `gated_advisory_agreement` are exact label equality,
including NONE and UNCERTAIN. `both_planes_valid` exposes paired fit availability.
Agreement is not correctness; missing geometry stays NaN, never zero error.

For example, estimates 0.134 m and 0.133 m against a 0.132 m box produce signed
errors +0.002 m and +0.001 m. Both error deltas are +0.001 m. A missing tilted
cluster instead produces NaN deltas while its advisory comparison remains visible.

The default approach is prescribed through the obstacle with no collision solver;
the existing simcam conductor report observes penetration from roughly 3.6 s.
`before_obstacle_face` only checks axle x against a single box/step front face;
it is **not** a collision/contact validity flag. Body/camera geometry can intersect
earlier, especially under tilt. Separate those views from visible, valid-plane,
pre-contact height errors. Floor loss, box-top-as-floor fitting, and close-range
visibility loss must not be counted as successful geometry because error is absent.
The paired camera views and detection/plane flags expose these cases.

## Non-rendering verification

```bash
~/Desktop/Research/wbr-lab-ops/.venv/bin/python .github/run_unittest.py tools/simcam_imu
python3 tools/lint_markdown.py docs/simcam_imu/README.md docs/simcam_imu/WORKLOG.md docs/simcam_imu/REVIEW.md
```

Tests use synthetic CSVs with known gravity/rates, closed-form floor depth arrays,
and MuJoCo forward kinematics only. They never construct a graphics renderer.
Coverage includes window boundaries/gaps, known static/dynamic tilt and bias,
interpolation/slopes/scaling, source bounds, actual detector/gate rate inhibition
and recovery, axle clearance, rigid camera placement, zero-tilt simcam parity,
comparison joining and paired-output orchestration with the renderer stubbed.
All MuJoCo graphics construction is inside `render_run`, left for the conductor.

See [WORKLOG.md](WORKLOG.md) for actual local runs and [REVIEW.md](REVIEW.md) for
the handoff and pending rendered evidence.

## Conductor run (2026-10-30): result

Window: IMU elapsed 38–44 s, the most active 6 s of the recording (MEASURED hand motion: pitch −28…+18°, roll down to −19.5°).
Run at scale 1.0 (stress) and 0.3 (about ±8°, closer to a balancing robot, ASSUMED).
Scenario: `example_box132`. Counts are the 48 ticks before the robot reaches the box face.

| | scale 1.0 | scale 0.3 | zero tilt |
|---|---|---|---|
| Body pitch / roll (deg) | −27.2…17.9 / −8.6…0 | −8.1…5.4 / −2.6…0 | 0 / 0 |
| Raw STOP_CANDIDATE ticks | 1 | 8 | 32 |
| Raw UNCERTAIN ticks | 38 | 38 | 6 |
| Plane valid | 48/48 | 46/48 | 48/48 |
| Height error when detected | 1.1 mm (n = 1) | median 1.8 mm (n = 8) | — |

**Finding (MEASURED in simulation).** The geometry stays correct under real tilt: the box reads 0.131 m (see the PNGs). The advisory still goes UNCERTAIN about 80 % of the time. Two causes, both in ASSUMED integration code rather than the detector:

1. Before the fix, the gate required pitch and roll rates below `ASSUMED_STABLE_RATE_DEG_S = 5` even in STAND. Hand motion scaled to ±8° still reaches 10–20 °/s, so the gate left STAND and waited for the SETTLE dwell.
2. Before the fix, `tools/simcam/run.py` cleared the decision history whenever the gate was not in STAND. The detector then could not reach `confirm_n` again, so even the raw advisory was UNCERTAIN. The research note (#169) asked for a reset only after LANDING.

## Re-run

The [gate/history fix](../jump_gate/README.md#balancing-wobble-and-detector-history-fix-2026-10-30)
retains detector/decision history except at CROUCH entry and the first tick after
FLIGHT. In established STAND, maximum absolute pitch/roll rate scales confidence
linearly to zero at the new **ASSUMED** 60 deg/s limit; only rates above that limit
inhibit STAND. The strict 5 deg/s requirement remains for entering STAND through
SETTLE. Jump/contact inhibition and unknown-input handling are unchanged.

The commands below are for the conductor outside the sandbox. New rendered
results are pending; the earlier table records the behavior before this fix.
Run the three suites from the repository root:

```bash
python3 .github/run_unittest.py tools/jump_gate
~/Desktop/Research/wbr-lab-ops/.venv/bin/python .github/run_unittest.py tools/simcam
~/Desktop/Research/wbr-lab-ops/.venv/bin/python .github/run_unittest.py tools/simcam_imu
```

Repeat the measured-motion comparison at `--imu-start 38 --scale 0.3`:

```bash
PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
IMU_RESULTS=$(mktemp -d /tmp/wbr-gate-fix-imu.XXXXXX)
"$PYTHON" -m tools.simcam_imu.run docs/simcam/example_box132.json --imu-csv ~/wbr-evidence-archive/imu-view-live-20261030/imu_view_run.csv --imu-start 38 --scale 0.3 --record "$IMU_RESULTS/frames" --out "$IMU_RESULTS/timeline.csv"
```

Acceptance: raw STOP ticks before the box face should be close to the zero-tilt
run (32/48), gated STOP >= 25/48. The paired zero-tilt CSV is generated by this
same command. Inspect the 48 `before_obstacle_face=True` rows, raw/gated counts,
confidence, gate reason and the paired images; leave the measured results here
only after conductor execution.

Run all 13 unchanged scenarios through simcam, then score:

```bash
SCENARIO_RESULTS=$(mktemp -d /tmp/wbr-gate-fix-scenarios.XXXXXX)
for scenario_path in tools/sim_scenarios/scenarios/*.json; do
  scenario_name=${scenario_path##*/}
  "$PYTHON" -m tools.simcam.run "$scenario_path" --out "$SCENARIO_RESULTS/${scenario_name%.json}/timeline.csv" || break
done
python3 -m tools.sim_scenarios.score score_all "$SCENARIO_RESULTS"
```

Acceptance: 12/12 scored PASS still (jump windows unchanged).
`at_min_height_020` has no expected windows and remains NOT SCORED; the current
`score_all` CLI returns exit 1 for that unscored case even when all 12 scored
scenarios pass. Preserve the full output and distinguish this from a scored FAIL.

## Re-run after the gate fix (conductor, 2026-10-30)

Same window (38 s, scale 0.3), 48 ticks before the box face:

| | before fix | after fix | zero tilt |
|---|---|---|---|
| Raw STOP_CANDIDATE | 8 | 40 | 34 |
| Gated STOP_CANDIDATE | — | 38 (target ≥ 25: PASS) | 34 |
| Gated confidence on STOP | — | 0.52–1.0 (`wobble_confidence_scaled` on 22 ticks) | 1.0 |

Results:

- All 13 sim scenarios: 12/12 scored PASS.
- The two jump windows now end at LAND + the gate's settle dwell (gate spec), not at the end of the scripted SETTLE. The earlier pass came from the history wipe; see PR #175.
- In CROUCH, PUSH, FLIGHT, LAND and the dwell, the gated output is never JUMP_CANDIDATE.
