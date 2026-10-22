# Pi preflight and lab-runbook review — 2026-10-22

## Result

The Pi is reachable over direct Ethernet and the physical/software prerequisites
checked today are present. A subsequent read-only inspection confirms today's
completed Scenario A stereo capture and first-20-second sparse-map replay.
Foxglove rendering, live tracking continuity and moving captures remain unverified.

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
It also records the current Ethernet/preflight values and completed A evidence,
and prevents accidental repetition of A into its existing output directory.

- All 14 fenced Bash blocks in `LAB_DAY_EXECUTION.md` pass `bash -n`.
- `git diff --check` passes; `ops/worklog/CURRENT.md` is 40 lines.
- No camera node, recorder, replay, installation/build, or motor/STM32 command
  was run. No Pi files were changed.

## Claude handoff

Please review `LAB_DAY_EXECUTION.md`: ROS shell order is fixed, today's A
capture and 20-second map replay are verified from saved artifacts, while
Foxglove rendering, live tracking continuity and B/C remain unverified.

## Newer Scenario A evidence (owner correction)

- Saved run: `/home/richard/wbr-evidence/camera-day-20261022-01/A-stationary`.
- Capture at 08:24–08:25 +07: 25.015 s recording window, 24.070 s MCAP span,
  212.6 MiB, 362 images and CameraInfo per side, matching headers, 14.999 Hz,
  zero estimated internal gaps; all three processes exited 0. Live ORB logged
  initialization with 225 points and a pre-recording pose was retained.
- Existing replay at 08:36–08:37 +07: `passed:true`, 300 poses/statuses,
  20/20 nonempty clouds, max 214 finite landmarks in `slam_world`; input stamps
  match and application-dropped count is 0 for this paced offline replay.
  Separate map MCAP is 176.5 KiB. This is not a live throughput measurement.
- Capture logs do not establish continuous live tracking. Pixel content and
  Foxglove GUI have not been visually reviewed by Codex.
- Read-only evidence archive on Mac:
  `~/wbr-evidence-archive/camera-day-20261022-01/read-only-review-20261022/scenario-a-evidence.json`.
  SHA-256: `d620fb173285634cbf1c0e24a4c772bcc6f1595356ef64ff959b73ccd4d070de`.
- One attempted duplicate replay invocation stopped at the existing-output
  guard before the replay helper ran. No new replay or live capture was started.
- Execution division: Codex fixes/reviews software and documentation; the owner
  and execution chat run lab commands and make experiment decisions.
