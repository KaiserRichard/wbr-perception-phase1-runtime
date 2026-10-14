# Phase 2 source audit

Authoring date: 2026-10-10. Canonical WBR HEAD: 5932457; existing branch
feat/d435i-camera-capture-20260913; unrelated dirty work preserved. No Git
mutation, hardware execution, ORB execution, deployment or network changes.

The detailed page-source register and gate contracts remain in
../image-prompts/OUTLINE.md. BRIEF.md overrides older optimistic status: no
Pi gate passed. The existing 89-page outline was continued without rewriting
Phase 1 deliverables. N0 extracts platform prerequisites for teaching; N5–N7
are planned organizing gates, not accepted validators.

Read-only references inspected:

- WBR AGENTS.md, CLAUDE.md, README.md; docs architecture, decisions, state,
  next gate, evidence index, native bring-up, Docker audit, sensor validation,
  calibration readiness, tooling architecture and offline preparation/backlog.
- Phase A runbook and evidence reconciliation; historical experiment summaries;
  scripts/env.sh, config/script inventory; deleted root audit via git show.
- ORB-SLAM3 System.cc, Settings.cc, Tracking.cc, Frame.cc, ImuTypes.cc,
  stereo-inertial EuRoC reader/settings and repository preparation guidance.
- Read-only OS slides_course/main.tex preamble, README/REVIEW_LOG;
  slides playbook/layout/reviewer briefs; committed academic Beamer skill and
  preamble template. Copied preamble preserves class, moloch, Avenir Next,
  Menlo, canvas, palette, spacing, figure, placeholder, evidence and takeaway
  macros. Only project metadata changed. No OS deck PASS is inherited.

Primary web records rechecked during Phase 2:

1. https://arxiv.org/abs/2007.11898 — Campos et al.; v2 2021. No paper
   benchmark numbers copied as project results.
2. https://projects.asl.ethz.ch/datasets/euroc-mav/ — Burri et al., IJRR 2016;
   dataset contents and documented reference limitations.
3. https://raw.githubusercontent.com/ros2/ros2_documentation/jazzy/source/Concepts/Intermediate/About-Quality-of-Service-Settings.rst
   — offered/requested reliability and durability.
4. https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-0103.rst
   and rep-0105.rst — axes, units, continuous odom and jumping map.
5. https://github.com/realsenseai/librealsense/blob/v2.58.4/src/global_timestamp_reader.cpp
   — mapping mechanism, not this unit's physical synchronization.
6. https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration
   — candidate calibration requirements, not local build compatibility.
7. https://github.com/gaowenliang/imu_utils — candidate noise analysis tool.
8. https://github.com/MichaelGrupp/evo/wiki/Metrics — absolute/relative metrics.
9. https://www.raspberrypi.com/products/raspberry-pi-5/
   and https://www.intel.com/content/www/us/en/products/sku/190004/intel-realsense-depth-camera-d435i/specifications.html
   — product identity; no unsupported detailed specifications asserted.

Historical numeric claims use the local dated evidence, not vendor specs.
The 105-second raw CSV/PGM originals are absent from this Mac repository;
saved analysis/logs remain historical evidence only. CAD fallback, zero noise
arrays and enabled global time are never treated as measured calibration.
Actual camera transport, storage throughput, timing/noise/calibration,
algorithm initialization, trajectory accuracy and robot stability are unknown.
