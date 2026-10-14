# Phase 1 — WBR perception implementation outline

Planning snapshot: 10 October 2026. This is a page specification, not a built deck or hardware validation. Audience: the embedded/Linux-capable fourth-year owner, then lecturer and senior. All text, captions, notes and labels will be English. Each numbered row is one physical page, including section dividers. Expand abbreviations inline on their first main-content use, not on the cover, contents or references. Short numbered noun-phrase titles, one message/takeaway per page, deeper implementation details in speaker notes.

## Authority, status and preservation

`slides_course/BRIEF.md` is authoritative: **NO gate has PASSED on the Pi; restart fresh at N0.** Accepted ownership rules are KNOWN. Dated observations are HISTORICAL, with numeric observations also MEASURED and sourced. Unexecuted tests/mechanisms are PLANNED; unsupported quantities are UNKNOWN. Annotate relevant claims rather than adding an evidence-legend slide. Historical summaries named `n2-accepted` or containing PASS do not establish current qualification.

The older PROJECT_STATE/NEXT_GATE/EVIDENCE_INDEX drafts do not override the owner. September 8 VM/Docker USB2 audit is NO-GO; historical Pi sessions observed 5000M and later 480M. A 105-second run did not complete N2. Preserve all historical evidence and calibration warnings. No current camera availability or state is inferred.

Deck preparation is camera-free: no device command, SSH hardware session, camera process, ORB-SLAM3 run, firmware/calibration write or capture. Future physical execution requires the owner's exact `CAMERA AVAILABLE`; flags are attestations, not authorization. Proposed nodes/interfaces/dataset formats are teaching material, not approved implementation changes. No files outside slides_course are changed, and no Git mutation is permitted by the brief.

## Visual contract for Phase 2

Copy the pre-document preamble from the read-only OS `slides_course/main.tex`: moloch, 208×117 mm 16:9 canvas, 12 pt Avenir Next and Menlo, navy #1F3A5F, teal #2A9D8F, fault-only orange #E76F51, paper #FAFAF7, the figure/repeat-caption, takeaway, evidence and named-placeholder macros. Retain 6 mm margins, global list spacing and 1.12 line spread, top-aligned columns, numbered figures and page-only footer. Replace project metadata and V/W ids with P ids; do not inherit OS names, class or controller. Unknown cover identities remain absent.

Exact architecture, paths, transforms, clocks, timing, queues, gates, states and boundary drawings are TikZ. P01–P12 are explanatory scenes, never measurement or wiring evidence. Reference every figure in nearby text; captions directly below, one number per unique figure. Body fonts stay 12 pt; split content rather than shrink. Result pages have empty axes and exactly “To be filled after N4/N5 runs”.

The referenced academic-beamer-deck skill and committed template were read with `git show HEAD:prompts/academic-beamer-deck/...`; template files are absent from the OS worktree but present in HEAD. OS playbook/layout/reviewer briefs and course README/REVIEW_LOG were read. The OS review has a pending round; it does not certify this deck. Phase 1 stops at these files. Outline approval precedes Phase 2 frame writing; PDF build and every-page full-size QA occur only in Phase 2.

## Source register

Local paths are relative to the WBR root; keys are authoring provenance, not filename clutter on slides. Inspected WBR HEAD `5932457`, branch `feat/d435i-camera-capture-20260913`, dirty tree. Historical runtime identity requires dirty-source/binary hashes as well as revision. `config/orbslam3/` and `config/realsense/` are empty, not qualified configs.

| Key | Source and scope |
|---|---|
| B | slides_course/BRIEF.md; owner authority and required depth. |
| R | AGENTS.md, CLAUDE.md; preservation, safety, evidence and approval. |
| A | README.md, docs/ARCHITECTURE.md, docs/DECISIONS.md; accepted Pi/STM32 and two-IMU ownership. |
| S | docs/PROJECT_STATE.md, docs/NEXT_GATE.md, docs/EVIDENCE_INDEX.md; draft/OPEN context, superseded by B for status. |
| N | docs/RPI5_NATIVE_PERCEPTION_BRINGUP.md; native deployment plan, historical commands are not authorization. |
| H | docs/D435I_BASELINE_AUDIT.md, docs/DOCKER_RUNTIME_ARCHITECTURE_REVIEW.md; September 8 VM/Docker history. Deleted root audit inspected with git show HEAD:D435I_BASELINE_AUDIT.md. experiments/2026-09-08-d435i-baseline/RESUME_SUMMARY.json supplies saved metrics. |
| E | docs/PI5_NATIVE_SENSOR_VALIDATION_2026-09-12.md and experiments/2026-09-12-pi5-native-sensor-validation/EVIDENCE_RECONCILIATION.md; saved 105-second analysis/logs and USB regression, not current PASS. September 13 archived summaries remain HISTORICAL even where internally optimistic. |
| G | experiments/2026-09-12-pi5-native-sensor-validation/PHASE_A_RUNBOOK.md; exact current N1→N2→N3 rules and thresholds. |
| T | docs/PERCEPTION_TOOLING_ARCHITECTURE.md and same experiment directory N3_PREPARATION.md; tools/process ownership, candidate wrapper 4.58.4; scripts/env.sh sets domain 42. |
| C | docs/D435I_VIO_CALIBRATION_READINESS.md; unit reports BMI085, SDK fallback, unknown noise/time offset and historical metadata. |
| O | docs/ORB_SLAM3_OFFLINE_PREPARATION.md and docs/NEXT_TWO_WEEKS_PERCEPTION_PLAN.md; planned mono-inertial backlog, not completed stereo implementation. |
| U | Read-only third_party/ORB_SLAM3, recorded revision 4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4: src/System.cc, Settings.cc, Tracking.cc, Frame.cc, ImuTypes.cc, Examples/Stereo-Inertial/stereo_inertial_euroc.cc, EuRoC.yaml and RealSense_D435i.yaml. Example calibration is not this unit's calibration. |
| V | OS slides_course/main.tex, README.md, REVIEW_LOG.md; committed academic-beamer-deck skill/templates; slides/SLIDE_PLAYBOOK.md, LAYOUT_BRIEF.md, REVIEWER_BRIEF.md. |
| PI | [Pi 5 official page](https://www.raspberrypi.com/products/raspberry-pi-5/), [Active Cooler](https://www.raspberrypi.com/products/active-cooler/), verified 2026-10-10; product appearance/ports, not measured runtime performance. |
| RS | [Vendor comparison](https://www.realsenseai.com/compare-all-cameras/), [Intel D435i specifications](https://www.intel.com/content/www/us/en/products/sku/190004/intel-realsense-depth-camera-d435i/specifications.html), [vendor source documentation](https://github.com/realsenseai/librealsense/blob/master/doc/d435i.md?plain=1). Comparison/search records verified; detailed product-page fetching failed, so omit unverified spec numbers. Older vendor source describes BMI055; C records this unit's BMI085. |
| TF | ROS official [REP-103 source](https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-0103.rst), [REP-105 source](https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-0105.rst), verified 2026-10-10; rendered REP pages returned bot challenges. |
| Q | [Official Jazzy QoS documentation source](https://raw.githubusercontent.com/ros2/ros2_documentation/jazzy/source/Concepts/Intermediate/About-Quality-of-Service-Settings.rst), verified 2026-10-10; rendered docs URL returned bot challenge. |
| CLK | [Pinned librealsense global timestamp reader](https://github.com/realsenseai/librealsense/blob/v2.58.4/src/global_timestamp_reader.cpp), verified 2026-10-10; algorithm evidence, not unit synchronization. |
| P | Campos, Elvira, Gómez Rodríguez, Montiel, Tardós, [ORB-SLAM3 primary paper](https://arxiv.org/abs/2007.11898), [official source](https://github.com/UZ-SLAMLab/ORB_SLAM3), verified 2026-10-10. Cite arXiv record until journal metadata is separately verified; no guessed pages/DOI. |
| EU | Burri et al., [EuRoC dataset primary page](https://projects.asl.ethz.ch/datasets/euroc-mav/), 2016; paper DOI 10.1177/0278364915620033, dataset DOI 10.3929/ethz-b-000690084, verified 2026-10-10. Old DokuWiki URL has moved. |
| K | [Kalibr maintainer camera–IMU instructions](https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration), verified 2026-10-10; tool/import choice PLANNED. |
| I | [imu_utils maintainer repository](https://github.com/gaowenliang/imu_utils), verified 2026-10-10; local compatibility/noise unmeasured. |
| EV | [evo maintainer metrics](https://github.com/MichaelGrupp/evo/wiki/Metrics), [researchers' trajectory evaluation](https://github.com/uzh-rpg/rpg_trajectory_evaluation), verified 2026-10-10; method, not project accuracy. |

## Numbered page plan

| Page | Title | Message | Figure/layout | Sources |
|---:|---|---|---|---|
| 1 | Cover | WBR perception implementation guide; conceptual platform, no validation claim or invented team identities. | P01 | B,A |
| 2 | Contents | Paper flow: motivation, theory, detailed design, gates, evaluation, decisions, status, roadmap, conclusion. | Equal TikZ boxes | B,V |
| 3 | 1. Introduction | Section divider. | None | B |
| 4 | 1.1 Robot context | Wheel-biped robot (WBR) perception supports navigation while STM32 retains balance. | P02 | A |
| 5 | 1.2 Engineering problem | A plausible pose can be stale, misframed or uncalibrated; Linux failure must not remove balance. | TikZ failure chain | A,B |
| 6 | 1.3 Objectives | Qualify input, reproduce estimation, quantify quality and define the safe boundary. | Text | B,O |
| 7 | 1.4 Research questions | Can the Pi sustain trusted inputs, initialize repeatedly and supply fresh useful estimates within measured resources? | Text | B,O |
| 8 | 2. Background | Section divider. | None | B |
| 9 | 2.1 Stereo geometry | Infrared (IR) correspondence and calibrated baseline yield depth; rectification supports reliable pairing. | TikZ rays | U,RS |
| 10 | 2.2 Visual-inertial estimation | Visual-inertial odometry (VIO) combines images with inertial measurement unit (IMU) motion, distinct from body control. | P03 | P,A |
| 11 | 2.3 Odometry and mapping | Simultaneous localization and mapping (SLAM) adds revisiting and map correction; continuity is a separate requirement. | TikZ paths | P,A |
| 12 | 2.4 D435i streams | Two IR views and motion support stereo-inertial inputs; unit historically reports BMI085 despite older BMI055 descriptions. | P04 | RS,C |
| 13 | 2.5 ROS communication | Robot Operating System 2 (ROS 2) topics and Data Distribution Service (DDS) transport do not guarantee usable timely data. | TikZ pub/sub | Q,A |
| 14 | 2.6 QoS compatibility | Quality of Service (QoS) compatibility is offered/requested; reliable subscription cannot consume best-effort-only publication. | Table | Q |
| 15 | 2.7 EuRoC baseline | EuRoC micro aerial vehicle data provide stereo, IMU and reference trajectories; these are published dataset properties, not Pi results. | Text | EU,P |
| 16 | 3. System design | Section divider. | None | B |
| 17 | 3.1 Machine ownership | Mac is canonical; Pi acquires locally; Secure Shell (SSH) carries control and small evidence; workstation can supply reference runs. | TikZ machine domains | R,N,T |
| 18 | 3.2 Control boundary | Pi owns perception; STM32H7 owns Linear Quadratic Regulator (LQR), Virtual Model Control (VMC), Finite State Machine (FSM), balance and motor safety. | TikZ architecture | A,R |
| 19 | 3.3 Physical platform | Pi 5 8 GB, Ubuntu and Non-Volatile Memory Express (NVMe) storage are the target; actual supply/cooling/storage must be documented anew. | P05 | S,N,PI |
| 20 | 3.4 Local sensor path | Universal Serial Bus 3 (USB3) feeds kernel/librealsense/realsense-ros; recording and processing stay on Pi. | TikZ data path | T,N |
| 21 | 3.5 Processes and threads | SDK capture, wrapper, observer and recorder have distinct owners; upstream tracking runs on caller with mapping/loop workers. | TikZ lanes | T,U |
| 22 | 3.6 Queues and backpressure | Trace SDK/DDS/executor/recorder/estimator queues and policies; unknown drop counters remain UNKNOWN. | TikZ FIFO | G,Q,U |
| 23 | 3.7 Payload budget | Calculated IR1 payload is 640×480×1×15 = 4.608 decimal MB/s; stereo doubles image payload before overhead. | Equation/table | G,U |
| 24 | 3.8 Storage qualification | Pin mount source/UUID/device identity and measured throughput/readback; microSD is for operating system and small logs. | P06 | G,R |
| 25 | 3.9 Software provenance | Record packages, source revisions, dirty-file hashes and settings; installed runtime can differ from checkout. | Table | H,T,R |
| 26 | 3.10 Frame definitions | The transform (TF) system relates frames; each pose defines parent/child, axes/origin, units and stamp; world/map/odom differ. | TikZ triads | A,TF |
| 27 | 3.11 Robot transform tree | PLANNED map→odom→base_link→body→imu_body with camera mount; world is optional reference, never competing parent. | TikZ tree | A,TF |
| 28 | 3.12 Camera transform tree | Separate camera, camera_optical, imu_camera, left/right camera frames; capture actual wrapper names/static transforms. | TikZ subtree | A,C,G |
| 29 | 3.13 Independent IMUs | D435i IMU supplies VIO; STM32 body IMU supplies balance; no naive fusion across independent clocks/mounts. | P07 | A,C |
| 30 | 3.14 Transform direction | p_b = T_b_c1 p_c; test inverse/basis vectors and column-major SDK versus row-major OpenCV arrays. | TikZ basis example | C,O,U |
| 31 | 3.15 Clock domains | Device/capture clock, host steady/civil time and ROS time need explicit relationship before subtraction. | TikZ domain boxes | A,C,CLK |
| 32 | 3.16 Timestamp chain | Preserve capture, hardware, driver, ROS header, publish, receipt, processing start/end and output semantics. | TikZ timeline | A,C |
| 33 | 3.17 Global time | Enabled global-time option is not measured camera–IMU offset or pure USB latency. | Table | C,CLK |
| 34 | 3.18 Timing observations | Same-clock receipt→processing/output intervals are measurable; capture→output needs mapping uncertainty; bag time is separate. | TikZ brackets | C,G |
| 35 | 3.19 Calibration register | Stereo geometry, camera–IMU extrinsics/time offset and device noise need independent provenance; SDK defaults are not measurements. | Table | C |
| 36 | 3.20 Stereo calibration | Match chosen profiles/distortion/rectification; inspect epipolar residuals and left/right time pairing before stereo estimation. | TikZ epipolar lines | U,K,C |
| 37 | 3.21 Calibration capture | PLANNED measured AprilGrid and all-axis motion support calibration; textured-room VIO motion has a different purpose. | P08 | C,K |
| 38 | 3.22 IMU noise | Allan variance/deviation separates noise and bias across averaging times; long enough full-precision stationary input is required. | Conceptual axes, no data | C,I |
| 39 | 3.23 Calibration tools | PLANNED Kalibr handles spatial/temporal estimation; imu_utils handles noise, not complete calibration; import/build trade-offs remain. | Table | K,I,C |
| 40 | 3.24 Algorithm threads | ORB-SLAM3 uses Oriented FAST and Rotated BRIEF features (expand component names in notes); tracking/mapping/loop closing have distinct roles. | TikZ source flow | P,U |
| 41 | 3.25 Tracking | Pair stereo images and image-bounded IMU intervals; extract/match features and estimate pose; inspect tracking/reset state before tuning. | TikZ stages | U |
| 42 | 3.26 Mapping and Atlas | Local optimization estimates map/inertial state; Atlas manages multiple maps/merging; correction can jump the output frame. | TikZ keyframes/maps | P,U |
| 43 | 3.27 Inertial initialization | Estimate gravity, velocity and biases with sufficient excitation; stereo scale does not remove calibration/timing requirements. | TikZ state stages | P,U |
| 44 | 3.28 Settings YAML | Audit camera model/intrinsics/size/fps, stereo baseline/rectification, IMU.T_b_c1/Frequency/noise, features and viewer in pinned parser. | Field table | U,O,C |
| 45 | 3.29 Input association | PLANNED accel interpolation on gyro times requires bracketing/gap rejection/no extrapolation; 200 Hz combined input is not 200 Hz raw accel. | TikZ samples | O,C |
| 46 | 3.30 Health interface | PLANNED pose/velocity, frames/time, validity, tracking/reset state and age cross boundary; uncertainty may be unavailable. | TikZ candidate fields | A,B |
| 47 | 3.31 Health supervision | PLANNED absent/initializing/fresh/stale/invalid transitions require receiver checks; heartbeat does not prove source freshness. | TikZ states | A,B |
| 48 | 3.32 Controller fallback | STM32 rejects unusable perception and retains body estimation/balance; optional autonomy references degrade under local policy. | TikZ boundary | A,R |
| 49 | 4. Implementation by gate | Section divider. | None | B |
| 50 | 4.1 Gate ladder | N0→N1→N2→N3→N4A/B/C→N5→N6→N7; owner confirms no current Pi PASS. | TikZ ladder | B,G,O |
| 51 | 4.2 N0 platform | Fresh restart needs recorded ARM64 Ubuntu/Jazzy, synchronized time, stable supply/cooling and clean health; inventory actual RAM. | P09 + checklist | G,N,B |
| 52 | 4.3 N1 USB and identity | N0 plus CAMERA AVAILABLE; own direct camera branch ≥5000M, separate identifiers, normal-user access and fresh sealed receipt. | TikZ USB topology | G,C |
| 53 | 4.4 N2 progression | Exact IR1 640×480 Y8/15, gyro/200, accel/100 through 20→105→mandatory 300 seconds; no fallback or combined IMU. | TikZ timeline | G |
| 54 | 4.5 N2 acceptance | Require exact rate/gap limits, positive timestamps/frame steps, coherent images, raw-log review and explicit acceptance; not calibration PASS. | Threshold table | G |
| 55 | 4.6 N3 live pipeline | Reviewed N2, qualified storage, wrapper inspection; one publisher/readback and complete 60-second observation before recording. | TikZ processes | G,T |
| 56 | 4.7 N3 bag and replay | Ten-topic IR1 baseline with context; finalized bag, stopped live camera, isolated full replay and count/type/stamp/payload match. | TikZ domains | G |
| 57 | 4.8 Stereo extension | PLANNED separately reviewed IR2 profile/topic/storage/calibration extension precedes N4B; accepted IR1-only N2/N3 stay intact. | TikZ fork | B,G,O |
| 58 | 4.9 N4A EuRoC | Authorized execution, pinned isolated build and dataset/config; repeated initialized finite trajectories plus reference evaluation, not compilation alone. | Checklist | O,U,EU |
| 59 | 4.10 N4B offline D435i | Qualified stereo pixels/full-precision motion/domains, reviewed numeric calibration and tested adapter; immutable raw/derived hashes. | P10 | C,O,B |
| 60 | 4.11 N4C live estimation | Accepted offline stereo and renewed sensor/ROS prerequisites; bounded live continuity, pairing, backlog, loss and shutdown qualification. | TikZ queues | B,G,U |
| 61 | 4.12 N5 profiling | Qualified runs need named latency/resource/accuracy measures and fixed repeated trials; numerical budgets await pre-run approval. | Checklist | B,O,EV |
| 62 | 4.13 N6 health fixtures | PLANNED absent/stale/invalid/reset fixtures qualify freshness semantics before physical transport. | TikZ fault matrix | A,B |
| 63 | 4.14 N7 STM32 boundary | Reviewed health interface and separate controller approval; staged Pi failures must preserve controller ownership; stability unverified. | TikZ safety domains | R,A,B |
| 64 | 4.15 Reproduction and evidence | Deploy new checksummed Mac bundles; retain full commands/config/raw logs/review receipts; never reset checkouts. | TikZ artifacts | G,T |
| 65 | 4.16 Bottom-up diagnosis | Hardware→USB→raw→clocks→driver→ROS→QoS→calibration→ORB-SLAM3→trajectory→evaluation; fix first failed layer. | TikZ ladder | A,H,G |
| 66 | 4.17 Failure isolation | USB2/power/permissions/topic silence/bad association/calibration fallback need different evidence and remedies. | Table | H,E,C |
| 67 | 4.18 Bounded AI tickets | Artificial intelligence (AI) agents get one uncertainty, allowed files/actions, fixtures, evidence and stop conditions; owner accepts gates. | P11 | R,T,O |
| 68 | 5. Evaluation method | Section divider. | None | B |
| 69 | 5.1 Experimental design | Freeze input/settings/binary; predeclare hypotheses; retain failures; at least three offline repeats is a PLANNED backlog minimum. | Table | O,B |
| 70 | 5.2 Absolute error | Absolute Trajectory Error (ATE): E_i = Q_i^-1 S P_i after association/alignment; report translation root mean square error and coverage. | Equation/TikZ | EV |
| 71 | 5.3 Relative error | Relative Pose Error (RPE) compares Q_i^-1 Q_j with P_i^-1 P_j; specify time/distance delta and translation/rotation statistics. | Equation/TikZ | EV |
| 72 | 5.4 Alignment and evo | Rigid alignment for metric stereo-inertial evaluation; scale fitting is diagnostic and can hide scale error; record evo options/tolerance/version. | Command plan | EV |
| 73 | 5.5 Initialization and continuity | Success denominator, initialization time, tracking loss duration, resets and relocalization need preserved state events and failed trials. | Event schema | O,U |
| 74 | 5.6 Latency and loss | P50/P95/P99 percentiles use named same-clock intervals; sequence/count gaps and unavailable queue/drop counters stay distinct. | Metric table | B,G,C |
| 75 | 5.7 Resource measurements | Log Central Processing Unit (CPU) load/frequency, temperature, memory, Resident Set Size (RSS), throttling and queue depth against events. | TikZ monitor lanes | T,O |
| 76 | 5.8 Accuracy results | Empty ATE/RPE axes; To be filled after N4/N5 runs; D435i accuracy remains UNKNOWN without suitable reference. | Empty TikZ axes | B,EV |
| 77 | 5.9 Timing results | Empty latency/queue/drop panels; To be filled after N4/N5 runs; no fictional curves, zeros or targets. | Empty TikZ axes | B |
| 78 | 5.10 Resource results | Empty CPU/frequency/temperature/memory/throttle axes; To be filled after N4/N5 runs. | Empty TikZ axes | B |
| 79 | 6. Engineering decisions | Section divider. | None | B |
| 80 | 6.1 Runtime and USB | Recommend native Pi/direct known-good USB-A↔USB-C; containers/topology changes need equivalent qualification and reproducibility benefit. | Table | N,H,G |
| 81 | 6.2 Inputs and clocks | Keep accepted IR1 640×480/15 gate; PLANNED stereo starts there; emitter-off feature trials are separate; global time needs domain evidence. | Table | G,C,U |
| 82 | 6.3 Algorithm and calibration | Upstream EuRoC/offline before wrapper/live; Kalibr candidate plus measured noise; wheel odometry waits for timing/frame/slip evidence. | Table | A,O,C,B |
| 83 | 6.4 Interface decisions | PLANNED rate, transport, thresholds and uncertainty fields await receiver evidence and architecture review. | Table | A,R,B |
| 84 | 7. Current status and roadmap | Section divider. | None | B |
| 85 | 7.1 Historical evidence | September 8 x86 VM/Docker NO-GO; September 12/13 history cannot promote current gates; 105-second run was not final N2. | TikZ dated timeline | H,E,B |
| 86 | 7.2 Current evidence gaps | No Pi gate passed; fresh N0 onward, USB/storage, N2/N3, calibrated stereo estimation and health remain unqualified. | Status table | B,S,C |
| 87 | 7.3 Conditional roadmap | Fresh N0→N1→N2→N3, reviewed stereo/calibration extension, N4A/B/C→N5→N6→N7; blockers yield records, not deadline promises. | P12 | B,O,G |
| 88 | 8. Conclusion | Trust needs qualified acquisition/timing/calibration/repeated estimation; controller independence protects balance; next step is N0 evidence. | Text | A,B,G |
| 89 | References | One compact primary-source page; published methods are distinct from historical project observations and plans. | Two columns | PI,RS,TF,Q,CLK,P,EU,K,I,EV |

## Gate authoring details (pages 50–63)

N0–N3 criteria below preserve G. N0 pulls platform prerequisites out of the existing N1 precheck for teaching; it is not a new implemented receipt. N4A/B/C retain the repository's subgate names. N5–N7 are PLANNED organizing gates requested by B, not existing accepted validators. No new numeric accuracy/latency/staleness targets are invented. Before those experiments, the owner must approve quantitative budgets and the trial matrix; lack of an approved budget prevents a performance PASS.

| Gate | Entry conditions | Explicit PASS contract | Evidence artifacts | Typical failure / stop |
|---|---|---|---|---|
| N0 platform | Owner starts fresh; read-only inventory, no camera access. | Actual ARM64 Ubuntu 24.04/Jazzy identity, synchronized UTC, documented supply/cooling, `throttled=0x0`, temperature <75°C and MemAvailable ≥512 MiB at precheck. Current 8 GB target checked against actual inventory. Stability under load must be observed again at N2/N5. | Platform/boot/package/time/power/cooling inventory, unfiltered kernel/health logs, exact utility hashes. | Undervoltage/sticky throttle flags, wrong architecture, unsynchronized time; retain evidence, resolve cause before fresh checks. |
| N1 direct D435i | N0 eligible, explicit CAMERA AVAILABLE, cable attestation, no competing camera process. After storage probing, take fresh N1. | Camera's own direct branch ≥5000M, expected SDK device/ASIC/firmware-update/USB-descriptor identity recorded separately, normal-user video/HID/IIO/custom-HID control access, expected firmware/IMU identity. Receipt eligible for this host/boot and ≤2 h old. | Sealed result.json, USB/sysfs/kernel snapshots, normal-user SDK enumeration, access modes/groups/process owners. | 480M → STOP before SDK enumeration/N2; missing identity/access → inspect exact branch/rule, never broad permissions or firmware update. |
| N2 raw sensor | Eligible N1; exact IR1 640×480 Y8/15 Hz, gyro/200 Hz, accel/100 Hz; no combined IMU, extra streams or fallback. | Reviewed 20 s smoke →105 s reproduction→mandatory 300 s raw soak. IR 14.25–15.75 Hz, gyro 190–210 Hz, accel 95–105 Hz; max image gap ≤0.20 s, motion ≤0.05 s. Positive timestamp/frame steps, no repeated/backward stamps or missing image frame numbers, valid coherent Y8 samples, clean kernel/SDK faults and documented health/startup offsets. Final reviewed accept-n2 receipt, not automatic capture success. | Finalized CSV, full argv/stdout/stderr, before/after topology, continuous raw journal, one-Hz health, three PGMs from separate 12 s image check, source/binary/package hashes, recomputed analyses and real review.json. | Faults/reset/disconnect/power, rate/gap violation, bad shutdown, missing images/review. Vendor CSV omits domains/rounds IMU; does not prove synchronization/calibration. Preserve IMU warning; transport qualification cannot establish VIO readiness. |
| N3 ROS + record/replay | Reviewed N2; qualified external storage; fresh N1 after storage probe; approved installed wrapper/version inspection. | Read back parameters on one `/camera/camera` publisher; observe complete 60 s live window, then bounded explicit-topic recording under load. Required frame/stamp/rate/context checks, clean SIGINT finalization and metadata. Stop live camera; isolated complete replay matches stored counts/types/header/full decoded payload order/hashes including latched context; review complete logs. | Parameter dump/readback, graph/QoS/frame/static-TF evidence, live/record observer metrics, bag info/finalized metadata/hashes, shutdown logs, quiet-domain and full replay receipts. | Missing required context/QoS mismatch, count discrepancies, unsafe mount, forced shutdown, live contamination. No `-a`, no combined IMU, no reindex-and-call-clean shortcut. |
| N4A upstream EuRoC | Separately authorized future execution; pinned isolated build, vocabulary, checked EuRoC files/settings/reference and approved trial plan. | Complete input accounted for; initialized finite monotonic trajectory exports and tracking/reset reports reproducible across planned repeats; reference-associated ATE/RPE and declared qualification budgets satisfied. Build alone cannot PASS. | Full build/run logs, source/config/dataset/binary hashes, association/reference policy, both trajectory exports, metrics and all trials. | Dependency/display/input-boundary/config error, initialization/loss, incomplete trajectory; do not patch upstream to hide failure. |
| N4B offline D435i stereo | Reviewed stereo extension, lossless left/right pixels, raw full-precision motion/domains; trusted calibration/time offset/noise, tested adapter, approved budget. | Stereo pairing/epipolar and IMU coverage checks pass; deterministic conversion accounting and transform/noise tests; repeatable initialization/continuity and finite outputs meet predeclared budgets. Accuracy claim only with suitable reference. | Original bag/context hashes, derived manifest/rejection/association reports, calibration target/tool/input/output identities, trajectories/state/resource metrics and failed trials. | Missing IR2, CAD/default IMU geometry treated as measured, zero noise placeholders, gaps/extrapolation, wrong transform/time-offset sign; remain OPEN. |
| N4C live stereo-inertial | Accepted N4B; renewed N0–N3 checks plus reviewed stereo live configuration and bounded run plan. | Required stereo/motion delivery and initialization/tracking continuity meet declared budgets; no unexplained backlog/drop, clean shutdown and complete input/output accounting. | Full live logs, pairing/queue/drop observations, tracking timeline, trajectory, package/config/binary identities and health. | Offline success but live lag, pairing loss, ROS scheduling/QoS/thermal fault; reproduce at first failed layer. |
| N5 profile/evaluate | Qualified input/estimator, fixed trials, clock definitions and approved numeric budgets. | Repeatable complete measurement coverage for initialization/loss/latency/resource metrics; suitable reference/alignment for claimed accuracy; all declared budgets met and missing counters explicitly UNKNOWN. | Raw timing/events/health, clock mappings with uncertainty, exact evo commands/options/version, percentiles/count reconciliation and all repeats. | Comparing incompatible clocks/datasets or best-run-only plots, absent ground truth, unknown loss reported zero. |
| N6 health semantics | N5 evidence; approved candidate interface and offline/synthetic fixture plan. | PLANNED tests reject absent/stale/invalid/nonfinite/wrong-frame/reset/session-mismatch data and accept eligible fresh data under receiver-side policy; source-age accounting justified. Synthetic success is TOOLING ONLY. | Fixture inputs/expected transitions/results, freshness clock assumptions, review record and interface version. | Receipt-only heartbeat mistaken for capture freshness, old session accepted, undocumented frame jump or missing uncertainty fabricated. |
| N7 STM32 boundary | Reviewed N6 contract plus separate controller/hardware/safety authorization; staged validation plan. | PLANNED controller evidence demonstrates retained body estimation/balance ownership and rejection/degradation for disconnected/stale/invalid/restarted Pi under approved test conditions. No motor/firmware action authorized by deck task. | Controller and Pi synchronized event evidence with explicit clock relation, fault scenarios, operator review, firmware/interface identities and measured behavior. | Perception used in hard-real-time balance path, unsafe auto-resume, untested physical stability presented as assured. |

### Exact baseline versus stereo extension

G's N2/N3 baseline is **IR1 only**, with IR2/RGB/depth/pointcloud/alignment/combined IMU disabled, `unite_imu_method=0`. The explicit N3 bag has IR1 image, CameraInfo, raw gyro, raw accel, both IMUInfo topics, three depth-to-stream extrinsics and `/tf_static` (ten topic entries). Sensor observer QoS is best-effort/volatile; static TF is reliable/transient-local. Actual names/types/parameters must match pinned version and live readback; proposed names are not measured graph evidence.

The brief's stereo-inertial goal requires a separately reviewed IR2 extension, paired lossless image coverage, stereo calibration/rectification, updated explicit topics and doubled-image storage/load tests. This is PLANNED and cannot be smuggled into N2. The existing IR1/BMI085 candidate YAML and mono-inertial adapter design are review artifacts, not runnable qualified stereo inputs. Preserve raw originals; derived format/API/node changes require approval.

### Calibration, settings and algorithm notes

Preserve verbatim SDK warning: “IMU Calibration is not available, default intrinsic and extrinsic will be used.” Historical C reports CAD extrinsics, identity sensitivity/zero bias and zero noise arrays: defaults/placeholders, not measured alignment or zero noise. Camera image calibration is separate. Firmware, SDK/ASIC/update/USB identifiers are separate fields even if values coincide. SDK times are milliseconds; retain originals before conversion. Global time being enabled does not establish exposure-to-motion offset.

Settings details belong in page 44 notes: new-format `File.version`, `Camera.type`, camera intrinsics/distortion, dimensions/fps/RGB order, `Stereo.b`/`Stereo.ThDepth` or the selected EuRoC rectification path, `IMU.T_b_c1`, `IMU.Frequency`, four noise/walk fields and `IMU.InsertKFsWhenLost`, ORB feature count/pyramid/FAST thresholds and viewer settings. Follow actual pinned parser path; do not mix legacy/new fields. `T_b_c1` maps camera into estimator IMU/body, not robot body or the opposite direction suggested by one example comment. Test inverse/composition on basis vectors. Continuous-time noise is discretized in tracking using input frequency; do not pre-discretize twice.

Tracking consumes stereo images and image-bounded IMU intervals. Local mapping handles keyframes/optimization; loop closing handles revisiting/merging, with additional optimization work where applicable; Atlas is multi-map state, not a process. Inertial initialization needs motion and valid timing/calibration; do not transfer monocular scale language blindly to stereo. A wrapper adds its own queues/pairing/executor behavior and can fail independently of upstream.

### Evaluation notes for pages 69–78

Define estimated P_i and reference Q_i as poses in consistent conventions and S as chosen alignment. ATE: E_i = Q_i^-1 S P_i, with translation root mean square error over associated samples. RPE: E_ij = (Q_i^-1 Q_j)^-1 (P_i^-1 P_j), with declared time/distance delta and translation/rotation summaries. Report association tolerance, rejected samples, valid overlap/coverage and reference limitations. Rigid six-degree-of-freedom alignment is the recommended metric stereo-inertial default; optional seven-degree-of-freedom scale alignment is explicitly diagnostic and can conceal scale error. No ground truth means no measured D435i ATE/RPE, regardless of smooth output.

Planned evo command family: `evo_ape tum REFERENCE.tum ESTIMATE.tum --align` after a verified coordinate/timestamp conversion, with `evo_rpe` using explicitly reviewed delta/options; log complete options/version and raw outputs. Do not assume ORB EuRoC exports already have TUM column order. Processing latency is same-clock end−start; receipt-to-output is a separate interval; capture-to-output requires a qualified clock mapping and uncertainty. Percentiles are over named eligible samples with counts/exclusions. ROS headers and bag storage time remain separate. Queue depth, drop counters and latency unavailable from a backend remain UNKNOWN rather than zero. Resource samples are observations, not direct electrical power measurements.

### Decision notes for pages 80–83

| Decision | Recommended PLANNED default | Trade-off / evidence that changes it |
|---|---|---|
| Native vs Docker | Native Pi baseline. | Container packaging adds UID/GID/device/version boundaries; revisit with identical physical qualification and demonstrated deployment benefit. |
| USB topology | Known-good direct USB-A↔USB-C into Pi USB3, strain relief. | Connector shape is insufficient; shared-storage/hub alternative must prove own-branch ≥5000M, power and sustained stability. |
| ROS vs non-ROS estimator | Upstream EuRoC then controlled offline path before ROS wrapper/live. | Wrapper gives integration but adds queues/association; prefer it only after matched-data comparison identifies equivalent behavior. |
| Resolution/frame rate | Keep exact accepted IR1 640×480/15; stereo extension begins at matching profiles as a reviewed candidate. | Higher rate/resolution trades features/blur against bandwidth/CPU; change only with paired quality/tail/resource evidence, never relax N2. |
| Emitter | Preserve accepted baseline option state; separate PLANNED emitter-off trial for natural-feature stereo SLAM. | Projected texture may differ from stable scene features; compare matching/tracking under controlled lighting before choosing final stereo setting. |
| Global time | Preserve baseline readback, log domains and conversions; no silent stamp correction. | Separate off/on diagnostic if mapping jumps/drift or physical alignment evidence demands it. |
| Calibration tooling | Kalibr candidate for camera–IMU spatial/time estimation plus measured IMU noise; imu_utils is a noise option. | Tool/bag/build/model compatibility and residual/holdout evidence decide; no copied noise or assumed zero offset. |
| Wheel odometry | Defer fusion until visual-inertial baseline is qualified. | Add only when synchronized encoders, frame/extrinsic model and slip evidence address a measured failure mode. |
| Pi→STM32 transport/rate | No fixed wire design; candidate bounded pose/velocity/health envelope with measured output cadence. | Receiver budget, link error/load and freshness measurements select transport/rate/thresholds before coding. |

N6/N7 candidate envelope: version/session/sequence, reference/child frame, source stamp/domain, validity/tracking/reset flags, pose/velocity when valid, uncertainty only if justified, and timing metadata needed for receiver age. Proposed publication rate is tied to observed useful estimator output and receiver capacity; heartbeat may be separate, with no invented Hz or stale timeout. A Linux receipt timestamp alone cannot justify source freshness on the microcontroller clock. Frame reset/correction requires explicit invalidation/re-establishment. STM32 keeps local body IMU/control/watchdog/motor limits; perception absence removes optional autonomy inputs according to reviewed policy, never controller ownership.

### Agent-ticket notes for page 67

For each gate: one question, exact allowed files/host/actions, fixture/manual commands, expected evidence, negative cases and STOP condition. N0 inventory ticket produces platform facts; N1 ticket diagnoses one own-branch/access failure; N2 ticket recomputes sealed timing/content without altering thresholds; N3 ticket checks readback/context/replay; N4 ticket isolates settings/association or a fixed-data run; N5 ticket derives metrics from preserved runs; N6 ticket implements reviewed offline state fixtures; N7 ticket documents approved boundary tests. Agents may prepare modular tooling and propose changes. Owner retains gate acceptance, physical attestations, architecture/API/format approval, supply/calibration judgments, firmware/motor authorization and safety decisions. Do not delegate blanket environment reinstalls, guessed calibration constants or fabricated manual review.

## Phase 1 validation and limitations

A read-only Python structural check passed: 89 consecutive physical pages, twelve P01–P12 prompt headings and matching page mappings, twelve fenced individual prompts plus two setup blocks, seven schedule lines, preserved USB/profile/timing/300-second requirements, and no Phase 2 files created. `git diff --check` passed. Final Git status retains the initial unrelated changes; only the three requested Phase 1 documents were written. No TeX build or rendered-page inspection was performed because this phase contains no frames. Prompt wording is reviewed; generated-image appearance is not verified until images arrive. External fetch limitations and official source fallbacks are recorded above.

Manual review: compare the page plan with B's required topics; compare gate details with G; verify every P-id's unique subject/page against BATCH.md. Phase 2 reproduction commands and ordered steps are in SCHEDULE.md. This specification does not certify hardware, dataset availability, calibration, build dependencies, timing budgets or robot safety.

Abbreviation authoring notes: on page 40 define Oriented FAST and Rotated BRIEF (ORB), Features from Accelerated Segment Test (FAST), and Binary Robust Independent Elementary Features (BRIEF) in natural inline language and speaker notes without shrinking the slide. On first relevant use expand Yet Another Markup Language (YAML), Application Programming Interface (API), First-In First-Out (FIFO), Software Development Kit (SDK), Universally Unique Identifier (UUID), and root mean square error (RMSE). Use full words for operating system and ground truth rather than introducing extra abbreviations. Literal field/topic/tool names remain exact. Code identifiers and required profile format tokens such as Y8 are explained where introduced rather than treated as prose abbreviations.

Frame notes for pages 26–28: body axes x forward/y left/z up; optical axes z forward/x right/y down, right-handed. Map corrections may jump; odom must remain continuous if published with REP-105 semantics. Assign exactly one TF publisher/parent per child. A direct jumping ORB map pose cannot simply be relabeled odom. `body` and `base_link` relationship, camera mount and actual wrapper frame names are PLANNED and require geometry evidence; estimator body means camera IMU, not STM32 robot body. `world` is an explicitly defined optional reference, not automatically an additional parent. Camera left/right optical frames need explicit conventions under their selected stream frames.
