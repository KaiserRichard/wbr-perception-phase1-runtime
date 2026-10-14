# WBR perception implementation deck

Phase 3 revises the existing deck to 109 pages, retaining the Phase-1 outline, P01–P12 illustration batch and `qa/main-v1.pdf`. The depth revision adds operational gate contracts, measurement/clock/evidence tables, annotated diagrams and symbolic worked examples. The deck is an engineering guide, not a hardware qualification report. No Pi gate has passed; restart from fresh N0 evidence. All work for this build stays in this directory. No camera, Pi, controller, firmware or ORB-SLAM3 experiment was run.

Deliverables: [PDF](main.pdf), [LaTeX source](main.tex), [Phase-3 page list](qa/PHASE3_PAGE_LIST.md), [review log](REVIEW_LOG.md), [Phase-3 source audit](qa/PHASE3_SOURCES.md). Detailed operational explanations and provenance are retained in LaTeX speaker notes. Results pages 96–98 contain empty axes marked “To be filled after N4/N5 runs”.

## Build and review

Use XeLaTeX, latexmk, the moloch Beamer theme, Avenir Next and Menlo. The generated LaTeX is self-contained apart from installed packages/fonts and optional illustration assets. From the repository root:

```sh
cd slides_course
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
python3 qa/check_deck.py
```

The Swift command uses the OS repository as a read-only renderer reference. It produces 1280 × 719 page images. After any content or image change, inspect every rendered page at full size, including captions, arrow geometry, labels and footer clearance. Structural checks alone cannot approve visual quality or hardware readiness.

`build_deck.py` plus `phase3_depth.py` are the modular authoring sources. The second module revises selected existing frames and inserts the Phase-3 depth pages. To regenerate the LaTeX, run `python3 slides_course/build_deck.py` from the repository root, then build and review again. It reads the existing Phase-1 outline and the OS deck preamble at its canonical path; it writes only this deck's LaTeX and the original-outline page list. Run `python3 qa/phase3_inventory.py` inside this directory to update the actual Phase-3 page list. Edit the generator for persistent content changes, or preserve direct LaTeX changes before regenerating.

## Illustration drop-in

The existing [prompt batch](image-prompts/BATCH.md) and [outline](image-prompts/OUTLINE.md) are unchanged. Generate one prompt per ChatGPT message, in P-id order, and drop the downloaded PNG files into `images/` with their original ChatGPT filenames. Then run:

```sh
python3 images/assign.py --dry-run
python3 images/assign.py
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
```

The assignment utility sorts by the timestamp in the filename, falls back to modification time, and uses filename order to break ties. It copies into the next missing P01–P12 slots, prints the mapping, preserves originals and occupied slots, skips previously assigned content, and records hashes in `images/assignments.json`. Chronological ordering assumes the supplied downloads were generated in P-id order. Visually verify each image's subject, hardware, allowed labels and fit; the manifest starts with `visual_review: PENDING` because assignment is not visual approval. Rebuild and repeat the page review after images arrive.

Phase 4 fills all twelve illustration slots using visual matching of the messy filenames in `images/incoming/`, rather than timestamp assignment. Originals are preserved. See [MAPPING.md](images/MAPPING.md) for subjects and retained prompt/hardware defects, and [phase4-assignments.json](images/phase4-assignments.json) for byte-identical copy hashes. Do not rerun chronological assignment for this incoming batch.

Current image pages: P01/1, P02/4, P03/10, P04/12, P05/19, P06/25, P07/30, P08/38, P09/55, P10/74, P11/86 and P12/107. No illustration placeholders remain. Phase 4 also attaches the page-20 kernel/SDK and ROS-topic labels inside their corresponding process/queue boxes. These fixes live in `phase3_depth.py` and survive regeneration.

## Sources and limits

The brief's owner-confirmed status overrides historical optimistic PASS wording. Local sources include AGENTS.md, CLAUDE.md, repository documentation, saved experiment summaries, configuration/scripts and read-only upstream ORB-SLAM3 source. The deleted root audit was read through `git show HEAD:D435I_BASELINE_AUDIT.md`, not restored. The initial branch was `feat/d435i-camera-capture-20260913`, at `5932457`; unrelated working-tree changes were preserved. No index, branch, stash, commit or push operation was performed.

The visual system comes from the OS deck and its committed academic Beamer skill/playbooks, read only. Primary external references and verification limits are listed in [SOURCES.md](qa/SOURCES.md) and on the single references page. [source-hashes.json](qa/source-hashes.json) records the local source snapshot; [phase3-final-artifacts.json](qa/phase3-final-artifacts.json) identifies the Phase-3 reviewed PDF, LaTeX and page images. Phase-2 inventories and hashes remain historical. [PHASE3_SOURCES.md](qa/PHASE3_SOURCES.md) records the revision audit.

Offline checks cover deck structure and synthetic assignment fixtures only. Planned calibration, stereo extension, health interface, transport choices and numerical performance budgets require their own reviewed evidence and approval. This deck does not implement or approve a new node graph, message, dataset format or controller policy.

Phase-3 QA uses the updated `qa/check_deck.py`; its original 89-page version is preserved as `qa/check_deck-v1.py`. Build/render logs and the individual-page verdict ledger use the `phase3-` prefix. Numerical N4–N7 budgets, interface rate/transport/stale threshold and missing live-driver/converter commands remain explicit UNKNOWN or PLANNED. The command blocks are future Pi examples, never evidence of execution.
