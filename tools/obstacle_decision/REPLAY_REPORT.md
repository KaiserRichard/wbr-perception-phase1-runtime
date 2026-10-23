# C2-BE offline RGB-D replay report

## Commands run

All commands ran from the repository root with the supplied perception environment. No ROS runtime, camera, Pi, network, or installation was used.

```sh
MPLCONFIGDIR=/private/tmp/wbr-mpl-cache MPLBACKEND=Agg \
  ~/Desktop/Research/wbr-venvs/perception/bin/python -m unittest discover \
  -s tools/obstacle_decision/tests -v

MPLCONFIGDIR=/private/tmp/wbr-mpl-cache MPLBACKEND=Agg \
  ~/Desktop/Research/wbr-venvs/perception/bin/python - <<'PY'
from pathlib import Path
from tools.obstacle_decision.tests.test_replay_bag import make_bag
root = Path('/private/tmp/wbr-c2-eval')
make_bag(root / 'synthetic_box.mcap')
(root / 'run_sheet.csv').write_text(
    'run_id,bag_path,box_height_m,box_front_distance_m,box_width_m,lateral_offset_m,'
    'camera_height_m,camera_tilt_deg,floor_type,notes\n'
    'synthetic_box,synthetic_box.mcap,0.05,1.0,0.30,0.0,0.30,0.0,synthetic,5 cm box at 1.0 m\n')
PY

~/Desktop/Research/wbr-venvs/perception/bin/python \
  tools/obstacle_decision/replay_bag.py \
  /private/tmp/wbr-c2-eval/synthetic_box.mcap --out /private/tmp/wbr-c2-eval/replay

MPLCONFIGDIR=/private/tmp/wbr-mpl-cache MPLBACKEND=Agg \
  ~/Desktop/Research/wbr-venvs/perception/bin/python \
  tools/obstacle_decision/eval_runs.py \
  /private/tmp/wbr-c2-eval/run_sheet.csv --out /private/tmp/wbr-c2-eval/eval
```

## Actual results

- Unit tests: **9 passed**, including the existing obstacle tests, synthetic MCAP replay, end-to-end run sheet evaluation, CSV header validation, and missing-topic diagnostic.
- The generated MCAP contains six 640×480 `16UC1` depth frames from `tools/ground_plane/synth.py`, with a 5 cm × 30 cm box whose front face is at 1.0 m, and color camera intrinsics.
- Replay output: frame count 6; plane-valid rate 1.0; camera-height median 0.299950 m; obstacle-height median 0.050064 m; obstacle-distance median 1.000000 m; obstacle-width median 0.299991 m; depth-valid fraction 0.45625; advisory counts `JUMP_CANDIDATE: 4`, `UNCERTAIN: 2`.
- Evaluator output: height error +0.000064 m; distance error 0.000000 m; width error −0.000009 m; camera-height error −0.000050 m; expected and estimated advisory both `JUMP_CANDIDATE` (correct).
- Both plot files were generated: `height_estimated_vs_measured.png` and `distance_error_vs_distance.png`.

## Limits

The test scene is analytic and stationary. Replay treats every processed frame as belonging to the static segment because the bag/run-sheet format has no segment boundaries. Advisory correctness uses the current assumed software thresholds, so this synthetic pass does not establish real-camera accuracy, robot clearance, or a safe jump decision. Per-frame `ms` measures detector execution in this host process only.
