# PREPARATION TAKEOVER COMPLETE

**Scope: camera-free tooling preparation only. No new hardware PASS.** No
camera detection, SDK invocation, streaming, N1/N2/N3 physical execution,
ORB-SLAM3, VIO, firmware/calibration change, package installation, network
configuration change, commit or push occurred.

## Repository state and recovered work

Mac branch `feat/pi5-native-sensor-validation-20260912`, HEAD
`593245740fa962ad2325dc531cdb48c21d5f15b2` remains canonical and uncommitted.
Pre-existing audit relocation, Obsidian directories, AGENTS.md, preparation
files and ORB_SLAM3 .DS_Store files are preserved. Pi checkout remains clean at
`5a2a7bea415382c2400c9352a20b2010257e6ab4`; its historical divergence was not
reset. The baseline audit's historical body matches committed HEAD after its
existing relocation notice. All **99 pre-existing raw experiment artifacts**
(JSON/CSV/log/text) match takeover-entry SHA-256 values, including manifest.json.

The interrupted session had already produced the historical reconciliation,
guarded N1/N2 utilities, analyzer, image checker, health/kernel monitoring,
storage probe, ROS observer, topic/QoS configuration, bag reader/replay and
31 passing offline tests. It had left the linked runbook, gate dispatcher,
explicit recorder, runtime bundle and storage tests unfinished. See
[initial A–V coverage](takeover-20260912T154755Z/INITIAL_COVERAGE.md).

Historical evidence supports the 20-second smoke and approximately 105-second
native run, never final 300-second N2. Saved timing totals are IR 1,573, gyro
20,974 and accel 10,607; raw SDK logs record orderly completion and the
calibration warning. IR metadata has 179 rows at 640×480. Original acquisition
CSVs/PGMs are missing from the Mac, so these totals are cross-checks of saved
results, not regenerated measurements. Later 480M topology and 0.944 MB/s
storage remain failed historical evidence.

## Work completed

Added the executable N2 progression/review path, mount-gated explicit N3
recording and clean-camera-stop boundary, source-hashed runtime bundling,
wrapper static/readback validation and missing runbook. Strengthened N1
nonfinite-speed rejection, N2 evidence sealing/re-enumeration checks, storage
blkid/finite-metric checks, ROS QoS checks, replay record-receipt binding and
bag-mutation detection. Whole-message replay comparison retains exact decoded
fields plus separate wire hashes; a synthetic test exposed why raw CDR bytes
alone can falsely reject equal CameraInfo content. Initial failed test logs
are preserved alongside the fixes and successful final run.

Direct Ethernet SSH was verified using scoped IPv6, with Wi-Fi retaining the
Internet default route. No persistent networking was modified. The two small
candidate wrapper/message archives were checksum-recorded and unpacked outside
both repositories, without installing packages or executing a camera node.
Their message libraries enabled full ten-topic synthetic ROS validation.

## Files

Created in this experiment directory: `PHASE_A_RUNBOOK.md`, `phase_gate.py`,
`n3_record.py`, `bundle_runtime.py`, `wrapper_inspect.py`,
`test_takeover_tooling.py`, `test_ros_offline.py`, this report and the clearly
labeled `takeover-20260912T154755Z/` evidence directory.

Modified existing preparation: `validation_common.py`, `n1_precheck.py`,
`sdk_capture.py`, `storage_qualify.py`, `n3_observer.py`, `n3_bag.py`,
`n3_metrics.py`, `test_n2_tooling.py`, `test_n3_metrics.py`,
`N3_PREPARATION.md`, and the experiment README handoff link. Fixed two stale
relocated-audit links in `docs/DOCKER_RUNTIME_ARCHITECTURE_REVIEW.md`.
Historical utilities/results were retained, not rewritten.

## Offline validation

- Mac: **43 passed, one Pi-only integration test skipped** (44 discovered).
- Pi: **44/44 passed**, including real ROS serialization/finalized SQLite bag
  inspection/full replay for all ten topics using constructed messages.
- Synthetic replay: IR 30, CameraInfo 30, gyro 400, accel 200, both IMUInfo
  topics one each, three extrinsics one each, TF one. Full decoded fields,
  header stamps/types and counts match; synthetic live-domain contamination
  is rejected, as is missing finalized metadata.
- Synthetic 300-second CSV: full-window checks cover 4,500 IR, 60,000 gyro,
  30,000 accel and nine interior windows; it never issues physical N2 PASS.
- C++ image sampler compiled on ARM64 with existing compiler/SDK; it was
  **not executed**. SDK-header warnings are retained, no upstream edits.
- Python AST, JSON parsing, shell syntax, Markdown links and `git diff --check`
  pass. Storage rejection, burst-only delivery, repeats/backward timestamps,
  wrong profiles, frozen images, changed evidence and absent-camera guards
  are covered. Tests never perform the external storage benchmark.

Evidence: [Mac tests](takeover-20260912T154755Z/mac-final-tests.txt),
[Pi build/tests](takeover-20260912T154755Z/pi-final-checks.txt),
[exact Pi commands](takeover-20260912T154755Z/pi-final-checks-command.sh),
[static audit](takeover-20260912T154755Z/offline-static-audit.json),
[synthetic replay evidence](takeover-20260912T154755Z/SYNTHETIC-takeover-20260912T154755Z-final/README.md),
[deployment/source hashes](takeover-20260912T154755Z/final-deployment.json).
The ~10 MB synthetic bag was removed after the test; small reports/logs were
copied to the Mac. Reproduction uses the saved test code and package hashes.

## Readiness

READY means preparation/tooling readiness, not permission to execute now.

| Deliverable | Status |
|---|---|
| N1 USB/access tooling | READY |
| N2 smoke / reproduction / mandatory 300-second soak | READY |
| N2 analyzer / image-content validation | READY |
| Raw kernel classification / Pi health monitoring | READY |
| Storage qualification / NVMe-JMS583 procedure | READY |
| N3 ROS live observer / topic-type-QoS validation | READY |
| N3 explicit recorder / finalization / stop-live boundary | READY |
| N3 isolated-domain replay | READY |
| Provenance / fail-closed gates | READY |

All A–V preparation categories are complete within the authorized scope.
Wrapper installation and every physical qualification remain future work.

## Runtime handoff and blockers

Verified final Pi bundle:
`/home/richard/wbr-runtime/wbr-runtime-20260912T160912Z`.
Earlier immutable test bundles remain for traceability; use this final bundle.
The system wrapper and message packages remain **uninstalled**. Candidate
installation is substantial: 137,372,870 download bytes, 565,048,320 installed
bytes added, 221 new packages and one upgrade with the inspected cache. Review
and explicitly approve installation separately; refresh the transaction first.

The Pi still reports `throttled=0x50000`; preserve that power history and
resolve supply/cooling concerns before a fresh N1. Camera is unavailable.
The direct known-good USB3 cable/blue port, recreated normal-user HID/IIO
access and the mandatory 300-second soak require physical validation.
SN530/JMS583 mount identity, write/fsync/readback speed and coexistence with
camera USB3 are unqualified. Calibration fallback remains a final VIO blocker.
No acquisition-latency, queue-overflow, power or performance improvement claim
is inferred from these tooling tests.

User actions: supply `CAMERA AVAILABLE` when true; document supply/cooling and
the direct cable; resolve nonzero power history; separately authorize wrapper
installation and actual external storage setup/qualification when needed.
Use a fresh Pi shell without the temporary archive test environment.

Exact first hardware command on the Pi, only after that message and physical
cable confirmation (the runbook contains the full staged session):

```bash
source /opt/ros/jazzy/setup.bash
python3 /home/richard/wbr-runtime/wbr-runtime-20260912T160912Z/n1_precheck.py \
  --camera-available --direct-cable-confirmed \
  --output "$HOME/wbr-evidence/n1-$(date -u +%Y%m%dT%H%M%SZ)"
```

A nonzero result means STOP. Do not continue N2 while power/USB/access fails.
Follow [PHASE_A_RUNBOOK.md](PHASE_A_RUNBOOK.md) for N2 review, storage and N3.
**Stopped and waiting for `CAMERA AVAILABLE`. No commit or push.**
