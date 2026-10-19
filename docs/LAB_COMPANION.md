# WBR lab companion

## 0. Read this before opening a terminal

Build reviewable **N0 → N3 evidence** with the merged `lab/` tools. N3 is the active gate; **no gate is PASS; N0–N3 remain OPEN**. MEASURED unresolved prerequisites are under-voltage on 5 V/3 A and the old card's 16.6 MB/s against 18.4 MB/s demand. The current camera's Software Development Kit (SDK) serial is **317422076650**, firmware 5.17.3.10. Old-unit **243322073847** evidence does not transfer. Sources: [PROJECT_STATE.md](PROJECT_STATE.md), [NEXT_GATE.md](NEXT_GATE.md).

This lab cannot establish calibration accuracy, estimator performance, exposure latency, controller safety or all-day reliability. The D435i inertial measurement unit (IMU), `imu_camera`, is separate from the STM32 body IMU. Every current tool has **Hardware run: NONE** in [GATE_TOOLING.md](GATE_TOOLING.md).

Four reading labels recur below: **understand** = why; **execute** = an action after prerequisites; **verify** = inspect evidence; **blocked-unknown** = stop until the named evidence/decision exists.

Command tags describe execution provenance:

- **[MAIN, UNTESTED ON HW]**: merged interface; physical behavior UNKNOWN.
- **[OFFLINE-VERIFIED: ran on fixtures]**: only the home rehearsal was executed, including the non-executing plan.
- **[BLOCKED: reason]**: documented command or missing procedure awaiting prerequisites.
- **[MANUAL REVIEW]**: operator interpretation/action, without an automatic acceptance claim.

Use evidence labels precisely: **MEASURED** observations, **CALCULATED** arithmetic, **SOURCE-SUPPORTED** documented requirements, **INFERRED** interpretation, **ASSUMED** explicit operating assumptions, **PROPOSED** local policy, **UNKNOWN** absent evidence.

Check exits: **0 PASS, 1 FAIL, 2 BLOCKED, 3 usage/internal error**. Precedence: **FAIL > BLOCKED > PASS**. Missing evidence cannot rescue an observed failure. A tool PASS is evidence for human review, **never a gate PASS**.

Historical note: `WBR_STUDY_GUIDE.md` Part II and `WBR_LAB_PLAN_v1.md` (project files, absent from this repo) describe September's `phase_gate.py`, `n1_precheck.py`, `n3_record.py`, `n3_bag.py` bundle. This companion uses `lab/`; the historical `accept-n2` human-receipt idea survives as explicit MANUAL REVIEW after each `result.json`.

## 1. Before the lab: decisions at home

### Five blockers

| Blocker | Decision needed | Recommended decision |
|---|---|---|
| **B1: profile conflict** | Bag policy expects infrared (IR) 15 Hz; raw defaults to 848×480 Y8/30; calibration uses 640×480/30. Audit severity: High. | Review separate named profiles. Make bag config match the actual launch; do not change rates merely to make checks pass. |
| **B2: missing launch** | No reviewed `lab/` ROS launch matches the bag contract. | BLOCKED until a command is written/reviewed and its effective parameter dump checked. The bring-up example remaps names and enables IR1 only; do not use it as-is. |
| **B3: storage** | Replacement 128 GB card is owner-reported available, qualification UNKNOWN. | Qualify the actual destination before recording; retain old measured limits until reviewed replacement evidence exists. |
| **B4: supply** | Owner reports a 27 W supply available; negotiation/stability UNKNOWN. `require_5a` is true. | Use and qualify the declared 5 A supply. A declared 5 V/3 A supply FAILs by design; do not waive the criterion. |
| **B5: authorization** | Physical capture requires explicit owner **CAMERA AVAILABLE**. | Obtain it before acquisition. The calibration wrapper additionally enforces `WBR_CAMERA_AVAILABLE`; setting it does not create permission. |

Sources: [raw thresholds](../lab/d435i_raw/thresholds.yaml), [bag config](../lab/rosbag_qual/config.json), [calibration criteria](../lab/calib_record/criteria.json), [power thresholds](../lab/power_usb/thresholds.yaml), [consistency audit](audits/2026-10-18-tool-consistency.md), [bring-up §6](RPI5_NATIVE_PERCEPTION_BRINGUP.md), [calibration instructions](../calibration/lab/README.md). Hardware availability is owner-reported, not MEASURED qualification; the canonical state still records the older order status.

**Understand B3 — CALCULATED decimal payload rates.** Y8 is one byte/pixel, stereo is two images:

- 848 × 480 × 2 × 30 = 24,422,400 B/s ≈ **24.4 MB/s**.
- 640 × 480 × 2 × 30 = 18,432,000 B/s ≈ **18.4 MB/s**.
- 848 × 480 × 2 × 15 = 12,211,200 B/s ≈ **12.2 MB/s**.

These exclude serialization, IMU and filesystem overhead. The bag config's `storage.max_write_rate_bps = 16.6e6` is a historical comparison ceiling, not a benchmark of today's destination. The [calibration plan, prerequisites/storage](D435I_CALIBRATION_PLAN.md) requires a sustained test larger than the largest take, lasting at least its duration, with ASSUMED margin ≥1.5 × 18.4 = **27.6 MB/s** for that full-rate plan. **[BLOCKED: no exact storage benchmark command in these sources]**: obtain a reviewed procedure; do not improvise a destructive disk test.

### Pack

**[MANUAL REVIEW]** Bring the Raspberry Pi 5 with cooling, current D435i, direct Universal Serial Bus 3 (USB3) data cable, suitable 5 A supply, 128 GB card and Mac with the full repository/evidence space. For optional calibration: the preferred A3 6-column × 4-row AprilGrid, or A4 fallback, matte print on a rigid flat board, calipers and tape for measurements. Sources: [bring-up arrival checklist](RPI5_NATIVE_PERCEPTION_BRINGUP.md), [state](PROJECT_STATE.md), [calibration lab](../calibration/lab/README.md), [plan](D435I_CALIBRATION_PLAN.md). The USB2 stick is not a recording destination: MEASURED 1.09 MB/s.

### Twenty-minute rehearsal: no hardware

Run from the repository root on the Mac. These exact commands were run offline on 2026-10-19. Outputs belong to fresh `/tmp` directories; use new names on every repeat. `/private/tmp` below is the Mac's resolved `/tmp` path.

**Minutes 0–5 — execute, plan only. [OFFLINE-VERIFIED: ran on fixtures]** Source: [lab/README.md](../lab/README.md), paths substituted.

```sh
python3 lab/run_lab_session.py --session-dir /tmp/wbr-session-plan --calib-take /tmp/none --plan
```

Real console excerpts, with intervening command lines omitted:

```text
Session directory: /private/tmp/wbr-session-plan
Commands are shown in execution order; ROS step prompts are operator actions.
```

```text
CONFIRM: Place the camera on a still, rigid surface for the full raw capture.
CONFIRM: Start the configured RealSense ROS camera node in ROS domain 42 and ensure it is streaming.
CONFIRM: Stop the live camera node before replay qualification.
```

Exit **0** means successful planning, not a check PASS. It prints commands without creating a session, opening devices or validating that `/tmp/none` exists. Never execute the Mac-resolved capture lines from that output.

**Minutes 5–10 — execute, historical power analysis. [OFFLINE-VERIFIED: ran on fixtures]** Source: [power README, evidence replay](../lab/power_usb/README.md), output path substituted.

```sh
python3 lab/power_usb/check_power_usb.py --analyze-only lab/power_usb/tests/fixtures/real-partial --out /tmp/lc-r1
```

Real console output, exit **2**:

```text
power_usb BLOCKED (idle; capture MEASURED partial historical excerpts, multiple sessions; NOT a combined qualification run)
criterion              status
raw_integrity          PASS
under_voltage          PASS
ext5v                  BLOCKED
temperature            BLOCKED
window_coverage        BLOCKED
supply                 BLOCKED
usb_link               BLOCKED
usb_topology           BLOCKED
kernel_log             BLOCKED
load_window            PASS
```

**Verify:** historical excerpts lack a complete common observation window. `under_voltage PASS` describes available evidence under this policy; it does not erase the project's measured power problem. `raw_integrity PASS` checks saved bytes, not authenticity.

**Minutes 10–15 — execute, old-unit analysis. [OFFLINE-VERIFIED: ran on fixtures]** Source: [raw README, saved evidence](../lab/d435i_raw/README.md), output path substituted.

```sh
python3 lab/d435i_raw/check.py --analyze-only lab/d435i_raw/tests/fixtures/old-unit-smoke --outdir /tmp/lc-r2
```

Real console output, exit **1**:

```text
CRITERION                        STATUS
identity.serial                  FAIL
identity.firmware                PASS
identity.usb_type                PASS
legacy.csv                       PASS
profiles                         FAIL
capture                          BLOCKED
rates                            BLOCKED
receipt_gaps                     BLOCKED
timestamps                       BLOCKED
stereo                           BLOCKED
emitter                          BLOCKED
static                           BLOCKED
ir_content                       BLOCKED
latency_policy                   PASS
d435i_raw: FAIL | /private/tmp/lc-r2/result.json
```

**Verify:** correct rejection: old serial and old profile fail today's contract. Missing domains, host-monotonic stamps and right IR block other checks. `latency_policy PASS` means unmapped latency was withheld; latency remains UNKNOWN.

**Minutes 15–20 — [MANUAL REVIEW].** Open both output directories in an editor. Follow each criterion's evidence path from `result.json`, compare raw logs with measured values and threshold sources, and explain FAIL versus BLOCKED aloud. Do not edit a result to change its status.

## 2. Terminal map

| Terminal | Ownership | ROS domain |
|---|---|---|
| Pi A: control | Individual checks or orchestrator; normal camera user; repository root | Record/live checks 42; replay tool creates observer/player in 43 |
| Pi B: camera | One reviewed foreground ROS camera node, only after native raw capture exits | 42; localhost-only, matching recorder |
| Mac | Offline review, evidence preservation; later calibration fitting | No ROS graph needed for offline analysis |

**Execute — [MAIN, UNTESTED ON HW].** Source: [lab/README.md](../lab/README.md). Source this in each Pi terminal that uses ROS 2 (Robot Operating System 2):

```sh
source /opt/ros/jazzy/setup.bash
```

**One camera owner at a time:** native SDK capture and the ROS node never overlap. Stop the ROS node before replay and before calibration capture. The orchestrator neither sources ROS nor starts the camera driver.

Its order is power → still raw → operator starts camera in 42 → record → operator stops camera → replay in 43 → check a **saved** calibration take. Power gates everything; raw gates ROS; failed recording gates replay. Saved-take checking is independent of record/replay once power passes. Do not use `--yes` or `--continue-on-fail` on the first hardware run. Prefer the separate cards below to preserve explicit review stops. Source: [lab/README.md](../lab/README.md), [orchestrator](../lab/run_lab_session.py).

## 3. Lab sequence: one card at a time

All paths below are source examples. Select a **new directory on the qualified evidence volume** before execution; substitutions require recording the actual path. Commands do not qualify their destinations. Do not prepopulate a failed run directory for another attempt.

### A. Power and USB

**Understand / why:** establish a bounded baseline before adding stream load. Software supply declarations and sampled voltage are useful evidence, not complete electrical measurements.

**Execute — [MAIN, UNTESTED ON HW].** Source: [power README](../lab/power_usb/README.md).

```sh
python3 lab/power_usb/check_power_usb.py \
  --out lab/power_usb/runs/idle-20261018 --duration 60
```

**Verify / expect:** all IDs must pass: `raw_integrity`, `under_voltage`, `ext5v`, `temperature`, `window_coverage`, `supply`, `usb_link`, `usb_topology`, `kernel_log`, `load_window`. Defaults require declared ≥5000 mA, matched camera speed ≥5000 Mbit/s, sampled EXT5V ≥4.75 V (PROPOSED) and temperature <80 °C. New under-voltage/current bit 0 or a newly set historical bit 16 fails; baseline history remains visible.

**[MANUAL REVIEW]** Open `result.json`, raw voltage/throttle reads, before/after **`lsusb -t` output**, matched sysfs camera speed and kernel suffix/matches. A 5000M root hub alone proves nothing about the camera branch. Approve only the observed idle window.

**If it fails:** resolve supply/cooling first, then cable/port/topology; inaccessible readings mean BLOCKED, not healthy. **[BLOCKED: reviewed streaming-load command absent]**: obtain a bounded load/monitoring procedure before claiming power coverage during raw/ROS acquisition. This idle check cannot provide it.

**Keep:** whole directory: `capture.json`, `raw/`, `thresholds.yaml`, `analysis.json`, `kernel-window.log`, `kernel-matches.json`, `result.json`.

### B. Raw IR + camera IMU

**Understand / why:** isolate camera/SDK delivery before ROS discovery, driver parameters or storage complicate diagnosis. This stores sample images and timing rows, not a full-rate image bag.

**Execute — [MAIN, UNTESTED ON HW].** Only after B5 and prerequisite review; no ROS owner; camera still on rigid support. Source: [raw README](../lab/d435i_raw/README.md).

```sh
python3 lab/d435i_raw/check.py --capture --static \
  --outdir /home/richard/wbr-evidence/d435i-raw-20261018-01
```

**Verify / expect:** `capture`, `identity.serial/firmware/usb_type`, `profiles`, `emitter`, `duration`, `csv`, `sample_accounting`, `stereo`, `gyro.static`, `accel.static`, `ir_left.ir_content`, `ir_right.ir_content` and each stream's `samples/rate/receipt_gap/drops/timestamps`. Require the current identity, actual stereo Y8 848×480/30, emitter OFF, gyro/200, accel/100 (native 200 fallback only if offered), orderly 60 s window, full accounting and no discontinuities. Default rate tolerance is PROPOSED ±5%; receipt gaps include boundaries: IR ≤0.1 s, motion ≤0.05 s. Stereo pairs use equal frame numbers/common domains, ≤0.01 ms skew, no unpaired frames.

**[MANUAL REVIEW]** Open `result.json`, `capture.json`, SDK/stdout/stderr logs and **every retained Portable Graymap (PGM) image** from both sides. Look for plausible scene structure, saturation or corruption; pixel statistics alone cannot prove good optics. Confirm the static claim and cleanup/emitter restoration. `latency_policy PASS` credits no latency.

**If it fails:** power/USB → selected serial → offered/resolved profiles → counts/clock evidence. Missing binding/device/profile is BLOCKED; do not substitute another camera. Preserve timeout/partial artifacts. This 60 s tool run does not replace the historical N2 15 Hz/300 s soak or attest the different ROS profile; reconcile B1 before promotion.

**Keep:** whole output including `samples.csv`, both configs, `request.json`, `capture.json`, `sdk.log`, captured console logs, PGMs, `metrics.json`, `result.json`.

### C. Start camera node and read back parameters

**Understand / why:** the launched graph must match the bag contract, not merely display images.

**Execute — [BLOCKED: B1/B2, no reviewed matching launch/readback procedure].** No runnable launch is supplied. Sources: [bag README/config](../lab/rosbag_qual/README.md), [bring-up §6 example](RPI5_NATIVE_PERCEPTION_BRINGUP.md). Unblock with a written/reviewed launch and pre-record parameter-readback command for **`/camera/camera`**, domain 42, both IR views and camera information, `/camera/camera/gyro/sample`, `/camera/camera/accel/sample`, `/tf_static`, separate gyro/accel (`unite_imu_method` 0).

**Verify / expect — [MANUAL REVIEW]:** check actual profile and emitter/global-time settings, exact `/camera/camera/infra{1,2}/image_rect_raw` and camera-info names, and parameter dump against reviewed policy. The recorder later saves a dump too; successful dumping alone does not validate values. No tool PASS substitutes for this checkpoint.

**If it fails:** return to raw identity/profile evidence, then driver/version/parameters. Do not improvise remaps from the IR1-only example. **Keep:** launch receipt, full node log, effective dump and review decision; exact new receipt paths are BLOCKED pending that procedure.

### D. Record the bag

**Understand / why:** measure bounded delivery and preserve the graph/configuration needed to interpret it. Quality of Service (QoS) compatibility must be observed.

**Execute — [BLOCKED: B1–B4 and card C must be resolved].** Source: [bag README](../lab/rosbag_qual/README.md). After review, use the matching reviewed config:

```sh
ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 python3 lab/rosbag_qual/record_check.py \
  --config lab/rosbag_qual/config.json \
  --output-dir /path/to/evidence/record
```

**Verify / expect:** `record:bounded/exit/capture_window/bag_exists/bag_info/parameter_dump/topic_qos`; per-topic `present/count/header_rate/bag_receive_rate/stamp_order/stamp_repeats/bag_receive_order/max_gap` and the remaining result criteria. Current config: 20 s request, ≥80% receive-span coverage, IR/info 14.25–15.75 Hz, gyro 190–210, accel 95–105; no reversed/repeated dynamic stamps, parse errors or header gap events; exact stereo pairing ≥0.99. These are configured policies, not new measurements.

**[MANUAL REVIEW]** Open `result.json`, `record.log`, bag information, `parameter_dump.stdout`, `topic_info.json`, saved config/QoS and analysis. Sensor overrides are best-effort/volatile; static transforms are reliable/transient-local. Verify offered/requested compatibility. Header and receive rates are separate quantities.

**If it fails:** check earlier layers before topics/QoS, then storage. A bag-size/duration ratio below 16.6 MB/s cannot prove write margin. **Keep:** whole record directory, especially `bag/`, metadata, command receipt, logs, readbacks, analysis and result.

### E. Stop the live node

**Understand / why:** release hardware ownership and remove live publishers before replay.

**Execute — [MANUAL REVIEW].** Ctrl-C in Pi B; wait for foreground node exit and device release. Source: [bring-up §6 step 7](RPI5_NATIVE_PERCEPTION_BRINGUP.md), [bag README](../lab/rosbag_qual/README.md).

**Verify / expect:** clean shutdown; replay checks quiet graphs in both domains. No independent `result.json` belongs to this manual step. **If it fails:** preserve crash/reset logs and stop; do not start another owner on uncertain state. **Keep:** shutdown log and operator note.

### F. Replay, isolated

**Understand / why:** compare saved delivery with an isolated replay, preserving original stamps. Live publishers could make replay counts look healthier than the bag.

**Execute — [BLOCKED: accepted recording and stopped camera required].** Source: [bag README](../lab/rosbag_qual/README.md).

```sh
ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 python3 lab/rosbag_qual/replay_check.py \
  --config lab/rosbag_qual/config.json \
  --bag /path/to/evidence/record/bag \
  --output-dir /path/to/evidence/replay \
  --live-domain 42 --replay-domain 43
```

**Verify / expect:** `replay:quiet:node_list.json`, `replay:quiet:replay_node_list.json`, `replay:player`; per-topic `evidence/count/stamps/rate`. Default rate tolerance is PROPOSED 10%, count fraction ≥0.99; stamped streams additionally require exact sequence hashes, so that count allowance does not permit stamp loss. Zero static-transform stamps are valid.

**[MANUAL REVIEW]** Read `result.json`, graph receipts, `player.log` and observations before accepting replay evidence. **If it fails:** verify camera stopped, domain isolation, plugin/dependencies, then QoS/count/stamp differences. Do not mix domains to get traffic. **Keep:** entire replay and original record directories.

### G. Optional calibration take, then saved-take check

**Understand / why:** capture suitable excitation separately from a still raw check; screen a finalized take before expensive fitting. Default session policy resolves N3 first.

**Execute — [BLOCKED: B5, power/storage/profile attestation and calibration prerequisites].** Source: [calibration lab README](../calibration/lab/README.md). Only after the owner's explicit authorization and verified deployment:

```sh
export WBR_CAMERA_AVAILABLE='CAMERA AVAILABLE'
bash "$HOME/wbr-runtime/calib-lab-20261015/pi/record_calib_take.sh" C1 60
```

The fixed wrapper uses 640×480/30, gyro/200, accel/100, emitter OFF; captures into random-access memory (RAM), then copies/hashes. A 60 s request may have SDK spans slightly below the ASSUMED 60 s minimum; the checker recommends a comfortably interior duration such as 90 s. Review that choice before acquisition; the example is not a guaranteed duration PASS. Move the camera smoothly through all axes around a fixed visible measured grid; include still ends. Do not lower RAM reserves or substitute card capture when the wrapper refuses.

**Execute — [MAIN, UNTESTED ON HW].** Saved files only; source: [calib_record README](../lab/calib_record/README.md).

```sh
python3 lab/calib_record/check_calib_take.py \
  --take-dir "$HOME/wbr-evidence/2026-10-15-calib-C1" \
  --kind camera-imu --outdir "$HOME/wbr-evidence/check-C1-01"
```

**Verify / expect:** `completeness`, `capture_checksums`, `metadata`, `recorder_stop`, `sdk_domain`, `duration`, `excitation.gyro/accel`, `rate_drops.*`, `timestamp.*`, `stereo_pairing`, `callback_bag_agreement`, `ir_dimensions`, `motion_blur.*`, `storage.write_headroom/free_space`, `input_unchanged`. **`target_detection` remains BLOCKED:** existing tools supply no AprilGrid detection counts. Missing post-capture `storage.json` also blocks capacity; it cannot be recreated on a Mac copy as Pi evidence.

**[MANUAL REVIEW]** Read every result/log and inspect target visibility, excitation and blur. A numeric sharpness proxy is not target detection or observability. **If it fails:** inspect capture/identity/clock/accounting before motion and storage; retain missing receipts as BLOCKED. **Keep:** original outer session plus `take/`, payload hashes/copy verification, power/kernel logs, and complete checker output. This checker does not capture or calibrate.

### H. Copy evidence and verify hashes

**Understand / why:** results reference raw files, sometimes large inputs outside the result directory. A result alone is not an archive. Secure Hash Algorithm 256-bit (SHA-256) manifests identify the preserved bytes.

**Execute — [MANUAL REVIEW].** Preserve whole session/record/replay/take directories, including failures. The calibration wrapper already saves `ram-sha256.txt` and `copy-verify.log`; inspect them. Sources: [calibration lab](../calibration/lab/README.md), [check outputs](../lab/calib_record/README.md), [bag preservation](../lab/rosbag_qual/README.md).

**[BLOCKED: exact authorized transport and general session hash command absent from the required sources].** Obtain a reviewed copy/hash procedure naming real source/destination paths. No invented transport command is supplied. **Verify:** destination bytes against preserved manifests before deletion; hashes identify bytes, not authenticity. **If it fails:** retain source and RAM evidence; diagnose copy/storage. **Keep:** manifests, verification receipts and original artifacts.

## 4. Failure triage: bottom-up

**PROPOSED stop policy:** new under-voltage, reboot, camera USB <5000M or timestamp reversal stops acquisition. Preserve partial evidence. Allow **one retry**, only after a discriminating diagnostic/correction, in a new directory; otherwise stop for review. Never reuse a capture output directory: tools refuse existing evidence rather than safely appending a retry. Never relax thresholds to obtain PASS.

| Symptom → likely layer | First check | Do NOT do |
|---|---|---|
| Voltage/throttle event → power | Raw samples, supply declaration, kernel log | Clear history to hide it |
| Reset/480M → USB | Camera branch in saved tree plus matched sysfs speed | Read root-hub speed as camera speed |
| Wrong/absent unit → identity | SDK serial versus separate USB/ASIC/update IDs | Transfer old-unit acceptance |
| Missing rows/stalls → raw stream | Profiles, callback/writer counts, SDK errors | Start ROS to conceal raw failure |
| Reversal/domain switch → clocks | Per-stream domain and original timestamps | Subtract epochs or patch stamps |
| Unexpected graph → driver/params | Effective dump and launch receipt | Reinstall or change many variables |
| Missing/incompatible traffic → topics/QoS | Exact names/types and endpoint QoS receipts | Assume image display qualifies recording |
| Bag gaps/low headroom → storage | Destination qualification, receive span, logs | Treat average byte ratio as benchmark |
| Replay count/hash failure → replay | Quiet graphs, player log, recorded baseline | Leave live camera publishing |

Sources: [NEXT_GATE.md](NEXT_GATE.md), tool READMEs above. Diagnose the first unresolved layer; an observed upper-layer symptom does not identify its cause.

## 5. Clock cheat card

**Understand:** never subtract across domains without a qualified mapping. Equal-looking numbers, shared units and monotonicity do not establish synchronization.

| Clock | Used for | Boundary |
|---|---|---|
| D435i `hardware_clock` | Device sample intervals | Same declared device/domain/session |
| D435i `global_time` | SDK conversion toward OS system time | Not host monotonic; not exposure latency |
| D435i `system_time` | Separately reported SDK domain | Not interchangeable with hardware/global; calibration rejects it |
| ROS `header.stamp` | Driver/source stamps and sequence | Actual domain needs run readback |
| rosbag2 receive `messages.timestamp` | Writer/receive ordering and rates | Separate from source header/exposure |
| `CLOCK_MONOTONIC` | Host intervals, callback/replay arrivals | Same-host timeline; scheduling included |
| `CLOCK_REALTIME` | Wall-time/Coordinated Universal Time provenance | May jump; not an interval clock |

**Verify:** retain clock names, units, session and underlying API. `CLOCK_MONOTONIC_RAW` is another clock, not an alias for MONOTONIC. Kernel boot timestamps stay separate too. Raw tools withhold unmapped latency; a header/receive fit cannot separate offset from transport delay. These camera clocks do not describe STM32 `imu_body`. Source: [GATE_TOOLING clock inventory](GATE_TOOLING.md), [raw README](../lab/d435i_raw/README.md), [calibration clock policy](../lab/calib_record/README.md).

## 6. Eight judgment questions

<details>
<summary>Open for short answers</summary>

1. **Why does idle power PASS not qualify streaming?** Different load and observation window; faults between samples remain possible. Require reviewed streaming-window evidence.
2. **Why is the old-unit FAIL correct?** Serial/profile violate the current contract. Missing evidence blocks other criteria; FAIL takes precedence.
3. **What does a bag gap count mean?** Events exceeding the configured period multiple, not an exact count of lost physical samples. Raw frame-number gaps are a different metric.
4. **Why replay in 43 with the camera stopped?** Isolate saved traffic and prevent live publishers contaminating counts/stamps; both graphs must be quiet of camera nodes.
5. **What can the disk ratio not measure?** Write stalls, fsync latency, cache behavior or remaining margin. Low saved byte rate can also accompany lost data.
6. **Does global time permit device-to-monotonic subtraction?** No. A session-qualified mapping with uncertainty is needed; global time relates toward system time.
7. **Does raw static PASS calibrate the IMU?** No. Mean/gravity/statistical checks are plausibility evidence, not bias/scale/noise calibration or stationarity proof.
8. **Who promotes a gate after tool PASS?** The owner, after reviewing evidence and candidate gate criteria. Neither orchestrator aggregation nor fixture PASS grants promotion.

</details>

## 7. Go deeper only if needed

`WBR_STUDY_GUIDE.md` lives in the **project files, not this repository**. Use these chapter pointers; the current source-linked tool contracts above govern execution.

| Lab step | Guide chapter | Read for |
|---|---|---|
| Power, USB, raw identity | §2 | Hardware/USB/power diagnosis |
| Destination and copy | §3 | Storage budgets and evidence retention |
| Raw/bag timing | §8 | Clock-domain reasoning |
| Launch, topics, record/replay | §9 | ROS, QoS and rosbag |
| Optional takes | §10 | Calibration judgments |
| Review/promotion | §15 | Gate ladder and evidence |

### After the lab

- Copy complete evidence, including failures; verify hashes before deleting originals.
- Record actual hardware/profile/software, clock domains, unresolved blockers and human continuation decisions.
- Only after human review, the owner decides updates to `PROJECT_STATE.md`, `NEXT_GATE.md` and the evidence index. This companion changes none of them. **Tool PASS is not gate PASS.**

### Command → source → tag ledger

Paths may be substituted only as described above. Commands appear in full at their action cards; blocked procedures have no invented command.

- Plan (`python3 lab/run_lab_session.py`, `--plan`) → `lab/README.md`, `lab/run_lab_session.py` → **[OFFLINE-VERIFIED: ran on fixtures]**.
- Power fixture (`python3 lab/power_usb/check_power_usb.py`, `--analyze-only`) → `lab/power_usb/README.md` → **[OFFLINE-VERIFIED: ran on fixtures]**.
- Raw fixture (`python3 lab/d435i_raw/check.py`, `--analyze-only`) → `lab/d435i_raw/README.md` → **[OFFLINE-VERIFIED: ran on fixtures]**.
- `source /opt/ros/jazzy/setup.bash` → `lab/README.md` → **[MAIN, UNTESTED ON HW]**.
- Idle power (`python3 lab/power_usb/check_power_usb.py`, `--duration 60`) → `lab/power_usb/README.md` → **[MAIN, UNTESTED ON HW]**.
- Raw capture (`python3 lab/d435i_raw/check.py`, `--capture --static`) → `lab/d435i_raw/README.md` → **[MAIN, UNTESTED ON HW]**.
- Bag record (`ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 python3 lab/rosbag_qual/record_check.py`) → `lab/rosbag_qual/README.md` → **[BLOCKED: B1–B4 and reviewed launch]**.
- Bag replay (`ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 python3 lab/rosbag_qual/replay_check.py`) → `lab/rosbag_qual/README.md` → **[BLOCKED: accepted record, camera stopped]**.
- `export WBR_CAMERA_AVAILABLE='CAMERA AVAILABLE'` → `calibration/lab/README.md` → **[BLOCKED: explicit owner authorization/prerequisites]**.
- Calibration capture (`bash "$HOME/wbr-runtime/calib-lab-20261015/pi/record_calib_take.sh" C1 60`) → `calibration/lab/README.md` → **[BLOCKED: authorization, qualified power/storage/profile]**.
- Saved take (`python3 lab/calib_record/check_calib_take.py`, `--take-dir`, `--kind camera-imu`) → `lab/calib_record/README.md` → **[MAIN, UNTESTED ON HW]**.
