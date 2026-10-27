# Supervisor report revision — 2026-10-27

- Deliverables: `reports/2026-10-supervisor/main.tex`, compiled `main.pdf`,
  `README.md`, and one attributed external illustration in `figures/`.
- Owner-authorized structure: WBR perception / ORB-SLAM3, compact results,
  future integration. Title and student/supervisor details updated. Comparison,
  AGV implementation detail, standalone board section and glossary removed.
- D435i confirmed by owner; original dense-map plot label retained and qualified.
  Camera IMU integration remains unverified; historical EuRoC is explicitly
  stereo-inertial using the dataset's IMU.
- Read-only independent audit and conductor source checks confirmed: 3,639
  matched pose/reference samples, B-H05-D1p3 cluster-merging failure and differing
  plot/subset scope, current growing dense-map numbers, B-H08 UART replay scope.
  No measured values or original result-image bytes were changed.
- Validation: `latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex`
  succeeded; all eight pages rendered/inspected; no overfull/underfull,
  missing-character or unresolved-reference warnings. Placeholder and package
  checks passed; all five `[ngày]` slots remain; no new packages.
- Before-copy and build/render QA: `/tmp/wbr-supervisor-edit-20261027/`.
  No hardware or experiment execution. No new performance claims.
- Recommendation for review: assess readability and the extent of future-work
  detail; replace photo/video/CAN/IMU/date placeholders only with owner evidence.

## Owner follow-up: figure interpretation

- Removed requested extra concept-image and dense-title caption explanations;
  changed WBR subheading. Dense report title now D435i, rendered from saved PLY.
- Kept the separately committed Claude height figure byte-for-byte; identified
  the red X as the retained merged-cluster failure, not an isolated-book sample.
- Replaced distance scatter with per-trial signed cm errors, named objects/tape
  readings and zero reference. All eight evaluation rows preserved; reproducible
  renderer and source-hash/value receipt added under the report directory.
- Relayed distance/frame-total discrepancy documented in README; saved JSON values
  remain authoritative for this plot. No new measurement or detector execution.
- Final XeLaTeX build is eight pages with no font/reference/box warnings;
  rendered-page review confirms labels do not overlap. All original photo/video,
  CAN/IMU and five date placeholders remain.
