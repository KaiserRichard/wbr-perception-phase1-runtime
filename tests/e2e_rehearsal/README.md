# Synthetic end-to-end toolchain rehearsal

This software-only unittest suite checks the documented tool CLIs and their
machine-readable artifacts with generated SQLite/CDR fixtures. **One standard
ROS bag interface is blocked:** the existing exporter misaligns IMU doubles.
See [FINDINGS.md](FINDINGS.md), R26-01, and its expected-failure regression.
Later stages run using an explicitly named compatibility copy of the bag.

## Run on the Mac or Pi

From a full repository checkout, with Python 3.11+ (3.12 on Pi), the repository's
NumPy dependency, POSIX PTYs, bash and make already available:

```sh
make -C tests/e2e_rehearsal test
```

No ROS installation, camera, UART device, network or GUI is used. This command
writes `tests/last-run.log`, propagates Python failure through `tee` on both
older Mac make and Linux make, and normally finishes in about 12 seconds on
the review Mac, below the ticket's 120 second limit. The Pi duration is UNKNOWN.
Generated bags, trajectories, PNGs, raw PTY bytes, sender logs and health summary
are temporary and removed after each test. The review's expanded dependency
suite transcript is also recorded in `tests/last-run.log`; a new `make test`
replaces it with the rehearsal-only transcript.

## Pipeline and criteria

1. Generate two seconds of standard ROS 2 little-endian CDR: two textured
   640×480 mono8 IR topics at 30 Hz and separate gyro/accel topics at 200 Hz.
   The gyro is `(0.01, 0.02, 0.03)` rad/s and accel `(0, 0, 9.81)` m/s²;
   those are **ASSUMED** camera-IMU values, independent of the STM32 body IMU.
   `header.stamp` names an assumed synthetic D435i device clock; SQLite
   receive stamps name a separate assumed bag receive clock, related explicitly
   by `receive = bag_receive_start + clock_offset + round((header - device_header_start) * (1 + drift_ppm / 1e6))`.
2. Run `lab/rosbag_qual/analyze_bag.py --bag ... --config ... --output-dir ...`.
   Assert PASS in `result.json` and re-evaluate with `--analyze-only ...`.
   The generated config declares topic presence, rates, gaps, exact stereo
   pairing and a synthetic byte-rate ceiling; it does not qualify real storage.
3. Run `tools/stamp_drift/analyze.py <bag> --header-clock D435I_GLOBAL_TIME
   --global-time-enabled true --output-dir ...`. All four streams must exist,
   report PASS and recover the injected 1200 ppm within the configured tolerance.
   The global-time option is an assumption for this synthetic fixture.
4. Standard IMU export is tested separately as expected failure R26-01. For
   downstream exercise, copy the bag and change only IMU padding to match the
   exporter's legacy alignment. Run `tools/n4b_offline/db3_to_euroc.py <copy>
   <export>` and `qualify_euroc.py <export> --outdir ...`. Assert metadata,
   exported gyro/accel values and PASS. A one-nanosecond stereo fault must
   produce FAIL/exit 1; absent export inputs must produce BLOCKED/exit 2.
5. Generate fake ORB output and EuRoC ground truth on the exported timestamp
   grid. Complete orthogonal Fourier modes make the exact post-SE3 ATE
   `0.025 * sqrt(3/2) = 0.0306186218 m`; the configured tolerance is `1e-8 m`.
   Run `tools/eval_pipeline/accuracy/evaluate.py --sequence SYNTHETIC --runs ...
   --ground-truth ... --times ... --out ...` and assert `summary.json`.
   EuRoC ground-truth quaternions use wxyz; fake ORB trajectories use xyzw.
6. Feed a snapshot from the last fake pose through the direct
   `vio_to_pose_events.py --input ... --snapshot-session ...` CLI, then run the
   documented `sender.py --device <PTY> --session-id 9` CLI. Missing or unusable
   mappings must yield HOLD with age/mapping flags clear. Start a persistent
   converter with `--clockmap ...` and explicit synthetic device-to-Pi
   `CLOCK_MONOTONIC_RAW` exchanges. Schedule the same last acquisition stamp
   into that map's send window; continue unavailable health reports during
   preparation. Valid mapping plus explicit OK/camera-IMU/reset/features and
   independent `primary_fresh=True` must yield FRESH. `health-summary.json`
   records decoded states/flags. CRC, frame completion and the shared sequence
   are checked; every heartbeat reaches the supervisor model.

All tool steps assert JSON artifacts, rather than stdout wording. Converter
stdout is its documented JSONL data interface and is saved before assertions.
Thresholds and synthetic parameters live in [config.json](config.json), with
sources; existing tool limits remain in their own configs.

## Regression evidence and limits

The main pipeline uses synthetic data only. A separate regression reuses the
repository's exact saved `tools/stamp_drift/tests/fixtures/real_ros_headers.json`
excerpt, rebuilding only its header prefixes and receive stamps in SQLite,
then running the drift CLI and saved-evidence analysis. These **MEASURED** bytes
come from a converted historical bag: zero fitted drift is a conversion artifact,
not live clock synchronization. No complete physical DB3 was found under the
permitted shared `experiments/` evidence directory.

The suite proves interface and arithmetic consistency within its stated
compatibility workaround. Passing fixtures is **not a gate PASS**. It cannot
prove standard ROS export until R26-01 is fixed, ROS graph behavior, sensor
cadence, physical clock identities, calibration, camera–IMU alignment, ORB-SLAM3
execution, Pi timing/storage/power, UART throughput, STM32 firmware or safety.
