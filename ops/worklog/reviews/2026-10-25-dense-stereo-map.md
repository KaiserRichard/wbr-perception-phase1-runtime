# Dense stereo map review — 2026-10-25

## Result

- Added `tools/local_map/dense_from_orb.py` to pair rectified infra1/infra2 by header timestamp, match ORB poses within 20 ms, estimate stereo depth, transform camera points through `slam_world` into `map`, and filter by 1 cm voxels observed in at least two frames.
- Generated `dense-out/map_dense.ply`, `map_dense.mcap`, `foxglove_layout.json`, `topdown.png`, and `stats.txt`.
- 225 frames used from 674 stereo pairs; no selected frame lacked a pose.
- Points: 4,447,683 before voxel filtering; 556,284 after filtering.
- Extents: x=4.660 m, y=4.525 m, z=4.113 m.
- Table-plane sanity fit constrained to near-horizontal normals (|normal_z| >= 0.85): 21,580 inliers, 5.766 mm RMS.
- MCAP inspection confirmed `/dense_map` in `map` with float32 xyz/intensity fields, `/orb/path` with 674 poses in `map`, and static `map -> slam_world` quaternion `(-0.5, 0.5, -0.5, 0.5)`.
- Final full run completed in about 36 seconds.

## Limitations

- The supplied environment did not include OpenCV and package installation was prohibited. The script therefore used its NumPy four-path semi-global fallback at quarter linear resolution; this is coarser than the OpenCV 3-way SGBM path in `tools/stereo_depth/sgbm_depth.py`.
- `stereo.yaml` labels the selected SDK baseline/intrinsics as readback rather than independently calibrated measurements.
- Dense output is a pose-fused visualization map; no ground-truth geometry or metric accuracy claim was established.
- No PRs merged; worktree remains uncommitted on the requested branch.

## Claude review

Claude: review this completed dense stereo map milestone, especially the quarter-resolution NumPy matching fallback and the table-plane interpretation.
