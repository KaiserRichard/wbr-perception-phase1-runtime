1. Phase 1: audit existing work and sources; deliver the numbered outline and P01–P12 prompt batch, then stop.
2. Obtain outline approval before Phase 2 frames; generate one P-id per ChatGPT message and retain downloaded filenames.
3. Phase 2: add images/assign.py to map timestamp-sorted unassigned downloads (mtime fallback) into next missing Pxx.png files, copying and printing mappings without overwrite.
4. Copy the OS course preamble and build main.tex with exact TikZ diagrams, English text, evidence labels and named missing-image placeholders.
5. Build with cd slides_course && latexmk -xelatex -interaction=nonstopmode main.tex; resolve all errors, box warnings, missing characters and undefined citations.
6. Render with swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview; inspect every page at full size and iterate fixes.
7. Write README.md and REVIEW_LOG.md with reproduction, sources, limitations, image mappings/placeholders, review rounds and FINAL only after QA passes; no hardware execution, commits or pushes.
