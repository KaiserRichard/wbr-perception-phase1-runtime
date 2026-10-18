# BRIEF — WBR end-to-end study guide (Markdown)

The owner found the slide deck too text-heavy and wants ONE end-to-end, detailed Markdown guide
covering both theory and the practical labs. Write it in English at
`study_guide/WBR_STUDY_GUIDE.md` in this worktree (`~/.worktrees/wbr-study-deck`). Work only inside
`study_guide/`. No commits, no branch changes, no hardware/SSH/GUI, no images generated.

## Reader
4th-year Electronics & Telecommunications student, strong in embedded/STM32/C/Linux. They will study
this guide end to end and then execute the labs from it. Write full explanatory prose (not
compressed jargon fragments), causal: problem → mechanism → assumptions → how to observe → how to
test → what would contradict → project implication. Spell out abbreviations on first use.

## Inputs (read before writing)
- Content already researched and audited: `slides_study/main.tex` (160-page deck, its frames and
  speaker notes), `slides_study/LAB_PLAN.md` (audited commands, step records), `slides_study/qa/`
  (COMMAND_AUDIT.md, SOURCES.md, steps.json, command-blocks.json), `slides_study/lab-config/`.
- Richer teaching source: `slides_study/base/main-v4-91p.tex` (91-page lecture) and
  `slides_study/base/main.tex` (Phase-8 facts; wins on conflicts).
- Lab sources: `slides_study/sources/LAB_DAY_2026-10-15-4b63.md`,
  `slides_study/sources/STM32_LINK_STEP_2026-10-15.md`, `docs/D435I_CALIBRATION_PLAN.md`.
- Project truth: `docs/PROJECT_STATE.md`, `docs/NEXT_GATE.md`, `docs/ARCHITECTURE.md`,
  `docs/DECISIONS.md`, `docs/EVIDENCE_INDEX.md` (in this worktree or the canonical repo
  `/Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime`, read-only).
- E6/E7 and HOLD/FAILSAFE: `~/Desktop/CN` (hw/README.md, docs/E7_DESIGN.md, docs/OS_CN_SYNERGY.md,
  docs/HYBRID_PLAN.md, docs/HARDWARE.md, e7/) and the OS repo
  `~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/protocol/PROTOCOL.md` + supervisor source. Read-only.
- If `slides_study/REVIEW_CODEX_K.md` exists (independent review of the deck), apply every valid
  finding about commands/criteria/technical correctness.

## Structure
0. How to use this guide; evidence labels (KNOWN / MEASURED / CALCULATED / SOURCE-SUPPORTED /
   INFERRED / ASSUMED / UNKNOWN / OPEN); current project state in one table (all gates as the sources say).
Part I — Theory (the bulk; aim for depth of a lecture course). Cover at least every topic of the
   91-page deck plus the study deck: robot context and ownership (Pi vs STM32, camera IMU vs body IMU,
   why the robot must not fall if the Pi fails); D435i hardware, streams, USB and power; storage
   budget; stereo geometry with depth/disparity error; IMU model, noise densities, random walk, Allan
   deviation; frames and transform conventions (T_a_b direction, lever arms); clocks and every
   timestamp kind, clock domains, latency decomposition; ROS 2 graph, topics/types, QoS compatibility,
   queues/backpressure, rosbag2 (storage formats, what a bag does and does not preserve); calibration
   (intrinsics, stereo extrinsics, camera–IMU with Kalibr, time offset sign, AprilGrid, observability
   and motion excitation, review thresholds); ORB-SLAM3 (threads, tracking, local mapping, loop closing,
   Atlas, stereo-inertial initialization, settings audit, IMU settings contract, input association);
   evaluation (ATE/RPE math with alignment choices, evo/trajectory tool, the measured EuRoC MH01
   result, proxies without ground truth, latency P50/P95/P99, drops, CPU/thermal/memory); health
   envelope and supervision (N6), Pi↔STM32 link (UART framing, CRC, heartbeats, supervisor states
   INIT/FRESH/HOLD/FAILSAFE, latching and recovery) (N7); gate ladder N0–N7 with per-gate acceptance and
   diagnosis tables; bottom-up debugging order; CN E6/E7 background.
   Every chapter ends with: worked example (numbers labeled CALCULATED/illustrative), common mistakes,
   check-yourself questions WITH answers (collapsible `<details>` blocks are fine).
   Use Mermaid diagrams (```mermaid) and ASCII diagrams where a picture helps; use LaTeX math ($...$).
Part II — Practical labs. Two short sessions (≤150 min each) plus home analysis, same scope as
   the deck: Session 1 = power/USB checks, D435i raw data, calibration recordings, STM32 link bench;
   Session 2 = re-runs, E6, E7, HOLD/FAILSAFE demo; Home = H0–H7. Start with packing list, shell
   variables (define $RUN, $DATA, $ID, STUDY, etc.), stop rules, and a Mermaid flow per session.
   Every step: goal and why now; physical setup; copy-paste commands (keep the audited command bytes
   from LAB_PLAN.md unless the review found an error; mark unverified ones `# UNVERIFIED`); expected
   output (example where sources have one); PASS/FAIL rule in words plus the number and its label;
   on FAIL what to do; files produced and which home step consumes them. Record ROS 2 bags in the lab,
   analyse at home. End with Session-1→2 handoff checklist and printable checklists.
Part III — Reference: glossary, command cheat sheet, file/folder map, open gaps, sources with paths.

## Quality loop
- Every command block copy-pastes cleanly (run `bash -n` on extracted blocks; script names/flags
  checked against the real scripts). Keep a `study_guide/CHECKS.md` with what was checked.
- Mermaid blocks syntactically valid (simple flowchart syntax, no exotic features).
- No gate shown PASS without source evidence. No invented numbers, scripts or firmware commands.
- Keep `study_guide/PROGRESS.md` updated after each part so another account can resume.
Final message: word count, section list, open gaps.
