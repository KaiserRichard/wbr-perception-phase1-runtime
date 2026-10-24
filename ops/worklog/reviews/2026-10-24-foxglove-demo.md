# Foxglove offline detector demo

- Changes: offline SQLite bag converter, importable Foxglove layout, README
  instructions, and synthetic rosbag integration test. No commits or pushes.
- Verification: `python -m pytest -q tools/bag_tools/tests/test_foxglove_demo.py`
  passed (1 test). Every message in all six MCAPs deserialized with the Jazzy
  typestore; source depth and marker header stamps/frame IDs matched, `/tf_static`
  existed, and RealSense Metadata was absent.
- Outputs: worktree fallback `foxglove-demo-out/`; six MCAPs, 51.4–67.7 MiB.
  Archive path was outside the writable sandbox. Per-run exact counts and
  advisory histograms are in session `ops/worklog/sessions/2026-10-24-foxglove-demo.md`.
- Limitations: Foxglove GUI import/rendering was not available for validation.
  Detector state uses current default `CoreParams`; output is offline current
  detector replay, not the node's historical live output.
- Claude: review this file and `tools/bag_tools/foxglove_demo_layout.json` for
  Foxglove layout importability.
