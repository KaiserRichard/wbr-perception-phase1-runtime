# Synthetic end-to-end toolchain rehearsal

This software-only test builds a temporary ROS 2 SQLite `.db3` bag using
hand-written CDR `Image` and `Imu` messages, then drives the existing tool CLIs
and checks their JSON outputs. No files generated during a run are retained
outside the temporary directory.

## Run

From the repository root:

```sh
make -C tests/e2e_rehearsal test
```

The command writes the unittest transcript to
`tests/e2e_rehearsal/tests/last-run.log`. Python standard library modules build
the bag and run the tests. `tools/stamp_drift` and the existing trajectory
evaluator use the repository's NumPy dependency. The synthetic bag contains
two 640×480 mono8 IR topics at 30 Hz, separate gyro and accel topics at 200 Hz,
and a 2 second sample window. Header stamps use an **ASSUMED synthetic device
clock**; SQLite receive stamps use a distinct **ASSUMED bag receive clock**.
The affine relation injects 1200 ppm drift and a configured offset. See
`config.json` for every synthetic value and test tolerance.

## Pipeline and assertions

1. `lab/rosbag_qual/analyze_bag.py --bag ... --config ... --output-dir ...`
   must write `result.json` with `PASS`. It checks CDR header decoding, the
   configured synthetic topic rates/gaps, monotonic stamps, exact IR pairing,
   bag receive span, and the configured synthetic byte-rate ceiling. The custom
   config adapts its profile to 30 Hz images and 200 Hz gyro/accel.
2. `tools/stamp_drift/analyze.py <bag> ... --output-dir ...` must write a
   passing result and report per-stream drift within the configured tolerance
   of the injected 1200 ppm. This tests affine-fit arithmetic across
   nanosecond epochs; it does not measure sensor/host synchronization.
3. `tools/n4b_offline/db3_to_euroc.py <bag> <out>` exports the four streams;
   `qualify_euroc.py <out> --outdir ...` must report `PASS`. The test also
   mutates a stereo timestamp to assert `FAIL` and supplies an absent export to
   assert `BLOCKED`. Separate gyro/accel topics do not reveal a RealSense
   driver's unite method; expected metadata is `UNKNOWN`.
4. A fake ORB output is generated from synthetic ground truth with deterministic
   translation noise. `tools/eval_pipeline/accuracy/evaluate.py` must write a
   passing `summary.json`; its SE3 ATE must recover the configured noise scale
   within tolerance. The fake output is not produced by ORB-SLAM3.
5. `vio_to_pose_events.py`'s converter creates one event without a mapping and
   one with an assumed synthetic camera-to-`CLOCK_MONOTONIC_RAW` exchange set.
   The documented sender CLI writes real protocol frames through a POSIX PTY;
   parsed payloads feed the existing supervisor model. The asserted states are
   `HOLD` without mapping and `FRESH` with valid mapped synthetic health and
   independent `primary_fresh=True`.

Assertions read `result.json`, `report.json`, `metadata.json`, and
`summary.json` artifacts. They do not rely on stdout wording. The unittest also
checks PASS/FAIL/BLOCKED result precedence. No compatible saved physical `.db3`
fixture was present in the shared evidence checkout, so the test is synthetic
only.

## What this proves and does not prove

**CALCULATED / ASSUMED:** the existing CLIs accept a common synthetic bag
shape, read the same CDR/header timestamps, export their expected intermediate
files, recover a deliberately injected drift/noise scale, and connect converter,
sender, PTY parser, and supervisor model interfaces. Test thresholds and
injected values are labelled in `config.json`; outputs from fixture runs are
not gate PASS evidence.

It does not prove any RealSense timestamp domain or offset, ROS graph behavior,
physical sensor cadence, camera calibration, camera–IMU alignment, actual
storage throughput, Pi timing, ORB-SLAM3 behavior, UART baud performance,
STM32 firmware behavior, or a project gate PASS. The test creates no hardware
access and writes no generated bag or trajectory into the repository.
