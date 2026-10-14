# Advisor progress report — 13 October 2026

Open `main.pdf`: **16 main slides + 4 backups**, intended for about 15 minutes.
`main.tex` contains speaker notes; `preamble.tex` copies the course theme, fonts,
palette, macros and evidence badge. The only raster asset is the existing P04
sensor illustration. Every diagram and chart is TikZ. No new image was generated.

Build and render from the repository root:

```sh
cd slides_report
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
```

Requirements: XeLaTeX/latexmk, moloch, Avenir Next, Menlo; macOS Swift/PDFKit
for the supplied renderer. `preview/page-01.png` through `page-20.png` are the
full-page review renders. See `REVIEW_LOG.md` for the completed review and
`SOURCES.md` for evidence paths, conflicts and the verified paper comparison.

Present slides 1–8 in about 6 minutes, 9–13 in about 5 minutes, and 14–16 in
about 4 minutes. These are presentation allocations, not experimental timings.
Backups are outside the meeting plan. Gate status is split across two slides
for legibility; the next-step sequence is also split across two slides. The
optional advisor-request slide is omitted because no concrete request is
recorded in the supplied evidence.

All gates remain OPEN or PLANNED. This build reads historical experiment
artifacts only: it runs no camera, ORB-SLAM3, Pi/SSH or hardware command. Earlier
builder logs and the brief are preserved; no Git mutation, commit or push was
performed. All new work is contained in `slides_report/`.
