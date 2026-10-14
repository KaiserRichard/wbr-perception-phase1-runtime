# Brief: deck B — process and learning deck (2026-10-13)

Builder rules: work ONLY inside `slides_progress/`. Read anything in the repo; do not edit outside
this folder (in particular not `slides_course/`, `slides_report/`, `third_party/`, docs).
No git commands that change index/branches/commits. English only.

## Purpose and audience
For the owner themself (4th-year electronics/telecom student, strong embedded/Linux, new to
SLAM evaluation). A process deck, not a final report: where the project is, what was done on
2026-10-13 explained from scratch, what comes next step by step, and which tool is used at each
step. They must finish it able to run and direct the next steps without losing direction.
Length about 35–45 pages. The 109-page `slides_course/main.pdf` is the deep reference: do not
repeat its theory; instead cite "Reference deck p. N" (look up real page numbers in
`slides_course/main.tex`/preview) for depth. A separate short advisor deck `slides_report/` is
being built in parallel by another builder; don't coordinate with it.
An earlier aborted attempt at progress pages is in `slides_course/qa/phase5-aborted/main.tex`
(search for the 2026-10-13 section). You may reuse its correct content and TikZ, but
re-check every claim against the sources.

## Style
Same preamble/theme/palette/fonts/macros/evidence badges as `slides_course/main.tex`
(copy its preamble). TikZ for every diagram; mixed layouts (tables, two-column, annotated
timelines, worked examples, checklists), never the same template page after page. Evidence
labels MEASURED / CALCULATED / SOURCE-SUPPORTED / INFERRED / ASSUMED / PLANNED / OPEN.
No gate PASS. No invented numbers. You may copy images from `slides_course/images/`.

## Outline
Part 1 Where we are (3–4 p.): whole-system map with today's position; gate ladder with status;
what changed (new D435i unit and its two serials, 4 GB Pi on microSD stand-in).
Part 2 Today's work explained (12–15 p.): platform and power (vcgencmd throttled flags,
under-voltage 49 % of samples, why it invalidates timing); ORB-SLAM3 native build, the 3
patches and why each was needed, swap; what EuRoC MH01 is; what ground truth is and how it is
obtained; what ATE is (SE(3) alignment without scale, RMS of residuals, formula, TikZ before/
after alignment with residual vectors, `evo_ape tum ... -a`), RPE briefly; the 3-run results vs
paper with run-to-run variation explained; what N4A proves and does not prove; gate status.
Part 3 The two D435i programs (8–10 p.): `d435i_record` (streams, why emitter OFF, device
timestamps, .db3 + timestamps.csv, 18.4 MB/s budget); patched `stereo_inertial_realsense_D435i`
(--bag offline = N4B, live = N4C, --no-viewer, what the IMU-handling patch fixes); TikZ data
path; why offline before live; config/calibration status (intrinsics, baseline, nominal
extrinsics, ASSUMED IMU noise); status built-never-run.
Part 4 Next steps as a runbook (10–12 p.), in order: fix power (5.1 V/5 A), storage migration to
128 GB card, N1/N2 on the new unit, first hand-motion take (recipe and log lines that mean
success/failure), N4B offline run and evaluation, calibration (Kalibr camera–IMU, Allan
variance for IMU noise), N4C live, profiling. Per step: goal, tool, command shape, expected
output, PASS criterion (from slides_course gate tables), failure symptom → where to look.
Part 5 Tool map (2–3 p.): each tool (librealsense, realsense-ros, rosbag2, ORB-SLAM3, Pangolin,
evo, Kalibr, Allan-variance tool, vcgencmd, etc.), what it does, which step uses it, status.
Part 6 How to direct agents for the next steps (1–2 p.): bounded tickets, evidence required.

## Sources
`experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md` (authoritative summary),
`experiments/2026-10-13-*/`, `docs/PROJECT_STATE.md`, `docs/NEXT_GATE.md`, `slides_course/main.tex`.
The paper value ~0.036 m (Campos et al., T-RO 2021) is quoted from memory in the facts file;
verify if you can, else label "table not re-verified". Tools not yet used are PLANNED.

## Build and review
`cd slides_progress && latexmk -xelatex -interaction=nonstopmode main.tex`; render with
`swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview`;
inspect every page at full size, fix, repeat. Write REVIEW_LOG.md ending "FINAL" and a short README.md.

## New illustrations (owner generates them)
Never generate images yourself. If a slide needs a new illustration that the existing
`slides_course/images/P*.png` cannot serve, use a visible named placeholder and add a prompt to
`image-prompts/BATCH.md` in this folder, in the same format as `slides_course/image-prompts/BATCH.md`
(reuse its STYLE GUIDE and HARDWARE REFERENCE). The robot must be a wheel-biped: a torso on
two articulated legs with one wheel at each foot, NOT a low wheeled cart. Do not reuse P01,
P02, P07 or P12 where the robot shape matters: they show a cart.

## REVISION 1: real cover page (owner comment on page 1)
Page 1 looks neither like a cover nor like a content slide. Fix:
1. Add a proper title/cover page as page 1, in the same style as the cover of
   `slides_course/main.pdf` and `slides_report/main.pdf`: title "WBR Perception — Progress
   Report", subtitle such as "Process, results and next steps", "Owner's operating guide",
   date 13 October 2026, and the platform line (D435i, Raspberry Pi 5 / ROS 2 Jazzy,
   ORB-SLAM3 stereo-inertial, STM32H7 boundary). An image is optional: reuse
   `slides_course/images/P04.png` (D435i) or a TikZ figure; do NOT use P01/P02/P07/P12 (cart robot).
2. Turn the current page 1 into an ordinary content slide "Where we are" with the normal
   frame title, laid out like other content pages (Today / Next boxes, reading route as a
   small agenda or table, takeaway line). Remove the stray orange circle if it is part of the deck.
3. Update the reading-route page numbers and any internal page references for the +1 shift.
   Rebuild, render, inspect pages 1–3 and any page whose references changed. Log "REVISION 1 FINAL".
