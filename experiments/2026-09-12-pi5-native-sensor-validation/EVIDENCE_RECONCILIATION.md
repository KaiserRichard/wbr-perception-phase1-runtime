# Phase A historical evidence reconciliation — 2026-09-12

This is an offline audit of saved evidence. The camera is unavailable. No
camera command, enumeration, stream, ROS camera process or hardware polling
was performed for this audit. **Tooling checks are not hardware PASS results.**
Use [PHASE_A_RUNBOOK.md](PHASE_A_RUNBOOK.md) for later execution after the user
explicitly sends `CAMERA AVAILABLE`.

## Provenance and preservation

The canonical Mac inspection found branch
`feat/pi5-native-sensor-validation-20260912`, HEAD
`593245740fa962ad2325dc531cdb48c21d5f15b2`. The initial working tree already
contained the deleted root audit, its untracked `docs/` copy, the untracked
native validation report/experiment directory, Obsidian directories, and
untracked content in the ORB_SLAM3 submodule. Those are pre-existing user
changes and are preserved. Neither checkout is reset, committed or pushed.

Before preparation edits, all **38** `file_sha256` entries in
[manifest.json](manifest.json) matched the corresponding local files, with no
missing listed files. The manifest itself had SHA-256
`68d634ea1b930f03502bd413e78947c58a235fd90720e6560cfaac827d50252d`.
It remains frozen, including historical wording and the older
`asic_usb_serial` conflation in capture results. Preparation changes to code
and documentation intentionally produce new hashes; they must not rewrite
historical raw logs/results or manufacture a historical source revision.
New runs need both the Git revision and hashes of uncommitted runtime files.

## Evidence-supported chronology

| Saved interval / source | Supported finding | Limit / gate consequence |
|---|---|---|
| September 8 UTM audit: [RESUME_SUMMARY.json](../2026-09-08-d435i-baseline/RESUME_SUMMARY.json), [B_RATES.json](../2026-09-08-d435i-baseline/B_RATES.json) | IR1-only B delivered 15 images in about 30 seconds (0.500 whole-window Hz), with 15 incomplete-frame notifications. Its first/last arrival rate was about 14.959 Hz. | The latter is a brief burst, not stable 15 Hz delivery. These VM/Docker results do not describe the native Pi. |
| First native smoke, 09:32:58–09:33:21 UTC: [capture result](smoke-01-capture-result.json), [SDK log](smoke-01-sdk.log) | Requested 20 seconds; shutdown hit custom-HID `enable_sensor` EACCES; SDK return code −2 after interruption. | Unfinalized CSV cannot establish counts/rates. This is a failed run, not zero measured delivery. |
| Second smoke, 09:40:02–09:40:25 UTC: [capture result](smoke-02-capture-result.json), [analysis](smoke-02-analysis.json) | Requested 20 seconds; SDK return code 0; interior 10-second timing window passed. | A smoke result is not final N2. |
| Sustained native capture, 09:41:52–09:43:40 UTC: [capture result](sustained-capture-result.json), [SDK log](sustained-sdk.log), [analysis](sustained-analysis.json) | Requested **105 seconds**, SDK return code 0; camera's video/HID branch is 5000M before/after; three interior 30-second windows passed. | Both saved result files explicitly leave N2 `NOT DECIDED`. No 300-second soak evidence exists locally. **No historical final N2 PASS.** |
| Later topology revalidation, 09:56:14–09:57:52 UTC: [preflight](usb-revalidation-20260912T095610Z/usb-storage-preflight.txt), [after snapshot](usb-revalidation-20260912T095610Z/health-kernel-after.txt), [access](usb-revalidation-20260912T095610Z/sensor-access.txt) | Camera at `4-1.1.2`, 480M through two USB2 hubs; USB descriptor serial absent; HID/IIO permissions denied. No stream was attempted. | Historical N1 regressed/blocked and N2 blocked by N1. Idle diagnostics do not establish streaming stability or any current camera state. |

Historical successful native path: direct known-good USB-A ↔ USB-C cable to
the Pi blue USB3 Type-A port. The next physical test must establish the
camera's **own** direct branch at ≥5000M. A 5000M root elsewhere in `lsusb -t`
does not qualify a 480M camera. Do not debug ROS or loosen udev rules while N1
fails.

## Native timing, content and health cross-check

The [sustained analysis](sustained-analysis.json) records:

| Stream | Total received count | Whole-window rates, 30-second windows at 10/40/70 seconds | Maximum timestamp gap across all samples |
|---|---:|---:|---:|
| IR1 640×480 Y8 / 15 Hz | 1,573 | 15.000 / 14.967 / 15.000 Hz | 66.677 ms |
| Gyro / 200 Hz | 20,974 | 200.033 / 200.033 / 200.033 Hz | 5.0001 ms |
| Accel / 100 Hz | 10,607 | 101.133 / 101.100 / 101.100 Hz | 9.8951 ms |

Every stream's saved all-sample analysis reports zero nonpositive timestamp
steps and zero missing frame numbers. The three interior windows include
arrival boundary metrics. These are checks of a saved analysis, **not a
recomputation from the absent acquisition CSV**. They do not establish
300-second continuity, SDK timestamp domain, absolute latency, or camera–IMU
synchronization. `rs-data-collect` did not serialize timestamp domain and
rounded motion vectors to 0.001 in its historical CSV.

The [capture result](sustained-capture-result.json) contains 104 health
samples. Recalculation gives temperature 58.95–62.25 °C; every sampled
`get_throttled` value is `0x0`; system CPU mean 1.089%, maximum 14.109%.
System CPU is an interval metric across cores; historical `ps %CPU` is a
process lifetime average. These are observed health values for that capture,
not a performance improvement claim or a power-supply qualification.

The complete local [sustained kernel log](sustained-kernel.log) consists of
two startup HID report-ID warnings. It contains no captured camera USB
reset/disconnect/re-enumeration; this is a statement about the saved interval,
not proof that logging could never miss an event. Preserve these warnings in
future classification and review raw context manually.

[IR metadata](ir-content-frame-metadata.csv) is available locally: 179 rows,
640×480, stride 640, 307,200 bytes, Global Time. The saved
[content analysis](ir-content-analysis.json) lists three distinct SHA-256
values, pixel standard deviations about 70.42 and a historical coherent-scene
visual review. **The PGM originals are absent locally**, so this audit cannot
repeat pixel statistics, hashes or visual review. Distinct samples are not
proof of deliberately tested scene motion; none was performed historically.

## Identity, permission and calibration boundaries

| Field | Historical expected value / meaning | Source |
|---|---|---|
| `DEVICE_SERIAL` | `243322073847`; use this for SDK/ROS device selection | [SuperSpeed SDK enumeration](sdk-enumeration-full.txt) |
| `ASIC_SERIAL` | `251843061466`; separate SDK field | Same enumeration |
| `FIRMWARE_UPDATE_ID` | `251843061466`; separate SDK field despite equal value | Same enumeration |
| `USB_DESCRIPTOR_SERIAL` | Historically recorded as `251843061466` on the successful path; absent on the later USB2 path | [original manifest snapshot](usb-revalidation-20260912T095610Z/manifest-before-resume.json), [USB2 preflight](usb-revalidation-20260912T095610Z/usb-storage-preflight.txt) |
| Firmware | `5.17.3.10` | SDK enumeration; USB `bcdDevice` is not firmware |
| SDK USB Type Descriptor | `3.2` on successful path; `2.1` on later path | Both saved full SDK enumerations |
| IMU | `BMI085` | SDK enumeration |

The initial SuperSpeed descriptor-serial value is retained in the original
manifest, and the saved helper previews demonstrate successful identity
matching. The initial full sysfs/USB transcript is not retained locally, so
this audit does not claim to have independently re-read that descriptor. The
later USB2 descriptor absence is directly supported by its saved raw output.

The preserved [udev rules](99-wbr-d435i.rules) require vendor `8086`, product
`0b3a` and USB descriptor serial `251843061466`. The
[helper](wbr-d435i-iio-permissions.py) checks the resolved USB ancestor again
and grants only the explicit IIO/custom-HID controls to `root:video 0660`.
Its default mode is read-only. Normal-user video access alone does not prove
HID/IIO or shutdown access. An absent USB descriptor serial on the invalid
480M path does not justify broadening the rule. Re-establish N1 first, then
verify actual access without root; any repair requires specific evidence.

The historical [SDK log](sustained-sdk.log) says:

> IMU Calibration is not available, default intrinsic and extrinsic will be used.

Raw N2 transport may eventually pass while this warning remains recorded.
That does not establish VIO calibration. Final VIO qualification remains
blocked pending calibration provenance and adequacy. No firmware update,
calibration replacement, speculative JSON preset or upstream warning-removal
patch belongs in this task.

## Storage and source availability

[storage-write-probe.json](storage-write-probe.json) records 67,108,864 bytes
written with fsync in 71.062 seconds: **0.9443705 MB/s**, with matching
readback SHA-256. The method was one buffered 64 MiB probe; readback may have
used cache. This is below the IR1 pixel payload of **4.608 MB/s**, before bag
overhead. It does not qualify N3 storage and says nothing about the planned
WD PC SN530 256 GB NVMe in a JMS583 enclosure.

The old `/dev/sda1`, exFAT UUID `1017-F615`, `/mnt/wbr-data` and capacity
figures belong to the historical temporary USB drive. Later saved evidence
shows it unmounted and the directory resolving to microSD. Never reuse those
identifiers for another device or trust a directory name as mount evidence.
Current policy reserves microSD for OS/packages/repository/small logs. The
future NVMe needs its own mount identity, sustained write/finalization and
readback checks, then camera stability/topology checks with both attached.

Local acquisition originals **not found** in this experiment tree:

- `sdk-smoke-02/frames.csv` and `sdk-sustained-01/frames.csv`, referenced under
  `/mnt/wbr-data/wbr-perception-phase1/2026-09-12/raw/` by the saved analyses.
- The three `ir1-frame-{30,90,150}.pgm` image originals.
- Any 300-second soak, ROS diagnostic bag (`.db3`/`.mcap`), finalized bag
  metadata or successful record/replay evidence.

The Mac does retain JSON analyses/results, SDK and kernel logs, topology and
permission transcripts, dependency metadata, IR metadata CSV and first-party
utilities. External files might exist elsewhere, but this offline audit does
not claim their presence or readability. Missing originals limit independent
re-analysis; never recreate them from summaries or replace them with mocks.

## Documentation reconciliation and verification

Additive notices in the bring-up plan, baseline audit, native report, README
and COMMANDS distinguish historical snapshots from present preparation. They
supersede old ROS-as-N2 commands, optional-soak wording, temporary-drive mount
instructions and unresolved storage-policy suggestions. Historical bodies
and raw files are retained; two broken audit links in the bring-up plan were
updated to the audit's existing `docs/` location. [N3_PREPARATION.md](N3_PREPARATION.md) must be read
with current software inspection and the runbook; historical apt candidates
and estimated costs are not current installation authority.

No application build is required for these documentation changes. Offline
verification consists of JSON parsing, the pre-edit 38-file hash comparison,
saved counts/window checks, recalculated health/storage arithmetic, IR
metadata inspection, and Markdown link checks. Expected result: historical
findings remain traceable and no missing hardware evidence is labeled PASS.
Failure symptoms include an unexplained raw-file hash change, an absent
linked artifact, current claims sourced only from old summaries, or any N2
PASS without the required soak. Synthetic fixtures test software only.

Rollback removes only the clearly marked Phase A notices and this new
reconciliation document, preserving user changes and raw evidence. Do not
restore the older `manifest-before-resume.json` over the frozen manifest as
a preparation rollback. The next step is the runbook's non-camera readiness
checks, followed by a stop until `CAMERA AVAILABLE`.
