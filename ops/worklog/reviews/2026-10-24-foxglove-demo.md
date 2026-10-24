# Foxglove offline detector demo (frame/layout follow-up)

- Changes: per-frame `/tf` aligns `wbr_ground` to the optical camera using the
  fitted/reused plane, marker array retains optical core markers and adds
  ground-frame obstacle cube/text, and stride-4 `/depth_points` has a `height`
  field. Layout fixed frame is `wbr_ground`, with follow mode off and both clouds
  enabled. README and the integration test were updated. No commits or pushes.
- Verification: requested Python ran
  `python -m pytest tools/bag_tools/tests/test_foxglove_demo.py -q`: 1 passed.
  The test checks one generated `/tf`, parent/child IDs and stamp, and the
  depth-cloud field names. Six MCAPs regenerated in `foxglove-demo-out/`; per-run
  counts and histograms are in `ops/worklog/sessions/2026-10-24-foxglove-demo.md`.
- Limitations: Foxglove GUI import/rendering and the layout's height color-field
  appearance were not available for validation. The converter uses current
  default `CoreParams`; this is offline current detector replay, not historical
  live node output.
- Claude: review this file and `tools/bag_tools/foxglove_demo_layout.json` for
  TF geometry and Foxglove layout importability.
