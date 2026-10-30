# Worker receipt — 2026-10-30

Status: implementation locally available; visual evidence and publication BLOCKED.
Only `tools/scene_twin/**` and `docs/scene_twin/**` were written. Model generator,
viewer inputs, archive, Pi and hardware were not modified. This scoped receipt
also records the documentation changes; the task's explicit allowed-file list
precludes editing the general `ops/worklog` files.

## Commands and actual results

- Read `ops/worklog/CURRENT.md`, `ops/USER_PROFILE.md`, `tools/imu_view/README.md`,
  viewer/generator code, bag tooling and archive flicker report.
- First real build/run:
  `~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m tools.scene_twin.view --run ~/wbr-evidence-archive/lab-day-20261025/3-box13 --record /tmp/scene-twin-box13 --fps 10`
  compiled model, then failed creating renderer:
  `mujoco.cgl.cgl.CGLError: invalid CoreGraphics connection`.
- Same recording command for `4-approach`, output `/tmp/scene-twin-approach`:
  same CGL failure. Partial directories contain only CSV headers, no images.
- `MUJOCO_GL=glfw` recording retry, output `/tmp/scene-twin-box13-glfw`:
  installed MuJoCo Darwin code still chooses CGL, same actual failure.
- `python3 .github/run_unittest.py tools/scene_twin`: final **10 tests PASS**,
  one file, zero skipped (MEASURED test result). Initial test failure was an exact
  zero comparison against floating-point subtraction residue; changed assertion
  to an approximate numerical comparison and reran successfully.
- Real MuJoCo build + `mj_forward` for every packet in all requested takes:
  **3,563 poses PASS** (MEASURED executed count). Checked each wheel centre minus
  radius and box centre minus half-height at z=0, tolerance 1e-12 m (ASSUMED
  numerical-check tolerance). This is geometry verification, not visual evidence.
- `git diff --check`: PASS for tracked changes; files are untracked because
  staging is blocked. Source whitespace was checked separately before handoff.
- `git add tools/scene_twin docs/scene_twin` and `git commit -m 'scene_twin: replay recorded obstacle advisories in MuJoCo'`:
  both failed with `Unable to create .../.git/worktrees/wbr-wt-scene-twin/index.lock: Operation not permitted`.
  The Git metadata directory is outside this session's writable roots.
- `git push -u origin chatgpt/20261030-scene-twin`:
  `Could not resolve hostname github.com: -65563`. No push occurred.
- `gh pr create --base main --head chatgpt/20261030-scene-twin --title 'scene_twin: MuJoCo replay of lab-day obstacle runs' --body-file docs/scene_twin/PR_BODY.md`:
  `error connecting to api.github.com`. No PR URL exists; no merge attempted.
  `gh auth status` also failed token validation while network was unavailable;
  credential validity cannot be concluded from this session.

## Actual replay values

All table entries are INFERRED from MEASURED detector packets, except pose counts
(MEASURED executed), motion classification (ASSUMED from run directory label),
and metadata existence (MEASURED filesystem observation). Units: metres.

| Run | Poses checked | Motion | Median box height | Face x | Robot x range | Bag origin |
|---|---:|---|---:|---:|---|---|
| 1-empty | 495 | static | 0.504785 | 0.617873 | 0 to 0 | UNKNOWN: no bag directory |
| 2-books46 | 563 | static | 0.047494 | 1.143863 | 0 to 0 | available |
| 3-box13 | 603 | static | 0.134455 | 1.146698 | 0 to 0 | available |
| 4-approach | 649 | approach | 0.118235 | 1.446604 | ~0 to 0.976037 | available |
| 4-approach-r2 | 607 | approach | 0.473943 | 1.449288 | -0.000076 to 0.007220 | available |
| 4-approach-r3 | 646 | approach | 0.133706 | 1.321251 | -0.128278 to 0.111690 | UNKNOWN: metadata absent |

Detector estimates can be wrong: the tall box in `1-empty`, the large height in
`4-approach-r2` and its nearly fixed range are reproduced detector behaviour.
They are not corrected from run names or treated as physical truth.

## Documentation changes and decisions

- Added `README.md`: commands, assumptions/statuses, trajectory equation,
  header/log-time distinction, Foxglove manual pairing and evidence limits.
- Added `PR_BODY.md`: concrete ready-to-use PR description.
- Added this receipt and `tools/scene_twin/results/README.md` with actual render
  failures and reproducible evidence commands; no fabricated GIF/PNG artifacts.
- First valid packet anchors x=0. Static labels freeze motion; approach labels
  use trailing-three-valid-sample median. Invalid samples freeze the filtered
  distance rather than slowly moving through dropout.
- Missing bag metadata uses a visibly ASSUMED first-packet origin; CSV manifest
  also records origin status. No false claim of bag alignment.
- Optional MCAP export not implemented: priority remains actual rendered evidence.

## Remaining milestone work

A Mac session with graphical access must run both evidence recordings, inspect
representative PNGs, and place the small GIFs + sample PNGs under results.
Commit/push and PR creation require writable worktree Git metadata and working
GitHub access. Ready PR title/body above; do not merge. No completed milestone
or completed visual review is claimed.

## Conductor follow-up (Claude, outside the worker sandbox, 2026-10-30)

- The sandbox blocked CoreGraphics and git; recording and publication were done outside it.
- Camera framing changed: floor enlarged to 4 m, view from behind the robot (azimuth 125°, elevation −18°).
- `--record ... --fps 5` for 3-box13 and 4-approach: 300 PNGs each. GIFs are 1.3 MB and 2.8 MB, in `tools/scene_twin/results/`.
- Frames inspected by eye: the robot is upright on the floor and the box is on the floor ahead, coloured by advisory (blue = JUMP_CANDIDATE).
- 4-approach detector distances span 0.30–1.30 m over 493 of 649 frames (MEASURED from packets.csv). The 1.3 m upper bound is the live range limit.
