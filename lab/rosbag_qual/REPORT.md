# T4 report — ROS 2 rosbag qualification

## Built

Implemented under the owned path `lab/rosbag_qual/`:

- `record_check.py`: bounded explicit-topic SQLite/MCAP recording with QoS
  overrides, command capture, parameter dump, per-topic QoS output and offline
  analysis.
- `analyze_bag.py` and `bag_core.py`: offline SQLite parsing with handwritten
  little-endian CDR header extraction; optional `rosbag2_py` fallback for MCAP.
  Header-stamp and bag-receive clocks are kept as separate measurements.
- `replay_check.py`: live-domain RealSense-node guard, separate replay-domain
  `rclpy` subscriber, playback rates, count checks and exact stamp-sequence
  preservation check.
- `config.json` and `qos_overrides.yaml`: the single threshold source and
  explicit sensor-compatible QoS contract.
- `tests/test_qual.py`: synthetic pass/fail/blocked fixtures plus a real saved
  DB3-input fixture when the shared 2026-10-14 evidence is available.

## Verification

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s
lab/rosbag_qual/tests -v` passes 5 tests. The tests cover PASS, FAIL from a
large header gap, FAIL from a header-stamp reversal, BLOCKED from a missing
bag, analyze-only re-evaluation, and the saved real DB3 input. Output is in
`tests/last-run.log`.

This is **MEASURED** software-test evidence only. No camera, ROS graph, Pi,
storage device, replay process, power state or thermal state was used in this
worktree verification.

## Open risks and known limits

- MCAP analysis depends on a Pi installation that provides `rosbag2_py`; the
  stdlib fallback intentionally supports SQLite `.db3` only.
- The CDR fallback extracts headers and does not claim full payload semantic
  validation. ROS-side `rclpy` replay subscriptions validate delivery and type
  loading, while image content and calibration remain outside this ticket.
- The default profile is the requested stereo IR profile. It must be changed
  in the config if the accepted driver profile publishes only IR1 or uses
  `image_raw`; changing topics without saving the resulting config would make
  the evidence non-reproducible.
- A fixture PASS is not an N3 gate PASS. Physical review still needs current
  Pi power, thermal, USB, storage and driver evidence, as required by the
  common rules.
- The inherited 18.4 MB/s storage threshold is retained as a current
  SOURCE-SUPPORTED demand ceiling; it is not a new storage measurement.

Proposed commit message: `Add offline rosbag record and replay qualification tooling`

