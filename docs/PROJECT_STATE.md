# Project State

> Canonical short summary updated 2026-10-18. **[INFERRED]** This is a software/documentation refresh from the tool index and saved evidence; no new hardware run was made. **[SOURCE-SUPPORTED]** Gate statuses below are unchanged and nothing here is a gate PASS. See the [gate-to-tool index](GATE_TOOLING.md) for scope and limits.

## Hardware (as of 2026-10-14)

| Item | State | Evidence |
|---|---|---|
| Raspberry Pi 5 | **[MEASURED]** 8 GB board boots the existing card; a 4 GB board was the stand-in on 2026-10-13 | [2026-10-14 session addendum](../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md) §1 |
| Boot / storage | **[MEASURED]** 32 GB microSD in use, no NVMe. **[SOURCE-SUPPORTED]** 128 GB V30/A2 microSD ordered; recordings go there after write qualification | [2026-10-13 session facts](../experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md) §A, §F; [calibration plan](D435I_CALIBRATION_PLAN.md) |
| 64 GB USB stick | **[MEASURED]** Not suitable for recording: USB 2.0, 1.09 MB/s with fsync | [2026-10-14 session addendum](../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md) §6 |
| Power | **[MEASURED]** Under-voltage on the 5 V / 3 A supply with both boards. **[SOURCE-SUPPORTED]** 5.1 V / 5 A supply ordered | [2026-10-13 session facts](../experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md) §A; [2026-10-14 session addendum](../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md) §1 |
| D435i | **[MEASURED]** New unit: SDK serial 317422076650, FW 5.17.3.10, BMI085. Old-unit 243322073847 evidence does not transfer | [camera swap addendum](../experiments/2026-10-13-pi5-env-snapshot/ADDENDUM_CAMERA_SWAP.md) |
| Controller | **[SOURCE-SUPPORTED]** STM32H7 owns balancing, control and safety; outside Phase-1 perception scope | [project architecture](../README.md) |

## Gate picture

**[SOURCE-SUPPORTED]** Gate names follow the project instructions (N0–N7). [Native Pi baseline §4](NATIVE_PI5_BASELINE_ARCHITECTURE.md#4-native-pipeline-stages) numbers ORB steps differently (N4 EuRoC, N5 Pi build, N6 saved bag, N7 live); the [calibration plan](D435I_CALIBRATION_PLAN.md#gate-naming-and-deviations-from-the-main-branch-baseline) maps the two schemes. Tool links below mean software is available, not that the tool has been run on hardware. **[SOURCE-SUPPORTED]** Every tool in the [gate tooling index](GATE_TOOLING.md) has hardware-run status NONE.

| Gate | Status (unchanged) | Evidence / what is missing | Tooling ready (software only, not hardware-validated) |
|---|---|---|---|
| N0 Platform | OPEN | **[MEASURED]** Pi 5, Ubuntu 24.04, ROS 2 Jazzy run ([environment snapshot](../experiments/2026-10-13-pi5-env-snapshot/)); **[MEASURED]** power remains unresolved | [platform_env](../lab/platform_env/README.md) checks software/manifest facts; [power_usb](../lab/power_usb/README.md) records power, thermal, USB and kernel observations. Neither is a complete N0 qualification. |
| N1 D435i access (new unit) | OPEN | **[MEASURED]** New-unit N1 stopped at the clock prerequisite, since fixed ([session facts](../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md) §§B, E); no new-unit physical verification | [power_usb](../lab/power_usb/README.md) provides `usb_link`, `usb_topology`, `kernel_log`, and power criteria; [d435i_raw](../lab/d435i_raw/README.md) adds SDK identity/profile evidence. |
| N2 Raw IR + IMU qualification (new unit) | OPEN | **[UNKNOWN]** Not run on the new unit. Old-unit September runs are retained as historical evidence ([2026-09-12](../experiments/2026-09-12-pi5-native-sensor-validation/), [2026-09-13](../experiments/2026-09-13-d435i-post-reboot-20260913T023833Z/)) | [d435i_raw](../lab/d435i_raw/README.md) checks raw stereo IR and separate camera gyro/accel streams; profile and limits are configured in its [thresholds](../lab/d435i_raw/thresholds.yaml). It does not qualify the selected VIO 640×480 profile unless configured accordingly. |
| N3 ROS 2 pipeline + record/replay | OPEN | **[INFERRED]** Active gate; no new-unit hardware evidence, see [NEXT_GATE](NEXT_GATE.md) | [rosbag_qual](../lab/rosbag_qual/README.md) records, analyzes, and replays; [stamp_drift](../tools/stamp_drift/README.md) diagnoses header/receive-time relation. These do not establish a cross-clock map or physical gate result. |
| N4A Known-dataset baseline (EuRoC MH01 on the Pi) | OPEN, strong evidence | **[MEASURED]** 3 runs, ATE RMSE 0.0415 / 0.0368 / 0.0416 m; IMU initialized each run. **[UNKNOWN]** Timing invalid because of throttling ([report](../experiments/2026-10-13-n4a-euroc-mh01/REPORT.md)) | [accuracy](../tools/eval_pipeline/accuracy/README.md), [trajectory_eval](../tools/trajectory_eval/README.md), and [n4a_timing](../experiments/templates/n4a_timing/README.md) cover trajectory/error and timing evidence. |
| N4B D435i offline stereo-inertial | OPEN | **[MEASURED]** Programs built ([prep](../experiments/2026-10-13-n4b-d435i-prep/)). First offline run crashed on an upstream null-pointer bug; **[INFERRED]** patch written, Pi rebuild pending ([session addendum](../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md) §5) | [n4b_offline](../tools/n4b_offline/README.md) exports and qualifies saved input; [vio_adapter](../tools/vio_adapter/README.md) provides fake-engine replay; [run_harness](../tools/run_harness/README.md) runs headless supplied engines. None verifies patched Pi rebuild or N4B tracking. |
| N4C D435i live | OPEN | **[UNKNOWN]** Not attempted | [profile](../tools/eval_pipeline/profile/README.md) measures resource/latency validity for a supplied process; **[SOURCE-SUPPORTED]** no current tool starts reviewed live VIO and establishes N7 acceptance ([GATE_TOOLING](GATE_TOOLING.md#n7--live-vio)). |
| N5–N7 | Not started | **[UNKNOWN]** No gate evidence | **[SOURCE-SUPPORTED]** N5 has partial manifest/accuracy/timing tools but no dedicated build check; N6 has [wrapper software checks](../ros2/wbr_orb_node/README.md) and offline tools; N7 has [profile](../tools/eval_pipeline/profile/README.md), but no live acceptance tool. Details: [GATE_TOOLING](GATE_TOOLING.md#n5--native-official-pi-build-and-execution). |

## Decisions and proposal status

- **Canonical stream profile — `d435i_vio_v1`, 640×480 Y8 stereo IR at 30 Hz, separate camera gyro at 200 Hz and accel at 100 Hz, emitter off. [ASSUMED decision / SOURCE-SUPPORTED inputs]** The [calibration plan](D435I_CALIBRATION_PLAN.md#1-stereo-ir-intrinsics) records factory IR intrinsics at 640×480 and uses that resolution; 30 Hz is the selected VIO/calibration acquisition rate to match the SLAM configuration. Profile support and sustained delivery on the new unit remain **[UNKNOWN]** until attested. This is distinct from the current [raw check default](../lab/d435i_raw/thresholds.yaml), which is 848×480 at 30 Hz and requires a per-run config for this decision; neither profile substitutes for the other. **[ASSUMED]** Its higher stream demand makes storage qualification and full-profile N2/N3 checks prerequisites.
- **PERCEPTION_HEALTH — candidate; firmware owner review required. [SOURCE-SUPPORTED]** The optional protocol-v3 `0x05` proposal is documented in [SPEC](../tools/perception_health/SPEC.md) and [README](../tools/perception_health/README.md). It remains a software prototype, not firmware integration or a safety interface; STM32 retains control and hard safety.
- **CI — exists for host software tests. [SOURCE-SUPPORTED]** [`.github/workflows/tests.yml`](../.github/workflows/tests.yml) runs on pushes and pull requests; operating instructions and limits are in [CI README](../.github/README.md). **[MEASURED]** A CI workflow is present in this repository; it does not run hardware gates or imply Pi validation.

## Current blocking question

**[MEASURED]** Can the Pi sustain the selected D435i stereo-inertial stream without dropped frames? The 5 V / 3 A supply showed under-voltage and the existing card sustained 16.6 MB/s against 18.4 MB/s estimated stream demand; recording into RAM gave zero dropped frames over 15 s as a workaround ([2026-10-14 addendum](../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md) §§1, 3–4). **[UNKNOWN]** Whether the ordered 5 A supply and 128 GB card resolve these constraints; both require qualification.

## Evidence quality rule

**[SOURCE-SUPPORTED]** A screenshot, successful build, tool fixture, or one successful launch is not enough to promote a gate to PASS. Tool results require evidence review under the gate criteria; no status changes in this update.
