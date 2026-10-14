# Ticket A: audit slides_course against the owner's goal (report only, no edits)
Audience and style (from the project owner, verbatim intent): the slides exist so that I UNDERSTAND THE SYSTEM. Do not cram logs, raw numbers or calculations that only AI agents need. Write it like a concise report to a supervisor: short, to the point, one idea per slide, plain English, diagrams over text, spell out abbreviations once. The reader is a 4th-year electronics/telecom student (strong embedded/STM32/C/C++/Linux), new to SLAM/VIO.
Facts: use only experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md, experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md, experiments/2026-10-13-n4a-euroc-mh01/REPORT.md, experiments/2026-10-13-n4b-d435i-prep/ (README, n4b_plan.md, calibration_notes.md), docs/*.md, slides_course/main.tex and slides_report/main.tex. Do not invent numbers. Mark anything unverified as such in one short phrase.
Rules: no ssh, no network, no installs, no git commits/branches/stash. Do not edit slides_course/ or slides_report/ (another thread owns them). Write only in your own output folder.
Output folder: experiments/2026-10-14-deck-audit/.
Read slides_course/main.tex (90 frames) and write AUDIT.md:
1 For every frame: KEEP (helps understanding) / BACKUP (useful detail, move to appendix) / CUT (log/number-heavy, AI-to-AI material) with a 5-10 word reason. Then the resulting lean outline (target 30-40 main frames).
2 Factual corrections: anything that contradicts the session fact files (new camera serials, 8 GB Pi now used, ORB-SLAM3 built + 4 patches, N4A done, microSD stall -> RAM recording, 64 GB USB unusable, power). List frame title, wrong statement, correct statement, source file.
3 Missing explanations the owner needs to understand the system (max 10), each with a one-sentence suggested slide.
This audit is for the slide thread to apply; do not modify slides_course/.
