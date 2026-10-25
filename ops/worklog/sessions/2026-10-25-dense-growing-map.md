# Dense growing map

- Extended `tools/local_map/dense_from_orb.py` with `--growing`; left changes uncommitted on `claude2/20261025-dense-map`.
- Ran the requested D435 sensor/ORB pose bags with the provided Python environment; exit 0. Used 225 stereo frames, 674 pairs, 0 skipped poses; final cloud 354,244 points, extent 4.525 × 4.214 × 3.532 m, plane RMS 5.76 mm (19,466 inliers).
- `map_growing.mcap`: 75 each of `/dense_map_growing`, `/orb/path`, `/tf`; 675 source infra1 frames and 674 camera-info records. Cloud payload maximum 2,400,137 bytes (150,000 points); all checked `/tf` first-transform header stamps equal MCAP log times.
- `dense-out` total 275 MB, below the 600 MB cap. No Foxglove GUI playback was performed.
