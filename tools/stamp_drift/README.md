# `stamp_drift`

This tool diagnoses the relationship between a D435i ROS message's
`header.stamp` and the rosbag2 recorder's host receive timestamp. It fits

```text
receive = a + (1 + d) * header_stamp
```

per topic, reports `d` in ppm, robust residual distributions, a lower-envelope
receive-minus-header proxy, reversals, possible residual steps, and pairwise
inter-topic drift differences. `IR` and `IMU` pairings are called out when the
topic names make those classes recognizable.

The JSON also has a diagnostic-only `diagnostic_status`: `PASS` means all
topics had usable fits without detected reversals/steps, `FAIL` means a fit had
a detected reversal or possible step, and `BLOCKED` means a topic lacked the
minimum samples for a fit. These statuses are not hardware or N3 gate verdicts.

The fit reuses the centered affine fitter from `tools/clockmap`; iterative MAD
rejection is applied around that fit. It does not modify `tools/clockmap`.
The JSON records both the selected `header_stamp` interpretation and a derived
`global_time_enabled` declaration (`true`, `false`, or `null` when unknown).

## Input and exact commands

CSV input requires these columns (extra columns are allowed):

```csv
topic,header_stamp_ns,receive_ns
/camera/infra1/image_rect_raw,1700000000000000000,2200000000
```

For a rosbag2 SQLite bag, pass the `.db3` file. The reader uses the `topics`
and `messages` tables, parses the first `std_msgs/Header` from CDR, and uses
`messages.timestamp` as the receive timestamp. It supports CDR little- and
big-endian encapsulation; no ROS Python packages are required.

On the Pi, after recording has stopped and the bag is finalized:

```sh
cd /path/to/wbr-perception-phase1-runtime
python3 tools/stamp_drift/analyze.py /qualified/path/bag_0.db3 \
  --header-clock D435I_GLOBAL_TIME \
  --json-out /qualified/path/stamp-drift/report.json \
  --md-out /qualified/path/stamp-drift/report.md
```

Use `D435I_GLOBAL_TIME` only when the run manifest/parameter readback records
that `realsense2_camera` `global_time_enabled` was enabled and effective. Use
`D435I_HARDWARE_TIME`, `SYSTEM_TIME`, or `UNKNOWN` otherwise; this option is
metadata and does not convert either clock.

On a Mac or another offline host:

```sh
python3 tools/stamp_drift/analyze.py timestamps.csv \
  --header-clock D435I_GLOBAL_TIME --json-out report.json --md-out report.md
python3 tools/stamp_drift/analyze.py --analyze-only saved-report-input \
  --header-clock D435I_GLOBAL_TIME
```

The `--analyze-only` form reads exactly one `.csv` or `.db3` in the directory
and writes `report.json` and `report.md` there. Exit 0 means analysis and report
writing completed; exit 2 means malformed input or fit/read failure.

## Reading the report

`drift_ppm` is the fitted receive-clock rate minus the header-clock rate. The
residual percentiles are fit residuals and should be read as centered jitter.
`lower_envelope_proxy_ns` is the minimum observed `receive_ns - header_stamp_ns`.
It is approximately offset plus minimum transport delay only under additional
assumptions. A fit cannot separate absolute latency from clock offset without a
two-way exchange or an independently known clock mapping. It also cannot prove
exposure-to-arrival latency, camera–IMU physical timing, timestamp-domain
selection, ROS QoS behavior, or a hardware gate.

Backward/non-increasing header stamps split the fit and are reported as a
possible global-time reset. Receive-time reversals are reported separately as a
possible recorder ordering problem. A monotonic forward residual step is
reported as a possible clock/transport discontinuity; inspect raw rows,
`global_time_enabled`, driver logs, and bag metadata before calling it a reset.

All numerical detector thresholds are in [`config.json`](config.json), with a
`source` and `rationale` for each. They are **PROPOSED diagnostics**, not N3
acceptance limits.

## Evidence and limitations

The checked-in `tests/fixtures/real_saved_evidence.csv` is adapted from the
measured D435i timing-probe rows at
`experiments/2026-09-13-d435i-post-reboot-20260913T023833Z/pi/timing-probe/data/frames.jsonl`.
That source has paired SDK `Global Time` and host `CLOCK_MONOTONIC` observations,
not ROS `header.stamp` and DB3 receive rows. The fixture therefore validates the
CSV reader and real-scale integer handling, but is **not** ROS bag evidence.
No qualifying `.db3` with both clocks was present in the shared checkout when
this tool was built. A future physical run must preserve the bag, parameter
readback, and effective timestamp-domain evidence.

