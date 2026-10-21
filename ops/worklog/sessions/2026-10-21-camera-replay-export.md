# Camera replay ROS output export — 2026-10-21

- Worker: codex-g/Sol; branch `chatgpt/20261021-camera-replay-export`.
- Read AGENTS/current/profile/root and camera-day READMEs, actual
  `ros2/wbr_orb_node/src/d435_node.cpp`, and PR79 `replay_metrics.py` from
  `/Users/quockaiser/.codex/worktrees/camera-replay-metrics/wbr-lab-ops`.
- Added only `rosbag_to_tum.py`, its pure tests, `ROSBAG_EXPORT.md`, this session.
  Documentation change: new export contract/CLI/limitations guide; central logs
  reserved for conductor. No estimator, launch, calibration or native changes.
- Exports header-precision TUM, exact status CSV (including second source stamp),
  SHA-256 provenance/counts/boundaries/counter coverage and optional image matches.
  Rejects contradictions before writing; absent streams explicit. No steady time,
  FPS, sorting, resets, stitching, normalization or synthetic poses introduced.

## Actual runs

- Mac: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -m unittest discover -s scripts/camera_day/tests -v`
  → **26 PASS** (1.663 s), including 14 new exporter tests. ROS imports lazy;
  timestamp precision/second rollover, malformed states/fields/nonfinite values,
  backsteps/counters, missing poses, source/header matching and exclusive output.
- Pi SSH: `ssh richard@192.168.50.2`; exclusive outside-Git evidence root
  `/home/richard/wbr-camera-replay-export-20261021` (all paths below relative).
  Used existing `source /opt/ros/jazzy/setup.bash`; no installs/builds required.
- First real run: `python3 synthetic_smoke.py` then
  `python3 rosbag_to_tum.py SYNTHETIC-output-bag SYNTHETIC-export --input-bag SYNTHETIC-input-bag`
  → exit 0. `synthetic-create.log`, `synthetic-export.log` preserve results.
  Tiny explicitly SYNTHETIC sqlite3 bags written with `rosbag2_py.SequentialWriter`
  and `rclpy.serialization.serialize_message`; actual reader uses deserialization.
- Final implementation saved in `final/rosbag_to_tum.py` (initial script preserved).
  `python3 synthetic_verify.py` → export/read-only/hash/counter/missing-pose/absent
  checks PASS, then **harness assertion failed**: wrong-type test accidentally set
  pose topic equal to default image topic, triggering the topic-distinctness guard.
  Script and `synthetic-verify.log` retained; no exporter defect found.
- Fixed only the harness options (`image_topic="/synthetic/unused"`):
  `python3 synthetic_verify_recovery.py` → PASS wrong ROS type rejection;
  `synthetic-verify-recovery.log`. No outputs created for rejected exports.
- `python3 -m unittest discover -s final/tests -p test_rosbag_to_tum.py -v`
  → **14 PASS** on Pi (0.077 s); `synthetic-pure-tests.log`.
- Final CLI: `python3 final/rosbag_to_tum.py SYNTHETIC-output-bag SYNTHETIC-export-cli-final --input-bag SYNTHETIC-input-bag`
  → exit 0; `synthetic-cli-final.log`. `SYNTHETIC-export-cli-final/export.json`
  links/hashes TUM/CSV: 2 poses, 4 statuses, 5 input images, 4 source matches,
  1 counter gap, 1 unmatched image, unknown tail, null FPS. Exact pose endpoints
  `1761000000.123456790` / `1761000000.123456793`; float `0.10000000000000002` preserved.
- Negative CLI: `python3 final/rosbag_to_tum.py SYNTHETIC-missing-pose-bag SYNTHETIC-missing-pose-cli-export`
  → exit **2**, publication/header contradiction, no output directory;
  `synthetic-cli-negative.log`. `SYNTHETIC-absent-export` explicitly contains zero rows.
- Mac PR79 integration: copied `SYNTHETIC-export-final` read-only into
  `/tmp/wbr-camera-replay-export-20261021-metrics/`, called `replay_metrics.analyze`
  with exported TUM/CSV → no errors, 2 poses/4 statuses/1 missing counter, null FPS;
  synthetic endpoint displacement `0.30000000000000004` m (no accuracy claim).
- No camera access, real replay, SLAM launch, compilation, motor/firmware command,
  training or other-worker source writes. Only synthetic sqlite3 tested; live data
  and MCAP not tested. Source bags must be finalized; capture tail remains unknown.
- Worker opens PR and does not merge; conductor owns real replay and integration.
