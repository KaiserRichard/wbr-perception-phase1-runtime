# Independent review — T3 calibration recording check

## Verdict

**APPROVE**

The implementation satisfies the T3 requirements within `lab/calib_record/`.
No confirmed correctness defect required a code change, so there are no fixes to
list. The checker is conservative about missing capture-time evidence: missing
manifests, post-capture storage receipts, Allan emitter readback, target
detection, unsupported bags, and unavailable decoded streams remain BLOCKED;
malformed supported evidence and failed acceptance checks fail.

## Review findings

1. **No confirmed findings.** The review checked threshold ownership and units,
   SDK versus host clock handling, domain transitions, full-take rates and gaps,
   frame continuity, stereo pairing, callback/bag agreement, checksum coverage,
   storage accounting, precedence, exit codes, missing-file behavior, and
   platform-independent paths. The code uses the existing `tools/take_tools`
   decoder/timing/stereo functions and `calibration/lab/pi/take_diagnostics.py`
   without modifying them.

## Requirements checked

- One saved camera–IMU or Allan take is analyzed offline; no device or recorder
  is opened.
- Completeness, original SHA-256 manifest coverage, identity/FW/profile and
  emitter readback are checked.
- Camera and Allan duration policies, whole-take rates, gaps and frame drops
  are evaluated from SDK timestamps.
- Camera excitation reports per-axis gyro RMS and accel population standard
  deviation using configured units and PROPOSED thresholds.
- Motion blur is a same-SDK-domain proxy; target detection is explicitly
  BLOCKED because the existing tools expose no AprilGrid detections.
- SDK, callback host-steady, callback host-realtime, writer/header and SDK
  host-system timelines are kept distinct; no cross-clock subtraction is used.
- Stereo uses unique frame numbers and configured same-domain SDK skew.
- Storage headroom and saved free-space receipts are labeled CALCULATED or
  BLOCKED/INFERRED as appropriate.
- `result.json` follows the PASS/FAIL/BLOCKED contract, including precedence
  and exit codes 0/1/2; usage/internal errors return 3.
- Tests cover PASS, FAIL and BLOCKED paths, including a fixture derived from
  real saved evidence.

## Test results after review

Exact commands and final output are recorded in `tests/last-run.log` for the
new suite. The review also ran these imported/relevant suites successfully:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s lab/calib_record/tests -v
  Ran 26 tests in 10.496s — OK
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/take_tools/tests -v
  Ran 20 tests in 5.047s — OK
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s calibration/lab/tests -v
  Ran 20 tests in 0.984s — OK
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s calibration/allan/tests -v
  Ran 12 tests in 32.539s — OK
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/calib_tools/tests -v
  Ran 16 tests in 0.821s — OK
```

The recorded fixture PASS is tooling verification only. No Pi, camera, serial
device, hardware timing, power, storage throughput, target visibility,
stationarity, or real calibration was verified.

## Remaining open items

- Run the checker against finalized new-unit Pi evidence with actual manifests,
  storage receipts, and Allan emitter readback.
- Add or integrate a trusted AprilGrid detection-count producer before treating
  a camera take as fully ready for Kalibr.
- Physically verify sustained storage, power/thermal cleanliness, and long-run
  Allan memory/runtime behavior.
