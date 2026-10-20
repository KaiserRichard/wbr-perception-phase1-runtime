# Current state

Last updated: 2026-10-20 11:02 +07 by Codex, after owner relayed Claude approval of DOC-20261020-1. See DOC-20261020-2 and decisions D-20261020-10 through -15.

## Active goal
Simulation / control: approved two-stage plan: reduced planar six-state gain-parity/re-synthesis, then full planar five-bar MuJoCo/VMC before RL. Branch: `chatgpt/20261020-simulation-control`; initial base `6929fb4`.
No controller implementation or MuJoCo run yet. No gate is PASS; N0–N3 remain OPEN.

## Hardware right now
- USER-REPORTED: the owner's physical WBR assemblies are not available yet; weighing and balance-test COM measurements are deferred. CAD/BOM availability remains UNKNOWN.
- Last checked camera: D435 without IMU, SDK serial 048622071151, firmware 5.17.3.10, USB 8086:0b07 at 5000M. D435i is used elsewhere; return date UNKNOWN.
- Last checked Pi 5 storage: 32 GB microSD, root 29G with 6.2G free. 128 GB migration is incomplete.
- USER-REPORTED: Win32 Disk Imager reading the 32 GB card to `D:\wbr-backup\wbr-pi5-32gb-20261020.img` at 8.5–8.8 MB/s. Completion and verification UNKNOWN; keep original card.
- SSH alias is configured: `wbr-pi5` -> `richard@192.168.50.2`. Alias resolution verified; connectivity not retested during card imaging.

## Evidence so far (latest first)
- SOURCE-SUPPORTED: DM-jump commit `6855ef8c6da20246251cfd473467c04112bf800f` supplies six-state, two-output LQR/VMC with gains scheduled by virtual leg length; code is in `User/APP/chassis[RL]_task.c` and `User/Algorithm/VMC/`, not the generic `User/Controller/` library.
- Code constants: links 75/140/140/75 mm, pivot spacing 80 mm, observer wheel radius 60.3 mm; wheel clamp ±2 N·m, joint clamp ±7 N·m, force clamp ±100 N. These are not verified physical measurements.
- CALCULATED: gain schedule evaluated at four leg lengths; VMC Jacobian matched finite differences at three poses (max absolute error 6.90e-9). No firmware execution or balancing test.
- 2026-10-20 card A, idle, D435 attached: tool PASS, exit 0, all ten criteria PASS.
  Pi `/home/richard/wbr-evidence/power-idle-d435-20261020-01`, Mac
  `~/wbr-evidence-archive/power-idle-d435-20261020-01` (731/731 SHA-256 OK).
  Session config `~/wbr-evidence/configs/power_usb_d435_0b07.yaml` (usb_identity only).
  Covers idle only, not streaming load, not D435i evidence.

## Blockers
1. Actual masses/COM/inertias, actuator response, measured timing, flashed firmware revision and original LQR A/B/Q/R/generation scripts remain UNKNOWN.
2. Architecture is approved, but compiled upstream C/Python parity and both model stages are not implemented. Earlier four-state scope stays archived.
3. MuJoCo/SciPy absent; Python 3.12 available. No dependencies installed.
4. Parallel lab: card B remains BLOCKED (missing pyrealsense2; no fallback today); 128 GB migration and recording write qualification incomplete.

## Open questions for the owner
- Can the lab supply CAD/mass properties, body/leg BOM and component specifications, plus the upstream LQR-generation files? Physical measurements wait until assemblies exist.
- Which source revision and actuator configuration should the eventual WBR use? No owned robot's flashed revision or hardware performance is established.

## Next step
First implementation milestone: compile pinned upstream gain-schedule/VMC C functions locally and compare the Python port on shared vectors; preserve applicable MIT notices. Then stage 1 physics/re-synthesis and stage 2 full planar five-bar/VMC validation.
Mass sweeps are sensitivity only. Every document change is logged; owner authorized publication and conditional merge of the reviewed documentation, not new controller code. Publication receipts are in the session log/PR history.
