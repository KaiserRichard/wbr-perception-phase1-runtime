# Terrain advisory topic

- Branch: `claude2/20261025-advisory-topic`; local uncommitted changes only.
- Added `/terrain_advisory` as Best Effort depth 1 `Float64MultiArray`, default
  10 Hz processed-frame rate, parameterized by `advisory_topic`.
- Fixed data order: code, front distance, height, width, confidence, plane-valid,
  monotonic sequence, and Pi monotonic receipt-to-publish age. Missing values are
  finite zeros; existing ROS outputs and binary codec remain in place.
- Added interface contract and an illustrative STM32H723 rclc subscriber with
  finite/length/code checks, local HAL tick freshness, wrap-safe 300 ms timeout,
  and `UNCERTAIN` safe default. The example is not compiled here.
- Ran `PATH=/private/tmp/claude-501/-Users-quockaiser-Desktop-Research-wbr-wt-claude2/86f1e3fb-27f1-4b36-ad4d-133cc09819f7/scratchpad/venv/bin:$PATH python3 -m pytest -q ros2/wbr_obstacle_node`: **7 passed in 0.37s**.
- `git diff --check` passed. No ROS runtime, Pi transport, STM32 build, or hardware
  test was requested or run.
