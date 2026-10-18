# Next Gate

> **[SOURCE-SUPPORTED]** This file describes exactly one active technical gate. **[INFERRED]** Reviewed 2026-10-18 against the current tool READMEs and [gate-to-tool index](GATE_TOOLING.md); no physical run was made and no gate status is promoted.

## Gate

N3 — ROS 2 Physical Sensor Pipeline

## Status

OPEN (reviewed 2026-10-18)

## Current state (2026-10-18)

- **[UNKNOWN]** No new-unit (317422076650) N1/N2/N3 evidence exists. The September N3 attempts used the old unit and do not transfer ([PROJECT_STATE](PROJECT_STATE.md), [old validation records](../experiments/2026-09-12-pi5-native-sensor-validation/)).
- **[MEASURED]** Under-voltage occurred on the 5 V / 3 A supply; the old card measured 16.6 MB/s sustained write against the estimated 18.4 MB/s stream demand ([2026-10-14 session addendum](../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md) §§1, 3). **[SOURCE-SUPPORTED]** A 5.1 V / 5 A supply and 128 GB V30/A2 card were ordered; arrival and qualification are **[UNKNOWN]** ([PROJECT_STATE](PROJECT_STATE.md)).
- **[SOURCE-SUPPORTED]** The minimum discrimination sequence is power/USB observation → current-unit raw stream/profile check → effective ROS parameter verification → bounded record and offline bag analysis → header/receive clock diagnostic → isolated replay. Tooling is software-ready but has hardware-run status NONE ([GATE_TOOLING](GATE_TOOLING.md#n3--rosbag-recordreplay)).
- **[UNKNOWN]** The current checkout contains no `wbr_d435i_bringup` path or README, so its `verify_params` CLI and exact invocation cannot be established here ([checkout file inventory](GATE_TOOLING.md)). Do not claim that this verifier ran; retain the explicit readback step below and resolve the tool/command before streaming.

## Why this gate matters

**[SOURCE-SUPPORTED]** Before using ROS 2 data for ORB-SLAM3/VIO, prove that the physical D435i streams can be exposed, measured, recorded and replayed with trustworthy stream selection, rates, timestamps and QoS ([native baseline §4](NATIVE_PI5_BASELINE_ARCHITECTURE.md#4-native-pipeline-stages)).

## Read first

Inspect current versions of:

- [PROJECT_STATE.md](PROJECT_STATE.md)
- existing N3 preparation/runbook files;
- previous `n3-physical-*` experiment results;
- launch receipts;
- parameter readback;
- topic expectations;
- QoS configuration;
- rosbag metadata if any.

**[SOURCE-SUPPORTED]** Exact current tool commands and ID definitions are in [GATE_TOOLING.md](GATE_TOOLING.md#n3--rosbag-recordreplay) and the linked [power_usb](../lab/power_usb/README.md), [d435i_raw](../lab/d435i_raw/README.md), [rosbag_qual](../lab/rosbag_qual/README.md), and [stamp_drift](../tools/stamp_drift/README.md) READMEs.

## Current uncertainty

**[UNKNOWN]** The first unresolved physical condition is fresh N1/N2 evidence from the new unit under a stable supply and a qualified recording card; earlier software tooling did not observe the current hardware. The smallest useful discriminating experiment is one fixed configuration and one bounded session, proceeding bottom-up so power/USB faults or profile mismatch are visible before a bag is interpreted. **[MEASURED]** The known prior confounders are undervoltage and insufficient sustained write performance; their replacement fixes have not been measured ([session addendum](../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md)).

**[ASSUMED decision / SOURCE-SUPPORTED inputs]** The intended VIO profile is `d435i_vio_v1`: both IR streams, Y8, 640×480 at 30 Hz, emitter off, separate D435i camera gyro at 200 Hz and accel at 100 Hz. The [calibration plan](D435I_CALIBRATION_PLAN.md#1-stereo-ir-intrinsics) records measured factory stereo intrinsics for 640×480 and selects 30 Hz for SLAM/calibration acquisition. **[UNKNOWN]** This 30 Hz profile has not been attested on the new unit. The current [d435i_raw default config](../lab/d435i_raw/thresholds.yaml) uses 848×480 at 30 Hz; `d435i_vio_v1` therefore requires a reviewed per-run config and its evidence copy. N2 qualification of the 848×480 default cannot qualify this selected 640×480 profile.

## Do

**[ASSUMED]** The sequence below is the minimum discriminating run. Run from the repository root on the Pi, use new evidence directories, keep the camera and rosbag tools in the stated ROS domains, and preserve each command receipt/config/readback. No step below is a claim that a run has happened.

### 0. Hardware prerequisites

- **[SOURCE-SUPPORTED]** Use the replacement 5.1 V / 5 A supply and confirm `power_usb` can observe the negotiated supply; the configured criterion is `supply` ([power_usb README](../lab/power_usb/README.md#criteria-and-configuration)). A 5 A label alone is not evidence of stable power.
- **[SOURCE-SUPPORTED]** Install the 128 GB card as the chosen recording volume and qualify sustained writes on the Pi before a full-rate bag. The [calibration plan](D435I_CALIBRATION_PLAN.md#prerequisites-and-powerstorage) specifies at least 27.6 MB/s (1.5 × estimated 18.4 MB/s demand) for a file larger and longer than the planned take; this is a proposed storage prerequisite, not an N3 tool ID. Confirm free space and use a dedicated evidence directory.
- **[SOURCE-SUPPORTED]** Connect the camera directly to a USB 3 port. `power_usb:usb_link` checks the matched device at the configured ≥5000 Mbit/s floor, with topology and kernel evidence; USB 3 connection alone does not prove stability ([power_usb README](../lab/power_usb/README.md)).

### 1. Power and USB observation

First capture a bounded idle baseline using the documented [power_usb command](../lab/power_usb/README.md#evidence-and-replay-on-mac-or-pi). Choose a new path for each run:

```sh
python3 lab/power_usb/check_power_usb.py \
  --out /home/pi/wbr-evidence/n3-20261018/01-power-usb --duration 60
```

Relevant IDs: `under_voltage`, `ext5v`, `temperature`, `window_coverage`, `supply`, `usb_link`, `usb_topology`, `kernel_log`, `load_window`, and `raw_integrity` ([criteria](../lab/power_usb/README.md#criteria-and-configuration)). **[INFERRED]** An idle check is only a prerequisite/baseline; it does not cover the streaming load. The raw and recording steps add the camera workload and preserve their own evidence.

### 2. Raw camera stream with `d435i_vio_v1`

Prepare a run-specific JSON config at `/home/pi/wbr-evidence/n3-20261018/d435i_vio_v1.json` from the checked-in [thresholds config](../lab/d435i_raw/thresholds.yaml), updating its declared profile to 640×480 Y8 IR1/IR2 at 30 Hz, emitter OFF, gyro 200 Hz, accel 100 Hz, and reviewing each threshold source/rationale. Save the effective config unchanged with the run. Do not modify the repository defaults as an undocumented runtime override. **[SOURCE-SUPPORTED]** The raw README provides `--config`, capture and reanalysis modes; numeric acceptance limits remain those in the selected config ([d435i_raw README](../lab/d435i_raw/README.md#capture-and-analysis)).

```sh
python3 lab/d435i_raw/check.py --capture --static --seconds 300 \
  --config /home/pi/wbr-evidence/n3-20261018/d435i_vio_v1.json \
  --outdir /home/pi/wbr-evidence/n3-20261018/02-d435i-raw
```

**[SOURCE-SUPPORTED]** The 300 s full-window soak is the mandatory N2 validation duration in the [calibration plan](D435I_CALIBRATION_PLAN.md#prerequisites-and-powerstorage); the checker supports `--seconds`. Review `identity.serial`, `identity.firmware`, `identity.usb_type`, `profiles`, `stereo`, `duration`, `sample_accounting`, `ir_left.samples/rate/receipt_gap/drops/timestamps`, `ir_right.*`, `gyro.*`, and `accel.*` plus static/image plausibility criteria ([criterion list](../lab/d435i_raw/README.md#exact-pi-commands)). **[UNKNOWN]** Tool profile support at this resolution must be confirmed by the run; if unavailable or different, stop and do not silently substitute the default profile.

### 3. Verify effective ROS parameters before recording

**[SOURCE-SUPPORTED]** The requested `wbr_d435i_bringup verify_params` tool is not present in this checkout, and no README documents its invocation. Its exact command is therefore **[UNKNOWN]**; obtain the corresponding tool/README and use its documented command to verify the effective `/camera/camera` parameters match `d435i_vio_v1`, including both IR profiles, gyro/accel rates, emitter state, topic names, QoS-relevant settings, and `global_time_enabled`. Preserve its output and the source launch receipt. Do not continue to record if parameter verification is unavailable or mismatched.

As supporting evidence only, capture the ROS parameter dump using the standard CLI after the camera node is already launched in domain 42:

```sh
source /opt/ros/jazzy/setup.bash
ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 ros2 param dump /camera/camera \
  > /home/pi/wbr-evidence/n3-20261018/03-camera-params.yaml
```

**[INFERRED]** This dump preserves readback for review but does not replace the absent `verify_params` check or establish that the launch configured the intended sensor profile.

### 4. Bounded ROS bag record and offline analysis

**[SOURCE-SUPPORTED]** After parameter verification succeeds, use the exact [rosbag_qual README](../lab/rosbag_qual/README.md#pi-commands) recorder command with the configured topic/QoS list and a fresh output path:

```sh
source /opt/ros/jazzy/setup.bash
ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 python3 lab/rosbag_qual/record_check.py \
  --config lab/rosbag_qual/config.json \
  --output-dir /home/pi/wbr-evidence/n3-20261018/04-record
```

Review `record:bounded`, `record:bag_info`, `record:parameter_dump`, `record:topic_qos`, `record:exit`, `record:capture_window`, `record:bag_exists`, and `record:offline_analysis`; also review configured per-topic `present`, `count`, `header_rate`, `bag_receive_rate`, `max_gap`, `drops`, `stamp_order`, `stamp_repeats`, `bag_receive_order`, `cdr`, and `receive_boundary_gap` IDs ([ID mapping](GATE_TOOLING.md#n3--rosbag-recordreplay)). Then explicitly analyze the finalized bag with the documented offline command:

```sh
python3 lab/rosbag_qual/analyze_bag.py \
  --config lab/rosbag_qual/config.json \
  --bag /home/pi/wbr-evidence/n3-20261018/04-record/bag \
  --output-dir /home/pi/wbr-evidence/n3-20261018/05-analysis
```

**[UNKNOWN]** `lab/rosbag_qual/config.json` must be confirmed to name the topics and profile actually launched. If `d435i_vio_v1` topics/profile differ from the config, use a reviewed run-specific config and preserve it; do not treat wrong-profile bag analysis as N3 evidence.

### 5. Header-stamp / bag-receive diagnostic

**[SOURCE-SUPPORTED]** Once recording is finalized, use the documented [stamp_drift command](../tools/stamp_drift/README.md#input-and-exact-commands). Use `D435I_GLOBAL_TIME` and `true` only when the effective parameter readback confirms `global_time_enabled` was enabled; otherwise declare the recorded hardware/system domain or `UNKNOWN`:

```sh
python3 tools/stamp_drift/analyze.py \
  /home/pi/wbr-evidence/n3-20261018/04-record/bag/bag_0.db3 \
  --header-clock D435I_GLOBAL_TIME --global-time-enabled true \
  --output-dir /home/pi/wbr-evidence/n3-20261018/06-stamp-drift
```

Review `<topic>:fit` and `<topic>:continuity` for supported topics. **[SOURCE-SUPPORTED]** This is a diagnostic of ROS `header.stamp` versus rosbag2 `messages.timestamp`; it cannot establish absolute latency, exposure timing, actual timestamp-domain selection, or a cross-clock map ([stamp_drift limits](../tools/stamp_drift/README.md#reading-the-report)).

### 6. Stop live camera and replay in isolation

Stop the camera node and confirm it is absent before replay. Use the exact [rosbag_qual replay command](../lab/rosbag_qual/README.md#pi-commands), with live domain 42 and isolated replay domain 43:

```sh
source /opt/ros/jazzy/setup.bash
ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 python3 lab/rosbag_qual/replay_check.py \
  --config lab/rosbag_qual/config.json \
  --bag /home/pi/wbr-evidence/n3-20261018/04-record/bag \
  --output-dir /home/pi/wbr-evidence/n3-20261018/07-replay \
  --live-domain 42 --replay-domain 43
```

Review `replay:player`, `replay:quiet:node_list.json`, `replay:quiet:replay_node_list.json`, and each configured `replay:<name>:evidence`, `count`, `stamps`, and (where configured) `rate` criterion ([criterion mapping](GATE_TOOLING.md#n3--rosbag-recordreplay)). Preserve the entire session manifest, effective configs, raw logs, result JSON files, and storage qualification. **[UNKNOWN]** Cross-check final tool results against current project policy before any gate decision.

## Do not

- jump to ORB-SLAM3 because binaries exist;
- reinstall the environment without evidence;
- change several independent variables at once;
- declare N3 PASS because images appear in RViz;
- mix live camera publishers with replay qualification.

## Candidate PASS criteria

**[SOURCE-SUPPORTED]** Replace each covered criterion with its tool ID(s) below. A matching ID means evidence can be collected; it does not mean the criterion is met. **[UNKNOWN]** Criteria without a direct ID still require explicit review and recorded evidence.

- D435i enumerates normally — `power_usb:usb_link`, `usb_topology`; supporting `d435i_raw:identity.serial`, `identity.firmware`, `identity.usb_type` (**partial enumeration coverage**).
- Required infrared and IMU streams exist — `d435i_raw:profiles`, `*.samples`, `stereo`; `rosbag_qual:topic:<name>:present`, `topic:<name>:count`.
- Actual rates are measured — `d435i_raw:*.rate`; `rosbag_qual:topic:<name>:header_rate`, `topic:<name>:bag_receive_rate`.
- Timestamp behavior is inspected — `d435i_raw:*.timestamps`; `rosbag_qual:topic:<name>:stamp_order`, `stamp_repeats`, `bag_receive_order`, `max_gap`; `stamp_drift:<topic>:fit`, `<topic>:continuity`. Clocks stay separately labelled; mapping remains UNKNOWN.
- QoS is documented — `rosbag_qual:record:topic_qos` plus saved `qos_overrides.yaml`, `topic_info.json` and config.
- A bounded rosbag is recorded — `rosbag_qual:record:bounded`, `record:exit`, `record:capture_window`, `record:bag_exists`.
- `ros2 bag info` succeeds — `rosbag_qual:record:bag_info`.
- The bag replays with live camera stopped — `rosbag_qual:replay:quiet:node_list.json`, `replay:quiet:replay_node_list.json`, `replay:player`.
- Replayed representative topics are measurable — `rosbag_qual:replay:<name>:evidence`, `count`, `stamps`, `rate` (rate only where configured).
- No serious USB/kernel failure appears — `power_usb:usb_link`, `usb_topology`, `kernel_log`, `under_voltage`, over the complete available observation window.
- Pi power/throttling state is recorded — `power_usb:under_voltage`, `ext5v`, `temperature`, `supply`, `window_coverage`; supporting `profile:no_throttle_or_undervoltage`, `max_temperature`. Polling limits remain.
- Evidence is preserved in a dedicated experiment directory — review tool output/raw-file contracts, `raw_integrity`, `record:saved_input`, `input_unchanged` where applicable, plus a project session manifest; no single criterion asserts the whole project-level manifest requirement.

## Required output

At completion, update:

- `docs/PROJECT_STATE.md`
- `docs/EVIDENCE_INDEX.md`
- this file with PASS / OPEN / BLOCKED and the next gate.
