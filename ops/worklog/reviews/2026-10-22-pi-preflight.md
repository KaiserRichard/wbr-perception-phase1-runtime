# Pi preflight and lab-runbook review — 2026-10-22

## Result

The Pi is reachable over direct Ethernet and the physical/software prerequisites
checked today are present. This is a read-only readiness check; it does **not**
verify live camera frames, ORB tracking, a new recording, offline map replay, or
Foxglove rendering.

## Evidence checked

- Bounded SSH to `wbr-pi5` (`192.168.50.2`) succeeded from Mac `en7`
  (`192.168.50.1`): Pi 5, aarch64, Ubuntu 24.04.4, 3.9 GiB RAM, 80 GiB free.
- Pi reported `EXT5V_V=5.16704000V`, `throttled=0x0`, and 51.0 °C.
- D435i serial `317422076650`, firmware `5.17.3.10`, enumerated over USB at
  `5000M`.
- Evidence storage resolves to `/dev/mmcblk0p2`. ROS 2 Jazzy executables,
  marked-loop runner, stereo settings, vocabulary, sparse-map node and replay
  helper were present at the documented paths.
- `codex-i` independently reviewed the runbook. Its stale SSH-timeout status was
  removed, while the distinction between enumeration and active tracking was
  retained. `codex-k` could not open SSH from its own restricted shell; the same
  bounded read-only check succeeded from the Mac host.

## Runbook correction and validation

The first ROS setup attempt failed because Bash `nounset` was enabled before
sourcing `/opt/ros/jazzy/setup.bash` (`AMENT_TRACE_SETUP_FILES` was unset). The
runbook now sources ROS with nounset disabled, then enables `-e` and `pipefail`.
It also records the current Ethernet/preflight values and leaves capture/replay
steps explicitly unverified.

- All 14 fenced Bash blocks in `LAB_DAY_EXECUTION.md` pass `bash -n`.
- `git diff --check` passes; `ops/worklog/CURRENT.md` is 40 lines.
- No camera node, recorder, replay, installation/build, or motor/STM32 command
  was run. No Pi files were changed.

## Claude handoff

Please review `LAB_DAY_EXECUTION.md` for the updated preflight values and ROS
shell-order correction; live streaming, tracking, capture and map replay remain
to be verified during the lab session.
