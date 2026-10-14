# Build and self-review — 13 October 2026

Scope: read the brief and retained existing `logs/`; no previous main source/PDF was present. Inspected Git status, branch (`feat/d435i-camera-capture-20260913`), recent history and relevant sources before writing. The brief explicitly forbids branch/index/commit changes, so all writes stayed inside `slides_progress/` and no Git mutation occurred. Existing unrelated working-tree changes were retained. No coordination with the report builder.

## Content audit

- 43 pages: where we are 1–4; today's work 5–18; programs 19–27; runbook 28–38; tools/sources 39–41; agent direction 42–43.
- Reconciled authoritative October facts with older PROJECT_STATE/NEXT_GATE drafts. New-unit SDK, ASIC, firmware-update and descriptor identities stay distinct. September evidence is historical.
- Verified published comparator against Campos et al., accepted T-RO paper, arXiv v2, Table II: MH01 stereo-inertial ATE 0.036 m. Retained the distinction between paper median of ten and project mean of three; do not claim exact protocol reproduction.
- Checked result numbers against N4A REPORT.md and saved evo summary. Under-voltage 87/178 samples, wall durations and clock offset retain their limits. No timing PASS; no D435i accuracy claim.
- Checked recorder/profile, CLI and IMU association behavior against current C++/patch/plan. Documented `.db3` current source versus `.bag` older prose. Build status comes from authoritative session facts, not an independent Pi audit in this task.
- Candidate intrinsics/baseline/extrinsics are SDK readback/nominal geometry; noise is ASSUMED; calibration/time offset remain OPEN. Preserved warning provenance and built-never-run status.
- N1→N2→N3, own-camera USB ≥5000M, exact raw IR1/15 + gyro/200 + accel/100, rate/gap bands and mandatory 300 s soak remain intact. Stereo/30 is a separate extension. Commands are future shapes, with explicit CAMERA AVAILABLE entry.
- OS-card migration does not qualify bulk data storage. Destructive disk identities/procedure require review; no cloning was performed. Calibration and Allan tool/import integration remain PLANNED; unknown acceptance budgets were not invented.
- Reference citations checked against extracted text of the actual 109-page course PDF (`qa/reference-text.txt`, `qa/reference-page-index.tsv`), not blindly against source comments. Source-order/frame numbering differed by one. Methods remain useful despite older reference status.

## Build/review loop

1. Generated 42 initial pages, preserving reference preamble/theme/fonts/palette/evidence helper. First build succeeded but revealed vertical overflows.
2. Replaced long command block titles with compact command panels, shortened source footers and repetitive runbook prose. Preserved font/canvas size and all thresholds. Subsequent builds isolated the remaining crowded runbook pages; shortened those further.
3. Added a source-key page (43 total). Fixed a LaTeX optional-spacing interpretation of `[F]` after a table rule. Kept intermediate build logs in `qa/build-1.log` through `qa/build-6.log`.
4. Rendered with the prescribed Swift/PDFKit utility. Inspected every page individually at native 1280×720 resolution: 1–6, 7–12, 13–18, 19–24, 25–30, 31–36, 37–43. Checked title/footer, prose, tables, formulae, arrows, labels, command panels and evidence wording.
5. Fixed result/source/checkpoint text flowing alongside tables by adding explicit paragraph termination; routed emitter and live-bypass arrows away from labels/boxes; shortened an awkward diagram label. Rebuilt and re-rendered; individually re-inspected affected pages 1–7, 17, 20–21, 26–27, 41, 43. Raised system-map labels and completed the bypass/source corrections; re-rendered and inspected 2, 26, 41 again.
6. Final exact build: `latexmk -xelatex -interaction=nonstopmode main.tex`. Exit 0, 43 pages, no LaTeX error and no overfull/underfull box warning. Prescribed render returned 43. Static document checks confirm 43 frames/PDF pages/PNGs and required profile/soak/results. `qa/validation.txt` records these checks. These are document checks only.

Reproduction: see README.md. `qa/provenance.json` records SHA-256 of source evidence, reference PDF/TeX and final deck/generator. `preview/` contains all final PNGs. No camera, ORB, sensor capture, SSH, calibration/firmware change, network setup or deployment was run. All engineering gates remain OPEN.

FINAL

## Revision 1 — continuation of the existing build

Read BRIEF.md and retained the existing 43-page content, generator, QA artifacts and previous review history. Before edits inspected status, branch (`claude/project-thread-rhsrup`) and five recent commits. The brief prohibits Git branch/index/commit mutations; no Git mutation occurred. All writes stayed inside slides_progress/.

- Added a proper page-1 cover using the reference cover's centered navy title, teal subtitle/rule, platform column and dated owner-guide line. Reused P04 (D435i) locally; no new image, cart robot or orange circle. Updated PDF title/subtitle/date metadata.
- Converted the old opening page to the ordinary content slide “Where we are” (page 2), keeping Today/Next boxes and a compact agenda table. Updated the route: context 2–5, work 6–19, programs 20–28, runbook 29–39, tools/sources 40–42, agent tickets 43–44. No other internal progress-page references needed a shift.
- The current course PDF is 91 pages, superseding the 109-page edition described in the earlier record. Extracted every current reference page and checked cited topics/page ranges. Existing reviewed main.tex already used current citations; synchronized the stale generator's citation inputs to those exact values and removed automatic page subtraction. Its generated content now matches reviewed main.tex exactly. Archived prior provenance; refreshed current artifact/reference hashes.
- Rechecked October session facts, saved SE(3) evo results and historical PROJECT_STATE/NEXT_GATE caveats. Retained thresholds, qualified status labels and all OPEN gates; no new hardware claim. Prior paper verification remains prior-builder provenance; no new external paper verification was performed in this cover revision.
- Initial cover build exposed Beamer interpreting its opening brace as an inline frame title. Added the reference cover's explicit `\relax`; rebuilt successfully. Failure and correction logs are retained as qa/build-revision1-1.log and qa/build-revision1-2.log.
- Rendered the corrected PDF with the prescribed Swift utility. Individually inspected all 44 pages at full native size, in groups 1–6, 7–12, 13–18, 19–24, 25–30, 31–36, 37–42, 43–44. Checked cover/title/agenda, diagrams, tables, commands, footers, evidence labels and reference citations. No remaining clipping, overlap, stray orange circle or layout correction was found. Actual PNG dimensions are 1280×719: the prescribed renderer truncates the scaled PDF height to an integer. Corrected README's old 1280×720 claim; no renderer change.
- Final prescribed build `latexmk -xelatex -interaction=nonstopmode main.tex` exited 0. XeLaTeX log has no errors, missing characters, overfull or underfull boxes. Verified 44 frames/PDF pages/previews, native preview dimensions, reading route, mandatory 300 s soak, rate/gap thresholds, measured RMSE values, authorization language and exact generator round trip. See qa/validation-revision1.txt, qa/build-revision1-final.log and qa/provenance.json.

Reproduce with the commands in README.md. These are document checks only. No camera, ORB, sensor, firmware, calibration, network, deployment or Pi action occurred. Historical evidence and other builders' folders were untouched.

REVISION 1 FINAL
