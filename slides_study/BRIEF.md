# BRIEF — WBR study deck with a two-session lab plan

You are writing a lecture-style Beamer study deck in `slides_study/` of this git worktree
(`~/.worktrees/wbr-study-deck`, branch `claude/project-thread-wbmvb5`). Work only inside
`slides_study/`. Do not touch any other checkout, do not switch branches, do not commit, do not
open GUI apps, do not contact the Raspberry Pi, camera or STM32. Everything is offline document work.

If `slides_study/` already contains work from a previous builder (`main.tex`, `PROGRESS.md`),
continue from that state instead of restarting. Keep `PROGRESS.md` updated after every part
so another account can resume.

## Reader and goal

The reader is the project owner: a 4th-year Electronics & Telecommunications student, strong in
embedded/STM32/C/Linux. They learn best from slides. The deck must let them (1) understand the WBR
Phase-1 perception system deeply enough to explain it aloud, and (2) walk into the lab and execute two
short scripted sessions without improvising. English only.

## Inputs (read all before writing)

- Style + content base: `base/main.tex` (current 78-page course deck, Phase 8, latest facts) and
  `base/main-v4-91p.tex` (the 91-page lecture version; richer teaching content). `base/images/` holds
  the figures they use. `base/README.md`, `base/REVIEW_LOG.md` explain provenance rules.
- Lab sources (authoritative for the plan):
  - `sources/LAB_DAY_2026-10-15-4b63.md` — latest one-day lab runbook (steps 0–11, 9b STM32 link).
  - `sources/STM32_LINK_STEP_2026-10-15.md` — Pi↔STM32 link bench test.
  - `../docs/D435I_CALIBRATION_PLAN.md` — calibration plan (main-branch version; newer than
    `sources/D435I_CALIBRATION_PLAN.md`, use the docs one, note differences only if material).
- Project truth: `../docs/PROJECT_STATE.md`, `../docs/NEXT_GATE.md`, `../docs/ARCHITECTURE.md`,
  `../docs/DECISIONS.md`, `../docs/EVIDENCE_INDEX.md`, `../AGENTS.md`.
- Scripts the plan may call — read them to get exact names, flags and outputs; never invent a script:
  `/Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime/experiments/2026-10-15-demo-day/`
  (`demo.sh`, `remote.sh`, `summary.py`), `.../experiments/2026-10-15-lab-day/`,
  `.../experiments/2026-10-14-db3-to-euroc/` (rosbag .db3 → EuRoC), `.../tools/`,
  `../calibration/` in this worktree (Kalibr scripts, AprilGrid YAMLs, Allan tooling).
- HOLD/FAILSAFE: the STM32 supervisor states INIT/FRESH/HOLD/FAILSAFE are defined in
  `/Users/quockaiser/Desktop/OS/OS-project/heterogeneous-edge-ai-os/protocol/PROTOCOL.md`
  (MCU_STATUS 0x84) and the link firmware described in the STM32 link step. Read-only.

## Deliverable

`slides_study/main.tex` → `slides_study/main.pdf`, built with
`latexmk -xelatex -interaction=nonstopmode main.tex` from `slides_study/`. Copy needed images into
`slides_study/images/`. Target roughly 120–160 pages. Write `slides_study/README.md` (what it is,
how to build, sources) and `slides_study/LAB_PLAN.md` (the same two-session plan as plain Markdown
so commands can be copied from a terminal; slides and Markdown must agree).

### Style (keep identical)

Same preamble, moloch theme, 208×117 mm canvas, Avenir Next/Menlo, navy/teal/fault/paper palette,
helper macros (`\evidence`, `\takeaway`, `\deckitems`, `\coursefigure`, notes with provenance),
TikZ diagrams, evidence labels (KNOWN / MEASURED / CALCULATED / SOURCE-SUPPORTED / INFERRED /
ASSUMED / UNKNOWN / OPEN). No gate is PASS unless a source says so with evidence. Never shrink fonts
or use `\resizebox` on whole frames to cram text: split into more frames instead. Code on slides
uses `fragile` frames with a Menlo `semiverbatim`/`lstlisting` block small enough to fit, with a
line-break strategy for long commands (backslash continuation).

### Part A — Lecture (expand, don't just copy)

Start from the 91-page lecture flow and update facts with the 78-page Phase-8 deck (Phase 8 wins on
any conflict). For each concept add teaching depth: a "why it matters for WBR" frame, a worked
example or calculation where one is natural (clearly labeled CALCULATED/illustrative), a common
mistake, and a "check yourself" recap question with answer in notes or a backup slide. Topics at
least: system ownership (Pi vs STM32, camera IMU vs body IMU), D435i hardware and USB, stereo
geometry, IMU model and noise (Allan variance), frames and transforms, clocks and timestamps (all
the timestamp kinds), ROS 2 topics/QoS/rosbag, calibration (intrinsics, stereo extrinsics,
camera–IMU with Kalibr, time offset), ORB-SLAM3 stereo-inertial pipeline and initialization,
evaluation (ATE/RPE, the measured EuRoC MH01 result, proxies without ground truth), Pi↔STM32 link
and supervisor states, gate ladder N0–N7 and current state.

### Part B — Two scripted lab sessions (the main new content)

Replace the single long lab day with **two short sessions**, each ≤ ~2.5 h of lab time:

- **Session 1:** power and USB checks (Pi PSU/under-voltage flags, `vcgencmd get_throttled`, USB3
  link speed, firmware/serial, `rs-enumerate-devices`), D435i raw data checks (IR1/IR2/gyro/accel
  rates, timestamps domain, drops), calibration recordings (static IMU for Allan, S stereo take,
  camera–IMU Kalibr takes, per the calibration plan), and the STM32 link bench test (Step 9b,
  optionally 9c).
- **Session 2:** re-runs of anything that failed or was marginal in Session 1, the E6 and E7
  experiments, and the HOLD/FAILSAFE demo (show the STM32 supervisor going FRESH→HOLD→FAILSAFE when
  Pi heartbeats/data stop and recovering when they resume; the robot must not depend on the Pi).
  E6/E7 and the HOLD/FAILSAFE demo belong to the Computer Networks (CN) course project in
  `~/Desktop/CN` (read-only), integrated with the OS project's STM32 supervisor:
  - **E6** = edge-offloading run on the two real Pis (8 GB Pi 5 = edge server, 4 GB Pi = client).
    Commands: `~/Desktop/CN/hw/README.md` (also `hw/edge_server.py`, `hw/os_inference.py`).
  - **E7** = follow-on real-hardware experiment (STM32 tier, option C): `~/Desktop/CN/docs/E7_DESIGN.md`,
    `docs/CODEX_TICKETS.md` (E7, E7d2, T18), `~/Desktop/CN/e7/`. Mark what is untested on hardware.
  - **HOLD/FAILSAFE demo** = OS+CN integration part 6: network heartbeat and result age forwarded to
    the OS STM32 supervisor (`protocol/PROTOCOL.md` states); inject Wi-Fi loss and show HOLD then
    FAILSAFE over the real UART link. See `~/Desktop/CN/docs/OS_CN_SYNERGY.md`, `HYBRID_PLAN.md`,
    `HARDWARE.md`. So far only loopback / virtual serial tested: say so.
  Label these frames "CN/OS integration". Give them the same step layout (commands, PASS/FAIL) but
  keep WBR steps as the main detail. If a CN command cannot be verified from source, mark UNVERIFIED.

**Record in the lab, analyse at home.** Every sensor take is recorded as a ROS 2 bag
(`ros2 bag record` of the realsense topics with explicit topic list, storage format and output
folder), plus the native recorder where the sources use it. Include metadata capture (git hash,
config, `ros2 bag info`, sha256, throttling state before/after). Home analysis frames show the
offline commands (bag info, rate/timestamp checks, db3→EuRoC export, Kalibr, Allan, ORB-SLAM3
offline, trajectory evaluation) with what to look at.

**Every step** gets, consistently laid out (one step may span several frames):
1. Goal and why (one line).
2. Hardware setup / preconditions.
3. Copy-paste commands (exact, from the scripts that exist; mark any command you could not verify
   from source as `# UNVERIFIED`).
4. Expected output.
5. PASS / FAIL check with an explicit numeric or observable criterion and its evidence label
   (thresholds from the calibration plan are ASSUMED review thresholds, say so).
6. If FAIL: what to do (stop / retry once / defer to Session 2), bottom-up debugging order.
7. Files produced and where they go (USB/card path, naming).

Also include: a timeline slide per session, a packing checklist, a stop-rules slide (when to stop
and not tune SLAM to hide a sensor problem), a Session-1→Session-2 handoff checklist, and a printable
one-page checklist per session in backup.

## Quality loop (required before stopping)

1. Build; fix all errors. `rg -n '^!|Overfull|Missing character|undefined' main.log` must print
   nothing (Underfull hbox may remain only if invisible).
2. Render pages to PNG with
   `swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview`
   and look at every page for overflow into the footer, overlapping text, clipped code.
3. Check every command in the lab plan against the script it calls (name, flags, paths).
4. Write `slides_study/REVIEW_LOG.md`: page count, checks run, known gaps, UNVERIFIED commands.

Stop only after the loop passes. Final message: page count, PDF path, open gaps.

## Images (owner rule, added 2026-10-18)

Do not generate or download images. Reuse `base/images/` where they fit; otherwise draw with TikZ.
If a new raster illustration would genuinely help, place it with `\slideimg{...}{<ID>}{<caption>}`
(it renders a labelled placeholder box until the file exists) and write a ready-to-paste image prompt
for it in `slides_study/image-prompts/IMAGE_PROMPTS.md`, same format as `base/image-prompts/`
(ID, target file name `images/<ID>.png`, aspect ratio, slide/page, full prompt text, what must be
technically correct). The owner generates the images and drops them into `images/`.
