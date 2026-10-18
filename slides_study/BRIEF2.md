# BRIEF 2 — make it a real study deck (expansion + plain-language pass)

Same rules as `BRIEF.md` (read it again: scope, style, no images, evidence labels, no hardware,
no commits). Continue from the current state: `build_study.py` generates `main.tex` and
`LAB_PLAN.md`; edit the generator, not only the output. Keep `PROGRESS.md` updated per part.

The owner's goal: a polished lecture deck they can **learn from** and then **execute in the lab**.
Two problems with the current 160-page build:

1. **The lecture shrank.** It has 61 lecture pages; the 91-page source (`base/main-v4-91p.tex`)
   taught more. Every topic in v4 must appear in the study deck, expanded, unless Phase 8
   (`base/main.tex`) explicitly retired it (then say so in REVIEW_LOG with the reason). Topics that
   look missing or thin include: robot context and research questions, odometry vs mapping, sensor-to-pose
   execution path, topic/type contract, queues and backpressure, storage qualification, robot vs camera
   transform ownership, global time, worked latency decomposition, calibration register, Atlas and
   mapping, settings audit before tuning, numeric IMU settings contract, health envelope and health
   supervision (N6), Pi-to-STM32 boundary (N7), per-gate N0–N7 acceptance and diagnosis tables, N4A/N4B/N4C
   contracts, N5 measurement (latency/loss/CPU/thermal/memory, P50/P95/P99), trajectory conversion and evo,
   bottom-up diagnosis, evidence gaps, conditional roadmap, conclusion. Target lecture ≥ 100 pages.
   For each major topic: concept frame(s) with a TikZ diagram, "why it matters for WBR", worked
   example, common mistake, check-yourself (answer on the next frame or in a backup answer key,
   not hidden in notes only — the owner reads the PDF, not the notes).
2. **Lab step cards are written in compressed jargon** (e.g. "Source-checked study configs deployed
   at STUDY; actual graph/readback reviewed; one wrapper."). Rewrite every step card in full,
   plain sentences a 4th-year student understands on first read: what this step proves and why it
   comes now, what you physically do (cable, camera position, motion), what you should see on screen
   (paste a short example of expected output where the source has one), the PASS/FAIL rule in words
   plus the number, and what to do on FAIL. Define every variable ($RUN, $DATA, $ID, STUDY...) on a
   "Shell variables used in the lab" frame before Session 1 and in LAB_PLAN.md. Add a one-frame
   "map" before each session showing the steps as a TikZ flow with the decision points.
   Keep the commands exactly as audited unless the review finds an error.

Also add, for Session 1 and 2, a "what you take home" frame listing every bag/file and which home
step (H0–H7) consumes it.

Then rerun the full quality loop from BRIEF.md (build clean, render, look at every changed page,
command audit, LAB_PLAN.md ↔ slides agreement) and update REVIEW_LOG.md. If
`slides_study/REVIEW_CODEX_K.md` exists when you finish the expansion, apply its findings too
(re-locate them by slide title since page numbers shift) and record each as fixed/declined with reason.
Final message: page counts (lecture/lab/home/backup), PDF path, open gaps.
