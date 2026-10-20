# Current state

Last updated: 2026-10-20 09:40 +07 by Claude (seeded from the 2026-10-20 lab handoffs)

## Active goal
N0–N3 hardware evidence on the Pi with the lab tools in `lab/`. No gate is PASS;
N0–N3 remain OPEN (see `docs/PROJECT_STATE.md`).

## Hardware right now
- Camera attached: **Intel RealSense D435 (no IMU)**, SDK serial 048622071151,
  firmware 5.17.3.10, USB 8086:0b07. Owner swapped it in on 2026-10-20 because the
  D435i (serial 317422076650) is in use for another project. UNKNOWN whether and when
  the D435i returns.
- Pi 5 on 27 W supply; boot and data on the 32 GB microSD, root 29 GB with 6.1 GB
  free (MEASURED 2026-10-20). The 128 GB microSD is not installed yet.
- Network: direct Ethernet Mac 192.168.50.1 <-> Pi 192.168.50.2.
  `ssh richard@192.168.50.2` works; a `Host wbr-pi5` entry in `~/.ssh/config` may
  still be missing (only `wbr-pi5-wifi` existed).

## Evidence so far (latest first)
- 2026-10-20 card A, idle, D435 attached: tool PASS, exit 0, all ten criteria PASS.
  Pi `/home/richard/wbr-evidence/power-idle-d435-20261020-01`, Mac
  `~/wbr-evidence-archive/power-idle-d435-20261020-01` (731/731 SHA-256 OK).
  Session config `~/wbr-evidence/configs/power_usb_d435_0b07.yaml` (usb_identity only).
  Covers idle only, not streaming load, not D435i evidence.

## Blockers
1. No camera IMU: the D435 cannot provide the stereo-inertial input that N2–N4 need.
2. `pyrealsense2` missing on the Pi (`ModuleNotFoundError`): card B blocked.
3. Storage: 6.1 GB free on root; any recording needs the 128 GB card (and its write
   qualification, `docs/STORAGE_QUALIFICATION_DRAFT.md`, pending owner review).

## Open questions for the owner
- Is the D435i coming back, and when? This decides whether the plan waits for it or
  changes to a stereo-only or body-IMU path (a research-plan change: needs Claude review).

## Next step
Decide the D435i question. Meanwhile, low-risk work that does not depend on it:
the 32 GB -> 128 GB card migration (`wbr-storage-migrate`) and a plan for installing
a version-matched `pyrealsense2` (review before installing).
