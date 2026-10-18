# T2 independent review — 2026-10-18

## Verdict

**APPROVE.** No confirmed implementation defect was found, so no code changes
were necessary. The implementation stays within `lab/d435i_raw/`, uses the
repository's existing SDK timing/parser helpers, and does not claim hardware
qualification from fixtures.

## Findings

No blocking or lower-ranked correctness findings.

## Requirements review

- **Bounded SDK capture and saved-data analysis:** present. The parent bounds
  its SDK child by requested duration plus configured grace, preserves timeout
  evidence, and replay avoids SDK loading/opening (`check.py:35-72, 75-107`).
- **Requested streams and identity:** exact serial/firmware/USB descriptor
  checks, stereo 848x480 Y8/30, emitter OFF, gyro/200 and offered accel/100 or
  /200 are enforced; unavailable hardware/profile evidence blocks (`capture.py:91-162`,
  `analyze.py:120-168`).
- **Per-frame schema and clock domains:** rows retain frame number, SDK stamp
  and reported domain, available hardware/global/system stamp fields, plus
  separate host CLOCK_MONOTONIC and CLOCK_REALTIME receipts. Analysis checks
  monotonicity within named clocks and does not subtract unmapped domains
  (`capture.py:53-88`, `analyze.py:53-86`).
- **Rates, drops, receipt gaps and stereo:** whole-window rates, frame-number
  gaps/nonincreasing numbers, boundary-inclusive callback receipt gaps, and
  same-domain stereo timestamp pairing are checked (`analyze.py:215-295`).
- **Static IMU and IR image checks:** static plausibility requires saved
  operator confirmation; sampled raw Y8 pixels are parsed and checked against
  config thresholds (`analyze.py:296-344`).
- **Latency policy:** absolute receipt latency remains UNKNOWN/null without a
  qualified mapping; only same-clock receipt jitter is reported (`analyze.py:345-349`).
- **Threshold provenance and result contract:** thresholds are centralized in
  `thresholds.yaml` with sources/rationales; result JSON includes status,
  criteria, evidence, hashes and contract exit codes (`thresholds.yaml`,
  `analyze.py:109-115, 350-363`, `check.py:15, 107-115`).
- **Fixtures, docs and report:** old-unit evidence is provenance-labelled and
  tested; README states exact Pi/replay commands, criterion meanings and
  limits. REPORT records delivery, verification, hardware gaps and proposed
  commit text. `tests/last-run.log` contains both test runs.
- **Scope and repository rules:** no hardware, network, system-package,
  unrelated-path or git-state mutation was used. No shell script was added.

## Test results after review

Exact commands and results:

```text
python3 -m unittest discover -s lab/d435i_raw/tests -v
Ran 28 tests in 15.532s
OK

PYTHONPATH=experiments/2026-09-12-pi5-native-sensor-validation python3 experiments/2026-09-12-pi5-native-sensor-validation/test_n2_tooling.py -v
Ran 18 tests in 1.751s
OK

python3 -m py_compile lab/d435i_raw/*.py lab/d435i_raw/tests/test_check.py
passed (no output)

git diff --check
passed (no output)
```

Full unittest output is in [tests/last-run.log](tests/last-run.log).

## Remaining open items

- **UNKNOWN:** Pi 5 / Python 3.12 and the installed pyrealsense2/librealsense
  binding were not exercised. Actual profiles, metadata availability/units,
  device callback behavior, emitter restoration, USB stability, power, thermal
  behavior and sustained capture remain unverified.
- **UNKNOWN:** physical stillness and the actual scene/image content are not
  established by the software tests. Static statistics remain plausibility
  checks, not calibration.
- **PROPOSED:** acceptance thresholds require lab approval. SDK USB descriptor
  matching does not prove physical negotiated bus speed. No latency or
  camera-to-IMU alignment qualification is claimed.

These are hardware/lab verification limits, not omissions from the software
ticket; COMMON.md prohibits hardware access for this review.
