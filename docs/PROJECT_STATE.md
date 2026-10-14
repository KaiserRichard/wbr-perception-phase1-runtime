# Project State

> Canonical short summary of current WBR Phase-1 state, updated 2026-10-14 from committed evidence.
> Every row cites an evidence file. Nothing here is a gate PASS.

## Hardware (as of 2026-10-14)

| Item | State | Evidence |
|---|---|---|
| Raspberry Pi 5 | 8 GB board boots the existing card (MEASURED 2026-10-14); a 4 GB board was the stand-in on 2026-10-13 | `experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md` §1 |
| Boot / storage | 32 GB microSD, no NVMe in use. 128 GB V30/A2 microSD ordered; owner decision: recordings go on it after write qualification | `experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md` §A, §F; `docs/D435I_CALIBRATION_PLAN.md` (PR #1) |
| 64 GB USB stick | Unusable for recording: USB 2.0, 1.09 MB/s with fsync (MEASURED) | addendum §6 |
| Power | Under-voltage on the 5 V / 3 A supply with both boards (MEASURED); 5.1 V / 5 A supply ordered | session facts §A; addendum §1 |
| D435i | New unit: SDK serial 317422076650, FW 5.17.3.10, BMI085. Evidence from old unit 243322073847 does not transfer | `experiments/2026-10-13-pi5-env-snapshot/ADDENDUM_CAMERA_SWAP.md` |
| Controller | STM32H7 owns balancing, control and safety; outside Phase-1 perception scope | project instructions |

## Gate picture

Gate names follow the project instructions (N0–N7). `docs/NATIVE_PI5_BASELINE_ARCHITECTURE.md` §4 numbers the ORB steps
differently (N4 EuRoC, N5 Pi build, N6 saved bag, N7 live); the calibration plan in PR #1 maps the two schemes.

| Gate | Status | Evidence / what is missing |
|---|---|---|
| N0 Platform | OPEN | Pi 5, Ubuntu 24.04, ROS 2 Jazzy run (MEASURED, `experiments/2026-10-13-pi5-env-snapshot/`); power is not stable |
| N1 D435i access (new unit) | OPEN | New-unit N1 stopped at the clock prerequisite, since fixed (session facts §B, §E) |
| N2 Raw IR + IMU qualification (new unit) | OPEN | Not run on the new unit. Old-unit September runs: `experiments/2026-09-12-*`, `experiments/2026-09-13-*` |
| N3 ROS 2 pipeline + record/replay | OPEN | Active gate, see `docs/NEXT_GATE.md` |
| N4A Known-dataset baseline (EuRoC MH01 on the Pi) | OPEN, strong evidence | 3 runs, ATE RMSE 0.0415 / 0.0368 / 0.0416 m, IMU initialized every run (`experiments/2026-10-13-n4a-euroc-mh01/REPORT.md`). Timing invalid because of throttling |
| N4B D435i offline stereo-inertial | OPEN | Programs built (`experiments/2026-10-13-n4b-d435i-prep/`). First offline run crashed on an upstream null-pointer bug; patch 4 rebuild unfinished (addendum §5) |
| N4C D435i live | OPEN | Not attempted |
| N5–N7 | Not started | — |

## Current blocking question

Can the Pi sustain the full D435i stereo-inertial stream without dropped frames? Two measured causes come first:
under-voltage, and the card's sustained write rate (16.6 MB/s against 18.4 MB/s needed). Recording into RAM gave
0 dropped frames over 15 s as a workaround (addendum §3–§4).

## Evidence quality rule

A screenshot, successful build, or one successful launch is not enough to promote a gate to PASS.
