# Research jump gate and recorded-obstacle demo

This adds an advisory inhibitor and a MuJoCo visualization, using the proposed
policy in [camera tilt and jump research, section 3](../scene_twin/TILT_JUMP_RESEARCH.md#3-jump-gating-mapped-to-actual-firmware).
It does not grant jump permission. **STM32 keeps all balance, motor safety,
stop-latch and jump authority.** There is no hardware, ROS or link-protocol output.

The demo combines recorded obstacle advisories with the existing
[wbr_pose five-bar model](../../tools/wbr_pose/model.py) and
[scripted jump timeline](../../tools/wbr_pose/jump_demo.py).
The robot crouches, extends its legs, follows the kinematic flight arc and settles.
The box uses the **gated** advisory color: blue JUMP_CANDIDATE, red STOP_CANDIDATE,
green NONE, gray UNCERTAIN. An overlay gives raw versus gated advisory, gate phase,
reason, confidence, source timestamp and **SYNTHETIC** motion phase.

## Run and export

Run from the repository root using the existing environment. Rendering has not
been attempted by this worker because the sandbox cannot create Renderer/CGL
contexts. The conductor owns visual verification.

```sh
PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
"$PYTHON" -m tools.jump_gate.demo --record docs/jump_gate/render --fps 10 --jump-at 20
```

`--record OUT` requires an empty or new directory and writes `jump_gate.gif`, all
rendered PNG frames and `timeline.csv`. The default source is
`~/wbr-evidence-archive/lab-day-20261025/3-box13/packets.csv`;
`--packets PATH` selects another recording. `--jump-at` is packet-relative seconds
at **crouch onset**; the leading STAND interval from wbr_pose is skipped then.
The replay retains the complete recording and stops at its end.

With no `--record`, the same CLI opens a MuJoCo viewer. On macOS, launch the viewer
with `~/Desktop/Research/wbr-lab-ops/.venv/bin/mjpython -m tools.jump_gate.demo`
because MuJoCo requires its macOS main-thread launcher for interactive viewing.
Offscreen recording uses the Python command above.

CSV export needs no MuJoCo context and runs independently of rendering:

```sh
"$PYTHON" -m tools.jump_gate.demo --csv-only docs/jump_gate/timeline.csv --jump-at 20
python3 .github/run_unittest.py tools/jump_gate
python3 tools/lint_markdown.py docs/jump_gate/README.md docs/jump_gate/RUN_LOG.md
```

The [saved timeline](timeline.csv) contains 6,594 gate ticks over 59.911952393 s.
Ticks merge ASSUMED 100 Hz telemetry with every recorded packet acquisition.
Repeated packets retain their original integer `frame_stamp_ns`, packet index,
and relative geometry timestamp; they add no fresh-plane votes. CSV columns
identify every synthetic or assumed input, alongside raw/gated outputs and reason.
The CSV unit test replays every saved row through a new gate and compares outputs.

## DM-jump signal mapping

These source meanings come from the pinned DM-jump implementation cited in
[the research note](../scene_twin/TILT_JUMP_RESEARCH.md#3-jump-gating-mapped-to-actual-firmware),
not from a verified telemetry interface. An eventual integration must review an
aggregated status from both legs; this prototype accepts one explicit status.

| Firmware evidence | Gate input or meaning | Demo input source |
| --- | --- | --- |
| `jump_status=0`: crouch toward 0.08 m | Status 0, inhibited CROUCH | SYNTHETIC wbr_pose CROUCH |
| `jump_status=1`: thrust toward 0.21 m | Status 1, also inhibited CROUCH | SYNTHETIC wbr_pose PUSH |
| `jump_status=2`: leg retraction intent | Status 2 alone never establishes FLIGHT or STAND | SYNTHETIC FLIGHT/LAND |
| `jump_status=3`: reset | Explicit reset/inactive cue; cannot prove landing | SYNTHETIC SETTLE/STAND |
| `ground_detectionL/R`: estimated normal force below 5 N gives 1 airborne | `airborne_l/r=True`; both true enter FLIGHT | SYNTHETIC both true only in flight |
| First foot contact after flight | LAND; clear temporal evidence immediately | SYNTHETIC LAND: left false, right true |
| Sustained two-foot contact | Both flags false; SETTLE after landing/reset | SYNTHETIC SETTLE/STAND |
| Missing contact/status, inconsistent contact, stale telemetry or clock reset | UNKNOWN; UNCERTAIN with zero confidence | Covered by unit tests; not present in baseline CSV |

The synthetic first-foot contact is an illustration, not a measured left/right
landing order. Both-contact flags during status 0/1 are also scripted. Normal-force
estimates and source counter conditions are not simulated or validated here.
Status reset while both feet remain airborne stays FLIGHT; LAND to FLIGHT handles
a bounce. CROUCH to reset enters SETTLE for an aborted jump.

## Gate states and assumptions

`Tick` takes seconds in one monotonic clock domain, an explicit status, per-foot
airborne booleans, telemetry age, pitch/roll rates in degrees/second, plane validity,
and raw advisory/confidence. Optional `plane_stamp_s` preserves a held observation's
original time; omitting it means the tick supplies a new observation at `t`.
The output has `advisory`, `confidence`, `phase` and a machine-readable `reason`.

| Gate phase | Output |
| --- | --- |
| STAND | Current raw advisory and raw confidence times ASSUMED quality 1; raw UNCERTAIN stays UNCERTAIN with zero confidence |
| CROUCH, including thrust | UNCERTAIN, confidence 0 |
| FLIGHT | UNCERTAIN, confidence 0 |
| LAND | UNCERTAIN, confidence 0; invalidate gate temporal evidence |
| SETTLE | UNCERTAIN, confidence 0 until complete clean dwell |
| UNKNOWN | UNCERTAIN, confidence 0; recover only through a new SETTLE dwell |

Zero confidence during crouch is the conservative permitted choice under the
note's cap of at most 0.25 times raw confidence; thrust is zero as specified.
Unknown status is `None`, never an alias for inactive. Status 2 with contact waits
for explicit reset and cannot promote to STAND. Mixed foot flags outside a known
landing are inconsistent and yield UNKNOWN.

All quality/timing thresholds are named **ASSUMED** constants in
[gate.py](../../tools/jump_gate/gate.py): telemetry age at most 50 ms, continuous
clean contact at least 100 ms, absolute pitch and roll rates strictly below 5 deg/s,
and at least three distinct fresh planes spanning at least 200 ms. The additional
ASSUMED held-plane/advisory age limit is 250 ms. Numerical boundary tolerance is
1 ns. Any invalid/stale plane or unstable rate restarts the clean dwell.
Startup also begins in SETTLE. After LAND, pre-jump contact and plane history is
discarded; old observations cannot count toward recovery.

## Limits and observed result

- The archive has 603 packets: STOP_CANDIDATE, NONE and UNCERTAIN. **It has no
  JUMP_CANDIDATE samples.** Synthetic unit fixtures exercise both JUMP and STOP
  and check inhibition through every non-STAND phase.
- The saved replay starts STAND at 0.200146485 s, enters CROUCH at 20.0 s,
  FLIGHT at 20.52 s, LAND at 21.07 s, SETTLE at 21.11 s and recovers STAND at
  21.416163819 s. Gate dwell and the longer scripted pose SETTLE are distinct;
  the gate uses the injected signals and its declared dwell.
- Status/contact, telemetry age 0, attitude rates 0, and valid-plane flags are
  **SYNTHETIC/ASSUMED**. The CSV has neither plane validity nor confidence;
  raw confidence is explicitly ASSUMED 1, not a measured score or probability.
- This is a stationary box13 replay with synthetic vertical motion. No obstacle
  crossing, dynamic balance, real contact telemetry or camera/depth re-rendering
  is claimed. Recorded heights/distances do not change with the injected camera
  motion. Box height is the replay's detector median, not ground truth.
- The gate resets its own temporal evidence. Recorded advisories already contain
  the upstream detector's temporal filtering; an advisory-only wrapper cannot
  undo that history. A future live integration must separately reset the detector
  EMA/confirmation state after landing before supplying fresh raw decisions.
- Inhibition changes a STOP advisory to UNCERTAIN; it cannot clear any
  controller-owned stop/safety latch. No real jump safety or deployment claim.
- MuJoCo XML compilation, pose placement and gated colors were checked without a
  renderer. GIF, camera framing, overlay layout and interactive viewing remain
  untested by this worker. Files remain uncommitted for conductor review.

## Conductor render check (2026-10-30)

The sandbox could not render, so the conductor ran `--record ... --fps 10 --jump-at 20` outside it: 601 frames.
Frames inspected:

- t = 10 s, STAND: box red, STOP passed through.
- t = 20.7 s, FLIGHT: robot airborne, box grey, gated UNCERTAIN with confidence 0.
- STOP returns at t = 21.42 s, once the SETTLE dwell is satisfied.

Evidence in `results/`: a 6 s GIF of the jump window and three key PNGs. All phases are SYNTHETIC.
