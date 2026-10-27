# Supervisor report edit — 2026-10-27

- Owner confirmed D435i and authorized the requested Vietnamese rewrite.
  Edited the existing report project in place on its existing feature branch;
  no hardware/network experiment was started.
- Read TeX, extracted and rendered all eight original PDF pages. Preserved a
  before-copy outside git in `/tmp/wbr-supervisor-edit-20261027/before/`.
- Changed title/student/supervisor details, removed comparison/AGV/standalone
  demo-board/glossary sections; reduced repeated discussion. Replaced diagrams
  with aligned Atlas feedback and neutral dashed verification boundaries.
- Added an unchanged CC BY-SA 4.0 Commons illustration with author/license/source.
  All four original result images and names remain unchanged.
- Independent read-only evidence audit identified plot/subset distinction,
  the recorded B-H05-D1p3 clustering/setup issue, EuRoC stereo-inertial scope and
  matched pose/reference count, correct dense variant, and B-H08 UART scope.
  Corrected wording without changing the reported measured values.
- First XeLaTeX authoring pass exposed missing paragraph breaks around tables and
  bibliography `\\` being parsed with the next `[2]` label as a length. Fixed
  actual errors; final build succeeds, no box/font/reference warnings.
- Final checks: eight pages rendered; original placeholders and all five date
  slots preserved; no new packages; measured result figures unchanged.
- Sources and rebuild instructions are in the report README. No new measurements.

## Owner follow-up: caption and plot clarity

- Preserved Claude's newly committed height-plot annotation (e23de0d); caption
  now identifies its red X as the merged book/lamp failure.
- Removed the requested extra caption caveats; replaced the WBR subheading with
  natural wording and relabelled the report dense map D435i from the archived
  PLY, without changing the archived source.
- Replaced the unlabelled distance scatter with signed cm error per trial, object
  and tape-distance labels, zero reference and a separate failure marker. All
  eight saved rows remain; JSON receipt stores exact plotted values/input hashes.
- Local evaluation says 1.30m/136 processed frames vs relayed 1.38m/137; kept
  saved values, noted discrepancy in README, did not add disputed numbers.
- Rebuilt with XeLaTeX and inspected eight pages. No new measurements/packages.
