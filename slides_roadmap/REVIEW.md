# Roadmap review

Date: 14 October 2026. Scope: slides_roadmap/ROADMAP.md, slides_roadmap/main.tex, and the existing 22-page PDF.

## Findings

### 1. Roundabout or unnecessary work

- The roadmap invents P0–P8 labels alongside the project's accepted N0–N7 gates. Although it says P labels do not replace N gates, the slide path still makes the reader learn two sequences. Use the existing gate names as the path: camera-free preparation → N0–N3 input → N4A/N4B offline evidence → N4C/N5 live/resource evidence → N6 receiver → N7 robot tests. Describe N6 design preparation as parallel work, with N6 acceptance after N5.
- Estimator selection appears in the nine-row synthesis table, a score table, “decisions with defaults,” “alternatives,” the software matrix, and the week plan. These sections repeat the same conclusion and make judgment-based scores look like benchmarks. Keep one default and two evidence-based switch triggers.
- The dated weekly schedule, booking table, and phase-by-phase duration estimates repeat each other. Remove the October–November week promises; keep gate prerequisites, slot lengths, person-day ranges and elapsed capture time in one place.
- The ROS software matrix and standalone frame diagram restate tool choices or explain the optional navigation branch. Fold the first into phase tool lists and retain only the continuous-local-odometry constraint under optional navigation.
- Compare no estimator alternatives during first sensor/camera sessions. Keep the one bounded alternative check after trusted input and calibration have been verified.

### 2. Missing dependencies or hardware that would block a lab session

| Dependency | Evidence at review | Required next action |
|---|---|---|
| Stable Pi power and cooling | The 8 GB Pi boots the existing card, but under-voltage persists. The ordered 5.1 V/5 A supply is not verified as delivered. | Confirm the supply, active cooling, cable path and local-console/network fallback. Recheck power under the actual camera/storage workload. Raspberry Pi's recommended Pi 5 supply is 27 W USB-C; its 5.1 V/5 A profile raises the downstream USB budget. [Raspberry Pi hardware guidance](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html), [27 W supply specification](https://www.raspberrypi.com/products/27w-power-supply/). |
| N3 ROS camera wrapper | N3 preparation says the ROS camera wrapper is absent. Candidate RealSense ROS 4.58.4 and its message/dependency transaction were inspected but not installed. “Pinned librealsense/realsense-ros” overstates readiness. | Before booking N3, review the package transaction and confirm active-device selection, installed versions, parameter readback and topic/QoS tools. Preserve the Phase A profile and N1→N2→N3 order. The current camera identity must come from the 14 October facts and fresh N1; the older N3 preparation note includes an obsolete serial. |
| N3 and bulk-data storage | The 64 GB USB 2 stick measured 1.09 MB/s and is unsuitable. The 128 GB microSD has a calibration-only exception; it is not general N3/bag qualification. No external storage pass is recorded. | Arrange and qualify separate storage for N3/large bags, or resolve the receipt route with the owner. Keep the card exception narrowly scoped. Do not start a bag session because capacity alone appears adequate. |
| Kalibr input and workstation | Roadmap calls the workstation ROS 1 derived-bag route “tested.” The cited project files describe it as a future pilot. Kalibr's upstream guide requires ROS 1 bags; ROS 2 conversion is supported for standard ROS image/IMU types. RealSense .db3 is a ROS 2 rosbag2 file, and the planned SDK recording/export path has not been proved readable by Kalibr. | Choose and prove one offline conversion before collecting irreplaceable calibration data. Recommended: lossless PNG export plus full-precision timestamped IMU CSV, followed by Kalibr's ROS 1 bagcreater; test image pixels, stream counts, time units/domains and common coverage on a labeled synthetic fixture and known sample. Confirm an x86 ROS 1/Kalibr workstation or another reviewed environment. [Kalibr bag format](https://github.com/ethz-asl/kalibr/wiki/bag-format), [Kalibr ROS 2 conversion guidance](https://github.com/ethz-asl/kalibr/wiki/ROS2-Calibration-Using-Kalibr), [librealsense .db3 format](https://github.com/realsenseai/librealsense/blob/master/doc/record-and-playback.md). |
| Calibration capture | An A0 target must be printed flat and measured. The 15–24 h stationary IMU record needs its own recorder, storage, power, warm-up and overnight permission; target-motion takes cannot be stationary at the same time. | Complete the tool/target pilot before B2. Reserve the separate stationary slot only after a stop/recovery-tested recorder is reviewed. Kalibr recommends about 15–24 h for Allan-based noise parameters; that is a recommendation, not a transport-gate duration. [Kalibr noise guidance](https://github.com/ethz-asl/kalibr/wiki/IMU-Noise-Model), [camera–IMU capture guidance](https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration). |
| Controller integration | Exact STM32H7 board/pinout, controller engineer, available link, power rail and robot slot remain unknown. A fresh link/message/API and firmware work would need design review. | Name the controller owner and identify hardware before N6 implementation or B4. Keep the link/message, age and stop policy proposals until reviewed; synthetic fixtures do not establish physical balance. |

### 3. Durations

- The “4–6 calendar weeks” target and W1–W6 dates imply a delivery schedule before the power supply, ROS wrapper, external storage, calibration reader, workstation, controller staff and lab slots are confirmed. Remove those dates and do not publish a calendar estimate yet.
- The roadmap's 11–28 engineer-day sum is only a low-confidence planning estimate. It includes unfinished conversion/interface work, while the existing build had an interrupted power event and its resumed duration on the 8 GB Pi is unknown. Keep the 2–5-day tooling contingency separate and state what it excludes.
- Keep hands-on effort separate from elapsed capture and queue time. The stationary record adds roughly 30 minutes of warm-up plus 15–24 hours elapsed; it cannot overlap the moving-target session. A 3–4-hour N1–N3 booking may diagnose a failure without completing N3.
- Preserve the exact N2 20→105→300-second sequence. Do not shorten it to fit a slot or treat a short stereo demonstration as equivalent.

### 4. Wrong or unsupported technical claims

| Draft claim | Review |
|---|---|
| “tested workstation Kalibr ROS 1 derived-bag route” | Unsupported and inconsistent with the local calibration plan, which leaves the exporter and exact bag-reader route for future implementation/testing. Kalibr's own documentation says it expects ROS 1 bags; its ROS 2 guidance describes conversion and standard message-type limits. Replace with an explicitly untested dependency and a pre-capture proof step. |
| “pinned librealsense/realsense-ros/Jazzy” | The SDK package is recorded as 2.58.4; RealSense ROS 4.58.4 is only a candidate inspected offline, and its wrapper is absent. State installed versus proposed versions separately. |
| ORB/RTAB/OpenVINS/wheel-depth scores such as 68/100, 61/100 and 77/100 | These are an individual's weighted planning judgments, not measured WBR/Pi results. Their precision distracts from the evidence. Remove numbers from the roadmap and slides; describe the objective and test that would change the default. |
| 300-second stereo-memory comparison | The arithmetic is true for a hypothetical stereo stream, but it risks conflating that case with the mandatory 300-second N2 profile, which is IR1 Y8 at 15 Hz plus raw gyro/accel. Remove the comparison from the operational route. Keep the exact N2 profile unchanged. |
| “OpenVINS Jazzy support is available” if inferred from PR #500 | PR #500 is open, not merged, at this review snapshot. Keep it as a porting risk, not ready Pi support. [OpenVINS Jazzy PR #500](https://github.com/rpng/open_vins/pull/500). |
| Nominal factory calibration or room trajectory as proof of calibrated accuracy | The retained warning, assumed noise and unknown camera–IMU offset block that conclusion. Keep the warning and label loop/checkpoint metrics as proxies without synchronized ground truth. |

Other external statements were checked against primary sources. Raspberry Pi's power guidance supports the 5.1 V/5 A supply requirement for high USB load. Kalibr's camera–IMU procedure calls for a fixed target, low blur and motion exciting all axes; its YAML guide states the time-shift convention. The current Jazzy ORB-SLAM3 ROS wrapper cited in the draft describes monocular and monocular-inertial modes only; it is not the stereo-inertial default. [Wrapper README](https://github.com/gjcliff/ORB_SLAM3_ROS2).

### 5. Where the owner would not know exactly what to do next

The old roadmap names people only by role, assigns dates to unbooked slots, and does not surface which known dependency blocks the first booking. Replace it with this ordered owner checklist:

1. Confirm 5.1 V/5 A supply delivery, cooling, active camera loan window, local console/network access and current storage inventory.
2. Identify the STM32H7 controller owner, exact board/pinout, existing link and first supported-robot slot.
3. Review the N3 wrapper/dependency transaction and obtain qualified external storage for ROS bags.
4. Approve and prove the offline image/IMU-to-Kalibr ROS 1 path; print and measure the AprilGrid; confirm the workstation and overnight access.
5. Request B1 (fresh N0–N3), then B2 (target capture) and separate B2A (stationary noise record) only when their entry conditions are ready.
6. At the bench, wait for the owner's explicit “CAMERA AVAILABLE” authorization, run N0 then N1→N2→N3, and stop at the first unmet condition.
7. After each evidence review, schedule the next slot; do not reserve motion or navigation work as if earlier gates had passed.

## Fixes required in ROADMAP.md and main.tex

- Replace P0–P8 with gate-aligned stages.
- Remove duplicated synthesis tables, score weights and week calendar.
- Add current N3 wrapper/storage/conversion blockers and one recommended Kalibr conversion route, labeled unimplemented and untested.
- Put the owner’s first actions, lab readiness and effort/elapsed-time distinction in one concise path.
- Keep the STM32H7 safety boundary, current-unit identity distinction, calibration warning, exact N2 thresholds and separate navigation scope.

