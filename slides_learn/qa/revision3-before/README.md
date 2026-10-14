# How WBR perception works

`main.pdf` is the 45-page teaching deck. `preview/page-01.png` through `page-45.png` are its rendered pages. Start with the PDF; the appendix contains the glossary, tool list and reproduction commands.

The deck builds from embedded-system concepts through stereo, IMU measurements, frames and time, SLAM, calibration, software recording, evaluation and the gate ladder. Nine recaps invite the reader to explain each part aloud. A table corner provides the running example. Illustrative calculations are distinguished from the saved EuRoC results.

Build and render on this Mac, from the repository root:

```sh
cd slides_learn
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
python3 qa/check_source.py
```

Requirements: XeLaTeX, latexmk, the moloch Beamer theme, Avenir Next and Menlo fonts, macOS Swift/PDFKit/AppKit, and Python 3. The renderer is the existing external script named by the brief; it was read and executed without editing it.

`main.tex` is the build input. `qa/build_source.py` is the authored source-construction helper used in this session; running it regenerates and overwrites `main.tex`. Normal PDF reproduction does not require that helper. If editing the helper, regenerate before building. If editing `main.tex` directly, do not run the helper afterward.

Source locations are in each frame's speaker notes, and primary method references are on the last page. Normal Beamer output hides speaker notes; inspect `main.tex` to see the detailed provenance. The theme, palette, fonts and canvas were copied from `slides_course/main.tex`. P03, P04, P08 and P10 are byte-identical copies of conceptual course illustrations. All new diagrams are TikZ. No image was generated.

`READER_REVIEW.md` records the first full reader self-review and its requested fixes. `REVIEW_LOG.md` records revisions, the complete second image review, final changed-page checks and limitations. Build and render outputs are retained in `qa/`; `qa/artifact-manifest.json` records hashes of final source, PDF, images, logs and relevant source documents.

For manual validation, read all page images in order at full resolution. Ask whether each page can be explained aloud after one reading, whether terminology is defined before use, and whether anything overlaps or enters the footer. Check the worked calculations against their stated illustrative assumptions. This self-review is not an independent student comprehension test. The deck documents saved project evidence; building it validates no sensor, SLAM runtime or gate.

A subsequent reader pass applies targeted edits to main.tex. The input deck, previews
and prior review records are preserved in qa/reader-review-before/. READER_REVIEW.md
records this pass, and its results are appended to REVIEW_LOG.md. The original
qa/build_source.py produces the earlier deck and would overwrite these revisions.
To reconstruct this revision from the archived source, run
python3 qa/apply_reader_fixes.py, then use the normal build and render commands above.
Normal PDF reproduction requires only main.tex. New logs use the reader-review prefix.

Revision 2 updates pages 8, 25, 38, 40 and 45 from the 14 October session addendum.
It explains the slow recording writer and RAM workaround, the uninitialized
keyframe pointer and pending rebuild, the 8 GB Pi and unresolved power, and moves
the noise diagram's reference label clear of its curve. The deck remains 45 pages.
The prior deck and previews are preserved in qa/revision2-before/; new verification
logs use the revision2 prefix. REVIEW_LOG.md ends with REVISION 2 FINAL.

Build this version from main.tex with the normal commands above. Both historical
helpers, qa/build_source.py and qa/apply_reader_fixes.py, produce earlier versions
and would overwrite Revision 2. The addendum documents short diagnostic tests;
this deck build performs no camera, Pi or SLAM runtime validation.
