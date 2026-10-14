# WBR perception implementation deck

Phase 6 curates deck C from 109 to **91 pages**, behind the FINAL advisor deck A (`../slides_report/`) and progress deck B (`../slides_progress/`). It preserves the pre-curation deck in `qa/main-v3-109p.tex` / `.pdf`, the Phase-1 outline, P01–P12 illustrations and historical QA records. The reference retains every gate acceptance table and all 46 figures. Repeated prose is merged; empty section dividers and a duplicated symbolic example are cut. See [the 109-page audit](qa/PHASE6_AUDIT.md) and [current page list](qa/PHASE6_PAGE_LIST.md). The deck is an engineering guide, not a hardware qualification report. N4A now has three measured MH01 runs (ATE 0.0415 / 0.0368 / 0.0416 m), while all gates remain OPEN: stable power and reviewed acceptance budgets are missing; N4A RPE is now CALCULATED. The active platform is a 4 GB Pi / 32 GB microSD stand-in, and the new D435i has device serial 317422076650. Recorder and estimator are built, never run on this camera. Refresh N0 after repairing power. Authoring stays in this directory except the Phase-6 brief's explicit exception: update B's C-page references and rebuild B. No camera, Pi, controller, firmware or ORB-SLAM3 experiment was run.

Deliverables: [PDF](main.pdf), [LaTeX source](main.tex), [current page list](qa/PHASE6_PAGE_LIST.md), [review log](REVIEW_LOG.md), [Phase-3 source audit](qa/PHASE3_SOURCES.md). Detailed operational explanations and provenance are retained in LaTeX speaker notes. Results pages 80–82 contain N4A accuracy, wall durations, memory and power summaries. N4A RPE at 1 s and diagnostic Sim(3) ATE are now CALCULATED on page 80. Per-frame timing, queues and missing resource series remain empty and labeled “To be filled after N4/N5 runs”.

## Build and review

Use XeLaTeX, latexmk, the moloch Beamer theme, Avenir Next and Menlo. The generated LaTeX is self-contained apart from installed packages/fonts and optional illustration assets. From the repository root:

```sh
cd slides_course
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
python3 qa/check_phase6.py
```

The Swift command uses the OS repository as a read-only renderer reference. It produces 1280 × 719 page images. After any content or image change, inspect every rendered page at full size, including captions, arrow geometry, labels and footer clearance. Structural checks alone cannot approve visual quality or hardware readiness.

`build_deck.py`, `phase3_depth.py`, `phase6_curate.py` and `phase7_rpe.py` are the modular authoring sources. Phase 6 reuses status/results corrections from `phase5_progress.py` without inserting its separate progress section. The second module revises selected existing frames and inserts the Phase-3 depth pages. To regenerate the LaTeX, run `python3 slides_course/build_deck.py` from the repository root, then build and review again. It reads the existing Phase-1 outline and the OS deck preamble at its canonical path; it writes only this deck's LaTeX and the original-outline page list. The Phase-6 module writes the current audit, page list and old-to-new map; do not regenerate historical Phase-3 inventories. Edit the generator for persistent content changes, or preserve direct LaTeX changes before regenerating.

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

Current image pages: P01/1, P02/3, P03/7, P04/9, P05/14, P06/18, P07/22, P08/30, P09/45, P10/63, P11/74 and P12/89. No illustration placeholders remain. Phase 4 also attaches the page-20 kernel/SDK and ROS-topic labels inside their corresponding process/queue boxes. These fixes live in `phase3_depth.py` and survive regeneration.

## Sources and limits

The brief's owner-confirmed status overrides historical optimistic PASS wording. Local sources include AGENTS.md, CLAUDE.md, repository documentation, saved experiment summaries, configuration/scripts and read-only upstream ORB-SLAM3 source. The deleted root audit was read through `git show HEAD:D435I_BASELINE_AUDIT.md`, not restored. The initial branch was `feat/d435i-camera-capture-20260913`, at `5932457`; unrelated working-tree changes were preserved. No index, branch, stash, commit or push operation was performed.

The visual system comes from the OS deck and its committed academic Beamer skill/playbooks, read only. Primary external references and verification limits are listed in [SOURCES.md](qa/SOURCES.md) and on the single references page. [source-hashes.json](qa/source-hashes.json) records the local source snapshot; [phase3-final-artifacts.json](qa/phase3-final-artifacts.json) identifies the Phase-3 reviewed PDF, LaTeX and page images. Phase-2 inventories and hashes remain historical. [PHASE3_SOURCES.md](qa/PHASE3_SOURCES.md) records the revision audit.

Offline checks cover deck structure and synthetic assignment fixtures only. Planned calibration, stereo extension, health interface, transport choices and numerical performance budgets require their own reviewed evidence and approval. This deck does not implement or approve a new node graph, message, dataset format or controller policy.

Phase-3 QA uses the updated `qa/check_deck.py`; its original 89-page version is preserved as `qa/check_deck-v1.py`. Build/render logs and the individual-page verdict ledger use the `phase3-` prefix. Numerical N4–N7 budgets, interface rate/transport/stale threshold and missing live-driver/converter commands remain explicit UNKNOWN or PLANNED. The command blocks are future Pi examples, never evidence of execution.

## Phase-6 provenance and limits

[PHASE6_SOURCES.md](qa/PHASE6_SOURCES.md) records October sources and the independently re-verified paper comparator. [REVIEW_LOG.md](REVIEW_LOG.md) records full-size review, fixes, exact commands and final checks. The old `check_deck.py` remains the historical 109-page checker; use `check_phase6.py` for this deliverable. Structural checks are offline document checks, never runtime qualification. No new imagery is needed; retained generated-hardware limitations remain in [MAPPING.md](images/MAPPING.md).

B now has 44 pages after a concurrent cover/reading-route edit. Phase 6 preserves it; this task only changes B's 43 C-reference arguments. Current B verification and concurrent-change provenance are recorded in C's review log and QA files.

## Phase-7 calculated results

The supplied [trajectory evaluation summary](qa/n4a-traj-eval-summary.md) provides SE(3) RPE translation/rotation RMSE and diagnostic Sim(3) ATE. Provenance: `claude/project-thread-upkfjv`, commit `d3f9540`, PR #2, tool not yet merged; validation passed per its README. Pairing selects the first later reference pose at least 1 s later, without interpolation; 3,639 is the timestamp-association count per run. This is not an evo RPE equivalence claim. D435i accuracy stays UNKNOWN and no gate is promoted. Phase 7 explicitly permits the matching RPE-only edits and rebuild in B. See the Phase-7 review log for changed pages and reproduction commands.
