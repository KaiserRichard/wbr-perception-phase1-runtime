# Build and reader review log

Date: 14 October 2026. Scope: teaching deck D, entirely within `slides_learn/`.

The directory initially contained BRIEF.md, REVIEW_BRIEF.md, run.sh and launcher logs, but no main.tex, PDF or page images. These existing files were preserved. Before authoring, inspected Git status, current branch, recent history and the source decks. The existing branch remained `claude/project-thread-rhsrup`; no index, branch, commit or push operation was performed, as required by the brief. No file outside this directory was edited.

## Content and provenance

Created 45 pages with the course deck's copied theme, canvas, fonts and palette. The lighter design uses short explanations, large TikZ diagrams, one table-corner example, nine part recaps and a final appendix. Each frame has a source note. Project facts come from the named source decks, the 13 October session summary, saved trajectory summary and calibration documentation. Primary method references are on page 45. P03/P04/P08/P10 were copied unchanged; no new image was generated and no prohibited robot illustration was used.

The three-run ATE and RPE numbers were checked against the saved trajectory summary. The roughly 184-second input duration and roughly 81-metre evaluated reference span are distinguished. The paper MH01 comparator follows the progress deck's verified Table II attribution; the mean-versus-median and protocol limitations remain visible. RPE is explained over one-second segments, not as a universal centimetres-per-second error rate. Stereo depth, clock readings and residual calculations are explicitly illustrative. ROS recording and direct SDK recording are explained as separate paths.

## Build and review loop

1. Created the initial source. Fixed a LaTeX helper-name collision with the built-in picture command before obtaining the first complete PDF.
2. Built with `latexmk -xelatex -interaction=nonstopmode main.tex`. Rendered with the brief's Swift renderer and `qa/swift-cache`, producing 45 images at 1280 × 719.
3. Read all 45 first-draft page images in order. Wrote READER_REVIEW.md with exact unclear wording, required explanations and the five priority fixes. The first successful draft had two overfull vertical boxes, on the bag and RPE pages. Manual image review also found arrow labels overlapping boxes; those were not detected by TeX.
4. Applied the clarity and layout fixes to main.tex through the source-construction helper. Rebuilt and re-rendered. Read every one of the 45 second-draft images in order, including unchanged pages.
5. Made two final wording refinements on pages 23 and 30, rebuilt and re-rendered all pages, then opened those two changed images again. Their layout and explanations are clear. No other pages changed in this final wording pass.

## Final page-by-page reader and layout check

| Page | What the student can explain after reading | Final check |
|---|---|---|
| 1 | Why this wheel-biped needs perception. | Clear; conceptual image has whitespace. |
| 2 | The journey of the table-corner measurement. | Clear; four readable stages. |
| 3 | Pose, trajectory and depth. | Clear; definitions precede later use. |
| 4 | Pi versus STM32H7 responsibilities. | Connection label no longer overlaps boxes. |
| 5 | Why control survives delayed perception. | Three readable recap prompts. |
| 6 | Stereo cameras and the IMU. | Smaller image leaves room for explanation. |
| 7 | Disparity and a one-metre depth calculation. | Rectification and focal scale explained. |
| 8 | Gyro, acceleration, noise and bias. | Noise drawing identifies its unbiased reference. |
| 9 | Why the projector is off. | Features defined at their first use. |
| 10 | Each sensor's role and limitations. | Recap is readable. |
| 11 | Frames and transforms on a wheel-biped. | All three schematic frames show two axes. |
| 12 | Measurement timestamp versus arrival. | Timeline and delay arrow are clear. |
| 13 | Why clock readings need a relationship. | All labels fit; example clocks are illustrative. |
| 14 | Where and when samples belong. | Avoids using latency before its definition. |
| 15 | Features and matching. | Corner correspondence is visually clear. |
| 16 | Pose prediction and measurement correction. | No premature map-point terminology. |
| 17 | Keyframes, map points, SLAM and odometry. | Keyframe definition includes both image and pose. |
| 18 | Preintegration and initialization. | Stereo metric meaning is stated in plain words. |
| 19 | The three ORB-SLAM3 threads and loop closure. | Software named; diagram words do not split awkwardly. |
| 20 | Why tracking fails. | Calibration defined before the failure list. |
| 21 | How images and IMU jointly support a pose. | Three readable recap prompts. |
| 22 | Intrinsics and extrinsics. | Raised relation labels no longer overlap boxes. |
| 23 | Time offset, uncertainty and later calibration tools. | Final wording and changed image rechecked. |
| 24 | Why calibration precedes trust. | Recap distinguishes motion and target recordings. |
| 25 | USB delivery and librealsense. | SDK defined before later use. |
| 26 | ROS 2 nodes, topics and message metadata. | Diagram and explanation are readable. |
| 27 | Bags, offline/live processing and two recording routes. | Image/caption reduced; takeaway clears the footer. |
| 28 | The software journey and route distinction. | SDK already defined. |
| 29 | Independent ground truth and EuRoC. | Comparison label raised; handoff wording removed. |
| 30 | Fair rigid alignment without stretching. | Color legend and final wording rechecked. |
| 31 | ATE, residual and RMSE. | Illustrative 3–4–5 calculation readable. |
| 32 | RPE for a one-second motion segment. | Diagram not to scale; no footer collision. |
| 33 | What the three saved EuRoC runs establish. | Numbers, units, comparison and limitations readable. |
| 34 | What an accuracy score proves. | Recap distinguishes dataset and camera evidence. |
| 35 | Why N0 through N3 precede estimation. | Link speed explained; five-minute continuous test explicit. |
| 36 | The distinct N4A, N4B and N4C questions. | Baseline versus stereo extension stays distinct. |
| 37 | N5 timing, N6 health and N7 safe integration. | Latency and sample age explained. |
| 38 | Bottom-up debugging. | Short diagram and examples readable. |
| 39 | The complete gate ordering. | Recap is readable. |
| 40 | The dated current state and next steps. | Only overall status page; no gate acceptance implied. |
| 41 | How to choose and brief the next task. | Recap uses the running measurement example. |
| 42 | The main terms at a glance. | Two columns fit without tiny text. |
| 43 | Which tool answers which question. | One-line descriptions and table fit. |
| 44 | Deck reproduction and a saved-data scoring shape. | Correct shell continuation characters; appendix only. |
| 45 | Project provenance and primary method references. | Links and bibliography are readable. |

## Reproduction and check results

Run from the repository root:

```sh
cd slides_learn
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
python3 qa/check_source.py
```

Final build: exit 0, 45-page PDF; no LaTeX errors, warnings, overfull or underfull boxes in `qa/build-final.log`. Final render: exit 0 and page count 45 in `qa/render-final.log`. All page PNGs exist at 1280 × 719. Source checks confirm 45 frames, 45 source notes, nine recaps, no prohibited content-page tokens or images, and byte-identical reused assets. The final Git status matches the initial outside-folder state and the branch is unchanged.

Manual review confirms no remaining clipping, overlapping labels, footer collisions or tiny teaching text. The appendix uses the course's small font for commands and references; content explanations retain the normal 12-point class typography. No automatic overlap detection claim is made.

## Limits

This is an author reader self-review, not an independent comprehension study. The deck documents saved evidence; no new dataset score, camera command, ORB-SLAM3 execution, Pi action or sensor validation was performed. The strict raw profile, timing acceptance thresholds, mandatory 300-second N2 run, separate storage requirement and STM32H7 safety ownership were not changed. Historical evidence and the existing launcher logs remain unchanged. The renderer requires the Mac path and fonts named in the reproduction instructions.

READER REVIEW FINAL

FINAL

## Subsequent reader review requested by REVIEW_BRIEF.md

Date: 14 October 2026. Read every existing preview image, pages 1–45 in order, as a fourth-year electronics student new to SLAM. This was an assistant-simulated reader review, not an independent human comprehension study. Preserved the input source, PDF, images, prior review records, README and manifest in qa/reader-review-before/ before editing. The earlier entries above describe the original authoring pass.

Wrote READER_REVIEW.md with exact input wording, page numbers, explanations needed, agent-handoff language and five prioritized fixes. Applied those fixes to main.tex without changing the structure, theme or fonts. Changed pages: 8, 11, 13, 15, 17, 18, 19, 22, 23, 26, 27, 28, 33, 36, 37, 39, 40, 41, 42 and 44. Revisions explain IMU behavior and drift, add illustrative frame/clock arithmetic, describe feature signatures, clarify publishing/subscribing and both recording routes, explain the principal point and map restart, and simplify results and planning language. The median explanation includes both middle values for ten ordered results.

Measured EuRoC scores and historical experiment evidence were not changed. All 45 original source notes are unchanged. New frame and clock example numbers are explicitly illustrative; their arithmetic was checked. The accelerometer comparison teaches textbook behavior, not a new hardware measurement. The USB >=5000M requirement, mandatory 300-second N2 run, exact one-stream baseline in the notes, calibration warning provenance, storage requirements and STM32H7 safety ownership remain intact. A ROS-to-SLAM input program is explained as necessary without claiming it has been built or validated.

Built and rendered the revision, then opened and read all 20 changed page images. The explanations fit at the normal teaching font size; no clipping, label collision or footer overlap was visible. Made final clarity refinements on pages 22 and 33, rebuilt and rendered, and opened their final images again. Both are clear and fit. Byte comparisons confirm that exactly the 20 revised page images differ from the archived input; the other 25 pages are identical.

Reproduction commands, run from slides_learn:
- latexmk -xelatex -interaction=nonstopmode main.tex
- swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
- python3 qa/check_source.py

Final build and render returned exit 0: 45 PDF pages and 45 PNGs. No TeX warnings or overfull/underfull boxes appear in final main.log. Source checks passed: 45 frames, 45 source notes, nine recaps, no forbidden teaching-page tokens/images, and reused assets remain byte-identical to course assets. New logs are qa/reader-review-build-final.log, qa/reader-review-render-final.log, qa/reader-review-source-check-final.log and qa/reader-review-verification.log. The artifact manifest records final hashes; its prior version is archived.

Manual validation: read the changed images and explain the examples aloud; compare the result table with the archived input and saved trajectory summary. Image comparison checks change scope, not human comprehension or automatic overlap detection. README documents that the original source generator would restore the older deck; normal builds use main.tex. The targeted revision helper reconstructs this version from the archived source.

All writes stayed inside slides_learn/. No branch, index, commit or push operation was performed, following the brief's specific builder rule. No camera, Pi, ORB-SLAM3, sensor capture, firmware or calibration command ran. This work validates teaching artifacts only.

READER REVIEW FINAL


## Revision 2: 2026-10-14 facts and small fixes

Scope: only the final Revision 2 section of BRIEF.md. Read the full brief, the
14 October session facts addendum, relevant deck frames and prior review records.
Inspected Git status, branch and recent history before edits. Followed the brief's
specific builder rule: no index, branch, commit or push changes, and all writes
inside slides_learn/. Preserved the input source, PDF, 45 previews, README, review
log, page manifest and artifact manifest in qa/revision2-before/. Their hashes
are recorded in qa/revision2-before-hashes.json and verified unchanged.

Changed teaching pages:

| Page | Revision and reader/layout check |
|---|---|
| 8 | Moved “Unbiased reference” below the dashed reference line. It clears the noise curve and time axis. |
| 25 | Kept USB and librealsense definitions; explained a recording buffer using a UART receive queue. The small TikZ picture shows arrivals, slow writing, a filling buffer and dropped frames. Explained the card's 16.6 MB/s against 18.4 MB/s needed, the likely writer bottleneck, RAM-first recording, verified copying and RAM's loss on power failure. The 15-second test is distinguished from the still-pending longer RAM take. All text and diagram labels fit. |
| 38 | Explained the first-frame offline crash as an uninitialized address in embedded C, then the null initialization fix. The EuRoC example did not call this path. The interrupted rebuild and required successful rerun remain explicit. No successful fix validation is implied. Text and diagram fit. |
| 40 | Updated the single overall status page to 14 October: 8 GB Pi with the same OS card, short stereo/IMU streaming, slow card and USB stick, short successful RAM capture, pending rebuild and unresolved under-voltage. Next steps distinguish diagnostic RAM/offline/live work from calibration, storage qualification and gate acceptance. The CAMERA AVAILABLE rule remains visible. No footer collision. |
| 45 | Added the 14 October addendum to project references and the source note. References remain readable. |

Detailed provenance and qualifications are in speaker notes on pages 25, 38 and
40. The card bottleneck remains a strong inference rather than a manufactured
measurement. Notes retain the shutdown gap, RAM test duration/rates, successful
checksum copy, untested longer RAM recording, pending patched rerun and unknown
8 GB Pi Wi-Fi access. The short results do not establish sustained reliability
or any gate PASS. The three historical EuRoC scores, calibration warnings and
N0–N7 gate pages are unchanged, including USB >=5000M, the exact N2 raw profile
and mandatory 300-second soak. STM32H7 safety ownership is unchanged.

Built and rendered once, then opened and read all five changed page images at
1280 x 719 as the target student. Refined the slow-writing label and clarified
that the crash attempted access through the garbage address. Rebuilt and
re-rendered, then opened the final pages 25 and 38 again. Page 8's reference
label, page 40's status and page 45's references are unchanged from the inspected
first render. All changed pages can be explained after one reading; no visible
clipping, overlap, tiny teaching text or footer collision remains. This is an
author-simulated reader check, not an independent student comprehension test.

Reproduction commands, run from the repository root:

```sh
cd slides_learn
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
python3 qa/check_source.py
```

Final build and render exited 0, producing 45 PDF pages and 45 PNGs. No TeX
warnings, errors, overfull or underfull boxes appear in final main.log. Source
checks pass: 45 frames, 45 source notes, nine recaps, no forbidden teaching-page
tokens/images, and reused assets byte-identical to the course images. Byte
comparison confirms only pages 8, 25, 38, 40 and 45 changed; the other 40 images
and source frames are identical to the archived input. Git branch/status match
the initial snapshot. Verification does not claim automatic overlap detection.

Logs: qa/revision2-build-final.log, qa/revision2-render-final.log,
qa/revision2-source-check-final.log and qa/revision2-verification.log. Updated
qa/page_manifest.txt and qa/artifact-manifest.json for the final artifacts.
README warns that both historical source helpers would overwrite Revision 2;
normal reproduction uses main.tex directly. Manual validation: inspect the five
changed previews, explain buffer overflow and the pointer fix aloud, and compare
the dated statements with experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md.

No camera command, Pi access, sensor capture, ORB-SLAM3 runtime, firmware or
calibration change occurred. No image was generated. Historical evidence and
prior review entries were preserved. This revision validates teaching artifacts
only and does not fix power, qualify storage or verify the pending runtime patch.

REVISION 2 FINAL

## Revision 3: What to learn before each gate

Scope: only the owner-requested Revision 3 section of BRIEF.md. Read the builder
rules, existing deck, prior reviews and relevant project gate descriptions.
Inspected Git status, current branch and recent history before edits. Followed
the brief's specific rule: all writes inside slides_learn/, and no Git command
that changes branches, index or commits. Preserved 52 input files (source, PDF,
45 previews, README, review log, source checker and manifests) in
qa/revision3-before/; qa/revision3-before-hashes.json verifies those copies.

Added two pages immediately before the appendix, both titled “What to learn
before each gate.” Eight rows with four columns cannot remain readable on one
page at the deck's type size: four rows per page allow short, legible phrases.
Page 42 covers N0–N3; page 43 covers N4–N7. Each gate has its existing plain-word
question, prerequisite concepts, one primary reading and one self-check. New
terms throttling, QoS, tf2 and Allan analysis are explained in the table. N4
summarizes its known-data, camera-replay and live stages without making camera
qualification a prerequisite of the independent EuRoC experiment. N5 remains
about timing/resources; N6 about detecting unusable poses; N7 about safe use.
Expected self-check answers and source qualifications are in speaker notes.

Updated the existing references page, now page 47, into two readable columns.
It keeps project evidence and illustration provenance and adds Raspberry Pi,
librealsense, ROS 2 tutorials/tracing, Kalibr/Furgale, Forster, Sturm, Zhang and
Scaramuzza, evo, Barfoot and ST watchdog readings alongside Campos and Burri.
PDF inspection confirms 15 distinct clickable reference URLs. Primary reading
provenance is in qa/revision3-reading-sources.md. ROS documentation browsing was
blocked by Anubis, so its contents were checked against official documentation
source and a ROS documentation mirror. Normal documentation links remain in
the deck. Barfoot's author copy is an updated draft of the second edition.

Reader/layout review: opened and read final pages 42, 43 and 47 at 1280 x 719.
The four table columns remain distinct; gate questions and self-checks can be
explained aloud after one reading. No paths, commands or status labels appear
on the new teaching pages. Both tables and the references clear the footer.
References retain readable type and descriptive links. Initial iterations
exposed vertical overflow and a Beamer grouping issue that hid reference text;
removed extra takeaway lines and corrected grouping before final inspection.
An early render started before PDF conversion completed and failed; the final
build and render ran sequentially and succeeded. No failure is treated as PASS.
This is an author-simulated reader test, not an independent student study.

Reproduction commands, from the repository root:

```sh
cd slides_learn
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
python3 qa/check_source.py
python3 qa/verify_revision3.py
swift -module-cache-path qa/swift-cache qa/inspect_revision3.swift
```

Final build, render, source checks, artifact comparison and PDF inspection exited
0: 47 PDF pages, 47 PNGs, 47 source notes and nine original recaps. No TeX warnings,
errors, overfull or underfull boxes appear in final main.log. All 44 retained
source frames are identical to Revision 2. Their rendered content pixels are
identical when excluding only the page-number rectangle (1100,680)–(1280,719).
New pages are 42–43; the former references page 45 is updated as page 47. The
original 45 previews and other archived input files remain hash-identical.
Reused images remain byte-identical to course assets. Pixel comparison checks
scope, not comprehension or automatic overlap detection.

Logs: qa/revision3-build-final.log, qa/revision3-render-final.log,
qa/revision3-source-check-final.log, qa/revision3-verification.log and
qa/revision3-pdf-inspection.log. Updated page/artifact manifests and README.
qa/apply_revision3.py reconstructs this revision from the archived Revision 2
source; ordinary reproduction builds main.tex directly. Historical helpers
would restore earlier decks. Manual validation: read pages 42–43 aloud, answer
each self-check and follow the corresponding reference links on page 47.

The Git branch remained unchanged. A concurrent new untracked slides_roadmap/
directory appeared during this session; this revision did not create or edit
it. Other initial status entries remain present. No camera command, Pi access,
ORB-SLAM3 runtime, capture, firmware or calibration change occurred. No image
was generated. Gate thresholds, exact raw profile, mandatory 300-second soak,
safety ownership, prior content and historical evidence remain unchanged.
Allan reading does not replace N2 delivery checks; callback timing is not complete
pose latency; transform theory and watchdog documentation are not a project
health protocol or safety approval. This work validates teaching artifacts only.

REVISION 3 FINAL


## Revision 4 — infrared projector explanation

Scope: owner-requested Revision 4 only. Read the builder rules, repository
instructions, Git status/branch/recent history, existing deck and review records
before edits. All writes stayed inside slides_learn/. No Git mutation, commit,
push, Pi access, camera process, sensor capture, firmware/calibration change or
ORB-SLAM3 runtime occurred. The brief explicitly forbids branch changes, so the
existing branch was retained. Initial and final Git status entries are identical.
Input source, PDF, all 47 previews, README, review log, source checker and manifests
are archived in qa/revision4-before/ with a checked SHA-256 manifest; previous
revision archives and historical evidence were not changed.

Added exactly two frames immediately after the original page 9, which is unchanged:

- Page 10 explains the two IR cameras and projector, that only the cameras capture
  images, and that invisible projected dots add texture to a plain wall. A TikZ
  OFF/ON illustration leads into disparity and Z = f b / d, with all units defined.
  The approximately 5 cm baseline is the saved nominal unit configuration's
  0.0499 m, not newly measured or validated calibration.
- Page 11 uses side-by-side TikZ diagrams with earlier and later camera positions,
  movement arrows, world positions and separate image observations. The real
  corner stays fixed while its pixel shifts left. The attached projector's spot
  slides right across the table; its pixel remains fixed in this illustrative
  translation over a flat surface without rotation. This constant-pixel outcome
  is not asserted for arbitrary surfaces or rotations. The three-row summary
  distinguishes depth use, temporal ORB-SLAM3 tracking and our initial OFF tests.
  OFF is explicitly experimental, with a later tracking/depth ON/OFF comparison
  proposed, not performed. The requested question closes the slide; its answer
  is that the corner stays fixed in the room and moves only in the image.

Updated the page 2 reading map and added the RealSense projector primary-source
link to the existing references page, now page 49. Gate learning tables shift to
44–45 and appendix to 46–49. Existing source notes have no obsolete shifted numeric
page references; the new note's page 7 geometry reference still points to page 7.
No earlier revision content was redone. Existing checks and page/artifact manifests
were updated for 49 pages; revision4-specific checks are reproducible below.

Provenance: owner brief; October 13 session facts section F for nominal baseline;
existing course/progress explanation and Campos et al. (2021) for static scene
feature geometry. Verified active-stereo background against RealSense,
[Projectors for D400 Series Depth Cameras](https://dev.realsenseai.com/docs/projectors/),
sections 1 and 3, accessed 14 October 2026. That primary source explains texture
for simultaneous left/right correspondence and does not claim our experimental
OFF choice is universally required. The across-time failure mechanism is the
geometric inference shown in the diagram, not a newly measured failure.
Detailed assumptions and source locations are in speaker notes. No image was
generated; illustrations use TikZ and existing assets are unchanged.

Reader/layout review: opened and read pages 2, 8–12 and 49 at the rendered
1280 x 719 size; re-opened page 11 after fixing its label collisions. Page 10
moves from illumination to matching to depth, so a reader can distinguish a
projector from an imager. Page 11 separates world and image positions and makes
the within-pair/across-time distinction explainable aloud. Natural-feature and
feature concepts follow the existing page 9 definition. Titles, diagram labels,
three summary rows, experimental qualification and check question remain readable
and clear of the footer. Initial page 11 vertical overflow and label overlap were
fixed by shortening prose, adjusting diagram positions and removing an unnecessary
table header; body fonts and deck theme were retained. A small references overflow
was fixed with spacing. An initial edit attempt used the wrong relative working
directory and failed before changing source; its subsequent build was a no-op.
Final build/render were sequential and succeeded. No initial failure is reported
as PASS. This is an author-simulated reader review, not an independent student test.

Reproduction commands, from the repository root:

```sh
cd slides_learn
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
python3 qa/check_source.py
python3 qa/verify_revision4.py
swift -module-cache-path qa/swift-cache qa/inspect_revision4.swift
```

Final verification: 49 PDF pages, 49 previews, 49 source notes, nine recaps and
16 distinct clickable reference URLs, including the new projector link. No TeX
warnings, errors, overfull or underfull boxes. All 45 prior source frames outside
the reading map and references are identical to input; their rendered content
pixels are identical when excluding only the footer rectangle
(1100,680)–(1280,719). Archived input files remain hash-identical. Reused assets
remain byte-identical to course assets. Pixel comparison establishes revision
scope, not comprehension or automatic overlap detection. No runtime/gate claim
is established by this teaching-artifact validation.

Logs: qa/revision4-build-final.log, qa/revision4-render-final.log,
qa/revision4-source-check-final.log, qa/revision4-verification.log and
qa/revision4-pdf-inspection.log. Scope mapping is in
qa/revision4-changed-pages.json; qa/revision4-slides.tex records the final inserted
frames as a reference snippet (main.tex remains the build input).

The inherited manifest included unavailable historical source paths. Their old
hashes are retained separately as historical_sha256_unavailable_paths; current
available artifact hashes were verified. No missing source file was recreated.

REVISION 4 FINAL


## Revision 5 — page 11 corner versus dot diagram

Scope: only Revision 5 of BRIEF.md. All edits are inside slides_learn/;
Git index, branch and commits were not changed under the builder rules.
Before editing, inspected Git status, current branch, recent history, the brief,
page 11 source and its existing preview. Preserved input source, PDF, review log,
artifact manifest and all 49 previews in qa/revision5-before/ with SHA-256 hashes
in qa/revision5-before-hashes.json. Earlier revision evidence is unchanged.

Gave the diagram more vertical room by increasing its vertical coordinate scale
from 0.75 cm to 0.85 cm. Placed both “Moves right” labels explicitly above the
motion arrows, clear of camera boxes and viewing rays. Moved “Same world point”
above the table line, away from the dashed ray; shortened the adjacent table label
to “Table in the room” to keep the labels separate. Moved both colored image
captions farther below their image labels. Put the three-row summary and the
experimental-choice note beside each other below the diagram. Shortened the
summary's “ORB-SLAM3 feature tracking across time” to “ORB-SLAM3 tracking across
time”; the introduction still identifies fixed room features. The teaching
content, geometric assumptions, OFF qualification, later ON/OFF comparison and
verbatim check question are preserved. Theme, fonts, all source notes, page count,
reading map and references are unchanged; no new page was needed.

Reproduction commands from the repository root:

```sh
cd slides_learn
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache   ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift   main.pdf preview
python3 qa/check_source.py
python3 qa/verify_revision5.py
swift -module-cache-path qa/swift-cache qa/inspect_revision4.swift
```

Final build, render, source checks, scope verification and PDF inspection exited 0.
The PDF has 49 pages and 16 distinct reference links; all 49 previews exist at
1280 x 719. Final main.log contains no errors, warnings, overfull or underfull
boxes. Only frame 11 differs from archived source; only page 11 differs among
rendered PNGs (all other pages are byte-identical). Archived inputs remain
hash-identical, all 49 source notes are unchanged, reused image assets remain
byte-identical and Git status/current branch match the initial snapshot.

Manual reader/layout review: opened pages 10, 11 and 12 at full rendered size.
Page 10 still teaches within-pair matching and depth; page 11 clearly separates
fixed-world corners from sliding lit spots, world positions from image positions,
and explanatory captions from boxes. Both motion labels have clear space above
their arrows. The summary, qualification and check question remain readable,
with space above the footer. Page 12 still provides the sensor recap. This is an
author-simulated reader review, not an independent student comprehension test.
Pixel comparison verifies revision scope, not automatic overlap detection.
The diagrams remain illustrative; no hardware, capture or runtime validation ran.

Initial layout passes produced vertical overflow and were corrected before final
validation. One render was started while an intermediate build was still running
and failed; rerendered successfully after build completion. The first scope
checker counted a preamble frame macro; corrected it to inspect document frames.
Those failed attempts are not reported as successful checks.

Final logs: qa/revision5-build-final.log, qa/revision5-render-final.log,
qa/revision5-source-check-final.log, qa/revision5-verification.log and
qa/revision5-pdf-inspection.log. Provenance: owner Revision 5 request and the
existing Revision 4 teaching example and speaker notes; no new factual claims.

REVISION 5 FINAL
