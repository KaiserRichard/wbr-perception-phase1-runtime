# Phase-2 review log

FINAL — 2026-10-10. Deck-layout and authoring-tool QA passed; no hardware gate qualification is claimed.

## Continuation and scope

Continued the existing 89-page Phase-1 outline, schedule and P01–P12 prompt batch. These files were preserved. Added the LaTeX/PDF, modular content generator, non-overwriting image assignment utility, documentation and QA artifacts inside `slides_course/`. Inspected branch, status, recent history and relevant sources before editing. The OS repository and upstream source were read only. No Git mutation, camera-dependent command, SSH, sensor capture, firmware/calibration change or ORB-SLAM3 execution occurred.

## Review rounds

1. Initial generation/build: resolved LaTeX escaping, equation/underscore handling and the cover's dimension parsing. Build logs are retained in `qa/build-round*.txt`.
2. Clean build and first visual review: rendered and opened all 89 individual pages at original 1280 × 719 size, plus a contact sheet. Found crowded illustration columns, axis/header collisions, ambiguous queue ordering, overly long box labels, mixed-unit result axes and a conclusion rendered as a divider.
3. Layout/content corrections: reduced diagram geometry rather than body font size, shortened crowded bullets/labels, moved N0/N4B entry criteria above their columns, corrected FIFO wording, added explicit interpolation samples and reset transitions, separated result panels by unit, expanded abbreviations and restored the substantive conclusion on page 88. A polish rebuild exposed an escaping issue; it was fixed before review continued.
4. Final review: rebuilt cleanly, rendered again and inspected every page individually at full size. Standardized figure-reference wording. Corrected page 26's optical-axis geometry to x right, y down and z forward, then rebuilt, rerendered and rechecked that page. The final contact sheet was also inspected. No remaining overflow, overlap, missing glyph or broken diagram was found.

The full page/title inventory is in `qa/PAGE_LIST.md`; `qa/page-review.tsv` records all 89 page verdicts. `qa/final-artifacts.json` hashes the reviewed artifacts. The verdict covers the deck and tooling, not a Pi or robot gate.

## Final checks

| Check | Result |
|---|---|
| Mandated XeLaTeX/latexmk build | Exit 0; 89 PDF pages |
| TeX log errors, overfull/underfull, missing characters, undefined references/citations | No matches |
| Mandated Swift rendering | Exit 0; 89 individual 1280 × 719 PNGs |
| Individual full-size visual review | 89/89 reviewed; corrected page 26 rechecked |
| Figure numbering | 56 unique labels, strictly increasing 1–56; all referenced |
| Figures retained/dropped | 44 exact TikZ figures + 12 illustration slots; none dropped |
| Source/evidence labels | Historical sessions separated from current UNKNOWN/PLANNED qualification |
| Result plots | Three empty result figures; no fabricated samples |
| Image assignment fixtures | Synthetic ordering, fallback mtime, dry-run, idempotence and occupied-slot preservation passed |
| Git whitespace check | `git diff --check`: no output |

The inherited moloch theme, palette, typography, margins, figure/evidence/takeaway macros and body sizing were retained. Technical drawings use TikZ. Every figure has a nearby textual reference and caption. A single references page links verified primary records. More detailed requirements, source warnings and operational context appear in speaker notes. The local checks and their raw output are in `qa/check_deck.py`, `qa/check-results.txt`, `qa/build-final.txt`, `qa/render-final.txt` and `qa/figure-number-check.txt`.

## Placeholders and limitations

No illustration downloads were present. Visible named placeholders remain at P01/page 1, P02/4, P03/10, P04/12, P05/19, P06/24, P07/29, P08/37, P09/51, P10/59, P11/67 and P12/87. These are intentional under the brief, not missing-file build failures. Generate them with the preserved `image-prompts/BATCH.md`, assign with `images/assign.py`, visually check content/hardware and repeat build/render/review.

No Pi gate has passed. The historical 105-second capture is not N2; USB ≥5000M, the exact IR1/raw-motion profile, timing thresholds and mandatory 300-second soak remain intact. Stereo qualification is a separately reviewed extension. Hardware, calibration, storage, accuracy, live timing and controller behavior remain unqualified. The document makes no new architecture, public API, message or experiment-format implementation change.

Reproduction commands, environment requirements, source provenance and image workflow are in `README.md`. No unresolved deck-layout issue was found in the final rendered snapshot; the twelve missing illustrations and all unmeasured hardware outcomes remain explicit.

## PHASE 3 — depth revision, 10 October 2026

Continued from the existing 89-page builder state. Preserved `qa/main-v1.pdf`, Phase-1 outline/prompt batch/schedule, Phase-2 review records and source hashes. All writes stayed inside `slides_course/`; the OS repository and upstream sources were read only. Git branch/index/stash/commits were untouched. No Pi, camera, ORB-SLAM3, controller or capture command was executed.

The final deck has 109 pages. `phase3_depth.py` provides a modular revision layer over the existing generator. Gate pages now separate purpose/entry/tools/artifacts from acceptance tables with measurement, clock and evidence fields. N4A, N4B and N4C each have separate contracts. N4A depends on N0 in the hardware gate graph; N4B needs N3 plus the reviewed stereo extension/calibration; live work needs accepted offline inputs and renewed transport evidence. Future command examples follow the checked repository utilities or pinned upstream entry point. Absent converter, live-driver and N6/N7 harness commands are identified as PLANNED rather than invented.

Added process/thread/queue ownership, exact baseline topic/type/rate/QoS tables, static/dynamic TF owners, timestamp fields and stamping locations, same-clock latency decomposition with mapping uncertainty, settings parser/noise scaling details, planned health envelope and receiver fallback semantics. Symbolic window-coverage and ATE examples, RPE pairing policies and trajectory conversion explain the measurement method without fabricated results. Tables and two-column layouts replace selected generic flows. Removed both “Figure N explains …” and illustration lead-in filler; references now occur in substantive bullets, captions or takeaways.

### Revision and visual rounds

- Rounds 1–3: expanded gate contracts and diagrams; corrected table widths and paragraph boundaries after initial horizontal/vertical overflow. Restored displaced P09/P10 slots on substantive provenance pages.
- Rounds 4–6: inspected rendered diagrams and corrected arrow-label collisions in the data-path, clock and boundary drawings. Adjusted TikZ spacing without shrinking body typography. Removed a misleading N4A-to-N4B dependency arrow. Added exact baseline message types, stationary content criteria and four IMU noise keys.
- Final rounds: inspected pages 1–109 individually at original 1280 × 719 resolution. Corrected escaped arrows in failure summaries/settings and rechecked pages 45, 61, 66 and 67. Expanded technical abbreviations, corrected YAML expansion, removed remaining illustration filler and corrected roadmap ordering. Rechecked every page changed by these final edits, including the illustration layouts. Unchanged pages retain the earlier individual inspection within this Phase-3 review.

Final inspection found no remaining overflow, text/arrow overlap, clipped caption/footer or unreadable diagram. Intentional section dividers, symbolic examples and pending illustration slots retain their designed whitespace. This verdict concerns deck presentation and source consistency, not runtime qualification. The per-page ledger is `qa/phase3-page-review.tsv`; `PASS_LAYOUT` never denotes a Pi gate PASS.

### Reproduction and validation

```sh
cd slides_course
python3 build_deck.py
python3 qa/phase3_inventory.py
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
python3 qa/check_deck.py
```

Final evidence: `qa/phase3-build-final.txt`, `qa/phase3-render-final.txt`, `qa/phase3-check-results.txt`, `qa/phase3-figure-number-check.txt`, `qa/PHASE3_PAGE_LIST.md` and `qa/phase3-final-artifacts.json`. The final XeLaTeX log has no overfull/underfull boxes, missing characters or undefined references. Structural and explicitly synthetic assignment tests passed: 109 actual pages, preserved 89 outline markers, 46 unique figures referenced and numbered consecutively, all twelve P-ids, three empty result-axis figures, mandatory raw thresholds/calibration warning, no filler or accidental tab escapes. The initial structural checker incorrectly expected inserted frames to add original-outline markers; corrected it to check preserved markers and actual frame/section count separately. `git diff --check` produced no output. No hardware PASS is claimed.

### Sources, placeholders and limits

Revision provenance, primary-source verification and unresolved implementation choices are recorded in `qa/PHASE3_SOURCES.md`. The inherited OS preamble/theme/palette/fonts/macros remain in use. No architecture, API, message, firmware or dataset implementation was changed. N4–N7 numeric budgets, health rate/transport/age bound, live adapter and converter remain UNKNOWN/PLANNED pending the required reviews.

Visible illustration placeholders: P01/page 1, P02/4, P03/10, P04/12, P05/19, P06/25, P07/30, P08/38, P09/55, P10/74, P11/86 and P12/107. Results pages 96–98 remain empty and marked “To be filled after N4/N5 runs”. No gate has passed on the Pi; historical evidence is retained as historical. Fresh N0 is the next runtime step; N1 onward remains conditional on explicit CAMERA AVAILABLE. The exact raw profile, USB ≥5000M, timing thresholds and mandatory 300-second N2 soak are unchanged.

PHASE 3 FINAL


## PHASE 4 — Visual image assignment and small fixes (2026-10-10)

Continued the existing 109-page Phase-3 deck. All writes remained inside `slides_course/`; no branch, index, stash, commit or push change and no camera, Pi or runtime command was performed. Earlier prompt/outline files, historical QA records and `qa/main-v1.pdf` were preserved.

### Visual assignment

Opened every one of the twelve `images/incoming/` PNGs individually at original 1672-pixel-wide resolution. Matched subject and must-show content against `image-prompts/BATCH.md`, without using timestamp or UUID order. Each image has one distinct best-match slot; no unmatched or duplicate subjects. Copied unchanged originals into `images/P01.png` through `P12.png`. SHA-256 checks confirm byte-identical copies and unchanged originals. `images/MAPPING.md` records original filename, subject and retained defects; `images/phase4-assignments.json` records provenance hashes.

Retained image limitations include robot silhouettes without clear biped legs (P01/P02/P07/P12), black generic controller boards (P01/P07), invented miniature board markings and simplified cooler geometry (P01/P05/P07/P09), generated tag-like target patterns unsuitable for actual calibration (P08), and weakly distinguishable stereo viewpoints (P10). No fabricated experiment result, measured numerical display or gate PASS was seen. These are conceptual assets; assigned as the brief requests, not regenerated or edited. No illustration placeholders remain.

### Layout rounds

Round 1: moved page 20's detached kernel/SDK and ROS-topic labels into the relevant wrapper and reader-queue boxes in `phase3_depth.py`, then regenerated `main.tex`. Built the deck and inspected all twelve image-bearing PDF pages at full 1280 × 719 resolution: 1, 4, 10, 12, 19, 25, 30, 38, 55, 74, 86 and 107. Every image retains its full composition and aspect ratio; captions, text and footers are clear. No image layout change was needed. Page 20's taller wrapper box crowded the recorder branch, which was corrected in round 2 by shortening box text and spacing the lower row and connector. The initial renderer was inadvertently launched before PDF generation finished and failed on the incomplete PDF; rerun successfully after build completion.

Round 2: rebuilt and rendered all 109 pages, then inspected final page 20 at full size. Labels are attached inside their boxes; the recorder arrow has clear space between rows with no box/text overlap. The final twelve image-page PNGs are byte-identical to the individually reviewed round-1 renders, confirmed by hashes. `qa/phase4-page-review.tsv` lists the 13 reviewed PDF pages and their titles. Unchanged non-image pages retain their Phase-3 review; Phase 4 did not repeat that broader content review.

### Reproduction and validation

```sh
cd slides_course
python3 build_deck.py
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
python3 qa/check_deck.py
rg -n '^!|Overfull|Underfull|Missing character|undefined' main.log
```

Run rendering only after latexmk finishes. Final build succeeded; error/warning grep produced no matches (rg exit 1 for an empty match set). Offline structural and synthetic assignment checks passed: 109 pages and 46 unique referenced figures. Figure numbering remains consecutive 1–46; all twelve illustration figures are used and none dropped. The renderer reports 109 pages. Copy hashes and final reviewed-page hashes pass. `git diff --check -- slides_course` produced no output. Evidence: `qa/phase4-build-final.txt`, `qa/phase4-render-final.txt`, `qa/phase4-check-results.txt`, `qa/phase4-figure-number-check.txt`, `qa/phase4-reviewed-image-pages.json` and `qa/phase4-final-artifacts.json`.

Updated `README.md` to describe this visually assigned incoming batch and the actual image pages. The chronological assignment utility is unchanged and was not used for this batch. No new source claims, measurements, gate decisions or interface design were introduced. The deck remains at 109 pages; empty results axes and no-Pi-gate-PASS status are unchanged. Presentation checks and synthetic fixtures do not qualify hardware.

PHASE 4 FINAL

## PHASE 6 — Curated deep reference C (2026-10-13)

Read advisor deck A (20 pages) and progress deck B (43 pages) and confirmed both REVIEW_LOGs end FINAL before curating C. Continued the existing 109-page Phase-3/4 deck; Phase-5 artifacts/module were already present, but the incoming main deck still had 109 pages. Reused the existing status/results correction functions without adding a separate daily progress section. No earlier phase was restarted.

The required pre-curation `qa/main-v3-109p.tex` and `.pdf` already existed. TeX was byte-identical to incoming main.tex (SHA-256 in PHASE6_SOURCES); preserved these backups and every historical QA record. Git status, branch and recent history inspected first; no Git mutation. All authoring inside C, except the brief's explicit exception for B's numeric reference edits and rebuild. No runtime/hardware commands.

### Curation and evidence

`qa/PHASE6_AUDIT.md` lists KEEP / MERGE / CUT / UPDATE and a reason for every incoming page 1–109. Seven empty section-divider pages and the redundant symbolic ATE example were cut. Eleven prose pages were merged into their operational destinations, preserving their full teaching text, commands and source notes in destination speaker notes. Added one short Changes since 2026-10-10 page. Final C: **91 pages**; depth and preservation requirements determine this count.

All **46 figures** retained: 34 TikZ/mathematical figures and 12 conceptual illustrations, numbered consecutively and referenced. No illustrations regenerated or dropped; known hardware/target defects remain in images/MAPPING.md. No placeholders. All **11 gate acceptance tables are byte-identical** to incoming tables, including thresholds, measurement clocks and evidence columns. Exact raw profiles, USB >=5000M, timing bands and mandatory 300-second soak remain intact. N2's accept-n2 command is preserved in the evidence page notes.

Reconciled current hardware (4 GB / 32 GB microSD stand-in, no NVMe), new-unit serial fields, factory NOMINAL geometry/ASSUMED noise, prepared association helper and built-never-run offline/live programs. Populated results pages **80–82** with source-backed N4A ATE, wall-duration, memory, power and sampled-temperature summaries. RPE, per-frame timing/queues/loss and missing resource series stay visibly empty. Verified the paper Table II comparator 0.036 m and ten-run median; project mean of three is a different statistic. N4A remains MEASURED / OPEN under C's own N0-health/ATE-RPE/budget criteria; no gate promoted.

### Build and visual rounds

1. First curated build found one vertical overflow on N5 and an unescaped imu_utils name. Fixed both without reducing font size.
2. Built/rendered 91 pages; inspected **each page individually at full 1280×719 resolution**, after the contact-sheet overview. Checked text/diagram/table geometry, captions, image aspect ratios, footers and evidence wording. Removed the redundant objectives block, corrected remaining older calibration labels and the active-settings takeaway; expanded metrics before use. Shortened boundary/acceptance wording and adjusted the ATE heading/placeholder line break.
3. Final build/render: 91 nonempty 16:9 pages; re-inspected all **12 changed renders** (5, 14, 28, 36, 38, 41, 59, 60, 72, 80, 88, 89) at full size. The other 79 final PNGs are byte-identical to their individually inspected round-2 PNGs. `qa/phase6-page-review.tsv` records all 91 page verdicts and final hashes. No overlap, clipping, overflow, broken TikZ or figure-reference defect remains. Intentional formula/reference whitespace is retained; presentation verdicts do not qualify hardware.

Some intermediate authoring commands used the wrong relative working path and did not perform the intended write/build; corrected and rerun. An audit-reason lookup failed before writing main.tex; fixed it. The first structural comparison incorrectly included the preamble's parameterized figure helper (`#1`); narrowed that comparison to document body. Final logs/checks below identify the actual deliverables; no failed attempt is labeled successful.

### B reference-only exception

After final C review, updated **43 numeric reference arguments** in `slides_progress/main.tex` using the audited old-to-new map. Our reference-only result changes no other source bytes, verified against `qa/phase6-progress-before.tex` and reconstructed in `qa/phase6-progress-reference-only.tex`. Rebuilt B with XeLaTeX and rendered/extracted into C's QA directory; initial B **43 pages**, all individually inspected at full size for reference/footer fit. Every PDF reference matches the final C page map.

During final artifact checks, a concurrent builder added B's cover, adjusted the reading route and preamble metadata. Preserved those edits; did not revert or overwrite them. `qa/phase6-progress-concurrent.tex` and `.diff` distinguish concurrent changes from this task's numeric-reference-only result. Rebuilt/checked the current **44-page B** (latexmk up-to-date, exit 0), rendered and extracted it. Inspected current pages 1/2/30/40 at full size; current pages 3–44 have exactly the previously reviewed page bodies, excluding pagination pixels (two one-pixel anti-alias differences were initially outside the mask; enlarged the footer mask, not the document). All 43 reference fields still match C, every bound 1–91. Both logs clean. Only numeric references in B were authored by this task; B's other files and concurrent edits were preserved. For deliberate B regeneration, verify the saved reference mapping before rebuilding.

### Reproduction and final checks

```sh
cd slides_course
python3 build_deck.py
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
python3 qa/check_phase6.py
swift -module-cache-path qa/swift-cache qa/phase6-extract.swift main.pdf
# B source already contains updated references; rebuild it without regenerating:
cd ../slides_progress
latexmk -xelatex -interaction=nonstopmode main.tex
```

Exact generator reproduction verified without rewriting TeX: build_deck.py → phase3_depth.py → phase6_curate.py yields the reviewed main.tex. C and B latexmk exit 0; warning/error search is **empty**. C renderer reports **91**; initial B **43**, current B **44**. `qa/check_phase6.py` passes 91 frames, 109 audit rows, all 46 unique/referenced consecutive figures, unchanged gate tables and raw thresholds. PDF title extraction independently agrees with all 91 mapped pages. `qa/phase6-progress-validation.txt` verifies B source scope and rendered references. These are offline document checks only.

Evidence: `qa/phase6-build-final.txt`, `qa/phase6-render-final.txt`, `qa/phase6-check-final.txt`, `qa/phase6-pdf-text.txt`, both page-review ledgers, old-to-new map, B reference-change JSON/current build/render/text/concurrent-source records, `qa/PHASE6_SOURCES.md` and `qa/phase6-final-artifacts.json`. Surplus old preview pages 92–109 are preserved in `qa/phase6-obsolete-preview/`; current preview contains exactly 91 pages. No camera, capture, ORB execution, Pi/SSH, network, firmware/calibration, storage migration, upstream edit, controller test, commit or push. Qualification and physical safety remain OPEN; visual review is not a projector/hardware trial.

PHASE 6 FINAL

## PHASE 7 — Calculated N4A RPE in C and B (2026-10-13)

Continued the existing Phase-6 FINAL state; no previous phase was restarted. Inspected Git status, branch and recent history first. The Phase-7 exception authorizes B's RPE edits and rebuild; all other authoring stayed inside C. No Git index/branch/stash/commit/push mutation, no experiment evidence edit, no runtime/SSH/camera/ORB execution. Preserved incoming C/B TeX/PDF and preview hashes in `qa/phase7-baseline/`.

### Changes and provenance

C page 80 replaces the empty RPE panel with per-run SE(3) RPE translation RMSE **0.013295 / 0.013559 / 0.014021 m** and rotation RMSE **0.076464 / 0.076776 / 0.074883 deg** at 1 s, labeled CALCULATED. Retained ATE/paper plot, figure D76 (Figure 42), and D435i accuracy UNKNOWN. Diagnostic Sim(3) ATE **0.018874 / 0.023794 / 0.022288 m** is labeled CALCULATED and explicitly fits scale; SE(3) remains the stereo-inertial paper metric. C pages 59/60 no longer call N4A RPE missing; page 76 labels the N4A calculation and records its pairing/provenance in notes. Gate acceptance tables and thresholds are unchanged; N4A remains OPEN for stable power and reviewed budgets.

B page 17 states the calculated values, shared-clock assumption, zero offset, 0.02 s association tolerance, first reference endpoint at least 1 s later and no interpolation. Its takeaway explains local drift (~1.3 cm over 1 s) versus global aligned-path ATE. B pages 19/41 remove stale RPE-unproven/PLANNED wording. Page count retained. Calculation source/footer and notes distinguish traj_eval from evo RPE filters.

Source: unchanged `qa/n4a-traj-eval-summary.md`, supplied from `tools/trajectory_eval/traj_eval.py`, branch `claude/project-thread-upkfjv`, commit `d3f9540`, PR #2, not yet merged. Flags: `--t-max-diff 0.02 --t-offset 0 --align-both --rotation-ate --rpe-delta 1 --rpe-unit s`. The supplied report/README states that SE(3) ATE reproduces saved evo values and tool validation passed; this task did not rerun evaluator validation. **3,639 is the timestamp-associated pose-pair count per run**, not a newly asserted count of eligible 1 s RPE intervals. Pairing takes one first qualifying endpoint per eligible start without interpolation. This calculation does not establish frames, calibration, clocks, live performance or gate PASS.

Persistent C edits live in new `phase7_rpe.py`, called after curation by `build_deck.py`; B's generator carries only the same RPE edits. README now reflects calculated RPE. Historical Phase-6 audit/QA records remain unchanged. Captured generator writes in memory to verify exact regeneration without rewriting historical audit files.

### Build, render and review

First C layout overflowed by 99.3 pt because the diagram and table used incompatible top baselines. Center-aligned the two minipages; final log is clean. Some authoring commands initially used a wrong relative working directory and failed without writing; corrected paths and reran. B generator comparison exposed an extra paragraph marker/newline; fixed generator formatting without altering reviewed output.

Built and rendered both complete PDFs. Individually inspected **all seven changed pages at full 1280 × 719 resolution**: C 59/60/76/80 and B 17/19/41. Tables, formulas, ATE ticks/comparator, RPE units, labels, captions and footers are readable with no overlap or clipping. All **128 unchanged page PNGs** are byte-identical to the saved previews, retaining previous full-page review. C remains **91 pages**, B **44**. No new/dropped images or figures; C retains all **46** uniquely referenced figures numbered consecutively 1–46. No placeholders added; missing timing/resource axes remain intentionally empty. No unresolved Phase-7 layout issue. The tool's unmerged status and unqualified D435i/live behavior remain explicit limitations.

### Reproduction and checks

```sh
cd slides_course
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
cd ../slides_progress
latexmk -xelatex -interaction=nonstopmode main.tex
cd ../slides_course
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift ../slides_progress/main.pdf ../slides_progress/preview
PYTHONDONTWRITEBYTECODE=1 python3 qa/check_phase7.py
python3 qa/check_phase6.py
rg -n '^!|Overfull|Underfull|Missing character|undefined' main.log ../slides_progress/main.log
```

Both latexmk builds exit 0. Warning/error grep: **empty** (rg exit 1 for no matches). Renderers report 91/44 pages. Offline document checks pass: intended source scope and exact values/provenance, byte-identical acceptance tables, exact C/B generator reproduction, all unchanged render hashes; inherited Phase-6 checks pass figure numbering and raw gate thresholds. These checks qualify documents only.

Evidence: `qa/PHASE7_PAGE_LIST.md`, `qa/phase7-reviewed-pages.json`, `qa/phase7-final-artifacts.json`, final course/progress build/render logs, PDF text extractions, `qa/phase7-check-final.txt`, `qa/phase7-inherited-check.txt`, and incoming source/PDF/hash backups. Earlier failed/intermediate logs are retained as such. PDFs: `main.pdf` and `../slides_progress/main.pdf`.

PHASE 7 FINAL

## PHASE 8 — October 14 audit and session facts

Continued Phase-7 FINAL from the incoming 91-page deck; did not restart earlier phases. Before edits inspected Git status, branch and recent history, BRIEF, current source/generator/review records, the academic Beamer skill/template and OS layout/reviewer/playbook references. The brief explicitly prohibits Git mutation, so the existing branch was retained. No index/branch/stash/commit/push changes. All authoring stayed inside `slides_course/`; no hardware/runtime, camera, ORB execution, SSH, network, firmware/calibration, upstream or experiment-file changes.

Saved the required `qa/main-v4-91p.tex` **before editing**; its SHA-256 matches the audit's source hash `f96ac47afb5362c51b5219d6a6b4a329b854657f8182bbada669722fab454089`. Saved the matching PDF, incoming README, and all 91 incoming previews. Historical audits, calculations, assets and experiment evidence remain unchanged.

### Content and disposition

Applied all 91 frame dispositions: **33 KEEP ideas + five M1–M5 explanations = 38 main pages**; references on page **39**, followed by **39 backups**. Seven CUT frames removed from the presentation and preserved in the version backup. Eleven BACKUP command/detail frames consolidated into related question-page notes; all remaining BACKUP material follows references in the appendix. `qa/PHASE8_DISPOSITION.md` accounts for every audit ID. `qa/PHASE8_PAGE_LIST.md` and `qa/phase8-page-map.json` give final destinations.

Updated current platform to the measured 8 GB boot / 7.8 GiB RAM with the same 32 GB card; the 4 GB platform is historical N4A context. Power is unresolved, and final Wi-Fi reachability/operating state is unverified. Replaced built-never-run camera wording with observed recordings and first-frame offline crash. Explained three initial native compatibility patches versus patch 4's pointer initialization and incomplete power-interrupted rebuild. Added microSD gaps and inferred write blocking, unsuitable 64 GB USB throughput, clean short RAM recording and checksum-copy limits. Current direct SDK path is distinct from planned ROS/N3 integration. New-camera identity fields and the unavailable-IMU-calibration warning remain in notes.

Added feature correspondences, the IMU interval/visual-correction model, projector-off rationale, RAM capture/copy separation, and distinct EuRoC/D435i code paths (M1–M5). Revised pose/mount meaning, calibration register, conceptual aligned-path residuals with measured ATE, initialization hand motion, and dataset-versus-camera evidence (M6–M10). Roadmap states resume patch-4 rebuild → 100-second RAM take → offline replay/plot → live diagnostic, while formal gates remain OPEN.

The audit explicitly excludes later RPE verification and the paper comparator from its main result. Main retains only rigid-alignment MH01 ATE 0.0415 / 0.0368 / 0.0416 m, mean 0.040 m, with no scale fitting. Appendix labels the earlier RPE calculation **unverified in permitted sources**; no numeric RPE/Sim(3)/paper comparison is asserted in main. Earlier Phase-6/7 verification/calculation evidence remains archived unchanged. D435i accuracy remains UNKNOWN. No new paper/evaluator validation was attempted.

Removed visible internal source footers and evidence-path columns; original tables and paths remain in `\note{}`. All **13 gate/ancillary threshold-and-clock tables** preserve their first two cells byte-for-byte, including all 11 gate acceptance tables. USB ≥5000M, exact N2 profile/timing bands, staged durations and mandatory 300-second soak remain intact. The paired 30 Hz development profile and 15-second RAM diagnostic cannot qualify N2. No gate status promoted.

### Build and visual review

1. Initial disposition assertion caught omitted BACKUP ID 25 before writing main.tex; added it to the clock group. Round-1 XeLaTeX build was clean and rendered 78 pages. Inspected every page individually at full 1280 × 719 resolution. Found overlapping boundary/keyframe/health labels, a diagonal clock connector crossing text, rotated queue labels, two malformed quote strings, and diagrams implying a sequence between unrelated calibration/evidence types. Also replaced generic temporal-only feature matches with stereo + temporal matches.
2. Fixed those diagrams without reducing body fonts. Moved pose teaching to a full-width layout; expanded USB/SDK. Flattened consolidated notes and made the page denominator consistent across the references/appendix boundary. A relative-path authoring command failed before its intended edit, then was corrected; no failed command is treated as successful. Round-3 build/render/check was clean.
3. Added the conceptual ATE residual panel beside the measured plot. Rebuilt and inspected **all 78 pages again individually at full size**, covering the full main story, reference page and every backup. Last polish corrected apostrophe spacing, defined SLAM before use, defined ground truth, and clarified first-use backup terms. Rebuilt/rendered once more. Individually inspected the **nine changed pages** 6/10/15/28/40/44/70/71/72. The other **69 final PNGs are byte-identical** to their individually reviewed pre-polish images. `qa/phase8-page-review.tsv` records every final page hash/verdict. No unresolved overlap, clipping, broken figure or build defect remains.

Final: **78** pages; **53** uniquely captioned, referenced figures, numbered consecutively 1–53. 51 TikZ/mathematical visuals and two retained illustrations (P01 cover, P10 appendix); all P01–P12 originals/assets/mapping defects preserved. No new image generation; no placeholders. Timing/resource panels remain intentionally empty where data is missing. Known image defects remain conceptual-illustration limits; rendered QA does not verify hardware, physical safety or projector-room readability.

### Reproduction and verification

```sh
cd slides_course
python3 build_deck.py
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
swift -module-cache-path qa/swift-cache qa/phase6-extract.swift main.pdf > qa/phase8-pdf-text.txt
PYTHONDONTWRITEBYTECODE=1 python3 qa/check_phase8.py
rg -n '^!|Overfull|Underfull|Missing character|undefined' main.log
```

XeLaTeX/latexmk exit **0**; diagnostic grep **empty** (exit 1 for no matches). Renderer and independent PDF text extraction report 78 pages; every footer uses 78. Offline validator passes audit coverage, immutable incoming hash, threshold/clock preservation, original evidence tables in notes, no visible source paths, all figure labels/numbers/references, restricted main metrics, and exact deterministic generator reproduction. These checks qualify the document only.

Persistent authoring is `phase8_audit.py`; `build_deck.py` dispatches directly to it from the immutable incoming source and leaves earlier QA inventories intact. Updated README gives reproduction, current limits and preserved image workflow. Final evidence: build/render/check logs, PDF text, page-review TSV, source register, disposition/page list/map and artifact hash manifest.

The optional progress-deck reference edit was declined to keep all writes within C. B's old numeric references continue to target the archived 91-page source/PDF; use the new map/list for current C. No other folder touched. No hardware gate PASS is implied by this review.

PHASE 8 FINAL
