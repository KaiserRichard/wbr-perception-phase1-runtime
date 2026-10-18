# T27 completion report

Built only under `ros2/wbr_perception_bringup/`; no existing tool, upstream
source, project-state document or other ticket path was modified. No git
write command, network, package install, GUI, SSH, camera or physical UART was
used. Changes are intentionally uncommitted for the conductor.

## Implementation

- Ament Python metadata, installed launch/config resources, and
  `perception_stack.launch.py` with all requested arguments plus bag, repository,
  output and ORB parameter paths.
- A ROS-independent planner selects exactly one source, defines subscription
  and first-message barriers, binds live/replay clock policy, adds ORB -> health
  -> optional recorder -> profiler, and defines reverse teardown and required
  exit policy. ORB is executed directly so profiler attachment uses its PID.
- A supervisor owns process groups, preserves raw command logs and receipts,
  checks required exits including successful exits/EOF, and performs sequential
  SIGINT/SIGTERM/SIGKILL teardown. Its exit reaches the launch `OnProcessExit`
  handler. One supervisor avoids ROS launch signaling independent children in
  parallel during shutdown.
- Runtime-only rclpy readiness subscriptions observe combined camera IMU and
  both IR topics. No ROS module is imported by the planner or offline analyzer.
- Growing ORB JSONL -> existing VIO `Converter` -> existing health
  `sender.process`, with existing serial transport or a file transport for
  `health_uart=none`. Unknown clocks, camera IMU initialization, feature counts
  and collapsed tracking-state information remain conservative.
- Existing profiler sampler reused by subprocess. Existing lab recording
  topic/storage/QoS contracts reused, with combined camera IMU added to recording
  and saved effective QoS. No bounded lab qualification runner is misused as a
  persistent required process.
- COMMON result schema, status/exit precedence, SHA-256 raw evidence inventory,
  human-readable table, and hardware-free `--analyze-only` reanalysis. Saved
  results are recomputed; stale `result.json` verdicts are ignored.

All new operational thresholds and their sources are in `config/stack.json`.
Host-only fixture deadlines are explicitly scoped in `tests/config.json`.

## Verification

Run from the worktree root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s ros2/wbr_perception_bringup/tests -v \
  > ros2/wbr_perception_bringup/tests/last-run.log 2>&1
```

MEASURED host verification is saved in `tests/last-run.log`. Tests cover
planner order/exclusion, sensor-only mode, none/device health selection,
live/replay clock policy, direct PID profiling, launch `OnProcessExit` wiring
through API doubles, real child lifecycles and reverse teardown, every required
process exiting, normal bag EOF, readiness timeout, absent ROS BLOCKED, raw-file
hashes/reanalysis, SIGTERM handling and SIGINT escalation. The actual existing
converter and sender emit decodable v3 frames in a file without opening UART.
Four real saved source epochs are retained verbatim with provenance; their
associated estimator/health values are synthetic or UNKNOWN.

Final MEASURED outcome: **22 unittest tests PASS** (including six individual
required-process exit scenarios within the corresponding test). Complete output
is in `tests/last-run.log`. The process-group permission-race regression also
passes: EPERM does not prove a group has disappeared and cannot abort cleanup.
Missing UART paths are BLOCKED by a read-only preflight check before opening
anything.

Additional successful checks: AST syntax for all nine Python files, XML/JSON
parsing, ament marker/launch resource presence, source whitespace, and
`PYTHONDONTWRITEBYTECODE=1 python3 setup.py check --metadata` from this package.
No shell script was added (`bash -n` is not applicable). These checks do not
substitute for colcon or ROS execution.

## Unverified and open risks

- UNKNOWN: colcon build/install, actual Jazzy launch behavior, real DDS traffic,
  native ORB linkage, and physical camera/UART/profiler/rosbag behavior. No
  hardware gate PASS is claimed.
- The camera package is on an unmerged branch. The exact required launch name
  is used with no guessed argument names. Its pinned profile, actual IR topic
  names, serial/firmware binding and combined-IMU publication must be checked
  when that branch is available. Missing dependencies BLOCK; missing messages
  time out before ORB. First-message presence cannot qualify IMU interpolation.
- The default ORB package can be a fake build; sourcing the intended real-ORB
  overlay and qualified vocabulary/settings remains a deployment prerequisite.
  The node's conservative initialization/feature sentinels remain UNKNOWN.
- The package deliberately disables source-age mapping. It cannot certify any
  camera/ROS/host/MCU clock relationship or authorize control eligibility.
- Recorder startup follows readiness/health, so startup traffic is omitted.
  Initial bag messages precede ORB subscription by design. EOF shuts down the
  stack and reports FAIL rather than claiming an operator-completed run.
- Process-exit monitoring does not detect a stalled publisher that stays alive.
  Externally launched publishers are not managed; separate replay/live ROS
  domains and independent sensor/recording qualification remain required.
- SIGKILL of the supervisor or host failure can leave children; process-group
  escape and uninterruptible kernel I/O defeat software-only cleanup. Outer
  launch shutdown grace exceeds all configured sequential teardown deadlines.
- Existing dependency issue observed, left unchanged per COMMON: the health
  sender's background heartbeat thread does not propagate a transport write
  exception to the foreground reader. During pose silence a UART write failure
  could leave that process alive. File mode and foreground pose writes are
  covered here; heartbeat-thread fault propagation needs an owner follow-up in
  `tools/perception_health/py/sender.py`. No existing tool was patched.
- ROS launch may exit successfully after a supervisor failure; the saved
  `result.json` and analyzer exit code are the authoritative orchestration
  result, not ROS launch's exit code.

Proposed commit message: `feat(bringup): orchestrate perception stack with readiness and ordered teardown`
