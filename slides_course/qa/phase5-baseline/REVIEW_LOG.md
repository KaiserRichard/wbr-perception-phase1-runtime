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
