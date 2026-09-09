# 1. Architecture decision

**Reference baseline: Pi 5 + Ubuntu 24.04 ARM64 + ROS2 Jazzy + native RealSense + native SLAM.**
Docker is **deferred until native success**. This is the management baseline,
not a claim that Pi compatibility or performance has already passed.

```text
D435i → Pi 5 native Linux → native librealsense / realsense-ros → ROS2
      → recorded-data validation → native ORB-SLAM3 / ROS wrapper later
```

- **Pi:** physical sensor and eventual native VIO reference system.
- **Lab:** x86 native reference / heavy benchmark.
- **UTM:** offline development only; no physical sensor acceptance evidence.

This document governs repository direction; the existing
[Pi bring-up plan](RPI5_NATIVE_PERCEPTION_BRINGUP.md) supplies supporting detail.
All gates below remain unpassed on Pi. This change creates only this document.

# 2. Why the current upstream stack is not our baseline

`ORB_SLAM3_ROS2` is a **useful predecessor/reference implementation**.
Verified differences from our intended baseline are:

| Mismatch | Verified evidence and consequence |
|---|---|
| Existing images are amd64 | The saved [image inventory](RPI5_NATIVE_PERCEPTION_BRINGUP.md#4-arm64-compatibility-audit) lists seven local `linux/amd64` images. These artifacts are not native ARM64 images; this does not classify every possible build of the recipes. |
| Compose requests NVIDIA | [Wrapper Compose](../third_party/ORB_SLAM3_ROS2/docker-compose.yaml) reserves an NVIDIA GPU in `base`, inherited by `orb_slam3`; that reservation is inappropriate for the Pi baseline. |
| RealSense runtime/source mismatch | Saved [runtime log](../experiments/2026-09-08-d435i-baseline/A_LOG.txt) reports realsense-ros **4.58.1**, built/running with SDK **2.58.1**; our [source checkout](../third_party/realsense-ros/realsense2_camera/package.xml) is **4.58.4**. The source pin does not identify the tested binary; this is not an SDK build/runtime version mismatch. |
| Embedded versus official ORB | [Wrapper submodules](../third_party/ORB_SLAM3_ROS2/.gitmodules) select `gjcliff/ORB_SLAM3`, while the [parent](../.gitmodules) separately selects `UZ-SLAMLab/ORB_SLAM3`. The wrapper calls fork APIs `GetFrameDrawerImage()` and `GetMapPCL()` absent from the official checkout's `System.h`. |
| Docker build prerequisite | [Wrapper CMake](../third_party/ORB_SLAM3_ROS2/CMakeLists.txt) requires the embedded `ORB_SLAM3/build` package export and generated libraries. Its [Dockerfile](../third_party/ORB_SLAM3_ROS2/Dockerfile) comments out the ORB build; Compose runs `colcon build` without first establishing that prerequisite. A clean checkout needs an explicit ORB dependency build. |
| Image topic mismatch | [Camera Compose](../third_party/ORB_SLAM3_ROS2/ros2_realsense_d435i_camera_calibration/docker-compose.yaml) remaps IR1 to `/camera/image_raw`; the [wrapper](../third_party/ORB_SLAM3_ROS2/src/imu_mono_realsense.cpp) subscribes to `camera/infra1/image_rect_raw`. The current mapping launch supplies no matching remap. |
| Mode mismatch | [Mapping launch](../third_party/ORB_SLAM3_ROS2/launch/mapping.launch.py) defaults to `monocular`, overriding the node's `imu-monocular` default. Intended VIO requires explicit `imu-monocular`. |

Evidence is current checkout inspection plus saved experiment/audit records;
no Docker or hardware commands were run for this document.

# 3. New repository ownership model

Extend existing parent directories; add only missing responsibilities as needed.

| Parent path | Ownership and contents |
|---|---|
| `scripts/pi/` | Our platform checks and, later, controlled native build entry points; record ARM64 dependencies, resource limits and build provenance. |
| `scripts/sensor/` | Our native sensor launch, raw-stream checks and bag record/replay entry points; explicit topic/QoS contracts. |
| `scripts/evaluation/` | Our official EuRoC runners, trajectory evaluation and comparable summaries; separate wrapper-integration results. |
| `config/realsense/` | Our explicit raw IR1/gyro/accel profile, topic names and runtime version manifest; no assumed combined IMU. |
| `config/orbslam3/` | Our estimator mode, calibration provenance and later wrapper launch/remaps; keep official benchmark and D435i integration configurations distinct. |
| `experiments/` | Existing dated evidence runs; add manifests, commands, logs and gate decisions without rewriting historical runs. |
| `results/` | New derived metrics, trajectories and reports keyed to experiment IDs; distinguish `official/` and `wrapper/` results. |
| `docker/` | Existing parent tools Dockerfile remains available; future parent deployment recipes only after re-entry criteria. |
| `third_party/` | Upstream-owned source, preserved at recorded gitlinks, including nested wrapper/calibration dependencies. No edits, deletion or replacement. |
| `data/bags/`, `data/datasets/` | Reuse existing ignored storage for bags and benchmark datasets; track checksums and metadata in experiments. |
| `scripts/env.sh`, `docs/`, `README.md` | Reuse parent environment and documentation entry points; align their guidance with this decision later. |

We own orchestration, configuration, validation and evidence; upstream owns its
source implementation. Future native build/install artifacts stay in ignored
parent workspace paths, outside upstream source. The wrapper's fixed build and
output paths require review before integration; any needed adaptation belongs
in a separately reviewed parent-owned package, not an edit under `third_party/`.

# 4. Native pipeline stages

PASS requires saved evidence, not topic existence or successful launch alone.
Each experiment must declare duration and numeric acceptance limits before it
runs (rates/gaps, error, latency and resource limits as applicable). Missing
criteria or evidence means STOP. No Pi gate is credited from a UTM run.
N4 can proceed independently of Pi/D435i readiness on SSH or Lab; N5 needs N0 and N4, N6 needs N3 and
N5 plus reviewed integration, and N7 needs all preceding evidence.

### N0 — Pi platform

- **Question:** Is the intended native platform ready?
- **Input:** Physical Pi, Ubuntu 24.04 image, power/cooling, network and storage.
- **Output:** Platform manifest and SSH/architecture checks.
- **PASS:** Pi 5, Ubuntu 24.04, `aarch64`/`arm64`, repeatable SSH, adequate resources and no power/thermal faults during the declared check.
- **STOP:** Wrong platform, unreliable access, insufficient storage, power or thermal faults.

### N1 — USB

- **Question:** Does the D435i have a stable direct USB3 connection?
- **Input:** N0, native sensor prerequisites, D435i and known USB3 cable/port.
- **Output:** Device identity, topology/speed, permissions and kernel log.
- **PASS:** Correct device at SuperSpeed (5000M or higher), stable enumeration and intended non-root access.
- **STOP:** 480M fallback, resets/disconnects or device permission failures.

### N2 — raw D435i IR1 + gyro + accel

- **Question:** Can native ROS2 deliver all three raw streams reliably?
- **Input:** N1, recorded SDK/ROS driver versions and explicit raw-stream profile.
- **Output:** Per-stream counts/rates/gaps/timestamps, camera information, parameters and logs.
- **PASS:** IR1, separate gyro and separate accel meet declared full-window limits; timestamps advance, image encoding and motion values are valid, and no sustained stalls or USB resets occur.
- **STOP:** Missing/stalled stream, timing/value failure or access error; combined `/imu` alone cannot pass.
- **Calibration warning:** Must be recorded and investigated, and blocks later VIO qualification until resolved. A warning alone does not fail raw transport: N2 may still PASS if USB/image/gyro/accel continuity and data validity meet the criteria above.

### N3 — rosbag record/replay

- **Question:** Can the accepted sensor evidence be captured and replayed intact?
- **Input:** N2 profile; explicit IR1, gyro, accel, camera-info and relevant calibration/TF topic list.
- **Output:** Checksummed bag, recording metadata and replay validation report.
- **PASS:** Required topics, counts and original message timestamps survive capture/replay within declared loss limits; QoS and playback clock policy are recorded and verified.
- **STOP:** Missing metadata/streams, storage loss, timestamp changes or incompatible replay QoS/clock behavior.

### N4 — official ORB-SLAM3 EuRoC

- **Question:** Does the official estimator establish a native benchmark reference?
- **Input:** Native build of pinned official ORB on SSH or Lab, fixed EuRoC sequence/configuration and ground truth; use monocular-inertial for the intended VIO comparison.
- **Execution:** Functional EuRoC validation may run on SSH or Lab; Lab is preferred for native x86 reference/performance benchmarking. EuRoC remains independent of Pi/D435i readiness.
- **Output:** Build manifest, trajectory, tracking coverage, timing and ground-truth error report.
- **PASS:** Sequence completes with inertial initialization and repeatable coverage/error within declared limits; alignment and evaluation settings are saved.
- **STOP:** Build/run failure, failed initialization, inadequate trajectory coverage or evaluation outside limits; wrapper/fork results cannot substitute.

### N5 — Pi ORB build

- **Question:** Can the same official baseline build and execute natively on Pi?
- **Input:** N0 and N4 pins/dataset; explicit dependency plan and bounded build parallelism.
- **Output:** ARM64 build manifest and EuRoC smoke-run trajectory/resource comparison.
- **PASS:** Native compile/link and dataset execution succeed within declared correctness and resource limits; runtime performance is recorded separately.
- **STOP:** Unresolved dependency/ABI failure, OOM, thermal faults or invalid trajectory; compilation alone is insufficient.

### N6 — saved D435i bag → ROS wrapper

- **Question:** Does reviewed native wrapper integration process validated saved data?
- **Input:** N3 bag, N5, explicitly identified wrapper/estimator revisions, device/profile calibration and `imu-monocular` configuration.
- **Output:** Repeatable offline trajectory, initialization/tracking evidence, timing and frame-contract checks.
- **PASS:** Topic/QoS/clock contracts match; raw-to-combined IMU synchronization and camera–IMU calibration are verified; initialization, tracking and pose semantics meet declared limits.
- **STOP:** Fork/API incompatibility, unverified IMU interpolation/time alignment, sample calibration used without validation, wrong mode/topics or invalid/stale poses.

### N7 — live VIO

- **Question:** Does the validated offline integration sustain live Pi operation?
- **Input:** N6 integration/configuration and the N2 native sensor profile.
- **Output:** Live trajectory, tracking/latency/resource report and reproducible evidence capture.
- **PASS:** Initialization and tracking remain valid over the declared motion/duration; latency, drops and resources stay within limits without growing backlog.
- **STOP:** Repeated tracking loss, timing/calibration failure, unbounded backlog, sensor stalls, USB or power/thermal faults.

# 5. Component provenance

Sources/revisions below identify checked-out code, not proven native binaries.

| Component | Upstream source | Our role | Build/runtime plan |
|---|---|---|---|
| Official ORB_SLAM3 | `UZ-SLAMLab/ORB_SLAM3`, `4452a3c4ab75` | Estimator benchmark and evaluation harness | Native SSH or Lab EuRoC N4 (Lab preferred for native x86 reference/performance benchmarking), then native Pi N5; preserve official identity. |
| ORB_SLAM3_ROS2 | `gjcliff/ORB_SLAM3_ROS2`, `efd7acd9ea31` | Review ROS integration and own future launch/config adaptation | Preserve reference; review native dependency/API/output paths before N6. |
| Embedded ORB fork | `gjcliff/ORB_SLAM3`, `0f29ad5f5632`, nested under wrapper | Identify modified estimator/API dependency | Preserve; any native integration using it is labeled modified-wrapper integration, never official benchmark. |
| realsense-ros | `realsenseai/realsense-ros`, `9a11121700cb` / 4.58.4 | Own sensor contract and source-to-runtime traceability | Select native package or source installation with recorded matching provenance; separately pin librealsense SDK/backend, which is not a parent submodule. |
| Our configs/scripts | Parent repository | Own orchestration, measurements and acceptance criteria | Native-first; record parent SHA, configuration hashes, package versions and actual executable/library provenance per run. |

Official ORB is not a drop-in replacement for the embedded fork: the wrapper
uses additional APIs and its own CMake package export. N4/N5 evaluate the
official estimator; N6/N7 evaluate the explicitly selected integration stack.

# 6. What we can reuse

Labels describe candidate reuse; **no code or assets are copied now**.

| Concept/asset inspected | Classification | Scope |
|---|---|---|
| Mapping launch structure: arguments and conditional visualization/replay | **REUSE AFTER REVIEW** | Keep parameterized orchestration ideas; review paths, clocks, explicit mode, headless defaults and sensor/SLAM separation. |
| D435i monocular and monocular-inertial YAML examples | **REFERENCE ONLY** | Useful settings schema; intrinsics, extrinsics, rates and noise values are not calibration truth for our camera/profile. |
| ROS subscriptions in `src/imu_mono_realsense.cpp` | **REUSE AFTER REVIEW** | Sensor QoS, MONO8 conversion and timestamped IMU conversion are candidates; review queue bounds, image/IMU time boundaries, concurrency and remaps. |
| Pose publication in the same source | **REUSE AFTER REVIEW** | `Tcw.inverse()`, `orb_odom` and TF illustrate integration; verify tracking validity, acquisition timestamps, optical/body frames and camera-to-body transform before reuse. |
| Dockerfiles, Compose and entrypoint ideas | **REFERENCE ONLY** | Retain ROS base/dependency environment, service separation and workspace mounts as later design inputs; review ARM64 builds, permissions, DDS and persistence. |

These assets are in the [preserved wrapper](../third_party/ORB_SLAM3_ROS2/).
No inspected wrapper runtime asset is classified **REUSE DIRECTLY** for the
native baseline; existing parent data/experiment directory conventions can be
reused directly without importing upstream behavior.

# 7. What NOT to migrate

- NVIDIA reservations or existing amd64 image artifacts into the Pi runtime.
- Hard-coded UID/GID 1000/1001, VM device groups, device numbers or container paths.
- Example D435i calibration, static TF or noise values as measured device truth.
- Current IR1 topic mismatch or the launch recorder's unrelated color-topic list.
- Implicit monocular mode for a VIO experiment.
- Unverified combined IMU behavior: `unite_imu_method:=2` alone does not prove interpolation; preserve separate raw streams ([saved IMU findings](../experiments/2026-09-08-d435i-baseline/IMU_NOTES.md)).
- Mandatory GUI, point-cloud/video/map export or full Nav2/PCL features without a gate requirement.
- Upstream source rewrites or VM build/install artifacts to make the native baseline appear ready.

# 8. Immediate next implementation when Pi arrives

1. Boot/SSH/ARM64 verification.
2. ROS installation.
3. Native RealSense installation.
4. D435i USB3 validation.
5. Raw IR1 + gyro + accel sensor gate.

# 9. Docker re-entry criterion

Reconsider Docker after **native sensor PASS (N2/N3) + native official ORB
baseline PASS (N4/N5) + a specific isolation/reproducibility benefit** is identified.
The native reference remains authoritative; moving a wrapper deployment also
requires its native N6/N7 evidence. Compare equivalent inputs, versions and
metrics before accepting any container variant.

| Later option | Reason to consider / evidence needed |
|---|---|
| A. Fully native | Retains the validated path; evaluate whether version manifests and scripted setup already provide sufficient reproducibility. |
| B. Native RealSense + containerized ORB | Isolates estimator dependencies while preserving native device access; measure DDS/QoS, clock, data-transfer and latency behavior. |
| C. Fully containerized | Packages driver and estimator userspace; validate ARM64 images, host-kernel/USB dependency, permissions and all sensor/runtime gates again. |

No final deployment option is selected now. Existing upstream Docker assets
and `docker/Dockerfile.jazzy-tools` remain available as references.

# 10. Repository changes proposed

Only this document is added now. Minimal subsequent parent changes:

1. Update `README.md` with the native-first architecture, machine roles and a link here; cross-link existing bring-up/review documents without rewriting historical evidence.
2. Review `scripts/env.sh` for explicit native ROS setup, domain/RMW choices and an optional, justified FastDDS transport override.
3. Add `scripts/pi/check_platform.sh`, `scripts/sensor/check_usb.sh`, `scripts/sensor/run_native.sh`, `scripts/sensor/check_raw.py` and `config/realsense/d435i_raw.yaml` for N0–N2; resolve device-supported profiles on Pi.
4. Add `experiments/README.md` with the gate/provenance manifest convention; retain all existing experiments. Add `results/README.md` and extend `.gitignore` only for generated build/runtime artifacts, keeping small reports trackable.
5. After N2, add `scripts/sensor/record.sh` and `scripts/sensor/replay.sh` for N3. At N4/N5, add `scripts/evaluation/run_euroc.sh`, `scripts/pi/build_orbslam3.sh` and `config/orbslam3/README.md` documenting benchmark/integration separation.
6. At N6, add reviewed parent wrapper launch/configuration under `config/orbslam3/`; propose a minimal parent ROS package only if API/path adaptation requires code. Keep `third_party/` and existing Docker projects unchanged; add no new Docker deployment yet.
