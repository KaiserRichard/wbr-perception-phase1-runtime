# J1 — Software component inventory

Research snapshot: **2026-10-14**. **INFERRED recommendation:** build a shared, provenance-preserving input/evaluation foundation, then an ORB-SLAM3 adapter; defer other engine adapters until R1's measured switch trigger occurs. This inventory implements no architecture or public contract. It builds on [R1][R1], [R2][R2] and [R3][R3], without repeating their algorithm comparison, wire-contract design or lab plan.

Labels apply to the claims in their paragraph/table cell: **SOURCE-SUPPORTED** = inspected primary source; **MEASURED** = cited repository evidence (including inspected code, not necessarily executed behavior); **INFERRED** = engineering recommendation; **ASSUMED** = declared premise; **UNKNOWN** = unverified. Upstream default branches are mutable; pin revisions before implementation. `S` means `/Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime`; paths below are relative to S. `P` means `experiments/2026-10-13-n4b-d435i-prep`; `Q` means `experiments/2026-09-12-pi5-native-sensor-validation`.

**MEASURED:** [13 October facts][F13] and [14 October addendum][F14] establish native recording, a patched driver, EuRoC accuracy and a clean 15-second RAM take. They do not establish successful post-fix D435i replay: the null-pointer fix rebuild was interrupted. Live calibrated VIO remains OPEN; nominal geometry and assumed noise are not calibration. `docs/PROJECT_STATE.md` and `docs/NEXT_GATE.md` remain stale/draft. Target: Pi 5 **8 GB**, Ubuntu 24.04/Jazzy; STM32H7 retains balance/LQR/VMC/FSM/motor safety if Pi/ROS fails. Camera and body IMUs remain separate [ADR-001/002][ADR]. R1b's independent report was absent from the inspected research directory.

## C0. Artifact manifest and clock mapping — shared foundation

**INFERRED:** add a small manifest/validation layer, not a new storage engine: immutable raw hashes; SDK/build/engine revisions; device identities; profiles; calibration/settings/converter hashes; raw and mapped stamp domains; mapping uncertainty; interpolation/rejection counts; reset/frame epochs. Latency uses host monotonic time. Device-to-Pi and Pi-to-MCU mappings are distinct, versioned relations; UTC is log context. This component is engine-agnostic and needed for attributable replay and usable source age. **MEASURED:** audit columns exist in [P/d435i_rs.h][RS]; trajectory hashes/CLI provenance exist in [trajectory evaluator][TE]; no complete cross-component manifest/mapping service was found. **UNKNOWN:** real clock drift/asymmetry requires device/link measurements. Minimal hardware-free proof: inject offset, drift, wrap, clock step and reboot; mappings invalidate on session change, uncertainty grows with delayed/asymmetric exchanges, and cross-domain subtraction is rejected. Reconsider implementation if an existing audited synchronization service supplies these exact relations.

## C1. Recording, replay and conversion

**SOURCE-SUPPORTED correction:** “rosbag2 since librealsense 2.56” is not defensible. [v2.56.5 ros_writer.cpp, lines 22–29][OLD] opens a ROS 1 `rosbag::Bag`; current [ros2_writer.cpp, lines 30–70][NEW] selects SQLite storage and CDR. Its bundled [sqlite_storage.cpp, lines 196–212][SQL] creates `topics(id,name,type,serialization_format,offered_qos_profiles)` and `messages(id,topic_id,timestamp,data)` plus a timestamp index. The writer uses standard Image/Imu type names, separate gyro/accel fields, and separate metadata carrying original SDK stamps/domains [NEW]. Its message stamp is derived from the writer's timestamp argument; do not assume that is the original device epoch. **UNKNOWN:** first released migration version and actual Pi file schema/compression were not established here. The `.db3` filename/comment in [recorder][REC] is insufficient; inspect file magic, tables, topic types, CDR decoding and original metadata before choosing a reader. [Upstream documentation][RSDOC] warns compressed recordings are SDK-only.

**INFERRED recommendation:** retain native SDK replay for the existing ORB diagnostic; create one audited exporter yielding a EuRoC ASL-style `mav0/cam{0,1}/data/*.png`, per-camera `data.csv`, `imu0/data.csv` and calibration/provenance. Preserve integer nanoseconds, lossless pixels and original separate IMU streams; create combined IMU only as a declared derivative.

| Destination | Existing upstream coverage — SOURCE-SUPPORTED | Required glue — INFERRED |
|---|---|---|
| EuRoC ASL sensor folder | [rs-convert][RSC] exports PNG/raw/CSV; it also offers legacy bag→db3. | No inspected tool proves a complete SDK→ASL export. Assemble layout, original-time recovery, camera pairing, combined IMU and manifest; compare all counts/pixel hashes. |
| TUM trajectory | ORB [System.h][OS] exposes trajectory exports; local evaluator accepts TUM/ORB/EuRoC GT [TE]. | TUM trajectory is estimator output, not a stereo/IMU recording replacement. Declare camera versus IMU pose, seconds and quaternion order. |
| Standard ROS 2 sensor bag | [rosbags readers/writers][RR] and [conversion][RB] cover bag I/O; current SDK writer uses Image/Imu [NEW]. | Normalize topic names, capture stamps, frame IDs, CameraInfo/TF and a combined Imu topic. Standard type names alone do not establish VIO-ready semantics or Jazzy replay compatibility. |
| ROS 1 bag for Kalibr | [rosbags-convert][RB] covers ROS 2→ROS 1; [kalibr_bagcreater/bagextractor][KB] cover image folders/IMU CSV↔ROS 1 bag. | Convert the normalized uncompressed standard bag, or arrange Kalibr's own folder layout then reuse bagcreater. It differs from ASL (`cam0/*.png`, `imu0.csv`). Never treat SDK partial Imu fields as complete samples. |

**MEASURED:** [Q/n3_bag.py][NB] already inspects/replays finalized ROS bags with metadata and expected topics; it is not a native SDK importer. **INFERRED:** reuse maintained readers/serializers first; write only missing semantics/layout glue. Change this choice if an upstream importer demonstrates exact stamps, metadata and pixel equivalence on the actual retained recording.

## C2. Input association and timestamp validation

**MEASURED:** [d435i_input.h][IN] is SDK/ORB-independent C++ interpolation/order logic: finite checks, strictly increasing per-stream stamps, 50-ms development gap guard, bounded queues, accel brackets and no extrapolation. Its `take(t)` consumes through the first gyro at/after the image, explicitly relying on ORB's endpoint retention. Stereo pairing, ≤1-ms skew, image ordering and a single unchanging SDK domain are in the [driver patch][PATCH], not this header. The 50-ms guard does not replace N2 timing limits.

**SOURCE-SUPPORTED:** librealsense distinguishes hardware clock, OS system time and hardware time converted to OS global time [rs_frame.h][RF]. [global_timestamp_reader.cpp][GT] returns GLOBAL_TIME only when enabled and its mapping is ready, otherwise the original domain. **INFERRED:** audit transitions; a global-time option readback does not prove every frame is mapped or that physical camera–IMU offset is zero.

**INFERRED recommendation:** reuse interpolation/validation, but split combined-sample production from ORB interval extraction. Preserve raw samples and record prefix/tail exclusions; after calibrated time shift, recheck image/IMU coverage. **SOURCE-SUPPORTED:** ORB consumes synchronized rectified stereo plus a per-frame IMU vector [OS]; OpenVINS has per-sample `feed_measurement_imu` and grouped `feed_measurement_camera` [OV]; VINS has `inputIMU`/`inputImage` and also a ROS-facing implementation [VH]. Basalt feeds images to optical flow and combined per-sample IMU into the estimator; optical flow supplies its vision queue [vio.cpp][BF], [interface][BH]. Thus reuse is **partly**, not a drop-in header for every engine. Evidence to change: selected engine boundary tests prove identical endpoint ownership, scheduling and time conventions.

## C3. Calibration import and engine settings

**SOURCE-SUPPORTED:** Kalibr defines `T_cam_imu` as IMU→camera and `t_imu=t_cam+timeshift_cam_imu`; stereo `T_cn_cnm1` maps the preceding camera into the next [KY]. Its noise densities are continuous; sampled white-noise std is density/√Δt, bias increments scale with √Δt [KN]. **INFERRED:** define `T_A_B` as B→A, invert analytically, never just negate translation, and prevent double application of time/noise conversions.

| Engine | SOURCE-SUPPORTED settings/conventions | INFERRED minimum work / UNKNOWNs |
|---|---|---|
| ORB-SLAM3 | [EuRoC settings][OY] use camera→IMU `IMU.T_b_c1` (older parser uses `Tbc`), camera models and stereo geometry. [Tracking.cc][OT] multiplies density by √frequency and divides random walk by √frequency. | Export inverse Kalibr transform into the selected settings dialect; reverse stereo transform where required; use correct delivered/rectified intrinsics. Apply image time shift in the adapter once; inspected settings have no Kalibr shift field. Do not discretize noise twice. |
| OpenVINS | [YamlParser][OP] accepts either `T_imu_cam` or `T_cam_imu` and inverts as needed. [VioManagerOptions][OO] reads cam0 timeshift and Kalibr noise fields. | Reuse upstream parser, adding OpenCV YAML syntax, nested `imu0` noise configuration and estimator options as needed. Validate models and reject incompatible per-camera time shifts: loader only takes cam0's offset. No new mathematical converter required. |
| VINS-Fusion | [Config][VY]/[parameters.cpp][VP] use camera→body `body_T_cam0/1`; `td` adds to image time. Config labels noise as measurement/bias std; [integration_base.h][VI] squares those values directly. | Invert extrinsics, emit separate supported camera-model files and set `td` once. UNKNOWN: a universal Kalibr-density mapping is not proven by these field names; derive/test sampled-noise propagation against the selected implementation before use. |
| Basalt | [Calibration header][BC] has camera→IMU `T_i_c`, ns camera offset and continuous noise with internal sampling conversion. [Calibration workflow][BD] writes `calibration.json`. | Prefer its supported calibration workflow if evaluating Basalt. Otherwise write a version-pinned serializer/model mapping. UNKNOWN: offset sign at the selected dataset consumer and complete distortion/serialization compatibility; do not infer these from a field name. |

**UNKNOWN:** no maintained universal Kalibr→ORB/VINS/Basalt converter was verified in this search; absence is not established globally. **INFERRED recommendation:** one validated calibration record plus ORB exporter now; use OpenVINS native loading if fallback is needed. Change only when a maintained converter passes nonidentity rotation/translation, shifted-motion, model-rejection and noise-unit fixtures. Hardware-free import tests prove conventions, not calibrated values; lab captures/held-out residuals still block N4B [R1 §4][R1].

## C4. Estimator adapter and state/health capabilities

**INFERRED recommendation:** a thin asynchronous interface: feed timestamped IMU/stereo; obtain immutable `Estimate` containing source epoch/domain, reference/child frame, pose, optional velocity/covariance with availability, initialization/state/reasons, reset counter and frame/map epoch; request reset and observe completion. Serialize access and copy snapshots; never expose engine pointers downstream. Common API is reusable; engines' output semantics are not.

| Engine | Actual SOURCE-SUPPORTED exposure | INFERRED adapter responsibility |
|---|---|---|
| ORB | [System.h][OS]: tracking state, tracked points, reset/active-map reset, `MapChanged()` for big changes. [Map.h][OM]: ID, IMU initialization, `GetLastBigChangeIdx`; [Atlas.h][OA]: current map, count, creation/switch, IMU initialization. Atlas pointer is private in System.h. | Add reviewed locked snapshot access if necessary; do not assume a public Atlas getter. MapChanged is not a full reset/epoch event log. Count owned resets and observe internal map transitions; unsupported covariance/velocity remain unavailable. |
| OpenVINS | [VioManager.h][OV]: initialized flag/time, state and feature access. [StateHelper.h][OH]: covariance extraction. | Convert IMU state/JPL orientation and marginal covariance ordering/frame. Initialized alone does not establish fresh usable tracking. Own recreation/reset epochs; do not assume Atlas-like global recovery. |
| VINS | [estimator.h][VH]: INITIAL/NON_LINEAR state, poses/velocities/biases, clearState, failureDetection. **Critical:** inspected [estimator.cpp lines 896–899][VE] immediately returns false from failureDetection. | Add freshness/numerical/feature health observation; method presence is no failure guarantee. Expose synchronized state/reset events; do not substitute preintegration covariance for estimator pose covariance. |
| Basalt | [VioEstimatorBase][BH]: pose/velocity/bias output queue, last processed stamp, finished flag; initialization entry points. | Normalize output and frontend errors/backlog; own lifecycle epochs. No equivalent public tracking-health enum or pose-covariance output is verified in this interface. |

**MEASURED:** the driver [PATCH] is an ORB-specific precursor, not this reusable boundary. **INFERRED change evidence:** expose further capabilities only after pinned-header/implementation audit and recorded loss/reset trials.

## C5. Pose output, body transform and TF ownership

**SOURCE-SUPPORTED:** REP-103 specifies SI/body forward-left-up and optical right-down-forward; REP-105 distinguishes continuous drifting `odom` from globally corrected/jumping `map` [REP-103][103], [REP-105][105]. ORB [System.cc][OC] returns tracker `Tcw`; inertial trajectory export uses an IMU/body pose. **INFERRED:** neither “body” label denotes the robot automatically. With E the engine sensor frame, `T_world_base=T_world_E × T_E_base`; invert ORB `Tcw` first. Transform covariance with the appropriate Jacobian, preserving lever-arm terms; velocity at the camera IMU is not necessarily velocity at base_link.

**INFERRED recommendation:** implement one shared frame/output bridge with engine-specific normalization in C4; follow [R1 §2][R1] ownership (local estimator owns odom→base_link, SLAM correction owns map→odom at the same epoch, mount/internal sensor geometry have distinct owners). Without a qualified continuous local estimator, publish diagnostic SLAM-world pose and defer odom. Relabeling loop-corrected ORB pose cannot supply continuity. **UNKNOWN:** final mount geometry/dynamic joint relation requires robot access. Change only on measured extrinsics and verified reset/loop continuity.

## C6. Health monitor and Pi→STM32 semantics

**INFERRED recommendation:** implement [R2 §1][R2]'s candidate state/validity contract, starting health-only; do not redesign its transport here. Engine-specific inputs are initialization, tracking-loss interpretation, covariance availability/ordering, velocity validity and map/reset/relocalization events. Engine-agnostic policy covers finite values, source age with mapping uncertainty, frame/calibration acceptance, queue/resource faults, sequence/session and lease invalidation. Fresh heartbeat with frozen estimate stays stale. Unknown covariance stays unavailable. Treat unknown reset observation as invalidity, not an unchanged epoch. **MEASURED:** system health sampler [Q/health_monitor.py][HM] exists; no complete estimator-health state machine/receiver harness was found, consistent with R2. **UNKNOWN:** accepted age/recovery budgets remain controller review items. Change policy on measured fault/recovery traces and approved budgets; STM32 fallback/balance authority remains local.

## C7. Profiling and bounded runtime

**SOURCE-SUPPORTED:** [ros2_tracing][TR] supplies ROS tracepoints; [perf][PF] samples CPU activity; [psutil][PS] exposes process/system metrics; [vcgencmd][VC] reports temp/clock/throttle flags, with current bits distinct from historical bits; SDK [frame metadata][RF] includes counters/exposure/sensor stamps. **INFERRED:** these suffice as collection primitives, not a complete latency monitor. Reuse [HM] and add frequency plus per-stage monotonic events (acquisition callback, association/queue, preprocessing, engine, output, encoding/send), queue depth/oldest age, drops and rejection causes. Native calls need explicit events; ROS traces cannot see all engine threads automatically. Aggregate P50/P95/P99/max with sample counts, warmup/eligibility and initialization/lost intervals; keep raw timelines and separate offline throughput from live age. **UNKNOWN:** Pi tails/throttling under sustained load need hardware. Change tooling only if its overhead or missing observability is measured.

## C8. Evaluation and repeatability

**MEASURED:** [tools/trajectory_eval/traj_eval.py][TE] already implements ATE/RPE, timestamp association, alignment, input hashes and batch aggregation; [demo plot][DP] adds path/stream/power diagnostics. **INFERRED recommendation:** reuse evaluator; write a dataset regression runner that freezes input/config/builds, launches repeated engine runs, captures exit/crash/initialization/reset/loss/coverage/resource events, and evaluates successful and failed trials without survivor selection. Reference-free checks: finite state, monotonic source sequence, stereo epipolar residuals, IMU coverage, stillness drift, return/checkpoint discrepancy and discontinuities. These are consistency tests, not ATE ground truth. Metric stereo-inertial comparison defaults SE(3); Sim(3) is diagnostic. Hardware-free known rigid transform/drift and frozen retained dataset repeats prove tooling; representative mounted-robot accuracy needs independent reference/lab access. Change runner only if existing upstream batch tooling reproduces the same provenance and failure denominator.

## C9. Link codec and receiver reference

**MEASURED:** [R2 §§1–2,5][R2] defines candidate UART/COBS/CRC/session/lease policy and explicitly says its synthetic harness does not exist. **INFERRED recommendation:** reuse audited COBS/CRC primitives once selected; write host encoder/decoder plus a portable bounded receiver policy reference and fault fixtures. Engine choice never enters byte framing; C4/C6 supply normalized semantics. Freeze exact widths/layout/endianness and policy revision before fixtures; maintain cross-language golden vectors. Hardware-free proof includes split/coalesced/truncated/oversized frames, corruption, NaN, duplicates/reordering/wrap, reboot/old epoch, clock uncertainty and frozen pose with healthy heartbeat; rejected packets never renew leases and parsing resynchronizes within fixed memory/work bounds. **UNKNOWN:** actual MCU UART/DMA load, motor EMI, watchdog/fallback and balance independence need N7 hardware; host tests cannot prove them. Change transport only on R2's measured failure triggers.

## Validation and source scope

**MEASURED:** authoring inspected the listed repository inputs, source code and primary web sources; only this file was written. Static checks verify local citation targets and required inventory/gate structure. No SSH, installs, camera, ORB, MCU execution or gate promotion occurred. Minimal tests below are future proving tests, not reported executions. **INFERRED:** the nine requested components plus C0 are sufficient for the stated milestone; mapping/navigation planners, wheel/body-IMU fusion and learned runtime policy remain separate later scope [R1][R1].

[R1]: ../../../wbr-perception-phase1-runtime/slides_roadmap/research/R1_algorithms.md
[R2]: ../../../wbr-perception-phase1-runtime/slides_roadmap/research/R2_integration.md
[R3]: ../../../wbr-perception-phase1-runtime/slides_roadmap/research/R3_plan.md
[F13]: ../../../wbr-perception-phase1-runtime/experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md
[F14]: ../../../wbr-perception-phase1-runtime/experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md
[ADR]: ../../../wbr-perception-phase1-runtime/docs/DECISIONS.md
[RS]: ../../../wbr-perception-phase1-runtime/experiments/2026-10-13-n4b-d435i-prep/d435i_rs.h
[REC]: ../../../wbr-perception-phase1-runtime/experiments/2026-10-13-n4b-d435i-prep/d435i_record.cpp
[IN]: ../../../wbr-perception-phase1-runtime/experiments/2026-10-13-n4b-d435i-prep/d435i_input.h
[PATCH]: ../../../wbr-perception-phase1-runtime/experiments/2026-10-13-n4b-d435i-prep/stereo_inertial_d435i_file.patch
[NB]: ../../../wbr-perception-phase1-runtime/experiments/2026-09-12-pi5-native-sensor-validation/n3_bag.py
[HM]: ../../../wbr-perception-phase1-runtime/experiments/2026-09-12-pi5-native-sensor-validation/health_monitor.py
[TE]: ../../../wbr-perception-phase1-runtime/tools/trajectory_eval/traj_eval.py
[DP]: ../../../wbr-perception-phase1-runtime/experiments/2026-10-14-d435i-demo/plot_run.py
[OLD]: https://github.com/realsenseai/librealsense/blob/v2.56.5/src/media/ros/ros_writer.cpp#L22-L29
[NEW]: https://github.com/realsenseai/librealsense/blob/master/src/media/ros2/ros2_writer.cpp#L30-L187
[SQL]: https://github.com/realsenseai/librealsense/blob/master/third-party/realsense-file/rosbag2/rosbag2_storage_default_plugins/src/rosbag2_storage_default_plugins/sqlite/sqlite_storage.cpp#L196-L212
[RSDOC]: https://github.com/realsenseai/librealsense/blob/master/doc/record-and-playback.md
[RSC]: https://github.com/realsenseai/librealsense/blob/master/tools/convert/rs-convert.cpp
[RB]: https://ternaris.gitlab.io/rosbags/topics/convert.html
[RR]: https://ternaris.gitlab.io/rosbags/topics/rosbag2.html
[KB]: https://github.com/ethz-asl/kalibr/wiki/bag-format
[RF]: https://github.com/realsenseai/librealsense/blob/master/include/librealsense2/h/rs_frame.h#L15-L30
[GT]: https://github.com/realsenseai/librealsense/blob/master/src/global_timestamp_reader.cpp#L517-L520
[KY]: https://github.com/ethz-asl/kalibr/wiki/yaml-formats
[KN]: https://github.com/ethz-asl/kalibr/wiki/IMU-Noise-Model
[OS]: https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/master/include/System.h#L99-L167
[OY]: https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/master/Examples/Stereo-Inertial/EuRoC.yaml#L50-L72
[OT]: https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/master/src/Tracking.cc#L547-L558
[OM]: https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/master/include/Map.h#L75-L108
[OA]: https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/master/include/Atlas.h#L73-L116
[OC]: https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/master/src/System.cc
[OV]: https://github.com/rpng/open_vins/blob/master/ov_msckf/src/core/VioManager.h#L66-L99
[OP]: https://github.com/rpng/open_vins/blob/master/ov_core/src/utils/opencv_yaml_parse.h#L453-L494
[OO]: https://github.com/rpng/open_vins/blob/master/ov_msckf/src/core/VioManagerOptions.h#L144-L258
[OH]: https://github.com/rpng/open_vins/blob/master/ov_msckf/src/state/StateHelper.h
[VH]: https://github.com/HKUST-Aerial-Robotics/VINS-Fusion/blob/master/vins_estimator/src/estimator/estimator.h
[VE]: https://github.com/HKUST-Aerial-Robotics/VINS-Fusion/blob/master/vins_estimator/src/estimator/estimator.cpp#L896-L899
[VY]: https://github.com/HKUST-Aerial-Robotics/VINS-Fusion/blob/master/config/euroc/euroc_stereo_imu_config.yaml
[VP]: https://github.com/HKUST-Aerial-Robotics/VINS-Fusion/blob/master/vins_estimator/src/estimator/parameters.cpp
[VI]: https://github.com/HKUST-Aerial-Robotics/VINS-Fusion/blob/master/vins_estimator/src/factor/integration_base.h#L23-L32
[BH]: https://github.com/VladyslavUsenko/basalt/blob/master/include/basalt/vi_estimator/vio_estimator.h#L56-L111
[BF]: https://github.com/VladyslavUsenko/basalt/blob/master/src/vio.cpp#L152-L195
[BC]: https://vladyslavusenko.gitlab.io/basalt-headers/calibration_8hpp_source.html
[BD]: https://github.com/VladyslavUsenko/basalt/blob/master/doc/Calibration.md
[103]: https://github.com/ros-infrastructure/rep/blob/master/rep-0103.rst
[105]: https://github.com/ros-infrastructure/rep/blob/master/rep-0105.rst
[TR]: https://github.com/ros2/ros2_tracing
[PF]: https://perfwiki.github.io/main/tutorial/
[PS]: https://psutil.io/
[VC]: https://www.raspberrypi.com/documentation/computers/os.html#get_throttled

## Inventory and gate dependencies

**INFERRED inventory classification/build order; MEASURED repository availability; SOURCE-SUPPORTED upstream coverage is linked above.** “Lab” describes qualification, not code-writing access. All minimal tests are hardware-free and prove software behavior only. Gates retain [R1/R2][R1]'s meanings: N3 ROS sensor record/replay; N4A known dataset, N4B D435i offline, N4C live; N5 measurement; N6 health semantics; N7 controller/robot integration. Stable power/storage and fresh N1→N2 remain external prerequisites; stereo/30 is a separately qualified extension, not replacement of IR1/15 or the mandatory 300-second N2 soak.

| Component / purpose | Engine-agnostic? Why | Exists / reuse / must write | Lab needed for qualification | Minimal proving test | Blocks gates |
|---|---|---|---|---|---|
| C0 provenance/clocks | Yes: identity/time across boundaries | RS/TE fragments; write manifest/mapping validators | Camera/Pi/link clocks | Offset/drift/wrap/reboot fixture; forbid mixed clocks | N3–N7 |
| C1 retain/decode/replay/convert | Yes: raw sensors; exports declare engine frames | REC, NB; reuse SDK/rosbags/Kalibr; write normalization/ASL glue | Storage/camera ROS pipeline | Tiny stereo+separate-IMU recording; magic/schema/CDR, exact counts/ns/pixels round trip; compressed input takes SDK path | N3, N4B/C, N5 |
| C2 associate/validate | Partly: validation/interpolation shared; batching engine-specific | IN, PATCH, P/analyze_take.py; extract shared sample feed | Physical skew/gaps/domains | Existing P/test_d435i_input.cpp plus skew/domain/tail and engine-endpoint fixtures | N3 input audit; N4B/C, N5 |
| C3 settings/calibration | Partly: calibration math shared; schema/models/noise differ | Candidate P/D435i_317422076650_stereo_inertial.yaml; reuse OpenVINS parser/Basalt tools; write ORB exporter | Current unit target/motion/noise captures | Nonidentity transform round trip; time-shift sign; unsupported model/noise-unit rejection | N4B/C, N5; acceptance flag N6 |
| C4 feed/state/reset adapter | No: engine API/state semantics | PATCH precursor; upstream headers; write adapter/snapshots | Loss/relocalization/reset trials | Fake engine initialization→loss→reset/map switch; stale epoch cannot escape; pinned engine dataset smoke | N4B/C, N5, N6 |
| C5 robot pose/TF | Partly: composition shared; source pose semantics differ | R1/architecture design; write frame bridge | Mount/joint extrinsics | 90° rotation + translation/lever arm; inverse direction; injected loop jump/reset invalidates alignment | N5, N6, N7 |
| C6 usable health | Partly: shared policy; engine evidence differs | HM resource sampler, R2 proposal; write estimator monitor | Recovery/age/controller budgets | Frozen pose+fresh heartbeat; missing covariance; invalid clock/calibration/frame; reset clears validity | N6, N7; event logging N4/N5 |
| C7 latency/resources/queues | Partly: collection shared; internal stage hooks differ | HM, PATCH timing fragments; reuse tracing/perf/psutil/vcgencmd; write events/aggregator | Sustained Pi load/power/thermal | Known delays/queue drops/throttle log; correct quantiles/counts and source age, missing sensors stay unavailable | N4C, N5, N7 |
| C8 regression/evaluation | Partly: metrics shared; invocation/export engine-specific | TE batch ATE/RPE, DP; write run orchestration/continuity checks | Robot/reference accuracy; retained datasets need none | Analytic trajectory+drift; repeated frozen dataset; failed/empty/reset runs retained in denominator | N4A/B, N5, N7 evidence |
| C9 codec/receiver/fault fixtures | Yes: normalized contract independent of estimator | R2 proposal; select COBS/CRC primitives; write host codec/reference receiver | Actual STM32/link/load/fallback | Golden vectors, arbitrary chunking, corruption, oversized input, wrap/session/stale/epoch tests; bounded memory | N6 software; N7 physical |

**INFERRED dependency graph** (software fixtures can be prepared concurrently; gate acceptance follows the existing ladder):

```text
N0 stable power + qualified storage -> fresh N1 -> N2 (unchanged full soak)
  -> N3 [existing ROS tooling + C0 + C1 + C2 audit]
  -> reviewed stereo/profile/calibration captures [hardware + C1 + C2]

Known public dataset + qualified engine build + C0 + C8 -> N4A
N3 + stereo captures + C1 + C2 + C3 + C4 + N4A -> N4B
N4B + bounded live queues + C7 -> N4C
N4A/B/C + C0 + C4 + C5 + C7 + C8 + approved metric bounds -> N5

C0 + C4 + C5 -> C6 (engine facts -> shared validity/health)
C6 + R2 reviewed contract -> C9 host codec/receiver fixtures
N5 + C6 + C9 + approved clock/age/reset semantics -> N6
N6 + actual STM32 receiver/mailbox + final mount/link/power
    + controller-owned fallback + separate physical safety approval -> N7

Every gate produces retained evidence; missing hardware/budgets stay OPEN.
C9 fixtures can be built before N5; they do not promote N6 or N7.
```
