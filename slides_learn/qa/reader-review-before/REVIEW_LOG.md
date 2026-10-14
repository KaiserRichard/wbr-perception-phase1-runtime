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
