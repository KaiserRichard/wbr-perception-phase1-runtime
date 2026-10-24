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

## Frame and layout follow-up

- Corrected the converter to publish one `/tf` per aligned depth frame, parent
  `wbr_ground` to child `camera_link`. It composes
  `T(ground<-depth_optical) * inverse(T(camera_link<-depth_optical))`, where
  the latter is built from the bag's `/tf_static` chain. The depth and color
  branches therefore retain their single static parent chain below camera_link.
  Ground axes follow `detect.ground_coords`: forward, left, up; origin is the
  floor below the camera. The last plane is retained if plane fitting stops
  yielding one.
- Kept core markers in their optical frame. Added a ground-frame solid obstacle
  cube (longitudinal depth × lateral width × height) and a status/height/range
  label. Added `/wbr_obstacle_node/depth_points`, stride 4, fields `x,y,z,height`.
- Layout fixes the 3D panel to `wbr_ground`, disables following, hides transform
  labels and sets axis scale to 0.1; both point clouds and markers, the color
  Image panel, and advisory height/distance in Raw Messages remain visible.
- Re-ran with the requested Python at
  `/private/tmp/claude-501/-Users-quockaiser-Desktop-Research-wbr-wt-claude2/86f1e3fb-27f1-4b36-ad4d-133cc09819f7/scratchpad/venv/bin/python`.
  `python -m pytest tools/bag_tools/tests -q`: 1 passed. Six outputs are in
  `foxglove-demo-out/` (regenerated sizes in bytes: B-H02 93,620,522; B-H05
  75,261,264; B-H08 94,822,050; B-H13 74,621,313; B-H26b 75,013,840;
  S1-empty 72,884,364).
- Follow-up counts (each generated topic has one message per aligned depth
  frame; `/tf_static` retained):

  | Run | Color | Depth | Color info | Depth info | `/tf` | Generated each | Bytes |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | B-H02 | 134 | 138 | 139 | 139 | 138 | 138 | 93,620,522 |
  | B-H05 | 110 | 110 | 111 | 111 | 110 | 110 | 75,261,264 |
  | B-H08 | 137 | 139 | 139 | 140 | 139 | 139 | 94,822,050 |
  | B-H13 | 109 | 110 | 111 | 111 | 110 | 110 | 74,621,313 |
  | B-H26b | 108 | 109 | 110 | 110 | 109 | 109 | 75,013,840 |
  | S1-empty | 108 | 110 | 106 | 111 | 110 | 110 | 72,884,364 |
- Generated each = advisory, markers, obstacle_points, depth_points, and `/tf`.
  Histogram remains B-H02 UNCERTAIN 138; B-H05 JUMP_CANDIDATE 108 / UNCERTAIN
  2; B-H08 JUMP_CANDIDATE 137 / UNCERTAIN 2; B-H13 STOP_CANDIDATE 108 /
  UNCERTAIN 2; B-H26b STOP_CANDIDATE 107 / UNCERTAIN 2; S1-empty
  STOP_CANDIDATE 108 / UNCERTAIN 2.
- Audited every regenerated MCAP: five child frames in each graph, no child
  parent conflict, and all marker/pointcloud frame IDs (plus depth and color
  optical frames) resolve to `wbr_ground`. The regression test composes the
  static camera chain and emitted `/tf`; a floor point in depth optical
  coordinates maps to ground z=0 within 1e-6 m. Generated `.mcap` files are
  ignored by git as intended.
- GUI import/render and visual color-field styling remain unverified.
