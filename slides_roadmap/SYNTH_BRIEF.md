# Synthesis: the roadmap document and deck (read slides_roadmap/COMMON.md first)
Inputs: `slides_roadmap/research/R1_algorithms.md`, `R1b_algorithms_independent.md` (an independent second opinion; if it does not exist yet, poll every 60 s for up to 40 minutes before continuing without it), `R2_integration.md`, `R3_plan.md` and the repo facts.
The owner asked: do not be biased, do not jump to conclusions. Where R1 and R1b disagree, show both views and the evidence, then decide; keep alternatives visible with switch triggers.
Resolve conflicts between them explicitly (pick one, say why). Then produce:
1. `slides_roadmap/ROADMAP.md`: the concise, detailed roadmap. Phases from now to deployment on the
   robot. For each phase: goal (the question it answers), steps (how), software tools, hardware and
   lab needs (and when to book), owner actions, exit criteria (observable), duration range,
   risks. Plus the hardware booking table, the decision list with defaults, and the week plan.
2. `slides_roadmap/main.tex` → `main.pdf`: a deck of about 16–22 slides for the owner. Style: copy
   the preamble from `slides_brief/main.tex` (same look). Plain sentences, one idea per slide, slide
   titles state the point, spell out abbreviations once, no file paths or evidence labels on slides
   (sources in \note{} and a references slide). Structure: where we are (1 slide, with a simple
   diagram) → the whole road on one page (TikZ timeline/phase ladder from today to robot) → one
   slide per phase (what / how / tools / hardware / done-when / time) → hardware and lab booking
   plan (table) → software stack by phase (table) → the robot integration boundary (TikZ: Pi ↔
   STM32 message, what happens on failure) → risks and decision points → this week and next week.
   Never generate images; TikZ only. Do not use slides_course/images P01/P02/P07/P12.
3. Build `cd slides_roadmap && latexmk -xelatex -interaction=nonstopmode main.tex`; render
   `swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview`;
   inspect every page, fix layout and clarity, write REVIEW_LOG.md ending "FINAL".
