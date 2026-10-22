# Pi setup preflight — 2026-10-22

- Read-only setup check from the Mac; no recording, replay, package install,
  camera launch, or motor/STM32 command.
- `ssh -G wbr-pi5`: `192.168.50.2`; Mac `en7`: `192.168.50.1`. One bounded,
  strict-host-key SSH check succeeded: `wbr-pi5`, aarch64, Ubuntu 24.04.4,
  3.9 GiB RAM, 80 GiB free on `/`.
- Pi read-only values: EXT5V 5.16704000 V; `throttled=0x0`; 51.0 °C. D435i
  serial `317422076650`, FW 5.17.3.10, enumerated at USB 5000M.
- Evidence path resolves to `/dev/mmcblk0p2`. ROS Jazzy executables
  `d435_node`/`orb_node`, marked-loop capture runner, stereo settings, ORB
  vocabulary, isolated sparse-map node, and replay helper all exist.
- First combined check stopped at `source /opt/ros/jazzy/setup.bash` because
  Bash nounset was enabled (`AMENT_TRACE_SETUP_FILES` unbound). A new bounded
  read-only SSH check without nounset completed. Runbook now uses `set +u` before
  ROS setup and `set -eo pipefail` afterward.
- Codex-I read-only audit confirmed the old timeout status was stale and that
  camera enumeration/package listing do not prove an active stream/tracking.
  Codex-K was also asked for a bounded read-only check; its own sandbox initially
  rejected the SSH stdin setup, so the conductor performed the successful check.
- Updated `LAB_DAY_EXECUTION.md` to record today's preflight and remaining
  unverified work. All 14 fenced Bash blocks pass `bash -n`; `git diff --check`
  passes. No source or calibration files changed.

- Owner supplied newer A evidence. Read-only inspection confirms 362 matched
  stereo pairs in a 212.6 MiB MCAP, process exits 0 and ORB initialization with
  225 points. Existing 20-source-second replay passed: 300 poses/statuses,
  20/20 nonempty clouds, max 214 points, retained map MCAP.
- A duplicate replay attempt stopped at the existing-output guard before the
  helper ran. No new replay or capture was launched by this check.
- Archived small text/JSON evidence outside git; archive path/hash in the review.
  Runbook/CURRENT corrected; Codex reviews software, owner/execution chat runs
  lab commands and decides experiments. Live continuity and GUI remain unverified.
