# From the D435i prototype to a supervised WBR deployment

Planning snapshot: **14 October 2026**. This is a review proposal, not an approved interface, booking, hardware PASS or permission to run the camera. WBR means wheel-biped robot; SLAM means simultaneous localization and mapping; VIO means visual-inertial odometry.

**First deployment objective:** repeatable D435i localization on the Raspberry Pi, reported as optional health-checked information during supervised slow robot motion. It does not authorize navigation or motor control. Pi failure must not remove STM32H7 balance, body estimation, LQR, VMC, FSM, motor or jump safety authority. D435i camera IMU and STM32 body IMU remain separate; no naive fusion.

Use the existing N0–N7 gates. The stages below group their work; they do not add gates or change acceptance criteria. All camera-dependent commands, camera processes, ORB-SLAM3 execution, calibration changes and capture wait for the owner's explicit **CAMERA AVAILABLE**.

## Owner-facing route and conditional six-week plan — revision 1

The deck uses plain phase names first. Gate codes below refer to the existing acceptance checks, not new gates. “Done when” on each phase slide points to observable recordings, plots, logs or repeatable procedures. Estimate age means elapsed time from image capture to available position output; it is unknown without a validated clock relationship. Unused evaluation data means recordings not used to fit calibration. Synthetic cases test software behavior only. Optional position information never owns balance or motor safety.

| Plain phase | Existing checks | Conditional week | Hardware |
|---|---|---|---|
| Stable power and storage | Preparation / N0 | 1 | Pi, supply, cooler, qualified storage, console |
| Trustworthy camera data | N0 → N1 → N2 → N3 | 1 | D435i, direct USB 3 cable, same Pi and data path |
| Calibrate the camera | Acquisition for N4A / N4B | 2 | Measured A0 target, rigid backing/stand, light, calipers, workstation |
| SLAM on our own recordings | N4A / N4B | 2–3 | Stable-power target Pi, immutable takes, Kalibr workstation |
| SLAM live on the Pi | N4C / N5 | 3 | Final cooling/data path, marked textured room |
| Health signal to the STM32 | N6 | Design 3–4; acceptance after N5 | Confirmed MCU board, reviewed link, debugger, controller engineer |
| On the robot | N7 supported, then separately authorized motion | 4–5 | WBR, reviewed mount/rail, rated stand, independent stop, then tether/operator/spotter |
| Repeat and repair | Repeat applicable existing checks | 6 | Same hardware and backup space |

Weeks start **14 October 2026**; these are conditional targets, not reservations or promised dates. Keep the same unit/configuration and carry unmet checks into the next week. Do not shorten the mandatory 300-second N2 soak or stationary recording to fit this calendar. Base effort remains about **11–28 engineer-days**, plus **2–5 days** if conversion/tools fail and unknown parts/lab queues. Overlap requires separate staff; it does not reduce total effort.

### Hardware and lab bookings: bench and calibration

| Item | Phase | Status | Book when | Prepare first |
|---|---|---|---|---|
| 8 GB Pi + D435i | Input → live | Have per notes; confirm loan | W1; retain through W6 | Same unit, console, USB 3 cable |
| 5.1 V/5 A supply + cooler | All Pi work | Supply ordered; cooler confirm with lab | Before first camera slot | Confirm arrival and power checks |
| Large-data storage | Input → live | Borrow / buy; unqualified | Before W1 input slot | Sustained-write and replay checks |
| 128 GB microSD | Calibration only | Ordered; arrival unknown | Before target slot | Confirm exception; qualify short takes |
| A0 grid, stand, light, calipers | Calibration | Print/buy; tools confirm with lab | W2: 3–4 h | Measure grid, prove import route |
| Quiet bench + workstation | Calibration | Lab; confirm access | W2: 30 min + 15–24 h | Test IMU recorder, backup and stop |

### Hardware and lab bookings: live Pi and robot

| Item | Phase | Status | Book when | Prepare first |
|---|---|---|---|---|
| Marked textured room | Live Pi | Lab; confirm route | W3: 2–3 h | Replay accepted; age/resource limits |
| STM32H7 + link + debugger | Health signal | Lab; board/owner unknown | W3–4; after review | Confirm board, voltage, pins and link |
| WBR + mount + battery rail | Supported robot | Lab; stock/design unknown | W4: 3–4 h | Review mount/power; receiver tests |
| Rated stand + independent stop | Supported robot | Lab; confirm suitability | With controller owner in W4 | Approve fault procedure |
| Tether + clear route + spotter | Slow robot motion | Lab; confirm suitability | W5: 2–3 h | Supported tests; separate motion approval |
| Repeat/repair access + backups | Handoff | Lab; confirm access | W6: 2–4 h reserve | Preserve failures; list unresolved work |

### Software stack by phase

| Phase | Software / purpose | What must be ready |
|---|---|---|
| Preparation / input | Ubuntu + ROS 2 Jazzy; RealSense SDK/driver; existing raw checks; rosbag2 recorder/replay. | Review wrapper install; verify actual profiles and complete replay. |
| Calibration | Lossless PNG + full-precision IMU export → ROS 1 bag; Kalibr; Allan sensor-noise analysis. | Conversion/workstation and long recorder are future reviewed tools. |
| Saved-data / live SLAM | Native ORB-SLAM3 stereo-inertial; existing adapter; trajectory and health/resource plots. | Finish existing fix; preserve versions, settings and raw evidence. |
| STM32 health | Small reviewed Pi health adapter + bounded STM32 receiver; synthetic rejection tests. | Message, link and limits need controller approval before implementation. |
| Robot / handoff | Same frozen stack; startup/stop/rollback runbook; checksummed runtime bundle. | No balance authority on Pi; reuse a validated controller link. |

### Next six weeks: preparation through live Pi

| Week | Owner / lab | Engineering work | Visible result |
|---|---|---|---|
| 1: 14–20 Oct | Confirm parts, camera loan, storage, console and workstation; request 3–4 h bench. | Prove conversion offline; target/recorder preparation; fresh input checks after authorization. | Reviewed input/replay receipts or a precise blocker. |
| 2: 21–27 Oct | Book target 3–4 h and separate overnight; same camera/Pi. | Three target takes, unused room takes, stationary data; first-take review and backups. | Usable captures, two matching copies; calibration reports or recapture decision. |
| 3: 28 Oct–3 Nov | Workstation; reserve marked route 2–3 h; agree controller limits. | Stable-power reference; repeated own-data replay; live and sustained-load measurements. | Tracking/reset and estimate-age plots; no growing queue; accept or diagnose. |

### Next six weeks: controller, robot and contingency

| Week | Owner / lab | Engineering work | Visible result |
|---|---|---|---|
| 4: 4–10 Nov | Controller owner; confirmed WBR, board, link, stand and stop; 3–4 h. | Accept receiver after live/resource review; motors-disabled then approved supported faults; mount/power checks. | Rejection/fallback traces and unchanged local control within approved limits. |
| 5: 11–17 Nov | Separate motion approval; tether, route, operator/spotter; 2–3 h. | Supervised slow motion, Pi-loss trial, repeat startup/stop and review vibration/age. | Target: mounted tracking plus verified health/fallback behavior; no navigation claim. |
| 6: 18–24 Nov | Hold 2–4 h repair/repeat slot; extend camera loan if needed. | Resolve the failing layer; freeze utility/settings bundle; second-operator repeat. | Reproduction report, verified backups and explicit remaining blockers. |

### Algorithm comparison: keep one default, test one challenger

| Candidate | Demo | CPU | Motion | /100 | Decision |
|---|---|---|---|---|---|
| ORB-SLAM3 stereo/IMU | 5 | 3 | 3 | 68 | Default; existing tools |
| RTAB-Map own motion estimate | 3 | 2 | 3 | 68 | For an obstacle map |
| OpenVINS | 3 | 4 | 3 | 61 | First matched-data challenger |
| Wheels/body + depth | 2 | 5 | 2 | 56 | Requires working robot exports |
| ORB RGB-D | 3 | 3 | 2 | 52 | New input path needed |
| Basalt | 2 | 3 | 3 | 53 | Prove build/adapter benefit |
| VINS-Fusion | 2 | 3 | 3 | 47 | Prove port benefit |
| Kimera-VIO | 2 | 2 | 3 | 48 | More dependencies; defer |

Hardware statuses reflect the dated project notes; current availability must be confirmed with the lab. No purchase or booking was made. The 128 GB card exception is calibration/VIO-only; routine large bags still need separately qualified storage. Conversion, long-duration recorder and controller message/receiver are review proposals, not completed tools.

Scores reproduce the independent [R1b decision table](research/R1b_algorithms_independent.md), with technical risks checked against [R1](research/R1_algorithms.md). Scale: 1 poor fit/high burden, 3 plausible/unverified, 5 strong fit/low burden. The displayed total also includes software/Jazzy support, navigation and licensing: `(30D + 20C + 20R + 15J + 10N + 5L) / 5`. Full component values are in R1b and slide notes. These are inferred planning aids, not measured Pi speed or acceptance thresholds. ORB and RTAB tie at 68; the immediate localization objective breaks that tie in favor of existing ORB tools. Other R1b options are RTAB with external odometry (54, later composition) and learned DROID/DPVO (36, CPU-only deployment mismatch); neither is a second immediate estimator path.

Switch after trusted input/calibration and 2–3 days bounded diagnosis only if ORB repeatedly misses approved age/continuity limits and a verified OpenVINS build meets the same limits on identical data. A mapping-first objective favors a measured RTAB comparison; a proven wheel/body export can change the first robot-demo scope. Lower-scored Basalt/VINS/Kimera need a reproducible ARM build and meaningful matched-data advantage before reopening. Core capabilities trace to [ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3), [OpenVINS](https://github.com/rpng/open_vins) and [RTAB-Map](https://github.com/introlab/rtabmap_ros). Upstream pages were checked during revision; hardware performance was not tested.

The detailed route below retains exact raw profiles, timing thresholds, calibration warning/identity provenance and implementation-review boundaries. This revision changes presentation, not the architecture or acceptance criteria.

## What the evidence says now

| Current observation | What it establishes and what remains open |
|---|---|
| The 8 GB Pi booted the existing 32 GB card; under-voltage persisted. A 5.1 V/5 A supply was ordered, but arrival and qualification are unknown. | Boot is established. Stable power, cooling and under-load behavior are not. |
| Three Pi EuRoC MH01 runs measured ATE RMSE 0.0368–0.0416 m. | Known-input accuracy evidence only. N4A remains OPEN: speed was measured under under-voltage, and the report used a 4 GB stand-in. Repeat the reference on the target Pi with qualified power. |
| A 15-second memory-backed stereo take reported no image drops; a 100-second microSD take had major gaps. The storage-blocking cause is a strong inference. A 64 GB USB 2 stick measured 1.09 MB/s. | Short recording works. Sustained recording and a general-purpose bag medium are not qualified. Do not use the stick for capture. |
| The active D435i SDK serial is 317422076650. ASIC serial and separately observed USB descriptor serial are 327743061057. | Confirm all four identity fields afresh at N1. Keep SDK serial, ASIC serial, firmware-update ID and USB descriptor serial separate; firmware-update ID is still unverified. September receipts/calibration do not transfer. |
| SDK evidence preserves: “IMU Calibration is not available, default intrinsic and extrinsic will be used.” IMU noise was assumed and the physical camera–IMU offset is unknown. | Factory stereo geometry is a starting point to validate, not proof of per-unit camera–IMU alignment or calibrated VIO. Preserve the warning and raw logs. |
| The installed SDK is recorded as 2.58.4. N3 preparation found no installed RealSense ROS camera wrapper; candidate ROS package 4.58.4 and its dependencies were inspected but not installed. | N3 package install/readback and physical ROS delivery remain OPEN. “Prepared” or synthetic API compatibility is not installed-wrapper validation. |

Sources: [13 October session facts](../experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md), [14 October addendum](../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md), [N4A report](../experiments/2026-10-13-n4a-euroc-mh01/REPORT.md), [N3 preparation](../experiments/2026-09-12-pi5-native-sensor-validation/N3_PREPARATION.md), [current lab runbook](../experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md).

## Clear these blockers before booking capture

| Blocker | Status | Owner action |
|---|---|---|
| Pi power, cooling and access | Under-voltage persists on 5 V/3 A. 5.1 V/5 A supply delivery is unknown. The 8 GB Pi's Wi-Fi is unverified and Ethernet is loose. | Confirm the suitable supply and cooler. Ensure a local console or verified control-network fallback. Acquisition remains local to the Pi; SSH is control only. Test power under representative load before gate progression. Raspberry Pi recommends its 27 W USB-C supply for Pi 5; its 5.1 V/5 A profile increases downstream USB current capacity. [Hardware guidance](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html), [supply specification](https://www.raspberrypi.com/products/27w-power-supply/). |
| N1–N3 runtime | Candidate RealSense ROS 4.58.4 and message packages are not installed. The wrapper transaction was inspected offline and must be reviewed again before installation. | Review and authorize that transaction separately; verify the installed SDK/wrapper versions, active SDK serial, parameter readback and topic/QoS behavior. Do not use the older SDK serial in the stale N3 preparation note. The wrapper cited for stereo integration documents monocular and monocular-inertial modes only, so it is not the stereo-inertial default. [Wrapper README](https://github.com/gjcliff/ORB_SLAM3_ROS2). |
| Storage for ROS bags | The USB stick is too slow. The 128 GB microSD has a **calibration-only** exception and has no qualification result. | Identify and qualify separate external storage for N3 and routine large bags, or resolve the receipt path with the owner. Keep the microSD exception limited to calibration/VIO data. MicroSD remains for OS, tools and small logs. |
| Kalibr-compatible input | The D435i .db3 recording is ROS 2 rosbag2 format. Kalibr's primary toolchain expects ROS 1 bags; the planned export/converter is not implemented or tested. | Prove one route before collecting calibration data: export lossless PNG images and full-precision timestamped IMU CSV, then create the ROS 1 bag with Kalibr's bagcreater. Test a labeled synthetic fixture and known sample for pixels, counts, units, clock domains, order and common coverage. This route is a proposal, not an existing tool. Confirm the required workstation/environment first. [Kalibr bag format](https://github.com/ethz-asl/kalibr/wiki/bag-format), [Kalibr ROS 2 conversion notes](https://github.com/ethz-asl/kalibr/wiki/ROS2-Calibration-Using-Kalibr), [RealSense .db3 format](https://github.com/realsenseai/librealsense/blob/master/doc/record-and-playback.md). |
| Calibration target and overnight data | No measured AprilGrid print or tested stationary IMU-only recorder is established. | Print and measure the target; confirm rigid backing, stand, lighting, metrology, backup space and overnight permission. Review recorder/export format and normal-stop/failure recovery before requesting B2A. |
| Controller integration | Named controller engineer, exact STM32H7 board/pinout, available link, power rail and robot slot are unknown. | Identify the owner, board and existing communications link before N6 or robot bookings. Message/API, link and firmware work stay proposals pending review. |

Kalibr recommends a fixed, known, well-lit target, low motion blur and rotation/translation that excites all IMU axes. Its noise guidance recommends about 15–24 hours of stationary data for Allan-based parameter estimates; that duration is guidance, not a sensor gate. [Camera–IMU procedure](https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration), [IMU noise model](https://github.com/ethz-asl/kalibr/wiki/IMU-Noise-Model).

## One gate-aligned route

### Camera-free preparation — do this first

**Purpose:** make the next authorized lab session useful.

- Reconcile current receipts and active-unit identifiers against 14 October facts. Confirm supply delivery, camera loan window, storage, console/network access, controller owner/board, calibration workstation and overnight access.
- Complete the synthetic PNG/CSV-to-Kalibr ROS 1 bag pilot and inspect a known sample. Preserve original timestamps/domains and full-precision IMU values. Verify pixels, topic counts, units, monotonic order and common camera/IMU coverage. Do not claim synthetic results qualify a camera or recorder.
- Prepare the measured A0 AprilGrid and a checksummed Mac-origin utility bundle. Any first-party exporter/recorder or format change needs review before implementation.
- Obtain review of the candidate N3 package transaction and storage receipt route. Do not install packages or modify the Pi as an assumed preparation step.
- Draft N6 health/frame/time semantics for controller review. Implement no public message/API or firmware change without approval.

**Exit:** blockers have an owner and evidence-based next action; reader/export route works on offline fixtures; target and N3 package/storage decisions are ready for review. No camera, ORB-SLAM3, sensor or calibration execution occurs in this stage.

**Effort:** about 2–5 engineer-days, low confidence until the conversion and workstation are checked. Parts and lab queues add elapsed time.

### Trustworthy camera data — N0 → N1 → N2 → N3

**Order:** record a fresh N0 platform baseline, pass N1, complete exact N2, review and accept N2, then run N3 record and isolated replay. Diagnose the first unmet condition and stop. Do not jump to ORB-SLAM3.

- **Tools:** existing guarded N1/N2/N3 tools from the [Phase A runbook](../experiments/2026-09-12-pi5-native-sensor-validation/PHASE_A_RUNBOOK.md); reviewed Jazzy package/runtime; exact readback and topic/QoS observer.
- **Hardware:** target 8 GB Pi, qualified 5.1 V/5 A supply and cooling, active D435i, direct USB 3 cable/port, local console or verified network, and storage qualified for the N3 bag. Confirm every item before the session.
- **N1:** camera branch must report USB **≥5000M**, correct active unit, normal-user access, clean kernel/power state and current receipts. A connector shape or old speed observation is not a pass.
- **N2:** preserve exactly **IR1 Y8 640×480/15, gyro/200, accel/100**, with **20 → 105 → mandatory 300 seconds**. Never substitute the stereo profile. Keep all original content, startup/boundary, kernel, power, normal-stop and review requirements. The full rate bands are IR 14.25–15.75 Hz, gyro 190–210 Hz, accel 95–105 Hz; image gaps ≤0.20 s and motion gaps ≤0.05 s; stamps/frame numbers increase and no image frames are missing.
- **N3:** use the reviewed wrapper and explicit required raw, calibration, IMUInfo, extrinsics and TF topics. Check the finalized bag and complete decoded fields/counts/stamps against a full isolated replay after the live camera stops. No live/replay collision. Only a reviewed receipt can accept the result.
- **Owner:** authorize camera-dependent work with the exact phrase CAMERA AVAILABLE; ensure access/supply and arrange a 3–4 h diagnostic/gate slot. That slot may diagnose without completing N3.
- **Exit:** reviewed current-unit receipts for N0–N3. Latched-power diagnostic mode remains OPEN_DIAGNOSTIC and cannot enter N3 or promote PASS.

**Effort:** about 0.5–3 engineer-days plus the 3–4 h booking. Under-voltage, USB2, missing wrapper, permissions or storage failure stops progression; do not reinstall/reset by default.

### Calibrate the camera; SLAM on our own recordings — N4A / N4B

**N4A default:** finish and link-check the interrupted patch-4 build in its isolated copy, then rerun the same EuRoC MH01 reference on the target Pi after stable-power evidence. Record source/binary hashes, full command, trajectory, CPU/RSS, temperature and power. The previous 0.0368–0.0416 m is not a speed result and does not establish D435i performance.

**N4B data:** after N0–N3 and separate stereo-profile attestation, capture **IR1+IR2 Y8 640×480/30, gyro/200, accel/100, emitter OFF**. The current four-stream recorder is limited to 120 seconds; the separate 15–24 h stationary record needs a reviewed IMU-only recorder and lossless export.

- Use a fixed measured 6×6 AprilGrid with 80 mm tags and 0.25 spacing ratio. The printed pattern is 580 mm before a one-tag border; the bordered extent is at least 740 mm, so plan a rigid-backed A0 print. Confirm print dimensions/flatness with lab metrology.
- Retain S=120 s, C1–C3=120 s each, six-pose I diagnostics and V1–V3=90 s held-out room sequences. Keep target-calibration motion separate from textured-room VIO evaluation. Inspect the first take before repeating.
- Keep the Pi and cables fixed while moving the camera smoothly with slack. Capture useful translation and rotation about all axes; avoid blur, saturation and shocks. Capture the stationary IMU after warm-up in a separate session. Do not run moving-target and stationary recording simultaneously.
- Export original image payloads losslessly and preserve full-precision raw motion, timestamps, domains, warnings and metadata. Convert SDK milliseconds to the explicitly required units only in derived files, with tested sign/scale. Keep raw files unchanged.
- Use the reviewed ROS 1 Kalibr bag route from camera images and IMU CSV; do not feed a .db3 to Kalibr by suffix assumption. Validate the ROS 1 workstation/environment and import on fixtures before B2.
- Validate factory stereo projection/baseline, then estimate camera–IMU spatial/time parameters with a supported noise model. A target fit, SDK output or Allan plot alone is not calibrated VIO.

**Tools:** reviewed exporter, converter and recorder; Kalibr; Allan analysis; offline ORB adapter; trajectory evaluation. No new converter, dataset schema or threshold is considered accepted by this roadmap.

**Hardware:** same D435i/Pi, qualified calibration data medium under the recorded exception or separate storage, measured target, rigid backing/stand, lighting, calipers/straightedge and backup space. Request a 3–4 h target slot only after the reader pilot. Reserve **30 min warm-up plus 15–24 h** separately for stationary data, with a tested recorder and overnight permission. Retain two verified copies.

**Exit:** three repeat calibration estimates, supported target/motion coverage, ordered common timing coverage, validated import, preserved raw warnings and configuration provenance. Report residuals, uncertainty and fit limits. If Allan averaging times do not support a bias-walk estimate, leave that parameter OPEN. Room trajectory plots are not ground truth.

**Effort:** about 1–2 engineer-days for physical acquisition/review plus overnight elapsed time. Tool or import incompatibility can add 2–5 engineer-days; recapture adds a new slot.

### SLAM live on the Pi — N4C / N5

- Hold the N4B-reviewed binary and settings fixed. Start headless, without a competing camera publisher or visualizer. Run three short repeats, then a proposed ≥30-minute combined-load profile covering map growth, loop closure and recovery.
- Measure each input, output, drop, queue/backlog, reset and tracking state. Measure capture-to-pose only if clock mapping and uncertainty are validated; otherwise report output age as unknown. Separate waiting, tracking and publish time; report P50/P95/P99.
- Record Pi power, throttling, temperature, CPU, RAM and storage under the same load. A 33.3 ms 30 Hz period is arithmetic, not a Pi performance guarantee.
- **Before acceptance:** controller/perception owners must approve useful source-age, loop, stop and resource bounds from measured evidence. No example age/lease number in this document is a safety limit.
- **Hardware/booking:** final Pi, camera, cooling, cables and data path; textured marked route; operator and reviewer; 2–3 h slot after N4B review.
- **Exit:** repeatable initialization/tracking, finite outputs with honest state/reset, no unexplained loss or growing queue, stable power/thermal behavior and source age inside approved bounds. If map save/load is promised, assess it separately. Offline replay does not prove live throughput.

**Effort:** about 1–3 engineer-days. If corrected inputs still produce repeated failures, time-box diagnosis to 2–3 days and compare one challenger on identical retained data.

### Health signal to the STM32 — N6

N6 design and synthetic fixtures can be prepared while data work proceeds, after the controller owner is named. N6 acceptance follows N5.

- **Default link:** reuse an existing proven controller link. If none exists, propose a dedicated 3.3 V UART only after board/pin/voltage/console/ground review. Do not assume Wi-Fi, motor CAN, USB-CDC or a new port.
- **Proposal:** agree session/sequence, source time and age bound, frame, validity/reset state, bounded parser/mailbox and invalidation behavior. Define the clock relation and uncertainty. No fixed public message/API, field widths, rate or timeout is accepted here.
- **Fixtures:** reject malformed length/CRC/version, NaN, duplicate/wrapped sequence, old session, timer wrap/drift, wrong frame, stale/frozen pose with fresh heartbeat, reset/map jump and lost Pi/link. Invalid data cannot refresh a lease. Require a local monotonic timeout and explicit re-enable after reset.
- **Hardware:** reviewed message and transport, named controller implementer and MCU test setup. Synthetic receiver results prove software behavior only, not physical balance.
- **Exit:** reviewed expected-versus-actual receiver traces and controller fallback policy; no actuator reference is enabled by N6.

**Effort:** about 2–4 engineer-days. Fixtures may overlap other work; approval and hardware availability set the calendar path.

### On the robot — N7 supported tests, then separately authorized slow motion

**Mounted/supported step**

- Before mounting, qualify the perception power branch under approved worst load. Review battery/DC–DC/fuse/wiring, USB power, heat, EMI/grounding and independent controller supply. A converter's printed current rating is not qualification.
- Record rigid torso mount, camera-to-body transform, view through allowed pitch/leg travel, cable strain relief and payload/center-of-mass changes. Recheck relevant N1/N2 profile, USB and calibration evidence after topology changes.
- Begin motors-disabled with health receiver and controlled fault injection. Progress to approved supported tests only with the controller owner present, rated stand/restraint, debugger and independent stop.
- **Exit:** no unexpected actuation/reset or loop-budget violation; stale/Pi/link/SLAM/reset faults withdraw optional input within preapproved bounds; STM32 local protections retain authority. A stand does not prove free balance. Static visual-inertial input may truthfully remain uninitialized.

**Effort/booking:** about 1–3 engineer-days; request a 3–4 h robot/controller/stand/stop slot only after N6 review and rail/mount tests.

**Supervised motion step**

- Requires a separate physical-motion approval. Establish the controller's balance baseline first, then tethered balance with zero autonomous references, then bounded manually driven flat-room motion with localization advisory only.
- Use an operator, spotter, cleared route and independent local stop. Predeclare speed/turn/acceleration, clearance, stopping, repeat count and pass/fail bounds. Test Pi/link/tracking loss and preserve every trial. Re-enable only by an operator after reset/recovery.
- Freeze a checksummed Mac-origin runtime bundle in a new Pi runtime directory. Record exact sources/binaries/configs/commands and startup/stop/rollback steps. Do not reset either checkout.
- If no synchronized independent reference exists, label return/checkpoint error as a proxy; do not claim room ATE or absolute accuracy. Report tether loading and its limits. No jumping or autonomous navigation.
- **First deployment:** advisory localization during supervised slow indoor motion, with uncertainty and unsupported cases disclosed.

**Effort/booking:** about 1–4 engineer-days, 2–3 h motion plus a separately available repeat/repair slot. Loan, operator and controller queues are unknown.

### After N7 only — optional navigation expansion

Treat navigation as a separate approved objective. First log acquisition-stamped wheel/body/leg/contact telemetry without fusion; verify clocks, geometry, contact and slip. Add continuous local odometry only when supported by evidence. Keep global map correction separate so loop closure/reset cannot jump the local motion state. Qualify obstacle coverage and occupancy mapping; sparse ORB landmarks are not an obstacle map. The D435i depth stream is only a candidate sensor.

Use Nav2 only after reviewed continuous odometry, frames, obstacle/goal/stopping limits and controller veto are established. robot_localization is optional only if independent wheel/body observations justify it. Do not double-count ORB-consumed camera IMU or correlated wheel pose/twist. [REP-105 frame semantics](https://github.com/ros-infrastructure/rep/blob/master/rep-0105.rst), [Nav2 Jazzy odometry guidance](https://docs.nav2.org/jazzy/configuration_and_development/first_time_robot_setup_guide/odom/setup_robot_localization/), [RTAB-Map ROS 2](https://github.com/introlab/rtabmap_ros/tree/ros2).

**Effort:** estimate after telemetry, obstacle coverage and controller requirements are known. Do not include a navigation delivery date in the first-deployment estimate.

## Booking order and realistic effort

Request slots only after each entry condition is ready:

| Request | Required people/hardware | Readiness and time |
|---|---|---|
| B1: fresh N0–N3 | Pi, supply/cooling, active D435i, direct USB 3 cable, qualified N3 storage, reviewed wrapper, console/network, operator | 3–4 h; may diagnose rather than finish N3 |
| B2: target calibration | Same unit, B1 exits, tested import/export route, measured A0 AprilGrid, stand/light/metrology, backup | 3–4 h; inspect first take before repeating |
| B2A: stationary IMU | Same fixed camera/Pi, reliable power/storage, tested IMU-only recorder, overnight permission | 30 min warm-up plus 15–24 h; separate from target motion |
| B3: live N4C/N5 | Final camera/Pi/cooling/data route and textured room | 2–3 h after N4B review |
| B4: N7 supported | Robot/controller owner, reviewed rail/mount/link, debugger, rated stand/restraint, independent stop | 3–4 h after N6 review |
| B5: supervised motion | Same robot, controller owner, operator/spotter, approved tether/restraint, cleared floor and local stop | 2–3 h plus a distinct repeat/repair slot; separate motion approval |

The phase estimates sum to **about 11–28 engineer-days** if N6 design overlaps work and separately staffed work is available. This is a **low-confidence planning estimate**, not a promise; one engineer still performs the total effort serially. Add the 2–5-day tool/import contingency, a 30-minute warm-up, 15–24 hours stationary recording, recapture, parts delivery and lab/controller queues. Calendar time is unknown until supply, software route, storage, named people and slots are confirmed. Do not shorten the mandatory N2 soak to fit a booking.

### One default and switch rules

- **Default:** native ORB-SLAM3 stereo-inertial for advisory localization, after trusted inputs, calibration, repeated offline evidence, live/resource measurement and reviewed N6/N7 behavior. Existing native build/input work makes this the lowest-rework localization route; it is not a measured Pi ranking or qualified D435i result.
- If corrected N4B inputs still fail reviewed repeatability/resource criteria after bounded diagnosis, compare OpenVINS on identical retained data. Its ROS 2 Jazzy proposal is open at this snapshot, so budget port/build work; do not treat it as ready on the Pi. [OpenVINS Jazzy PR #500](https://github.com/rpng/open_vins/pull/500).
- If the owner's first deliverable changes to occupancy mapping, evaluate RTAB-Map on measured Pi load before selecting it. If already-validated acquisition-stamped wheel/body exports exist and the objective is a smaller rolling/obstacle demo, review that as a different scope; it does not qualify VIO.
- Do not build two estimators or a ROS SLAM wrapper in the first path. Keep the reviewed modular health adapter separate; add a ROS output adapter only for an identified consumer.
- Before distribution, inventory the pinned upstream and dependency licences. Upstream ORB-SLAM3 is GPLv3. [ORB-SLAM3 source and licence](https://github.com/UZ-SLAMLab/ORB_SLAM3).

## Stop conditions and immediate owner actions

| Stop signal | Next action |
|---|---|
| New under-voltage/throttle/reset, USB below 5000M, storage gap or receipt mismatch | Stop the gate; diagnose power, topology or storage with the same load. Do not switch algorithms or relax thresholds. |
| Missing N3 wrapper, storage, permission or replay evidence | Keep N3 OPEN. Review package/receipt dependencies and rebook; do not use a prepared archive as installed-camera proof. |
| Calibration target/import/noise data inadequate | Inspect the first take and reader before recapturing. Keep unsupported noise terms OPEN; preserve every failed take and warning. |
| Repeated calibrated tracking loss or growing source-age queue | Profile one variable at a time, time-box corrected-input diagnosis, then compare one estimator on identical data. |
| Fresh heartbeat with frozen pose, reset, wrong frame or uncertain epoch | N6 receiver rejects the estimate and revokes optional input; require explicit operator re-enable. |
| Mount flex, blocked view, rail drop, EMI or loop disturbance | Return to supported tests and review the mechanical/electrical/controller limits. No jump/fall claim. |
| Controller, operator, stand or independent stop unavailable together | Do not consume a motion booking. Continue offline preparation or rebook. |
| No synchronized room reference | Report continuity/recovery/checkpoint proxies and uncertainty; leave absolute accuracy unclaimed. |
| Unreviewed public message, graph, firmware or experiment-format change | Stop implementation and obtain the required design/format approval first. Preserve source failures and historical evidence. |

**Owner's next actions, in order:**

1. Confirm supply arrival, cooling, camera loan duration, local console/network fallback and current data-storage inventory.
2. Name the controller engineer; identify the STM32H7 board/pinout, existing link and support/stop hardware.
3. Review the N3 wrapper transaction and obtain qualified external bag storage.
4. Confirm the ROS 1 Kalibr workstation and approve/test the offline export route; print and measure the target; secure overnight permission.
5. Request B1, B2 and B2A only when their readiness conditions above are met.
6. At the bench, explicitly authorize camera work, run N0 then N1→N2→N3, review each result and stop at the first unmet condition.
7. Schedule N4 and robot slots only after the prior gate evidence is reviewed. Keep motion and optional navigation as separate approvals.

## Reproduction and limits

Build and render the documentation from repository root:

    cd slides_roadmap
    latexmk -xelatex -interaction=nonstopmode main.tex
    gs -dSAFER -dBATCH -dNOPAUSE -sDEVICE=png16m -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -r156 -sOutputFile=preview/page-%02d.png main.pdf
    swift -module-cache-path qa/swift-cache qa/extract_pdf_text.swift main.pdf qa/revision1-pdf-text.json
    python3 qa/check_revision1.py

The project also provides offline/synthetic fixture and bundle commands in the Phase A runbook. Use those only when their implementation is reviewed. They do not qualify hardware.

This review ran no SSH, camera, ORB-SLAM3, sensor capture, firmware/calibration change, package installation, network mutation, purchase, booking or lab message. No N gate was accepted. Hardware supply/storage, wrapper install, bag conversion, calibrated D435i trajectory, Pi sustained performance, controller interface and physical fallback remain unverified. All numeric calibration, age, loop, motion and stop limits outside N1–N3 remain proposals until approved by the responsible owner.

