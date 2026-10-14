# D435i VIO calibration readiness

Status: **NOT READY for validated monocular-inertial VIO**. Camera metadata was
read on 2026-09-13; live timing and motion capture are blocked by repeated Pi
undervoltage. No firmware, EEPROM, calibration, or option write was performed.

Evidence root: [camera session](../experiments/2026-09-13-d435i-camera-capture-20260913T015621Z/).
Primary evidence: [full enumeration](../experiments/2026-09-13-d435i-camera-capture-20260913T015621Z/pi/CAMERA_METADATA_SNAPSHOT/rs-enumerate-complete.txt),
[structured snapshot](../experiments/2026-09-13-d435i-camera-capture-20260913T015621Z/pi/CAMERA_METADATA_SNAPSHOT/structured-v2/metadata.json),
and [unfiltered SDK log](../experiments/2026-09-13-d435i-camera-capture-20260913T015621Z/pi/CAMERA_METADATA_SNAPSHOT/structured-v2/sdk.log).

## Identity and provenance

| Field | Observed value |
|---|---|
| SDK Device Serial | 243322073847 |
| ASIC Serial | 251843061466 |
| Firmware Update ID | 251843061466 |
| Linux USB descriptor serial | 251843061466, separately observed |
| Firmware / IMU | 5.17.3.10 / BMI085 |
| SDK Debian package | ros-jazzy-librealsense2 2.58.4-1noble.20260831.020056 |
| Camera USB branch | 5-1, 8086:0b3a, 5000 Mb/s, no intervening hub in sysfs |
| Canonical HEAD | 593245740fa962ad2325dc531cdb48c21d5f15b2, dirty worktree; bundle hashes identify actual tools |

## Quantity register

| Quantity | Classification | Evidence / remaining requirement |
|---|---|---|
| IR1 640×480 Y8/15 projection | SDK PROVIDED | fx=fy=388.5274353027344; cx=319.10430908203125; cy=239.55616760253906 pixels |
| IR1 distortion | SDK PROVIDED | Brown Conrady; five coefficients zero for this profile. Treat as this SDK stream's projection, not proof that the physical lens has zero distortion. |
| Other image intrinsics | SDK PROVIDED | Full enumeration and per-profile JSON cover available depth, IR1, IR2 and RGB projections; unavailable Y16-profile reads are preserved. |
| IR1 → SDK gyro coordinates | SDK PROVIDED / source default | Identity rotation; translation [-0.005520000122487545, +0.005100000184029341, +0.011739999987185001] m. SDK explicitly reports CAD fallback. Not measured on this unit. |
| Gyro ↔ accelerometer | SDK PROVIDED | Identity transform returned; physical alignment error remains unmeasured. |
| Gyro / accel intrinsic matrices | SDK PROVIDED / source default | Each is identity 3×3 plus zero bias. Logs explicitly report unavailable calibrated intrinsics. |
| IMU noise / bias variances | UNKNOWN / MUST MEASURE | SDK returns zero arrays. These are placeholders, not zero-noise measurements. |
| Gyro noise density / random walk | MUST MEASURE | No device-specific estimate captured. Do not copy BMI055 or another D435i's values into BMI085 qualification. |
| Accel noise density / random walk | MUST MEASURE | Stationary measurements and Allan-deviation analysis needed; short motion capture cannot determine long-term bias walk. |
| Camera / raw motion frequencies | SDK PROVIDED requested capability | IR1 15, gyro 200, accel 100 Hz profiles available. Current 300-second measured qualification absent. |
| ORB combined IMU input frequency | ASSUMED candidate: 200 Hz | Requires explicit offline accel interpolation onto gyro timestamps and verified bracketing. This does not turn the raw accel sensor into 200 Hz. |
| Global-time configuration | SDK PROVIDED | Current value 1 on all three sensor modules; actual frame domains unobserved this session. |
| Camera ↔ IMU time offset | UNKNOWN / MUST MEASURE | Rates and enabled global time cannot establish exposure-to-IMU alignment. |
| ROS headers, CameraInfo, IMUInfo, TF | ROS PROVIDED when captured | Not captured: N2 prerequisite has not passed. |
| Factory calibration provenance | PARTIAL SDK PROVIDED | Read 512-byte active calibration table and advanced-settings JSON. Neither is a full EEPROM dump nor proof of untouched factory history. |

## Meaning of the warning

Preserved warning: “IMU Calibration is not available, default intrinsic and
extrinsic will be used.” The matching-version upstream
[parser](https://github.com/realsenseai/librealsense/blob/v2.58.4/src/ds/ds-calib-parsers.cpp)
emits it when reading the IMU table throws. The precise device-side reason
(absent table, invalid data, read/firmware problem) is not established by that
sentence alone. This unit's additional INFO lines establish actual fallback:
CAD extrinsics, unit sensitivity, and zero bias. The returned noise arrays are
not measured noise statistics. Image calibration is a separate source and is
not invalidated solely by this IMU warning.

The upstream D435i CAD branch is selected by product ID; its comment mentions
BMI055. This device reports BMI085. Do not infer a different IMU model from
that comment, or treat the CAD geometry as measured alignment. The SDK package
is recorded exactly; the archived upstream tag is reference source, not a
verified byte-for-byte reconstruction of the Debian build (log line numbers differ).

## Timestamp investigation still required

Capture each stream's `get_frame_timestamp_domain()` and full-precision
`get_timestamp()` alongside host steady-clock arrival, host UTC arrival, frame
number, exposure/frame metadata, and raw motion values. Preserve domain changes
at startup, repeated/backward stamps, maximum gaps, and common coverage bounds.
SDK timestamps are milliseconds; retain original values before conversion.

The SDK's [global timestamp reader](https://github.com/realsenseai/librealsense/blob/v2.58.4/src/global_timestamp_reader.cpp)
maps device-clock time toward host time. An enabled option is not a measured
camera–IMU exposure offset. Host arrival minus stamp is not pure USB latency.
Do not mix hardware-relative stamps with UTC, or align streams using arrival
time. A later global-time-off diagnostic must be a separate labeled experiment;
do not alter the accepted N2 profile or silently rewrite stamps.

In ROS, preserve original header stamps and bag storage times independently.
Measure header behavior against native evidence; retain full `/tf_static` and
all extrinsics. Equal domains still leave physical alignment unproven.

## Kalibr decision and physical capture instructions

Kalibr or equivalent spatial/temporal calibration is **likely required** before
claiming VIO quality because IMU calibration falls back to source defaults.
The exact scope depends on subsequent intrinsic, timing, and motion evidence.
[Kalibr's requirements](https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration)
include an appropriate IMU model, noise parameters, a fixed known calibration
target, and rotation/translation excitation of all axes. Ordinary textured-room
motion is useful for VIO development; it is not automatically a Kalibr dataset.

Operator procedure, only after stable power, N1/N2 and suitable storage:

1. Keep the Pi fixed and cool. Move the camera with strain relief and enough
   cable slack; do not disturb the USB connector or power lead.
2. Record the fixed target's type, printed/measured dimensions and configuration.
   An AprilGrid is preferable; keep it well lit and visible at varied image
   positions/distances. Record a separate textured-room sequence for VIO.
3. Begin with 10 seconds stationary. Then slowly rotate about each of the three
   axes and translate left/right, up/down, and toward/away from the target.
4. Mix slow and moderate combined motion, avoiding planar-only trajectories,
   violent impacts, saturation and blur. Finish with 10 seconds stationary.
5. Inspect decoded IR frames, target detections, three-axis motion ranges,
   saturation, gaps and common timestamp coverage before classifying usefulness.
   Preserve failed takes and operator notes; never certify by duration alone.
6. Capture separate stationary IMU data for noise analysis while the camera is
   available. Choose duration from the required Allan averaging times; a brief
   record cannot support long-term random-walk claims. Raw SDK CSV rounds motion
   to 0.001, so use full-precision raw messages for this analysis.

No guided sequence has yet been recorded. The operator confirmed a Raspibase PWM fan on the Pi four-pin fan header and
availability for guided motion. The exact supply rating, cable attestation,
a measured target and qualified storage remain open. An inline meter reportedly
shows 5 V at 0.6–0.7 A; its position and transient voltage behavior are unknown.

## Candidate configuration and validation

[ORB-SLAM3 candidate](../experiments/2026-09-13-d435i-camera-capture-20260913T015621Z/orbslam3_ir1_bmi085_candidate.yaml)
uses captured projection and the explicitly provisional SDK CAD transform.
Noise values remain strings that a numeric settings reader must reject.
It is a review artifact, not a runnable calibrated configuration.

`T_b_c1` maps camera coordinates into body/IMU coordinates: `p_b = T_b_c1 p_c`.
This direction follows the actual frame-transform code, despite ambiguous
wording in the upstream example. SDK rotations are column-major arrays;
OpenCV YAML matrix data are row-major. Test a transform and its inverse on
known basis vectors before using a nonidentity matrix.

Next gate: restore stable power → fresh N1 → 20/105/300-second native gates →
timestamp-domain evidence → guided capture → calibrated offline adapter/run.
