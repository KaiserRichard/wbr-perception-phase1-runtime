# Advisor progress report — 14 October 2026

Open `main.pdf`: **17 main slides + 4 backups + the existing references page**
(22 pages total), intended for about 15 minutes. Revision 2 adds one main slide
for the offline crash and patch 4; it preserves the owner’s data-path drawing,
source notes, path-free gate tables, risk-table format and next-step takeaway.

Updated: 8 GB Pi in use; still-take streaming; failed microSD moving take;
15-second RAM workaround; patch 4 applied with rebuild/replay pending; and the
15 October diagnostic plan (RAM capture → replay → plot/review → live).
No gate PASS is claimed. Successful 100-second RAM capture, post-patch replay,
room accuracy, calibration and live performance remain unverified.

Build and render from the repository root:

```sh
cd slides_report
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
swift -module-cache-path qa/swift-cache qa/revision2/extract.swift
```

Requires XeLaTeX/latexmk, moloch, Avenir Next, Menlo, and macOS Swift/PDFKit.
`preview/page-01.png` through `page-22.png` are full-page renders.
`main.tex` keeps sources in speaker notes; `SOURCES.md` records provenance and
limits. Theme, palette and fonts are retained; all diagrams/charts are TikZ.
P04 is the existing sensor illustration; no images were generated.

Suggested meeting allocation: slides 1–8 about 5 minutes, 9–14 about 6 minutes,
15–17 about 4 minutes. Backups/references are outside the main presentation.
These are presentation allocations, not experimental timings.

See `REVIEW_LOG.md` (ending `REVISION 2 FINAL`) and `qa/revision2/` for checks.
Pre-revision TeX/PDF, README and sources were saved there; historical logs remain.
All writes stayed inside `slides_report/`. No Git index/branch/commit changes,
push, hardware/camera process, ORB-SLAM3, Pi/SSH or calibration command ran.
