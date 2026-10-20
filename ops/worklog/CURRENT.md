# Current state

Last updated: 2026-10-20 13:38 +07 by codex-f conductor.

## Active goal
- Parallel tracks: stereo ORB-SLAM3 -> ROS 2 pose; ASSUMED reduced six-state MuJoCo -> newly synthesized LQR -> push recovery.
- Conductor independently runs worker results and merges green PRs; Claude reviews completed milestones only.
- Gain exercise `sim/parity/student.py` remains owner-only. Parity scaffold compiled; 15 infrastructure tests pass; Python gain/VMC parity remain incomplete.

## Hardware right now
- USER-REPORTED this afternoon: no camera available; only a 4 GB Pi, slow 32 GB microSD and STM32. Live-camera milestone cannot run today without a camera.
- SSH `wbr-pi5` -> richard@192.168.50.2 timed out; current Pi model/network identity UNKNOWN. Owner asked about power/Ethernet/address.
- Keep STM32 untouched. No disk migration or deletion authorized.
- Earlier D435 idle power/USB evidence remains historical, not current 4 GB Pi evidence. Archive: ~/wbr-evidence-archive/power-idle-d435-20261020-01 (731/731 hashes verified in prior session).
- 128 GB migration completion remains UNKNOWN; original 32 GB backup must be preserved.

## Workers
- codex-g / gpt-6-astra ultra: isolated pi-orbslam-pose worktree, branch chatgpt/20261020-pi-orbslam-pose; bounded SSH and offline wrapper preparation while hardware absent.
- codex-i / gpt-6-astra ultra: isolated sim-lqr-push worktree, branch chatgpt/20261020-sim-lqr-push; implement and run MuJoCo balance/push and open-loop control.
- g/i latest sessions completed and no active task children found before launch. k has interactive session; not used. f is conductor only.

## Known limitations
- Body/leg masses, COM, inertias, actuator response and real robot LQR generation remain UNKNOWN; sim assumptions must be explicit and replaceable from one config.
- Parity is still pending, independently of the newly authorized running simulation work. No source-controller reproduction or sim-to-real validation claimed.
- Local full-suite prior failure: macOS lacks termios 460800 baud in existing link-bench test. Linux CI for parity scaffold bc4aea5 was green.
- No gate promoted; no hardware control or RL training.

## Next step
Conductor updates AGENTS conducting rules and integrates parity scaffold, verifies worker commands, merges only after green CI. Await Pi SSH details; no camera needed for Mac simulation. Final milestone review lists actual merged PRs and runs; never label blocked prep as completed pose/balance.
