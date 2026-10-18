# Gate-to-tool index

This is an operator index for the current checkout, assembled from the tool
READMEs, argument parsers/configuration, and the current project-state,
next-gate, and native-baseline documents. It does not promote any gate. A tool
result is evidence for review; fixture or offline PASS is not a Pi hardware
PASS.

Evidence labels retain the repository convention: MEASURED (observed capture or
run), CALCULATED (derived), SOURCE-SUPPORTED (upstream/project requirement),
INFERRED (implementation/interpretation), ASSUMED (explicit assumption),
PROPOSED (local policy choice), and UNKNOWN (not established).

The hardware-run column is NONE for every tool below. The checkout contains
offline validation, synthetic fixtures, and derived checks of historical files,
but no committed hardware evidence produced by these current tools.

## Gate overview

| Gate | Question | Primary tools | Project state |
|---|---|---|---|
| N0 | Is the Pi platform, power, cooling, storage and software environment ready? | lab/platform_env, lab/power_usb | OPEN; power is not stable |
| N1 | Is the new D435i on a stable direct USB3 connection? | lab/power_usb; raw identity as support | OPEN |
| N2 | Can native ROS 2 deliver separate IR1, gyro and accel reliably? | lab/d435i_raw; saved-take adjuncts | OPEN; new unit not run |
| N3 | Can accepted sensor data be recorded and replayed intact? | lab/rosbag_qual; stamp_drift and n4b_offline adjuncts | OPEN; active gate |
| N4 | Does official ORB-SLAM3 establish the EuRoC reference? | eval_pipeline/accuracy, trajectory_eval, n4a_timing | OPEN; strong N4A evidence, timing invalid |
| N5 | Does the official baseline build and execute natively on Pi? | platform_env, accuracy, profiling/timing | Not started |
| N6 | Does reviewed wrapper integration process a saved bag? | n4b_offline, vio_adapter, calib_tools, frames, run_harness | Not started; N4B OPEN |
| N7 | Does the validated integration sustain live Pi operation? | eval_pipeline/profile; no current live acceptance tool | Not started |

The architecture calls the EuRoC, offline D435i, and live-D435i variants N4A,
N4B, and N4C. N4B/N4C do not substitute for the official N4 baseline.

## N0 — Pi platform

### lab/platform_env/check_platform.py

Question: do read-only software, filesystem, ROS, package, ORB-artifact and
udev facts match the checked-in manifest? The manifest is based on a MEASURED
4 GB Pi 5 stand-in; model and RAM are INFO fields for the 8 GB target.

Exact Pi command from the README:

    cd ~/wbr-perception-phase1-runtime
    source /opt/ros/jazzy/setup.bash
    OUT="$HOME/wbr-evidence/platform-env-$(date -u +%Y%m%dT%H%M%SZ)"
    python3 lab/platform_env/check_platform.py --outdir "$OUT"

Optional commands:

    python3 lab/platform_env/check_platform.py --outdir "$OUT" --write-manifest-candidate
    python3 lab/platform_env/check_platform.py --analyze-only "$OUT"

Criterion IDs are the manifest field names:
pi_model, board_ram_bytes, kernel_release, ubuntu_version, ros_distro,
ros_jazzy_realsense2_camera_package, ros_jazzy_librealsense2_package,
librealsense_sdk_version, d435i_firmware_expected, orbslam3_source_commit,
orbslam3_applied_patches, liborbslam3_sha256, stereo_inertial_euroc_sha256,
pangolin_version, opencv_version, eigen_version, python_version, clocksource,
cpu_governor, swap_bytes, ntp_synchronized, recording_mount,
recording_free_bytes, and d435i_udev_rule_present.

INFO fields do not affect the verdict. Firmware is not probed because the tool
never opens the camera. It does not test power, thermal behavior, USB speed,
storage write rate, ROS streaming, or sustained load. Command durations use
Linux CLOCK_MONOTONIC; collection UTC uses CLOCK_REALTIME; neither is a device
timestamp.

| Hardware run | NONE |
|---|---|
| Limits | Manifest comparison only; no complete N0 qualification |

### lab/power_usb/check_power_usb.py

Question: during a bounded idle or already-reviewed load window, are Pi
voltage/throttle, thermal, USB, kernel and load observations complete and
within policy?

Exact commands from the README:

    python3 lab/power_usb/check_power_usb.py \
      --out lab/power_usb/runs/idle-20261018 --duration 60

    python3 lab/power_usb/check_power_usb.py \
      --out lab/power_usb/runs/load-20261018 --duration 60 --interval 1 \
      --load-cmd 'exec stress-ng --cpu 4'

Saved-evidence reanalysis:

    python3 lab/power_usb/check_power_usb.py \
      --analyze-only lab/power_usb/runs/load-20261018 \
      --out lab/power_usb/runs/load-20261018-reanalysis

Criterion IDs: raw_integrity, under_voltage, ext5v, temperature,
window_coverage, supply, usb_link, usb_topology, kernel_log, load_window.

Numeric policy is in lab/power_usb/thresholds.yaml. The 4.75 V, 80 °C, 5 A,
5000 Mbit/s, sampling and load-coverage limits are PROPOSED or
SOURCE-SUPPORTED as stated there. Device-tree current and PMIC voltage are
software observations, not a complete electrical measurement. The checker
does not open cameras or serial devices. It reads CLOCK_MONOTONIC and
CLOCK_REALTIME; kernel boot timestamps remain in their native domain.

| Hardware run | NONE; the partial fixture is historical context, not a complete run produced by this tool |
|---|---|
| Limits | Idle PASS cannot qualify streaming, N0/N1/N3, or perception performance |

## N1 — D435i USB

There is no separate check_usb entry point. N1 evidence is split between
power_usb and raw SDK identity.

The power_usb commands and IDs are those above, especially usb_link,
usb_topology, kernel_log, under_voltage, ext5v, supply, and window_coverage.
usb_link checks the matched 8086:0b3a sysfs device at the configured
SuperSpeed floor and stable before/after enumeration. It does not assume the
SDK serial identifies the USB descriptor.

The raw checker can add SDK identity/profile evidence:

    python3 lab/d435i_raw/check.py --capture --static \
      --outdir /home/richard/wbr-evidence/d435i-raw-20261018-01

Relevant raw IDs are identity.serial, identity.firmware, and identity.usb_type.
The SDK USB descriptor is not a negotiated bus-speed measurement.

| Hardware run | NONE |
|---|---|
| Limits | No current tool proves cable/power/USB stability for the entire N2/N3 window |

## N2 — raw IR1 + gyro + accel

### lab/d435i_raw/check.py

Question: can the selected new SDK device deliver the configured raw stereo IR
and separate camera-IMU streams for the full window?

Exact commands:

    python3 lab/d435i_raw/check.py --capture --static \
      --outdir /home/richard/wbr-evidence/d435i-raw-20261018-01

    python3 lab/d435i_raw/check.py --capture --static --seconds 120 \
      --outdir /home/richard/wbr-evidence/d435i-raw-20261018-02

    python3 lab/d435i_raw/check.py --capture --static \
      --config lab/d435i_raw/thresholds.yaml \
      --outdir /home/richard/wbr-evidence/d435i-raw-20261018-03

Saved-file modes:

    python3 lab/d435i_raw/check.py --analyze-only \
      /home/richard/wbr-evidence/d435i-raw-20261018-01 \
      --outdir /home/richard/wbr-evidence/d435i-raw-20261018-01-analysis

    python3 lab/d435i_raw/check.py --analyze-only \
      lab/d435i_raw/tests/fixtures/old-unit-smoke \
      --outdir /tmp/d435i-old-unit-analysis-20261018-01

IDs: capture, identity.serial, identity.firmware, identity.usb_type, profiles,
emitter, duration, csv, sample_accounting, stereo, latency_policy,
gyro.static, accel.static, ir_left.ir_content, ir_right.ir_content, and for
each stream in {ir_left, ir_right, gyro, accel}:
stream.samples, stream.rate, stream.receipt_gap, stream.drops, and
stream.timestamps.

Default profile: 848x480 Y8 IR1/IR2 at 30 Hz, emitter OFF, separate gyro at
200 Hz and accel at 100 Hz (native 200 Hz fallback). It is the D435i camera IMU
(imu_camera), never the STM32 body IMU. The tool checks whole-window rates,
frame gaps, same-domain timestamp continuity, stereo pairing, static
plausibility, and sampled image content. It deliberately reports unmapped
latency as UNKNOWN and passes latency_policy only to document that latency was
not credited.

The capture uses SDK/device clocks only within named domains and host callback
CLOCK_MONOTONIC/CLOCK_REALTIME independently. It does not create a camera to
host mapping, prove exposure latency, calibration, focus, scene responsiveness,
or physical N2 PASS.

| Hardware run | NONE; old-unit 243322073847 fixture is MEASURED historical input, not current-unit evidence |
|---|---|
| Limits | PROPOSED raw-stream limits; fixture PASS is not a gate PASS |

### Saved-take adjuncts

lab/calib_record/check_calib_take.py qualifies one finalized D435i recording
before calibration/Allan processing. Exact commands:

    set -euo pipefail
    cd "$HOME/wbr-runtime/calib-check"
    python3 lab/calib_record/check_calib_take.py \
      --take-dir "$HOME/wbr-evidence/2026-10-15-calib-C1" \
      --kind camera-imu --outdir "$HOME/wbr-evidence/check-C1-01"
    python3 lab/calib_record/check_calib_take.py \
      --take-dir "$HOME/wbr-evidence/allan-stationary-15h" \
      --kind allan --outdir "$HOME/wbr-evidence/check-allan-01"

Reanalysis:

    python3 lab/calib_record/check_calib_take.py \
      --analyze-only /absolute/path/to/saved-calib-C1 \
      --kind camera-imu --outdir /absolute/path/to/new-check-C1-02
    python3 lab/calib_record/check_calib_take.py \
      --analyze-only /absolute/path/to/saved-allan-take \
      --kind allan --outdir /absolute/path/to/new-check-allan-02 \
      --config lab/calib_record/criteria.json

IDs: completeness, capture_checksums, samples, metadata, recorder_stop,
sdk_domain, duration, excitation.gyro, excitation.accel,
rate_drops.gyro/rate_drops.accel/rate_drops.ir1/rate_drops.ir2,
timestamp.gyro/timestamp.accel/timestamp.ir1/timestamp.ir2,
stereo_pairing, callback_bag_agreement, ir_dimensions, motion_blur.ir1,
motion_blur.ir2, target_detection, storage.write_headroom,
storage.free_space, input_unchanged, and for Allan takes recorder_counts and
emitter_state; storage is the malformed-storage error path. Missing AprilGrid
counts make target_detection BLOCKED.

tools/take_tools has no common criterion IDs; it returns structural audit/export
status and rejection lists. Exact commands:

    python3 tools/take_tools/take_tools.py inspect stereo_imu.db3
    python3 tools/take_tools/take_tools.py audit stereo_imu.db3
    python3 tools/take_tools/take_tools.py audit stereo_imu.db3 --json audit.json --markdown audit.md
    python3 tools/take_tools/take_tools.py export-euroc stereo_imu.db3 NEW_OUTPUT_DIRECTORY

It keeps SDK, ROS header and bag-writer clocks separate and does not fit a
mapping, calibrate, or prove estimator replay.

| Hardware run | NONE for both tools; historical real-file fixtures are offline evidence |
|---|---|
| Limits | Calibration-take checks are not N2 acceptance limits |

### lab/calib_result — Kalibr result acceptance (Mac-side adjunct)

This check evaluates saved Kalibr camera–IMU and stereo results as calibration
candidates. Pi commands capture the takes; Kalibr fitting and this acceptance
check run on the Mac. The checker is not an N2 stream check and does not establish
physical calibration accuracy.

Run from the repository root on the Mac, using the exact result directories and
factory/profile inputs for the reviewed takes:

    python3 lab/calib_result/check_kalibr_result.py \
      --camimu-chain /path/to/derived/C1-imucam/take-camchain-imucam.yaml \
      --camimu-results /path/to/derived/C1-imucam/take-results-imucam.txt \
      --stereo-chain /path/to/derived/S1-stereo/take-camchain.yaml \
      --stereo-results /path/to/derived/S1-stereo/take-results-cam.txt \
      --run-imu /path/to/derived/C1-imucam/work/imu.yaml \
      --outdir /path/to/derived/C1-acceptance

Saved-evidence reanalysis:

    python3 lab/calib_result/check_kalibr_result.py \
      --analyze-only /path/to/derived/C1-acceptance \
      --outdir /path/to/derived/C1-acceptance-reanalysis

Criteria cover camera–IMU and stereo reprojection residuals, IMU residuals,
camera–IMU time shift and transform, stereo baseline, intrinsics, distortion,
and exact use of the provisional IMU noise parameters. Threshold policy and
per-limit provenance are in `lab/calib_result/thresholds.yaml`; selected
limits are PROPOSED. Missing residual summaries BLOCK. The fixture parser test
derived from a real TUM-VI Kalibr smoke result is not D435i calibration evidence.
Criterion IDs are `imu_translation_delta`, `imu_rotation_delta`,
`cam0_camimu_reprojection_{mean,std}`, `cam1_camimu_reprojection_{mean,std}`,
`cam{0,1}_stereo_reprojection_{mean,std}_{x,y}`,
`gyro_residual_{mean,std}`, `accel_residual_{mean,std}`,
`cam{0,1}_timeshift`, `cam{0,1}_distortion_model`,
`cam{0,1}_{fx,fy,cx,cy}_drift`,
`cam{0,1}_{k1,k2,p1,p2}_distortion_{delta,sanity}`,
`stereo_baseline_delta`, `imu_noise_provenance`,
and `input_available` on blocked input paths.

| Hardware run | NONE; Kalibr and the checker are offline, and fixtures do not qualify physical calibration |
|---|---|
| Limits | Cannot prove target metrology, sensor alignment/time mapping, noise-model validity, runtime behavior, or a project gate PASS |

## N3 — rosbag record/replay

### lab/rosbag_qual

Question: can explicitly selected IR, camera-info, separate gyro and accel
topics be recorded with QoS evidence, inspected, and replayed with the camera
stopped?

Exact recording command:

    source /opt/ros/jazzy/setup.bash
    ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 python3 lab/rosbag_qual/record_check.py \
      --config lab/rosbag_qual/config.json \
      --output-dir /path/to/evidence/record

Exact replay command:

    source /opt/ros/jazzy/setup.bash
    ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 python3 lab/rosbag_qual/replay_check.py \
      --config lab/rosbag_qual/config.json \
      --bag /path/to/evidence/record/bag \
      --output-dir /path/to/evidence/replay \
      --live-domain 42 --replay-domain 43

Exact offline commands:

    python3 lab/rosbag_qual/analyze_bag.py \
      --config lab/rosbag_qual/config.json \
      --bag /path/to/bag \
      --output-dir /path/to/evidence/analyze
    python3 lab/rosbag_qual/analyze_bag.py \
      --config lab/rosbag_qual/config.json \
      --analyze-only /path/to/evidence/analyze

Recording IDs: record:bounded, record:bag_info, record:parameter_dump,
record:topic_qos, record:exit, record:capture_window, record:bag_exists,
record:offline_analysis, and record:saved_input (the last three appear on
their applicable/error paths). Offline qualification adds ir_pairing,
disk:duration, disk:write_rate, and per-topic IDs.

For each configured topic, the analyzer expands:
topic:<name>:present, topic:<name>:count, topic:<name>:header_rate,
topic:<name>:bag_receive_rate, topic:<name>:max_gap, topic:<name>:drops,
topic:<name>:stamp_order, topic:<name>:stamp_repeats,
topic:<name>:bag_receive_order, topic:<name>:cdr, and
topic:<name>:receive_boundary_gap.

Configured names are /camera/camera/infra1/image_rect_raw,
/camera/camera/infra2/image_rect_raw, /camera/camera/infra1/camera_info,
/camera/camera/infra2/camera_info, /camera/camera/gyro/sample,
/camera/camera/accel/sample, and /tf_static. Static TF has presence/count/CDR
coverage but no dynamic rate IDs.

Replay IDs: replay:player, replay:quiet:node_list.json,
replay:quiet:replay_node_list.json, and for each topic
replay:<name>:evidence, replay:<name>:count, replay:<name>:stamps, and (for
rate-configured topics) replay:<name>:rate. replay:saved_input or
replay_check covers blocked input/graph setup.

ROS header.stamp, rosbag2 messages.timestamp, and replay arrival
CLOCK_MONOTONIC are separate. No mapping to D435i hardware/global time is
inferred. The default 16.6 MB/s disk comparison and replay/rate/count limits
are PROPOSED. A gap count is a gap event, not a physical lost-sample count.
SQLite can be parsed with the stdlib; split/MCAP paths need rosbag2_py and can
be BLOCKED.

| Hardware run | NONE; tests use synthetic SQLite/CDR and a portable derived real-bag parser fixture |
|---|---|
| Limits | Passing a synthetic fixture does not qualify Pi storage, USB, QoS, power, thermal state, calibration, or N3 |

### lab/run_lab_session.py

This orchestrator runs power/USB, raw capture, ROS record, isolated replay and
saved calibration qualification in dependency order. It never starts the camera
driver or sources ROS.

    source /opt/ros/jazzy/setup.bash
    python3 lab/run_lab_session.py \
      --session-dir /home/richard/wbr-evidence/session-20261018-01 \
      --calib-take /home/richard/wbr-evidence/calib-C1 \
      --calib-kind camera-imu

    python3 lab/run_lab_session.py \
      --session-dir /tmp/wbr-session-plan \
      --calib-take /home/richard/wbr-evidence/calib-C1 \
      --plan

It has no new physical IDs; SESSION.json aggregates child IDs from power_usb,
d435i_raw, rosbag_record, rosbag_replay, and calib_record. --yes and
--continue-on-fail alter orchestration only.

| Hardware run | NONE; tests use stub check executables |
|---|---|
| Limits | Aggregation does not make a project gate PASS |

## N4 — official EuRoC baseline (N4A)

### tools/eval_pipeline/accuracy

Question: does the pinned official stereo_inertial_euroc complete EuRoC
repeatedly, initialize its IMU, produce enough poses, and remain within the
configured calculated accuracy policy?

Exact Pi runner:

    bash tools/eval_pipeline/accuracy/run_euroc.sh \
      "$HOME/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc" \
      "$HOME/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt" \
      "$HOME/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC.yaml" \
      "$HOME/datasets/euroc/MH01" \
      "$HOME/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt" \
      MH01 3 "$HOME/wbr-evidence/euroc-accuracy/MH01-$(date -u +%Y%m%dT%H%M%SZ)"

Exact evaluator:

    python3 tools/eval_pipeline/accuracy/evaluate.py \
      --sequence MH01 \
      --runs /path/to/run01 /path/to/run02 /path/to/run03 \
      --ground-truth /path/to/MH01/mav0/state_groundtruth_estimate0/data.csv \
      --times /path/to/EuRoC_TimeStamps/MH01.txt \
      --out /path/to/new/evaluation

IDs: all_engine_runs_exit_zero, all_runs_initialized,
se3_ate_rmse_each_run, pose_fraction_each_run. Thresholds are PROPOSED,
including 0.046 m SE3 ATE RMSE and 0.95 minimum pose fraction. The wrapper
records hashes, ldd, throttle snapshots, stdout and command receipts.
Phrase-based tracking diagnostics can miss events if logging changes. EuRoC
accuracy is not D435i accuracy and cannot pass N3/N6/N7.

The shell wrapper has no --help; verified usage is
run_euroc.sh BINARY VOCABULARY SETTINGS DATASET TIMES SEQUENCE RUNS OUTDIR.
The evaluator argparse --help was verified.

| Hardware run | NONE; validation re-evaluates saved historical trajectories |
|---|---|
| Limits | Execution/accuracy evidence is not a compile proof, D435i result, or project gate PASS |

### tools/trajectory_eval

Reusable calculated ATE/RPE engine used by the accuracy pipeline. It has no
common PASS/FAIL/BLOCKED criterion IDs; it emits metrics, assumptions,
association/alignment, hashes and warnings. Primary invocation is the
accuracy evaluator above. It requires explicit format, time unit, clock and
frame assumptions, does not apply extrinsics, and cannot prove synchronization
or frame identity.

| Hardware run | NONE; reads trajectory files offline |
|---|---|
| Limits | Alignment can hide gauge/frame problems; Sim3 is diagnostic |

### experiments/templates/n4a_timing

Question: can a controlled repeated N4A run preserve preflight, resource,
accuracy and latency evidence while making timing validity explicit?

Exact Pi run:

    chmod +x experiments/templates/n4a_timing/*.sh
    bash experiments/templates/n4a_timing/run_n4a_timing.sh \
      --wait-for-cooldown --require-performance \
      /home/pi/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc \
      /home/pi/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt \
      /home/pi/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC.yaml \
      /home/pi/datasets/euroc/MH01 \
      /home/pi/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt \
      MH01 3 /home/pi/wbr-evidence/n4a-timing-$(date -u +%Y%m%dT%H%M%SZ)

Exact analysis:

    python3 experiments/templates/n4a_timing/analyze_n4a_timing.py \
      --experiment /home/pi/wbr-evidence/n4a-timing-YYYYMMDDTHHMMSSZ \
      --sequence MH01 \
      --ground-truth /home/pi/datasets/euroc/MH01/mav0/state_groundtruth_estimate0/data.csv \
      --times /home/pi/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt

--analyze-only DIR is the saved-preflight mode.

Preflight IDs: shared_orb_lock_available,
soc_temperature_below_start_limit, cpu_governor_recorded,
cooling_state_recorded, no_prior_throttle_bits, and (when applicable)
launcher_inputs_present. Capture adds one criterion per run directory
(run01, run02, ...); analysis adds declared_runs_present. Delegated profile
IDs are no_throttle_or_undervoltage and max_temperature.

The profiler uses host CLOCK_MONOTONIC; EuRoC uses its dataset time base; UTC is
provenance only. Only runs with complete capture/preflight/profile/accuracy/event
evidence enter VALID. The README says it cannot prove between-poll power,
calibration, image drops before ORB, camera-to-host mapping, real-time pace, or
an N4/N5/N7 PASS. MH01 is 20 Hz; the unrelated 30 Hz profile budget is not an
MH01 criterion.

| Hardware run | NONE; throttle fixture is derived historical evidence |
|---|---|
| Limits | Timing validity is conditional; it is not real-time qualification |

## N5 — native official Pi build and execution

N5 needs a native compile/link/build manifest as well as execution. No current
dedicated build-check tool with N5 criterion IDs exists. Partial evidence:

- platform_env: orbslam3_source_commit, orbslam3_applied_patches,
  liborbslam3_sha256, stereo_inertial_euroc_sha256, pangolin_version and
  package fields; these are manifest comparisons, not a fresh build.
- accuracy: the four IDs above show a supplied executable ran and was analyzed.
- n4a_timing: preflight/capture/profile IDs add resource evidence, not build
  provenance.

run_harness can exercise a supplied headless engine, but has no common criteria:

    PYTHONDONTWRITEBYTECODE=1 python3 tools/run_harness/harness.py \
      tools/run_harness/examples/orb_pi.yaml --out tools/run_harness/runs/NEW_RUN

Replace every TO-FILL path/domain first. Per-repeat statuses are OK, CRASH,
NO_TRAJECTORY, and TIMEOUT; OK is not a gate PASS. The harness uses host
monotonic duration and delegates trajectory evaluation; it does not sandbox the
filesystem or prove full coverage.

| Hardware run | NONE |
|---|---|
| Coverage gap | No single current criterion proves native compile/link plus bounded N5 execution |

## N6 — saved D435i bag to reviewed wrapper (N4B/offline)

### ros2/wbr_orb_node — ROS wrapper software check and Pi replay candidate

The package implements a proposed recorded/live stereo-plus-combined-camera-IMU
node; its ROS 2 / ORB integration is UNBUILT in this checkout. Host software
check from the repository root:

    make -C ros2/wbr_orb_node test
    python3 ros2/wbr_orb_node/scripts/check_core.py \
      --outdir /path/to/new/software-check
    python3 ros2/wbr_orb_node/scripts/check_core.py \
      --analyze-only /path/to/saved/software-check

The software-check IDs are `all`, `real`, and `emit`. `all` runs C++ fake-engine
assertions, `real` checks preserved source epochs from the saved fixture, and
`emit` checks synthetic health/runtime emission. These are host software checks,
not N6/N7 acceptance IDs. The README also documents `core-test`, a separate
fake-only Pi build, an optional existing-ORB build, and saved-bag replay. The
fake-only Pi build command is:

    colcon build --base-paths ros2/wbr_orb_node --packages-select wbr_orb_node \
      --cmake-args -DWITH_ORB_SLAM3=OFF

The offline replay commands, after sourcing the intended install and with the
camera publisher stopped, are:

    ros2 run wbr_orb_node orb_node --ros-args \
      --params-file "$WBR_ROOT/ros2/wbr_orb_node/config/replay.yaml" \
      -p source_session:=bag-run-unique-id \
      -p output_directory:=/home/richard/wbr-evidence/NEW-orb-replay \
      -p left_topic:=/camera/camera/infra1/image_rect_raw \
      -p right_topic:=/camera/camera/infra2/image_rect_raw \
      -p imu_topic:=/camera/camera/imu
    ros2 bag play /absolute/path/ACCEPTED_BAG --clock

The optional ORB build flags and required parameter details remain in
`ros2/wbr_orb_node/README.md`. These commands require their documented ROS/build
artifacts and their execution is not evidence that the node is live-qualified.
Missing ROS/ORB build evidence, combined-IMU time synchronization, DDS/pre-
callback drops and hard real-time behavior remain UNKNOWN.

| Hardware run | NONE; README marks the ROS/ORB build unexecuted, and host fixtures are software-only |
|---|---|
| Limits | Fake-engine checks cannot qualify estimator behavior, calibration, sensor timing, runtime loss, or N6/N7 |

### tools/n4b_offline

Question: can a finalized SQLite bag be exported and screened as a
time-preserving EuRoC-style input, with ORB settings/provenance explicit before
a Pi wrapper run?

Exact commands:

    python3 tools/n4b_offline/db3_to_euroc.py /path/to/stereo_imu.db3 /path/to/euroc-export
    python3 tools/n4b_offline/qualify_euroc.py /path/to/euroc-export --outdir /path/to/qualify-run
    python3 tools/n4b_offline/qualify_euroc.py --analyze-only /path/to/euroc-export --outdir /path/to/qualify-run-2
    python3 tools/n4b_offline/make_orb_yaml.py --output-dir /path/to/orb-settings --fps 30

Diagnostic runner:

    bash tools/n4b_offline/run_n4b.sh --allow-unpatched \
      "$HOME/orbslam3/ORB_SLAM3" \
      "$HOME/wbr-evidence/2026-10-14-d435i-ramtest15s/euroc-export" \
      "$HOME/wbr-evidence/2026-10-14-d435i-ramtest15s/euroc-export/times_ns.txt" \
      "$HOME/wbr-runtime/n4b-prep-20261013/D435i_317422076650_stereo_inertial.yaml" \
      "$HOME/wbr-evidence/n4b-offline-run"

Qualification IDs: camera_counts, png_files, stereo_stamps, image_order,
imu_order, imu_coverage, image_rate, imu_rate, image_gap, imu_gap, times_file.
Limits are in qualify_config.json and are PROPOSED screening limits. The
exporter uses ROS header.stamp as configured D435i device/global time, ignores
bag receive and librealsense metadata time, and linearly interpolates accel on
gyro stamps. No camera-IMU offset or extrinsics are applied; absent combined
data cannot reveal the driver's unite method.

run_n4b.sh has no --help; verified usage is
run_n4b.sh [--allow-unpatched] ORB_ROOT DATA_DIR TIMES_FILE SETTINGS_YAML OUTDIR.
The normal path refuses without the recorded patched-build checksum;
--allow-unpatched is diagnostic.

| Hardware run | NONE; README explicitly says no physical Pi run and patched checksum is incomplete |
|---|---|
| Limits | Export/qualification is not N6 estimator tracking or calibration proof |

### tools/vio_adapter

Proposed C++ association/snapshot boundary and fake-engine offline replay:

    make -C tools/vio_adapter test
    python3 tools/vio_adapter/euroc_replay.py \
      /Users/quockaiser/Desktop/Research/wbr-data/2026-10-14-d435i-ramtest15s/euroc \
      tools/vio_adapter/NEW_REPLAY_OUTPUT

No common criterion IDs. Outputs are counts/snapshots/summary. Replay always
uses a fake engine, so states/maps/translations are synthetic even with real
input. Optional ORB binding needs caller include/library paths and a qualified
build; it is not compiled here.

| Hardware run | NONE; real_replay is offline association evidence |
|---|---|
| Limits | No trajectory accuracy, latency, calibration, or N6 PASS |

### Supporting calibration/frame tools

calib_tools converts an already-produced Kalibr file and has no common IDs:

    python3 tools/calib_tools/calib_convert.py \
      --camchain tools/calib_tools/tests/fixtures/camchain-imucam.yaml \
      --imu tools/calib_tools/tests/fixtures/imu.yaml \
      --output-dir tools/calib_tools/example-output \
      --target both --fps 30 --units-si

It emits provenance/hashes but does not verify real calibration, clock mapping,
engine loading, image rates, or hardware.

frames has no common IDs and publishes no ROS TF:

    python3 tools/frames/convert_trajectory.py tools/frames/examples/camera.tum \
      --epochs tools/frames/examples/epochs.jsonl \
      --mount tools/frames/examples/mount_proposed.json \
      --time-unit s --sensor-frame camera_optical \
      --pose-direction sensor-to-world --quaternion-order xyzw \
      --output tools/frames/examples/base.synthetic.jsonl

Mount, optical/body convention, reset/map segments and clock domain are
explicit. A proposed mount is not robot calibration.

| Hardware run | NONE for calib_tools and frames |
|---|---|
| Limits | Diagnostic conversion only |

## N7 — live VIO

### tools/eval_pipeline/profile/profile.py

This is the current resource/latency validity tool, not a live VIO launcher.
Exact commands:

    python3 tools/eval_pipeline/profile/profile.py sampler --pid 1234 --out /tmp/wbr-profile-run --period-s 0.1 --throttle-period-s 1.0
    python3 tools/eval_pipeline/profile/profile.py latency --events /tmp/run/events.csv --out /tmp/wbr-profile-run
    python3 tools/eval_pipeline/profile/profile.py latency --tracking /tmp/run/run_tracking.csv --out /tmp/wbr-profile-run
    python3 tools/eval_pipeline/profile/profile.py validity --analyze-only /tmp/wbr-profile-run
    python3 tools/eval_pipeline/profile/profile.py report --run /tmp/wbr-profile-run

Optional mapping: add --clockmap /path/to/qualified-map.json to latency.
Criterion IDs are no_throttle_or_undervoltage and max_temperature. Latency
percentiles and realtime fields are metrics, not acceptance IDs. Validity fails
on sampled current/historical throttle bits and blocks on missing telemetry.
The profiler adds observer load and cannot see between polls, image backlog,
camera-IMU timing, pose correctness, or physical gate status.

| Hardware run | NONE; fixtures include only a derived historical N4A row |
|---|---|
| Coverage gap | No current tool starts reviewed live VIO and evaluates initialization, sustained tracking, latency, drops, resources, and power together |

The perception-health integration README also documents this future pipeline,
but marks its prerequisites as not implemented and does not make it an N7
check:

    set -euo pipefail
    python3 -B tools/perception_health/integration/vio_to_pose_events.py \
      --input /run/wbr/vio/snapshots.fifo \
      --snapshot-session "$(cat /run/wbr/vio/session-id)" \
      --clockmap /run/wbr/vio/camera-to-pi-raw.json \
      | python3 -B tools/perception_health/py/sender.py \
          --device /dev/ttyAMA0 --baud 115200

There is no live producer, qualified clockmap, UART hardware check, firmware
parser, or reviewed runtime behind this command in the checkout. Its software
integration IDs are listed in the supporting inventory below; hardware run is
NONE.

## NEXT_GATE N3 candidate criteria mapped line by line

This maps each line in docs/NEXT_GATE.md to current tool IDs. A mapping means
the tool can produce relevant evidence; it does not mean the criterion is met
or that tool policy is the project policy.

| Candidate criterion | Tool IDs / coverage | Result |
|---|---|---|
| D435i enumerates normally | power_usb: usb_link, usb_topology; d435i_raw: identity.serial, identity.firmware, identity.usb_type | Partial; no standalone enumeration-only check |
| Required infrared and IMU streams exist | d435i_raw: profiles, *.samples, stereo; rosbag_qual: topic:<name>:present, topic:<name>:count | Covered with configured assumptions |
| Actual rates are measured | d435i_raw: *.rate; rosbag_qual: topic:<name>:header_rate, topic:<name>:bag_receive_rate; calib_record: rate_drops.*; n4b_offline: image_rate, imu_rate | Covered with separate clock labels |
| Timestamp behavior inspected | d435i_raw: *.timestamps; rosbag_qual: `topic:<name>:stamp_order`, `topic:<name>:stamp_repeats`, `topic:<name>:bag_receive_order`, `topic:<name>:max_gap`; n4b_offline: image_order, imu_order, times_file; stamp_drift: `<topic>:fit`, `<topic>:continuity` | Covered per clock plus a diagnostic header/receive fit; mapping remains UNKNOWN |
| QoS documented | rosbag_qual: record:topic_qos plus qos_overrides.yaml/topic_info.json/config | Covered as documentation; physical compatibility still needs run |
| Bounded rosbag recorded | rosbag_qual: record:bounded, record:exit, record:capture_window, record:bag_exists | Covered |
| ros2 bag info succeeds | rosbag_qual: record:bag_info | Covered |
| Bag replays with live camera stopped | rosbag_qual: replay:quiet:node_list.json, replay:quiet:replay_node_list.json, replay:player | Covered by graph checks; no physical run |
| Replayed representative topics measurable | rosbag_qual: replay:<name>:evidence, replay:<name>:count, replay:<name>:stamps, replay:<name>:rate | Covered |
| No serious USB/kernel failure | power_usb: usb_link, usb_topology, kernel_log, under_voltage | Covered only with the same complete observation window |
| Pi power/throttling recorded | power_usb: under_voltage, ext5v, temperature, supply, window_coverage; profile: no_throttle_or_undervoltage, max_temperature | Covered as separate diagnostics; polling limits remain |
| Evidence preserved in dedicated experiment directory | Output/raw-file contracts; raw_integrity, record:saved_input, input_unchanged support preservation | No single criterion asserts the project-level experiment-manifest requirement |

### tools/stamp_drift (N3 timestamp diagnostic)

This offline diagnostic compares each supported topic's ROS `header.stamp`
with the rosbag2 `messages.timestamp` receive value. On the Pi, analyze a
finalized DB3 from the repository root:

    python3 tools/stamp_drift/analyze.py /qualified/path/bag_0.db3 \
      --header-clock D435I_GLOBAL_TIME --global-time-enabled true \
      --output-dir /qualified/path/stamp-drift

Only declare `D435I_GLOBAL_TIME` when the effective RealSense parameter
readback is recorded; otherwise use the documented hardware, system, or
unknown domain. Offline CSV and saved-report commands are documented in
`tools/stamp_drift/README.md`.

The per-topic criteria are `<topic>:fit` and `<topic>:continuity`. The first
requires every segment to have a usable positive-slope affine fit; the second
checks detected reversals and residual steps against configured limits in
`tools/stamp_drift/config.json`. These diagnostic thresholds are PROPOSED.
The JSON and markdown statuses are diagnostics, not N3 verdicts. The fit cannot
separate clock offset from transport delay or prove exposure latency, sensor
synchronization, or which timestamp domain was actually active.

| Hardware run | NONE; saved historical/conversion fixtures are offline and are not live ROS recorder evidence |
|---|---|
| Limits | Diagnostic only; no absolute latency or cross-clock mapping |

No candidate line is silently treated as PASS because a matching ID exists.
NEXT_GATE also asks for project-state/evidence-index updates; this ticket owns
only this index and does not alter those files.

## Clock domains used by the tooling

| Name | Linux API or device clock | Tools | Boundary/limit |
|---|---|---|---|
| D435i hardware_clock | librealsense device hardware clock | d435i_raw, calib_record, take_tools, clockmap | Same named device domain/session only |
| D435i global_time | librealsense global conversion using device and OS system time | d435i_raw, take_tools, n4b_offline, clockmap | Not host steady time; analyzer proxy is not an online map |
| D435i system_time | SDK-reported/system-time domain | d435i_raw, take_tools, calibration checks | Retained separately; no cross-clock subtraction |
| ROS header.stamp | Driver message timestamp | rosbag_qual, n4b_offline, take_tools | Separate from rosbag receive time; mapping is UNKNOWN |
| rosbag2 messages.timestamp | Bag writer/receive timestamp | rosbag_qual, take_tools | Not a device/exposure timestamp |
| Linux host steady | CLOCK_MONOTONIC | platform_env, power_usb, d435i_raw, calib_record, replay arrival, runtime_observer, profile, n4a_timing | Same-host intervals only unless explicitly mapped |
| Linux raw steady | CLOCK_MONOTONIC_RAW | clockmap integration, perception_health integration | Session/boot-qualified T7 mapping contract |
| Linux wall time | CLOCK_REALTIME/UTC | platform, power, raw capture, calibration receipts, profiling provenance | Provenance only; not an interval clock |
| EuRoC dataset time | Dataset timestamps/ORB output | accuracy, trajectory_eval, n4a_timing, run_harness | Common-dataset assumption does not establish live sync |
| Adapter source epoch | Integer ns in declared domain | vio_adapter, frames, run_harness, health integration | Session/domain changes require a new adapter/session |
| MCU timer | Link-bench TIM2 at 1 MHz; health model simulated/local timer | link_bench, health integration | MCU-local deadlines are not Pi/camera epochs |
| STM32 body IMU | Controller-owned sensor clock/data | None of these D435i checks | Explicitly outside scope; never relabel camera IMU |

clockmap is the only mapping library here. Its three-exchange minimum and
1 ms step threshold are PROPOSED; maps are session-scoped and uncertainty
bearing. Raw capture and N3 tools intentionally withhold unmapped latency.

## Tools without direct N0–N7 coverage

| Tool | Exact documented invocation | Outputs/IDs | Limits and hardware run |
|---|---|---|---|
| tools/clockmap | python3 tools/clockmap/analyze.py /path/to/timestamps.csv | JSON diagnostics, no common IDs | Offline diagnostic fit, not online map/latency proof. NONE |
| tools/runtime_observer | make -C tools/runtime_observer test; aggregate.py, patch_timing.py, resource_sampler.py as documented | Trace/resource fields, no common IDs | Observer loss/overhead and mapping limits. NONE |
| tools/perception_health | python3 tools/perception_health/py/sender.py --device /dev/ttyAMA0 --baud 115200 --input /path/to/pose_events.jsonl | Prototype codec/model, no N0–N7 IDs | Not firmware/safety/gate evidence. NONE |
| tools/perception_health/c/mcu | make -C tools/perception_health/c/mcu test | Host parity scenarios: sequence gaps/duplicates, CRC rejection, source-age HOLD/FAILSAFE, saturation/unavailable age, LOST, silence, timer wrap; no N0–N7 IDs | Host-only candidate; target integration, timing, firmware and safety are unverified. NONE |
| tools/perception_health/integration | e2e_pty_test.py --outdir <tmp>/full --summary-outdir <tmp>/summary; --analyze-only | *.transport, no_mapping, mapped_ok, lost_latched, sender_stops, real_replay | PTY/software criteria, synthetic mapping, simulated MCU timer. NONE |
| tools/ros2_bridge | python3 -m unittest discover -s tools/ros2_bridge/tests -v; make -C tools/ros2_bridge test | No common IDs | Explicitly UNBUILT; no rclcpp/ORB/live bridge. NONE |
| tools/link_proto | make -C tools/link_proto test; unittest discover tools/link_proto/tests | No common IDs | CANDIDATE protocol, not accepted STM32 interface. NONE |
| tools/link_bench | python3 link_bench.py --port /dev/ttyAMA0 --out OUT; --loopback; or /dev/ttyACM0 | summary/rtt/fault/timeout, no N0–N7 IDs | Requires Nucleo/serial hardware; F446 stand-in, not STM32H7. NONE |
| tools/calib_tools | calib_convert.py ... --target both --fps 30 --units-si | Provenance/hash output, no common IDs | Synthetic inputs; no real calibration/runtime proof. NONE |
| tools/frames | convert_trajectory.py ... --sensor-frame camera_optical ... | Custom JSONL, no common IDs | Diagnostic mount conversion; no mount qualification. NONE |
| tools/take_tools | inspect/audit/export-euroc commands above | Audit status/rejections, no common IDs | Structural decoder/exporter only. NONE |
| tools/run_harness | harness.py tools/run_harness/examples/orb_pi.yaml --out tools/run_harness/runs/NEW_RUN | Per-repeat OK/CRASH/NO_TRAJECTORY/TIMEOUT | Headless attestation, not sandbox/coverage/gate PASS. NONE |
| tools/vio_adapter | make test; euroc_replay.py DATA NEW_OUTPUT | Counts/snapshots/summary, no common IDs | Fake-engine replay; optional ORB binding not compiled. NONE |
| lab/calib_result | check_kalibr_result.py --camimu-chain ... --camimu-results ... --stereo-chain ... --stereo-results ... --run-imu ... --outdir ...; --analyze-only DIR --outdir ... | Calibration result acceptance criteria described above; no N0–N7 IDs | Offline candidate screening only; physical calibration unverified. NONE |
| ros2/wbr_orb_node | `make -C ros2/wbr_orb_node test`; `check_core.py --outdir DIR` / `--analyze-only DIR` | Software-check IDs: `all`, `real`, `emit`; not common gate IDs | Software-only check; ROS 2 / ORB integration UNBUILT and hardware run NONE |

Optional ticket paths absent from this checkout are `tools/deploy/` and a
top-level `ros2/` directory; this checkout has `ros2/wbr_orb_node/`, documented
above. `tools/eval_pipeline/` and `tools/stamp_drift/` are present and indexed
above. No command or criterion is invented for an absent path.

## Verification

See the review record for the exact commands, test results, and CLI checks run
for this index update. This is CALCULATED software evidence only, not hardware
evidence.
