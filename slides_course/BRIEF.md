# Brief: WBR perception implementation deck

You are the builder for a new LaTeX Beamer (XeLaTeX) deck in the WBR repository
`~/Desktop/Research/wbr-perception-phase1-runtime`. Work only inside `slides_course/`.
Do NOT edit anything else in this repo, `third_party/`, or any file in the OS repo
`~/Desktop/OS/OS-project/heterogeneous-edge-ai-os` (read-only reference). Do NOT run any git
command that changes the index, branches, stash or commits. The working tree has unrelated
uncommitted changes; leave them alone.

## Goal and audience
1. Primary reader: the project owner (4th-year electronics/telecom student, strong embedded,
   STM32, C/C++, Linux). The deck exists so they understand the WBR perception system well
   enough to make correct engineering decisions and direct AI coding agents without losing
   direction. Explain the WHOLE implementation path in as much detail as needed.
2. Secondary readers: their lecturer and a senior (progress report).
3. Language: 100% English, including TikZ labels and captions. Spell out each abbreviation
   on first use.
4. Length: long is fine. Target roughly 70–90 pages.

## Subject
How to implement WBR (wheel-biped robot) Phase-1 perception: Intel RealSense D435i +
ROS 2 Jazzy + ORB-SLAM3 stereo-inertial on a Raspberry Pi 5 (8 GB, Ubuntu, NVMe), then the
integration boundary into the robot, where an STM32H7 owns hard-real-time balance, LQR, VMC,
FSM and motor safety. If ROS, SLAM or the Pi fails, the robot must not lose balance.

Required depth on:
- system architecture and Pi-vs-STM32 ownership boundary (and why);
- data path from sensor to pose: USB3 → librealsense → realsense-ros → topics/QoS → rosbag →
  ORB-SLAM3 → trajectory → evaluation; process/thread structure, queues, bandwidth;
- frames (world, map, odom, base_link, body, imu_body, camera, camera_optical, imu_camera,
  left/right camera) and the TF tree; camera IMU (D435i) vs body IMU (STM32) separation;
- timestamps and clock domains (sensor capture, hardware/device, driver, ROS header, publish,
  receipt, processing start/end, output); global-time options; never subtract across domains
  without a defined relationship;
- calibration: stereo intrinsics/extrinsics, camera–IMU extrinsics and time offset, IMU noise
  (Allan variance), tools (e.g. Kalibr / imu_utils) as PLANNED choices with trade-offs;
- ORB-SLAM3 internals at the level needed to operate it (tracking, local mapping, loop
  closing, Atlas, IMU initialization, settings YAML fields);
- the gate ladder N0–N7 (Pi platform; D435i on USB3 5000M; raw IR1/gyro/accel qualification
  incl. 300-s soak; ROS 2 pipeline + rosbag record/replay; ORB-SLAM3 on EuRoC; offline D435i
  stereo-inertial; live stereo-inertial; profiling/evaluation; perception-health interface;
  STM32 integration boundary), each with entry conditions, explicit PASS criteria, evidence
  artifacts, and typical failure modes;
- failure modes and bottom-up debugging order (hardware → USB → raw sensor → clocks →
  driver → ROS → QoS → calibration → ORB-SLAM3 → trajectory → evaluation);
- evaluation plan: ATE, RPE (definitions, alignment, evo), initialization success,
  tracking loss/relocalization, P50/P95/P99 latency with defined timestamps, dropped frames,
  queue depth, CPU/freq/temp/memory/throttling; result slides as empty axes marked
  "To be filled after N4/N5 runs";
- perception-health interface and the Pi→STM32 boundary (what crosses, rate, staleness,
  what the STM32 does when perception is absent/stale/invalid); PLANNED, not designed in code;
- decision points with trade-offs (e.g. native vs Docker, USB topology, ROS vs non-ROS
  ORB-SLAM3 path, resolution/FPS, emitter on/off, global time, calibration tool, when to add
  wheel odometry), each with a recommended default and what evidence would change it;
- how to direct AI agents per gate (bounded tickets, evidence required, what not to delegate).

## Sources of truth (read; do not invent)
`AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/*.md` (especially PROJECT_STATE, NEXT_GATE,
RPI5_NATIVE_PERCEPTION_BRINGUP, D435I_BASELINE_AUDIT, ARCHITECTURE, DECISIONS,
EVIDENCE_INDEX, D435I_VIO_CALIBRATION_READINESS, ORB_SLAM3_OFFLINE_PREPARATION,
PI5_NATIVE_SENSOR_VALIDATION_2026-09-12), `experiments/*` summaries, `config/`, `scripts/`,
`git log`. Read deleted-in-worktree files with `git show HEAD:<path>`. Upstream ORB-SLAM3
source is in `third_party/ORB_SLAM3` (read only). For external facts (D435i specs, ORB-SLAM3
paper, EuRoC, ROS 2 QoS, evo) cite primary sources you can verify; if you cannot verify,
say so rather than inventing a number or citation.

Current state (owner-confirmed, overrides older optimistic wording): NO gate has PASSED on the
Pi. Hardware evidence so far: a NO-GO x86 VM/Docker audit over USB2, and historical Pi-native
sessions (2026-09-12/13) that saw 5000M once, then regressed to 480M; a 105-s capture did not
complete N2. The owner is restarting fresh from N0. Label every unmeasured item PLANNED;
historical evidence HISTORICAL; use KNOWN / MEASURED (with source) / PLANNED / UNKNOWN labels.
No invented measurements.

## Style and method (copy from the OS deck)
Use exactly the same preamble, theme (moloch), palette, fonts, figure macros, evidence badges,
density and flow as the OS deck: `~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides_course/main.tex`
(copy its preamble; reuse its `build_deck.py` approach if useful) and its README/REVIEW_LOG.
Follow the skill: `git -C ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os show
HEAD:prompts/academic-beamer-deck/SKILL.md` and its template files, plus `slides/SLIDE_PLAYBOOK.md`,
`slides/LAYOUT_BRIEF.md`, `slides/REVIEWER_BRIEF.md` in the OS repo. Paper-style flow:
motivation → problem → objectives → background → system design (very detailed) →
implementation by gate → evaluation method → decisions → current status → roadmap →
conclusion → references.

Exact diagrams (architecture, data path, TF tree, clock domains, timelines, gate ladder,
state machines, queues, boundary interface) are TikZ. AI images only where they genuinely help.

## Images (ChatGPT filenames)
New illustrations get ids P01, P02, ... (about 10–14). The owner generates them in ChatGPT
in P-id order, one per message, and drops the downloaded files into `slides_course/images/`
WITHOUT renaming (ChatGPT names like `ChatGPT Image Oct 10, 2026, 03_12_45 PM.png`).
Provide `slides_course/images/assign.py` that maps unassigned ChatGPT-named images, sorted by
the timestamp in their filename (fallback: mtime), to the next missing P-ids in order and
copies them to `Pxx.png`, printing the mapping. Frames must compile with a visible named
placeholder when `Pxx` is absent.

## Phases
PHASE 1 (stop after this): write `slides_course/image-prompts/BATCH.md` (STYLE GUIDE +
HARDWARE REFERENCE block for Raspberry Pi 5 with active cooler, Intel RealSense D435i, a
generic STM32H7 board, a wheel-biped robot silhouette; then one fenced prompt per P-id with
aspect ratio, unique subject, must-show, must-not-show, allowed labels; plus a P-id → page →
subject table) and `slides_course/image-prompts/OUTLINE.md` (numbered page outline with each
page's message and source). Also write `slides_course/SCHEDULE.md`: 5–8 lines, the build
steps in order. Then stop.

PHASE 2: write `main.tex`, build with `cd slides_course && latexmk -xelatex
-interaction=nonstopmode main.tex`, render with `swift -module-cache-path qa/swift-cache
~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview`, inspect
EVERY page image at full size, and fix overflow, overlaps, tiny text, empty space, broken
TikZ, unlabeled claims, non-English text, inconsistent terms. Repeat until the skill QA
checklist passes. Write `REVIEW_LOG.md` (rounds, issues, fixes, the word "FINAL" when done,
pages with placeholders) and `README.md` (build, image drop-in, sources).

## PHASE 3: depth revision (owner feedback pending; reviewer critique)
The v1 deck (saved as qa/main-v1.pdf) is clean but too thin for its primary purpose. Nearly
every page is the same template: 4 short bullets + a 4-box linear flowchart + a filler sentence
"Figure N explains the X". The owner needs to understand the system, not a slogan per page.
Revise main.tex (or build_deck.py) so that:
- The "Figure N explains ..." filler sentences are removed everywhere; reference figures inside
  meaningful sentences or captions instead.
- Each gate N0–N7 gets at least two pages: (a) purpose, entry conditions, exact commands/tools,
  artifacts produced; (b) a PASS/FAIL criteria table with the threshold, how it is measured,
  which clock/timestamp it uses, and the evidence file — plus typical failure modes and what
  each symptom points to in the bottom-up order. Use repo thresholds; never invent.
- Diagrams carry real information: data-path diagram shows processes, threads, queues, topic
  names, message types, rates and QoS; clock-domain diagram shows each timestamp field and
  where it is stamped; TF tree shows which node/owner publishes each edge and static vs
  dynamic; gate ladder shows dependencies (N4A depends only on N0, N4B on N3+calibration, etc.)
  and current status per gate; the Pi/STM32 boundary shows the health message fields, rates,
  staleness rule and STM32 fallback behaviour (PLANNED).
- Use tables, two-column layouts, annotated timelines and small worked examples (e.g. a
  latency decomposition with symbolic terms, an ATE computation outline) where they teach more
  than bullets. Mix layouts; avoid identical pages.
- Keep the same style, labels (PLANNED/HISTORICAL/UNKNOWN), no invented numbers. Page count
  may grow to ~100–110. Rebuild, render, inspect every page, log as round "PHASE 3" in
  REVIEW_LOG.md ending with "PHASE 3 FINAL".

## PHASE 4: image assignment and small fixes
The owner generated the 12 images; filenames are messy (UUIDs plus two descriptive names), so
timestamp order is NOT reliable. Copies are in `slides_course/images/incoming/`.
1. Open and look at every image in `images/incoming/`. Match each one to its P-id by visual
   content against `image-prompts/BATCH.md` (subject, must-show). Copy (do not move) each
   to `images/Pxx.png`. If an image matches no prompt, or two match one slot, or an image
   shows a hardware error (wrong board colour/shape, invented text, fake measurements),
   leave the slot assigned anyway with the best match and record the defect.
2. Write `images/MAPPING.md`: table P-id | original filename | subject seen | defects.
3. Fix page 20 (3.4 Sensor-to-pose execution path): the "kernel / SDK" and "ROS topics"
   labels float detached above the diagram; attach them to the boxes/lanes they describe.
4. Rebuild, render, inspect every page with an image at full size (crop, aspect ratio,
   overlap with text), fix layout. Log as "PHASE 4" in REVIEW_LOG.md ending "PHASE 4 FINAL".

## PHASE 5: 2026-10-13 progress section (owner request)
The owner did not understand two results from 2026-10-13 and wants them explained IN THE DECK:
(1) "EuRoC test: ATE about 4 cm vs paper 3.6 cm, so ORB-SLAM3 works on the Pi" and
(2) "D435i programs built (SLAM program + recorder)". Teach these so a reader with no SLAM
evaluation background understands what was done, what it proves and what it does not.

FIRST understand the existing deck: read main.tex / build_deck.py / phase3_depth.py and
REVIEW_LOG.md, and the current gate pages for N4A/N4B/N4C and results pages (~96–98, empty
axes). Integrate; do not duplicate or contradict existing pages. Update any page whose status
text is now stale (e.g. "no gate has passed" stays true, but N4A now has MEASURED evidence;
the platform is temporarily a Pi 5 4 GB on microSD; a NEW D435i unit replaced the old one).

Sources (only these plus existing deck sources; cite evidence paths on slides or in notes):
`experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md` (authoritative summary),
`experiments/2026-10-13-n4a-euroc-mh01/REPORT.md`, `experiments/2026-10-13-orbslam3-pi-build/`,
`experiments/2026-10-13-n4b-d435i-prep/`, `experiments/2026-10-13-pi5-env-snapshot/`.
The paper value (~0.036 m, Campos et al., T-RO 2021, stereo-inertial MH01) is "quoted from
memory" in the facts file: verify against the paper if you can access it; otherwise label it
"SOURCE-SUPPORTED, table not re-verified".

Add a section "2026-10-13 progress" (~10–14 pages), mixed layouts, TikZ diagrams:
1. What changed today (platform 4 GB/microSD stand-in, new camera serials, ORB-SLAM3 native
   build + 3 patches and why each was needed, under-voltage 49 % of samples).
2. What EuRoC MH01 is; what ground truth is and how it was obtained (TikZ: drone + tracker →
   ground-truth trajectory; ORB-SLAM3 → estimated trajectory).
3. What ATE is: SE(3) alignment (no scale for stereo-inertial), RMS of position residuals;
   TikZ showing two trajectories before/after alignment with residual vectors; the formula;
   how evo computes it (`evo_ape tum ... -a`). Contrast with RPE briefly.
4. Results table: 3 runs 0.0415 / 0.0368 / 0.0416 m, mean 0.040 m, vs paper; maps, resets,
   IMU init, peak RAM. Why run-to-run variation exists (multithreading nondeterminism).
   Fill the existing results pages (~96–98) with these N4A numbers where they fit; keep
   any axis that still has no data empty and marked.
5. What N4A proves (algorithm + ARM64 build + patches reproduce published accuracy on known
   data: isolates ORB-SLAM3 from camera/calibration/timing) and what it does NOT prove (D435i,
   calibration, timestamps, real-time speed; timing invalid under throttling: 282–301 s wall
   for 184 s data). N4A status: MEASURED evidence, gate still OPEN pending stable power rerun
   unless the deck's own N4A criteria say otherwise — decide from the deck's criteria and say why.
6. The two D435i programs: d435i_record (what streams, why emitter OFF, camera timestamps,
   .db3 + timestamps.csv, 18.4 MB/s budget) and the patched stereo_inertial_realsense_D435i
   (--bag offline = N4B, live = N4C, --no-viewer; what the patch fixes in IMU handling).
   TikZ data path: D435i → librealsense → recorder .db3 → playback → IMU preintegration +
   stereo ORB → tracking/local mapping/loop closing → trajectory → evo. Why offline first.
7. Config/calibration status: intrinsics, baseline, camera–IMU extrinsics NOMINAL (factory),
   IMU noise ASSUMED (needs Allan variance). Status: built, never run on the camera.
8. Next physical step: the hand-motion recipe and what log lines indicate success/failure.
9. Power and storage status (32 GB card no margin vs 128 GB plan; 5.1 V/5 A supply ordered).
Rebuild, render, inspect every new/changed page at full size, fix layout. Log as "PHASE 5"
in REVIEW_LOG.md ending with "PHASE 5 FINAL". Do not touch anything outside slides_course/.

## PHASE 6: curate the reference deck (owner allowed restructuring; they have not read it yet)
Run only after `slides_report/` and `slides_progress/` are FINAL. This deck is now deck C, the
deep learning reference behind the advisor report (A, `slides_report/`) and the progress deck
(B, `slides_progress/`). Read A and B first.
1. Audit all 109 pages: list each page as KEEP / MERGE / CUT / UPDATE with a reason in
   `qa/PHASE6_AUDIT.md`. Cut pages that repeat each other, carry little information, or
   duplicate what B now explains better; merge thin neighbouring pages; keep every gate PASS
   table, exact diagram and source-backed fact. Target is whatever the content needs (likely
   70–90 pages), not a number.
2. Update stale status with 2026-10-13 facts (`experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md`):
   new D435i unit and serials, 4 GB Pi on microSD stand-in, N4A EuRoC measured evidence (gate
   status per the deck's own criteria), D435i programs built not run. Fill the empty results
   pages with N4A numbers where they fit. Keep a short "Changes since 2026-10-10" page.
3. Save the pre-phase-6 deck as `qa/main-v3-109p.tex` first. Rebuild, render, inspect every
   page at full size, fix. Then update `slides_progress/` page references to C so they match the
   new page numbers (only that edit in slides_progress/; rebuild it). Log "PHASE 6 FINAL".

## PHASE 7: fill N4A RPE (CALCULATED) in decks C and B
New source: `slides_course/qa/n4a-traj-eval-summary.md`, output of `tools/trajectory_eval/traj_eval.py`
from branch claude/project-thread-upkfjv (commit d3f9540, PR #2), run on the three MH01 runs with
`--t-max-diff 0.02 --t-offset 0 --align-both --rotation-ate --rpe-delta 1 --rpe-unit s`
(RPE pairs: first later pose whose reference timestamp is >= 1 s later; no interpolation;
3,639 matched pairs). Its SE(3) ATE reproduces evo exactly. Label these CALCULATED (tool not
yet merged; tool's own validation passed per its README).
1. Deck C page 80 "5.8 Accuracy results": replace the empty RPE axis with the per-run SE(3)
   RPE translation RMSE (0.013295 / 0.013559 / 0.014021 m) and rotation RMSE (0.076464 /
   0.076776 / 0.074883 deg) at 1 s, and add a compact note of Sim(3) ATE (0.018874 / 0.023794 /
   0.022288 m) explaining that Sim(3) also fits scale, so it is not the stereo-inertial metric
   compared to the paper. Keep "D435i accuracy UNKNOWN". Fix any other C page that says N4A RPE
   is UNKNOWN or unmeasured.
2. Deck B (`slides_progress/`, you may edit it for this only): pages that say "No RPE result was
   measured today" or similar → state the CALCULATED values and how they were computed; add one
   sentence on what RPE 1.3 cm per 1 s means (local drift) versus ATE (global). Keep page count
   unless a page overflows.
3. Rebuild and render both decks, inspect changed pages at full size. Log "PHASE 7 FINAL" in
   slides_course/REVIEW_LOG.md.

## PHASE 8: apply the 2026-10-14 audit and facts
Inputs: `experiments/2026-10-14-deck-audit/AUDIT.md` (frame-by-frame KEEP/BACKUP/CUT, factual
corrections, missing explanations) and `experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md`.
1. Save `qa/main-v4-91p.tex` first.
2. Apply every factual correction (8 GB Pi in use, ORB-SLAM3 + 4 patches, microSD stall → record
   into RAM, 64 GB USB unusable, power still unstable, offline crash + patch 4 rebuild pending).
3. Apply the audit's KEEP/BACKUP/CUT: move BACKUP frames to an appendix after the references;
   cut CUT frames. Add the missing explanations it lists where they fit.
4. Remove visible source footers/evidence-path columns from content pages (keep them in \note{});
   keep the references page.
5. Update `slides_progress/` page references to this deck only if they break (optional), and
   do not touch other folders. Rebuild, render, inspect every page, log "PHASE 8 FINAL".
