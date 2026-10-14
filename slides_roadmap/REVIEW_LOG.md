# Roadmap synthesis and deck review

Date: 14 October 2026. Scope: the SYNTH_BRIEF deliverables, documentation only. Final deliverables are `ROADMAP.md`, `main.tex`, its copied `preamble.tex`, and the **22-page** `main.pdf`. This log records the content decisions, build and manual page inspection; it does not accept any robot/runtime gate.

## Inputs, provenance and boundaries

- Read SYNTH_BRIEF, COMMON, repository instructions, R1/R2/R3, dated 13–14 October facts, lab and Phase A runbooks, required architecture/state/decision/calibration/bring-up documents, existing brief preamble/deck and relevant course gate/boundary material.
- R1b was absent initially. A one-minute polling process started at 07:31:46 UTC and found it at 07:36:46 UTC, after 300 seconds. Read the completed independent report before final selection; `qa/r1b_poll.log` retains all six observations, including the initial check. No missing-review assumption was needed.
- Primary upstream pages were rechecked for ORB capabilities/licence, OpenVINS Jazzy PR status, the existing wrapper's monocular limitation, Kalibr requirements/time/transform/noise conventions, Raspberry Pi power guidance, frame/Nav2 requirements, RTAB-Map roles and robot_localization licence. URLs are in ROADMAP and speaker notes/references. Mutable pages must be pinned before runtime implementation.
- Starting Git inspection: branch `claude/project-thread-rhsrup`, HEAD `cf09251`, substantial existing dirty/untracked work. COMMON's task-specific prohibition on Git mutation was followed; no branch change, commit or push. Only the roadmap folder was authored. Existing research reports and historical evidence were preserved.
- No SSH, installation, camera command, ORB execution, sensor capture, firmware/network mutation, purchase, booking or message to lab personnel occurred. No image generator was used; all slide diagrams are TikZ. The copied preamble retains the existing visual style byte for byte; its unused image helpers do not introduce raster assets into this deck.

## Content review and fixes

1. **Estimator bias:** incorporated both reports rather than treating the existing build as proof of superiority. The independent review's ORB/RTAB tie at 68, uncertain Pi performance, objective sensitivity and ready-wheel-interface switch are visible. ORB remains the next localization candidate; RTAB own odometry remains a mapping-first alternative, OpenVINS a matched-data VIO challenger, wheel/body/depth a smaller demo if lab exports already work. No candidate is declared hardware-qualified.
2. **Wrapper timing:** resolved R1's early thin ROS node versus R3's deferral. Native estimator plus a reviewed modular live-health adapter comes first, N3 ROS qualification remains mandatory, and a ROS estimator adapter follows an actual consumer. No file-scraping health implementation or silent camera-owner duplication is proposed.
3. **Safety numbers:** retained R2's concrete values only as candidate bench scenarios. Controller-approved source-age, lease, silence, loop, stop and motion limits remain prerequisites to physical acceptance. A fresh heartbeat cannot refresh a frozen estimate; invalid/reset sessions revoke optional input and require explicit re-enable.
4. **Storage:** preserved the owner's calibration-card exception while exposing the existing external-storage receipt mismatch. No forged receipt or threshold weakening. Prefer qualified external storage for N3/routine datasets if the exception route blocks. Correct payload/capacity and longest-take qualification remain explicit.
5. **Identity and calibration:** four serial fields remain separate; firmware-update identity stays independently unverified rather than adopting tooling expectation as observation. Kept existing three 120 s calibration takes, heldouts and measured target dimensions; identified A0 printing and the future hours-long recorder dependency. Preserved calibration warnings, default/noise/offset limitations and the distinction between camera and body IMUs.
6. **Licence conflict:** upstream ROS 2 robot_localization manifest states Apache-2.0; corrected R1's BSD label in the synthesis without editing historical research. Distribution scope/dependency inventory remains a later owner decision.
7. **Duration realism:** distinguished total effort from critical-path overlap and overnight/lab queues. Main ranges total 8.5–24 days; P5 adds 2–4, approximately 11–28 total engineer-days. The 4–6-week mounted advisory target is conditional and can slip. Navigation is a separate 2–4+ week low-confidence scope. No date or booking is represented as confirmed.
8. **Avoiding roundabout work:** reused the existing build and native acquisition, deferred Docker, Pi visualization, learned/GPU methods, jumps, unnecessary parallel ports and optional navigation. Kept all fixed N1→N2→N3 thresholds/stages and mandatory 300 s soak. Requalification after final mount/power/topology remains required.

## Build and document checks

Commands from `slides_roadmap/`:

```bash
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
swift -module-cache-path qa/swift-cache qa/extract_pdf_text.swift main.pdf qa/pdf-text.json
```

Build passes 1 and 2 succeeded; final build succeeded. `qa/build-final.log` records latexmk's up-to-date final targets and 22 pages. Final `main.log` has **no Overfull, Underfull, Warning or Error entries**. The initial Swift invocation compiled its module cache, then succeeded; `qa/render-final.log` reports 22. Rendered pages are `preview/page-01.png` through `page-22.png` at 1280 pixels wide.

Camera-free document assertions passed: 19 repository-relative ROADMAP links resolve; nine phase blocks and 22 sourced/noted frames exist; preamble matches the brief exactly; main.tex uses no image helpers/includegraphics; target/storage arithmetic agrees. `qa/document-checks.txt` labels this document-only validation.

PDFKit text extraction confirms 22 pages, every footer from 1/22 to 22/22, the explicit next-week date, and no visible file paths or evidence-status labels. URLs remain linked titles on the references slide; source paths/labels reside in notes. PDF text is preserved in `qa/pdf-text.json`. Runtime/manual verification commands are linked in ROADMAP rather than executed here.

## Manual page inspection

Every page was opened individually at its rendered resolution after build pass 2. Changed pages were reopened after the final build/render.

| Page | Inspection result / correction |
|---|---|
| 1 | Starting evidence and simple diagram readable; unknown camera/robot readiness clear. |
| 2 | Whole road and optional branch fit. Shortened parallel-health callout to remove awkward word splitting; final page rechecked. |
| 3 | Camera-free phase, tools, owner actions and authorization phrase readable. |
| 4 | Gate order, 5000M branch and mandatory soak visible; exact profile/limits retained in notes/document. |
| 5 | Target and overnight dependencies readable; future recorder explicitly required. |
| 6 | Simplified the title to improve its rendering/clarity; final title and all rows rechecked. |
| 7 | Live age/resource criteria and heartbeat warning fit; no throughput promise. |
| 8 | Synthetic receiver scope and interface review explicit; tooling success not physical safety. |
| 9 | Supported tests, controller attendance and stand limitations readable. |
| 10 | Supervised advisory scope, repeat/handoff and separate motion review visible. |
| 11 | Optional navigation dependencies and added duration fit; occupancy-map limitation explicit. |
| 12 | All six booking rows readable, no clipping; unconfirmed stock/arrival stated. |
| 13 | Five software groups fit; native-first choice and mandatory N3 both visible. |
| 14 | Two-way message boundary clear. Added separation below return-status line and explicit failure-text lines, removing awkward hyphenation; final page rechecked. |
| 15 | Independent tie, score uncertainty and selection/switch reasoning readable; no benchmark ranking implied. |
| 16 | Arrow labels initially overlapped boxes. Moved labels below diagram; final page rechecked, clean separation. |
| 17 | Six risk/next-action rows fit; input-layer diagnosis and accuracy limits readable. |
| 18 | Five defaults and required later decisions readable; no concrete interface acceptance claimed. |
| 19 | Current-week dates, owner/engineer actions and conditional bench entry clear. |
| 20 | Reworded date as “Week of 21 October 2026” for clear rendering; final page rechecked. Overnight/soak requirements retained. |
| 21 | Later conditional weeks and question/exit pairs readable; no guaranteed delivery. |
| 22 | Primary linked references and distinction between planning judgments and unmeasured performance readable. |

Final visual verdict: readable tables/text, clean diagram routing, no detected clipping or overlap, consistent existing palette/fonts, 22 slides, notes/references provenance present. PDF screenshots are review artifacts, not experimental evidence.

## Limitations and handoff

Hardware availability, parts delivery, camera calibration, Pi sustained performance, controller implementation/budgets and physical fallback remain unverified. The roadmap is a reviewable proposal; it does not approve architecture/public API/node graph/message/firmware changes or robot motion. Offline/synthetic checks establish tooling only. Exact N2 thresholds and its 300-second soak were preserved, not rerun. Deployment acceptance needs observed results and reviewed criteria.

Owner's next action: confirm the P0/B1 inventory and people, protect target/overnight camera access, and review the interface/acceptance proposals before implementation. The saved deck/document are ready for that discussion.

FINAL

## REVIEW FINAL — critical review and applied fixes (14 October 2026)

Scope: response to `REVIEW_BRIEF.md`. `REVIEW.md` records the five requested review categories and linked technical sources. `ROADMAP.md` and the 15-frame `main.tex` incorporate the accepted corrections. This is a documentation review; it does not accept a robot/runtime gate.

### Findings addressed

- Replaced the parallel P0–P8 taxonomy and duplicated estimator/schedule tables with the existing N0–N7 route, one default plus evidence-based alternatives, and one effort-versus-calendar summary.
- Exposed the first-session blockers and owner actions: unconfirmed stable Pi power/access, absent RealSense ROS wrapper, unqualified large-bag storage, unproved ROS 1 Kalibr import, missing target/overnight tooling, and unknown controller owner/hardware.
- Corrected the Kalibr dependency claim. The selected lossless PNG plus full-precision timestamped IMU CSV to ROS 1 bagcreater path is a proposal requiring synthetic and known-sample verification; RealSense `.db3` is rosbag2. See [Kalibr bag format](https://github.com/ethz-asl/kalibr/wiki/bag-format), [Kalibr ROS 2 conversion guidance](https://github.com/ethz-asl/kalibr/wiki/ROS2-Calibration-Using-Kalibr), and [RealSense recording documentation](https://github.com/realsenseai/librealsense/blob/master/doc/record-and-playback.md).
- Removed unsupported algorithm scores and calendar promises. Effort ranges are low-confidence; the displayed 11–28 engineer-day base excludes a separately stated 2–5-day tool/import contingency and unknown queues.
- Preserved N1→N2→N3 order, USB ≥5000M, exact IR1 Y8 640×480/15 + gyro/200 + accel/100 N2 profile, 20→105→mandatory 300-second stages, rate/gap thresholds, calibration warnings, separate serial fields and STM32H7 safety ownership. No camera work was authorized or performed.

### Build and document QA

From `slides_roadmap/`:

```bash
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
swift -module-cache-path qa/swift-cache qa/extract_pdf_text.swift main.pdf qa/review-final-pdf-text.json
```

All three final commands exited successfully. The LaTeX build produced 15 pages with no Overfull/Underfull, warning or error diagnostics (`qa/build-review-final.log`). The renderer refreshed `preview/page-01.png` through `page-15.png`; stale pages 16–22 from the former deck were removed. Text extraction confirms 15 pages (`qa/extract-review-final.log`, `qa/review-final-pdf-text.json`). These checks validate document generation only; no hardware or runtime tests were run.

### Visual inspection

Opened all 15 rendered pages individually. Rechecked pages 9, 13 and 14 after layout fixes. Removed the N6 arrow-label collision, rendered “low confidence” as TeX rather than literal Markdown, aligned the visible base-effort total with the separately stated contingency, and fixed slide 14's vertical overflow. Final inspection found the content readable with no detected clipping or overlap.

### Limitations and handoff

The ROS 1 converter, recorder, wrapper install, camera calibration, sustained Pi performance, controller interface and robot behavior remain unimplemented or unverified as marked in the roadmap. No gate PASS, architecture/API/message/firmware approval, purchase, booking or external communication is claimed. Camera-dependent work and ORB-SLAM3 remain blocked until the owner's explicit `CAMERA AVAILABLE` authorization. Historical review/build material above this section remains unchanged.

## REVISION 1 FINAL — owner-facing roadmap (14 October 2026)

Scope: `REVISION_BRIEF.md`, with `COMMON.md` read before edits. Final deck: **23 slides**. Updated `main.tex`, `ROADMAP.md`, PDF and previews; added revision-specific QA artifacts only under `slides_roadmap/`. The prior `qa/main-v1.pdf` is unchanged; the starting TeX/roadmap are preserved in `qa/revision1-original/`. Existing research and earlier review records remain unchanged. The copied preamble was not edited.

### Brief coverage

- Plain phase titles now precede gate codes, which appear as small secondary text. Eight phase pages use the exact **What / How / Tools / Hardware / Done when / Time** pattern. Completion rows point to recorded counts, matching copies, tracking/reset plots, receiver traces or reproducible operator procedures.
- Removed visible agent vocabulary: authorization token, booking codes, source-age, fixture, entry checks, held-out and advisory. Added a glossary and plain explanations for estimate age, percentiles, target, RGB-D and Nav2. Exact operational authorization and detailed technical provenance remain in notes and ROADMAP.
- Added the one-page TikZ road with week ranges and hardware beneath each phase; two hardware/lab tables with item, phase, status, booking timing and preparation; software stack by phase; two pages covering every week from 14 October through 24 November.
- Restored the scored algorithm comparison requested by the owner: ORB-SLAM3, RTAB-Map, OpenVINS, wheel/body/depth, ORB RGB-D, Basalt, VINS-Fusion and Kimera. Scores reproduce R1b's engineering judgments, checked against R1; they are explicitly not Pi benchmarks. Full six-criterion weights/component provenance remain in notes and ROADMAP. The following page states concrete matched-data switch criteria and the 2–3-day diagnosis time box. ORB is the first localization route; RTAB is the mapping-first alternative.
- Calendar weeks are conditional, inventory is unconfirmed where evidence is missing, and no booking is claimed. Total effort remains about 11–28 engineer-days with a separate 2–5-day tool contingency and unknown queues.
- Preserved USB >=5000M, exact raw IR1 Y8 640x480/15 + gyro/200 + accel/100, unchanged rate/gap limits, 20/105/mandatory 300-second N2 stages, N1→N2→N3 order, separately attested stereo profile, calibration warnings, separate serial identities and STM32H7 balance/motor/jump ownership.

### Build, rendering and document checks

Reproduce from `slides_roadmap/`:

```bash
latexmk -xelatex -interaction=nonstopmode main.tex
gs -dSAFER -dBATCH -dNOPAUSE -sDEVICE=png16m -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -r156 -sOutputFile=preview/page-%02d.png main.pdf
swift -module-cache-path qa/swift-cache qa/extract_pdf_text.swift main.pdf qa/revision1-pdf-text.json
python3 qa/check_revision1.py
```

All final commands succeeded. `qa/revision1-build-final.log` and `main.log` record a clean 23-page build: no Overfull, Underfull, Warning, Error or missing-character diagnostics. `qa/revision1-render-gs.log` records all 23 preview pages. PDFKit rendering was also exercised; Ghostscript with antialiasing generated the final previews for independent rendering review. `qa/revision1-extract.log` and `qa/revision1-pdf-text.json` retain text extraction.

`qa/revision1-checks.log` validates all 23 page numbers, eight six-row phase blocks, absence of prohibited visible vocabulary, exact raw rates/gaps/soak and USB requirement, score arithmetic, local Markdown links, 23 preview files and existence of the preserved v1 PDF. These are document-only checks; no synthetic receiver/conversion or sensor test is claimed.

### Page inspection

Every rendered page was opened for inspection. Reopened affected pages after changes. Initial issues corrected: hardware label crossing the timeline's second row, Beamer consuming small gate text as an unused subtitle, crowded score/table layouts, unsupported Unicode arrows and phase-label color/alignment. The final layout uses the existing font sizes, canvas and palette; dense tables have modest local line-spacing changes rather than frame scaling.

| Page | Final inspection |
|---|---|
| 1 | Historical starting evidence, reference-data caveat and controller boundary fit. |
| 2 | Whole road, week ranges and hardware labels fit without overlap. |
| 3 | Glossary readable; terms explained in plain language. |
| 4 | Preparation phase and small platform code visible; six rows fit. |
| 5 | Dependencies and owner's authorization requirement fit. |
| 6 | Input phase, small ordered codes and observable completion fit. |
| 7 | Exact profile, stages, rates, gaps and mandatory soak readable. |
| 8 | Calibration phase, target explanation and separate overnight time fit. |
| 9 | Saved-data replay phase and traceable results fit. |
| 10 | Live phase and approved-limit completion fit. |
| 11 | Estimate age, clock caveat and percentiles readable. |
| 12 | Eight scored candidates, judgment caveat and weights fit. |
| 13 | Default and evidence-based switch conditions readable. |
| 14 | Controller health phase and synthetic scope fit. |
| 15 | Supported robot phase and local-control completion fit. |
| 16 | Motion phase, operator repeat and separate approval fit. |
| 17 | Bench/calibration inventory and booking table fits. |
| 18 | Live/controller/robot inventory and booking table fits. |
| 19 | Software stack and future-tool dependencies fit. |
| 20 | Weeks 1–3, dates, owners and visible results fit. |
| 21 | Weeks 4–6, contingency and supported-before-motion rule fit. |
| 22 | Optional navigation diagram and later-scope requirements fit. |
| 23 | Linked primary sources and planning limitations fit. |

Final visual review: no detected clipping or diagram/table overlap. Previews and PDF text are document QA artifacts, not experimental evidence.

### Provenance and limitations

Git state inspected before edits: branch `claude/project-thread-rhsrup`, HEAD `b45bb6d`, substantial existing dirty/untracked work. COMMON explicitly prohibits Git mutations; no branch switch, commit or push occurred. Changes stayed in the roadmap folder. Primary ORB/OpenVINS repositories were checked; RTAB branch web retrieval failed, so no new support/version claim was inferred from that retrieval. Existing dated research remains the score provenance.

No SSH, install, camera command, ORB execution, capture, calibration/firmware/network mutation, public interface implementation, purchase, lab booking or external message occurred. Hardware and all acceptance gates remain unverified by this revision. The schedule and controller/motion limits remain proposals for the owner to review.

REVISION 1 FINAL
