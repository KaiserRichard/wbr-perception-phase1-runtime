# Box-ahead obstacle estimate and jump advisory

Offline NumPy prototype for estimating box geometry from a depth frame and
filtering it into an informational STM32 advisory. **The Pi does not grant jump
permission.** Balance, jumping, actuation, and safety remain entirely owned by
the STM32. There is no transport, ROS node, camera access, or hardware action.

`detect.process_frame(depth_m, K, params, state)` fits the floor with the
existing `tools/ground_plane/plane.py`, constrained to a camera-facing normal
within 30°; it reuses the last plane for up to three frames when a fit fails.
Optical-frame `(x right, y down, z forward)` maps to ground coordinates
`(forward=z, lateral=−x, up=n·p+d)`. A 2 cm grid and connected components
produce front-face distance, 95th-percentile height, lateral width, depth
extent, and point count. ASSUMED defaults include 0.25 m corridor half-width,
0.02 m minimum obstacle height, and 0.3–3.0 m range.

`decide.update` applies a 3-of-5 temporal confirmation, EMA geometry, and a
two-frame clearing hysteresis. Jump height limits are ASSUMED at 0.03–0.12 m;
taller confirmed objects produce STOP_CANDIDATE. Invalid plane near a tracked
obstacle also produces STOP_CANDIDATE; otherwise plane failure is UNCERTAIN.
Optional forward speed yields distance/speed time-to-contact.

`advisory_codec.py` is a PROPOSED type-4 message using the existing COBS and
CRC-32C framing. See [ADVISORY_SPEC.md](ADVISORY_SPEC.md). Firmware owner review
is required before any firmware use.

## Run

From the repository root:

```sh
~/Desktop/Research/wbr-venvs/perception/bin/python -m unittest discover -s tools/obstacle_decision/tests -v
MPLCONFIGDIR=/private/tmp/wbr-mpl-cache MPLBACKEND=Agg ~/Desktop/Research/wbr-venvs/perception/bin/python tools/obstacle_decision/evaluate.py
```

Evaluation writes `results/metrics.json`, `results/height_error.png`, and
`results/confusion.png`. The sweep uses 80 deterministic synthetic boxes:
heights 0.03/0.05/0.08/0.12/0.20 m, front distances 0.5/1.0/1.5/2.0 m,
camera pitch 0°/3°, disparity noise sigma 0.1 px and two seeds. Camera height
0.30 m is ASSUMED. Empty-floor and out-of-corridor controls are included.

## Limits

Synthetic renderer only; no real-box validation, no RealSense camera validation,
no ROS integration, no Pi timing or transport. Corridor and decision thresholds
are assumptions, not robot clearance/jump capabilities. Synthetic geometry
does not model reflective surfaces, multipath, motion distortion, camera
extrinsic error, floor irregularity, or real depth holes. Advisory names are
candidates only and must never be interpreted as permission to jump.

## Replay recorded RGB-D bags and evaluate box runs

`replay_bag.py` reads ROS 2 MCAP messages without ROS runtime dependencies. It
uses the aligned color-depth topic with color camera calibration when present;
otherwise it selects the depth image and depth camera info pair. `16UC1` depth
is converted from millimetres to metres; `32FC1` is treated as metres. The
`--stride` option processes every Nth depth frame. Output contains one CSV row
per processed frame and a summary JSON. The summary treats the full bag as the
static segment because the expected stationary box captures do not carry a
separate segment annotation; trim bags to the static interval before evaluation
if they include motion or setup.

```sh
~/Desktop/Research/wbr-venvs/perception/bin/python tools/obstacle_decision/replay_bag.py capture.mcap --out results/capture
~/Desktop/Research/wbr-venvs/perception/bin/python tools/obstacle_decision/replay_bag.py capture.mcap --depth-topic /camera/camera/depth/image_rect_raw --info-topic /camera/camera/depth/camera_info --stride 2 --out results/depth
```

`eval_runs.py` expects a UTF-8 CSV with this header (the mobile-demo run sheet
was not present when this evaluator was added):

```csv
run_id,bag_path,box_height_m,box_front_distance_m,box_width_m,lateral_offset_m,camera_height_m,camera_tilt_deg,floor_type,notes
```

Distances and dimensions are metres; `camera_tilt_deg` is degrees. A relative
`bag_path` is resolved from the run-sheet directory. Evaluation writes
`evaluation.md`, `evaluation.json`, one replay subdirectory per run, and plots
for estimated versus measured height and distance error versus measured
distance. Advisory correctness uses the current `DecisionParams` defaults
(jump height 0.03–0.12 m); these are assumed informational thresholds, not
hardware clearance criteria.

```sh
MPLCONFIGDIR=/private/tmp/wbr-mpl-cache MPLBACKEND=Agg \
  ~/Desktop/Research/wbr-venvs/perception/bin/python tools/obstacle_decision/eval_runs.py \
  lab/mobile_demo/run_sheet.csv --out results/mobile_demo
```
