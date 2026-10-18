# Cross-tool consistency audit — 2026-10-18

**Scope:** the raw D435i, calibration, ROS bag, N4B exporter, power/USB, evaluation, profiling, and shared clock/observer tools named in T17, plus the older latency tools where they report percentiles. This is source/configuration inspection, not a hardware qualification. Evidence labels below follow the project convention. No mechanical code change was justified; the profile, policy, and statistical differences require an explicit owner decision.

## Aggregate tests

Command: `bash tools/run_all_tests.sh` (macOS, Python 3.11). The run completed and printed the table below. `tools/link_bench` failed in both its make target and Python suite: the PTY runner reported `baud 460800 not supported by termios`, then error cleanup timed out waiting for the simulator. The Python suite also skipped its QEMU firmware integration test because `qemu-system-arm` and `arm-none-eabi-gcc` are unavailable. All other listed suites passed. This is not an aggregate PASS. Rerun on a host supporting the configured baud or fix the test's macOS serial setup in its owning ticket.

| Suite | Status | Detail |
|---|---|---|
| make:tools/link_proto:test | PASS | host target |
| make:tools/link_bench:test | FAIL | make exited 2 |
| make:tools/runtime_observer:test | PASS | host target |
| make:tools/vio_adapter:test | PASS | host fake-engine target |
| make:tools/ros2_bridge:test | PASS | host target |
| python:tools/calib_tools/tests | PASS | unittest discovery |
| python:tools/clockmap/tests | PASS | unittest discovery |
| python:tools/frames/tests | PASS | unittest discovery |
| python:tools/link_bench/tests | FAIL | unittest exited 1; one QEMU test skipped |
| python:tools/link_proto/tests | PASS | unittest discovery |
| python:tools/ros2_bridge/tests | PASS | unittest discovery |
| python:tools/run_harness/tests | PASS | unittest discovery |
| python:tools/runtime_observer/tests | PASS | unittest discovery |
| python:tools/take_tools/tests | PASS | unittest discovery |
| python:tools/vio_adapter/tests | PASS | unittest discovery |
| python:tools/trajectory_eval | PASS | unittest discovery |
| python:calibration/allan/tests | PASS | unittest discovery |
| python:calibration/lab/tests | PASS | 26 tests |
| python:.github/tests | PASS | unittest discovery |
| python:tools/n4b_offline/tests | PASS | unittest discovery |
| python:tools/perception_health/tests | PASS | unittest discovery |
| python:lab/calib_record/tests | PASS | unittest discovery |
| python:lab/d435i_raw/tests | PASS | unittest discovery |
| python:lab/power_usb/tests | PASS | unittest discovery |
| python:lab/rosbag_qual/tests | PASS | unittest discovery |
| python:tools/eval_pipeline/accuracy/tests | PASS | unittest discovery |
| python:tools/eval_pipeline/profile/tests | PASS | unittest discovery |

## Findings by topic

Severity: **High** means results can describe different profiles or invalidate a gate comparison; **Medium** means result interpretation/policy can differ; **Low** means labels differ while calculations are guarded or equivalent.

### Nominal sensor profiles and IMU combining

| Severity | Files and lines | Observed values / disagreement | Evidence-supported interpretation and recommendation |
|---|---|---|---|
| High | [`lab/d435i_raw/thresholds.yaml`](../../lab/d435i_raw/thresholds.yaml#L8-L14); [`lab/rosbag_qual/config.json`](../../lab/rosbag_qual/config.json#L5-L76); [`tools/n4b_offline/db3_to_euroc.py`](../../tools/n4b_offline/db3_to_euroc.py#L15-L22); [`calibration/lab/pi/record_calib_take.sh`](../../calibration/lab/pi/record_calib_take.sh#L33); [`lab/calib_record/criteria.json`](../../lab/calib_record/criteria.json#L1-L5) | Raw N2 specifies stereo IR 848×480 Y8@30, emitter OFF, gyro 200 Hz, accel preferred 100 (or 200). ROS bag qualification config uses IR 15 Hz, gyro 200, accel 100 (lines 7–76). N4B exporter accepts only 640×480 and exports separate raw gyro/accel on an interpolated accel-to-gyro grid. Calibration capture/check uses stereo 640×480@30, gyro 200, accel 100, emitter OFF. The bag config has no emitter or `unite_imu_method` setting. | **MEASURED:** saved Pi evidence reports IR1/IR2 at 30 Hz, gyro 200.2 Hz, accel 101 Hz for the 2026-10-14 RAM take; the last second had a shutdown gap. **SOURCE-SUPPORTED:** factory calibration and its recorder explicitly use 640×480; the current raw-check config describes the separate 848×480 N2 selection. These are distinct test contracts, not one safely replaceable constant. Recommendation: publish named/versioned N2, N3, calibration, and N4B profiles, record the resolved stream profile/emitter/driver parameters with every bag, and require explicit conversion compatibility. Do not call an exported interpolated combined IMU the driver's `unite_imu_method`; exporter metadata correctly reports driver method `UNKNOWN` unless a combined topic matches. Evidence: [`experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md`](../../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md#L5-L8), [`calibration/lab/README.md`](../../calibration/lab/README.md#L18-L30), [`tools/n4b_offline/db3_to_euroc.py`](../../tools/n4b_offline/db3_to_euroc.py#L83-L107). |

### Clock-domain names and arithmetic

| Severity | Files and lines | Observed values / disagreement | Evidence-supported interpretation and recommendation |
|---|---|---|---|
| Low | [`tools/runtime_observer/event_recorder.h`](../../tools/runtime_observer/event_recorder.h#L103-L127); [`tools/runtime_observer/README.md`](../../tools/runtime_observer/README.md#L58-L60); [`tools/eval_pipeline/profile/profile.py`](../../tools/eval_pipeline/profile/profile.py#L100-L101); [`tools/eval_pipeline/profile/README.md`](../../tools/eval_pipeline/profile/README.md#L34-L45) | The same Linux `CLOCK_MONOTONIC` host clock appears as `host_steady` in observer event files, `CLOCK_MONOTONIC` in sampler CSV, and `host_steady / Linux CLOCK_MONOTONIC` in combined reports. | These names are documented aliases for the host monotonic timeline; session identity is required for observer epochs. Recommendation: retain both the machine-readable domain token and a human-readable clock description in combined outputs. Current profile mapping checks enforce same `host_steady` observer session before source timestamps are compared. |
| High | [`calibration/allan/d435i_imu_record.cpp`](../../calibration/allan/d435i_imu_record.cpp#L73-L100); [`lab/calib_record/REPORT.md`](../../lab/calib_record/REPORT.md#L96-L100) | In the Allan recorder, `Stats::add` increments `domain_changes` when a new SDK timestamp domain arrives, but still computes `dt = s.stamp - last_stamp` and uses it for reversal, duplicate, and max-gap accounting across the boundary. | This is an actual cross-domain subtraction and can create false timing diagnostics if SDK timestamp domains change. The calibration take checker independently rejects domain changes and excludes cross-domain intervals through `tools/take_tools.timing`, but that does not repair the recorder's own counters. Recommendation: reset/skip the interval at a domain boundary and add a regression test in the recorder's owning change. Per COMMON.md, this bug is recorded here and was not changed in this audit. |
| Medium | [`tools/perception_health/py/sender.py`](../../tools/perception_health/py/sender.py#L13-L26); [`tools/clockmap/analyze.py`](../../tools/clockmap/analyze.py#L164-L199); [`lab/d435i_raw/analyze.py`](../../lab/d435i_raw/analyze.py#L298-L305); [`lab/rosbag_qual/bag_core.py`](../../lab/rosbag_qual/bag_core.py#L368-L371); [`tools/n4b_offline/db3_to_euroc.py`](../../tools/n4b_offline/db3_to_euroc.py#L149-L151) | The sender explicitly uses `CLOCK_MONOTONIC_RAW`; observer/profile uses `CLOCK_MONOTONIC`; clockmap's target is named `host_steady`; ROS header stamps and bag receive timestamps are separately named and their mapping is UNKNOWN. | No unguarded cross-domain subtraction was found in these Python tools. `CLOCK_MONOTONIC_RAW` and `CLOCK_MONOTONIC` are separate labels and must not be treated as interchangeable. Clockmap explicitly fits SDK global time to host steady and labels its offset/jitter limitations; the perception-health sender requires a RAW-target mapping before age arithmetic; raw D435i and rosbag tools avoid comparing epochs across domains. **Recommendation:** preserve these explicit mapping gates and record the underlying Linux clock API whenever a file says `host_steady`. |

### Throttle bits and temperature policy

| Severity | Files and lines | Observed values / disagreement | Evidence-supported interpretation and recommendation |
|---|---|---|---|
| Medium | [`lab/power_usb/thresholds.yaml`](../../lab/power_usb/thresholds.yaml#L16); [`tools/eval_pipeline/profile/config.json`](../../tools/eval_pipeline/profile/config.json#L5-L8); [`tools/runtime_observer/resource_sampler.py`](../../tools/runtime_observer/resource_sampler.py#L1-L40); [`tools/eval_pipeline/accuracy/run_euroc.sh`](../../tools/eval_pipeline/accuracy/run_euroc.sh#L31-L38) | Power and profile decode bits 0–3 and 16–19 consistently. Profile treats any listed current or latched bit as invalid; power records all bits but its acceptance criteria exclude several throttle/frequency/soft-temperature bits. `run_euroc.sh` records before/after throttle snapshots, while accuracy evaluation does not use them as an acceptance criterion. Both power and profile choose 80 °C, but power fails only when temperature is **greater than** 80 °C while profile requires **less than** 80 °C, so exactly 80 °C differs. | Bit meanings are SOURCE-SUPPORTED and agree. Policy scopes differ: power/USB readiness, profile timing validity, and accuracy are distinct. The 80 °C limit is PROPOSED in both configs; no evidence selects inclusive versus exclusive comparison. Recommendation: decide whether exactly 80 °C is allowed, centralize or cross-reference the policy, and keep accuracy's saved throttle snapshots visible while stating that they do not validate timing. No threshold change is justified by evidence. |

### Storage throughput

| Severity | Files and lines | Observed values / disagreement | Evidence-supported interpretation and recommendation |
|---|---|---|---|
| Medium | [`lab/rosbag_qual/config.json`](../../lab/rosbag_qual/config.json#L92-L97); [`lab/calib_record/criteria.json`](../../lab/calib_record/criteria.json#L22-L26); [`lab/calib_record/check_calib_take.py`](../../lab/calib_record/check_calib_take.py#L457-L463); [`calibration/lab/pi/record_calib_take.sh`](../../calibration/lab/pi/record_calib_take.sh#L20-L25) | The 16,600,000 B/s historical card result and 18.4 MB/s stream demand appear in ROS bag comparison, calibration storage headroom, and RAM-capacity planning. Calibration applies a proposed 20% reserve to the old 16.6 MB/s figure; RAM planning reserves 18.4 MB/s × 1.2 × 1.5 for file/temporary capacity. | **MEASURED:** 1.66 GB/100 s = 16.6 MB/s on the old microSD; **CALCULATED/INFERRED:** the full stream needed about 18.4 MB/s, and the old card could not sustain it. The rosbag 16.6 MB/s setting is explicitly a historical comparison ceiling, not a current destination qualification; calibration reports a warning against its proposed 13.28 MB/s headroom value. These have different purposes but share constants. Recommendation: put the evidence numbers in a single referenced profile/threshold source when storage configs are next revised, and never treat a passing bag-size/duration proxy as sustained-write proof. Evidence: [`experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md`](../../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md#L6-L8). |

### `result.json` and exit-code contract

| Check | Contract inspection | Result |
|---|---|---|
| `lab/power_usb` | `check_power_usb.py:488-500,503-558` | Compliant: required top-level fields, criterion `threshold_source`, raw hashes, table, saved-analysis mode; PASS/FAIL/BLOCKED map to 0/1/2 and usage/internal error to 3. |
| `lab/d435i_raw` | `analyze.py:308-319`; `check.py:75-115` | Compliant: fields, hashes, table, `--analyze-only`; 0/1/2/3. Capture-setup/usage failures can exit 3 before an evaluated result exists. |
| `lab/calib_record` | `check_calib_take.py:523-527,632-684` | Compliant: normal and dependency-BLOCKED outputs include required fields; saved `--analyze-only`; 0/1/2/3. |
| `lab/rosbag_qual` offline analyze, record, replay | `qual_common.py:150-168`; `analyze_bag.py:81-94`; `record_check.py:246-259`; `replay_check.py:301-316` | Compliant: shared result builder, evidence hashes, offline saved-analysis modes, contract statuses and error code 3. Missing ROS/native support is BLOCKED. |
| `tools/n4b_offline/qualify_euroc.py` | `qualify_euroc.py:67-88` | Compliant: fields, criterion sources, table, `--analyze-only`, 0/1/2; usage errors use the contract parser with exit 3. |
| `tools/eval_pipeline/profile` validity | `profile.py:323-351,383-409` | Compliant: `result.json`, fields, criterion sources, saved-analysis mode, table, 0/1/2/3. Sampler and latency subcommands are data collectors/evaluators, not independent PASS/FAIL checks. |
| `tools/eval_pipeline/accuracy` | `evaluate.py:188-223` | Not a lab `result.json` checker: writes `summary.json`/`report.md` under its own accuracy-pipeline schema and returns 0/1/2/3. It records no `host` or `raw_files` at the top level. Keep distinct unless the project wants it covered by the common lab-check contract. |

No contract defect was found in the lab qualification checks audited. The accuracy pipeline is a separate report contract by design; harmonizing it would be a scope/design decision.

### Percentile definitions for latency

| Severity | Files and lines | Observed definition | Recommendation |
|---|---|---|---|
| Medium | [`tools/runtime_observer/stats.py`](../../tools/runtime_observer/stats.py#L8-L14); [`tools/eval_pipeline/profile/README.md`](../../tools/eval_pipeline/profile/README.md#L34-L45); [`tools/link_bench/pi/link_bench.py`](../../tools/link_bench/pi/link_bench.py#L103-L119); [`tools/link_bench/pi/la_analyze.py`](../../tools/link_bench/pi/la_analyze.py#L103-L112); [`tools/clockmap/analyze.py`](../../tools/clockmap/analyze.py#L52-L58) | Runtime observer, profile latency, and both link-bench percentiles use nearest-rank (`ceil(q*n)`, one-based). Clockmap uses NumPy `percentile` default interpolation (linear between samples), which differs for finite sample counts. Calibration residuals use mean/median/std/RMS rather than latency percentiles; accuracy reports RMSE, not percentiles. | Name the quantile method in clockmap output and choose whether clockmap should align with nearest-rank or keep NumPy's interpolated estimate. Existing values cannot be compared exactly across those methods for small samples. No code change without that choice. |

### Camera identity labels

| Severity | Files and lines | Observed values / disagreement | Evidence-supported interpretation and recommendation |
|---|---|---|---|
| Low | [`docs/PROJECT_STATE.md`](../../docs/PROJECT_STATE.md#L11-L15); [`lab/d435i_raw/thresholds.yaml`](../../lab/d435i_raw/thresholds.yaml#L3-L6); [`lab/calib_record/criteria.json`](../../lab/calib_record/criteria.json#L19-L20); [`calibration/lab/config/camchain_factory_317422076650.yaml`](../../calibration/lab/config/camchain_factory_317422076650.yaml#L1-L6); [`lab/d435i_raw/REPORT.md`](../../lab/d435i_raw/REPORT.md#L70-L76) | Current SDK device serial is 317422076650, firmware 5.17.3.10. Older raw fixture/evidence has SDK serial 243322073847. Power USB identifies by VID/PID and records a USB descriptor serial, not the SDK serial. Factory calibration comments distinguish SDK serial from ASIC/update-ID/USB serial. | No wrong current identity constant found. Legacy fixture explicitly labels old camera evidence and tests reject it as current-unit evidence. Recommendation: retain separate named fields for SDK serial, firmware-update ID, ASIC serial, and USB descriptor serial; do not make descriptor serial equal the SDK serial. |

## Fixes and open decisions

**Code/config fixes:** none. The profile and policy differences are explicit legacy/current evidence, separate qualification profiles, or policy/statistical decisions without evidence for a single replacement value. The Allan recorder's cross-domain interval subtraction is a real bug, but COMMON.md directs this ticket to report existing tool bugs instead of fixing them. No regression tests were added because no code was changed.

**Recommended owner decisions:** fix the Allan recorder cross-domain interval accounting with a regression test; name and version the sensor profiles and bag provenance; decide 80 °C boundary behavior; decide whether to centralize storage constants; label clockmap percentile method and choose a common method if direct comparison is needed; decide whether accuracy summaries should adopt the lab result contract.

**Proposed commit message:** `docs: audit cross-tool consistency and open profile decisions`

### Resolved by T21 — 2026-10-18

- Allan recorder `Stats::add` now counts timestamp-domain transitions and skips interval subtraction across the boundary; the next sample establishes the new domain baseline. A C++ regression test exercises transition, recovery, and same-domain duplicate accounting using the local librealsense stub.
- Power/USB and profile validity both fail inclusively at 80 °C (79.9 °C passes; 80.0 °C fails). Raspberry Pi's Pi 5 article says the processor begins throttling when the temperature reaches 80 °C: https://www.raspberrypi.com/news/heating-and-cooling-raspberry-pi-5/ . Both configs and operator docs cite this source.
- Clockmap retains NumPy's percentile calculation and labels every percentile object and top-level report `numpy linear interpolation`; its README records that runtime_observer/profile uses nearest-rank and finite-sample values can differ.
