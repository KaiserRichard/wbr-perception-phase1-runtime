# Build and self-review log — 2026-10-13

## Scope and starting state

Read `BRIEF.md`, including its subsequent owner-generated-illustration addendum,
and repository `AGENTS.md`. Inspected Git status, branch
`feat/d435i-camera-capture-20260913`, recent history (HEAD `5932457`) and relevant
sources before writing. The checkout contained substantial existing work.
`slides_report/` contained the brief and builder logs, but no TeX/PDF to extend.
Those files were preserved. All new writes stayed inside `slides_report/`;
no Git mutation, upstream edit, hardware/camera process, ORB execution, SSH,
firmware/calibration action or network-configuration change occurred.

## Content review

- Followed the requested advisor-report outline: 16 main slides and exactly
  four backups. Split gate status and next steps for readable room-scale type.
  Omitted optional advisor requests because no concrete supported ask exists.
- Copied course preamble/theme/palette/fonts/macros/evidence badge; updated only
  report metadata and provenance comments. Added report-specific source helpers.
- Used TikZ for every diagram/chart. Reused only P04, copied unchanged. No
  cart-shaped robot assets, new image generation or missing illustration is used.
- Matched N0–N7 contracts to the course. N4A is independent of camera gates;
  N4B requires N3 plus stereo/calibration; N4C renews physical input load.
- Kept every status OPEN or PLANNED; successful builds and trajectories are
  never gate acceptance. Preserved SDK calibration warning and noise assumptions.
- Verified the paper value **0.036 m** in Campos et al. accepted manuscript,
  Table II, MH01 stereo-inertial row. Paper statistic is median of ten runs;
  slide 10 explicitly distinguishes our three-run results and median.
- Checked ATE numbers against `eval/ape_summary.txt`, power denominator against
  `power_window.log`, and decimal stereo payload arithmetic. No synthetic
  observations or invented measurements are presented.
- Retained USB ≥5000M, unchanged N2 raw profile/thresholds and mandatory 300 s
  soak. Stereo 30 Hz N4 development is separate from the 15 Hz IR1 N2 baseline.
- Documented stale inventory, kernel provenance mismatch, older prep receipts,
  SDK recording-format uncertainty, clock offset, storage and calibration limits
  in `SOURCES.md` and speaker notes.

## Build/review iterations

1. First XeLaTeX attempt failed because Beamer interpreted the title's opening
   brace as an inline frame title. Added `\relax` at the title frame opening.
   The failure is preserved in `qa/build-pass1.log`; it was not ignored.
2. Successful build (`qa/build-pass2.log`), then required Swift/PDFKit render
   at 1280×719. Inspected **every page 1–20 individually at full image size**.
   Found a gate-edge label overlapping its line, an awkward camera-independent
   wrap, a paper-chart label covering bar area, and a storage-table wrap too
   close to the bottom rule. Also clarified pending N7 authorization and the
   ATE variables.
3. Fixed the gate routing/label, shortened its node caption, moved the paper
   label to a separate legend, used sans-serif chart value labels, shortened
   the storage row and clarified N7/ATE wording. Rebuilt and re-rendered.
   Inspected **every page 1–20 again at original image size**, including all
   four backups. Final review findings are below.
4. Updated provenance comments only, rebuilt the final PDF, extracted text and
   checked page count/aspect ratio. Re-rendered the final PDF and compared all
   PNG digests to the reviewed images; identical pixels confirm the final
   artifact matches the visual review.

## Final page-by-page review

| Page | Review result |
|---|---|
| 1 | Clear title/date, sensor image intact; no robot geometry claim |
| 2 | One goal, large type, controller boundary explicit |
| 3 | Ownership and fault arrows readable; integration labeled planned |
| 4 | Full logical path visible; SDK adapter / ROS qualification distinction retained |
| 5 | Gate labels and all arrows separated; no text/edge collision |
| 6 | N0–N3 status and repository evidence paths legible |
| 7 | N4A–N7 status/paths readable; N7 bench review/tests pending |
| 8 | Current temporary platform and distinct serials correct |
| 9 | Known dataset, ground truth and unchanged example explicit |
| 10 | Zero-based bars match table; paper legend clear; statistic caveat visible |
| 11 | Supported scope and remaining uncertainties readable |
| 12 | Built/not-run status explicit; exact N4 profile and assumptions visible |
| 13 | Power denominator, timing limitation, historical storage, calibration and RAM distinguished |
| 14 | Ordered prerequisite exits, USB floor and mandatory soak retained |
| 15 | Calibration/offline/live order clear; no nominal-config qualification claim |
| 16 | Meeting closes on measured progress and OPEN gates; only Further detail deck mention |
| 17 | ATE definition, variables, rigid alignment and command readable |
| 18 | Three build patches and disabled-test limitation explicit |
| 19 | Sample proportions, historical flags and clock limitation visible |
| 20 | Decimal payload, historical probe and planned capacity readable; row clears rule |

## Final checks and reproduction

From `slides_report/`:

```sh
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
swift -module-cache-path qa/swift-cache qa/extract.swift
```

Final XeLaTeX/latexmk exit **0**; `main.log` has no TeX errors, warnings,
overfull or underfull boxes. Renderer exit **0**, **20 pages**.
PDF check exit **0**: **20 nonempty 16:9 pages**. Two complete visual inspections
finished; the final re-render matches reviewed PNGs. See `qa/build-final.log`,
`qa/render-final.log`, `qa/pdf-check.log`, `qa/pdf-text.txt` and
`qa/artifact-checks.txt`. `SHA256SUMS` identifies deliverable sources, PDF and
review renders. Existing historical artifacts remain untouched.

Limit: visual review used the required 1280-pixel full-page render, not a
physical projector trial. Hardware, calibration, real-time performance and
safety qualification remain OPEN; those were outside this document build.

FINAL

## Revision 2 — 14 October 2026

Scope: only “REVISION 2” in the brief. Read the brief, repository AGENTS.md,
14 October session addendum, 15 October lab runbook, existing TeX/theme,
README, source register and review log. Inspected Git status, branch
`claude/project-thread-rhsrup` and recent history (HEAD `cf09251`) before edits.
Substantial existing work was present; all writes stayed inside `slides_report/`.
The brief’s prohibition on Git mutations was followed: no index, branch,
commit or push changes. No camera, ORB-SLAM3, Pi/SSH or hardware action occurred.
Pre-revision TeX/PDF, README, source register and checksum manifest are retained
in `qa/revision2/`; historical review/build records remain unchanged.

Content and owner edits:

- Dated report/status to 14 October. Active hardware is 8 GB Pi, measured
  7.8 GiB, same card/supply; power remains unresolved. Removed unsupported
  no-swap completion/new EuRoC claims from the risk-table thread wording.
- Kept the owner’s page-4 data-path geometry and direct-library vs planned
  ROS 2 distinction; updated recorder status and notes only. Gate tables
  still have no path columns, sources remain in notes, and no unexplained
  “SDK” is visible. Kept risk-table layout and the original page-14 takeaway.
- Replaced stale built/not-run camera slide with still, failed moving-card,
  and 15-second RAM test observations. MicroSD blocking is INFERRED, not
  proven by an isolated causal test. Long RAM capture remains unverified.
- Added exactly one main slide: first-frame SIGSEGV, uninitialized current
  keyframe pointer, patch 4 applied in Pi copy, rebuild interrupted by power
  loss and pending verification. Historical EuRoC results remain unchanged.
- Next steps follow the lab plan: setup and entry gates, rebuild/linkage,
  100-second RAM capture, offline replay, Mac plot/review, live then summary.
  Power/calibration remain OPEN; room plot has no ground truth. No gate PASS.
- Unchanged USB ≥5000M, N1 → N2 → N3, exact N2 raw profile/rates/gaps and
  mandatory 300-second soak are retained in notes. The shorter stereo demo
  does not replace them. RAM budget is not qualified persistent storage.
- Updated patch/storage backups and source register. Existing theme, fonts,
  P04 and TikZ system retained. No new images or report-structure redesign.

Build and visual review:

1. An initial edit-script write used the wrong working-directory prefix and
   failed before changing the deck; corrected the path and applied edits.
2. XeLaTeX/latexmk completed successfully; rendered all 22 pages with the
   prescribed Swift renderer. Inspected changed pages individually at full
   1280×719 render size: 1, 4, 6–8, 11–17, 19 and 21.
3. Shortened the native-build inventory row and the storage payload row to
   avoid awkward dangling text. Clarified patch-4 rebuild status in the
   backup title/badge and updated the storage badge to match current tests.
4. Rebuilt/re-rendered the final PDF. Re-inspected pages 8, 19 and 21 at full
   size; inspected remaining pages 2, 3, 5, 9, 10, 18, 20 and 22 as well.
   Every page received visual inspection. No clipped text, overlapping
   labels/arrows or unreadable table was found. The owner’s camera-library
   caption retains its existing wrap and drawing geometry.

| Final pages | Review finding |
|---|---|
| 1, 6–8 | Date, distinct serial fields, active hardware and OPEN status correct |
| 4 | Owner diagram retained; no ROS 2 integration success implied |
| 9–11 | Historical three-run results/ATE comparison intact; sustained input unproven |
| 12 | Still shutdown gap, failed card take and short clean RAM test distinguished |
| 13 | Crash path, applied patch and pending rebuild clear; no claimed fix verification |
| 14 | Owner risk-table format retained; power, storage, calibration and RAM limits explicit |
| 15–16 | Demo order and reviewed exits readable; owner takeaway retained |
| 17 | Summary matches addendum; no PASS, safety boundary unchanged |
| 18–21 | Four backups legible; patch and current storage updates consistent |
| 2–3, 5, 22 | Goal/boundary/gates and existing references retained |

Final verification and reproduction (from `slides_report/`):

```sh
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
swift -module-cache-path qa/swift-cache qa/revision2/extract.swift
shasum -a 256 -c SHA256SUMS
```

Build exit **0**; no TeX errors/warnings/overfull/underfull boxes in `main.log`.
Render exit **0**, **22 pages**: 17 main, four backups, existing references.
PDF check exit **0**: nonempty 16:9 pages; no visible source lines, evidence
paths or unexplained SDK. See `qa/revision2/build-final.log`,
`render-final.log`, `pdf-check.log`, `pdf-text.txt`, and checksum results.
README allocates approximately 15 minutes to the main slides; that is a
presentation plan, not a timed rehearsal. Review used desktop renders, not a
projector trial. Session evidence is summary-reported; no fresh hardware
validation was attempted and no raw experimental evidence was changed.

REVISION 2 FINAL
