# WBR perception course deck — Phase 8

The October 14 revision has **38 main slides**, a references page, and **39 question-driven backup slides** (78 PDF pages). The main story explains the hardware, sensing, estimation, diagnostic results and next work. The appendix keeps gate acceptance, ROS/QoS, transforms, clocks, configuration, metrics and controller contracts. All gates remain OPEN.

Open [main.pdf](main.pdf). See the [page list](qa/PHASE8_PAGE_LIST.md), [audit disposition ledger](qa/PHASE8_DISPOSITION.md), [old-to-new page map](qa/phase8-page-map.json), and [review log](REVIEW_LOG.md). Source paths and original evidence columns are in LaTeX speaker notes rather than content-page footers.

The 8 GB Pi booted the unchanged 32 GB card, but power and later availability remain unresolved. The initial native build and three EuRoC trials are historical measured evidence. The D435i recorder now has diagnostic trials; card recording had large gaps, while a short RAM test was clean. The offline estimator crashed on its first frame. A fourth patch was applied in the Pi build copy, but rebuilding was interrupted. No successful D435i trajectory or calibrated accuracy is established.

The main ATE result is 0.0415 / 0.0368 / 0.0416 m, mean 0.040 m, after rigid rotation/translation alignment without fitting scale. The audit requests omission of the paper comparator and later RPE numbers from the main result; the appendix marks the earlier RPE claim unverified under its source restriction. The earlier Phase-7 calculation report and all historical QA/evidence remain unchanged.

## Build and validate

With XeLaTeX, latexmk, moloch, Avenir Next and Menlo installed:

```sh
cd slides_course
python3 build_deck.py
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
swift -module-cache-path qa/swift-cache qa/phase6-extract.swift \
  main.pdf > qa/phase8-pdf-text.txt
PYTHONDONTWRITEBYTECODE=1 python3 qa/check_phase8.py
rg -n '^!|Overfull|Underfull|Missing character|undefined' main.log
```

The final `rg` command must print nothing (exit 1 means no matches). The check is offline document QA only. After any edit, inspect every rendered page at full 1280 × 719 resolution for text, diagrams, table fit and captions. Neither compilation nor a clean diagnostic recording qualifies the hardware.

`build_deck.py` now dispatches to modular [phase8_audit.py](phase8_audit.py), which continues from the preserved incoming [91-page source](qa/main-v4-91p.tex). The matching PDF is `qa/main-v4-91p.pdf`. It does not rerun earlier phases or overwrite their audits. Make persistent changes in the Phase-8 module. The required version backup is immutable input; its SHA-256 is checked by the validator.

## Sources and provenance

Current facts come from `experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md`; curation follows `experiments/2026-10-14-deck-audit/AUDIT.md`. Historical baseline/build/calibration context comes from the October 13 session facts, N4A report, N4B plan/calibration notes, existing deck notes and bibliography. An input hash register is in `qa/PHASE8_SOURCES.md`. Pi raw evidence was not copied or independently rerun during this document task.

USB ≥5000M, N2 IR1 Y8 640×480/15 + gyro/200 + accel/100, timing thresholds, and the mandatory 300-second soak are unchanged. The paired IR1/IR2 30 Hz emitter-OFF development path is separate. Recording into RAM is a diagnostic workaround, not persistent-storage qualification. Camera, ORB execution, calibration/firmware, SSH, controller tests and network configuration were not performed by this build.

The optional `slides_progress/` reference update was not taken; that folder is unchanged. Its older numeric references target the archived 91-page deck. Use the Phase-8 page list/map for this revision rather than interpreting those old numbers as current.

## Illustrations

Existing image originals, P01–P12 assets, [prompt batch](image-prompts/BATCH.md), and [mapping/defects](images/MAPPING.md) are preserved. P01 remains on the cover; P10 appears in the provenance appendix. Other existing illustrations remain available in the archived version. No new images or regeneration are needed. Technical teaching visuals use TikZ; the current deck has 53 unique, consecutively numbered figures.

The existing drop-in utility still supports future missing images:

```sh
python3 images/assign.py --dry-run
python3 images/assign.py
```

It copies unassigned ChatGPT-named files into missing P-id slots; it does not replace occupied slots. Do not rerun chronological assignment for the Phase-4 incoming batch, whose images were matched by content. Any changed illustration requires a rebuild and visual review.
