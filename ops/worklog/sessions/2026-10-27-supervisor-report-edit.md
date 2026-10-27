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
