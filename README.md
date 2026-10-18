# WBR Perception Phase 1 Runtime

Perception/runtime research and experiment workspace for a wheel-biped robot (WBR).
Phase 1 benchmarks official ORB-SLAM3, validates Intel RealSense D435i sensing,
records repeatable ROS 2 datasets, evaluates ORB_SLAM3_ROS2 offline and live,
and characterizes failure modes before robot integration.

The native reference is Raspberry Pi 5 (8 GB), Ubuntu 24.04 ARM64 and ROS 2 Jazzy.
**Pi owns perception; STM32H7 owns balance and safety.** The intended data flow is
`D435i → Pi ORB-SLAM3 / VIO → ROS 2 → state estimation / autonomy → high-level references → STM32H7`.
STM32H7 retains hard-real-time balance, LQR, VMC, PID/PD, jump control, actuator
torque and CAN. The D435i camera IMU is distinct from the STM32 body IMU.
Docker is deferred until native success; see the [baseline architecture](docs/NATIVE_PI5_BASELINE_ARCHITECTURE.md).

Start with [project state](docs/PROJECT_STATE.md), the [next active gate](docs/NEXT_GATE.md),
and the [gate-to-tool index](docs/GATE_TOOLING.md). These describe open work and evidence limits;
the presence of tools or successful builds does not establish a gate PASS.

## Repository map

Directories without a root README link to their contents and relevant entry points.

| Directory | Contents / entry point |
| --- | --- |
| [.github/](.github/) | [CI README](.github/README.md): host test runner, discovery and workflow. |
| [calibration/](calibration/) | [AprilGrid targets](calibration/aprilgrid/README.md), [Allan analysis](calibration/allan/README.md), [lab calibration workflow](calibration/lab/README.md). |
| [data/](data/) | Ignored [bags](data/bags/) and [datasets](data/datasets/); keep large recordings outside Git. |
| [docker/](docker/) | [Jazzy tools Dockerfile](docker/Dockerfile.jazzy-tools); [architecture review](docs/DOCKER_RUNTIME_ARCHITECTURE_REVIEW.md). |
| [docs/](docs/) | Architecture, calibration plans, audits, project state and gates; start at [GATE_TOOLING](docs/GATE_TOOLING.md). |
| [experiments/](experiments/) | Dated evidence and historical reports; [timing protocol README](experiments/templates/n4a_timing/README.md). |
| [lab/](lab/) | [README](lab/README.md): bounded qualification checks and session orchestration; individual check READMEs are indexed in [GATE_TOOLING](docs/GATE_TOOLING.md). |
| [queue/](queue/) | [Task rules](queue/tasks/COMMON_QUEUE.md) and implementation briefs. |
| [research/](research/) | [Software foundation proposal](research/sw-foundation/PROPOSAL.md) and component/architecture research. |
| [ros2/](ros2/) | [wbr_orb_node README](ros2/wbr_orb_node/README.md): native ORB adapter ROS package and host tests. |
| [scripts/](scripts/) | [env.sh](scripts/env.sh): repository root and ROS environment settings. |
| [third_party/](third_party/) | Pinned upstream submodules listed in [.gitmodules](.gitmodules); preserve upstream source ownership. |
| [tools/](tools/) | Host tests and reusable tooling listed below. |

### Tools

Each link opens the tool's README; `eval_pipeline/` groups accuracy and profiling.

| Tool directory | Purpose |
| --- | --- |
| [calib_tools](tools/calib_tools/README.md) | Convert Kalibr calibration into ORB-SLAM3/OpenVINS settings with provenance. |
| [clockmap](tools/clockmap/README.md) | Session-scoped clock mapping and timestamp diagnostics. |
| [deploy](tools/deploy/README.md) | Checksummed Pi bundles, deployment, rollback and offline smoke checks. |
| [eval_pipeline/](tools/eval_pipeline/) | [Accuracy README](tools/eval_pipeline/accuracy/README.md) and [profile README](tools/eval_pipeline/profile/README.md). |
| [eval_pipeline/accuracy](tools/eval_pipeline/accuracy/README.md) | Repeated official EuRoC runs and trajectory accuracy reports. |
| [eval_pipeline/profile](tools/eval_pipeline/profile/README.md) | Pi resource/latency profiling with power and thermal validity checks. |
| [frames](tools/frames/README.md) | Diagnostic sensor-to-robot pose conversion with explicit frames. |
| [link_bench](tools/link_bench/README.md) | Diagnostic Pi–MCU link bench; Nucleo-F446RE is a stand-in, not the STM32H7 controller. |
| [link_proto](tools/link_proto/README.md) | Candidate COBS/CRC-32C codec and receiver policy; firmware-owner review required. |
| [n4b_offline](tools/n4b_offline/README.md) | D435i bag export, qualification, settings generation and offline ORB runs. |
| [perception_health](tools/perception_health/README.md) | Health-message prototype using a separate protocol from link_proto. |
| [perception_health/c/mcu](tools/perception_health/c/mcu/README.md) | MCU receiver/policy implementation and host verification. |
| [perception_health/integration](tools/perception_health/integration/README.md) | Software end-to-end pose/health integration and evidence analysis. |
| [ros2_bridge](tools/ros2_bridge/README.md) | Diagnostic pose/health bridge skeleton; ROS build remains unverified. |
| [run_harness](tools/run_harness/README.md) | Repeatable headless engine orchestration with preserved run evidence. |
| [runtime_observer](tools/runtime_observer/README.md) | Event recording, resource sampling and offline timing aggregation. |
| [stamp_drift](tools/stamp_drift/README.md) | ROS header-stamp versus bag receive-time drift diagnostics. |
| [take_tools](tools/take_tools/README.md) | Inspect, audit and export saved D435i recorder streams. |
| [trajectory_eval](tools/trajectory_eval/README.md) | Offline time association, SE3/Sim3 alignment, ATE and RPE. |
| [vio_adapter](tools/vio_adapter/README.md) | Native VIO interface, sensor association, fake engine and optional ORB binding. |

## Quickstart

Run commands from the repository root unless a `cd` is shown. Host tests require
Python 3.11+ (Pi: 3.12), NumPy, PyYAML, make and host C/C++ compilers already available.
They use fixtures/simulators and do not require ROS, ORB or physical devices.

```bash
git clone --recurse-submodules https://github.com/KaiserRichard/wbr-perception-phase1-runtime.git
cd wbr-perception-phase1-runtime
bash tools/run_all_tests.sh
```

From the Mac, preview deployment using a fake host; then deploy a clean checkout
to your configured SSH alias `pi5`. The bundle excludes datasets, upstream sources
and most experiment evidence; it does not install ROS, ORB or sensor dependencies.
See [deployment prerequisites and rollback](tools/deploy/README.md).

```bash
bash tools/deploy/deploy.sh fake-pi --dry-run --allow-dirty
bash tools/deploy/deploy.sh pi5
```

On the Pi, plan a lab session with a new evidence directory and an existing saved
calibration take (replace the example take path). `--plan` only prints commands
and prompts; it creates no session and performs no capture. After reviewing the
[lab instructions](lab/README.md) and qualifying power/cooling/storage, omit
`--plan` to run. The operator starts the ROS camera driver and stops it before replay.

```bash
cd "$HOME/wbr-tools/current"
source /opt/ros/jazzy/setup.bash
python3 lab/run_lab_session.py --session-dir "$HOME/wbr-evidence/session-01" \
  --calib-take "$HOME/wbr-evidence/calib-C1" --calib-kind camera-imu --plan
```

For EuRoC, first prepare the official native ORB build and extracted dataset on
the Pi. Set these example paths to the actual locations and use a fresh output
directory. The [accuracy README](tools/eval_pipeline/accuracy/README.md) explains
inputs, criteria and limitations. Evaluation can also run on the Mac with saved files.

```bash
ORB="$HOME/orbslam3/ORB_SLAM3"
EUROC="$HOME/datasets/euroc/MH01"
OUT="$HOME/wbr-evidence/euroc-MH01-01"
bash tools/eval_pipeline/accuracy/run_euroc.sh \
  "$ORB/Examples/Stereo-Inertial/stereo_inertial_euroc" "$ORB/Vocabulary/ORBvoc.txt" \
  "$ORB/Examples/Stereo-Inertial/EuRoC.yaml" "$EUROC" \
  "$ORB/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt" MH01 3 "$OUT"
python3 tools/eval_pipeline/accuracy/evaluate.py --sequence MH01 \
  --runs "$OUT/run01" "$OUT/run02" "$OUT/run03" \
  --ground-truth "$EUROC/mav0/state_groundtruth_estimate0/data.csv" \
  --times "$ORB/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt" --out "$OUT/evaluation"
```

## Evidence rules

Use **MEASURED** for observations, **CALCULATED** for derived values,
**SOURCE-SUPPORTED** for cited requirements, **INFERRED** for interpretations,
**ASSUMED** for explicit assumptions, and **UNKNOWN** for unverified claims.
Mark locally chosen numeric acceptance thresholds **PROPOSED**; keep thresholds
in the relevant tool's YAML/JSON policy with a source or rationale.
Name every timestamp's clock domain; subtraction across clocks requires an explicit
documented mapping (D435i hardware/global time, ROS header.stamp, Linux monotonic/realtime, MCU timer).
Preserve raw logs, identities, versions, commands, configurations and hashes.
**Fixture/test PASS is tooling evidence, not a gate PASS.** EuRoC accuracy does not
qualify D435i operation or sustained Pi timing. Review raw evidence against declared
criteria and the [active gate](docs/NEXT_GATE.md); hardware behavior remains UNKNOWN until verified.
