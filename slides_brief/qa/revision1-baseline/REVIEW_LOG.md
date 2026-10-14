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
