# Common rules for software-foundation research workers

Question owner asked (via project lead): what software must exist between today's state and running
visual-inertial SLAM on the WBR (wheel-biped robot), and in what order should it be built? The owner
does NOT want premature conclusions. Separate algorithm-agnostic components from ones that depend on
the SLAM engine choice (ORB-SLAM3 default; OpenVINS fallback; VINS-Fusion, Basalt, RTAB-Map considered).

Read-only inputs (shared checkout, other threads are working there — never write into it):
S=/Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime
- $S/AGENTS.md, $S/CLAUDE.md, $S/docs/*.md (ARCHITECTURE, DECISIONS, PROJECT_STATE (stale), NEXT_GATE (stale))
- $S/experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md, $S/experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md
- existing code: $S/experiments/2026-10-13-n4b-d435i-prep/ (d435i_record.cpp, d435i_input.h, d435i_rs.h,
  stereo_inertial_d435i_file.patch, analyze_take.py), $S/experiments/2026-10-14-d435i-demo/plot_run.py,
  $S/tools/trajectory_eval/traj_eval.py (ATE/RPE tool, PR #2)
- ALREADY-DONE roadmap research — do NOT duplicate, build on it and cite it:
  $S/slides_roadmap/research/R1_algorithms.md (engine choice, ROS 2 path, TF ownership, calibration, Pi perf targets)
  $S/slides_roadmap/research/R2_integration.md (Pi<->STM32 candidate contract, UART/COBS/CRC framing, receiver policy, test ladder)
  $S/slides_roadmap/research/R3_plan.md (hardware, critical path); R1b_algorithms_independent.md if present.

Fixed constraints: Pi 5 (8 GB, Ubuntu 24.04, ROS 2 Jazzy) owns perception/SLAM; STM32H7 owns balance, LQR,
VMC, FSM, motor safety; the robot must not lose balance if the Pi/ROS fails. D435i IMU and body IMU stay
separate (no naive fusion). Frames and timestamps are first-class (define clock domain for every stamp).

Research: web search allowed. Primary sources first (papers, official docs, upstream source code and
maintainer issues). Every external claim gets a URL, ideally to a file/line or section. Label every claim
SOURCE-SUPPORTED / MEASURED (repo evidence path) / INFERRED / ASSUMED / UNKNOWN. Separate what a source says
from your interpretation. Prefer reusing maintained tools over writing new code; say so explicitly when an
existing tool already covers a component.

Rules: write ONLY your one output file in this directory. No ssh, no installs, no git commands that change
anything, no edits elsewhere. English only. Be decisive: one recommendation per question plus the evidence
that would change it. Max ~2500 words plus tables.
