# Camera-free preparation and future N1 → N2 → N3 execution

**STOP before hardware execution until the user explicitly sends `CAMERA AVAILABLE`.**
This runbook supersedes execution suggestions in historical COMMANDS.md and
reports. Offline/synthetic success means **TOOLING PASS**, never hardware PASS.
No ORB-SLAM3, live VIO, firmware/calibration changes or motor-control work here.

## Ownership and evidence

Mac checkout is canonical; Pi runs an isolated checksummed copy. Preserve both
Git checkouts and historical results. Acquisition, CSV/image processing,
recording and replay execute on the Pi. SSH carries control and small evidence.
Native SDK owns sensor threads; Python main threads own child processes and
one-Hz health sampling. ROS wrapper owns its capture threads; recorder and
observer are separate owned subprocesses. STM32H7 owns hard-real-time safety.

Keep `manifest.json`, historical SDK logs/results, `run_sdk_capture.py`,
`analyze_sdk_csv.py`, and `sample_ir.cpp` unchanged as provenance. Future commands
use the new guarded utilities. All output paths must be new. Archive failed
runs; never repair a bag with reindex and call its original shutdown clean.

The archived ~105-second native run is useful history but is **not final N2**.
Its original sample CSVs and three PGM files are not in this Mac repository.
See [EVIDENCE_RECONCILIATION.md](EVIDENCE_RECONCILIATION.md).

## Phase A: safe now

Mac, from repository root:

```bash
export WBR_TOOLS="$PWD/experiments/2026-09-12-pi5-native-sensor-validation"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "$WBR_TOOLS" -p 'test_*.py' -v
export WBR_BUNDLE="/tmp/wbr-runtime-$(date -u +%Y%m%dT%H%M%SZ)"
python3 "$WBR_TOOLS/bundle_runtime.py" build "$WBR_BUNDLE"
python3 "$WBR_TOOLS/bundle_runtime.py" verify "$WBR_BUNDLE"
```

Use a unique new bundle after every implementation change. The manifest records
the Mac revision, dirty status and exact source hashes, since HEAD alone cannot
identify uncommitted work. `SHA256SUMS` also seals the manifest.

The direct Ethernet link was verified using Pi link-local address
`fe80::2ecf:67ff:fea2:86d3`, scoped to Mac `en7`; Pi receives SSH on `eth0`.
These interface/address values are observations, not permanent configuration.
The Pi's Internet default route is via Wi-Fi `wlan0`. The ordinary
`wbr-pi5.local` name may select Wi-Fi. Verify the interface after reconnecting
the adapter. Use the already trusted hostname key rather than disabling host
key checking for the link-local address:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o HostKeyAlias=wbr-pi5.local \
  'richard@fe80::2ecf:67ff:fea2:86d3%en7' \
  'printf "%s\n" "$SSH_CONNECTION"; ip -brief address; ip route'
```

No persistent route, netplan, NetworkManager, SSH or Mac network changes are
needed for this demonstrated link. If it fails, retain existing connectivity
and inspect interface/address state; do not change configuration silently.

Copy the new bundle to the same unique basename in `/home/richard/wbr-runtime/`
using SSH/SFTP. Create the destination with exclusive `mkdir`, never rsync
`--delete` or overwrite an older bundle. On the Pi, in that bundle:

```bash
sha256sum -c SHA256SUMS
python3 bundle_runtime.py verify .
source /opt/ros/jazzy/setup.bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s . -p 'test_*.py' -v
g++ -O2 -std=c++17 -Wall -Wextra sample_ir_checked.cpp \
  -I/opt/ros/jazzy/include -L/opt/ros/jazzy/lib/aarch64-linux-gnu \
  -Wl,-rpath,/opt/ros/jazzy/lib/aarch64-linux-gnu -lrealsense2 -o sample_ir_checked
sha256sum sample_ir_checked
```

Compilation is safe without the camera. **Do not execute the sampler now.**
SDK-header compiler warnings must be retained. No `colcon build` is required:
these are standalone utilities using binary Jazzy packages, not a new ROS
workspace or package. A source rebuild would be a separately reviewed change.

Optional camera-free ROS integration, Pi only:

```bash
WBR_RUN_ROS_SYNTHETIC=1 PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest test_ros_offline -v
```

This creates a temporary ~10 MB **synthetic** SQLite bag from constructed
messages, inspects finalized metadata and runs a complete replay in domains
181/182. It verifies real ROS serialization, storage and playback for the
image/CameraInfo/raw-IMU/TF subset by default; if RealSense message types are
available, it includes both IMUInfo messages and all three extrinsics too. It does
not launch a camera, enumerate USB, qualify storage or generate hardware gates.

The takeover also exercised all ten topics using two small `.deb` archives
downloaded with `apt download` and unpacked with `dpkg-deb -x` into a unique
inspection directory, **without package installation or executing the wrapper**.
The archive versions/hashes and exact temporary Python/library/ament environment
are in the takeover evidence command logs. After sourcing Jazzy, that test used:

```bash
export WBR_EXTRACTED=/home/richard/wbr-package-inspect/takeover-20260912T154755Z/extracted/opt/ros/jazzy
export PYTHONPATH="$WBR_EXTRACTED/lib/python3.12/site-packages:$PYTHONPATH"
export LD_LIBRARY_PATH="$WBR_EXTRACTED/lib:$LD_LIBRARY_PATH"
export AMENT_PREFIX_PATH="$WBR_EXTRACTED:$AMENT_PREFIX_PATH"
WBR_RUN_ROS_SYNTHETIC=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_ros_offline -v
```

Use a fresh shell for physical execution: this archive environment is for
synthetic message testing only. `WBR_SYNTHETIC_EVIDENCE=/new/directory` optionally
preserves small test JSON/logs, never the temporary bag. No successful archive
test implies the system wrapper is installed or that all its dependencies load.

Read-only inventory: `python3 platform_inspect.py` (save stdout to a new file).
The takeover found `throttled=0x50000`, recording historical power/throttling
events. Investigate supply, cable and cooling before the next physical gate;
preserve this evidence. A clean reboot after resolving the cause, when the
user chooses, establishes a fresh observation interval, not retroactive proof.
N1 requires `0x0`, synchronized UTC, ARM64 Ubuntu 24.04, Jazzy, <75°C and
at least 512 MiB MemAvailable. No reboot or package installation is performed
by preparation tools.

## Future storage: WD PC SN530 + JMS583

The old UUID `1017-F615` and 0.944 MB/s probe belong to a different temporary
drive. The planned NVMe/enclosure has **no qualification evidence**. Physical
model/label provenance should include both the SN530 and the enclosure;
JMS583 may expose its own bridge model/serial rather than the NVMe identity.

After separately authorizing physical storage setup, identify the actual disk,
partition, filesystem UUID, mount source/options and USB branch with `lsusb`,
`lsusb -t`, `lsblk`, `blkid`, and `findmnt`. Never infer identity from `/dev/sda1`
or a directory name. The tool refuses root/microSD, mount fallbacks, symlinks,
wrong UUID/source, unknown identity, read-only or unwritable paths. It never
formats or mounts anything. Mount/format/permission changes need review.

The default write budget is 8 GiB, at least 1 GiB and 60 seconds with fsync
after each 64 MiB batch. Required overall **and worst-batch** throughput is
≥9.216 decimal MB/s (2× raw IR payload 4.608 MB/s), plus matching SHA-256
readback and finalized cleanup. This is a conservative engineering margin,
not a guarantee of loss-free recording. Buffered readback may use cache; no
power-loss durability or direct-I/O claim follows.

A fast NVMe can exhaust 8 GiB before 60 seconds: this is an incomplete
qualification, not evidence of poor throughput. Review a larger write budget
(for example 32 GiB), free-space cost and desired duration before rerunning.
The script retains 10 GiB headroom and requires budget + headroom before any
probe write. Do not run this substantial write on microSD or during Phase A.

Future Pi example, replace all three identifiers with inspected real values:

```bash
python3 storage_qualify.py --mount /mnt/wbr-nvme --uuid ACTUAL_NVME_UUID \
  --device /dev/ACTUAL_PARTITION --output "$WBR_RUN/storage" \
  --qualify-external-storage
```

Qualify storage before the N1/N2 sequence when possible, with camera and
storage physically connected but no camera processes. **Fresh N1 after the
storage probe is mandatory**. A storage PASS cannot override a camera 480M
branch, power flags or shared-USB instability. Bags must stay on that exact
qualified mount; small N1/N2 CSVs, three images and health logs may use microSD.

## First commands after CAMERA AVAILABLE

On the Pi, in the verified runtime bundle, after physically documenting supply,
cooling and the direct known-good USB-A↔USB-C SuperSpeed cable in a blue USB3
Type-A port:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1
export WBR_RUN="$HOME/wbr-evidence/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$HOME/wbr-evidence"
mkdir "$WBR_RUN"
python3 n1_precheck.py --camera-available --direct-cable-confirmed --output "$WBR_RUN/n1"
```

The **first hardware command** is the final line. Flags attest facts already
established by the user's message and physical inspection; they do not grant
authorization on their own. A nonzero exit means STOP and review result.json.
Never put subsequent gates after a semicolon that ignores failure.

N1 captures UTC/host/user/groups, raw USB tree, camera sysfs branch/speed and
descriptor identity, raw kernel context, all node modes, video/HID/IIO and
custom-HID controls, owners and normal-user SDK enumeration. Camera's own
speed must be ≥5000M and direct. **480M → STOP before SDK enumeration/N2.**
Read-only permission checks include IIO buffer controls, scan enables,
sampling/hysteresis controls, current_trigger and custom HID enable_sensor.
The existing helper only applies root:video 0660 to explicit controls under
the serial-matched USB ancestor. No permission repair happens automatically.
Never broaden the rule to compensate for a missing descriptor on USB2.

Identifiers remain separate: SDK `243322073847`; ASIC `251843061466`;
firmware-update ID `251843061466`; USB descriptor serial separately observed.
Expected firmware `5.17.3.10`, BMI085. No firmware update is part of a mismatch
response. N1 receipts expire after two hours or reboot and seal raw evidence.

## Future N2 stages

Run each command only after the previous command exits zero; inspect its
output before continuing. No capture stage automatically accepts final N2.

```bash
python3 phase_gate.py n2 --camera-available --seconds 20 \
  --n1-result "$WBR_RUN/n1/result.json" --output "$WBR_RUN/smoke"
python3 phase_gate.py n2 --camera-available --seconds 105 \
  --n1-result "$WBR_RUN/n1/result.json" --previous "$WBR_RUN/smoke/capture-result.json" \
  --output "$WBR_RUN/reproduction"
python3 phase_gate.py n2 --camera-available --seconds 300 \
  --n1-result "$WBR_RUN/n1/result.json" --previous "$WBR_RUN/reproduction/capture-result.json" \
  --output "$WBR_RUN/soak"
```

Each run uses exactly IR1 640×480 Y8/15, gyro/200, accel/100. No fallback or
combined IMU. It preserves requested duration, UTC start/end, exact SDK argv,
stdout/stderr, finalized CSV, before/after topology, continuous raw journal,
one-Hz temperature/throttling/memory/system CPU/process CPU/RSS/free space,
shutdown results, package/OS/kernel and source/binary hashes. A separate
12-second image-only sampler follows each raw interval and saves three PGMs.
It does not extend or replace the required 300-second raw soak.

Timing bands: IR 14.25–15.75 Hz, gyro 190–210, accel 95–105. Image maximum
gap ≤0.20 s; motion ≤0.05 s. All timestamp and frame steps must be positive,
no repeated/backward timestamps or missing image frame numbers. Whole-request
and interior-window rates, arrival gaps and boundary offsets are all reported.
The vendor starts its arrival timer before opening sensors: initial offsets
above the gap target require a documented setup explanation, never an
automatic loss exemption. Internal and trailing gaps stay strict. The vendor
CSV lacks timestamp-domain tags and rounds IMU values to 0.001; do not infer
sensor synchronization, exact latency or calibration quality from it.

Review all raw logs and three images. Require coherent grayscale content,
valid Y8 dimensions/bytes, nontrivial statistics and distinct saved hashes.
Distinct content alone does not prove intentional scene motion. Kernel
reset/disconnect/re-enumeration/xHCI/UVC/HID/IIO/corruption/power faults fail.
Known HID report-ID warnings remain in raw logs for attribution. Preserve:
`IMU Calibration is not available, default intrinsic and extrinsic will be used.`
Transport may pass, but final VIO qualification remains blocked.

Create `$WBR_RUN/review.json` **only after actual review**, with current UTC,
reviewer, notes, power_supply, cooling, scene and calibration_provenance strings,
plus explicit Boolean true for raw_logs_clean, images_coherent,
startup_offsets_explained, imu_values_plausible, power_cooling_documented and
calibration_warning_preserved. Do not copy a prefilled acceptance template.

```bash
python3 phase_gate.py accept-n2 --camera-available \
  --n1-result "$WBR_RUN/n1/result.json" --smoke "$WBR_RUN/smoke/capture-result.json" \
  --reproduction "$WBR_RUN/reproduction/capture-result.json" \
  --soak "$WBR_RUN/soak/capture-result.json" --review "$WBR_RUN/review.json" \
  --output "$WBR_RUN/n2-accepted"
```

This rechecks sealed evidence, recomputes timing/content, requires all three
stages and archives the reviewed inputs. It can issue N2_ACCEPT PASS only
after future physical evidence and explicit review, never from old summaries.

## Future N3 wrapper, live gate, recording and replay

The takeover found no installed RealSense ROS wrapper. See
[N3_PREPARATION.md](N3_PREPARATION.md) for the version/dependency blocker.
Inspect an approved installation without starting the camera:

```bash
python3 wrapper_inspect.py --output "$WBR_RUN/wrapper-static.json"
```

The prepared baseline targets wrapper 4.58.4. Parameter names were checked in
the pinned source; installed file inspection and live readback are separate
requirements. Do not install/upgrade automatically or claim candidate packages
are installed. `n3_record.py` refuses an absent/unreviewed wrapper version.

After reviewed N2 PASS and storage PASS, using N1 taken after qualification:

```bash
python3 n3_record.py --camera-available --n1-result "$WBR_RUN/n1/result.json" \
  --n2-result "$WBR_RUN/n2-accepted/result.json" \
  --storage-result "$WBR_RUN/storage/result.json" \
  --bag "/mnt/wbr-nvme/NEW_SESSION_BAG" --seconds 20 --output "$WBR_RUN/n3-record"
```

This launches `/camera/camera` with n3_baseline.yaml, verifies readback, then
observes a complete 60-second live window using sensor-compatible QoS. Only
then does it record explicit topics from n3_topics.json, while observing
delivery under recording load. RGB/depth/IR2/pointcloud/alignment/RGBD/combined
IMU stay off. `unite_imu_method=0`. Metadata topics may exist but are not part
of the explicit baseline bag. No services/actions are invoked to change camera
state; parameter service reads only. `/tf_static` is reliable/transient-local;
raw sensor subscriptions are best-effort/volatile. Frame IDs must be stable,
image/CameraInfo agree and static TF must connect all sensor frames.

The explicit bag contains IR1 image, CameraInfo, raw gyro, raw accel, both
IMUInfo topics, three depth-to-stream extrinsics, and `/tf_static`. These
context topics are supported by 4.58.4 and required for this baseline. Do not
make one optional just because it is missing; inspect actual version/graph.
The source selects depth as the extrinsics base from **available** profiles
even when depth streaming is disabled. No `/camera/camera/imu`, no `-a`.

For diagnosis in a future live window: `ros2 node list --no-daemon`,
`ros2 topic list -t`, `ros2 topic info --verbose TOPIC`, and
`ros2 param dump /camera/camera`; save outputs. These are supplementary to the
simultaneous observer, not replacements for it. Do not launch a second node.

The recorder receives SIGINT and must finalize metadata; forced termination,
missing topics/types/context, count discrepancy or invalid stamps fail.
Next the runner stops its live camera, verifies the live domain is quiet and
returns. Inspect the unfiltered logs and result before replay. Failed runs
remain preserved and are not eligible for accepted replay.

```bash
python3 n3_bag.py replay /mnt/wbr-nvme/NEW_SESSION_BAG \
  --record-result "$WBR_RUN/n3-record/result.json" \
  --live-domain 42 --replay-domain 43 --output-dir "$WBR_RUN/n3-replay"
```

Replay checks finalized metadata and hashes, camera processes and both domains
before starting. A separate observer guards domain 42 throughout; domain 43
accepts only the bag player. Ready/stop handshakes bracket the entire playback
and queue drain. Counts/types/header and full-payload hashes must match stored
messages, including latched context. Bag mutation or any live camera process
invalidates acceptance. ROS discovery is localhost-only for this baseline.
Full-message comparison hashes every decoded field, including exact numeric
bits and sequence order; serialized wire hashes are also retained. DDS/CDR
encoding bytes can differ even when fields match, so wire padding is not
treated as a sensor-content change. Changed pixels/calibration/stamps still fail.
Review complete player/observer logs before accepting N3. No next-stage SLAM
command follows this runbook.

## Verification and rollback

Expected offline result: unit tests pass, ROS integration passes on sourced
Pi Jazzy, C++ compilation succeeds, bundle checksums match, and absent-camera
entry points reject before hardware access. Expected future result: nonzero
STOP/FAIL for bad USB, permissions, profile, timestamps, missing context,
unsafe storage or live replay contamination; REVIEW_REQUIRED after automatic
capture/record/replay checks, and N2 PASS only through explicit reviewed acceptance.

Tests do not establish USB stability, permission persistence, scene response,
NVMe throughput or calibration. Queue overflow/drop counts and absolute
end-to-end delay not exposed by a backend remain **unavailable**, never zero;
frame/count gaps and raw diagnostic warnings provide loss evidence.

Rollback: retain all evidence, compare takeover before/after hashes and restore
only changed preparation utilities from their pre-edit copy. Deploy a new
bundle for corrections; never reset the Pi checkout or edit deployed source
in place. No commits/pushes are authorized.
