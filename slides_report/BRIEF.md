# Brief: deck A — advisor progress report (2026-10-13)

Builder rules: work ONLY inside `slides_report/`. Read anything in the repo; do not edit outside
this folder (in particular not `slides_course/`, `slides_progress/`, `third_party/`, docs).
No git commands that change index/branches/commits. English only.

## Purpose and audience
A short report the owner presents to their advisor in a normal meeting slot (about 15 minutes,
15–18 main slides + up to 4 backup slides). It reports progress, it does not teach everything.
The 109-page reference deck `slides_course/main.pdf` is the deep reference; the learning deck
`slides_progress/` (built in parallel by another builder) explains things from scratch. This
deck links to neither in-slide beyond a final "Further detail" line.
One message per slide, readable from the back of a room, large figures, few words.

## Style
Same preamble/theme/palette/fonts/macros/evidence badges as `slides_course/main.tex`
(copy its preamble). TikZ for every diagram. You may reuse `slides_course/images/P01.png`
(title) and P04 (D435i) by copying into `slides_report/images/`. Evidence labels:
MEASURED / CALCULATED / SOURCE-SUPPORTED / INFERRED / ASSUMED / PLANNED / OPEN. No gate PASS
unless the evidence says so (it does not). No invented numbers.

## Outline (adjust only if a source contradicts it)
1 Title. 2 Problem and goal (WBR; perception on Pi 5, balance on STM32H7; failure isolation).
3 Ownership boundary diagram. 4 One-diagram data path (D435i → librealsense → recorder/ROS 2 →
ORB-SLAM3 → trajectory → evaluation; later health signal → STM32). 5 Method: gate ladder
N0–N7 and the evidence rule. 6 Gate status table as of 2026-10-13 (status + evidence path per
gate). 7 What changed since the last report (new D435i unit, 4 GB Pi on microSD stand-in,
native ORB-SLAM3 build + 3 patches). 8 N4A setup: EuRoC MH01, ground truth, unmodified upstream
example, 3 runs. 9 N4A result: table + bar chart of 3 runs vs paper (~0.036 m). 10 What N4A
proves / does not prove. 11 D435i pipeline built (recorder + patched stereo-inertial program),
status built-not-run. 12 Blockers and risks (under-voltage 49 % of samples, timing invalid,
storage margin, nominal calibration, 4 GB RAM). 13 Next steps with order and exit criteria.
14 What I need / questions for the advisor (only if supported; else omit). 15 Summary.
Backup: ATE definition and alignment; the 3 build patches; power evidence; storage calc.

## Sources
`experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md` (authoritative summary),
`experiments/2026-10-13-*/` (REPORT.md etc.), `docs/PROJECT_STATE.md`, `docs/NEXT_GATE.md`,
`slides_course/main.tex` (gate definitions and PASS criteria; keep consistent with it).
The paper value ~0.036 m (Campos et al., T-RO 2021, ORB-SLAM3 stereo-inertial EuRoC MH01) is
quoted from memory in the facts file; verify if you can, else label "table not re-verified".

## Build and review
`cd slides_report && latexmk -xelatex -interaction=nonstopmode main.tex`; render with
`swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview`;
inspect every page at full size, fix, repeat. Write REVIEW_LOG.md ending "FINAL" and a short README.md.

## New illustrations (owner generates them)
Never generate images yourself. If a slide needs a new illustration that the existing
`slides_course/images/P*.png` cannot serve, use a visible named placeholder and add a prompt to
`image-prompts/BATCH.md` in this folder, in the same format as `slides_course/image-prompts/BATCH.md`
(reuse its STYLE GUIDE and HARDWARE REFERENCE). The robot must be a wheel-biped: a torso on
two articulated legs with one wheel at each foot, NOT a low wheeled cart. Do not reuse P01,
P02, P07 or P12 where the robot shape matters: they show a cart.

## REVISION 2: bring the advisor report up to 14 October
Note: the owner has hand-edited this deck since FINAL (sources moved to notes, gate tables
without path columns, page 4 data-path redraw, page 13 risk table, page 14 takeaway, no
unexplained "SDK"). Keep all of that.
Using `experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md`, update the deck to 14 October: 8 GB Pi
in use; camera streaming verified on a still take; first moving take failed from microSD write
speed and the RAM-recording fix; offline crash and patch 4 (rebuild pending); next steps = the
fast-track demo plan (`experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md`). Add at most
two slides; stay presentable in ~15 minutes. No source lines or paths on slides. Rebuild,
render, inspect changed pages, log "REVISION 2 FINAL".
