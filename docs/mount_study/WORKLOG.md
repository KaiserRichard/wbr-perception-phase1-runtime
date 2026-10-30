# Mount study worker log

- 2026-10-30: read session notes, profile, simcam scenario/run/depth interfaces,
  obstacle detector and advisory policy, ground-plane intrinsics and fitting
  convention, and team/model body geometry. Allowed edits restricted to
  `tools/mount_study/**` and `docs/mount_study/**`; central worklogs unchanged.
- Implemented pure analytic geometry, 54 configurations, body-relative camera XML
  wrapper, opt-in rendering, timeline aggregation, tables, JSON/CSV and plots.
- First no-render unit run: 7 passed, 1 failed because the expected VFOV fixture
  was mistyped (63.6127° versus calculated 63.6168917°). Corrected the fixture;
  no detector or geometry parameters changed.
- Ran the analytic artifact command successfully: 54 PENDING_RENDER rows; no CGL
  or MuJoCo rendering attempted. Plots contain analytic curves only.
- Documentation decision: treat far distance as approach-window-limited; separate
  held advisory from fresh detection and simulation-truth floor support. Mark
  Intel minimum-depth claim UNKNOWN without offline datasheet verification.
- Documentation added: REPORT.md, this log and generated results/TABLE.md.
  No external documentation, source, scenario library or owner-only file edited.
- Final checks: all 8 non-rendering unit tests PASS (0.044 s); analytic sweep
  completed with all 54 rows; Markdown lint PASS, 0 issues across 3 files.
- Handoff: conductor runs the exact test/render/lint commands in REPORT.md.
  Rendered blind/far distances and floor validity remain pending.
