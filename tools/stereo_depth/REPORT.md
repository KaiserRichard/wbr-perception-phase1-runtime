# C2-M1B: offline dense depth from recorded IR stereo MCAP

## Built

- `mcap_stereo.py` decodes ROS 2 MCAP images and camera info, extracts infra1
  `fx,cx,cy`, derives baseline from infra2 `P[3] = -fx*B`, and pairs the two
  image streams by exact header timestamp. The CLI streams pairs instead of
  loading all 2,215 image pairs into memory.
- `sgbm_depth.py` computes dense SGBM disparity and a left/right consistency
  mask, converts valid disparity to float32 metric depth, and writes compressed
  depth arrays, millimetre PNGs, previews, a JSON summary, and a contact sheet.
- Tests cover CameraInfo baseline extraction, a missing/unpaired image stamp,
  and depth recovery from a synthetic known shift.

## Exact commands and result

Full bag, default every-15th-pair run:

```sh
~/Desktop/Research/wbr-venvs/perception/bin/python \
  tools/stereo_depth/sgbm_depth.py
```

Output directory:
`/Users/quockaiser/Desktop/Research/wbr-data/derived/stereo-depth-20261023/`

The run completed with 2,215 left images, 2,215 right images, 2,215 exact-stamp
pairs, zero unpaired left or right images, and 148 processed frames. It wrote
148 compressed depth arrays, 148 millimetre PNGs, 148 preview PNGs,
`contact_sheet.png`, and `summary.json` (446 files total).

Calibration measured from the MCAP `camera_info`:

| Value | Measured |
|---|---:|
| infra1 `fx` | 386.953308 px |
| infra1 `cx`, `cy` | 321.034302 px, 241.040131 px |
| infra2 baseline from projection matrix | 0.049912553 m |
| `fB` | 19.313828 px·m |
| Image size | 640 × 480 |
| SGBM disparities | 80 (covering the 0.3 m target range) |

Per-frame statistics over the 148 processed frames (valid pixels only for depth
percentiles):

| Statistic | Result |
|---|---:|
| Valid fraction, mean / median | 0.5301 / 0.5365 |
| Valid fraction, 5th–95th percentile across frames | 0.3161–0.6342 |
| Median depth per frame, median across frames | 0.9280 m |
| Per-frame p5 depth, median across frames | 0.3396 m |
| Per-frame p95 depth, median across frames | 2.4142 m |

OpenCV compute time per frame on this Mac, averaged across the selected frames:

| Resolution | Mean | Median |
|---|---:|---:|
| Full, 640 × 480 | 55.61 ms | 54.36 ms |
| Half, 320 × 240 | 12.36 ms | 11.96 ms |

These timings cover SGBM plus consistency checking, excluding MCAP decode and
file output. Half-resolution timing uses images resized by 0.5, half-scaled
intrinsics, and a correspondingly reduced disparity count.

Unit tests:

```sh
~/Desktop/Research/wbr-venvs/perception/bin/python \
  -m unittest discover -s tools/stereo_depth/tests -v
```

Result: 3 tests passed. The synthetic 8 px shift recovered the expected 10 m
depth within the 0.5 m test tolerance.

## Limitations

- The recording is passive infrared with the projector emitter off. Surfaces
  with little IR texture, occlusions, and reflective or otherwise difficult
  material can yield invalid or erroneous matches; invalid pixels are zero.
- There is no ground-truth depth stream in this MCAP. Metric accuracy is
  **UNKNOWN**; these outputs are a stand-in for the camera's own depth stream,
  not a validated replacement or accuracy claim.
- The reported depth distributions describe SGBM outputs, not scene truth.
- The CLI processes every Nth pair (default 15), starting at pair index 0.
  It does not emit aligned color or point clouds.
