# Deck E build and self-review

Date: 14 October 2026. Scope: `slides_brief/` only. Continued the previous folder state, which contained BRIEF.md and builder/rotation logs but no deck source. Preserved those logs. Read Git status, branch and recent history without changing Git. The brief's explicit no-Git-mutation rule overrides the general feature-branch preference for this build.

## Source review

Read the authoritative 14 October addendum, 13 October session facts, EuRoC benchmark report, course RPE evaluation summary, demo material and 15 October lab runbook. Copied the report's included preamble/theme/palette and reused only the permitted P04 asset. The older report's camera-never-run and 8-GB-not-measured wording is superseded by the addendum.

Kept important distinctions: initial native build used three compatibility patches; fourth patch is applied but rebuild unfinished. Still take has a shutdown gap. Card bottleneck is strongly inferred, not a proven causal measurement. The 15-second memory test succeeded; a full 100-second take remains pending. The original benchmark used the 4 GB Pi; no 8 GB rerun numbers were found. RPE is a one-second relative displacement error, not a constant accumulated drift rate. Room accuracy requires ground truth. Blocker ownership is proposed role allocation; sources do not assign named people.

## Build and review loop

1. Created eleven slides, with the exact requested cover wording, full-sentence outcome titles on the ten content slides, sources in hidden speaker notes, no more than four short bullets, one schematic TikZ gap timeline and the requested blocker table.
2. First compile failed because Beamer parsed the cover's opening group as an inline frame title. Added the same `relax` guard used in the reference deck. Preserved the failed build log; did not force a failed build through.
3. Second compile succeeded. Rendered all eleven pages with the requested Swift renderer and inspected each page individually at 1280-pixel width. Found crowded text at column boundaries in the blocker table and an unnecessarily long plan takeaway. Also shortened the three-sentence opening summary and expanded AI on the cover.
4. Rebuilt and rendered the final PDF. Inspected all eleven final page images individually again. The table now has distinct readable columns, the final takeaway avoids an awkward line-break hyphen, and the summary has three concise sentences. No clipping, footer collisions or illegible text remained.

## Final page-by-page review

| Page | Outcome and review |
|---|---|
| 1 | Exact cover wording, AI reporting relationship, WBR expansion and permitted camera illustration are legible. |
| 2 | Three sentences state what works, what blocks progress and what happens next; ample spacing. |
| 3 | Native build, new camera and 8 GB board are distinct short bullets; fourth-patch rebuild is not claimed complete. |
| 4 | Accuracy range is prominent; paper comparison, RPE definition, narrow scope and pending rerun are readable. |
| 5 | Both IR streams and IMU are reported; the shutdown gap is explicit. |
| 6 | Gap duration and rate mismatch are clear; schematic timeline is labeled as not to scale; causality remains inferred. |
| 7 | Zero drops and 33-millisecond maximum gap are explicit; 100-second capture remains unmeasured. |
| 8 | First-frame crash, pointer fix and power-interrupted rebuild form one clear status message. |
| 9 | All five blockers have needs and proposed owners; power, card, stick speed, connectivity and calibration are retained. |
| 10 | Requested rebuild-to-summary sequence is preserved; offline review precedes live; reliability and accuracy limits are visible. |
| 11 | Only source-supported availability, connectivity and lab timing decisions are requested. No delivery or booking is assumed. |

Each outcome can be identified within 20 seconds. This is a builder readability judgment, not a measured user-reading trial. The whole deck is suitable for a five-minute briefing. The cover is the required title/date rather than a sentence; table labels and diagram ticks are intentionally compact.

## Validation and reproduction

Commands run from `slides_brief/`:

```sh
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
swift -module-cache-path qa/swift-cache qa/extract.swift main.pdf > qa/deck-text.txt
```

Final build and rendering exited successfully; renderer reported 11 pages. Final TeX log has no errors or overfull/underfull boxes. Extracted visible text has no evidence labels, source paths, commands or flags. Source inspection confirms at most four bullets per slide. Image checksum confirms P04 is identical to the allowed original. Final checks, PDF checksum and all reviewed preview checksums are recorded in `qa/checks.json`. Build/render/text logs are retained in `qa/`.

All validation was local document compilation, text inspection and visual review. No SSH, network, package installation, camera, ORB-SLAM3 execution, capture or hardware action occurred. No files outside `slides_brief/` were edited; no commits or pushes were made. Runtime status remains historical, and no experiment gate is promoted.

FINAL


## Revision 1 — two jobs, product focus

Scope: only the owner’s Revision 1 request. Inspected Git status, branch and recent history read-only before changes. The brief prohibits Git mutations, so the branch was retained. Preserved the original source, PDF, previews, README, review log and checks in `qa/revision1-baseline/`; pre-existing logs remain unchanged. No files outside `slides_brief/` were edited.

The revised eleven-slide deck has a cover, four system-status slides and six forward-plan slides. It explains the record/replay chain in one TikZ diagram with component status and the later STM32H7 safety boundary, retains the benchmark and recording results, then turns the shortest path into lab setup, rebuild, capture, replay/plot and live/summary steps. Each step states why, team work, owner participation, observable completion and sequence. The final slide separates the conditional demo result from product acceptance and names stable power, storage qualification, calibration and fresh N1–N3 evidence as follow-up work.

Source review reused the authoritative 14 October addendum, 13 October facts, EuRoC report, course RPE summary and 15 October runbook; the safety boundary follows AGENTS.md. Sources remain in hidden notes. Owner/team responsibilities are proposed briefing roles, not historical named assignments. The plan promises no unsupported build duration, hardware arrival or booking. The raw-input gates remain entry requirements too: the diagnostic take cannot replace the mandatory 300-second soak, exact raw profile, USB rate or timing/health thresholds. The owner’s explicit camera-availability authorization remains necessary at the bench. No gate is promoted.

### Build and visual review

The first source-generation attempt used a repository-relative path from inside the deck folder and failed before writing the source. Corrected the path, then built and rendered the revised deck successfully. Inspected all eleven round-one page images individually. Fixed an awkward word break in the trajectory diagram, clarified the visual-inertial product goal, labeled the camera as the new unit and included the measured same-card boot on the 8 GB Pi. Rebuilt, rendered and inspected all eleven final pages individually again at 1280-pixel width. No text clipping, overlapping diagram labels or footer collisions remained.

| Page | Final review |
|---|---|
| 1 | Exact cover/date and the Pi 5 visual-inertial milestone are clear; permitted P04 image retained. |
| 2 | One diagram shows the six-stage route, per-stage status and later safety boundary. |
| 3 | Benchmark accuracy is retained with ATE/RPE expansions, narrow scope and pending 8 GB rerun. |
| 4 | Streaming, long-take gaps, inferred card bottleneck and measured short RAM fix remain distinct. |
| 5 | Patch/rebuild state, same-card boot, power, connectivity, storage and calibration are readable. |
| 6 | Owner lab/hardware requests and ordered entry gates are visible; 300-second soak is explicit. |
| 7 | Rebuild purpose, team checks, owner support and completion condition are concise. |
| 8 | 100-second capture, owner motion, input/copy review and repeatability purpose are explicit. |
| 9 | Replay/plot checks precede owner review and live; room accuracy limit is visible. |
| 10 | 90-second live attempt, owner participation and one-slide summary deliverable are clear. |
| 11 | Conditional demo scope and power/storage/calibration/gate follow-up complete the product plan. |

Each page’s outcome is identifiable within 20 seconds as a builder judgment, not a measured reading trial. The cover uses the prescribed wording; diagram labels and role labels are deliberately compact. The preamble/theme/palette and permitted image were retained unchanged.

### Reproduction and validation

Run from `slides_brief/` using existing local installations:

```sh
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
swift -module-cache-path qa/swift-cache qa/extract.swift main.pdf > qa/deck-text-revision1.txt
```

Final build and rendering succeeded; PDF has eleven slides. TeX log has no errors or overfull/underfull boxes. Text/source checks confirm at most four bullets per slide, one hidden source note per slide, and no visible paths, commands, flags, hashes or evidence labels. P04 matches the permitted original. Checks and final PDF/source/preview checksums are in `qa/checks-revision1.json`; round-one/final build and render logs and extracted text remain in `qa/`.

All validation was camera-free, offline document compilation and review. No SSH, network, installation, camera capture, ORB-SLAM3 execution or hardware action occurred. No Git mutations, commits or pushes occurred. Hardware results are historical source observations; the demo is still a conditional future plan.

REVISION 1 FINAL
