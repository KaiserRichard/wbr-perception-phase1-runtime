# Study-deck progress

## Input review complete — 2026-10-18

No incoming `main.tex` or `PROGRESS.md` existed at the study-deck root. Base artifacts remain untouched. Read the 91-page teaching version, Phase-8 revision/provenance, lab and link runbooks, current calibration plan, project state/gates, local runtime/calibration/conversion tools, CN E6/E7 sources and OS supervisor integration sources.

Missing worktree inputs: root AGENTS.md and docs/{ARCHITECTURE,DECISIONS,EVIDENCE_INDEX}.md. Read their canonical Mac-checkout equivalents read-only. Work remains on the existing branch, without commits or hardware/network/GUI access.

Decisions: Phase 8 overrides the older lecture. Later lab replay observations are dated source reports, not new gate evidence. Current calibration plan wins over the supplied older copy: qualified 128 GB-card exception, 6×4 printable target, SYSTEM_TIME rejection, Intel Mac Kalibr image and `--cams`. Correct its stale six-row paragraph using actual target YAML. CN hardware owner inventory is dated separately from historical WBR measurements.

Two source limitations must stay visible: native SDK and ROS wrapper cannot concurrently own the camera; hours-long Allan capture exceeds either short supervised session. Use explicit ROS takes and separate native replicas, preserve identities, and label native-to-ROS compatibility / missing CSV companion bridge UNVERIFIED. No invented executable. Long stationary work is scheduled between sessions at home, separately from lab time.

Next: author lecture, synchronized step records/LAB_PLAN, compile and inspect all rendered pages, command audit, final review log.

## Part A authored

`build_study.py` now contains the expanded lecture in the 91-page teaching progression, updated with Phase-8 facts. Concepts have WBR motivation, worked examples, mistake/check questions with answers in notes. Added explicit timestamp kinds, continuous-time noise scaling, transform/time-shift signs, gate requirements, measured MH01 ATE, RPE source restriction and latched supervisor recovery. Native/ROS and WBR-bench/CN-supervisor firmware remain separate.

## Session 1 authored

Added 150-minute timeline, packing/stop rules, prepared-path contract, manifest, power/USB/N1, exact N2 stages and reviewed acceptance, N3 baseline, explicit ROS recipes/QoS, S and C1–C3 motions, Allan pilot/overnight split, link bench/optional analyzer and handoff. Step records carry goal/setup/expected/PASS-FAIL/fallback/files and drive both outputs. Explicit blockers include the archived N3 runner's storage receipt policy, native/ROS companion gaps and printable-target long-range visibility. Next: Session 2 and home-analysis cards, then full compile/render/audit.

## Session 2 authored

Added explicit two-Pi roles, selected E6 hardware pass and optional Wi-Fi/ONNX branches, E7-C gateway with exact CLI, real-UART readiness, network-result-loss vs heartbeat-loss injections, latched FAILSAFE/reset recovery and final archive. Full four-pass E6 campaign and E7 qualification exceed the short-session scope and are labeled separately. CN/OS hardware remains UNTESTED; E7 telemetry alone emits no INFERENCE and cannot establish supervisor FRESH. No invented firmware flash or result-producer command is provided.

## Home analysis and document build authored

`main.tex`, `LAB_PLAN.md`, README and flat ROS/QoS configs are generated. Current count: 157 pages (61 lecture pages), 32 complete step records, 50 command blocks. Added schema-aware home audit/export, Kalibr, native Allan, generic offline ORB plus optional demo wrapper, trajectory evaluation and printable session backups. Explicitly recorded source gaps rather than inventing adapters or firmware commands.

## Quality loop in progress

Initial compile passed but exposed missing Avenir glyphs; replaced with LaTeX transpose/arrow/checkbox symbols. Corrected authoring working-directory mistakes without touching sources; no failed operation is treated as successful. Current build has no required log-pattern matches. Command audit checks all 50 blocks for shell syntax and exact Markdown/TeX agreement, 21 first-party CLI families, config keys and 70 source hashes; PASS. Full render and every-page visual review remain underway. Final hashes/review log still pending.

## Visual round 1 complete; final polish built

Rendered all 157 initial pages using the mandated Swift renderer and looked at every page in full-resolution 4-page sheets, plus individual dense/cover examples. No overflow, overlap or clipped code/footer found. Corrected teaching clarity (first-use acronyms, bidirectional ORB worker links), captured wrapper logs explicitly, bound per-terminal take IDs, added explicit native/bench/CN archive commands and optional source-checked ONNX service. Final count is 160 pages, 32 step records, 53 command blocks. Final build is clean; final render/review and artifact manifest pending.

## FINAL — full document quality loop complete

Final deliverables: `main.tex`, `main.pdf` (**160 pages**), synchronized `LAB_PLAN.md`, README, REVIEW_LOG, study ROS/QoS mappings and QA artifacts. Printable session checklists are PDF pages 156/157. Final required latexmk and Swift renderer both exit 0. Required diagnostic rg and Underfull scan print nothing. All 53 command blocks match Markdown/TeX and pass shell syntax; 23 first-party CLI families and 76 immutable input/source hashes checked.

Visual coverage: every page in the 157-page draft was inspected in original-resolution four-page sheets; all 19 new/changed final pages individually rechecked. The 141 other final bodies are pixel-identical to reviewed content. Final page numbers/media boxes and body/footer bounds pass. Deterministic generation verified without rewriting outputs. Per-page verdicts, source/command registers, source/body comparisons and final artifact hashes are under `qa/`.

No unresolved document build/layout defect. Open operational gaps are intentional and detailed in REVIEW_LOG: ROS/native/Allan extraction and companions, N3 card receipt compatibility, actual sensor/power/calibration evidence, and real-UART CN/OS image/result-producer readiness. Long Allan work is outside both lab-time caps. No hardware gate promoted; no hardware/network/GUI action, deployment, branch change or commit performed. Work is ready for document review; future runtime work must resolve its labeled prerequisites.

## BRIEF2 — continuation started

Read BRIEF.md, BRIEF2.md, existing generator, progress, prior QA and both base decks. Preserved the incoming command/page/step registers and review log under qa/brief2-baseline. The incoming 160-page build has 61 lecture pages and notes-only answers. Expansion will preserve the audited command bytes, restore every v4 topic with Phase-8 factual precedence, add visible answers and explanatory diagrams, and replace compressed step cards with plain sentences generated into both outputs. Full build/render/every-page review and renewed command/source/agreement audits remain required. No hardware work or Git mutation is authorized or performed.
