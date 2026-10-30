# T1 physics run log

Worker: 2026-10-30, Mac sandbox, branch supplied by conductor. Existing local
Python environment only; no installs, network, rendering, git writes or hardware
access. File changes and implementation decisions are recorded here because the
ticket permits writes only under `sim/twin3d` and `docs/twin3d`.

## Build and iteration

- Read `ops/worklog/CURRENT.md`, `ops/USER_PROFILE.md`, `sim/README.md`, the planar
  plant/LQR/config, visual generator, lessons 04/05, `tools/wbr_pose`, simcam and
  JumpGate implementation. Also read the local supplier parameter-source audit.
- Built the virtual-leg contact model, scheduled LQR, length PD and hybrid jump;
  immediately ran the real physics scenarios before unit tests or audits.
- Initial command:
  `~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m sim.twin3d.run --seeds 1 --out docs/twin3d/runs/attempt01`.
  Exit 0 produced three CSVs, but evaluation FAIL: stand/drive eventually rested
  the base on the floor despite nearly zero body pitch. The independent hips
  developed an antisymmetric mode absent from the mean-state controller. Jump
  at command 0.3 m/s and gap 0.20 m failed to traverse the box.
- Added per-side differential hip PD (20/0.8), kept the source LQR weights, and
  ran `OPENBLAS_NUM_THREADS=1` for subsequent physics commands. Drive now keeps
  0.3 m/s through the full run instead of stopping its reference at 1 m, allowing
  explicit crossing-time and final-speed reporting.
- Attempt 02: `--seeds 1 --out docs/twin3d/runs/attempt02`, exit 0. Stand and drive
  PASS. Jump used 0.9 m/s and 0.17 m gap; FAIL from body/box contact during crouch
  and wheel/box contact during descent. Jump peak pitch 16.45 degrees.
- Increased thrust-only length PD from 1800/24 to 5000/16, retaining the ±100 N
  per-side clamp. Attempt 03: `--scenario jump_box --seeds 1 --out docs/twin3d/runs/attempt03`,
  exit 0. At gap 0.30 m, wheels cleared with 21.61 mm minimum margin, but the
  trailing body hit the box on descent; peak pitch 52.24 degrees and floor
  contact made this FAIL. The run later recovered; that does not erase failure.
- Changed only trigger gap to 0.25 m. Attempt 04:
  `--scenario jump_box --seeds 1 --out docs/twin3d/runs/attempt04`, exit 0.
  Seed 0 jump PASS, 70.14 mm wheel clearance, 3.485-degree peak pitch, no box
  or body-floor contact. Aggregate checker exit 1 correctly reflected missing
  stand/drive and the other nine jump seeds, rather than a failed individual jump.
- Preliminary batch `runs/final`: separate stand/drive seed-0 commands and ten
  jump seeds. Aggregate PASS, 10/10 jumps. This batch preceded explicit
  post-step forward refresh and the final all-airborne wheel-torque suppression.
  `runs/verified` is authoritative for the delivered code.
- Final consistency changes: refresh `mj_forward` after integration so pose,
  contact and camera timestamps agree; zero wheel torque during any airborne
  interval, including brief crouch/thrust contact loss; log numerical warnings
  and perception enablement; derive camera field of view from simcam intrinsics.
  Re-ran all physics criteria after these changes.

## Commands and actual validation

All physics commands below use
`~/Desktop/Research/wbr-lab-ops/.venv/bin/python`, with
`OPENBLAS_NUM_THREADS=1`. Final verified commands:

```sh
export PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
export OPENBLAS_NUM_THREADS=1
"$PYTHON" -m sim.twin3d.run --scenario stand --seeds 1 --out docs/twin3d/runs/verified
"$PYTHON" -m sim.twin3d.run --scenario drive --seeds 1 --out docs/twin3d/runs/verified
"$PYTHON" -m sim.twin3d.run --scenario jump_box --seeds 10 --out docs/twin3d/runs/verified
python3 -m sim.twin3d.check docs/twin3d/runs/verified --out docs/twin3d/runs/verified/summary.json
"$PYTHON" .github/run_unittest.py sim/twin3d
python3 tools/lint_markdown.py docs/twin3d/README.md docs/twin3d/RUN_LOG.md docs/twin3d/REVIEW.md
```

- Model compilation: nine joints, six actuators; real `mj_step`/`mj_forward`
  succeeded. No renderer was constructed in physics runs.
- Initial requested unittest run: 8/9 PASS. Ballistic acceleration test expected
  exact −9.81 to six decimal places, actual −9.809971987675715 from the explicit
  1e-5 joint armature. Corrected the assertion to a stated 5e-5 m/s² tolerance;
  did not change the physics to satisfy that assertion.
- Added renderer-stub integration coverage that feeds an actual nonzero raw
  JUMP_CANDIDATE through the real JumpGate in both active phases. Held depth
  retains acquisition time and makes no additional renderer calls.
- Requested unittest runner after fixes: 10 tests PASS, 0 skipped; includes
  compilation, joints/actuators, ballistic flight, gain dimensions and local
  stability at three lengths, strict FSM thresholds, no pose writes by control,
  saved-log positive/negative fixtures and gate integration.
- Perception-only final review: track the prior physical airborne flag separately
  from FSM phase, so detector history resets once on actual first contact, rather
  than repeatedly during RETRACT/SETTLE flight. Expanded the renderer-stub test
  to preserve held observations in flight and invalidate them on landing.
- `gains.json`: preserved four full calculated synthesis records. Spectral
  radii are below one at all four grid points; no interpolation/global proof.
- Physics results and Markdown lint: see final validation receipt below.

## Final validation receipt

- All three final runner commands exited 0; 12 CSVs, 106012 rows total, 106 s
  simulated time across the batch. Every recorded MuJoCo warning count is zero.
- `python3 -m sim.twin3d.check docs/twin3d/runs/verified --out docs/twin3d/runs/verified/summary.json`:
  exit 0, aggregate PASS; stand PASS, drive PASS, jumps **10/10 PASS**.
- Stand: 30.000 s, peak pitch 0.527610 degrees, no base-ground contact.
- Drive: first 1 m at 3.824 s, crossing speed 0.304240926 m/s, final speed error
  0.000523377 m/s; total 1.651855741 m through 6 s, no base-ground contact.
- Jumps: ten distinct seeds 0–9, all 7 s; minimum wheel clearance per run ranges
  from 69.949806 to 71.080939 mm, peak pitch across all jumps 3.484618 degrees.
  No wheel, leg or body box contact and no base-ground contact; every run has
  upright evidence more than one second after final landing.
- Gate field in physical logs is null/UNVERIFIED, as expected without perception.
- Markdown lint: `0 issues across 3 file(s)`; rerun after documentation updates.

## Remaining conductor work

- Run the exact `--perception` and `--require-perception` commands in README
  outside the sandbox. Rendered detector/gate performance remains UNVERIFIED.
- Conductor owns git commit/push/PR and CI. Worker did not attempt those actions.
- Review handoff is [REVIEW.md](REVIEW.md); physics does not validate hardware.

## T1 source-counter correction

- Read `/private/tmp/claude-501/dmjump-ref/chassisR_task.c` and
  `chassisL_task.c`. Right `jump_loop_r` lines 280–321 increments its counter
  only when the leg threshold is true and does not clear it on a false sample;
  the left `jump_loop_l` lines 208–230 does the same. Both sides must reach 10,
  then both counters reset on phase change. These are accumulating, not
  consecutive, qualifying passes.
- The source keeps the same targets/thresholds: 0.08 m / L0 < 0.10 m, 0.21 m /
  L0 > 0.18 m, and stand set / L0 < set + 0.01 m. No duration, timeout or
  contact sensor advances the source FSM. No timeout was added to the emulation.
- Right task sets `CHASSR_TIME=1` at line 55 and delays by it; left task sets
  `CHASSL_TIME=1` at line 38 and delays by it. Tick duration is unspecified.
  Therefore 1 ms per simulated pass is ASSUMED from the twin's control period.
- Implemented per-side accumulating counters and regression tests. Command
  `~/Desktop/Research/wbr-lab-ops/.venv/bin/python .github/run_unittest.py sim/twin3d`:
  exit 0, 11 tests passed.
- Fresh physics batch commands, each exit 0:
  `OPENBLAS_NUM_THREADS=1 ~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m sim.twin3d.run --scenario stand --seeds 1 --out docs/twin3d/runs/corrected`;
  corresponding `--scenario drive --seeds 1`; and
  `--scenario jump_box --seeds 10`, same output directory. Aggregate checker
  exit 0: stand 30 s PASS (0.52761 degree peak), drive PASS (1 m at 3.824 s,
  final speed error 0.0005234 m/s), jump 10/10 PASS (42.36–46.04 mm minimum
  wheel clearance, peak pitch ≤3.48462 degrees). All 12 runs had zero MuJoCo
  warnings and no box/base contacts.
- Results are saved in `runs/corrected/summary.json`; README now identifies
  this corrected batch. The source-supported body/leg/wheel set remains
  3.5/0.2/0.7 kg; inertias and COM remain ASSUMED. The prior planar
  2.0/0.5/0.6 kg set is explicitly marked NOT USED.
