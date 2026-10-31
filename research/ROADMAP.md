# WBR research roadmap

Prepared 2026-10-31. Three programs add visible capabilities while keeping the wheel-bipedal robot (WBR) safety boundary intact. The WBR uses DM motors over CAN; it has no micro-ROS. RobStride plus micro-ROS is a separate AGV. The STM32 owns balance and motor safety. Pi, learned, remote, and simulated outputs never command motors directly.

## Program 1 — “Go to the red box”: grounded, freshness-aware autonomy

### Visible demo

On a screen, say “go to the red box.” The display highlights the selected object in a recorded RGB-D view, places its estimated 3D location on the ORB-SLAM3 map, and draws a simulated route. It also shows confidence, capture-to-result age, and a clear `STALE`, `AMBIGUOUS`, or `RELOCALIZE` refusal. Start with replay and Nav2 simulation; this is not a claim of WBR navigation. The 24 Oct bags show tabletop objects, not a navigation sequence or moving person.

### Research question + measures

Does an explicit age and uncertainty contract prevent false or stale semantic goals during compute and network delay, while keeping useful-goal coverage? Compare the same annotated frames with and without age-aware rejection, then compare local and remote inference if server access is available. Measure target identity and 3D position against manual labels, false-goal and abstention rates, valid-goal coverage, stale-result rejection, camera-to-goal age (p50/p95/p99), map-reset recovery, CPU/RAM, network bytes, and end-to-end delay. A result with no reduction in accepted stale/false goals, or with unusably low coverage, says this design has no demonstrated benefit. Report replay and live Pi results separately.

### 2-week prototype on our rig

1. **Days 1–2 — freeze data and labels.** Inventory 24 Oct D435i bags, timestamps, calibration, and the depth scale; label a fixed set of target frames and freeze scoring rules. Existing evidence: [P1 measured results](explore/p1/RESULTS.md) and [bag reader / run protocol](explore/p1/README.md). COCO YOLO11n at 640 px measured 22.4 FPS model-only and 18.8 FPS full pipeline on the Mac; Pi 5 CPU measured 2.43 FPS at 1 thread and 3.43 FPS at 4. On the live Pi Camera v2 (31 Oct, 1280×720 via `rpicam-vid`, 100 frames, performance governor, throttled=0x0), end-to-end capture + inference + NMS ran at 2.40 FPS (1 thread) and 3.38 FPS (4 threads). Capture costs only ~4 ms, so inference is the whole bottleneck ([live results](explore/p1/RESULTS.md#live-pi-camera-v2-2026-10-31)). It found zero books in B-H05; COCO has no box or step class. Do not treat these as a useful WBR detector.
2. **Days 3–5 — replay goal grounding.** Add phrase-to-object selection, 3D projection, confidence, source stamp, sequence/session, and expiry. Save annotated frames, a target/pose CSV, and false-goal/abstention counts. Use open-vocabulary inference or manual labels for the tabletop proof; retain depth geometry for metric distance.
3. **Days 6–8 — freshness and refusal.** Inject delayed, reordered, duplicated, missing, and expired results plus an ORB reset. Save a replay receipt with every invalid goal rejected and a status overlay showing why.
4. **Days 9–11 — route display.** Feed only valid goals into Nav2 simulation; save a screen recording, route/target overlay, and per-run metrics. Invalid or expired goals must never reach the planner.
5. **Days 12–14 — edge comparison.** If lab access is available, replay the same workload on Pi 5 + D435i under ORB-SLAM3 and record camera-to-goal age, CPU/RAM, temperature, and dropped work. If an edge server is available, compare timestamped low-rate offload on the same frames. Deliver raw CSVs, bag IDs/hashes, overlays, and a go/no-go note. No physical navigation is in this prototype.

### Hardware / compute

- **Mac i9, 16 GB:** bag inspection, annotation, CPU baselines, plots, and Nav2 replay; best development machine already available.
- **Pi 5, 8 GB + Pi Camera v2 (imx219):** ROS, ORB-SLAM3, local depth/geometry, and freshness refusal. The measured YOLO11n CPU rate is only 3.43 FPS at four threads before concurrent SLAM; do not schedule it as a continuous detector. D435i is available only at lab visits; 24 Oct D435i bags already exist.
- **Brother’s i7, 32 GB, RTX 3060 Laptop 6 GB:** optional short CUDA inference/export or fine-tuning comparison; not robot-latency evidence.
- **Chợ Mơ café:** Private RTX 4060 8 GB for a prepared local model/export trial; Training RTX 3060 12 GB for a larger batch or fine-tune; Stadium RTX 4090 24 GB only if measured model work needs it. Sessions are 2–4 h, no admin, and files reset at shutdown, so export all artifacts before shutdown. ×3 credit is not assumed available.
- **Kaggle/Colab free GPU:** optional offline model comparison/fine-tuning; copy checkpoints, labels, and logs to persistent storage. It cannot measure camera-to-goal latency on the WBR network.

### Risk (top 2–3) + mitigation

- **Tabletop data can make the demo look more capable than it is.** Label the replay scope and show refusals; obtain new navigation scenes before a navigation claim.
- **Slow/mismatched detector.** Use manual/open-vocabulary labels for the first demo and geometric depth for obstacle distance; measure any new model end to end under ORB load.
- **Late or wrong semantic result becomes a goal.** Require frame age, identity, sequence, confidence, and expiry; reject on delay, ambiguity, or SLAM reset. STM32 remains the balance and motor-safety authority.

## Program 2 — RL locomotion: learn a speed governor, then negotiate terrain

Owner reopened the RL research track on 30 Oct. The G1 governor experiment is the first step; stopped PPO v3 remains stopped.

### Visible demo

First show a learned bounded speed-reference governor beside its fixed baseline in simulation: command speed, robot motion, pitch, tracking error, and safety-limit status are visible together. Then run it in the merged T1–T5 bench twin package (#182–#185, #187): the 3D MuJoCo model stands, drives, and clears an 8 cm box; T2 keyboard/UDP teleoperation is owner-verified; T3–T5 add the bench firmware, Foxglove layout, and lab-day script. The later demo is a local height patch, selected step mode, and bounded step negotiation. Neither the twin’s jump nor an RL result establishes physical WBR capability.

### Research question + measures

Does the G1 learned governor improve command tracking or recovery over its frozen fixed baseline under the same disturbances and delays without worsening strict balance outcomes? Compare paired held-out cases and seeds. Measure strict success, falls, normalized position/speed/pitch/rate error, recovery time, action/slew limits, delay strata, completed policy transitions/s, and update/evaluation wall time. The result is “no demonstrated RL benefit” if the baseline has no headroom, the frozen benefit criterion is missed, precision or survival regresses, or the run is incomplete. G1 is an experiment, not a result: the source and Kaggle/Colab notebooks are on unmerged `origin/claude1/20261031-rl-g1`; owner runs are pending. Its Mac smoke measured 338.8 transitions/s; a separate five-process timing window measured 416.6 aggregate transitions/s. Those are throughput measurements, not learned-policy results; laptop execution was assessed NO-GO and no final policies exist. The candidate is an assumed planar model, so keep it distinct from the 3D twin until a matched integration is built.

### 2-week prototype on our rig

1. **Days 1–2 — run the prepared G1 experiment.** Owner runs the frozen Kaggle or Colab notebook; preserve notebook output, source/model/config hashes, checkpoints, failures, and `run-manifest.json`. Branch instructions/artifacts: [`sim/rl/g1/README.md`](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/tree/claude1/20261031-rl-g1/sim/rl/g1) and [`cloud/CLOUD_README.md`](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/blob/claude1/20261031-rl-g1/sim/rl/g1/cloud/CLOUD_README.md). Do not call a smoke or timing run an RL result.
2. **Days 3–4 — inspect the paired evaluation.** Retain all five seed outcomes and the frozen held-out cases; publish strict/survival/error tables and run timing. Incomplete or readiness-blocked runs remain `PARTIAL`/blocked, not a pass.
3. **Days 5–7 — connect governor to the 3D twin.** Define a separate interface from desired speed to bounded speed-reference adjustment; run the same commands and disturbances with the fixed governor and the learned governor. Save code/config hashes, CSV traces, and a side-by-side viewer recording. Do not reuse the planar G1 scores as twin evidence.
4. **Days 8–10 — evaluate 3D simulation.** Use [`sim/twin3d/run.py`](../sim/twin3d/run.py) and the saved T1 evidence in [`docs/twin3d/`](../docs/twin3d/README.md); record matched flat-floor and perturbation panels, falls, pitch, speed error, and compute. T1 is a reduced virtual-leg model with assumed parameters, not a calibrated five-bar WBR model.
5. **Days 11–14 — freeze next rung or stop.** If governor benefit survives paired cases, specify model/data needed for a five-bar/contact twin and low-step task; keep the existing 3D twin as today’s simulation base while recording its limits. If benefit is absent, freeze the result and revise the research question before new training. Any eventual physical test requires separately commissioned hardware, a verified STM32 fallback, and owner-approved trial conditions.

### Hardware / compute

- **Mac i9, 16 GB:** twin development, visualization, small CPU MuJoCo runs, and final result inspection. The 3D twin uses assumed geometry and virtual legs; it is a useful interactive simulation, not the final calibrated plant.
- **Pi 5, 8 GB + Pi Camera v2:** future policy inference and sensor-age profiling only; not large-scale training. Use D435i sensor recordings only during lab visits.
- **Brother’s i7, 32 GB, RTX 3060 Laptop 6 GB:** G1’s CPU PPO/MuJoCo is the relevant option only after measured throughput and offline execution checks; the GPU does not accelerate ordinary MuJoCo CPU physics. It can host later CUDA batch work if required.
- **Chợ Mơ café:** Private RTX 4060 8 GB, Training RTX 3060 12 GB, Stadium RTX 4090 24 GB (×3 credit only, if confirmed). Current G1 is CPU-first, so use the Mac or laptop for it; use Training/Stadium only for a later measured GPU-batched simulator that actually benefits. Sessions are 2–4 h, no admin; export before shutdown because files reset.
- **Kaggle/Colab free GPU:** current first step is the prepared G1 notebook run and artifact return; save outputs/checkpoints off the ephemeral session. Use only for this frozen experiment, not new tuning. GPU notebook success does not prove Pi inference or hardware transfer.

### Risk (top 2–3) + mitigation

- **G1 branch is unmerged and owner runs are pending.** Treat its notebook as prepared code only; preserve exact revisions and run receipts before drawing conclusions.
- **Simulation mismatch.** Keep legacy planar, reduced 3D twin, and future five-bar model results separate; label every assumption and compare only matched controllers within a model.
- **Unsafe transfer.** STM32 owns balance and motor safety; learned/remote policy output is bounded advisory input only. No direct motor command or hardware trial follows from a simulation pass.

## Program 3 — SLAM + AI: learned relocalization and semantic map sidecar

### Visible demo

Replay a D435i sequence on screen with ORB-SLAM3 pose and map points. When tracking degrades, show a learned-feature sidecar proposing keyframe matches, stereo geometry checking them, and a recovered ORB tracking state—or a clear rejection. Add object labels as a separate semantic layer. ORB-SLAM3 remains the metric pose authority; the sidecar never silently changes its map or publishes an unverified pose.

### Research question + measures

Does a low-rate learned keyframe matcher improve recovery after induced ORB tracking loss, without increasing stale pose output or exhausting the Pi’s tracking budget? Separately, does conservative dynamic masking reduce moving-object map contamination without causing tracking loss? Compare ORB-only against logged proposals, then geometrically verified proposals; test masks on a repeatable person-crossing sequence when available. Measure recovered losses/attempt, false accepted matches, tracked-frame fraction, map-point persistence/contamination, p50/p95/p99 inference and pose age, dropped frames, CPU/RAM/temperature, and reset/relocalization time. If recovery does not improve or any stale pose / tracking loss increases, retain ORB-only. No ground-truth trajectory accuracy claim without ground truth.

### 2-week prototype on our rig

1. **Days 1–2 — freeze ORB baseline.** Replay a hashed 24 Oct bag and save trajectory, tracked/lost state, map-point count, per-frame latency, and CPU/RAM/temperature. Existing evidence includes Pi/D435i stereo capture and ORB initialization, a 20 s replay with 300 poses/20 point clouds, and an ORB MapPoint cloud sidecar; live continuity and full-duration behavior remain unverified. See [`ops/worklog/CURRENT.md`](../ops/worklog/CURRENT.md) and [`MAP_POINTS.md`](../ros2/wbr_orb_node/MAP_POINTS.md).
2. **Days 3–5 — learned feature proposals.** Run XFeat on sampled adjacent/keyframe pairs on Mac; compare with ORB features after the same stereo/RANSAC verifier. Save matches, inlier ratios, per-pair timing, and difficult-pair overlays. Proposals remain offline and cannot change ORB state.
3. **Days 6–8 — induce and recover.** On replay, induce or select tracking-loss segments; invoke the sidecar only at loss/keyframes, geometrically verify, and log candidate versus accepted recovery. Deliver a side-by-side map/trajectory video and recovery table.
4. **Days 9–11 — dynamic scene.** If a lab recording is available, capture/replay a person crossing the view and compare no mask, geometric rejection, and conservative semantic mask. Keep mask production asynchronous; drop masks past their age limit. Without person data, mark this comparison unavailable.
5. **Days 12–14 — Pi budget and decision.** At a D435i lab visit, run ORB and sidecar under the same ROS workload; save latency percentiles, pose age, missed frames, and thermal data. Decide using successful recoveries per induced loss with no increase in stale pose output. Deliver scripts/config, bag hashes, CSVs, overlays, and limitations. No motor or STM32 change.

### Hardware / compute

- **Mac i9, 16 GB:** bag replay, XFeat/LightGlue CPU experiments, ORB trajectory analysis, overlays, and plots.
- **Pi 5, 8 GB + Pi Camera v2 (imx219):** preserve ORB-SLAM3 as primary pose source; profile a low-rate feature/mask sidecar under the real ROS load. D435i is lab-visit-only; 24 Oct D435i bags are available for replay. Pi feature/SLAM FPS is not established by published GPU results.
- **Brother’s i7, 32 GB, RTX 3060 Laptop 6 GB:** batch learned feature extraction or GPU-only DROID/DPV comparison; results are a research comparator, not Pi real-time evidence.
- **Chợ Mơ café:** Private RTX 4060 8 GB or Training RTX 3060 12 GB for prepared feature-model comparison; Stadium RTX 4090 24 GB only for a measured GPU memory/throughput need. Use 2–4 h no-admin sessions, and export all source, weights, and results before shutdown resets files. ×3 credit is not assumed.
- **Kaggle/Colab free GPU:** optional offline keyframe/feature or DROID/DPV comparisons on saved bags, with artifacts copied to persistent storage. Do not offload live pose authority to a notebook.

### Risk (top 2–3) + mitigation

- **Pairwise matches may not improve SLAM.** Count accepted recoveries and map behavior, not match scores alone; keep ORB map updates disabled until a later reviewed integration.
- **Compute contention makes pose stale.** Run asynchronous, low-rate proposals and reject results by capture age/sequence; retain ORB-only tracking when late.
- **Static tabletop bags do not test moving people or robot vibration.** Label those limits; obtain a repeatable dynamic recording and later hardware run before claiming robustness.

## Start order

| Program | First step this week | Owner action needed |
|---|---|---|
| 1. Grounded autonomy | Freeze labels and scoring from the 24 Oct bags; use measured P1 results as the detector baseline. | Provide/request access to the existing edge-AI server if remote inference is to be compared; otherwise proceed with replay labels. |
| 2. RL locomotion | Run the prepared G1 Kaggle or Colab notebook and return its full run artifacts; then port the governor comparison to the 3D twin. | Run the prepared G1 notebook; preserve notebook output, checkpoints, hashes, and metrics. |
| 3. SLAM + AI | Freeze an ORB-SLAM3 replay baseline, then log XFeat proposals without modifying ORB map state. | Schedule a D435i lab visit for a fresh person-crossing and Pi-load comparison when convenient. |

## Sources

- [Visual Language Maps for Robot Navigation (ICRA 2023)](https://arxiv.org/abs/2210.05714)
- [ORB-SLAM3 (IEEE T-RO 2021)](https://doi.org/10.1109/TRO.2021.3075644)
- [Computation Offloading and Information Freshness in Edge-Assisted Networked Robotic Systems (Frontiers in Robotics and AI, 2026, accepted)](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2026.1999591/abstract)
- [Fast Traversability Estimation for Wild Visual Navigation (RSS 2023)](https://www.roboticsproceedings.org/rss19/p054.html)
- [Learning robust autonomous navigation and locomotion for wheeled-legged robots (Science Robotics 2024)](https://arxiv.org/abs/2405.01792)
- [Learning robust perceptive locomotion for quadrupedal robots in the wild (Science Robotics 2022)](https://doi.org/10.1126/scirobotics.abk2822)
- [MuJoCo Playground](https://github.com/google-deepmind/mujoco_playground)
- [XFeat: Accelerated Features for Lightweight Image Matching (CVPR 2024)](https://openaccess.thecvf.com/content/CVPR2024/papers/Potje_XFeat_Accelerated_Features_for_Lightweight_Image_Matching_CVPR_2024_paper.pdf)
- [DynaSLAM (IEEE RA-L 2018)](https://arxiv.org/abs/1806.05620)
- [Raspberry Pi AI HAT documentation](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html)

**Citation spot-check (Claude 2, 31 Oct, live web fetch): 5 of 5 PASS.** Title, first author and venue matched for VLMaps (Huang, ICRA 2023), wheeled-legged navigation and locomotion (Lee, Science Robotics 9(89) 2024), Wild Visual Navigation (Frey, RSS XIX 2023), DynaSLAM (Bescos, RA-L 3(4) 2018) and the information-freshness paper (Jeon, Frontiers in Robotics and AI 13, accepted 15 Oct 2026, final version pending). All other sources are VERIFIED in [explore/CITATION_CHECK.md](explore/CITATION_CHECK.md).
