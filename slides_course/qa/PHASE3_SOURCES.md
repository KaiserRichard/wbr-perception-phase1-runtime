# Phase-3 source and scope audit — 2026-10-10

Continued the existing builder's generator, main.tex, 89-page outline and v1 PDF; no restart. The Phase-1 prompt batch, outline and schedule, Phase-2 review record, historical QA hashes and qa/main-v1.pdf are retained. All writes stay inside slides_course/. Current branch feat/d435i-camera-capture-20260913, HEAD 5932457; no Git mutation, camera/ORB execution, SSH, calibration, firmware, package installation or upstream edit.

The owner-confirmed brief overrides older NEXT_GATE/PROJECT_STATE wording: NO Pi gate has passed; fresh N0 starts qualification. N0 extracts existing N1 platform prerequisites for teaching. N4A/B/C and N5–N7 contracts are proposed teaching/acceptance structure, not newly implemented validators. Numeric estimator, performance and controller acceptance budgets remain UNKNOWN. Future N4–N7 evidence filenames are explicitly proposed.

Primary local contracts re-read: Phase A runbook, N3 preparation, n3_topics.json, n3_baseline.yaml, n3_metrics.py; native bring-up thresholds; calibration readiness; offline preparation and two-week backlog; architecture, decisions, evidence index, state and historical Pi report. AGENTS.md, CLAUDE.md, README.md, Git status/branch/history, scripts/env.sh and config inventory inspected. Deleted root audit read with git show HEAD:D435I_BASELINE_AUDIT.md. Read-only pinned ORB System.cc, Settings.cc, stereo-inertial EuRoC reader/settings checked for threads, target/argv, headless constructor and trajectory output names.

Important source distinctions:

- N2 exact raw profile and 20→105→300 s progression are unchanged. CSV source/arrival stamps are kept separate; absent domain metadata and rounded motion do not prove synchronization or calibration.
- N3 is still IR1-only and ten explicit topics. Adding IR2/adapter format/live node is a separately reviewed extension, not implemented by these slides.
- The native offline handoff uses a mono target/example. The deck explicitly labels its stereo-target adaptation; argv/export names come from the actual pinned stereo-inertial reader. The candidate mono YAML is not a stereo-qualified settings file.
- Native bring-up stationary gyro ≤0.10 rad/s and accel 9.0–10.5 m/s² are engineering proposals, separately identified from automatic validator checks. No new thresholds invented.
- N4A depends on N0 in the hardware gate graph, plus separately authorized build/data/settings; N4B requires N3 plus stereo/calibration; N4C renews live qualification after offline acceptance. An independent EuRoC result cannot promote camera transport.
- Health envelope, publication rate, link, age rule and fallback are PLANNED. r_h and A_max remain symbolic/UNKNOWN; no ROS message or STM32 policy is implemented or approved.

Read-only OS style sources: slides_course main.tex preamble, README/REVIEW_LOG; slides playbook/layout/reviewer briefs; committed prompts/academic-beamer-deck/SKILL.md and its existing reference template. Inherited moloch, Avenir Next/Menlo, palette, 12pt body, evidence/figure/takeaway system retained; diagram geometry changed without font scaling.

Primary external records verified again during Phase 3:

- ORB-SLAM3 paper: https://arxiv.org/abs/2007.11898
- EuRoC dataset: https://projects.asl.ethz.ch/datasets/euroc-mav/
- ROS Jazzy QoS: https://raw.githubusercontent.com/ros2/ros2_documentation/jazzy/source/Concepts/Intermediate/About-Quality-of-Service-Settings.rst (HTML endpoint denied access; official raw documentation succeeded)
- REP-103 / REP-105: https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-0103.rst and rep-0105.rst
- evo metrics / formats: https://github.com/MichaelGrupp/evo/wiki/Metrics and https://github.com/MichaelGrupp/evo/wiki/Formats
- Planned tools: https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration and https://github.com/gaowenliang/imu_utils
- Pinned clock reader: https://github.com/realsenseai/librealsense/blob/v2.58.4/src/global_timestamp_reader.cpp

These records establish methods and candidate tools, not local compatibility or hardware measurements. Latency/window-rate/ATE examples are explicitly SYMBOLIC. Result axes remain empty and labelled “To be filled after N4/N5 runs”. Missing illustrations remain visible P01–P12 placeholders. Phase 3 performs deck/tooling QA only.
