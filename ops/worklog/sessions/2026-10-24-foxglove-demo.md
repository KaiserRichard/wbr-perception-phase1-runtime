# Foxglove offline detector demo

- Added `tools/bag_tools/foxglove_demo.py`: low-level rosbag2 SQLite reader,
  RealSense metadata skipped, MCAP ROS 2 writer; original color/depth/camera
  info/TF streams retained and current `AdvisoryCore` outputs added per depth
  header. Output includes MarkerArray, six-field advisory JSON and PointCloud2.
- Added Foxglove layout JSON, bag-tools instructions and one synthetic rosbag
  conversion test. `pytest -q tools/bag_tools/tests/test_foxglove_demo.py`:
  1 passed. The test's first run exposed the rosbag writer's existing-path
  requirement; removing the pre-created directory fixed it.
- Converted six requested bags to `foxglove-demo-out/<RUN>.mcap`. The evidence
  archive destination is outside the workspace write sandbox, so outputs remain
  in the worktree fallback. `B-H08` required a camera-info prepass because its
  depth stream begins before the first color CameraInfo message.
- Validated each MCAP by iterating messages and deserializing output schemas:
  color/depth/camera-info/TF and generated topics present; no Metadata topics;
  every detector marker header matched its source depth frame stamp/frame_id.
- Per-run output receipt (MiB uses 1,048,576 bytes; `generated` is each of
  advisory/markers/points):

  | Run | Size MiB | Color | Aligned depth | Color info | Aligned info | TF | Generated each | Advisory histogram |
  |---|---:|---:|---:|---:|---:|---:|---:|---|
  | B-H02 | 66.47 | 134 | 138 | 139 | 139 | 1 | 138 | UNCERTAIN 138 |
  | B-H05 | 53.73 | 110 | 110 | 111 | 111 | 1 | 110 | JUMP_CANDIDATE 108, UNCERTAIN 2 |
  | B-H08 | 67.72 | 137 | 139 | 139 | 140 | 1 | 139 | JUMP_CANDIDATE 137, UNCERTAIN 2 |
  | B-H13 | 53.30 | 109 | 110 | 111 | 111 | 1 | 110 | STOP_CANDIDATE 108, UNCERTAIN 2 |
  | B-H26b | 53.83 | 108 | 109 | 110 | 110 | 1 | 109 | STOP_CANDIDATE 107, UNCERTAIN 2 |
  | S1-empty | 51.44 | 108 | 110 | 106 | 111 | 1 | 110 | STOP_CANDIDATE 108, UNCERTAIN 2 |
- Current detector output histogram: B-H02 UNCERTAIN 138; B-H05
  JUMP_CANDIDATE 108, UNCERTAIN 2; B-H08 JUMP_CANDIDATE 137, UNCERTAIN 2;
  B-H13 STOP_CANDIDATE 108, UNCERTAIN 2; B-H26b STOP_CANDIDATE 107,
  UNCERTAIN 2; S1-empty STOP_CANDIDATE 108, UNCERTAIN 2.
- Recommendation: open an MCAP via Foxglove File > Open local file, then import
  `tools/bag_tools/foxglove_demo_layout.json` through Layouts > Import from file.
  Copy artifacts to the evidence archive after this worktree is accessible to
  that destination.
