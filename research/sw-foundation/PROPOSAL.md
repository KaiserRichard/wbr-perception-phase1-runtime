# WBR software foundation: what to build, in what order (proposal, 2026-10-14)

Status: PROPOSAL for owner review. Nothing here is a gate PASS or an accepted architecture.
Evidence: `J1_components.md` (component inventory, codex-g) and `J2_architecture.md` (architecture
alternatives, codex-c), both built on the slide thread's `slides_roadmap/research/R1_algorithms.md`,
`R2_integration.md` and `R3_plan.md`. Labels: SOURCE-SUPPORTED / MEASURED / INFERRED / UNKNOWN.

## 1. Answer to the hypothesis "ROS 2 pose/health node + Pi->STM32 contract + latency logger first"

INFERRED: the components are needed eventually, but that order is not justified yet.
- Both independent reports converge on data-first -> native adapter -> ROS output bridge (J2 §7, J1 graph).
- Reason: the open uncertainty today is upstream of any node. Post-fix D435i replay has never run
  (MEASURED, 14 Oct addendum §5), and no retained take has been audited end to end. A ROS node now would
  entangle wrapper/QoS/clock faults with the unresolved input faults (violates ADR-003 isolation).
- UNKNOWN: whether ROS 2 adds meaningful latency on Pi 5 for stereo/30 + IMU/200. No matched measurement
  exists (J2 §5: Pi 4/Foxy study only). So native-first is justified by existing code and fault isolation,
  NOT by a measured ROS penalty.
- The Pi->STM32 contract should be *designed* early (semantics, rejection rules, test vectors) but the
  wire sender comes after estimate semantics exist (J2 §4, §7).

## 2. Correction found by the research (updated: the Pi writes SQLite/CDR with librealsense 2.58.4, and take_tools reads it; see tools/take_tools/README.md)

SOURCE-SUPPORTED (J1 C1): "librealsense writes rosbag2 since 2.56" is not defensible. v2.56.5
`ros_writer.cpp` writes ROS 1 bags; the newer `ros2_writer.cpp` writes SQLite/CDR. Which one the Pi build
uses is UNKNOWN; the `.db3` file name proves nothing. The first take on the Mac must be inspected
(file magic, tables, topic types, original timestamp metadata) before any converter is trusted.

## 3. Components: engine-agnostic vs engine-specific (J1 table)

| # | Component | Engine-agnostic? | Exists | Hardware needed to *write* it |
|---|---|---|---|---|
| C0 | Run manifest + clock-domain mapping validators | Yes | fragments (`d435i_rs.h`, eval tool) | No |
| C1 | Retained-take decoder, audit, EuRoC-ASL / ROS 2 / Kalibr export | Yes | recorder only; reuse `rosbags`, `rs-convert`, `kalibr_bagcreater` | No (a real take needed to validate) |
| C2 | Input association / timestamp validation | Partly | `d435i_input.h` + patch | No |
| C3 | Calibration import (Kalibr -> ORB/OpenVINS/Basalt settings) | Partly (math shared, schemas differ) | hand-written ORB yaml | No |
| C4 | Estimator adapter: feed, pose, tracking state, reset/map epoch | No | patch precursor | Pi for validation |
| C5 | Camera pose -> body pose / TF | Partly | design only (R1) | Mount extrinsics for values |
| C6 | Health/validity monitor | Partly | R2 proposal | No |
| C7 | Latency/resource/queue observer | Partly | timing fragments; reuse ros2_tracing, psutil, vcgencmd | Pi for measurement |
| C8 | Regression/evaluation runner | Partly | ATE/RPE tool (PR #2), plot tool | No |
| C9 | Pi->STM32 host codec + reference receiver + fault fixtures | Yes | R2 candidate only | No (STM32 for N7) |

## 4. Proposed build order (INFERRED)

1. **C0 + C1 data foundation** (start now, Mac-only): decoder/inspector for the recorder's file, lossless
   EuRoC-ASL exporter with integer-ns original stamps, separate raw gyro/accel, hashes and a manifest;
   synthetic fixtures first, then one real take copied from the Pi. Unblocks: every engine can be run on the
   same retained takes (ORB EuRoC path, OpenVINS, Basalt) and Kalibr input.
2. **C3 calibration converter** with explicit `T_A_B` convention tests (inverse direction, Kalibr timeshift
   sign, continuous vs discrete noise). Small, engine-agnostic math; prevents a classic silent VIO failure.
3. **C9 codec + reference receiver + fault harness** for the R2 candidate envelope, health-only, labelled
   CANDIDATE. Hardware-free; can run in parallel with 1-2.
4. **C4 + C7 native ORB adapter with built-in latency/queue events**, after the Pi thread gets post-fix
   replay working. Engine-specific; needs the Pi.
5. **Thin ROS 2 output/diagnostics bridge (C5/C6)** once estimate semantics are characterized.

Experiment that would overturn this (J2 §7): on the same retained take with stable power, run native,
native+ROS bridge, and realsense-ros topic input around the same ORB core; if the ROS path matches input
audits and latency budgets with less custom code, switch to ROS-first.

## 5. Threads and Codex

Items 1-2 and item 3 share no files and need no hardware, so a second build thread for item 3 is
reasonable. Item 4 must wait for the Pi thread (it owns the Pi and camera). Codex capacity (b, c, g, d with
`-m gpt-6-luna`) is the real limit, shared by three threads.

## 6. Decisions only the owner can make

- Approve data-first order (default if no answer: proceed with items 1-2).
- Whether the Pi->STM32 envelope may be prototyped now as CANDIDATE (needs the controller owner's review
  before any STM32 work).
- Copy one retained take (e.g. the 15 s RAM test) to the Mac for C1 validation (Pi thread action).
