# TerrainAdvisory firmware proposal

**Audience:** WBR STM32H7 firmware owner

**Status:** Request for interface and integration review. Candidate software
protocol only; no H7 firmware integration or actuation authorization is implied.

## Purpose and safety boundary

Add a receive-only `TerrainAdvisory` input from the Raspberry Pi. The current Pi output describes a possible obstacle;
it is not a command, clearance check, jump permission, or safety-rated measurement. The STM32 remains sole owner of
balance, jump execution, state transitions, actuator limits, and all safety decisions. A lost, invalid, stale, or
uncertain input must never create motion.

The format below comes from `tools/obstacle_decision/ADVISORY_SPEC.md` and
`tools/link_proto/SPEC.md`. Both identify the interface as proposed and require
firmware-owner review before use. Numeric wire constants and design limits below are ASSUMED/proposed unless explicitly
tagged; run observations are MEASURED, and derived arithmetic is CALCULATED.

## Pi message and link

The Pi sends link-protocol version 1, type 4 (`TerrainAdvisory`), using the candidate framing in
`tools/link_proto/SPEC.md`:

`COBS(header || payload || CRC-32C) || 00`

Header fields are version u8, type u8, payload length u16, session u64, and packet sequence u32; multibyte values and
payload floats are little-endian. The CRC-32C covers the decoded header and payload. Do not serialize a C struct
directly; decode explicit offsets. The candidate Pi↔MCU link is UART **460800 baud, 8N1** (ASSUMED interface setting in
the bench firmware/spec; actual H7 clock and baud accuracy must be confirmed on its board).

| Payload offset | Encoding | Field and units |
|---:|---|---|
| 0 | u64 | Pi monotonic timestamp, ns |
| 8 | u64 | Source camera frame stamp, ns |
| 16 | u8 | Advisory: 0 `NONE`, 1 `JUMP_CANDIDATE`, 2 `STOP_CANDIDATE`, 3 `UNCERTAIN` |
| 17 | u8 | `plane_valid`, boolean 0/1 |
| 18 | f32 | Confidence, unit interval |
| 22 | f32 | Obstacle front-face distance, m |
| 26 | f32 | Obstacle height, m |
| 30 | f32 | Obstacle lateral width, m |
| 34 | f32 | Fitted plane pitch, rad |
| 38 | f32 | Camera height above plane, m |

Payload length is **42 B (ASSUMED/proposed layout)**. Header plus payload plus CRC is **62 B decoded (CALCULATED)**; the
bench documents up to **64 B on wire including COBS and delimiter (CALCULATED)**. At **15 Hz (MEASURED in the 2026-10-24
synthetic run: 900 records / 60 s)**, that maximum record occupies about **9.6 kbit/s (CALCULATED, 64 B × 10 UART bits ×
15/s)** in the Pi→MCU direction. Type 5 (`AdvisoryEcho`) is an optional MCU→Pi diagnostic response, not a required
controller input; its candidate payload is **27 B (ASSUMED / proposed layout)**.

## Evidence and limits

### Obstacle estimate and bag evaluation

`tools/obstacle_decision/results/lab-20261024/README.md` summarizes tabletop RGB-D bags re-evaluated with the
then-current detector. On **six box runs (MEASURED)** with heights ≤13 cm, median height error was **−0.2 to +0.4 cm
(MEASURED)**, distance error **−1.6 to +0.3 cm (MEASURED)**, and width error **−1.3 to +1.7 cm (MEASURED)**. The
`tools/obstacle_decision/results/lab-20261024/evaluation.md` has **7/8 box runs PASS (CALCULATED from rows and criteria)**; touching books at B-H05-D1p3 merged
and produced a conservative STOP (FAIL against the isolated-box reference). W1 passed at **1.006 m versus 1.000 m tape
(MEASURED)**; W2 failed at **1.424 m versus 1.500 m (MEASURED)**. A 2.45 cm book was classified `UNCERTAIN` at 2.6 cm
estimated height (MEASURED), correcting an earlier jump candidate. Thresholds and evaluation cases were chosen using
these runs; this is not held-out validation or a clearance claim.

### Timing, UART, faults, and replay

`tools/link_bench/results/20261024-nucleo/README.md` records the first real Pi 5↔Nucleo-F446RE UART run. The
50 Hz health phase delivered **3000/3000 replies (MEASURED; zero observed loss)** with **4.07/4.08 ms RTT P50/P99
(MEASURED)**; CRC, duplicate-sequence, and wrong-session faults each rejected **10/10 (MEASURED)**. The advisory **15 Hz
(MEASURED)** synthetic run delivered **900/900 echoes (MEASURED; zero observed loss)** with **2.81/2.82 ms RTT P50/P99
(MEASURED)**; WIRE, SEQUENCE, SESSION, and FIELDS faults were rejected. B-H08 replay delivered **139/139 echoes
(MEASURED; zero observed loss)**, with detector-plus-decision **78/83 ms P50/P95 (MEASURED)** and RTT **2.82/4.24 ms
P50/P99 (MEASURED)**. Times use Pi `CLOCK_MONOTONIC`; they exclude camera-to-Pi latency and provide no cross-clock
transit bound.

The bench **150 ms silence rule (ASSUMED/proposed)** declares `NO_LINK`: 100 ms gaps held link in **5/5 trials
(MEASURED)**; 300 ms gaps declared `NO_LINK` **5/5 (MEASURED)** at **150.0–150.003 ms MCU silence and 153.903–153.910 ms
Pi detection (MEASURED)**. Advisory data separately becomes stale after **300 ms without an accepted record
(ASSUMED/proposed)**; the synthetic fault run observed stale during **400 ms silence (MEASURED)** and clear on recovery.
The two timers serve different purposes and need owner approval.

The Pi detector-only timing in the lab README was **67/76 ms P50/P95 (MEASURED)** on a non-throttled Pi 5 after
optimization, versus **118/126 ms (MEASURED)** before it. This is slower than a 15 Hz frame period on much of the
distribution; the live chain's drop/age behavior must be measured before any freshness guarantee.
`ops/worklog/sessions/2026-10-25-live-advisory-summary.md` predates these physical tests and records no live Pi/ROS/bag run at that time. Saved-bag evidence is not live-camera evidence.

### Live LED tests 25 Oct

Cardboard rig; D435(i) 29 cm above the table, with tilt estimated at 12–13° by inclinometer and 13–14° by plane fit/ORB path. Pi 5→Nucleo-F446RE GPIO UART at 460800 baud (USB-powered). LED firmware: green `NONE`, yellow `JUMP`, red `STOP`, D9 plus yellow blink `UNCERTAIN`, red 2 Hz blink when stale. Advisory range limit: 1.3 m for whole clusters. Live detector was about 100 ms/frame; advisories about 8 Hz. Each run lasted 60 s.

| Run | Measured result |
|---|---|
| LED self-test | All four states and stale blink seen; 9,420 echoes. |
| Empty table (lamp removed) | `NONE` 553/553 frames; echoed 553/553. |
| Books, 4.6 cm at 1.00 m | `JUMP` 561/563 (two `UNCERTAIN` while confirming); estimated height 4.75 cm, distance 0.998 m; echoed 563/563; RTT P50 2.8 ms. |
| Box, 13.1 cm at 1.00 m; removed at ~42 s | `STOP` until 42.6 s, then `NONE`; estimated height 13.4 cm, distance 0.993 m; echoed 603/603. |
| Approach, box initially at 1.6 m | Detection at 1.3 m limit; tape 1.285–1.31 m, detector 1.27–1.30 m. Live LED flickered at range edge; run 1 also flickered at the 12 cm height threshold. |
| ORB-SLAM3 stereo map along table | Forward leg 2.009 m against 2.00 m tape; one map, no pose jumps. Return leg not completed within the 45 s recording. |

- Every listed per-run advisory was echoed; no UART loss was observed in these counts. Stale indication was exercised in self-test.
- Replaying recordings within each 60 s window with 0.10 m range and 0.01 m height hysteresis reduced transitions 156→2 (run 2) and 218→25 (run 3). These are replay results, not observed live LED behavior. Evidence: `ops/worklog/reviews/2026-10-25-flicker-report-window.md` (on branch `claude2/20261025-lab-fixes`).
- Remaining run-3 changes came from a ~2–3 cm object (likely a power cable) at 1.1–1.2 m toggling `UNCERTAIN`/`NONE`, and nearest-object switching between a ~9 cm object at ~1.2 m and the box.
- These are bench observations on the cardboard setup, not general performance or a safety-rated clearance. Return leg was not captured. Raw recordings: `~/wbr-evidence-archive/lab-day-20261025/` on the Mac (120 files, SHA-256 verified against the Pi).

## Proposed receive-side behavior

1. Keep reception passive and outside actuator paths. Validate bounded UART framing, exact version/type/length, COBS,
   and CRC-32C before parsing.
2. Accept only a locally provisioned Pi session; received session IDs cannot bind/switch the receiver. Require a newer
   per-session sequence under an owner-reviewed wrap rule. Rejected, duplicate, or old packets do not refresh freshness.
3. Validate enum, `plane_valid` 0/1, six finite floats, confidence [0,1], and owner-approved geometry bounds. Bounds are
   not fully defined yet. Reject invalid data and retain reasons/counters.
4. After **300 ms (ASSUMED/proposed)** with no accepted record, expose stale/`UNCERTAIN` and no usable obstacle. For
   motion eligibility this behaves as `NONE`; it cannot request stop, jump, or actuation. Keep stale distinct in
   diagnostics so it differs from fresh `NONE`. Owner to confirm this semantic.
5. A future FSM may use fresh `JUMP_CANDIDATE` only as a hint gating a jump mode the firmware already owns, subject to
   local state, contact, balance, clearance, operator, and safety checks. It cannot create a mode, bypass vetoes,
   command torque, or override safety. Initial integration exposes telemetry only.

### Resource reference

`tools/link_bench/LED_REPORT.md` reports the complete F446 bench image after
LED support: **7,568 B text, 0 B data, 5,120 B BSS, 12,688 B text+data+BSS (MEASURED on the F446 target build)**; binary
image **7,572 B (MEASURED)**. This includes the bench application, protocol, and LED support; it is not an isolated
TerrainAdvisory cost, and it is not an STM32H7 estimate. H7 compiler, linker map, stack/queue allocation, DMA/ISR
design, and integration effects must be measured in the target firmware build. Do not budget H7 RAM from the F446 BSS
number.

## Decisions requested from firmware owner

- Ratify or replace the type 4/5 fields, widths, byte order, float encoding, session binding, and per-type sequence
  policy.
- Confirm units and frames for distance, width, camera height, and pitch; define accepted bounds and whether zero
  geometry is legal with each advisory.
- Confirm **15 Hz (MEASURED current sender rate)** as the desired rate and whether latest-sample overwrite or a bounded
  queue is appropriate.
- Choose the advisory stale timeout; the current **300 ms (ASSUMED/proposed)** differs from the bench `NO_LINK` silence
  rule of **150 ms (ASSUMED/proposed)**.
- Treat **0.10 m range hysteresis and 0.01 m height hysteresis as proposals** pending owner selection. Obstacles within about **1 cm of the 12 cm height threshold** are inherently ambiguous at the observed measurement variation.
- Define whether `UNCERTAIN` means “not yet temporally confirmed” (as used for the small book) or “measurement
  below/near a decision band.” Decide how consumer logic distinguishes stale/no-feed from a fresh `NONE`.
- Review the tracking-state enum in `tools/perception_health/SPEC.md`: it lists `SYSTEM_NOT_READY=0`, `NO_IMAGES_YET=1`,
  `NOT_INITIALIZED=2`, `OK=3`, `RECENTLY_LOST=4`, `LOST=5`, `OK_KLT=6` (ASSUMED enum values). It appears offset by one
  from the expected ORB-SLAM3 values, with `SYSTEM_NOT_READY` remapped from −1 to 0. Verify against the pinned source
  before use. TerrainAdvisory has no tracking state; do not import this enum implicitly.
- Clock mapping is **not implemented/qualified (UNKNOWN)**. Pi monotonic time, camera source stamp, and MCU timer must
  not be subtracted across domains. Decide whether to leave timestamps diagnostic-only or define a qualified mapping/age
  contract before relying on data age beyond MCU receipt silence.

## Suggested H7 integration and bench plan

1. Owner freezes a versioned interface. Add a bounded parser/state outside the balance loop; define DMA/ISR handoff,
   queue depth, overflow behavior, and telemetry.
2. Build on H7 with warnings; measure flash, RAM, stack, queue, and cycle-cost deltas against baseline. Check receiver
   work cannot block balance/safety scheduling; leave FSM/actuator code unchanged.
3. Reuse `tools/link_bench` sender/fault workflow, adapted to H7 diagnostics. Confirm board pins/baud and 3.3 V logic
   first; run fresh 15 Hz messages and saved B-H08 replay.
4. Inject bad CRC/COBS, wrong version/type/length/session, duplicate/old/wrapped sequence, invalid fields, NaN/Inf,
   overflow, UART errors, and reset/rebind. Confirm rejects do not refresh freshness. Pause for **100/150/300/400 ms
   (ASSUMED test points)**, record MCU-local loss/stale times, then check recovery; these are not limits.
5. Keep motors disabled and robot supported. Verify telemetry only and no FSM/actuator change for any advisory,
   including `JUMP_CANDIDATE`. A future FSM test needs separate owner review and controlled test plan.

Evidence paths are cited inline above; raw advisory summaries are under
`tools/link_bench/results/20261024-nucleo/`.
