# 2026-10-21 camera replay metrics (codex-g worker)

- Branch/worktree: `chatgpt/20261021-camera-replay-metrics`, isolated
  `/Users/quockaiser/.codex/worktrees/camera-replay-metrics/wbr-lab-ops`.
- Read AGENTS, CURRENT, USER_PROFILE, root/camera-day/ROS READMEs and
  `ros2/wbr_orb_node/src/d435_node.cpp`. Status has source stamps, state,
  publication flag and cumulative counts, but no steady processing timing.
- Added only the authorized analyzer, focused tests, REPLAY_METRICS.md and this
  session. Documentation describes formulas/assumptions/worked example, CLI,
  conservative optional CSV headers, missing-output/coverage limits and loop
  evidence. Central logs/CURRENT and protected exercises were not changed.
- Read-only SSH via `wbr-pi5`: inspected `Tracking.h`, `LoopClosing.cc`, source
  revision and SHA-256 under `/home/richard/orbslam3/ORB_SLAM3`. Revision
  `727f3cbd79482af0360447a26b906950c84ce61c`; LoopClosing SHA-256
  `50c5a4ca6e5618bec11759f87610c56aaea1bef7bd4c82909f37d0bc0ff2b7b1`.
  No remote writes/builds/launches. Source inspection is not binary provenance.
- Verified `*Loop detected` is positive detection; `PR: Loop detected with
  Reffine Sim3` occurs below the coincidence threshold. Detection can be rejected
  by `BAD LOOP!!!`; no direct correction-completed stdout marker at the end of
  CorrectLoop. Merge and GBA/map-update events stay separate. Missing/partial
  logs yield unknown, not no. Complete logs support only no observed detection.
- Built and ran the real analyzer before tests. Initial synthetic evidence:
  `/private/tmp/wbr-replay-metrics-synthetic-l82_wna4`. Its moving fixture comment
  incorrectly described endpoint/path; actual coordinates produced 0 m and
  9.2360679775 m. Preserved that evidence; made a new explicit fixture below.
- Final **SYNTHETIC**, not hardware, three-replay CLI run: exit 0. Inputs, exact
  invocation `command.txt`, stdout/stderr and JSON/Markdown reports retained in
  `/private/tmp/wbr-replay-metrics-synthetic-final-spjwe7re/`.
  - Moving: endpoint 1 m, path 7 m, 14.285714%; positive detection; correction
    unknown; 5 processedFPS, 3 trackedFPS over measured synthetic 1 s; one loss
    episode, two frames without a pose, zero missing status rows.
  - Static: endpoint/path 0 m, percentage unavailable (degenerate); complete
    synthetic log has only a candidate, so no observed detection; FPS/loss unknown.
  - Partial: observed endpoint/path 5 m, 100%; no log/timing/state evidence, so
    loop/FPS/loss unknown; full replay endpoint interpretation unavailable.
- Exact required check:
  `python3 -m unittest discover -s scripts/camera_day/tests -p test_replay_metrics.py -v`
  passed 18 tests (initial 0.945 s, final 0.895 s). Final stdout/stderr saved as
  `focused-tests.stdout.txt` / `focused-tests.stderr.txt` in the final fixture
  directory. Review found error notes could interrupt the Markdown table;
  moved notes after all rows and added a contiguous-table regression assertion.
- Limitations: no actual camera-day3 trajectories supplied/analyzed; no real FPS,
  hardware accuracy or successful physical-loop claim. CSV is independent of
  unfinished native instrumentation. PoseStamped requires an external TUM export.
  No heavy simulation/training, hardware command, calibration, firmware or
  evidence rewrite. Worker opens PR; conductor independently runs and merges
  after green CI.
