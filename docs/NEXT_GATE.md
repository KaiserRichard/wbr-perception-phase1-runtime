# Next Gate

> This file should describe exactly one active technical gate.
> Replace the draft below after inspecting current evidence.

## Gate

N3 — ROS 2 Physical Sensor Pipeline

## Status

OPEN (reviewed 2026-10-14)

## Current state (2026-10-14)

- No new-unit (317422076650) N1/N2/N3 evidence exists yet; the September N3 attempts used the old unit and do not transfer (`docs/PROJECT_STATE.md`).
- Two prerequisites are measured as unresolved: under-voltage on the 5 V / 3 A supply, and card write rate below the stream rate (`experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md` §1, §3).
- Parallel diagnostic work (N4B demo runbook `experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md`) is explicitly OPEN and does not replace this gate.

## Why this gate matters

Before using ROS 2 data for ORB-SLAM3/VIO, prove that the physical D435i streams can be exposed, measured, recorded and replayed with trustworthy stream selection, rates, timestamps and Quality of Service (QoS).

## Read first

Inspect current versions of:

- `docs/PROJECT_STATE.md`
- existing N3 preparation/runbook files;
- previous `n3-physical-*` experiment results;
- launch receipts;
- parameter readback;
- topic expectations;
- QoS configuration;
- rosbag metadata if any.

## Current uncertainty

Determine the exact first unresolved condition in previous N3 physical attempts.

Possible classes include:

- driver/package state;
- launch parameters;
- stream profile;
- topic names;
- QoS;
- timestamps;
- record command;
- storage;
- replay;
- metric tooling.

Do not guess which one failed.

## Do

1. Audit previous N3 evidence.
2. Establish exact current Pi/software state before mutation.
3. Identify the minimum discriminating test.
4. Run a bounded physical experiment only after the failure mode is understood.
5. Preserve logs/config/version information.

## Do not

- jump to ORB-SLAM3 because binaries exist;
- reinstall the environment without evidence;
- change several independent variables at once;
- declare N3 PASS because images appear in RViz;
- mix live camera publishers with replay qualification.

## Candidate PASS criteria

Update these against current runbook/tooling before final use.

- D435i enumerates normally.
- Required infrared and IMU streams exist.
- Actual rates are measured.
- Timestamp behavior is inspected for obvious discontinuity/reversal.
- QoS is documented.
- A bounded rosbag is recorded.
- `ros2 bag info` succeeds.
- The bag replays with the live camera stopped.
- Replayed representative topics are measurable.
- No serious new USB/kernel failure appears.
- Pi power/throttling state is recorded.
- Evidence is preserved in a dedicated experiment directory.

## Required output

At completion, update:

- `docs/PROJECT_STATE.md`
- `docs/EVIDENCE_INDEX.md`
- this file with PASS / OPEN / BLOCKED and the next gate.
