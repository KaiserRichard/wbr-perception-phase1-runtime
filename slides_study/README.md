# WBR perception study deck

A lecture and two scripted lab sessions for the project owner. The current deck has **160 pages**, with worked examples, common mistakes, recap answers in Beamer notes, 32 synchronized step cards, home-analysis instructions and two printable one-page session checklists. All hardware gates remain **OPEN**.

- [main.pdf](main.pdf): presentation and printable backup checklists.
- Printable session checklists: PDF pages **156** and **157**.
- [LAB_PLAN.md](LAB_PLAN.md): the same step records and commands, copyable from a terminal.
- [PROGRESS.md](PROGRESS.md): continuation state.
- [REVIEW_LOG.md](REVIEW_LOG.md): quality-loop evidence and material limitations.
- [qa/SOURCES.md](qa/SOURCES.md), [qa/COMMAND_AUDIT.md](qa/COMMAND_AUDIT.md): inspected sources, hashes, command/path/flag checks.
- [lab-config/](lab-config/): source-checked flat ROS launch mappings and recording QoS; installed hardware behavior is UNVERIFIED.

## Build

From this directory, with XeLaTeX/latexmk, moloch, Avenir Next and Menlo installed:

```bash
python3 build_study.py
latexmk -xelatex -interaction=nonstopmode main.tex
rg -n '^!|Overfull|Missing character|undefined' main.log
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \
  main.pdf preview
python3 qa/audit_documents.py
swift -module-cache-path qa/swift-cache qa/pdf_audit.swift \
  main.pdf qa/pdf-audit.json
```

The `rg` command must produce no output (exit 1). Inspect every rendered PNG after any change. `build_study.py` is the persistent authoring source and deterministically emits `main.tex`, `LAB_PLAN.md` and the page/step inventories. It never executes lab commands. For visible answer/provenance pages, enable the inherited `show only notes` option and build a separate output; the delivered presentation hides notes. The original preamble, fonts, palette, canvas and helper macros are retained; only metadata/footer total and normal-size listings support are added.

## Sources and precedence

The lecture follows the richer `base/main-v4-91p.tex` sequence, updated by `base/main.tex` Phase 8 on every conflict. `base/README.md` and `base/REVIEW_LOG.md` govern provenance; original base files are unchanged. The latest supplied `sources/LAB_DAY_2026-10-15-4b63.md` and `sources/STM32_LINK_STEP_2026-10-15.md` supply operational interfaces and later, explicitly dated diagnostic reports.

Use `../docs/D435I_CALIBRATION_PLAN.md`, not the older supplied source copy. Material updates include the qualified 128 GB-card exception, printable 6×4 AprilGrid, SYSTEM_TIME rejection, Intel-Mac Kalibr image and `--cams` plural. The plan's stale six-row print paragraph is corrected using actual target YAML/README; the small printable target's far-range visibility is an explicit open S-test limitation. Worktree project state and NEXT_GATE remain authoritative for WBR gate status. Missing worktree AGENTS/architecture/decisions/evidence-index files were read from the canonical Mac checkout without modification.

Exact interfaces were inspected in the canonical WBR demo/remote/summary scripts, lab runbook, older db3 converter, worktree calibration and take/evaluation/link tools, and canonical realsense-ros source. CN uses `~/Desktop/CN/hw/README.md`, E7 design/tickets/implementation and synergy/hardware documents. The requested original OS protocol is v1; the NET_STATUS behavior needed for CN is in the newer read-only `~/.worktrees/OS-wt-cn/` v3 protocol and integration sources. CN's 16 October owner inventory is distinct from historical WBR power measurements.

Inherited raster P01 is conceptual artwork with known robot/board inaccuracies, never a wiring guide. Technical diagrams and calculations are authored in TikZ/LaTeX. No image generation, browsing, GUI, hardware access, deployment, branch change or commit was performed.

## Operating limits

Each supervised lab session is capped at 150 minutes. The 30-minute warm-up and ≥4-hour provisional / preferred 15–24-hour stationary Allan recording run at home between visits, not inside that lab-time budget. Full E6 four-pass campaigns, E7 sustained qualification, V-route ablations, card setup/builds and installation are separate preparation/follow-up work.

Every primary S/C/A take is explicitly ROS-recorded. Native SDK replicas need validated derived ROS companions; native N2/vendor and Allan CSV lack a supplied companion path. The ordinary ROS wrapper bags also lack a reviewed source-preserving extractor for the supplied native-format Kalibr/Allan tools. Those branches are marked UNVERIFIED/BLOCKED instead of inventing an executable or running two camera owners together.

Other explicit gaps: strict N3 receipt acceptance for the approved card exception, installed wrapper/metadata/exposure behavior, and real-UART CN/OS firmware/result-producer readiness. Only loopback/host/virtual-serial integration is reported tested so far. Stopping results while heartbeat continues can show HOLD→FAILSAFE; stopping heartbeat can enter FAILSAFE directly. FAILSAFE is latched, and the current board port requires reset before fresh readiness. These demonstrations do not establish WBR physical balance or N7.
