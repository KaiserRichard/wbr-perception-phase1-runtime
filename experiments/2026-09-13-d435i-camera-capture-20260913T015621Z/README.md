# WBR D435i camera capture and two-week handoff — power blocked

**Mission partially completed; no current N2 or N3 PASS.** Live camera access was
explicitly authorized. Repeated fresh Pi undervoltage prevented the streaming
gates. All independent read-only metadata work, source inspection, configuration
preparation, handoff documentation and applicable offline tests were completed.
No commit, push, reset, firmware/EEPROM write, motor action or network change.

Machine status: [mission-status.json](mission-status.json).
Evidence/data inventory: [dataset-inventory.json](dataset-inventory.json).
Canonical source HEAD: `593245740fa962ad2325dc531cdb48c21d5f15b2`, dirty worktree;
branch `feat/d435i-camera-capture-20260913`. Existing user work remains preserved.
Pi checkout stays on `main` at `5a2a7bea415382c2400c9352a20b2010257e6ab4` and was
not edited. Acquisition software lives in separate runtime bundles.

## N0 / Pi

Power: `throttled=0x50000` persisted, and monotonic kernel logs show repeated
**new** undervoltage events during this session, including at boot elapsed
940, 993, 1013, 1188, 1214, 1319, 1849, 1929 and 1995 seconds. This is not merely
an inherited sticky-bit interpretation. [Initial](pi/kernel-before-monotonic.log)
and [final](pi/kernel-final-monotonic.log) logs preserve events and recovery lines.
Reboot was not performed: sudo requires interactive authentication. The operator
has no dedicated Pi 5 supply available, reports 5 V at 0.6–0.7 A on a USB tester,
and confirmed a Raspibase PWM fan on the Pi four-pin header. The exact supply
model and tester placement remain under investigation. Guided motion availability
is confirmed. See [operator setup](operator-setup.json).

Thermal: spot measurements roughly 51–54°C; no camera-load thermal qualification.
Memory: approximately 3.6 GiB available initially, no swap. Ubuntu 24.04 ARM64,
Jazzy and synchronized system time were observed.

Network: SSH uses Ethernet `192.168.50.2`; Wi-Fi remains the Internet route.
Ethernet negotiated 100 Mb/s in kernel evidence; no baseline acquisition was
sent over SSH. No persistent configuration changed.

Storage: root microSD had about 20 GiB available. SN530/JMS583 not attached.
The attached old 58.6 GiB exFAT USB2 flash device (UUID `1017-F615`) is unmounted
and unqualified. No write benchmark or bag recording was attempted under the
unstable power condition. About 1 MB of small evidence was retained on microSD.

## N1

USB: camera is direct child `5-1`, VID/PID `8086:0b3a`, **5000 Mb/s** in both
`lsusb -t` and sysfs. No intervening hub appears. Physical cable/supply/cooling
attestation remains pending; do not conflate observed topology with cable labeling.

Identity: SDK serial `243322073847`; ASIC `251843061466`; firmware-update ID
`251843061466`; separately observed USB descriptor serial `251843061466`;
firmware `5.17.3.10`; IMU `BMI085`.

Normal-user video/HID/IIO/control and USB-node access passed in the separate
read-only snapshot. Full enumeration succeeded as `richard`. No permission
changes were needed. Prepared `n1_precheck.py` returned **FAIL at N0 power**:
[actual receipt](pi/n1-initial/result.json). No N1 PASS receipt was manufactured.

## N2

Smoke: NOT RUN. Reproduction: NOT RUN. Mandatory 300-second soak: NOT RUN.
Rates, timestamp integrity, frame-number continuity, image integrity and
camera-load health: NOT MEASURED in this session. Kernel: new idle/platform
undervoltage remains a blocker. Historical ~105-second results are not a current
300-second PASS. Machine-readable verdict is in `mission-status.json`.

## Camera metadata

[Snapshot directory](pi/CAMERA_METADATA_SNAPSHOT/) contains full enumeration,
debug enumeration, separate USB/access identity, and two structured exports.
The final [JSON](pi/CAMERA_METADATA_SNAPSHOT/structured-v2/metadata.json) retains
269 advertised profiles, 261 returned profile intrinsics, 36 extrinsic pairs,
43 current option values, a 512-byte active calibration table and advanced settings.
The initial version and raw logs are preserved unchanged.

Ten read failures remain explicit: ASIC/projector temperature while idle, plus
eight Y16 intrinsics (IR1/IR2, 1280×800 or 640×400, 15 or 25 Hz). Exporter exit 2
means partial snapshot; no missing quantity was invented. The baseline Y8
640×480/15 projection was successfully read. Two repeated active-table and
advanced-settings reads were byte-identical.

Timestamp domains: actual frame domains NOT CAPTURED. Current global-time option
is 1 on Stereo, RGB and Motion modules. This proves configuration only.
ROS CameraInfo/IMUInfo/extrinsics/TF are not yet captured.

The warning is preserved verbatim in the SDK logs. Additional INFO messages
explicitly report CAD extrinsic fallback and unavailable gyro/accel intrinsic
calibration. Zero variance arrays are placeholders, not valid VIO noise values.
Readiness, source references and uncertainty are documented in
[calibration readiness](../../docs/D435I_VIO_CALIBRATION_READINESS.md).

## Calibration readiness

IR1: fx=fy=388.5274353027344, cx=319.10430908203125,
cy=239.55616760253906; SDK Brown Conrady coefficients all zero for this profile.
IR1→SDK gyro: identity R, t=[-0.005520000122487545,
0.005100000184029341, 0.011739999987185001] m, explicitly a CAD default.
Motion intrinsics: identity sensitivity, zero bias, default fallback.
Noise densities/walks and physical time offset: UNKNOWN / MUST MEASURE.
Kalibr or equivalent is likely required; exact scope remains unproven.

Guided target/multi-axis motion and stationary-noise recording instructions were
written before any prospective recording. The operator is available to perform
the sequence later; none has yet occurred.
No live capture dataset can be reconstructed from this metadata alone.

## N3

Wrapper: absent. [Apt review](pi/apt-reviewed.json) and
[simulation](pi/apt-simulation.txt): 221 new packages, one `libdeflate0` upgrade,
zero removals/downgrades/core-ROS replacements; 137,372,870 download bytes and
565,048,320 added installed bytes. Installation is authorized but deferred for
unstable power and unavailable interactive sudo authentication.

ROS parameters/topics/QoS/frame IDs/CameraInfo/extrinsics/TF and live rates:
prepared, **not physically observed**. Combined IMU remains disabled in the
candidate. No live node was launched because N2 has no PASS.

The final synthetic ten-topic record/replay test passed with generated messages:
30 IR images, 30 CameraInfo, 400 gyro, 200 accel, two IMUInfo, three extrinsics
and one TF message. [Test log](pi/pi-final-synthetic-ros-tests.log). This uses
previously unpacked message archives only for the synthetic Python environment;
it does not establish installed-wrapper readiness or hardware PASS.

## Bags and datasets

**No physical bag, raw image/IMU sequence, calibration-motion sequence or VIO
development dataset was created.** No camera-off replay of real data was possible.
The temporary synthetic bag was removed by its test fixture; small results remain
and are explicitly labeled SYNTHETIC.

| Retained package | Purpose / quality | Approximate size | Offline usefulness |
|---|---|---|---|
| `pi/CAMERA_METADATA_SNAPSHOT/` | Camera-specific metadata; partial reads documented | 577 KB | Configuration, calibration provenance and source comparison |
| `pi/n1-initial/` | Actual failed prerequisite | 9 KB | Explain blocked gate; never reuse as PASS |
| `pi/SYNTHETIC-final-ros-tests/` | Generated transport/replay checks | 66 KB | Tooling regression; no sensor research result |
| Platform/kernel/package evidence in `pi/` | Full small evidence collection; includes above groups | ~1 MB | Reproduction and diagnosis |

Per-file SHA-256, category, identity, firmware, profile context, storage, revision,
purpose and limitations are in [inventory](dataset-inventory.json). Snapshot
groups overlap; do not sum their sizes. Durations are not physical capture
durations. The active-table SHA-256 is
`f7c615c36e05442c36665fc8a553b89349ad12d302af3050b76a0ff3f511b47a`.
Final backup verification confirms 63 matching Pi→Mac file hashes; no third/offsite copy is
claimed. No original evidence was deleted.

## ORB-SLAM3

Build: not attempted; OpenCV development, Boost serialization development and
Pangolin are missing on Pi, and power is unstable. Existing upstream source was
inspected and preserved. [Candidate YAML](orbslam3_ir1_bmi085_candidate.yaml)
contains captured values and deliberate UNKNOWN noise strings; it is not a
runnable qualified configuration. Offline run: NOT RUN.

[Offline preparation](../../docs/ORB_SLAM3_OFFLINE_PREPARATION.md) provides source
identity, dependencies, isolated build commands, existing EuRoC input strategy,
accel/gyro association rules, validation tests, trajectory/export strategy and
evaluation criteria. Adapter design and first-party headless integration remain
reviewable future work; no new API/build/dataset format was silently introduced.

## Two-week offline plan and tooling note

- [Day-by-day plan](../../docs/NEXT_TWO_WEEKS_PERCEPTION_PLAN.md): evidence and
  clock review → pipeline/YAML/preintegration → calibration → build/adapter →
  initialization/tracking/resource diagnosis → repeatability → N4 proposal.
- [Tooling architecture](../../docs/PERCEPTION_TOOLING_ARCHITECTURE.md): purpose,
  input/output, use and proof limits of all requested first-party utilities.

## Runtime bundle and regression

Final Pi bundle: `/home/richard/wbr-runtime/wbr-runtime-20260913T021130Z`.
Mac build copy: `/tmp/wbr-runtime-20260913T021130Z`; durable archive in
[this experiment](wbr-runtime-20260913T021130Z.tar.gz). Archive SHA-256:
`643a7fb97599c12c19784584de49e5256ab3d3ff1573c39e1ed51e3a57f1f01f`.
33 source/evidence files plus manifest sealed by `SHA256SUMS`; source and
manifest verification passed. Old `/home/richard/wbr-runtime/wbr-runtime-20260912T160912Z`
was verified and never overwritten. An intermediate metadata bundle at
`wbr-runtime-20260913T020030Z` is also retained.

Final metadata binary hash:
`d0a5ff96c30ed091ae4a34d9045383fa0975d87e6c64f90eeebc00578c796e12`.
Compilation succeeded; SDK-header warnings are in preserved compile logs.
Mac and Pi offline suites: 44 tests each, one opt-in skip. Explicit Pi synthetic
ROS integration: one additional test passed across all ten topics. JSON/YAML,
local Markdown links, shell syntax, `git diff --check` and bundle/evidence hashes
were checked. No real camera capture process or sensor owner remains.

## Files changed by this task

- New `camera_metadata.cpp` in the existing first-party utility directory.
- `bundle_runtime.py`: include exporter; label bundle as tooling, not hardware PASS.
- `validation_common.py`: recognize metadata exporter in camera-process inventory.
- New four documents linked above.
- This timestamped experiment directory: raw evidence, logs, manifests,
  blocked verdict, candidate configuration and handoff. Existing dirty work is
  recorded in the initial Mac Git snapshots and was not overwritten.

Rollback: select a previously verified runtime bundle for existing gates;
retain this session as historical evidence. No Git commit is needed to revert
runtime selection, and no persistent camera/network state was modified.

## What is possible without the camera

Audit calibration and software provenance; learn and test the tools; inspect
SDK timestamp semantics and ORB source; plan/build dependencies on a suitable
offline machine; review the candidate/adapter and N4 criteria. Actual VIO
experiments require recorded images and full-precision IMU that are still missing.

## What still requires the physical camera / next gate

Stable supply/cooling and fresh power interval; physical direct-cable attestation;
fresh N1; exact N2 smoke/reproduction/**300-second soak** and image review;
frame timestamp domains; stationary and guided multi-axis/target data; physical
N3 parameters/topics/calibration/TF; qualified explicit-topic bags and backups.

A reboot alone cannot repair voltage drop. While investigating the existing
3 A supply, first establish its label/rating and tester position. For a direct
power-cable test, cleanly power off before removing an inline tester or changing
cables. The minimal privileged command is:

```bash
ssh -t richard@192.168.50.2 'sudo poweroff'
```

It is required because normal-user sudo reported that a password is needed;
additional task approval is not being requested. After shutdown, change the
power path, power up, reconnect and preserve fresh
`vcgencmd get_throttled`, temperature, USB tree and kernel logs before proceeding.
Do not install packages while power still faults. Once stable, the already
reviewed installation command (no `-y`) is:

```bash
ssh -t richard@192.168.50.2 \
  'sudo apt-get --no-install-recommends install ros-jazzy-realsense2-camera ros-jazzy-realsense2-camera-msgs'
```

Refresh simulation if candidates have changed. Use the existing
[N1→N2→N3 runbook](../2026-09-12-pi5-native-sensor-validation/PHASE_A_RUNBOOK.md)
for execution; this session's explicit camera authorization supersedes its old
camera-free stop statement. Gate thresholds and manual attestation still apply.
Use new output directories after recovery; never rewrite the failed N1 receipt.

## Power follow-up with the operator

The Pi boot device tree reports `max_current=3000` mA and
`usb_max_current_enable=0`; no high-current USB override was applied. The user
has no dedicated Pi 5 supply currently. A 5 V/3 A source can operate a Pi 5, but
its default aggregate USB peripheral limit is 600 mA. Supply capability, cable
loss and camera-load stability remain separate questions. See the
[official power documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html).
The operator is available for guided motion after the mandatory gates pass.
