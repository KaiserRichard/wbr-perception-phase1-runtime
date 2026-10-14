# D435i stereo-inertial calibration plan — N4B/N4C

Status: **OPEN**. SDK serial **317422076650**; no calibration or gate is qualified by this document.
MEASURED factory stereo readback remains the operating calibration; Kalibr validates it.
INFERRED nominal camera–IMU geometry and ASSUMED noise require independent evidence.
SOURCE-SUPPORTED conventions below fix transform directions, noise units and time-shift sign.
ASSUMED protocol: three 30 Hz target takes, separate stationary Allan data, then paired N4B ablations.
All acquisition is future local Pi work after `CAMERA AVAILABLE`, stable power and the required gates.
The D435i BMI085 frame `imu_camera` is separate from STM32 frame `imu_body`.
Body-IMU calibration is **OUT OF SCOPE**; no fusion, frame substitution or controller-IMU input is permitted.

Authorship: drafted by Codex from a reviewer brief; reviewed by Claude on 2026-10-13.
Reviewer verification: the three Kalibr wiki pages [R1–R3] were fetched on 2026-10-13 and the cited conventions
(T_cam_imu = IMU→camera, t_imu = t_cam + shift, continuous-time noise units, τ = 1 s / τ = 3 s reading, 15–24 h, ~10× inflation)
match them. Intel [R6, R7] and Bosch [R8] facts come from search-result summaries of those documents, not full reads.
Parser claims in §1–§2 and §5 were checked against pinned source: `Settings.cc` lines 318–321 (KannalaBrandt right camera
reads `Camera1.k1–k4`), 342 (`Stereo.T_c1_c2`), 493 (inverse before `stereoRectify`), 525 (`Tbc_` re-rotated after
rectification); `Tracking.cc` 613–614 / 1411–1419 (noise ×√f, walk ÷√f).
Not verified by anyone yet: Intel's statement that Y8 IR is ASIC-rectified, BMI085 gyro noise density, Kalibr arm64 Docker.

## Gate naming and deviations from the main-branch baseline

Gate names: this plan uses the project-instruction scheme (N4A/N4B/N4C). The main branch's
[NATIVE_PI5_BASELINE_ARCHITECTURE.md](NATIVE_PI5_BASELINE_ARCHITECTURE.md) §4 numbers the same steps differently:

| This plan | Main-branch §4 | Meaning |
|---|---|---|
| N4A | N4 (official EuRoC) + N5 (Pi ORB build, EuRoC smoke run) | Known-dataset baseline, here run on the Pi |
| N4B | N6 (saved D435i bag → estimator) | Offline run on recorded D435i data |
| N4C | N7 (live VIO) | Live D435i run |

Explicit deviation (ASSUMED decision, needs owner acceptance at PR review): the main-branch baseline is
**monocular-inertial** (`imu-monocular`, NATIVE_PI5 §4 N4/N6) through realsense-ros, and
[RPI5_NATIVE_PERCEPTION_BRINGUP.md](RPI5_NATIVE_PERCEPTION_BRINGUP.md) §11 defers IR2 and higher FPS, to be added later
one variable at a time. This plan changes three variables together: stereo (adds IR2), 30 Hz instead of the N2 15 Hz
profile, and recording through native librealsense (`d435i_record`) instead of realsense-ros/rosbag.
Reason: the 2026-10-13 N4B preparation already targets the upstream `stereo_inertial_realsense_D435i` path, and
stereo gives metric scale from the baseline, so IMU initialization does not have to recover scale alone (INFERRED).
Native recording keeps camera timestamps without the ROS layer while N3 is still OPEN. Consequences: N2's 15 Hz
qualification does not cover the 30 Hz stereo profile, so that profile needs its own attestation (already required
below). And if N4B fails, the three changes cannot be told apart. Mitigation (ASSUMED): if N4B fails, first rerun the
same recordings monocular-inertial with IR1 only (no new recording needed), and only then suspect stereo or calibration.

## Evidence labels and quantity register

SOURCE-SUPPORTED means local source code or reviewer-provided literature facts; the drafting agent had no network, so external citations rest on the reviewer verification above. MEASURED means archived SDK/readback or session observations, not independently established physical calibration. CALCULATED means arithmetic from stated inputs. INFERRED means interpretation. ASSUMED means a proposed operating choice or acceptance threshold. UNKNOWN means evidence is absent. Future results must retain these distinctions. All numeric acceptance thresholds proposed here are ASSUMED, not SOURCE-SUPPORTED; existing gate requirements remain unchanged.

Current values come from [candidate YAML](../experiments/2026-10-13-n4b-d435i-prep/D435i_317422076650_stereo_inertial.yaml) and [calibration notes](../experiments/2026-10-13-n4b-d435i-prep/calibration_notes.md), backed by [new-unit factory readback](../experiments/2026-10-13-pi5-env-snapshot/rs_calibration_new_unit.txt). References [L1–L8] and [R1–R10] below identify provenance. **Evidence location:** the local L-links resolve once the evidence PR (KaiserRichard/wbr-perception-phase1-runtime#4) is merged into `main`; that PR commits the experiment folders, `docs/D435I_VIO_CALIBRATION_READINESS.md`, `docs/PROJECT_STATE.md` and `docs/NEXT_GATE.md`. ORB-SLAM3 source links (L5) point to upstream at the pinned commit 4452a3c, because the repo vendors it as a submodule.

| Quantity | Current value + label | Method and recommendation | Data | Quality check | ORB YAML key + conversion | Mac/Pi |
|---|---|---|---|---|---|---|
| Stereo IR intrinsics | MEASURED: both IRs fx=fy=386.953308105469, cx=321.034301757812, cy=241.040130615234 px; 640×480 Y8; five Brown-Conrady zeros | Keep factory Rectified; Kalibr multicamera validation; independent corner reprojection alternative | S take: fixed measured Aprilgrid, static/slow views, 30 Hz, emitter OFF; protocol below | ASSUMED RMS reprojection ≤0.5 px; epipolar median ≤0.3 px, p95 ≤1 px | `Camera.type: "Rectified"`, `Camera1.fx/fy/cx/cy`, `Camera.width/height/fps`; no Camera2/distortion in this mode | Mac analysis; Pi capture |
| Stereo extrinsics / baseline | MEASURED IR1→IR2 R=I, t=[−0.049912553280592,0,0] m; CALCULATED b=49.9125533 mm | Keep factory; Kalibr validation plus tape-distance/disparity check; Intel health check only without table write | S take at 0.5/1/1.5 m, board frontoparallel then tilted; same profile/storage | ASSUMED depth error ≤2%; validation baseline difference ≤1 mm | `Stereo.b=+0.049912553280592`; fallback `Stereo.T_c1_c2=inverse(T_cn_cnm1)` | Mac analysis; Pi capture/optional read-only check |
| Camera–IMU extrinsic | MEASURED SDK R=I, t_bc=[−0.00552000012248755,+0.00510000018402934,+0.011739999987185] m; INFERRED CAD geometry | Kalibr IMU-camera with fixed factory camchain; factory is comparison, not per-unit alignment | C1–C3, 60–120 s, all 6 DOF, IR/30 gyro/200 accel/100 | ASSUMED CAD disagreement ≤5 mm and ≤2°; repeat spread ≤3 mm/1°; inspect residuals | `IMU.T_b_c1=inverse(T_cam_imu)`; metres, row-major OpenCV matrix | Mac Kalibr; Pi capture |
| Camera–IMU time offset | UNKNOWN physical shift; ASSUMED effective zero in current code; no YAML key | Kalibr default temporal estimation; zero if small/unrepeatable; follow-up common timestamp hook | C1–C3, same global-time setting and domains, exposure logged | ASSUMED max−min shift ≤1 ms across ≥3 takes; assess held-out residuals | No YAML mapping; CLI shift: corrected camera time = raw camera time + shift seconds | Mac estimation/code later; Pi capture/live later |
| IMU noise / walks | ASSUMED Ng=1e−3, Na=1e−2, Ngw=1e−6, Naw=1e−4; SOURCE-SUPPORTED example origin, not unit measurement | Stationary Allan; raw A and inflated B, choose by N4B ablation | A take: IMU-only gyro/200 accel/100, ≥4 h provisional, target 15–24 h | ASSUMED slope agreement ±0.1; segment estimates within 30%; no accepted discontinuities | `IMU.NoiseGyro/NoiseAcc/GyroWalk/AccWalk` continuous-time; `IMU.Frequency=200` combined grid | Mac analysis; Pi stationary capture |
| IMU intrinsics: bias/scale/misalignment | MEASURED SDK 3×3 identity, zero offsets and variance arrays; UNKNOWN true parameters; no YAML intrinsic keys | Recommend online ORB bias plus offline six-pose diagnostics; Kalibr intrinsic model only if warranted; no NVRAM writes | I take: six static orientations, 30 s each after settling; Allan bias; optional all-axis C data | ASSUMED gravity norm error ≤1%, gyro mean norm ≤0.01 rad/s; fit held-out poses | No scale/misalignment/static-bias YAML key; online bias is state, not noise/extrinsic | Mac fit/report; Pi capture |

## 1. Stereo IR intrinsics

MEASURED [L4]: IR1 lines 326–334 and IR2 lines 414–422 give the register values. SOURCE-SUPPORTED [L5]: Rectified reads Camera1 projection and assumes the right projection is identical, with no distortion keys. INFERRED (reviewer, not re-verified): D400 Y8 is ASIC-rectified and Y16 unrectified; equal intrinsics, zero coefficients and stereo R=I are consistent with that. Zero readback does not imply undistorted physical lenses. Y16 is not selected or qualified here.

ASSUMED decision: retain `File.version: "1.0"`, `Camera.type: "Rectified"`, the current Camera1 numbers, width 640, height 480 and fps 30. Do not add unused Camera2 keys or replace calibration from a fit to already rectified images. Factory is the operating choice; Kalibr `kalibr_calibrate_cameras` on the same Y8 pairs is a VALIDATION. An independent fixed-K target reprojection analysis is a justified cheap alternative check, not a new physical-lens calibration.

ASSUMED S protocol: one 120 s take, emitter OFF, measured Aprilgrid stationary; hold the camera still at 0.5, 1.0 and 1.5 m for 10 s each, then slowly sweep target position across both fields and tilt through several angles. Use lighting/exposure/storage below. Detect common tag IDs/corners in both raw decoded images. Report errors by location, range and frame, including failed detections; do not silently discard edge regions.

ASSUMED acceptance: fixed-factory-K reprojection RMS ≤0.5 px with no systematic edge pattern; median absolute row difference ≤0.3 px and p95 ≤1.0 px on static matched corners; ≥100 stereo pairs and coverage of all four image quadrants. Motion skew can mimic epipolar errors: use the static intervals first and preserve pair skew. If validation fails, inspect target scale/flatness, exposure, pairing and profile before changing calibration.

SOURCE-SUPPORTED fallback schema [L5], only after failed validation and separate implementation review:

- `Camera.type: "PinHole"`; both `Camera1.fx/fy/cx/cy` and `Camera2.fx/fy/cx/cy` are required.
- Radtan `[k1,k2,p1,p2]` maps to `Camera1.k1/k2/p1/p2` and `Camera2.k1/k2/p1/p2`. If `k1` exists, all four are read; `k3` is optional for each camera. Supply explicit zeros when appropriate.
- `Stereo.T_c1_c2` is a 4×4 `!!opencv-matrix` (`rows: 4`, `cols: 4`, `dt: f`, row-major `data`), mapping right to left; preserve `Stereo.ThDepth: 40.0` as ASSUMED example tuning. Do not use legacy `Camera.bf` or `Tbc`.
- SOURCE-SUPPORTED: PinHole stereo invokes software rectification in Settings; it also rotates `IMU.T_b_c1` internally for the new rectified frame. Supply the transform for the input left frame, not a manually twice-rotated transform. Validate the example's remap path before use.

SOURCE-SUPPORTED parser caveat: KannalaBrandt8 also needs both Camera1/Camera2 projections and `Stereo.T_c1_c2`. It reads Camera1 `k1/k2/k3/k4`, Camera1 `overlappingBegin/overlappingEnd`, and Camera2 `overlappingBegin/overlappingEnd`. In this pinned parser, readCamera2 unexpectedly reads **Camera1.k1–k4** for right distortion too; merely supplying Camera2.k1–k4 does not set distinct right coefficients. No fisheye switch is recommended for D435i Y8. Resolving that parser behavior would be a separate code ticket, not this plan.

## 2. Stereo extrinsics and baseline

SOURCE-SUPPORTED direction [L3,L5,R1]: RealSense A→B acts as p_B=R_BA p_A+t_BA. Define Kalibr cam0=IR1 and cam1=IR2; its cam1 `T_cn_cnm1` maps cam0→cam1. Thus copy the MEASURED SDK IR1→IR2 transform after converting SDK column-major rotation to a mathematical matrix. It has translation **−b** on X. ORB's `Stereo.T_c1_c2` maps IR2→IR1, so use its inverse: R=I, t=[**+b**,0,0]. Settings explicitly inverts this matrix before OpenCV stereoRectify [L5]. Names alone must not determine direction.

CALCULATED: b=0.049912553280592 m and fx*b=19.31382761 px·m. For rectified disparity d=u_left−u_right, Z=fx*b/d; ideal disparities at 0.5/1/1.5 m are 38.63/19.31/12.88 px. Positive depth requires positive disparity for this ordering. Use `Stereo.b` as a positive magnitude, never negative SDK t_x.

ASSUMED S check: measure distance from left optical center to the board plane along optical Z, accounting for housing-to-optical-center uncertainty; keep board frontoparallel and record tape uncertainty (goal ≤5 mm). Compare median corner triangulated Z with tape distance at all three positions (≤2% discrepancy); infer b_check=Z_tape*d/fx and compare with factory (≤1 mm). Report uncertainty: tape distance and factory fx confound independent baseline estimation. Kalibr stereo residuals and baseline agreement complement this check rather than proving absolute accuracy.

SOURCE-SUPPORTED [R7]: Intel On-Chip calibration produces a health number; On-Chip/Tare results may be validated and optionally burned to flash. ASSUMED recommendation: optical validation first; optional health assessment only if the selected invocation demonstrably does not write a table. Do not invent a health-number threshold without its documented definition. **Any calibration-table, EEPROM or NVRAM write, including OCC, Tare or rs-imu-calibration, requires explicit user approval and is outside the default plan.** Keep original readback and raw warnings unchanged.

## 3. Camera–IMU extrinsic T_b_c1

MEASURED values and INFERRED CAD interpretation are in the register and [L3]. Gyro↔accel returns identity/zero; true individual-axis alignment is UNKNOWN. ORB b means the camera's `imu_camera`, never STM32 `imu_body`. Keep SDK motion axes, units rad/s and m/s²; no ROS optical-to-link, ENU, NED or controller-body rotation is introduced.

SOURCE-SUPPORTED [R1,R2]: Kalibr needs camchain, IMU-noise YAML, target YAML and ROS1 bag. Hand-write camchain using factory intrinsics so `kalibr_calibrate_imu_camera` estimates camera–IMU geometry and time, not replacement camera intrinsics/stereo geometry. Both cameras: `camera_model: pinhole`, `intrinsics: [386.953308105469,386.953308105469,321.034301757812,241.040130615234]`, `distortion_model: radtan`, `distortion_coeffs: [0,0,0,0]`, `resolution: [640,480]`; topics `/cam0/image_raw`, `/cam1/image_raw`, overlaps `[1]` and `[0]`. cam1 `T_cn_cnm1` is the −b transform above. Template content is described here only; no template file is created by this ticket.

ASSUMED C1–C3 protocol: three 120 s default takes (60–120 s allowed), same exact IR1+IR2 Y8 640×480/30, gyro/200 and accel/100, emitter OFF. Fixed grid; move camera, not grid. Start/end 10 s still (5–10 s allowed); perform smooth translation X/Y/Z and rotation about each axis, then mixed motion at varied range/target position. Avoid impacts, saturation, cable tension, planar-only excitation and blur. Kalibr wiki does not specify duration; these durations are ASSUMED. Use the identical interpolation from `d435i_input.h`: a gyro-time IMU message with unchanged gyro and linearly interpolated accel within strictly valid brackets; never extrapolate or nearest-neighbor fill. Log discarded boundaries and preserve raw 100 Hz accel separately.

SOURCE-SUPPORTED [R2]: 20 Hz camera/200 Hz IMU worked well in the wiki. ASSUMED decision: default 30 Hz matches SLAM. A separate 20 Hz acquisition ablation is optional only after profile support is measured; UNKNOWN whether this unit supports IR/20. Do not request an unenumerated mode or treat decimated 30 Hz as physical 20 Hz. Any different profile needs its own attestation and must not replace N2. Kalibr runs on Mac, not Pi.

SOURCE-SUPPORTED conversion: Kalibr `T_cam_imu=T_c_i` gives p_c=T_c_i p_i. ORB `IMU.T_b_c1=T_i_c=inverse(T_c_i)` gives p_i=T_i_c p_c. For [R,t], inverse is [Rᵀ,−Rᵀt]. Write metres, row-major OpenCV 4×4. Factory initial T_cam_imu therefore has R=I and t=[+0.00552000012248755,−0.00510000018402934,−0.011739999987185] m. Test camera origin and three basis vectors, inverse composition and positive determinant, especially for nonidentity rotation.

ASSUMED quality: proper orthonormal rotation (numerical error ≤1e−6, determinant within 1e−6 of +1); no structured visual/inertial residual trend; visual RMS ≤0.5 px; ≥3 estimates with maximum pairwise spread ≤3 mm and ≤1°. Compare estimate with nominal CAD using translation norm ≤5 mm and relative rotation ≤2°. Larger disagreement first triggers inspection of data, frames, target dimensions and timing, not automatic rejection of a physically supported estimate or forced CAD agreement. Freeze a selected calibration on development data and check a held-out take; preserve all report PDFs, result text and camchain-imucam YAMLs.

## 4. Camera–IMU time offset

UNKNOWN current physical offset. SOURCE-SUPPORTED [L5,L7]: ORB YAML has no time-offset key; the patch removes upstream `double offset = 0` and its gyro/accel uses (patch lines 306/417/428). Domain checking already throws on mixed/changing IR/motion domains. Enabled global time alone does not establish exposure alignment, and arrival time is not sensor time.

SOURCE-SUPPORTED [R1,R2]: `timeshift_cam_imu=s` seconds means **t_imu=t_cam+s**. Temporal calibration is enabled by default; do not pass `--no-time-calibration` for C takes. ASSUMED follow-up: add `--cam-imu-shift-ms` with default zero, compute t_cam_corrected=t_cam_raw+s in one common live/offline association location, before IMU coverage selection and TrackStereo. Do not shift the gyro/accel timeline, both image and IMU clocks, or just the final TrackStereo call. Both stereo images share the correction. Preserve raw stamps in audit/export; converted Kalibr bags must not already contain the estimated correction when estimating it again.

ASSUMED quality: at least three same-setting C takes, max−min shifts ≤1 ms and stable sign; compare residuals with and without the estimated shift on held-out data. If |shift|<1 ms and not repeatable, document uncertainty and leave zero. A larger unrepeatable shift requires new timing/data investigation, not averaging it into a deployable value. Repeatable sub-ms shift may be evaluated but no precision claim is justified solely by optimizer output.

ASSUMED operating policy: preserve the present global-time setting, read it before/after on each module, and use the same setting for calibration, N4B and N4C. New-unit setting is UNKNOWN until read; old-unit value 1 is not transferable [L8]. A shift is meaningful only under its measured setting, exposure/profile and timestamp convention; toggling global time requires separate takes/re-estimation. Inspect per-stream dt for bursts, reversals, startup changes and gaps, and retain SDK milliseconds plus seconds conversion. Equal domains are necessary, not proof of timing calibration.

**Rule for calibration and N4 takes:** every IR and motion frame must report `RS2_TIMESTAMP_DOMAIN_GLOBAL_TIME` or `RS2_TIMESTAMP_DOMAIN_HARDWARE_CLOCK`, and the frame-timestamp metadata it depends on must be reported as supported. A take where any stream reports `RS2_TIMESTAMP_DOMAIN_SYSTEM_TIME` is rejected for calibration. That domain is host arrival time, which librealsense falls back to when hardware metadata is unavailable (INFERRED from SDK behavior; confirm on this unit). The existing equal-domain check would accept a take where both streams fell back to SYSTEM_TIME, so it is not enough on its own. Follow-up ticket 1 adds the domain whitelist next to the existing mixed-domain check.

## 5. IMU noise densities and bias random walks

ASSUMED current values: gyro density 1e−3 rad/s/√Hz, accel density 1e−2 m/s²/√Hz, gyro walk 1e−6 rad/s²/√Hz, accel walk 1e−4 m/s³/√Hz. SOURCE-SUPPORTED upstream example origin [L3]; no unit-specific Allan evidence exists. MEASURED SDK zero variance arrays are placeholders, not noiselessness.

SOURCE-SUPPORTED reviewer citation [R8]: BMI085 accelerometer flyer gives 120 µg/√Hz. CALCULATED with g=9.80665 m/s²: 120×10⁻⁶×g=1.176798e−3 m/s²/√Hz; current 1e−2 is 8.4976 times this. INFERRED: consistent with the practice of inflating optimistic static/specification values, but not derived from the flyer or this unit. BMI085 gyro density is **UNKNOWN** until its datasheet is inspected; do not substitute BMI088 or BMI055 values. Factory readback does not provide trustworthy noise parameters; Kalibr requires noise input rather than replacing Allan estimation.

ASSUMED A protocol: use a future IMU-only recorder, gyro/200 and accel/100, full float precision from librealsense frames; camera rigidly fixed on a vibration-free surface, cable strain-relieved, emitter OFF/no image streams, stable room temperature and cooling. Warm up 30 min before logging. Minimum provisional duration 4 h; target 15 h, extend to 24 h if storage/power allow. SOURCE-SUPPORTED [R3] suggests approximately 15–24 h; a shorter run cannot automatically support long-term walk. No target or NIR lighting is required; avoid sunlight/heating changes. Inspect sensor option support and frame metadata for a temperature source; UNKNOWN whether D435i exposes IMU temperature. Log sensor name, units, cadence and whether temperature is IMU, ASIC or unavailable; ASIC temperature is not relabeled as IMU temperature.

SOURCE-SUPPORTED [L6,L8]: historical SDK CSV rounded to 0.001 is unsuitable. Current first-party audit uses setprecision(17) and XYZ32F values, but `d435i_record` is four-stream and bounded to 1–120 s; it cannot perform this IMU-only hours-long experiment. Raw channels must remain separate for Allan analysis (gyro dt≈0.005 s, accel dt≈0.01 s); interpolated 200 Hz accel is correlated and is not a new 200 Hz sensor.

CALCULATED storage assumption: 300 samples/s × an ASSUMED 160 B/sample full-precision CSV row = 48,000 B/s, 0.1728 GB/h, 0.6912 GB/4 h, 2.592 GB/15 h, 4.1472 GB/24 h. Raw XYZ payload alone is 3,600 B/s (0.01296 GB/h). Serialization/index overhead is UNKNOWN; measure a finalized short IMU-only pilot, recompute budget, and reserve ASSUMED 2× projected size. Do not run image recording for Allan: at 18.4 MB/s, 15/24 h would require CALCULATED 993.6/1589.76 GB before overhead.

SOURCE-SUPPORTED analysis [R3,R9]: Mac `allan_variance_ros` (ori-drs) or a Python `allantools` script, installations later only with approval. Preserve per-axis Allan deviation, fitted regions, segment lengths, units and confidence/cluster counts. Read white-noise density from the −1/2-slope fit at τ=1 s and bias random walk from the +1/2-slope fit at τ=3 s, following Kalibr's convention; do not confuse the flat bias-instability minimum with walk. Never infer a walk if the relevant slope/averaging support is absent. Evaluate raw channels at their native rates without silently resampling bursty/gapped data.

ASSUMED quality: no nonfinite, duplicate/backward or unexplained missing samples in analyzed segments; inspect timestamp-dt histograms for batching/bursts rather than using host arrival. Seek slopes −0.5/+0.5 within ±0.1 on at least one decade of supported τ; compare first/second-half fitted values (≤30% difference). If support fails, report UNKNOWN rather than manufacture a walk. The long run tests power stability too; retain before/after and periodic throttling logs.

ASSUMED parameter sets: A = conservative maximum across axes for each raw fitted scalar (preserve per-axis values); B = 10× each A density/walk. SOURCE-SUPPORTED [R3]: static estimates are optimistic and low-cost MEMS may need approximately 10× or more because motion, scale and temperature effects are absent. B is an explicit hypothesis, not a measured result. Also retain the current example values as historical control. Initial Kalibr C solve may use documented provisional noise; rerun with A/B to inspect sensitivity before selecting extrinsics.

SOURCE-SUPPORTED mapping [R1,L5]: `gyroscope_noise_density`→`IMU.NoiseGyro`, `accelerometer_noise_density`→`IMU.NoiseAcc`, `gyroscope_random_walk`→`IMU.GyroWalk`, `accelerometer_random_walk`→`IMU.AccWalk`; Kalibr combined `update_rate: 200.0`→ORB `IMU.Frequency: 200.0`. These are continuous-time values: **do not pre-discretize**. Kalibr model σ_discrete=σ_density/√dt and σ_walk_discrete=σ_walk√dt; Tracking applies noise×√frequency and walk/√frequency, then ImuTypes builds covariances. Interpolation correlation remains a model limitation. Choose A/B by the paired N4B evaluation below, not preference.

## 6. IMU intrinsics: bias, scale and misalignment

MEASURED [L4] lines 469–488: identity sensitivity, zero offset, zero noise/bias variance. UNKNOWN true intrinsics and previous device calibration history. Preserve the reported new-unit warning “IMU Calibration is not available” and new raw stderr; [L3] notes the new enumeration text does not itself contain the warning. The longer old-unit fallback warning in [L8] must not be passed off as a new-unit log.

SOURCE-SUPPORTED [R6]: D435i ships without factory IMU intrinsic calibration; Intel `rs-imu-calibration.py` uses six static orientations, computes intrinsics/offsets and writes NVRAM. ASSUMED decision: do not run its write path by default. Offline diagnostic capture/fitting is a distinct operation; preserve raw samples and observed SDK motion-correction option so later correction cannot be applied twice.

ASSUMED recommendation: (a) use ORB's online gyro/accel bias estimation for baseline operation; (b) report static gyro mean, accelerometer gravity-magnitude and opposite-pose bias/scale diagnostics offline; (c) use Kalibr scale-misalignment models [R4] only as a diagnostic if residuals/pose tests indicate a problem. Online bias can address offsets but cannot establish scale/misalignment. Six gravity poses constrain accel behavior; stationary gyro data constrain zero-rate offset, not gyro scale. Without known angular rate or sufficiently observable dynamic calibration, gyro scale remains UNKNOWN. Do not claim six-pose data alone calibrate every gyro intrinsic.

ASSUMED I protocol: IMU-only at gyro/200 accel/100 with same options, warm-up, vibration-free support and temperature logging as A. Six approximately ±X/±Y/±Z-up orientations, 5–10 s settling then 30 s static each; one documented rotation transition at a time, no shocks. Use a rigid orientation fixture if available; exact leveling uncertainty is UNKNOWN until measured. No Aprilgrid or special lighting needed for static capture; optional dynamic intrinsic-model take reuses C lighting/target/all-axis excitation. Budget CALCULATED ~0.010 GB for 210 s at assumed 48 kB/s; reserve overhead as for A.

ASSUMED checks: held-out static poses gravity-norm error ≤1% relative to g=9.80665 m/s² (ASSUMED reference, not locally measured gravity); warm stationary gyro mean norm ≤0.01 rad/s; flag orientation/temperature-dependent residuals. Failure triggers diagnostic review, not NVRAM write. Repeat selected poses at end to inspect drift. Kalibr diagnostic models require checking the installed version's flags/model availability (UNKNOWN); no unverified flag is prescribed.

SOURCE-SUPPORTED [L5]: no IMU bias/scale/misalignment YAML keys in Settings. Online biases are estimated state. Never encode intrinsic corrections into `IMU.T_b_c1`, noise, frequency or fictitious YAML keys. If diagnostics justify software correction, propose a separate approved common-input implementation with explicit v_corrected=M(v_raw−bias), matrix/axis units, SDK-correction interaction and new validation data. No such correction or fusion is authorized by this document.

## Recording protocol and whole-calibration validation

### Prerequisites and power/storage

SOURCE-SUPPORTED [L1,L2]: PROJECT_STATE remains a historical draft; NEXT_GATE identifies N3 OPEN/VERIFY CURRENT STATE, not completed qualification. Session facts [L1] establish a temporary Pi 5 **4 GB**, 32 GB microSD and 5 V/3 A supply, distinct from target hardware. Old SDK serial 243322073847 receipts do not transfer.

ASSUMED execution sequence, after explicit `CAMERA AVAILABLE`: new 5.1 V/5 A supply and 128 GB card setup → sustained-write qualification of the 128 GB card as data storage (user decision, below) → fresh N1 → N2 → N3 audit/qualification → attested N4 30 Hz profile → calibration takes → N4B ablations → reviewed N4C. SOURCE-SUPPORTED [L2,L3]: N1 must attest SDK 317422076650 separately from ASIC, firmware-update ID and USB descriptor serial (each observed as 327743061057), USB **≥5000M**, permissions, topology, clock, stable power/cooling. N2 remains IR1 Y8 640×480/**15**, gyro/**200**, accel/**100**, 20 s→105 s→mandatory **300 s** soak: IR 14.25–15.75 Hz, gyro 190–210, accel 95–105, image gaps ≤0.20 s, motion gaps ≤0.05 s, positive timestamps/frame steps and no missing image frame numbers. Do not weaken health/fault requirements.

ASSUMED gate dependency: S/C/I/A are native-librealsense calibration recordings, requiring fresh N1 and N2 plus their own requested-profile/storage attestation; they do not inherently require a ROS publisher. However, this session's default sequence resolves the active N3 gate before these takes. Any ROS-derived recording/conversion evidence relies additionally on N3 topic/QoS/timestamp/record-replay qualification. N4B/N4C do not bypass N3; N4C follows reviewed N4B. Offline/synthetic checks qualify utilities only.

MEASURED [L1]: under-voltage at 87/178 samples (49%) during earlier SLAM runs. INFERRED recommendation: **do not start even the low-power IMU-only Allan run before the 5 A supply arrives**; the existing power evidence makes timestamp trust questionable. A new supply is not itself proof of stable power: record `vcgencmd get_throttled` before/after and periodically, preserve latched/live bits and abort/use a fresh take on new power faults; do not conceal them by resetting evidence.

SOURCE-SUPPORTED repository rule: microSD is OS/tools/small logs; large bags require separately qualified storage. **USER DECISION 2026-10-13:** the separate 64 GB USB drive is no longer available, so calibration and VIO takes are recorded on the 128 GB microSD (KIOXIA EXCERIA G3, V30/A2) as an explicit exception to that rule. (2026-10-14: the 64 GB stick was found again, but it is a 480 Mbps USB 2.0 device that measured 0.94 MB/s on 2026-09-12 and 1.09 MB/s on 2026-10-14, far below the 18.4 MB/s stream, so it is not a data volume.) Conditions (ASSUMED): a dedicated data directory (e.g. `/data/wbr-takes/`), never mixed with OS or build paths; a sustained-write qualification of this card on the Pi before the first take, using a file larger than the largest planned take and at least the take duration, with a margin of ≥1.5×18.4=27.6 MB/s (if it fails, full-rate recording is BLOCKED; IMU-only A/I takes are unaffected); free space ≥2× the planned take plus an OS reserve checked before every take; copy each session's takes to the Mac and verify checksums before deleting from the card. INFERRED risk: OS writes and recording compete on one card, so dropped frames during a take must be checked in the audit, not assumed absent.

### Target, light and exposure

ASSUMED target (revised 2026-10-14 to fit printable paper): Kalibr Aprilgrid t36h11, 6 columns × 4 rows, tagSpacing=0.3, tagSize 0.045 m on A3 landscape (preferred) or 0.030 m on A4 landscape (fallback). Print-ready PDFs, Kalibr YAMLs, generator and print/measure/mount instructions: [calibration/aprilgrid/](../calibration/aprilgrid/README.md). CALCULATED at f=386.95 px: a 45 mm tag spans 44/29/22 px at 0.4/0.6/0.8 m (work at 0.4–0.8 m); a 30 mm tag spans 39/23 px at 0.3/0.5 m. The earlier 6×6/80 mm grid (0.58 m wide) does not fit on A3 and is dropped. The YAML tagSize is nominal until replaced by the measured value.

ASSUMED print protocol: laser printer, matte paper, no “fit to page”, rigid flat board (tile large pages if needed without warping). Measure several tag black-edge dimensions and inter-tag gaps with calipers in both axes; use measured values in target YAML `target_type: aprilgrid`, `tagCols: 6`, `tagRows: 6`, `tagSize`, `tagSpacing`. Goal ASSUMED ≤0.5% dimension disagreement and ≤1 mm board bow; report measured uncertainty rather than nominal print size. Generate PDF later on Mac, not in this ticket.

INFERRED risk: some inkjet inks are near-IR transparent; the grid may appear blank to emitter-off IR. Before any take, inspect both IR views for strong decoded tags across intended ranges; failed visibility requires changing print/light, not enabling the projector. Ambient near-IR from daylight/incandescent/halogen is recommended; many LED lights have little NIR, causing darkness or long-exposure blur. Control heat/flicker and avoid glare.

ASSUMED exposure starting point: manual 2,000 µs (2 ms), lowest practical supported gain; adjust illumination/gain first, exposure only if needed. Verify SDK supported units/ranges and readback; actual suitable exposure/gain are UNKNOWN until tested. Require ASSUMED no saturated target regions and motion-blur displacement ≤1 px during C motion. Current recorder does not set exposure/gain or log gain; a bounded metadata/runtime-options ticket below is needed. Do not use unlogged automatic exposure changes. A/I runs require no visual exposure but record “not enabled” explicitly.

### Take inventory, manifests and formats

| Take | ASSUMED default | Profile / motion | CALCULATED storage at session 18.4 MB/s (decimal) |
|---|---|---|---|
| S stereo validation | 120 s | IR1+IR2 Y8 640×480/30, gyro/200 accel/100; static distances + slow coverage | 2.208 GB payload budget; reserve 3.0 GB using 1.5 GB/min |
| C1–C3 camera–IMU | 120 s each, minimum 3 takes | Same; fixed grid, 10 s still ends, 6 DOF | 2.208 GB each, 6.624 GB total; reserve 9.0 GB |
| A Allan | 4 h minimum provisional; 15–24 h preferred | IMU-only gyro/200 accel/100, stationary | 0.691/2.592/4.147 GB under 160 B/sample assumption; ≥2× reserve |
| I static diagnostics | Six 30 s poses + settling | IMU-only, same rates | About 0.010 GB for 210 s; actual row overhead measured later |
| V1–V3 VIO evaluation | 90 s each | Same full 30/200/100 profile; textured room, marked route | 1.656 GB each; reserve 2.25 GB each |

CALCULATED exact IR payload is 18.432 MB/s [L2]; table deliberately uses requested rounded 18.4 MB/s [L1]. Metadata, audit, SDK serialization and exporter copies add overhead (UNKNOWN); 1.5 GB/min is ASSUMED provisional full-profile reservation. Exported uncompressed PNG worst-case is comparable to source pixels; reserve another copy plus bag conversion, do not depend on compression. Preserve failed takes and checksums; use new directories and normal stop/finalization.

ASSUMED every manifest: take ID/duration/operator notes; SDK/ASIC/firmware-update/USB descriptor serials as distinct fields; firmware, librealsense/OS/recorder versions and hashes; requested/resolved profile; emitter readback; exposure/gain and auto/manual state; global-time and motion-correction settings by module; per-stream timestamp domains, raw sensor stamps and host arrivals; temperature source or UNKNOWN; supply/cable, throttled before/after/periodic; target measurements/light/room; storage qualification/free space; raw SDK stdout/stderr, counts, gaps, boundary losses and interruption reason. Readback currently says firmware 5.17.3.10; actual capture version must be re-recorded. Do not label host arrivals as exposure times.

SOURCE-SUPPORTED [L1,L6]: librealsense ≥2.56 recorder writes rosbag2 `.db3`; Kalibr needs ROS1 bag [R2]. Default future conversion: decode `.db3` through SDK playback into original grayscale PNGs and full-precision raw/combined IMU CSV; reuse `d435i_input.h` interpolation; then use `kalibr_bagcreater` on Mac. Exporter may run locally on Pi if Mac SDK support is unavailable, but acquisition stays Pi-local. Keep original timestamp scale/epoch, monotonic order, frame IDs, topic mapping and original audit separate; no arrival-time reconstruction. Export `/imu0` gyro+accel at gyro stamps and both camera topics at original image stamps. Validate converted bag headers against raw SDK audit to ≤1 µs (ASSUMED tolerance), counts, units and image checksums; any rounding/epoch change must be explicit.

INFERRED alternative: `rosbags-convert` may bridge ROS2→ROS1 if it understands this SDK bag's schema; compatibility is UNKNOWN and it does not automatically create the required combined IMU message. Default PNG/CSV route avoids assuming SDK `.db3` contains ordinary ROS2 sensor topics. Tool installation needs later approval; no converter is installed/run now. Confirm bagcreater's installed directory/CSV conventions using its help and create a tiny synthetic round-trip before real conversion.

SOURCE-SUPPORTED reviewer fact: Kalibr provides ROS1 Noetic Dockerfiles. ASSUMED runtime: Docker on Mac; Apple Silicon arm64 build feasibility is INFERRED, successful build/runtime UNKNOWN until tried. Do not install Kalibr on Pi. Fallback if the arm64 image fails to build or run: the x86 Lab workstation (main-branch NATIVE_PI5 §1 'Lab', native x86 reference platform), using Kalibr's stock amd64 Noetic Docker image. The take data and the calibration inputs stay identical, and the report records which machine produced it. Pin image/source/tool versions and record architecture/digest. Future Mac invocation after approved setup/conversion (paths illustrative, installed help must confirm):

```bash
kalibr_calibrate_imu_camera --bag C1.bag --cam factory-camchain.yaml --imu imu-A.yaml --target measured-aprilgrid.yaml
# Repeat independently for C2/C3; no --no-time-calibration.
kalibr_calibrate_cameras --bag S.bag --topics /cam0/image_raw /cam1/image_raw --models pinhole-radtan pinhole-radtan --target measured-aprilgrid.yaml
```

ASSUMED preserve `report-imucam-*.pdf`, `results-imucam-*.txt`, `camchain-imucam-*.yaml`, command/log/environment receipts and all fit failures. Exact exporter/bagcreater command is UNKNOWN until the bounded implementation ticket establishes its interface; the operator must not improvise it in a physical session.

### N4B paired ablation, then N4C

ASSUMED V motion [L2]: use three textured-room 90 s takes. First 20–30 s translate 10–30 cm in all axes with ±15–30° rotations; then traverse a tape-marked straight segment (≥2 m, ASSUMED) and a marked room loop, return camera to the same marked position/orientation, end 5–10 s still. Record a measured route length (ASSUMED ≥5 m) and closure-reference placement uncertainty. Do not use Aprilgrid-only C takes as the sole VIO performance data.

ASSUMED experiment: on identical immutable V takes, run a 2×2 matrix: factory T_b_c1/current zero shift versus selected Kalibr T_b_c1/validated shift, crossed with noise A versus B. Stereo remains factory in all default cells; keep current example-noise baseline too. If stereo validation failed, evaluate any approved replacement as a separately named factor, not a hidden simultaneous change. Hold feature tuning, bag, build, mapping settings and runtime options fixed; three replays per cell per take characterize scheduling variability. For isolating spatial/time causes, add fixed-noise transform-only and shift-only contrasts when full Kalibr differs materially. Select on development takes, verify on held-out V take.

ASSUMED review thresholds: IMU initializes within 30 s of deliberate excitation on every take; one map, zero resets; tracking loss ≤1% frames, no single loss >1 s; return-to-start translation error ≤2% of measured route length; tape straight-segment estimated length error ≤2%; closure-percentage spread across takes ≤1 percentage point. Record initialization time, map/reset history, loss intervals and per-run metrics, including unavailable trajectories. These are proxies without ground truth, not ATE or proof of calibrated accuracy. Loop closing can conceal drift: report both pre-loop and final closure when accessible, otherwise mark pre-loop UNKNOWN. Scale cannot be tuned using evaluation truth silently.

ASSUMED selection rule: require all review thresholds on held-out data; prefer lower median scale/closure error without worse initialization/loss/resets, and report uncertainty/ties. If neither noise set is supported, leave calibration OPEN; if indistinguishable, retain A provisionally and report no evidence for B. Optional fixed-extrinsic held-out Kalibr residual check requires verifying version support or implementing evaluation-only residuals, not pretending a free re-fit is held-out validation. N4C later measures live drops, timing, CPU/thermal/power and latency with the same settings; offline replay does not prove live throughput.

## Mac now versus Pi later

| Work | Mac now, no camera | Pi + D435i + 5.1 V/5 A supply + 128 GB card (OS and data, per user decision) later |
|---|---|---|
| This ticket | Write this plan only; status OPEN | No action authorized by this ticket |
| Templates/target | Future ticket describes/generates factory camchain, measured target YAML/PDF, provisional/A/B IMU YAML; no files created here | Measure print, confirm IR visibility and optical/exposure behavior |
| Timestamp hook / exporters | Future code and synthetic tests; reviewed interfaces and reproduction commands before session | Checksummed isolated bundle build; physical bag round-trip after gates |
| Kalibr | Future approved Docker build trial; arm64 UNKNOWN; no install/network now | No Kalibr installation; Pi-local acquisition only |
| Analysis | Future offline Allan, epipolar, tape scale/closure tools with labelled synthetic fixtures | Record S/C/A/I/V only after power/storage/N1/N2 prerequisites; default resolve N3 first |
| N4B/N4C | Analyze immutable evidence and reports, preserve historical originals | N4B reviewed ablations; only then N4C physical validation |

ASSUMED transport/build policy: later deploy checksummed copies of Mac utilities into a fresh Pi runtime bundle, preserving both checkouts and native build evidence. No SSH, network, installs, Git operations, camera commands, firmware writes or ORB execution occur in this docs-only ticket.

## Follow-up tickets for Codex (bounded; no code in this ticket)

1. **Time-offset hook and domain whitelist:** isolated example/common input helper only; reject SYSTEM_TIME frames (GLOBAL_TIME/HARDWARE_CLOCK only) for calibration/N4 takes; `--cam-imu-shift-ms` finite numeric option, default zero; shared live/offline application before coverage/association; raw audits unchanged. Synthetic tests: positive/negative shifts with known events, seconds/ms sign, both cameras, zero equivalence, prefix/EOF coverage, no double application, domain rejection. Document future build/manual replay commands and setting provenance; no core ORB API or invented YAML key. Review CLI change before implementation as required by repository rules.
2. **Calibration exporter/converter:** SDK file-only decode to lossless PNG, full-precision raw XYZ CSV and gyro-grid combined CSV using existing interpolation; immutable manifest/count/hash/domain checks. Validate synthetic interpolation, boundary/gap rejection, nanosecond ROS1 headers and PNG pixels, then real `.db3` round-trip later. Pin verified bagcreater conventions and exact commands; approved installations only. Dataset/schema changes require separate review.
3. **IMU-only recorder and capture metadata:** separate modular utility for hours-long 200/100 Hz recording, bounded queues/disk monitoring, signal-safe normal finalization, full precision, temperature-support query and health logging; no camera image streams or NVRAM writes. Small shared metadata improvement records gain/exposure/global time/motion correction; explicit temporary manual exposure option only after interface review. Synthetic tests cover precision, rate/duration validation, faults, disk exhaustion and stop; later short physical pilot measures overhead before Allan.
4. **Mac preparation:** content-only templates from values above, measured-dimension Aprilgrid PDF/YAML, approved pinned Kalibr Docker trial and architecture log; verify parser-compatible matrices and direction basis tests. No target dimensions substituted from nominal print when measurements differ. Record unsupported options instead of inventing flags.
5. **Mac analysis utilities:** modular epipolar/reprojection/tape-depth and Allan scripts, route-scale/closure and ablation summarizer; numeric labels and raw-evidence links retained. Synthetic fixtures with known corner offsets, disparities, transforms, constant/white/random-walk IMU and trajectory errors verify behavior only. Provide exact build/test/manual commands and example outputs before the operator session; no accuracy claim from fixtures.

## Open questions / UNKNOWNs

- UNKNOWN actual global-time setting/domains/exposure/gain and motion-correction behavior for the new unit; do not import old-unit settings.
- UNKNOWN IMU temperature access, BMI085 gyro datasheet density, intrinsic history and per-axis scale/misalignment.
- UNKNOWN raw timestamp exposure convention, offset repeatability, physical gyro/accel alignment and interpolation-induced correlation effects.
- UNKNOWN Kalibr arm64 Docker viability (fallback: x86 Lab workstation), installed version's fixed-extrinsic/intrinsic-model interfaces, SDK Mac decoding and bagcreater conversion compatibility.
- UNKNOWN new supply/card arrival, stable power, 128 GB card sustained-write qualification, exact recording overhead and unresolved N3 condition. Hardware availability is not gate evidence.
- UNKNOWN measured target size/flatness/NIR contrast, precise optical-center tape reference and local gravity. Current intrinsics/baseline have readback provenance, not independent metrology.
- SOURCE-SUPPORTED [L8] old-unit method notes apply; old-unit serial, numeric calibration, power/timing receipts and fallback logs do not transfer. No reviewer-design challenge is needed beyond the SOURCE-SUPPORTED parser caveat and storage-policy reconciliation already recorded above.

## References and provenance

Local sources (SOURCE-SUPPORTED code/procedure; MEASURED archived observations as stated):

- **L1:** [PROJECT_STATE](PROJECT_STATE.md), [NEXT_GATE](NEXT_GATE.md), [2026-10-13 session facts](../experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md). Historical draft state, active N3, new-unit/power/storage facts and 18.4 MB/s budget.
- **L2:** [n4b_plan.md](../experiments/2026-10-13-n4b-d435i-prep/n4b_plan.md) and [Phase A runbook](../experiments/2026-09-12-pi5-native-sensor-validation/PHASE_A_RUNBOOK.md). Gate order, exact N2 profile/thresholds, N4 recording/build/motion protocol.
- **L3:** [candidate YAML](../experiments/2026-10-13-n4b-d435i-prep/D435i_317422076650_stereo_inertial.yaml), [calibration_notes.md](../experiments/2026-10-13-n4b-d435i-prep/calibration_notes.md). Current values, upstream provenance, SDK/ORB directions and warnings.
- **L4:** [rs_calibration_new_unit.txt](../experiments/2026-10-13-pi5-env-snapshot/rs_calibration_new_unit.txt), 2026-10-13. Motion capabilities ~98–102, IR blocks 326–334/414–422, motion defaults 469–488, extrinsic sections.
- **L5:** pinned ORB-SLAM3 [Settings.cc](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/src/Settings.cc), [Tracking.cc](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/src/Tracking.cc), [ImuTypes.cc](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/src/ImuTypes.cc). Parser, stereo inverse/remap, Tbc and noise-frequency scaling; source identity documented in L3 as 4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4, not independently Git-inspected here.
- **L6:** [d435i_input.h](../experiments/2026-10-13-n4b-d435i-prep/d435i_input.h), [d435i_record.cpp](../experiments/2026-10-13-n4b-d435i-prep/d435i_record.cpp), [d435i_rs.h](../experiments/2026-10-13-n4b-d435i-prep/d435i_rs.h). Interpolation, 120 s limit, fixed profiles and audit precision/options.
- **L7:** [stereo_inertial_d435i_file.patch](../experiments/2026-10-13-n4b-d435i-prep/stereo_inertial_d435i_file.patch). Domain guards and removed offset.
- **L8:** [D435I_VIO_CALIBRATION_READINESS.md](D435I_VIO_CALIBRATION_READINESS.md). Old-unit methods and warnings only; not new-unit qualification.

External references below are **SOURCE-SUPPORTED by reviewer-provided facts/citation**, not freshly accessed or installed; UNKNOWN bibliographic details are not invented:

- **R1:** ETH Zurich ASL, Kalibr wiki, “YAML formats”: transforms, time shift and continuous-time IMU keys. https://github.com/ethz-asl/kalibr/wiki/yaml-formats
- **R2:** ETH Zurich ASL, Kalibr wiki, “Camera IMU calibration”: fixed target/all-axis motion, ROS1 inputs, 20/200 Hz example, time estimation and outputs. https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration ; Kalibr repository/Dockerfiles: https://github.com/ethz-asl/kalibr
- **R3:** ETH Zurich ASL, Kalibr wiki, “IMU Noise Model”: units, discretization, Allan fitting, 15–24 h and static-noise inflation caveat. https://github.com/ethz-asl/kalibr/wiki/IMU-Noise-Model ; recommended ori-drs tool: https://github.com/ori-drs/allan_variance_ros
- **R4:** Paul Furgale, Joern Rehder, Roland Siegwart, “Unified Temporal and Spatial Calibration for Multi-Sensor Systems,” IEEE/RSJ IROS, 2013. Paul Furgale, Timothy D. Barfoot, Gabe Sibley, “Continuous-Time Batch Estimation Using Temporal Basis Functions,” IEEE ICRA, 2012. Joern Rehder et al., “Extending kalibr: Calibrating the extrinsics of multiple IMUs and of individual axes,” IEEE ICRA, 2016. SOURCE-SUPPORTED-by-citation: calibration/intrinsic model basis; linked via https://github.com/ethz-asl/kalibr/wiki
- **R5:** Carlos Campos et al., “ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual–Inertial, and Multimap SLAM,” IEEE Transactions on Robotics, 2021. SOURCE-SUPPORTED-by-citation; implementation link: https://github.com/UZ-SLAMLab/ORB_SLAM3
- **R6:** Mirota and Scaife, “Intel RealSense Depth Camera D435i IMU Calibration,” Intel white paper, Rev 001, January 2019. Six orientations and NVRAM write; support entry: https://www.intel.com/content/www/us/en/support/articles/000032303.html
- **R7:** Intel, “Intel RealSense Self-Calibration for D400 Series Depth Cameras,” white paper (revision/date UNKNOWN here). On-Chip health check/Tare and optional flash write: https://dev.intelrealsense.com/docs/self-calibration-for-depth-cameras
- **R8:** Bosch Sensortec, “BMI085” flyer (revision/date/direct datasheet URL UNKNOWN here). Reviewer-verified accelerometer 120 µg/√Hz; gyro density UNKNOWN. No BMI088/BMI055 substitution.
- **R9:** IEEE Std 952-1997, “IEEE Standard Specification Format Guide and Test Procedure for Single-Axis Interferometric Fiber Optic Gyros,” 1997. Naser El-Sheimy, Haiying Hou, Xiaoji Niu, “Analysis and Modeling of Inertial Sensors Using Allan Variance,” IEEE Transactions on Instrumentation and Measurement, 2008. SOURCE-SUPPORTED-by-citation for Allan methodology; exact URLs not supplied/retrieved.
- **R10:** Existing L8 SDK fallback reference, librealsense v2.58.4 parser: https://github.com/realsenseai/librealsense/blob/v2.58.4/src/ds/ds-calib-parsers.cpp . Existing citation only; not verification of the installed binary or new-unit fallback reason.

Validation of this document: Mac-only inspection of listed local evidence and code, transform/storage arithmetic and document consistency review. No physical data, install, network, SSH, Git command or runtime calibration was performed. Status remains **OPEN**.
