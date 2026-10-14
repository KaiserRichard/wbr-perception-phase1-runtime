# Brief: deck E — short status report to the owner (as their supervisor)

Builder rules: work ONLY inside `slides_brief/`. Read anything in the repo; edit nothing outside it.
No ssh, no network, no installs, no git commands that change anything. English only.

## Framing
The owner is Claude's supervisor. This deck is the AI team reporting to them the way they
report to their advisor: concise, brief, outcome-first. 9–12 slides, readable in 5 minutes.
One idea per slide; the slide title is a full sentence stating the outcome. Full sentences,
at most 3–4 short bullets. No file paths, hashes, evidence labels (MEASURED/OPEN…), commands
or flags. Say "measured" or "not yet measured" in words only where it matters. Spell out every
abbreviation once (SLAM, IMU, ATE, RPE, USB, RAM…). One simple TikZ diagram or chart where it
replaces text (e.g. the recording-gap timeline, the RAM-buffer fix, the plan).

## Content (facts ONLY from the sources below; do not invent)
1. Cover: "WBR perception — status report, 14 October 2026".
2. Bottom line in three sentences: what works, what is blocked, what happens next.
3. What was done (13–14 Oct): ORB-SLAM3 built natively on the Pi with 4 small patches; new
   D435i unit set up; 8 GB Pi now in use with the same card.
4. Result 1 — ORB-SLAM3 reproduces published accuracy on EuRoC: three runs ATE 3.7–4.2 cm vs
   about 3.6 cm in the paper; RPE about 1.3 cm per second. What this proves / does not prove.
   (If the 8 GB EuRoC rerun numbers are not in the sources, say they are still pending.)
5. Result 2 — the camera streams correctly (20 s still take: both IR cameras 30 Hz, gyro, accel).
6. Problem found — the first 100 s hand-moved take was unusable: gaps of 0.3–2.9 s every ~5 s,
   because the microSD wrote only ~16.6 MB/s while the camera needs 18.4 MB/s. Small timeline.
7. Fix that worked — record into RAM first, copy afterwards: 15 s test, 0 dropped frames,
   IR 30 Hz, max gap 33 ms; 100 s (~1.7 GB) fits in RAM on the 8 GB Pi.
8. Problem found — offline ORB-SLAM3 crashed on the first frame: an upstream bug (uninitialised
   pointer), fixed by patch 4; the rebuild was interrupted by a power loss and must be resumed.
9. What is blocked and on whom: power (under-voltage even on the 8 GB Pi; needs the 5 A
   supply), storage (128 GB card), 64 GB USB stick too slow (~1 MB/s), Ethernet port loose /
   Wi-Fi not yet seen on the 8 GB Pi, calibration not done. Table: blocker | needs | owner.
10. Next steps — the fast-track demo plan, in order (resume rebuild → 100 s take into RAM →
    offline ORB-SLAM3 + plot → live run → one summary slide), and what stays unproven until the
    5 A supply and calibration exist.
11. Decisions needed from the owner (only those the sources support, e.g. power supply,
    Wi-Fi/Ethernet, lab session timing). Omit if none.

## Sources
`experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md` (authoritative for 14 Oct),
`experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md`, `experiments/2026-10-13-n4a-euroc-mh01/REPORT.md`,
`slides_course/qa/n4a-traj-eval-summary.md` (RPE), `experiments/2026-10-14-d435i-demo/`,
`experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md` (fast-track plan),
`slides_report/main.tex` (for consistent wording). Newer files in experiments/ dated 2026-10-14 may be used if relevant.

## Style and build
Copy the preamble/theme/palette from `slides_report/main.tex` (its \src macro writes to notes;
keep sources only in \note{}). Generous whitespace, large text. Images: may reuse
`slides_course/images/P04.png`; never P01/P02/P07/P12; never generate images.
Build `cd slides_brief && latexmk -xelatex -interaction=nonstopmode main.tex`; render with
`swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview`;
inspect every page; check: could the owner read each page in 20 seconds and know the outcome?
Fix and repeat. Write REVIEW_LOG.md ending "FINAL".

## REVISION 1 (owner, after first build): two jobs, product focus
The deck must do two things: (1) help the owner understand the system and where it stands,
(2) tell them clearly what comes next and WHY, because the goal is to speed up progress toward a
working product: the D435i visual-inertial SLAM demo running on the Pi 5.
- First half (about 4–5 slides): a one-diagram picture of the system (D435i → librealsense →
  recorder in RAM → ORB-SLAM3 → trajectory → plot; STM32 boundary later) and where each part
  stands today, plus the results and problems above.
- Second half (about 5–6 slides): a concrete forward plan to the demo, from
  `experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md` and the addendum's shortest path.
  One slide per step or a clear step table: step, why it is needed, what the owner must do or
  provide (hardware, being at the lab, moving the camera, approving), what "done" looks like
  (an observable outcome), and the time or order. End with what the demo will and will not
  prove, and what comes after the demo (5 A supply, calibration, then gates N1–N3 properly).
Keep the total at 10–14 slides. Rebuild, render, inspect, log "REVISION 1 FINAL".
