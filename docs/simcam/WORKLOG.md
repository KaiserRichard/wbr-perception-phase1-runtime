# Simcam worker receipt — 2026-10-30

## Scope and documentation

- Branch `chatgpt/20261030-simcam`; edits confined to `tools/simcam/**` and
  `docs/simcam/**`. No commit, push, PR, SSH, Pi access or hardware commands.
- Added shared-schema validation, box/step/wedge MJCF, body camera, planar-depth
  conversion, exact pinhole frustum, optional disparity noise, scripted pose,
  real detector/decision/gate integration, CSV and annotated PNG output.
- Added `example_box132.json`, `README.md` and this receipt. Per the task's
  allowed-file restriction, the global ops worklog/documentation logs were not
  edited; this file records documentation changes and implementation decisions.
- Decisions: source front/top mount, 3 degrees down from the synthetic evaluator;
  neutral camera height follows WBR geometry (0.2103 m at l0=0.12), instead of
  forcing synthetic evaluation's 0.30 m height. Body pitch zero because the
  existing jump timeline supplies no pitch. Preserve unchanged detector limits.
- Decisions: exact source intrinsics via off-axis GL projection, zero invalid
  depth, fixed 0.01–6 m clipping; compare expectations against gated output and
  retain a separate raw comparison. Clear external decision history while
  inhibited and the detector plane cache on crouch/first landing.

## Runs, failures and fixes

- Read detector/decision, synthetic evaluator/depth, scene twin, articulated
  WBR pose/jump, gate/demo/timeline and research section 4 before implementation.
- Verified depth semantics against official MuJoCo camera documentation and
  renderer source; links are in `depth.py` and README. Installed environment
  uses MuJoCo 3.3.7. No renderer was constructed.
- First non-rendering test run: fixture repository path was one parent too high;
  fixed the fixture path. A float32 exact-equality expectation differed from
  float64 literals by about 1.5e-9; changed to an appropriate numeric comparison.
- Next run: coarse 160×120 fixture estimated 0.114457 m for the 0.132 m box,
  failing its 5 mm height bound. Diagnostic sampling at 160/320/640 pixels wide
  gave 0.114457/0.125392/0.130841 m, with correct plane height/pitch. The low mount
  and stride leave too few top-edge samples at coarse resolution. Corrected the
  accuracy fixture to the required 640×480; did not change detector thresholds.
  The smaller jump test only asserts inhibition/recovery. Failure receipt:
  `/tmp/wbr-simcam-tests-coarse-failure.log` (ephemeral local diagnostic).
- `~/Desktop/Research/wbr-lab-ops/.venv/bin/python .github/run_unittest.py tools/simcam`:
  **PASS**, 3 test files, 21 tests, 0 skipped; 0.965 s on the recorded passing run.
  Includes the real detector on analytic depth, STOP for the 132 mm full-resolution
  fixture, gate inhibition during jumping, fresh history and eventual recovery.
- Non-rendering MuJoCo construction/pose smoke: all three obstacle types compiled,
  18 geoms and 11 mocap bodies. At t=0/1.2/1.6/2.2 s, measured camera heights were
  0.210300/0.185300/0.468996/0.192882 m and pitch was 3 degrees down throughout.
  Verified finite geom poses and camera x = axle x + 0.15 m. No GL context used.
- `~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m tools.simcam.run --help`:
  **PASS**, scenario, record, output, noise and seed arguments available.
- `python3 tools/lint_markdown.py docs/simcam/README.md docs/simcam/WORKLOG.md`:
  **PASS**, 0 issues across 2 files. The default
  `python3 tools/lint_markdown.py` also passed with 0 issues across 7 files.

## Remaining conductor run

- **PENDING:** actual MuJoCo camera RGB/depth rendering and complete 61-tick
  example. Rendering was explicitly excluded in the worker sandbox (CGL).
  Analytic tests and successful model construction do not prove rendered output.
- From the worktree, using an absent/empty record directory:

```bash
~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m tools.simcam.run docs/simcam/example_box132.json --record /tmp/wbr-simcam-box132 --out /tmp/wbr-simcam-box132/timeline.csv
```

- Limits: ideal depth unless optional noise enabled; no pitching body trajectory,
  collision dynamics, automatic jump/control feedback, real contact/IMU or
  hardware validity claim. Research tilt/oracle sweeps remain outside this task.
