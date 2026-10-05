# Claude Code Instructions — WBR Perception Runtime

Always reply to the user in English, even when the user writes in Vietnamese, unless they explicitly request Vietnamese.

## Read first

Before making architectural or implementation decisions, inspect:

- `AGENTS.md`
- `README.md`
- `docs/PROJECT_STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/NEXT_GATE.md`
- `docs/EVIDENCE_INDEX.md`

If one of these files does not yet exist or is clearly stale, report that rather than inventing its contents.

## Project

This repository is the Phase-1 perception/runtime research project for a wheel-biped robot.

Primary stack:

- Raspberry Pi 5;
- Ubuntu/Linux;
- ROS 2 Jazzy;
- Intel RealSense D435i;
- ORB-SLAM3.

The Pi owns perception, visual-inertial odometry, SLAM and non-hard-real-time estimation.
The STM32 owns hard-real-time balancing, control and actuator safety.

## Engineering rules

- Do not declare PASS without evidence.
- Do not modify hardware/system state unless the current ticket explicitly permits it.
- Preserve timestamp, frame and calibration provenance.
- Never confuse the D435i camera IMU with the robot body IMU.
- Do not jump to ORB-SLAM3 while an earlier sensor/ROS gate is unresolved.
- Compilation is not experimental validation.
- Prefer small, reversible changes.
- Run relevant tests before reporting completion.
- Never use destructive Git commands unless explicitly approved.
- Do not rewrite large parts of the repository merely to make them easier for the agent to understand.

## Hardware rule

One agent owns a stateful hardware execution session at a time.

Do not simultaneously mutate:

- Raspberry Pi system state;
- D435i runtime state;
- STM32 firmware state;
- a shared experiment directory.

## Return format

For execution tasks, return:

GOAL

STATUS
PASS / OPEN / BLOCKED

FILES INSPECTED

FILES CHANGED

COMMANDS RUN

TESTS

EVIDENCE

ASSUMPTIONS

RISKS

WHAT WAS NOT VERIFIED

NEXT RECOMMENDED ACTION
