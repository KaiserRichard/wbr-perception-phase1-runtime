# Serial swap and latched-power diagnostic tooling report

Date: 2026-10-13. Scope: Mac canonical checkout, offline/synthetic preparation only.

**MEASURED — tooling:** Final unittest discovery succeeded: 56 tests, 55 passed,
one skipped. A new runtime bundle was built and verified, including all 36
SHA256SUMS entries. This is tooling validation only; no hardware PASS was issued.

**MEASURED — supplied historical observations:** `rs_enumerate_new_unit.txt` and
`camera_plug_check.txt` record SDK serial `317422076650`, ASIC serial
`327743061057`, firmware-update ID `327743061057`, USB descriptor serial
`327743061057`, firmware `5.17.3.10`, SDK USB type `3.2`, a 5000 Mbps camera
branch, and `throttled=0x50000`. These files were read, not reproduced on hardware.
The user confirmed this active unit and explicitly chose diagnosis despite the
power history and unavailable better supply. Bits 16 and 18 record historical
under-voltage and throttling; live bits 0-3 were clear in that observation.

**UNKNOWN:** New-unit IMU type. The enumeration snapshot omits it. BMI085 remains
a required N1 observation; missing or different IMU type fails. New-unit transport,
power, calibration and N1/N2 behavior have not been validated physically here.

## Changes and behavior

All edited files are under `experiments/2026-09-12-pi5-native-sensor-validation/`.
The table gives the diff against a pre-edit copy, because this tooling directory
was already untracked in Git. Counts are added/removed lines, not a commit diff.

| File | + / - | Short diff summary |
| --- | --- | --- |
| `validation_common.py` | 29 / 0 | One-line `ACTIVE_UNIT` definition with four separate identity fields; historical serial comment; expected firmware/IMU; serial rendering and power helpers. |
| `n1_precheck.py` | 17 / 9 | Shared SDK/USB expectations; explicit diagnostic flag; masked power check; raw power and mode in result; successful diagnosis becomes OPEN_DIAGNOSTIC. |
| `sdk_capture.py` | 25 / 12 | Shared SDK selection and identity checks; diagnostic N1 prerequisite requires opt-in; apply diagnostic policy to every health sample; persist raw power samples and OPEN verdict. |
| `health_monitor.py` | 5 / 3 | Preserve raw vcgencmd output; opt-in failure evaluator allows only history mask, with default strict behavior retained. |
| `phase_gate.py` | 10 / 2 | N2 diagnostic CLI flag and explicit previous-stage opt-in; refuse diagnostic N1/captures at acceptance; strict acceptance result includes power metadata. |
| `n3_baseline.yaml` | 2 / 2 | Replace old SDK literal with shared serial placeholder. |
| `bundle_runtime.py` | 2 / 1 | Resolve that placeholder in the copied bundle YAML before hashing. |
| `n3_record.py` | 5 / 3 | Write a resolved session YAML; launch and compare readback against that same file. |
| `wrapper_inspect.py` | 2 / 2 | Resolve shared serial for static baseline inspection. |
| `wbr-d435i-iio-permissions.py` | 3 / 1 | Shared USB descriptor identity in the inventory helper N1 calls; no permissions applied. |
| `test_gate_tooling.py` | 61 / 2 | New USB fixture; old USB rejection; shared YAML serial; synthetic N1 power/verdict/identity cases and unknown-bit rejection. |
| `test_n2_tooling.py` | 138 / 1 | Health mode cases; synthetic capture monitor/result test; new/old/missing-IMU N1 receipts; opt-in progression; diagnostic acceptance rejection. |
| `test_takeover_tooling.py` | 4 / 4 | Shared active serial for wrapper readback fixtures; preserve type-mismatch rejection. |
| `PHASE_A_RUNBOOK.md` | 31 / 3 | Active identity, unknown IMU, serial-template handling, explicit diagnostic progression and deployment limitations. |

**MEASURED — policy:** Strict N1 still requires the exact `throttled=0x0` string;
strict run monitoring requires zero flags. With `--diagnostic-latched-power`,
only set bits within `0xF0000` are tolerated. `0x50000` can proceed as
`OPEN_DIAGNOSTIC`; `0x50005`, any live bit, unknown bit or malformed power text
fails. A successful diagnostic run remains OPEN even when the value is zero.
Failed checks remain FAIL. Success exits zero solely to allow deliberate N1 →
20-second → 105-second → 300-second diagnostic progression. The flag must be
supplied to N1 and every N2 command. N2 acceptance cannot issue PASS from
diagnostic inputs, and N3 still requires strict N2 PASS.

New N1 results and N2 capture results include `power_mode` and `throttled_raw`;
capture results additionally contain `throttled_samples_raw`, with raw observations
also in `health.jsonl`. A failure before a power observation leaves the raw field
null. Preflight failures that formerly produced no output directory still produce
no receipt. Timing/image analyses retain their separate tooling-check semantics;
the enclosing diagnostic capture verdict stays OPEN. Kernel/SDK fault detection,
calibration warning retention, USB >=5000M, exact raw profiles, all timing thresholds
and the mandatory 300-second N2 soak remain intact.

**MEASURED — memory inspection:** No active check assumes 8 GB RAM. N1 retains
524288 KiB (512 MiB) MemAvailable; run health retains its existing 256 MiB guard.
Other 8 GiB numbers concern storage budgets/reserves, not RAM. The supplied
`snapshot.txt` reports 3.9 GiB total and 3.6 GiB available at that snapshot,
consistent with the user's 4 GB Pi. **INFERRED:** The RAM capacity reduction
does not itself violate these checks. **UNKNOWN:** Memory headroom during future
physical capture; it must be monitored rather than inferred from this snapshot.

## Tests and reproduction

Executed on Mac Python 3.11, with no package installation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s experiments/2026-09-12-pi5-native-sensor-validation -p 'test_*.py' -v
```

Final output:

```text
Ran 56 tests in 2.623s

OK (skipped=1)
```

Skipped: `test_ros_offline.SyntheticROSTest.test_finalized_bag_complete_replay_and_no_publisher_boundary`,
reason `opt-in camera-free ROS integration`. The Pi/ROS integration opt-in was
not enabled. All new identity, N1 flag-off `0x50000` failure, flag-on `0x50000`
OPEN, flag-on `0x50005` failure, health monitoring and acceptance refusal tests
passed. These use explicitly synthetic/mocked observations and processes.

The initial 55-test run passed with one skip. After expanding capture coverage,
an intermediate 56-test run had three subcase errors because the process mock
also intercepted `platform.platform()`'s Mac subprocess lookup. Mocking that
lookup explicitly fixed the fixture; the final complete discovery passed.

Manual validation remains future work on an authorized Pi session: run the
PHASE_A_RUNBOOK N1 command with `--diagnostic-latched-power`, verify the measured
IMU field and inspect its OPEN receipt, then run each N2 command with that flag
and inspect raw logs/health/images. Retain the exact 20/105/300-second stages.
Exercise acceptance rejection against those OPEN receipts; do not fabricate a
human review. None of these hardware commands was executed for this ticket.

## Runtime bundle

**MEASURED — path:**
`experiments/2026-10-13-pi5-env-snapshot/bundles/wbr-runtime-20261013T044130Z`

Created UTC: `2026-10-13T04:41:30.483433+00:00`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/2026-09-12-pi5-native-sensor-validation/bundle_runtime.py build experiments/2026-10-13-pi5-env-snapshot/bundles/wbr-runtime-20261013T044130Z
PYTHONDONTWRITEBYTECODE=1 python3 experiments/2026-09-12-pi5-native-sensor-validation/bundle_runtime.py verify experiments/2026-10-13-pi5-env-snapshot/bundles/wbr-runtime-20261013T044130Z
```

Both commands exited zero and reported `tooling: PASS`, 35 payload files.
An independent Python SHA-256 check matched all 36 checksum entries, including
`bundle-manifest.json`. The bundled native YAML contains SDK serial
`317422076650`, with no unresolved serial placeholder.

SHA-256 of the bundle's `SHA256SUMS` file:

```text
d1141f1bb2b01bff3650811128de085ecabf14ad52f5e7c693e5d1bf5b3a4a99
```

The manifest records canonical revision
`593245740fa962ad2325dc531cdb48c21d5f15b2`, existing feature branch
`feat/d435i-camera-capture-20260913`, dirty/untracked Git status and actual payload
hashes. HEAD alone does not identify these uncommitted utilities. The bundle YAML
is intentionally rendered, so its checksum differs from the preparation template.
For a future swap, edit the one `ACTIVE_UNIT` line in the canonical source and
build a new bundle; do not edit sealed bundles in place.

## Preservation, limits and risks

**MEASURED — preservation:** Pre-edit tooling copies are at
`/private/tmp/wbr-serial-power-before-g1n8bsi1` for local comparison/rollback.
`run_sdk_capture.py` is not used by `phase_gate.py` and remains byte-for-byte
unchanged, as do `analyze_sdk_csv.py`, `sample_ir.cpp`, `manifest.json`, historical
enumeration/logs/results and `99-wbr-d435i.rules`. The corrected historical N3 YAML
under the 2026-09-13 experiment was never edited. Existing unrelated user work
was left intact. This report and the requested new bundle are the only outputs
written outside the tooling directory in the repository.

**MEASURED — not performed:** No SSH, Pi access, hardware operations, camera
enumeration/capture, sensor/firmware/calibration changes, package installs,
permissions application, C++ SDK build, physical soak, ROS replay, commits or
pushes. The bundle remains local and has not been deployed. Physical results
are UNKNOWN/OPEN; offline success establishes tooling only.

**INFERRED — risks:** Latched-power diagnosis cannot establish supply stability
or erase historical faults. One-Hz sampling may miss brief live flags; raw kernel
faults still stop capture. Existing calibration warnings continue to block VIO
qualification. The template YAML must be resolved before direct ROS use; the
bundle and session runner handle this. The inventory helper now depends on its
adjacent `validation_common.py` and must not be installed alone via old commands.
The retained historical udev rule targets the old unit; it is not an active-unit
installation recipe. The supplied `udev_change_2026-10-13.txt` records earlier
user-side permission changes, but their current effectiveness was not checked
here. N1 will inspect actual normal-user permissions without repairing them.

Supplied observation provenance (SHA-256):

| File in this snapshot directory | SHA-256 |
| --- | --- |
| `rs_enumerate_new_unit.txt` | `10f4f7b4bf3945c8a467d82cb6091b0fc0392a6e337bcb8f0816ea5e0c6f82f9` |
| `camera_plug_check.txt` | `962e7ff0f51c442d0d39465b4f0dcdb98cd35a521bbf6de66230e6731156364d` |
| `snapshot.txt` | `0558d8cef14d165de84a2043e24faf0e2e40a2e28303937fc15de8aab64385eb` |
| `udev_change_2026-10-13.txt` | `c8419e27f25a4d72ce3df52e2cbabc974f9391e27025053633bd08e229aba845` |
