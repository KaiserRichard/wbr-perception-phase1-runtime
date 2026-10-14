# Revision 1 of the roadmap deck (read slides_roadmap/COMMON.md first)
Claude reviewed v1 (saved as qa/main-v1.pdf). It is correct but too dense and gate-coded for the owner,
and it lacks pieces the owner explicitly asked for. Revise `main.tex` (and ROADMAP.md where needed):
1. Plain names first: every phase gets a plain-English name (e.g. "Stable power and storage",
   "Trustworthy camera data", "Calibrate the camera", "SLAM on our own recordings", "SLAM live on the
   Pi", "Health signal to the STM32", "On the robot") with the N-gate code only in small text.
2. Remove agent jargon from slides: no "CAMERA AVAILABLE", "B1", "source-age", "fixture", "entry
   checks", "held-out", "advisory" without a plain explanation. Define each technical term once.
3. Add the missing pages: (a) the whole road on one page as a TikZ timeline from today to the robot,
   with week ranges and the hardware each phase needs under it; (b) a hardware and lab booking table:
   item | which phase | have / ordered / lab / buy | when to book | what to prepare first; (c) a
   software stack table by phase; (d) a week-by-week plan for the next 4–6 weeks; (e) a slide showing
   the algorithm comparison (ORB-SLAM3 vs the alternatives from R1 and R1b) as a compact scored table,
   stating what would make us switch.
4. Keep each phase slide in the What / How / Tools / Hardware / Done when / Time pattern, but write
   "Done when" as something the owner can see (e.g. "a 100 s recording with no gaps longer than X").
5. Target about 20–24 slides. Rebuild, render, inspect every page, append "REVISION 1 FINAL" to REVIEW_LOG.md.
