#!/usr/bin/env python3
"""Build the Phase-3 depth revision of the existing deck; write only inside slides_course."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent
# Continue Phase 8 from its immutable incoming source; historical QA stays intact.
if (ROOT/'qa/main-v4-91p.tex').exists():
    from phase8_audit import build
    build()
    raise SystemExit(0)
OS=Path.home()/'Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides_course/main.tex'
preamble=OS.read_text().split(r'\begin{document}')[0]
preamble=preamble.replace('Heterogeneous Edge-AI Runtime','WBR Perception Implementation').replace('An end-to-end operating-systems study','A gate-by-gate engineering guide').replace('Team 3 Stars','').replace('Operating Systems course project','')
# Keep the complete inherited visual system; add only content helpers.
extra=r'''
\newcommand{\deckitems}[1]{\begin{itemize}#1\end{itemize}}
\newcommand{\deckflow}[1]{\begin{tikzpicture}[node distance=9mm]
\foreach \txt [count=\i] in {#1}{\node[box,font=\normalsize,text width=33mm,minimum height=14mm] (n\i) at ({mod(\i-1,4)*4.7},{-floor((\i-1)/4)*2.4}) {\txt};}
\end{tikzpicture}}
'''
rows=[]
for line in (ROOT/'image-prompts/OUTLINE.md').read_text().splitlines():
    m=re.match(r'\| (\d+) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|',line)
    if m: rows.append((int(m[1]),*m.groups()[1:]))
assert len(rows)==89
# Main-content bullets, one takeaway, and deeper operational notes.
D={}
def c(p,bullets,take,notes='',status='PLANNED'):
    D[p]=(bullets.split('|'),take,notes,status)
c(4,'Wheel-biped robot (WBR) navigation needs useful scene-relative motion.|STM32H7 keeps body estimation and balance locally.|Perception adds optional navigation information above that controller.', 'Qualify perception without making balance depend on Linux.', 'The Pi failure requirement is an ownership invariant, not measured physical stability. Actual geometry, mounting and motion budgets remain unknown.','KNOWN ownership / PLANNED integration')
c(5,'A pose may be plausible yet stale or expressed in the wrong frame.|Timing and calibration errors can survive a successful launch.|Linux stalls must remove optional autonomy inputs safely.', 'A valid number is not necessarily a usable estimate.', 'Bottom-up qualification separates transport continuity, clock semantics, geometry, algorithm state and receiver policy. No robot safety test has been completed.')
c(6,'Qualify physical input before estimation.|Reproduce estimation on immutable recorded inputs.|Measure accuracy, continuity, latency and resource limits.|Review a health boundary before controller integration.', 'Each objective needs its own evidence and acceptance review.')
c(7,'Can the Pi sustain the exact input without unexplained gaps?|Can stereo-inertial estimation initialize and track repeatedly?|Can a receiver reject stale, invalid or reset estimates?|Which resource or timing limit fails first?', 'Fix hypotheses and budgets before collecting comparison runs.')
c(9,'Infrared (IR) stereo matches one scene point in two views.|Rectified horizontal disparity d gives depth Z = f b / d.|Intrinsics, baseline b and correspondence determine geometric validity.', 'Stereo depth requires calibrated geometry and valid image pairing.', 'This equation assumes a rectified pinhole pair and nonzero disparity. Here f is focal length in pixels, b is baseline in metres, and Z is metres. No numeric baseline is asserted. See the selected ORB parser and camera profile.','KNOWN method')
c(10,'Visual-inertial odometry (VIO) combines image constraints and motion.|An inertial measurement unit (IMU) measures rotation and acceleration.|Images constrain drift; inertial propagation bridges image intervals.', 'The camera IMU supports perception, not STM32 balance.', 'ORB-SLAM3 tightly integrates visual and inertial constraints. The body controller has an independent IMU, mount, clock and calibration. Do not infer integration from shared names.','KNOWN method / PLANNED run')
c(11,'Simultaneous localization and mapping (SLAM) reuses mapped places.|Loop correction may move the globally consistent map pose.|Continuous local odometry is a separate output contract.', 'A jumping map pose cannot simply be relabeled odom.', 'A planned ROS integration must choose map correction and continuous odometry ownership explicitly. No continuous odometry bridge is implemented or approved.','KNOWN method / PLANNED output')
c(12,'Stereo-inertial input needs left/right IR images plus raw motion.|Historical unit metadata reports BMI085, not older BMI055 descriptions.|Calibration defaults and requested profiles do not prove usable VIO.', 'Identify the actual unit and preserve its calibration warning.', 'Historical 2026-09-13 metadata: firmware 5.17.3.10; SDK serial 243322073847; ASIC serial and firmware-update ID each 251843061466; USB descriptor separately observed. Preserve: IMU Calibration is not available, default intrinsic and extrinsic will be used. These are archived observations, not current enumeration.','HISTORICAL / MEASURED metadata')
c(13,'Robot Operating System 2 (ROS 2) connects topic publishers and subscribers.|Data Distribution Service (DDS) supplies transport and delivery policies.|Receipt does not prove source freshness or correct frame semantics.', 'Inspect the graph, policy and data together.', 'A node is a graph participant; a process can host several nodes and threads. Message header stamps belong to the producer semantics, not automatically to subscription receipt time.','KNOWN method / PLANNED pipeline')
c(14,'Quality of Service (QoS) is an offered/requested contract.|A reliable reader cannot match a best-effort-only writer.|Sensor observers use best-effort, volatile subscriptions.|Static transforms use reliable, transient-local delivery.', 'Topic names alone cannot prove a compatible connection.', 'Inspect reliability, durability, history/depth, deadline and lifespan where relevant. Reliable writers can satisfy best-effort readers. A volatile writer cannot satisfy a transient-local reader. Latched context must reach recorder and replay observer.','KNOWN ROS semantics')
c(15,'EuRoC micro aerial vehicle data contain stereo images and IMU.|Published reference trajectories support algorithm evaluation.|Freeze sequence, calibration and reference association policy.|A dataset baseline does not qualify Pi camera transport.', 'Use known inputs to isolate build and estimator problems.', 'Burri et al., 2016. EuRoC references have sequence-dependent motion-capture/laser-tracker limitations. Read known issues and use compatible reference coverage. No dataset download, build or ORB execution is authorized by this deck task.','KNOWN published dataset / PLANNED baseline')
c(17,'Mac checkout is canonical; preserve its dirty work.|The Pi acquires and records locally.|Secure Shell (SSH) carries control and small evidence.|Use a separate checksummed runtime bundle for each revision.', 'Deployment copies tools; it does not reset either checkout.', 'Installed binaries may differ from checked-out sources. Record source and binary hashes plus exact dependency versions. Large bags stay on independently qualified Pi-local storage. Network configuration changes require approval.','KNOWN ownership')
c(18,'Pi: perception, mapping, evaluation and optional autonomy.|STM32: Linear Quadratic Regulator (LQR) and Virtual Model Control (VMC).|Its Finite State Machine (FSM), watchdog and motor limits remain local.', 'Loss of Pi perception must not remove controller ownership.', 'LQR, VMC and FSM are controller responsibilities, not implemented in this slide task. The actual transport and command envelope remain planned. Physical balance retention still needs approved staged validation.','KNOWN ownership / PLANNED validation')
c(19,'Target: Raspberry Pi 5 with 8 GB memory and Ubuntu.|Non-Volatile Memory Express (NVMe) storage holds large datasets.|Document actual supply, cooling, memory and storage anew.', 'The target bill of materials is not platform qualification.', 'The active-cooler illustration is conceptual. Historical reports mention different memory inventory and a Raspibase fan. Fresh N0 must record the actual device; do not overwrite history with the target specification.')
c(20,'Universal Serial Bus 3 (USB3) feeds the local camera driver.|librealsense decodes sensor frames; realsense-ros publishes them.|ROS topics feed recording, estimation and trajectory evaluation.', 'Keep capture and recording local to the Pi.', 'Native path: camera to USB kernel/backend to SDK callbacks to ROS wrapper to DDS to recorder/observer/estimator. Offline path freezes a bag, converts reviewed stereo/motion inputs, runs upstream ORB, and evaluates trajectories. No remote USB or SSH streaming baseline is proposed.')
c(21,'Software Development Kit (SDK) threads own raw capture.|Wrapper capture, executor, recorder and observer have separate queues.|Upstream tracking runs on the caller; mapping and loop workers run separately.', 'Trace thread ownership before attributing a delay.', 'System.cc starts LocalMapping and LoopClosing threads, and a viewer when requested. TrackStereo invokes Tracking on the input caller. Atlas is shared map state, not a separate process. Wrapper scheduling is a separate layer.')
c(22,'A First-In First-Out (FIFO) queue sends its oldest item first.|Bound each SDK, DDS, executor, recorder and estimator buffer.|Record arrival/dequeue times, depth and discard policy.|An unavailable drop counter is UNKNOWN, never zero.', 'A deep queue can preserve delivery while destroying freshness.', 'Queue instrumentation is planned. Distinguish producer sequence gaps, observed arrival gaps, recorder count mismatch and measured queue overflow. Latest-only processing may bound age but discards input; inertial coverage must remain consistent.')
c(23,'Y8 stores one eight-bit grayscale byte per pixel; no compression assumed.|IR1 payload: 640 × 480 × 1 × 15 = 4.608 MB/s.|Stereo image payload doubles to 9.216 MB/s before overhead.|Metadata, motion, serialization and filesystem traffic add load.', 'Payload arithmetic is a lower bound, not throughput evidence.', 'MB uses decimal 1,000,000 bytes. Y8 is eight-bit grayscale. A 300-second IR1 image-payload equivalent is 1.3824 GB; N2 vendor CSV does not actually store those full image pixels. The storage floor 9.216 MB/s is a margin for IR1, not qualification for stereo recording.','KNOWN profile / CALCULATED payload')
c(24,'Pin mount source, partition and Universally Unique Identifier (UUID).|Measure overall and worst-batch writes, then hashed readback.|micro Secure Digital (microSD): operating system and small logs.', 'Qualify the actual data device before any bag recording.', 'Runbook storage proposal: at least 1 GiB and 60 s, overall and worst-batch throughput at least 9.216 decimal MB/s, fsync per 64 MiB batch, SHA-256 readback and finalized cleanup. Default 8 GiB budget may finish too early; a larger write needs review. Retain 10 GiB headroom. No formatting, mounting or storage probe runs here.')
c(25,'Record operating system, kernel, packages and compiler identity.|Hash dirty sources, runtime binaries and configuration.|Record backend, wrapper, middleware and launch parameters.|Keep failed runs and original raw logs immutable.', 'A commit identifier alone cannot identify a dirty runtime.', 'Historical SDK package 2.58.4 and candidate wrapper 4.58.4 do not imply installed source equivalence. Capture executable and shared-library resolution, vocabulary hash, data hash and run command. Preserve calibration warnings and startup/shutdown logs.')
c(26,'The transform (TF) system relates parent and child frames.|Body convention: x forward, y left, z up.|Optical convention: z forward, x right, y down.|A pose declares origin, axes, units, reference, child and stamp.', 'Frame names do not define geometry by themselves.', 'REP-103 conventions are right-handed. REP-105 map can jump; odom is locally continuous but may drift. world is optional and must be explicitly defined. The estimator body means camera IMU coordinates, not the STM32 robot body.','KNOWN conventions / PLANNED mounts')
c(27,'map → odom is the planned global correction edge.|odom → base_link must be continuous if published.|body and imu_body use measured robot mounting geometry.|Each child has exactly one parent and one transform owner.', 'Plan the tree before publishing any estimator transform.', 'world may be an external reference above map if explicitly defined; it is not a competing parent. body can coincide with base_link only if that choice is documented. Dynamic correction and local odometry owners require architecture review.')
c(28,'camera anchors the planned physical camera mount.|camera_optical and left/right optical frames define image axes.|imu_camera belongs to the camera sensor, not imu_body.|Capture actual wrapper names and static transforms.', 'Use measured camera geometry; do not infer it from a diagram.', 'Actual stream frame IDs may use wrapper-specific names. Check CameraInfo frame agreement, static TF connectivity, calibrated left/right transform and motion frames. The conceptual tree is not a wiring or SDK calibration certificate.')
c(29,'Camera IMU: D435i motion for VIO.|Body IMU: local STM32 balance.|Mounts, noise and clocks remain separate.|Fusion needs timing and geometry evidence.', 'Two IMUs are not interchangeable measurements.', 'Even nominally equal axes and frequencies do not establish synchronization. Do not substitute camera IMU when Pi fails or feed body IMU to ORB without reviewed calibration and clock mapping.','KNOWN separation / PLANNED fusion review')
c(30,'Camera-to-estimator-IMU transform: p_b = T_b_c1 p_c.|Its inverse maps IMU coordinates back into the camera.|SDK rotation arrays and OpenCV matrix storage orders differ.|Test basis vectors, inversion and composition.', 'Transform direction must follow code and numeric tests.', 'Frame.cc composes T_cb with T_bw; ImuTypes.cc stores T_cb = inverse(T_bc). SDK rotations are column-major; OpenCV YAML data are row-major. b here denotes estimator IMU/body, never automatically robot body. Identity defaults do not validate a future nonidentity calibration.','KNOWN source convention / PLANNED tests')
c(31,'Device timestamps may be hardware-relative.|Host steady time and civil time are different clocks.|ROS time may follow simulation rather than wall time.|A mapping needs units, offset, drift and uncertainty.', 'Never subtract across domains without a defined relationship.', 'Preserve original device milliseconds and integer ROS nanoseconds. Label each timestamp domain and mapping version, including startup domain changes and clock adjustment events. Equal clock-domain labels alone do not measure camera exposure-to-IMU offset.')
c(32,'Capture and device stamp describe source events.|Driver/publish events differ from source epochs carried in headers.|Receipt, processing start/end and output need instrumentation.|Bag storage time remains separate from the message header.', 'Name the event behind every latency timestamp.', 'Header stamps may copy a transformed capture stamp rather than publish time. Distinguish estimator pose epoch from output emission time. A single timeline is a semantic chain, not proof that timestamps share a clock.')
c(33,'Global-time option readback is a configuration observation.|The SDK maps device time toward host time.|Enabled global time does not measure camera–IMU offset.|Arrival minus mapped stamp is not pure USB latency.', 'Record domains and uncertainty before reporting source age.', 'Pinned v2.58.4 global_timestamp_reader.cpp provides algorithm evidence. Historical metadata read global time 1, but actual frame domains were not measured in that session. Off/on diagnostics must use separate labeled runs and preserve raw stamps.')
c(34,'Processing interval: host-steady end minus start.|Receipt-to-output includes queue wait and processing.|Capture-to-output requires a qualified device-to-host mapping.|Record startup, interior and trailing gaps separately.', 'One latency label must identify one interval and clock.', 'A source-age bound must include mapping uncertainty and timestamp semantics. ROS header time and recorder storage time cannot replace local steady-clock instrumentation. SDK timer starts before sensor opening; explain startup offsets without relaxing internal/trailing gap thresholds.')
c(35,'Stereo intrinsics/extrinsics belong to the selected image profiles.|Camera–IMU extrinsics and time offset need independent validation.|Noise densities and bias walks remain UNKNOWN for this unit.|SDK computer-aided design (CAD) fallback is not a unit measurement.', 'Separate transport acceptance from calibration readiness.', 'Preserve verbatim: IMU Calibration is not available, default intrinsic and extrinsic will be used. Historical logs establish CAD fallback, identity sensitivity, zero bias and placeholder zero noise arrays. Do not infer the precise device-side cause from this warning alone.','HISTORICAL defaults / UNKNOWN calibration')
c(36,'Match model, resolution, distortion and rectification path.|Use left/right calibration for the actual paired streams.|Inspect epipolar vertical residuals and temporal pairing.|Reject mismatched profiles before feature tuning.', 'Wrong geometry can mimic an algorithm failure.', 'For rectified images corresponding points should lie on the same horizontal epipolar line. Report residual distributions, target coverage, rejected pairs and timestamp differences; budgets require approval. Do not rectify twice or copy EuRoC calibration into D435i settings.')
c(37,'Measure the fixed target and configuration.|Excite every axis without blur or saturation.|Check detections and shared time coverage.|Capture stationary full-precision noise data.', 'A textured-room trajectory is not automatically calibration data.', 'Kalibr candidate: measured AprilGrid, safe cable slack, varied viewpoints and excitation. Preserve unsuccessful takes. Follow the readiness procedure only after camera authorization and prerequisite gates. No calibration write or guided capture is performed here.')
c(38,'Allan deviation compares noise across averaging time τ.|Short-time slope helps estimate white-noise density.|Longer records are needed to constrain bias instability or walk.|Vendor comma-separated values (CSV) round motion; use full precision.', 'Choose stationary duration from the averaging times you need.', 'Allan variance is half the mean squared difference between adjacent interval averages; Allan deviation is its square root. Record sample units/rates, temperature, stationary validity and confidence/sample support. Do not confuse bias instability with random walk. Tool compatibility and unit-specific parameters remain unknown.')
c(39,'Kalibr is a candidate for camera–IMU geometry and time offset.|imu_utils is a candidate for stationary noise analysis.|Bag import, camera model and dependency compatibility need tests.|Select tools using residuals, holdout data and reproducibility.', 'A tool name is not a calibration plan or accepted result.', 'Kalibr ROS1-oriented bag support does not imply direct ROS2 bag acceptance. Preserve originals and review an import/conversion path. imu_utils does not supply complete stereo/camera–IMU calibration. No dependency install or format implementation is authorized.')
c(40,'Oriented FAST and Rotated BRIEF (ORB) features link image views.|FAST: Features from Accelerated Segment Test; BRIEF: Binary Robust Independent Elementary Features.|Tracking runs on caller; mapping and loop workers optimize.|Atlas owns multiple maps and merging state.', 'Thread activity is not equivalent to valid tracking.', 'FAST means Features from Accelerated Segment Test; BRIEF means Binary Robust Independent Elementary Features. These expansions belong to the feature components. System.cc starts worker threads; tracking and map corrections need explicit event records. The viewer is additional work, not a prerequisite for a scientifically valid display-free output path.','KNOWN algorithm / PLANNED operation')
c(41,'Pair calibrated stereo images at a defined image epoch.|Attach all required IMU samples over each image interval.|Extract features, match stereo and predict/optimize pose.|Inspect tracking state, relocalization and reset before tuning.', 'Every processed image needs accounted motion coverage.', 'TrackStereo accepts images, timestamp and vector of IMU measurements. Adapter boundaries need leading and trailing coverage; do not assume example readers guard every boundary. Motion gaps, clock offset, frame error and weak texture require separate diagnosis.')
c(42,'Keyframes retain selected poses and visual constraints.|Local mapping optimizes nearby structure and inertial state.|Atlas can create multiple maps and later merge them.|Loop correction can change the reference transform.', 'Invalidate or re-establish downstream state after map changes.', 'A keyframe trajectory is not an all-frame trajectory. Compare coverage separately. Mapping load and loop/global optimization can create resource spikes. Preserve map/session/reset identity in the proposed health contract.')
c(43,'Stereo provides metric geometry when calibration is valid.|Inertial initialization estimates gravity, velocity and biases.|Sufficient excitation and correct timing remain necessary.|Record every attempted initialization and reset.', 'Stereo scale does not remove inertial initialization requirements.', 'Avoid transferring monocular unknown-scale wording to stereo. Degenerate motion, wrong noise, sign errors and gaps can defeat initialization despite available depth. Initialization criteria and numerical budgets remain planned.')
c(44,'YAML (YAML Ain’t Markup Language) settings select a parser path.|Audit camera model, intrinsics, dimensions and frame rate.|Audit stereo geometry, IMU transform, frequency and four noise fields.|Feature and viewer settings follow only after valid input.', 'Example settings are not this unit’s calibrated configuration.', 'Pinned new format uses File.version and Camera.type; Camera1/Camera2 projection and distortion, Camera.width/height/fps/RGB; Stereo.b or Stereo.T_c1_c2 and Stereo.ThDepth for the chosen path; IMU.T_b_c1/Frequency/NoiseGyro/NoiseAcc/GyroWalk/AccWalk/InsertKFsWhenLost; ORBextractor nFeatures/scaleFactor/nLevels/iniThFAST/minThFAST. Inspect actual parser behavior; do not mix legacy keys. Tracking multiplies density by sqrt(frequency) and divides walk by sqrt(frequency): do not discretize twice.')
c(45,'PLANNED: interpolate accel only between valid bracketing samples.|Use gyro epochs for a reviewed combined input grid.|Reject gaps, duplicate/backward time and extrapolation.|Retain originals and every interpolation/rejection decision.', 'A 200 Hz input grid does not make raw accel 200 Hz.', 'a(t) = (1−α)a0 + αa1 with α=(t−t0)/(t1−t0), t0≤t≤t1. Verify known linear signals, irregular spacing, missing endpoints and exact nanosecond conversions. Apply measured time offset once with a tested sign. A candidate mono adapter is not an implemented stereo input path.')
c(46,'Candidate envelope: version, session, sequence and tracking/reset state.|Include reference/child frame, source stamp and clock domain.|Pose/velocity are optional when valid; uncertainty may be unavailable.|Rate, transport and stale threshold await receiver evidence.', 'Review semantics before implementing the wire format.', 'Application Programming Interface (API) and message changes require approval. No fixed Hz or timeout is invented. Source-age accounting must survive independent Pi/STM32 clocks. Heartbeat may be separate but cannot claim a fresh estimate. Mark absent covariance explicitly rather than fabricate it.')
c(47,'ABSENT and INITIALIZING are not fresh estimates.|FRESH requires valid fields, frame/session and bounded source age.|STALE or INVALID removes optional perception input.|Reset requires explicit frame/session re-establishment.', 'A live heartbeat can still accompany stale perception.', 'This is a planned semantic state model, not firmware. Wrong frame, nonfinite fields, duplicate sequence, old session and unannounced map jump must reject. Receiver clock wrap, mapping uncertainty and restart behavior need reviewed fixtures.')
c(48,'STM32 keeps its body IMU, control loop and motor limits.|Receiver checks reject unusable perception locally.|Optional autonomy references degrade under a reviewed policy.|Pi restart never bypasses re-establishment checks.', 'The controller stays authoritative when perception disappears.', 'Candidate fallback may remove navigation references while preserving local balance; precise action depends on robot/controller design and safety review. This slide claims ownership, not measured stability. Transport/rate/threshold design is open.','KNOWN ownership / PLANNED fallback tests')
c(50,'N0 platform → N1 USB → N2 raw → N3 record/replay.|N4A EuRoC → N4B offline stereo → N4C live stereo.|N5 evaluation → N6 health → N7 controller boundary.|Owner-confirmed: no Pi gate has passed.', 'Each gate advances only with reviewed evidence.', 'N0 extracts platform prerequisites for teaching, not a new implemented receipt. N4 uses repository subgate names. N5–N7 are planned organizing gates; numeric budgets and physical execution approval are still required.')
c(51,'Entry: fresh restart; camera-free platform inventory.|PASS: 64-bit Arm architecture (ARM64), Ubuntu 24.04, Jazzy, synchronized Coordinated Universal Time (UTC).|Require throttled=0x0, temperature <75°C, MemAvailable ≥512 MiB.|Evidence: identity, power/cooling notes and complete health logs.', 'Stop on platform faults before investigating perception.', 'Check actual RAM against the 8 GB target. Historical sticky throttling and undervoltage are preserved, not erased by declaring a fresh gate. Resolve supply/cooling cause, then make a new observation interval. N2/N5 must verify health under load again.')
c(52,'Entry: eligible N0 plus explicit CAMERA AVAILABLE.|PASS: camera’s own direct branch ≥5000M, normal-user access.|Separate SDK, application-specific integrated circuit (ASIC), firmware-update and USB-descriptor identifiers.|Evidence: sealed result, topology, access and kernel snapshots.', '480M means STOP before SDK enumeration or N2.', 'Receipt must match host/boot and be at most two hours old. Verify video/HID/IIO/custom-HID controls without broad sysfs permissions. Expected historical unit firmware/IMU identity must be checked anew. Storage probing requires a fresh N1 afterward. Never repair mismatch through unapproved firmware update.')
c(53,'Entry: sealed, eligible N1 with exact requested profiles.|IR1: 640 × 480, Y8 eight-bit grayscale, 15 Hz.|Raw gyro 200 Hz and accel 100 Hz; no combined IMU.|Review 20 s → 105 s → mandatory 300 s raw soak.', 'No fallback stream or short capture substitutes for N2.', 'Every interval preserves CSV, exact argv/stdout/stderr, before/after USB topology, continuous journal, one-Hz health and source/binary hashes. Separate 12-second image check saves three PGMs after each interval. No IR2, depth, RGB or combined motion in the baseline.')
c(54,'IR: 14.25–15.75 Hz; maximum gap ≤0.20 s.|Gyro: 190–210 Hz; accel: 95–105 Hz; motion gap ≤0.05 s.|Positive stamps/frame steps; no missing image frame numbers.|PASS requires coherent pixels, clean logs and actual review.', 'Capture success alone does not accept N2.', 'Recompute whole-request and interior rates, boundary offsets and content statistics. Explain startup setup offsets without exempting internal/trailing gaps. Preserve known HID warnings and IMU calibration warning. Reviewed accept-n2 requires all 20/105/300-second receipts, raw logs, three-image checks, power/cooling and plausible IMU review. Calibration remains open.')
c(55,'Entry: reviewed N2, qualified storage and fresh N1.|Inspect installed wrapper/version before starting one publisher.|PASS: read back parameters and observe a complete 60 s live window.|Evidence: graph, QoS, frames, parameters and recording-load metrics.', 'Do not replace simultaneous observation with a brief topic echo.', 'Prepared baseline candidate is wrapper 4.58.4, not proof of installation. Use one /camera/camera publisher; unite_imu_method=0; no IR2/RGB/depth/pointcloud/alignment/RGBD/combined motion. Static connectivity and image/CameraInfo agreement are mandatory. Missing context or unsupported parameters stop the gate.')
c(56,'Record ten explicit baseline topics, including calibration context.|PASS: clean interrupt finalizes bag metadata and expected counts.|Stop live camera; isolate and observe the entire replay.|Match types, stamps, order and full decoded payload hashes.', 'A playable bag is not automatically a reproducible dataset.', 'Ten entries: IR1 image; CameraInfo; raw gyro; raw accel; gyro IMUInfo; accel IMUInfo; depth-to-IR1, depth-to-gyro and depth-to-accel extrinsics; /tf_static. Exact pinned names/types require inspection. Live domain 42, replay 43; localhost-only baseline. No record-all flag, combined /imu, reindex shortcut or live contamination. Preserve wire hashes too; CDR padding differences are not pixel changes.')
c(57,'IR1-only N2/N3 remain preserved transport baselines.|Stereo adds reviewed IR2 profile, paired pixels and context.|Requalify bandwidth, recording load, storage and calibration.|Updated nodes, messages or derived formats need approval.', 'The stereo goal does not authorize quietly changing N2.', 'An IR1-only dataset cannot feed stereo-inertial estimation. Prepare a separately reviewed extension with both camera projections, stereo extrinsics/rectification, all required motion/time coverage, explicit topics and lossless data. Existing mono-inertial candidate artifacts are not stereo qualification.')
c(58,'Entry: separately authorized run, pinned build/data/settings.|PASS: complete inputs, repeated initialization and finite trajectories.|Evaluate against reference with declared association and budgets.|Evidence: all run logs, exports, hashes and failed trials.', 'Compilation alone cannot pass N4A.', 'Build in an isolated source copy because upstream CMake writes outputs under source. Use bounded parallelism; audit OpenCV, Eigen, Pangolin, Boost, OpenSSL, DBoW2, g2o and Sophus. Preserve both all-frame and keyframe EuRoC exports; verify format and coordinate conventions. No ORB command runs during this deck build.')
c(59,'Entry: reviewed stereo inputs, calibration and tested conversion.|PASS: valid pairing, epipolar residuals and IMU interval coverage.|Require repeatable finite tracking within predeclared budgets.|Evidence: immutable raw/derived hashes, calibration and trajectories.', 'Without suitable reference, D435i accuracy remains UNKNOWN.', 'Lossless left/right pixels and full-precision raw motion are required. Reject placeholder noise and copied/default extrinsics treated as measured. Test interpolation, gaps, no extrapolation, offset sign, transform inverse and count reconciliation. New adapter formats require review before implementation.')
c(60,'Entry: accepted offline stereo plus renewed sensor/ROS checks.|PASS: delivery, initialization and continuity meet approved budgets.|Bound pairing wait and backlog; account for drops and shutdown.|Evidence: input/output state timeline, queue metrics and full logs.', 'Offline success does not prove live freshness.', 'Hold calibration and settings constant when replacing replay with live capture. Diagnose additional wrapper/DDS/executor scheduling and thermal load. Record every reset, loss, pairing rejection and incomplete interval; unsupported counters remain unknown.')
c(61,'Entry: qualified runs, fixed trials and defined clock relationships.|PASS: complete initialization, loss, timing and resource coverage.|Accuracy needs suitable reference, alignment and accepted budgets.|Evidence: raw events, evo commands, percentiles and all repeats.', 'No approved numerical budget means no performance PASS.', 'Record sample eligibility and exclusion counts, mapping uncertainty, middleware/backend, configuration and environmental conditions. Show failures rather than a best-run-only summary. Do not compare incompatible sequences or alignment policies.')
c(62,'Entry: reviewed candidate health contract and fixture plan.|PASS: synthetic cases reject absent, stale, invalid and old-session data.|Accept only eligible fresh data; test reset/frame changes.|Evidence: fixture inputs, expected transitions and review record.', 'Synthetic success proves tooling only.', 'Use nonfinite pose, wrong frame, old capture with new receipt, duplicate sequence, mapping uncertainty and restart fixtures. Offline tests do not establish physical transport or controller stability.')
c(63,'Entry: reviewed N6 plus separate controller/hardware authorization.|PASS: approved staged failures preserve local controller ownership.|Disconnect, stale output and Pi restart must reject perception.|Evidence: controller events, versions, timing relation and operator review.', 'The deck authorizes no motor or firmware action.', 'N7 physical stability is unknown. A staged safety plan and operator authority are prerequisites; timestamp correlation across Pi and microcontroller needs a defined relation. Never place hard-real-time balance under ROS scheduling.')
c(64,'Build a new checksummed bundle from canonical Mac utilities.|Deploy into a new Pi runtime directory; verify hashes there.|Store exact commands, settings, logs and real review receipts.|Retain historical evidence and every failed run unchanged.', 'A reviewable evidence packet is the deliverable of each gate.', 'Raw records precede derived analysis and explicit human acceptance. Do not fabricate review.json booleans or modify deployed sources in place. Bundle manifests include dirty-source hashes; successful software tests are labeled offline/synthetic tooling only.')
c(65,'Inspect hardware, power and the camera’s own USB branch first.|Then raw streams, clocks, driver, ROS graph and QoS.|Then calibration, ORB input/state, trajectory and evaluation.|Fix the earliest failed layer; preserve downstream symptoms.', 'Do not tune SLAM to hide a transport failure.', 'Bottom-up order reduces ambiguity. Save complete logs before changing one variable. Use recorded inputs to separate acquisition from estimator behavior; add only instrumentation needed to answer the bounded question.','KNOWN debugging order / PLANNED runs')
c(66,'480M: inspect cable, direct branch and power before software.|Silent topic: inspect publisher, parameter readback and QoS.|Initialization failure: inspect coverage, frames, offset and noise.|Calibration fallback: preserve warning; do not copy constants.', 'Similar symptoms can require different evidence.', 'Permissions need exact device-ancestor inspection, not broad access. If trajectory looks smooth, still inspect stale epochs, reset state and reference coverage. A storage bottleneck can manifest as delayed recording without raw sensor failure. Diagnose one layer at a time.')
c(67,'Artificial intelligence (AI): one bounded question.|Limit files, hosts, actions and fixtures.|Require commands, evidence and STOP conditions.|Owner accepts gates and safety decisions.', 'Delegate analysis, not unbounded authority.', 'Gate tickets: N0 inventory; N1 own-branch/access diagnosis; N2 sealed timing/content recomputation; N3 context/replay checks; N4 settings/association/fixed-data run; N5 metrics; N6 reviewed semantic fixtures; N7 approved boundary documentation. Do not delegate guessed calibration, blanket reinstall, fabricated review or autonomous motor tests.')
c(69,'Freeze input, binary, calibration and all settings.|Predeclare hypotheses, budgets, trial count and exclusions.|PLANNED backlog minimum: three fixed-data offline repeats.|Retain every failure and compare like-for-like conditions.', 'One successful run is not evidence of repeatability.', 'Three repeats are a planning minimum from the backlog, not a statistical guarantee or existing result. Choose longer/repeated trials from variability and acceptance uncertainty. Separate EuRoC reference runs, D435i offline, live and interface fixture campaigns.')
c(70,'Absolute Trajectory Error (ATE) compares aligned associated poses.|Let P_i be estimate, Q_i reference and S chosen alignment.|E_i = Q_i^{-1} S P_i; summarize translation magnitude.|Report root mean square error (RMSE), valid overlap and exclusions.', 'No reference means no measured absolute accuracy.', 'RMSE = sqrt(sum(norm(trans(E_i)) squared)/N). Association tolerance, transform direction, units, time coverage and reference limitations belong in the metric record. This is the chosen pose-convention definition; verify trajectory conversion before evo.')
c(71,'Relative Pose Error (RPE) compares motion between two epochs.|E_ij = (Q_i^{-1}Q_j)^{-1}(P_i^{-1}P_j).|Declare time or distance separation and eligible pair counts.|Report translation and rotation errors separately.', 'RPE answers local motion error at a declared separation.', 'A short time delta and long distance delta answer different questions. Specify all-pairs or consecutive-pairs policy, motion units, rotational units, association tolerance and failed/insufficient overlap. Global rigid alignment cancels from relative motions; scale fitting changes their metric values.')
c(72,'Default: rigid six-degree-of-freedom alignment for metric stereo.|Optional seven-degree-of-freedom scale fit is diagnostic only.|Use evo after verified coordinate and timestamp conversion.|Log version, options, association tolerance and raw output.', 'Scale fitting can conceal a stereo scale error.', 'Planned command family: evo_ape tum REFERENCE.tum ESTIMATE.tum --align. evo uses absolute pose error terminology for this command. Configure evo_rpe delta, delta unit and pose relation explicitly after checking the installed version. EuRoC exports are not automatically TUM column order; preserve originals.')
c(73,'Success rate uses all declared initialization attempts as denominator.|Measure initialization time from a defined first eligible input.|Track loss duration, resets and relocalization events.|Check trajectory coverage, not only exported sample count.', 'Report failed attempts alongside successful trajectories.', 'Retain sensor epoch, local event time, state, reset/session/map identifier and exclusion reason. Pose export presence alone cannot recover all state events. Numerical state-event instrumentation and interface changes require review before implementation.')
c(74,'P50/P95/P99 are the 50th/95th/99th latency percentiles.|Name receipt-to-start, processing and receipt-to-output separately.|Reconcile sequence gaps, received counts and recorded counts.|Unavailable queue/drop counters remain UNKNOWN.', 'Percentiles need event definitions and eligible sample counts.', 'Use one monotonic clock for host intervals. Capture-to-output requires mapping uncertainty. Define percentile estimator, warmup policy and number of samples. Frame loss, delayed arrival and intentional input rejection are different events; do not call all count mismatches dropped frames.')
c(75,'Log Central Processing Unit (CPU) load and clock frequency.|Track temperature, memory and Resident Set Size (RSS).|Record throttling, queue depth and free data space.|Align samples with initialization, loss and optimization events.', 'Resource averages cannot explain tail stalls alone.', 'Use system and process CPU separately, sample cadence, host-steady timestamps and complete hardware health logs. Frequencies/temperature are observations, not electrical power measurements. Unsupported queue instrumentation stays unknown. Capture tools themselves contribute overhead.')
c(76,'EuRoC accuracy can use its documented reference coverage.|D435i accuracy requires a suitable independent reference.|Show association, alignment and trial coverage with each result.', 'Accuracy results are unmeasured.', 'No fake points, lines, error bars, zeros or numerical targets appear on these axes. Fill only from reviewed N4/N5 evidence.', 'UNKNOWN results / PLANNED evaluation')
c(77,'Choose one named same-clock latency interval per distribution.|Pair percentile plots with counts, queues and loss evidence.|Source-age plots require qualified clock mapping.', 'Timing and loss results are unmeasured.', 'Empty axes represent missing observations rather than zero latency or zero loss. Budgets must be approved before performance acceptance.','UNKNOWN results / PLANNED evaluation')
c(78,'Report CPU/frequency, temperature, memory and throttling.|Retain time-series context and all trial identities.|Inspect resource changes around estimator events.', 'Resource results are unmeasured.', 'No curves or sample readings have been fabricated. N0 platform checks do not substitute for load qualification.','UNKNOWN results / PLANNED evaluation')
c(80,'Default: native Pi baseline and direct known-good USB3 cable.|Docker adds package, device and user/group boundaries.|A hub/storage topology can change shared power and bandwidth.|Revisit only after equivalent physical gates and clear deployment benefit.', 'Packaging cannot compensate for a 480M camera branch.', 'Container portability is useful only after identical sensor, clock and recording evidence. Connector shape is not negotiated speed. Shared-storage trials need own-branch speed, power and sustained-load evidence.')
c(81,'Keep exact IR1 640×480/15 qualification unchanged.|Stereo starts with matching profiles as a reviewed extension.|Emitter-off is a separate natural-feature tracking experiment.|Preserve global-time readback and original timestamp domains.', 'Change one input variable with paired quality and load evidence.', 'More resolution/rate may improve features but increases blur, bandwidth or CPU trade-offs. Preserve accepted emitter setting; compare off/on under controlled scene/lighting. Global time off/on diagnostics require separate evidence; no silent stamp rewrite or assumed zero offset.')
c(82,'Validate upstream EuRoC and offline inputs before live wrapper.|Candidate: Kalibr spatial/time calibration plus measured IMU noise.|Choose tools from import/build/model compatibility and residuals.|Defer wheel odometry until timing, frames and slip evidence exist.', 'Add complexity only to solve a measured failure mode.', 'A ROS wrapper helps integration but adds queues, pairing and revision differences. Matched-data comparison should establish behavior before choosing the path. Wheel fusion needs synchronized encoders, geometry and slip handling; no fusion node is designed here.')
c(83,'Candidate rate follows useful output cadence and receiver capacity.|Transport choice needs error, bandwidth and timing measurements.|Stale thresholds require measured age and safety-policy review.|Uncertainty fields are optional only when justified.', 'Approve the interface before writing messages or firmware.', 'Pi and STM32 clocks are independent. Link receipt cannot prove capture freshness without a source-age bound. No fixed transport, Hz, stale timeout or covariance is invented; first-party public API/message changes require approval.')
c(85,'8 September: x86 virtual machine (VM)/Docker USB2 NO-GO.|12/13 September: Pi saw 5000M, then USB regressed to 480M.|A historical 105-second capture did not complete N2.|Archived optimistic PASS wording cannot promote current gates.', 'History explains risks; restart acceptance from fresh N0.', 'Sources: baseline audit, Pi-native validation report, evidence reconciliation and calibration readiness. Historical raw CSV/PGM files from the 105-second capture are absent from this Mac repository. Retain saved analyses/logs and the limitation.','HISTORICAL / MEASURED saved observations')
c(86,'Owner-confirmed: no Pi gate has passed.|Current USB, platform and storage qualification are absent.|Stereo pixels, calibrated motion and repeated estimation are unqualified.|Health semantics and physical controller integration remain planned.', 'Current status is OPEN, not a recovered historical PASS.', 'The brief overrides older PROJECT_STATE/NEXT_GATE wording. Config directories contain no qualified stereo configuration. No new camera, ORB, network, firmware or robot execution occurred while creating the deck.','UNKNOWN current qualification')
c(87,'Start with fresh camera-free N0 evidence.|After CAMERA AVAILABLE: N1 → N2 → N3.|N4A needs N0; stereo/calibration enables N4B/C and N5.|Review N6; separately authorize N7.', 'Advance on evidence, not dates or a successful launch.', 'The roadmap is conditional. Earlier transport gates block physical acquisition; independent algorithm planning remains useful but no ORB execution is authorized now. Preserve every failure and ask for the missing decision only when concrete evidence is ready.')
c(88,'Trusted perception needs qualified input, clocks and calibration.|Repeated estimation and explicit metrics support engineering decisions.|Independent controller ownership limits perception failure propagation.|Status: no Pi gate passed; next action is fresh N0 evidence.', 'The guide supplies a reproducible path, not measured robot readiness.', 'Contribution: one source-grounded gate ladder, ownership boundary, implementation/data/clock model, evaluation contract and bounded AI tickets. The owner can direct agents without conflating tooling tests and hardware evidence. Physical balance and performance remain unverified.','KNOWN ownership / PLANNED qualification')

# Exact technical figures. Generic flow charts have deliberate straight arrows.
def flow(labels):
    labels=labels.split('|'); n=len(labels)
    width= min(43,176/n-7); step=width/10+0.8
    out=[r'\begin{tikzpicture}[y=.70cm]']
    for i,x in enumerate(labels):
        out.append(r'\node[box,font=\normalsize,text width='+str(width)+r'mm,minimum height=12mm] (a'+str(i)+f') at ({i*step},0) '+'{'+x+'};')
        if i: out.append(r'\draw[flow] (a'+str(i-1)+'.east) -- (a'+str(i)+'.west);')
    return '\n'.join(out)+r'\end{tikzpicture}'
def twoflows(a,b):
    return flow(a)+r'\par\medskip'+flow(b)
def tree(nodes,edges):
    out=[r'\begin{tikzpicture}[y=.70cm]']
    for name,x,y,label in nodes: out.append(r'\node[box,font=\normalsize,minimum width=25mm] ('+name+f') at ({x},{y}) '+'{'+label+'};')
    for a,b in edges: out.append(r'\draw[flow] ('+a+') -- ('+b+');')
    return '\n'.join(out)+r'\end{tikzpicture}'
F={}
F[5]=flow('Stale source|Plausible pose|Unsafe reference')
F[9]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]
\coordinate (l) at (0,0);\coordinate (r) at (7,0);\coordinate (p) at (3.5,3);
\node[box,font=\normalsize] at (0,-.5) {Left camera};\node[box,font=\normalsize] at (7,-.5) {Right camera};\node[box,font=\normalsize] at (3.5,3.5) {Scene point};
\draw[flow] (l)--(p);\draw[flow] (r)--(p);\draw[<->,navy,thick] (0,.3)--node[above,fill=paper]{Baseline $b$}(7,.3);
\node at (3.5,1.3) {$Z = f b / d$};\end{tikzpicture}'''
F[11]=twoflows('Local motion|Continuous odom','Revisited place|Map correction')
F[13]=flow('Publisher|DDS policy|Subscriber')
F[17]=flow('Mac: source|Pi: local runs|Evidence review')
F[18]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]
\node[draw=navy,fill=navy!6,minimum width=78mm,minimum height=33mm] (pi) at (0,0) {};
\node at (0,.9) {Raspberry Pi / Linux};\node at (0,.1) {Camera VIO / mapping};\node at (0,-.7) {Optional autonomy};
\node[draw=teal,fill=teal!6,minimum width=78mm,minimum height=33mm] (mcu) at (10,0) {};
\node at (10,.9) {STM32H7};\node at (10,.1) {Body IMU / balance};\node at (10,-.7) {Watchdog / motor limits};
\draw[flow] (pi.east)--node[above,lbl]{Health}(mcu.west);
\node[box,font=\normalsize] (mot) at (10,-3) {Actuation};\draw[flow] (mcu.south)--(mot);
\end{tikzpicture}'''
F[20]=twoflows('D435i|USB3 / kernel|librealsense|realsense-ros','Topics / QoS|Local rosbag|ORB-SLAM3|Trajectory / evaluation')
F[21]=twoflows('Capture threads|Wrapper executor|Recorder process','Tracking caller|Mapping worker|Loop worker')
F[22]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]
\node[box,font=\normalsize] (p) at (0,0) {Producer};
\foreach \x/\t in {4/Newest,6/Older,8/Oldest}{\node[box,minimum width=18mm,minimum height=15mm] at (\x,0) {\t};}
\node[box,font=\normalsize] (c) at (12,0) {Consumer};
\draw[flow] (p.east)--(3,0);\draw[flow] (9,0)--(c.west);
\draw[decorate,decoration={brace,mirror,amplitude=4pt},navy] (3,-1)--node[below=5pt]{Newest at input; oldest dequeued at output}(9,-1);
\end{tikzpicture}'''
F[26]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]
\node[text=navy] at (-1.7,1.2) {Body};
\draw[flow] (0,0)--(2,0) node[right]{x forward};
\draw[flow] (0,0)--(0,1.5) node[above]{z up};
\draw[flow] (0,0)--(-1,-.8) node[below]{y left};
\node[text=navy] at (8,1.5) {Optical};
\draw[flow] (7,0)--(9,0) node[right]{x right};
\draw[flow] (7,0)--(7,-1) node[below]{y down};
\draw[flow] (7,0)--(6,.8) node[above left]{z forward};
\end{tikzpicture}'''
F[27]=tree([('map',0,0,'map'),('odom',4,0,'odom'),('base',8,0,'base\_link'),('body',12,0,'body'),('imu',12,-2,'imu\_body'),('cam',8,-2,'camera')],[('map','odom'),('odom','base'),('base','body'),('body','imu'),('base','cam')])
F[28]=tree([('cam',7,0,'camera'),('opt',0,-2,'camera\_optical'),('imu',5,-2,'imu\_camera'),('left',10,-2,'left\_camera'),('right',15,-2,'right\_camera'),('lo',10,-4,'left optical'),('ro',15,-4,'right optical')],[('cam','opt'),('cam','imu'),('cam','left'),('cam','right'),('left','lo'),('right','ro')])
F[30]=flow('Camera point $p_c$|$T_{b\_c1}$|IMU point $p_b$')
F[31]=flow('Device clock|Qualified mapping|Host steady clock')+r'\par\medskip\centering ROS time and host civil time require separate semantics.'
F[32]=twoflows('Capture / device|Driver / header|Publish / receipt','Queue wait|Processing start/end|Output emission')
F[34]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]
\draw[flow] (0,0)--(15,0);
\foreach \x/\t in {1/Receipt,5/Start,10/End,14/Output}{\draw[navy] (\x,-.2)--(\x,.2);\node[above] at (\x,.3) {\t};}
\draw[<->,teal,thick] (5,-1)--node[below]{Processing}(10,-1);
\draw[<->,navy,thick] (1,-2)--node[below]{Receipt-to-output: one host steady clock}(14,-2);
\end{tikzpicture}'''
F[36]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]
\foreach \x/\t in {0/Left rectified,8/Right rectified}{\draw[navy,thick] (\x,0) rectangle ++(6,3);\node at (\x+3,3.5){\t};\draw[teal] (\x,1.5)--++(6,0);}
\fill[navy] (2,1.5) circle (3pt);\fill[navy] (10.5,1.5) circle (3pt);
\node at (7,-.6) {Correspondences share the epipolar row after correct rectification.};\end{tikzpicture}'''
F[38]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]
\draw[flow] (0,0)--(12,0) node[right]{Averaging time $\tau$};\draw[flow] (0,0)--(0,3.5) node[above right]{Allan deviation};
\node[text=muted] at (6,1.8) {PLANNED stationary analysis; no measured curve};\end{tikzpicture}'''
F[40]=twoflows('Stereo + IMU|Tracking caller|Current pose','Keyframe queue|Local mapping|Loop closing / Atlas')
F[41]=flow('Pair + interval|Features / matches|Pose optimization|State + output')
F[42]=flow('Keyframes|Local optimization|Atlas maps|Loop / merge')
F[43]=flow('Visual tracking|Inertial excitation|Gravity / bias estimate|Initialized state')
F[45]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]
\draw[flow] (0,0)--(13,0);\foreach \x in {2,6,10}{\fill[teal] (\x,0) circle (3pt);}\node[above] at (2,.3){$a_0$};\node[above] at (6,.3){$a(t)$};\node[above] at (10,.3){$a_1$};
\node at (2,-.6){$t_0$};\node at (6,-.6){Gyro epoch $t$};\node at (10,-.6){$t_1$};
\node at (6,1.6){$a(t)=(1-\alpha)a_0+\alpha a_1,\quad \alpha=\frac{t-t_0}{t_1-t_0}$};
\node[text=muted] at (6,-1.7){Reject without valid brackets; never extrapolate.};\end{tikzpicture}'''
F[46]=flow('Version / session|Pose + frame / time|Validity + reset|Receiver checks')
F[47]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]
\node[box,font=\normalsize] (a) at (0,0){ABSENT};\node[box,font=\normalsize] (i) at (4,0){INITIALIZING};\node[box,font=\normalsize] (f) at (9,0){FRESH};\node[box,font=\normalsize] (s) at (14,0){STALE};\node[box,font=\normalsize] (v) at (9,-2){INVALID};
\draw[flow] (a)--node[above,lbl]{Start}(i);\draw[flow] (i)--node[above,lbl]{Eligible}(f);\draw[faultflow] (f)--node[above,lbl]{Too old}(s);\draw[faultflow] (f)--node[right,lbl]{Bad/reset}(v);
\draw[flow] (v.west) -- node[below,lbl]{Reset review} (4,-2) -- (i.south);\draw[flow] (s.south) -- (14,-3) -- (4,-3) -- node[left,lbl]{Re-establish} (i.south);
\end{tikzpicture}'''
F[48]=twoflows('Perception envelope|Local validation|Optional autonomy','Body IMU|STM32 balance|Motor limits')
F[50]=twoflows('N0 platform|N1 USB|N2 raw|N3 bag / replay','N4A / B / C|N5 metrics|N6 health|N7 boundary')
F[52]=flow('Pi USB3 root|Direct data cable|D435i own branch')
F[53]=flow('20 s smoke|105 s repeat|300 s soak|Human review')
F[55]=flow('One publisher|Parameter readback|60 s observer|Bounded recorder')
F[56]=flow('Finalized bag|Camera stopped|Isolated full replay|Payload comparison')
F[57]=twoflows('IR1 after acceptance|Preserved N2 / N3','Reviewed IR2 extension|Stereo data + calibration|N4B inputs')
F[60]=flow('Stereo + motion|Bounded pairing|Tracking + workers|Fresh output')
F[62]=flow('Synthetic faults|Receiver semantics|Expected transitions|Tooling evidence')
F[63]=twoflows('Pi faults|Rejected perception|Optional-input fallback','Body IMU|Local controller|Local safety authority')
F[64]=flow('Raw + identities|Derived analysis|Actual review|Sealed acceptance')
F[65]=twoflows('Hardware / USB|Raw / clocks|Driver / ROS / QoS','Calibration|ORB / trajectory|Evaluation')
F[70]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]\node[box,font=\normalsize,text width=150mm,minimum height=22mm] {$E_i=Q_i^{-1}SP_i\qquad \mathrm{RMSE}=\sqrt{\frac{1}{N}\sum_i\|\operatorname{trans}(E_i)\|^2}$};\end{tikzpicture}'''
F[71]=r'''\begin{tikzpicture}[font=\normalsize,y=.70cm]\node[box,font=\normalsize,text width=150mm,minimum height=22mm] {$E_{ij}=(Q_i^{-1}Q_j)^{-1}(P_i^{-1}P_j)$\\[6pt]Same associated epochs; declared separation and pair policy.};\end{tikzpicture}'''
F[75]=flow('Timed health samples|Estimator events|Same-clock join|Trial summaries')
F[85]=flow('8 Sep: VM NO-GO|12 Sep: capture|13 Sep: power / USB faults|Fresh N0 restart')
images={1:'P01',4:'P02',10:'P03',12:'P04',19:'P05',24:'P06',29:'P07',37:'P08',51:'P09',59:'P10',67:'P11',87:'P12'}
subjects={1:'Conceptual perception platform',4:'Navigation context',10:'Visual and inertial motion cues',12:'D435i camera package',19:'Supply and cooling preparation',24:'Separate bulk-data storage',29:'Separate IMU mounting contexts',37:'Target-based calibration preparation',51:'Fresh preflight inspection',59:'Offline frozen-input analysis',67:'Bounded engineering task packet',87:'Conditional evidence journey'}
# Tables are semantic comparisons, not unverified results.
T={
14:[['Writer','Reader','Compatible'],['Best effort','Reliable','No'],['Reliable','Best effort','Yes'],['Volatile','Transient local','No']],
25:[['Identity','Retain'],['Source','Revision + dirty-file hashes'],['Runtime','Binary + library/package versions'],['Experiment','Settings + data + command hashes']],
33:[['Observation','What it establishes'],['Option enabled','Requested timestamp behavior'],['Frame domain','Per-frame clock classification'],['Mapped timestamp','Relationship with mapping uncertainty'],['Camera–IMU offset','Separate physical alignment measurement']],
35:[['Quantity','Current classification'],['Image projection','HISTORICAL SDK-provided profile'],['IMU geometry','HISTORICAL CAD fallback'],['IMU noise / offset','UNKNOWN; must measure'],['Stereo readiness','PLANNED separate qualification']],
39:[['Candidate','Role / remaining constraint'],['Kalibr','Spatial/time estimation; import/model/build'],['imu_utils','Noise analysis; precision/duration/build'],['Holdout checks','Residuals, repeatability and provenance']],
44:[['Settings group','Verify in pinned parser'],['Camera / Stereo','Projection, distortion, size/rate, rectification'],['IMU','T_b_c1, frequency, densities, walks'],['Features / viewer','Count, pyramid, thresholds, display load']],
54:[['Stream','Rate contract','Maximum gap'],['IR1','14.25–15.75 Hz','0.20 s'],['Gyro','190–210 Hz','0.05 s'],['Accel','95–105 Hz','0.05 s']],
66:[['Symptom','First discriminating evidence'],['480M / disconnect','Own branch + power/kernel logs'],['Topic silence','Graph + readback + QoS'],['Loss / failed initialization','Pairing + motion coverage + calibration']],
69:[['Campaign','Controlled question'],['EuRoC','Build / known-data estimator baseline'],['D435i offline/live','Input quality versus live scheduling'],['Health fixtures','Freshness and reset rejection']],
73:[['Event record','Required interpretation'],['First eligible input','Initialization-time origin'],['Tracking state / reset','Continuity and loss intervals'],['Pose epoch / output time','Coverage versus freshness']],
74:[['Metric','Required evidence'],['Latency percentiles','Named interval / clock / count'],['Loss','Sequence and count reconciliation'],['Queue depth / drops','Measured counter or UNKNOWN']],
80:[['Default','Evidence that changes it'],['Native Pi','Equivalent gates + packaging benefit'],['Direct USB3','Alternative topology sustains speed/power/load']],
81:[['Default','Evidence that changes it'],['Exact baseline profiles','Paired quality / tail-load comparison'],['Preserved emitter state','Separate controlled natural-feature trial'],['Logged global-time state','Measured domains/drift/offset evidence']],
82:[['Default','Evidence that changes it'],['Upstream then offline','Matched-data wrapper equivalence'],['Measured calibration/noise','Tool compatibility + holdout residuals'],['Defer wheel fusion','Synchronized geometry + slip evidence']],
83:[['Open choice','Evidence needed before design'],['Rate / transport','Useful cadence, load and link errors'],['Age threshold','Clock relation and receiver safety policy'],['Uncertainty','Estimator-supported interpretation']],
86:[['Layer','Current owner-confirmed status'],['Pi gates N0–N3','No PASS; restart fresh'],['Stereo/calibration N4','Unqualified / UNKNOWN'],['N5–N7','PLANNED; no measured results']]
}
def sentence_name(value):
    if value.startswith(('D435i','IMU','ROS','N0','N1','N2','N3','N4','N5','N6','N7')): return value
    return value[:1].lower()+value[1:]

def table(rows):
    k=len(rows[0]); widths=[182/k-4]*k
    out=r'\begin{tabular}{'+''.join('L{'+str(w)+'mm}' for w in widths)+r'}\toprule'+'\n'
    out+=' & '.join(r'\textbf{'+x+'}' for x in rows[0])+r'\\\midrule'+'\n'
    for row in rows[1:]: out+=' & '.join(esc(x) for x in row)+r'\\[5pt]'+'\n'
    return out+r'\bottomrule\end{tabular}'
def esc(s):
    s=re.sub(r'(?<!\\)_',r'\\_',s)
    return s.replace('&',r'\&').replace('%',r'\%').replace('≥',r'$\geq$').replace('≤',r'$\leq$').replace('→',r'$\rightarrow$').replace('×',r'$\times$').replace('τ',r'$\tau$').replace('α',r'$\alpha$').replace('°',r'$^\circ$')
def prose(s):
    expressions={'Z = f b / d':r'$Z=fb/d$', 'p_b = T_b_c1 p_c':r'$p_b=T_{b\_c1}p_c$', 'E_i = Q_i^{-1} S P_i':r'$E_i=Q_i^{-1}SP_i$', 'E_ij = (Q_i^{-1}Q_j)^{-1}(P_i^{-1}P_j)':r'$E_{ij}=(Q_i^{-1}Q_j)^{-1}(P_i^{-1}P_j)$', 'P_i':r'$P_i$', 'Q_i':r'$Q_i$'}
    saved=[]
    for a,b in sorted(expressions.items(),key=lambda item:-len(item[0])):
        if a in s:
            token=f'MATHPLACEHOLDER{len(saved)}'; saved.append((token,b)); s=s.replace(a,token)
    s=esc(s)
    for token,b in saved:s=s.replace(token,b)
    return s
out=[preamble,extra,r'\begin{document}',r'\raggedright']
for p,title,message,layout,sources in rows:
    out.append(f'% PAGE {p}: {title}\n% Source register: {sources}; see image-prompts/OUTLINE.md')
    if p==1:
        out.append(r'''\begin{frame}[c]\relax
{\centering\huge\bfseries\color{navy}WBR Perception Implementation\par}
{\centering\Large\color{teal}A gate-by-gate engineering guide\par}
\medskip{\color{teal}\hrule height .6pt}\vfill
\begin{columns}[T,onlytextwidth]\begin{column}{.48\textwidth}
\large Intel RealSense D435i\par\medskip
Raspberry Pi 5 / ROS 2 Jazzy\par\medskip
ORB-SLAM3 stereo-inertial\par\medskip
STM32H7 controller boundary\par\medskip
\normalsize Figure~\ref{fig:P01} identifies the conceptual platform.
\end{column}\begin{column}{.48\textwidth}
\coursefigure{P01}{\slideimg[.42\textheight]{\linewidth}{P01}{Conceptual perception platform}}{Platform objects; no validation claim.}
\end{column}\end{columns}\vfill
{\centering\color{muted}Engineering and evidence snapshot\quad 10 October 2026\par}
\note{Owner, lecturer and senior audience. No invented identity or affiliation. The owner confirms no Pi gate has passed; restart at N0. Figure is conceptual.}
\end{frame}''');continue
    if p==2:
        out.append(r'\begin{frame}{Contents}\begin{tikzpicture}')
        for i,s in enumerate(['Introduction','Background','System design','Implementation by gate','Evaluation method','Engineering decisions','Current status and roadmap','Conclusion'],1):
            y=-i*.99
            out.append(r'\node[fill=navy!6,rounded corners=3pt,minimum width=190mm,minimum height=8mm,anchor=west] at '+f'(0,{y}) '+'{};')
            out.append(r'\node[fill=navy,text=white,minimum width=10mm,minimum height=8mm,anchor=west,font=\large\bfseries] at '+f'(0,{y}) '+'{'+str(i)+'};')
            out.append(r'\node[anchor=west,text=navy,font=\large] at '+f'(1.5,{y}) '+'{'+s+'};')
        out.append(r'\end{tikzpicture}\end{frame}');continue
    if p in [3,8,16,49,68,79,84]:
        out.append(r'\section{'+title.split('. ',1)[1]+'}');continue
    if p==89: continue
    bullets,take,notes,status=D[p]
    out.append(r'\begin{frame}{'+title+r'}\evidence{'+status+'}')
    if p in images:
        pid=images[p]
        if p in [51,59]:
            out.append(r'\deckitems{'+''.join(r'\item '+prose(b) for b in bullets[:2])+r'}\medskip')
            bullets=bullets[2:]
        out.append(r'\begin{columns}[T,onlytextwidth]\begin{column}{.48\textwidth}\deckitems{'+''.join(r'\item '+prose(b) for b in bullets)+r'}\medskip Figure~\ref{fig:'+pid+r'} illustrates '+sentence_name(subjects[p])+r'.\end{column}\begin{column}{.48\textwidth}')
        out.append(r'\coursefigure{'+pid+r'}{\slideimg['+('.36' if p in [51,59] else '.49')+r'\textheight]{\linewidth}{'+pid+'}{'+subjects[p]+'}}{'+subjects[p]+r'; conceptual.}\end{column}\end{columns}')
    else:
        out.append(r'\deckitems{'+''.join(r'\item '+prose(b) for b in bullets)+'}')
        out.append(r'\vfill')
        if p in T: out.append(table(T[p]))
        elif p in F:
            key=f'D{p:02}'
            out.append(r'\coursefigure{'+key+'}{'+F[p]+'}{'+title.split(' ',1)[1]+r'; schematic.}')
        elif p in [76,77,78]:
            key=f'D{p:02}'
            panels={76:[('ATE translation (m)',0,0),('RPE translation (m)',9,0)],77:[('Latency (ms)',0,0),('Queue (messages)',6,0),('Loss (frames)',12,0)],78:[('CPU load (%)',0,0),('Frequency (Hz)',6,0),('Temperature (°C)',12,0),('Memory (MiB)',3,-2.7),('Throttle flags',9,-2.7)]}[p]
            chart=r'\begin{tikzpicture}[font=\normalsize,y=.60cm]'
            width=7 if p==76 else 4.7
            for label,x,y in panels:
                chart+=r'\draw[flow] '+f'({x},{y})--({x+width},{y})'+r';\draw[flow] '+f'({x},{y})--({x},{y+1.3})'+r';\node[anchor=south west] at '+f'({x},{y+1.4})'+'{'+esc(label)+'};'
            chart+=r'\node[text=muted] at '+('(8,-4)' if p==78 else '(8,-1)')+r' {To be filled after N4/N5 runs};\end{tikzpicture}'
            out.append(r'Figure~\ref{fig:'+key+r'} reserves axes without fabricated samples.\par\medskip\coursefigure{'+key+'}{'+chart+'}{'+title.split(' ',1)[1]+r'; no measured data.}')
        else:
            # Text-only pages use a second substantive question block.
            text={6:'Acceptance connects each objective to artifacts, failure cases and owner review.',7:'The answer must include failed runs, unknown counters and the limits of each claim.',15:'Compare build/configuration and estimator behavior before involving live capture.',23:'Qualify sustained recording under real load; theoretical USB speed is not available throughput.',58:'Check initialization, trajectory coverage and reference errors after every trial.',61:'Declare budgets and exclusions before inspecting results.',72:'Preserve original exports; conversion must be auditable and independently checked.',88:'The owner gains a bounded sequence for directing agents and interpreting evidence.'}.get(p,'Require source, context, negative cases and owner acceptance for every claim.')
            out.append(r'\begin{block}{Engineering decision}'+text+r'\end{block}')
    out.append(r'\vfill\takeaway{'+prose(take)+'}')
    # Notes preserve local provenance without cluttering the main page.
    out.append(r'\note{'+esc(notes)+' Source register: '+sources+r'. '+esc(message)+r'}\end{frame}')
# One primary-reference page, inherited 12 pt body elsewhere.
refs=[('orb','Campos, Elvira, Gómez Rodríguez, Montiel, Tardós. ORB-SLAM3. arXiv:2007.11898v2, 2021.','https://arxiv.org/abs/2007.11898'),('euroc','Burri et al. The EuRoC micro aerial vehicle datasets. International Journal of Robotics Research, 2016.','https://projects.asl.ethz.ch/datasets/euroc-mav/'),('ros','ROS 2 Jazzy: Quality of Service documentation.','https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html'),('rep','ROS REP-103 / REP-105: units, coordinates and frames.','https://www.ros.org/reps/rep-0105.html'),('sdk','RealSense librealsense v2.58.4: timestamp reader and calibration parser.','https://github.com/realsenseai/librealsense/tree/v2.58.4'),('kalibr','ETH Zürich ASL: Kalibr camera–IMU calibration.','https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration'),('imu','gaowenliang: imu_utils maintainer documentation.','https://github.com/gaowenliang/imu_utils'),('evo','Michael Grupp: evo trajectory metrics.','https://github.com/MichaelGrupp/evo/wiki/Metrics'),('hardware','Raspberry Pi 5 / Active Cooler and RealSense D435i vendor records.','https://www.raspberrypi.com/products/raspberry-pi-5/')]
out.append(r'\begin{frame}{References}\footnotesize\begin{columns}[T,onlytextwidth]')
for chunk in [refs[:5],refs[5:]]:
    out.append(r'\begin{column}{.48\textwidth}')
    for key,text,url in chunk:
        out.append(r'\par\medskip\textbf{['+str(refs.index((key,text,url))+1)+r']} '+esc(text)+r' \href{'+url+r'}{Primary source}.'+ (r' \href{https://www.intel.com/content/www/us/en/products/sku/190004/intel-realsense-depth-camera-d435i/specifications.html}{D435i record}.' if key=='hardware' else ''))
    out.append(r'\end{column}')
out.append(r'\end{columns}\vfill\normalsize Methods are published; project results remain unmeasured.\end{frame}\end{document}')
# Insert moderate numbered citations in relevant claims; no invented metadata.
citations={9:1,10:1,11:1,12:9,13:3,14:3,15:2,19:9,26:4,27:4,28:4,33:5,36:6,37:6,38:7,39:6,40:1,41:1,42:1,43:1,58:2,70:8,71:8,72:8}
text='\n'.join(out)
for p,ref in citations.items():
    start=text.index(f'% PAGE {p}:'); end=text.find('% PAGE ',start+1)
    chunk=text[start:end]
    # A hyperlinked numbered reference on first bullet is enough, without undefined bib entries.
    first=chunk.find(r'\item '); stop=chunk.find(r'\item ',first+6)
    if stop<0: stop=chunk.find('}\\medskip',first)
    if stop>0: chunk=chunk[:stop]+r' \hyperlink{referencepage}{['+str(ref)+']} '+chunk[stop:]
    text=text[:start]+chunk+text[end:]
text=text.replace(r'\begin{frame}{References}',r'\begin{frame}{References}\hypertarget{referencepage}{}')
from phase3_depth import revise
text = revise(text)
from phase6_curate import revise as curate
text = curate(text)
from phase7_rpe import revise as fill_rpe
text = fill_rpe(text)
(ROOT/'main.tex').write_text(text)
(ROOT/'qa/PAGE_LIST.md').write_text('\n'.join(f'{p}. {t}' for p,t,*_ in rows)+'\n')
print('Wrote Phase-3 main.tex; inherited OS preamble and original illustration slots.')
