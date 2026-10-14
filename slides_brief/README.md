# Deck E — owner status report

Historical status as of 14 October 2026. Revision 1: eleven slides for a five-minute supervisor briefing. The cover and four status slides explain the system; six forward-plan slides state why each step is needed, owner participation, observable completion conditions and order. Sources live only in speaker notes in `main.tex`; the PDF hides notes. No runtime, camera, network, or hardware tests were run to produce this deck.

## Reproduce

From the repository root, using the existing local TeX and Swift installations:

```sh
cd slides_brief
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
swift -module-cache-path qa/swift-cache qa/extract.swift main.pdf > qa/deck-text.txt
```

Inspect all eleven `preview/page-*.png` files at their original size. Check full-sentence outcome titles, readable text, whitespace, no clipping, and whether each slide conveys its outcome within 20 seconds. Source and layout review details are in `REVIEW_LOG.md`.

## Provenance and limits

The authoritative 14 October session addendum overrides older report wording. Additional evidence: 13 October session facts, EuRoC report, the course trajectory-evaluation summary, and the 15 October lab runbook. The palette, preamble, theme and helpers were copied from `slides_report/preamble.tex`, as included by `slides_report/main.tex`. P04 was copied unchanged from `slides_course/images/P04.png`; no raster imagery was generated.

The system diagram shows the record/replay route and each component’s status; live mode bypasses the recorder. The previous gap timeline is retained in the baseline snapshot. Card bottleneck causality is strongly inferred. Only the 15-second RAM capture was measured. Patch four is applied but its rebuild/replay remains unfinished. No 8 GB EuRoC rerun is reported. Owner/team responsibilities are a proposed role division for the briefing, not an evidenced assignment to named individuals. All future runtime work remains subject to the lab runbook and explicit camera availability; no gate is promoted.

The build stayed inside this folder and preserved the previous builder logs. The pre-revision source, PDF, previews and review documents are in `qa/revision1-baseline/`. Revision-specific build/render/text logs and checks are in `qa/`. The brief prohibits Git mutations, so the current branch was retained; nothing was committed or pushed.
