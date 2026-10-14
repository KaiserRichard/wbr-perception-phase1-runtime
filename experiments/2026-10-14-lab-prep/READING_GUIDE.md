# This afternoon: prepare for the 15 October lab

Spend **180 minutes**, in this order. The goal is to explain the data path and recognize a failed take before spending time on the estimator. Reading times are a suggested schedule, not experiment measurements.

Visual-inertial odometry (VIO) combines images with an inertial measurement unit (IMU). Simultaneous localization and mapping (SLAM) also recognizes revisited places and corrects the map. Tomorrow uses the camera IMU; STM32H7 keeps responsibility for balance and actuator safety.

```text
D435i stereo + IMU → local Pi recorder → RAM recording → saved take
                                                          ↓
                         same take + settings → offline ORB-SLAM3 → plot
                                                          ↓ review
                         camera + same settings → live ORB-SLAM3
```

## 1. Understand the current situation — 15 minutes

Read [session facts](../2026-10-13-SESSION_FACTS_FOR_SLIDES.md), sections D–F, then the entire [14 October addendum](../2026-10-14-SESSION_FACTS_ADDENDUM.md). Finish with the checklist in [tomorrow's runbook](LAB_RUNBOOK_2026-10-15.md).

Remember four things: the EuRoC baseline worked; the first long camera take had gaps; a short RAM take removed those gaps; replay crashed and needs the patch-4 rebuild. The 8 GB board did not fix under-voltage. A complete 100-second RAM take and successful patched replay are **unverified**.

The addendum supersedes older operating details. Some slides still say “never camera-run,” show the 4 GB stand-in, or imply the card is suitable for recording. Read those as an earlier snapshot.

## 2. Learn only the slides needed tomorrow — 45 minutes

Open `slides_course/main.pdf`. These are **PDF page numbers**, checked locally against the 91-page PDF on 14 October. Titles are the stable reference if the other thread rebuilds it. Follow the diagrams and takeaways; skip equations and numeric settings tables today.

| Time | Essential pages and exact frame titles | What to understand |
|---|---|---|
| 7 min | **6** “2.1 Stereo geometry”; **7** “2.2 Visual-inertial estimation”; **8** “2.3 Odometry and mapping”; **9** “2.4 D435i streams” | Two images constrain depth; inertial propagation bridges images; map correction differs from local motion. |
| 6 min | **12** “3.1 Machine ownership”; **13** “3.2 Control boundary”; **17** “3.6 Queues and backpressure”; **18** “3.8 Storage qualification” | Acquisition stays on the Pi. A blocked recorder can lose input. RAM removes card writes from acquisition. |
| 8 min | **23** “3.14 Transform direction”; **24** “3.15 Timestamp fields and domains”; **25** “3.16 Where timestamps are stamped”; **26** “3.17 Global time” | Coordinate direction and clock domain matter even when units look right. |
| 5 min | **28** “3.19 Calibration register”; **29** “3.20 Stereo calibration”; **38** “3.29 Input association” | Factory geometry and assumed noise are provisional. Acceleration is interpolated between valid samples at gyro times. |
| 9 min | **32** “3.24 Algorithm threads”; **33** “3.25 Tracking”; **34** “3.26 Mapping and Atlas”; **35** “3.27 Inertial initialization” | Tracking estimates each pose; selected keyframes support mapping; Atlas manages maps; initialization needs motion. |
| 10 min | **42** “4.1 Gate dependencies and status”; **49** “4.4 N2: reproduction and mandatory soak”; **50** “4.5 N2: delivery criteria”; **59** “4.9 N4A: camera-independent EuRoC baseline”; **61** “4.10 N4B: offline D435i stereo”; **64** “4.11 N4C: live stereo scheduling”; **73** “4.16 Bottom-up diagnosis” | Qualification precedes estimation. Offline replay isolates input/estimator defects before live scheduling. Read pages 61/64 with the addendum. |

**Skippable for tomorrow:** pages **1–5, 10–11, 14–16, 19–22, 27, 30–31, 36–37, 39–41, 43–48, 51–58, 60, 62–63, 65–72, 74–91**. These contain broader integration, detailed acceptance contracts, calibration campaigns, evaluation mathematics and historical reporting. “Skippable” applies to afternoon study; the lab prerequisites still apply. Pages 80–82 are optional if you want the baseline results presentation.

## 3. Read the local operating instructions — 35 minutes

| Time | Read these sections, in order | Why / what to skim |
|---|---|---|
| 4 min | [DECISIONS](../../docs/DECISIONS.md): ADR-001 through ADR-004; [ARCHITECTURE](../../docs/ARCHITECTURE.md): “Responsibility boundary,” “Sensor ownership,” “Timestamp chain” | Know which IMU is used and what the Pi owns. Skim the long frame-name list. |
| 5 min | [NEXT_GATE](../../docs/NEXT_GATE.md): “Status,” “Current uncertainty,” “Do not,” “Candidate PASS criteria”; [RPI5_NATIVE_PERCEPTION_BRINGUP](../../docs/RPI5_NATIVE_PERCEPTION_BRINGUP.md): §8 “Sensor gate,” §9 “Rosbag gate” | N3 remains OPEN; a direct software development demo does not promote it. Skim old installation instructions. |
| 5 min | [N4B preparation README](../2026-10-13-n4b-d435i-prep/README.md), then [n4b_plan](../2026-10-13-n4b-d435i-prep/n4b_plan.md): “Shortest credible sequence” and “One input path and exact profiles” | Know the two binaries and flags. The 30 Hz stereo take is separate from the 15 Hz raw qualification. |
| 8 min | Same plan: “Hand motion for initialization,” “Future N4B and N4C commands and observations,” “Frames and timestamps: measured versus unknown” | Rehearse the motion recipe and log review. Skim the long build recipe; the installed bundle already exists. Use the addendum's RAM and `.db3` updates. |
| 6 min | [calibration_notes](../2026-10-13-n4b-d435i-prep/calibration_notes.md): opening status, “Transform direction and math,” assumptions in “Upstream versus candidate”; [D435I_VIO_CALIBRATION_READINESS](../../docs/D435I_VIO_CALIBRATION_READINESS.md): “Meaning of the warning,” “Timestamp investigation still required” | Understand camera-to-IMU geometry and why enabled global time does not prove synchronization. Skim matrix arithmetic. Readiness contains **old-unit evidence**; do not transfer its serial or measurements. |
| 7 min | [N4A REPORT](../2026-10-13-n4a-euroc-mh01/REPORT.md): “Results,” “Not verified / limits”; [log triage](../2026-10-14-d435i-demo/DEBUG_GUIDE.md): the five symptom rows | The baseline validates this build on known data, not D435i accuracy or live speed. Debug input before tuning features. Skim raw numbers and source line references. |

## 4. Read the external explanations selectively — 70 minutes

No external page was fetched for this ticket. Titles already cited locally are retained; uncertain external headings are marked below. Use saved copies if available. Do not turn this study session into an installation or calibration session.

| Time | Must-read title / selection | Why it matters tomorrow; what to skim |
|---|---|---|
| 15 min | **“Visual-Inertial Odometry of Aerial Robots”**, Zhang and Scaramuzza — **title unverified offline**; beginner explanation | Focus on image constraints, inertial propagation, gravity and biases, and why the two sensors complement each other. Skim derivations, aerial-control material and comparisons of algorithms. Relate it to course pages 6–8. |
| 25 min | Campos et al. (2021), **“ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual–Inertial, and Multimap SLAM”** | Read the system overview diagram, the visual-inertial initialization subsection, and the Atlas/multi-map discussion. Initialization explains the early motion; Atlas explains why repeated map creation matters. Skim cost functions, optimization derivations and benchmark tables. Exact subsection numbering is **unverified offline**; locate by topic. |
| 15 min | Intel, **“Intel RealSense Depth Camera D435i IMU Calibration”**; D435i IMU documentation (“D435i” heading **unverified offline**); **“IMU Calibration Tool”** heading **unverified offline** | Read what gyro/accel supply, what IMU intrinsic calibration estimates, and the distinction between calibration and runtime bias estimation. Skim procedure screenshots and commands. Understand that the tool can write device calibration; tomorrow's room take is not that procedure. Older IMU-model descriptions need checking against this unit's BMI085. |
| 5 min | RealSense global-time documentation (“Global time” heading **unverified offline**); exact source reference **`global_timestamp_reader.cpp`**, librealsense v2.58.4 | Read the device-to-host clock mapping explanation. The precise source filename is cited in the local readiness doc; skim implementation details. Preserve current settings tomorrow and inspect recorded domains. Global time is not a measured camera–IMU exposure offset. |
| 10 min | Burri et al. (2016), **“The EuRoC micro aerial vehicle datasets”** | Read the sensor suite, calibration/synchronization description and ground-truth limitations. Skim flight apparatus and unrelated sequences. MH01 provides a known reference; tomorrow's room loop has no ground truth. |

The paper and Intel white-paper titles come from the course/report references and `docs/D435I_CALIBRATION_PLAN.md` references R5–R6. External suggestions are reading targets, not new evidence about the installed hardware.

## 5. Teach it back and rehearse — 15 minutes

Read the runbook once more. Answer these without looking; then check the short answers.

1. **Why switch the infrared emitter off?** Its projected dots move with the camera and can become misleading visual features. Use texture fixed in the room.
2. **Why move early if stereo already gives scale?** Inertial initialization still needs gravity, velocity and bias estimates. Translation and varied rotations provide useful excitation; stereo depth alone does not.
3. **What motion should I use?** Start smooth translation within 1–2 seconds, excite all axes for 20–30 seconds, make a small loop, revisit the initial view and finish still.
4. **Why record into RAM?** The long card-recorded take had large gaps; the short RAM test avoided them. Copy and verify after acquisition. A long RAM take is still unverified.
5. **What do `--bag` and `--no-viewer` mean?** Replay a saved take without real-time pacing; disable the graphical viewer. Omit `--bag` for live input.
6. **Does a plausible loop plot prove accuracy?** No. It shows estimated motion. Absolute Trajectory Error (ATE) needs a reference trajectory; the room take has none.
7. **Does global time prove synchronized camera and IMU exposure?** No. It maps clocks toward host time; physical camera–IMU offset remains unknown.
8. **Why is raw acceleration 100 Hz but estimator input 200 Hz?** Gyro times define the input grid; acceleration is interpolated only within valid brackets. No extra raw measurements are created.
9. **What do a new map and the calibration warning mean?** One startup map is normal; repeated new IDs need diagnosis. The warning means calibration is unavailable/defaulted, not that the exact failure cause is known. Preserve it.
10. **What did EuRoC establish, and what remains OPEN?** This native build produced accurate estimates on MH01. D435i calibration/timing, stable-power performance and gate qualification remain OPEN; old-camera evidence does not transfer.

Preparation provenance: only the ticket's local source set was read, plus the specifically requested command/triage helpers and the course PDF for page indexing. Validation was document/source consistency and local PDF text extraction only. No network, SSH, camera, ORB execution, installation or Git mutation was performed.
