# ROS 2 rosbag record/replay qualification

This directory implements the N3 record/replay check as three Python 3.11+
CLIs. It is software-only on the Mac and uses the same explicit IR/IMU topic
and QoS conventions as the existing N3 preparation material. The default
profile records both IR cameras; the configuration must match the profile
actually launched on the Pi (including whether topics are `image_rect_raw` or
`image_raw`). All acceptance numbers are in [config.json](config.json), with a
source or rationale beside each threshold.

## Pi commands

Run from the repository root after sourcing ROS 2 Jazzy. Keep the camera in
ROS domain 42 for recording. The configured node must be `/camera/camera`.

```sh
source /opt/ros/jazzy/setup.bash
ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 python3 lab/rosbag_qual/record_check.py \
  --config lab/rosbag_qual/config.json \
  --output-dir /path/to/evidence/record
```

The recorder uses the configured SQLite or MCAP storage plugin, explicit
`qos_overrides.yaml`, configured topic names, and a bounded duration. It saves
the exact command, recorder log, `ros2 bag info`, camera `ros2 param dump`, and
`ros2 topic info -v` output for every configured topic. A stopped camera is
required before replay:

```sh
source /opt/ros/jazzy/setup.bash
ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 python3 lab/rosbag_qual/replay_check.py \
  --config lab/rosbag_qual/config.json \
  --bag /path/to/evidence/record/bag \
  --output-dir /path/to/evidence/replay \
  --live-domain 42 --replay-domain 43
```

`replay_check` checks the live domain with `ros2 node list` and BLOCKS if a
RealSense or configured camera node remains. It then creates lazy `rclpy`
subscribers in the separate replay domain, runs `ros2 bag play`, measures
received rates, and compares message counts, header-stamp sequence hashes and
rates with the offline recording. If `rosbag2_py` is installed, MCAP can be
analyzed through its reader; SQLite `.db3` is always parsed offline with the
stdlib parser.

For a bag already on disk, with no ROS graph:

```sh
python3 lab/rosbag_qual/analyze_bag.py \
  --config lab/rosbag_qual/config.json \
  --bag /path/to/bag \
  --output-dir /path/to/evidence/analyze
python3 lab/rosbag_qual/analyze_bag.py \
  --config lab/rosbag_qual/config.json \
  --analyze-only /path/to/evidence/analyze
```

The second command re-evaluates saved `analysis.json`; it does not start ROS
or reopen a live graph. Each check writes `result.json` using the required
PASS/FAIL/BLOCKED contract and prints a short table. Exit codes are 0, 1 and 2
for PASS, FAIL and BLOCKED.

## Criteria and limits

- Per topic: configured presence/count, rate from `header.stamp`, bag receive
  rate from `messages.timestamp`, header-stamp reversals, and gaps exceeding
  `drop_gap_factor × nominal period`. These clocks are reported separately and
  are never subtracted from each other.
- IR pairing: exact left/right header-stamp pairing fraction.
- IMU: gyro and accel are independent configured topics, so their rates and
  timestamp continuity are checked separately; a combined IMU is not inferred.
- Disk: total bag bytes divided by the receive-time duration, compared with the
  configured storage demand ceiling.
- Replay: received rate, count fraction and exact header-stamp sequence hash.

Passing a synthetic fixture proves only the analyzer/tooling behavior. It does
not prove Pi storage margin, USB stability, RealSense driver QoS compatibility,
power, thermal behavior, calibration, IMU alignment, or a physical N3 gate
PASS. A result with status `PASS` is still evidence for review under the
project’s gate rules.

## Tests

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s lab/rosbag_qual/tests -v
```

The unit tests generate tiny SQLite bags with hand-written CDR `Image` and
`Imu` messages for PASS, dropped-gap, reversed-stamp and BLOCKED paths. When
present, the test also reads (without copying or modifying) the saved
2026-10-14 DB3 evidence as a real-input fixture. Test output is recorded in
`tests/last-run.log` in this worktree.

