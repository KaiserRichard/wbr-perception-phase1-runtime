# T19 report — stamp drift analyzer

## Built

- Added `tools/stamp_drift/analyze.py` for CSV and rosbag2 SQLite `.db3` input.
- Added a stdlib SQLite/CDR `std_msgs/Header` parser for little- and big-endian
  serialized messages.
- Added centered affine fitting through `tools.clockmap._fit_affine`, iterative
  MAD outlier rejection, per-topic drift/residual/proxy statistics, reversal and
  residual-step diagnostics, and inter-topic/IR-vs-IMU drift comparison.
- Added JSON and Markdown report generation, explicit clock-domain metadata, and
  the single threshold/rationale file `config.json`.
- Added diagnostic-only `PASS`/`FAIL`/`BLOCKED` statuses for clean fits,
  detected discontinuities, and insufficient samples; these are not hardware
  gate verdicts.
- Added synthetic PASS/FAIL-shaped diagnostics and a fixture adapted from real
  saved D435i timing evidence. No real rosbag2 DB3 containing both clocks was
  available in the shared checkout.

## Verification

Run:

```sh
python3 -m unittest discover -s tools/stamp_drift/tests -v
```

The command output is saved in `tests/last-run.log` for this worktree. The tests
cover diagnostic `PASS`, `FAIL`, and `BLOCKED` paths; known offset/drift with
jitter and outliers; a forward residual step; a header-stamp reversal;
inter-topic comparison; malformed CSV; real-scale measured-evidence fixture
parsing; and a synthetic SQLite/CDR bag.

Evidence label: **MEASURED** for the adapted source rows and **CALCULATED** for
all analyzer output. Synthetic recovery is a tooling check, not a hardware gate
PASS.

## Not verified / open risks

- No Pi, camera, serial device, ROS daemon, or hardware was accessed.
- No actual `.db3` with ROS `header.stamp` and `messages.timestamp` was available,
  so DB3 behavior is tested only with a synthetic schema and CDR payload.
- The analyzer cannot identify whether a ROS `header.stamp` is D435i global,
  hardware, or system time without run configuration/readback; the CLI records
  the operator's declared interpretation and does not infer it.
- Offset, transport delay, jitter, SDK global-time mapping error, and exposure
  timing are not separately identifiable from this one-way pair.
- A residual step is intentionally classified as possible clock/transport
  discontinuity; it is not automatically a global-time reset.
- The numeric detector settings are **PROPOSED** and are not N3/N7 acceptance
  thresholds.

Proposed commit message: `Add D435i ROS stamp drift analyzer`
