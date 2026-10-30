# X3 — Learned visual SLAM for the WBR

**Decision in one line:** keep ORB-SLAM3 as the robot's metric pose source; prototype learned features as a recovery/relocalization sidecar and semantic dynamic-object filtering as a controlled A/B. Do not replace the live SLAM stack with DROID-SLAM or DPV-SLAM on the Pi.

## 1. State of the art

| Work (venue/year) | What it contributes | WBR relevance / limit |
|---|---|---|
| [SuperPoint: Self-Supervised Interest Point Detection and Description](https://openaccess.thecvf.com/content_cvpr_2018_workshops/papers/w9/DeTone_SuperPoint_Self-Supervised_Interest_CVPR_2018_paper.pdf), CVPR Workshop 2018 | Learned keypoints and descriptors from synthetic pretraining plus homographic adaptation. | Candidate frontend; inference and licensing/deployment need checking on ARM. |
| [DynaSLAM: Tracking, Mapping and Inpainting in Dynamic Scenes](https://arxiv.org/abs/1806.05620), IEEE RA-L 2018 | Extends ORB-SLAM2 with multi-view geometry and/or learned masks to reject dynamic objects; evaluates monocular, stereo, RGB-D. | Direct precedent for people/objects corrupting the map. Masking every potentially movable class can discard useful static features. |
| [ORB-SLAM3](https://doi.org/10.1109/TRO.2021.3075644), IEEE T-RO 2021 | Mature visual, visual-inertial and multi-map SLAM for stereo/RGB-D as well as monocular cameras. | Our operational baseline; learned matching is not a drop-in replacement because the tracking, map-point, loop-closure and vocabulary interfaces are coupled. |
| [DROID-SLAM: Deep Visual SLAM for Monocular, Stereo, and RGB-D Cameras](https://arxiv.org/abs/2108.10869), NeurIPS 2021 | Recurrent neural pose/depth updates with dense bundle adjustment; supports stereo/RGB-D at inference. | Strong research comparator, but neural dense optimization is GPU-oriented; not a credible Pi 5 CPU real-time target. |
| [LightGlue: Local Feature Matching at Light Speed](https://openaccess.thecvf.com/content/ICCV2023/papers/Lindenberger_LightGlue_Local_Feature_Matching_at_Light_Speed_ICCV_2023_paper.pdf), ICCV 2023 | Adaptive learned sparse matcher with SuperPoint, DISK, ALIKED or SIFT features. | Useful for difficult keyframe/relocalization pairs; published gains are image matching/pose-estimation benchmarks, not proof of improved online SLAM. |
| [XFeat: Accelerated Features for Lightweight Image Matching](https://openaccess.thecvf.com/content/CVPR2024/papers/Potje_XFeat_Accelerated_Features_for_Lightweight_Image_Matching_CVPR_2024_paper.pdf), CVPR 2024 | Sparse and semi-dense learned features; paper reports real-time CPU matching at VGA on Intel i5-1135G7, up to 5× faster than compared learned methods. | Best low-cost learned-feature candidate to profile on Pi and Mac. The paper's laptop result does not transfer to ARM; its matcher is not a full SLAM system. |
| [Deep Patch Visual SLAM (DPV-SLAM)](https://arxiv.org/abs/2408.01654), ECCV 2024 | Adds loop closure to DPVO; reports 1–4× real-time on tested datasets, 2.5× DROID speed on EuRoC, and 5–7 GB GPU memory. | Valuable GPU research baseline, not Pi 5 CPU/8 GB RAM deployment evidence. |

## 2. What would look “wow” in a demo

- Show the live stereo camera, ORB pose/map, and boxes/person labels together; highlight points excluded as dynamic and show a stable static map while a person crosses the view.
- Walk out of view and return to a mapped area: visualize relocalization, the recovered trajectory and map continuity. A learned keyframe matcher can be shown proposing correspondences, with geometric verification and ORB-SLAM3 still deciding whether to accept them.
- Overlay object identities/labels on the existing box-scene RGB-D recordings, then compare trajectories and map points with semantic filtering on/off.

This is a visible capability upgrade only if the baseline exhibits the targeted failure. The 24 Oct table-and-box bags are useful for repeatable geometry and static-map tests; they do not by themselves establish robustness to moving people, long occlusion or outdoor lighting.

## 3. Researchable question and likely practical value

**Question:** on this camera and WBR motion, does a low-rate learned keyframe matcher improve recovery after brief visual degradation, and does conservative dynamic masking reduce map contamination without causing tracking loss?

1. **Most practical:** dynamic-feature rejection when people or carried objects move through view. Depth geometry may help distinguish inconsistent/moving foreground from the static scene; semantic masks alone mark an object class, not whether that instance is actually moving.
2. **Next:** learned features as a *separate* relocalization proposal path after ORB tracking loss. Verify proposals with stereo geometry / RANSAC and compare recovery success and latency. This avoids first rewriting ORB's tightly coupled map frontend.
3. **Lower priority:** replacing ORB features throughout the SLAM system. It requires integration across keyframes, map points, descriptors, loop closure and relocalization; a better pairwise matcher score alone does not prove better trajectory or map quality.
4. **Not a near-term WBR gain:** running DROID/DPV as the sole online estimator on Pi CPU. Their published results use GPU platforms and provide no Pi 5 CPU rate. They are useful offline comparators on a CUDA lab machine.

Novelty should be framed narrowly: characterize learned-recovery and conservative dynamic filtering under wheel-biped vibration, motion blur, low camera height and compute/freshness limits. These combinations are hypotheses to test, not established research gaps. Compare trajectory error only when ground truth exists; otherwise report tracked-frame fraction, relocalization success, map-point persistence/contamination, end-to-end latency and dropped frames, with limitations explicit.

## 4. Feasibility by platform

| Platform | Feasible now / later | Compute facts and caveats |
|---|---|---|
| Pi 5 8 GB, CPU, D435i | Keep ORB-SLAM3 stereo + ROS as primary. Run XFeat at low rate or on selected keyframes as an experiment; test a small detector for masks asynchronously. | Our project evidence already has stereo capture, ORB initialization and 20 s replay with 300 poses/20 clouds; it also records that live continuity and full-duration behavior remain unverified. No opened primary source reports XFeat, LightGlue, DROID or DPV FPS on this Pi. Measure on the actual ROS load; do not infer from TOPS. |
| Pi 5 + Hailo-8L AI HAT+ | Could accelerate supported object detection/segmentation as a parallel mask producer. | Raspberry Pi documents Hailo-8L vision inference on Pi 5. This is not a general CUDA accelerator: DROID/DPV dense SLAM and arbitrary SuperPoint/LightGlue/XFeat pipelines are not established as supported Hailo workloads. No directly comparable SLAM FPS published. Request only if the semantic-filter experiment wins on CPU and model conversion is demonstrated. |
| Pi 5 + Hailo-8 AI HAT+ | More NPU capacity for supported neural vision than 8L; same split architecture. | Still does not accelerate ORB's CPU geometry or automatically run learned SLAM. Treat model/compiler support and end-to-end latency as gating unknowns. |
| Jetson Orin Nano Super | Best lab loan for DROID/DPV and end-to-end learned-feature tests; keep the safety/control path on STM32 and compare pose output to Pi. | NVIDIA advertises up to 67 sparse TOPS in Super mode; TOPS is not SLAM FPS. DROID/DPV paper rates are on their own GPU systems, not this board. Benchmark exact resolution, precision, power mode, and concurrent ROS workload. |
| Intel MacBook, no NVIDIA GPU | Offline replay, XFeat/LightGlue CPU development, plots, and bag analysis. | XFeat reports VGA results on a particular Intel i5 laptop; our Mac CPU and thermal state differ. DROID/DPV on CPU are development experiments, not assumed real-time. |
| Robot after Nov 2026: STM32H723 + BMI088, DM-J4310 hip and DM-H6215 wheel motors over CAN, five-bar; COBS+CRC UART advisory, no micro-ROS | A better IMU and real body vibration make visual-inertial calibration and robust feature tracking more relevant. Keep learned perception advisory and timestamped; MCU remains balance/motor authority. | Validate camera–IMU time offset/extrinsics, vibration blur, exposure, motion limits and compute contention on hardware. No results transfer automatically from the bench or static table bags. |

**Published performance comparison:** XFeat: reported VGA matching on Intel i5-1135G7 CPU (paper figure gives roughly 19 FPS semi-dense and 27 FPS sparse); DROID-SLAM: GPU-oriented recurrent dense SLAM, no Pi CPU figure found in the opened paper; DPV-SLAM: 1–4× real-time on paper's test setup, 5–7 GB GPU memory; Jetson Orin Nano Super: up to 67 sparse TOPS (vendor peak, not a SLAM benchmark); Pi 5 CPU and Pi+Hailo SLAM rates: **UNVERIFIED / not found in opened primary sources**. Do not compare these as equivalent workload rates.

## 5. Compute/hardware to request

- First request: scheduled access to the existing Pi/D435i and bags for repeatable replay plus a safe stationary/hand-carried test with a walking person. No new hardware is needed to establish whether dynamic masking or XFeat recovery helps.
- If the learned pipeline is useful but Pi CPU latency misses the camera budget, request a **Jetson Orin Nano Super loan** for GPU SLAM comparison and concurrent ROS profiling. Ask for the full kit, cooling and power supply; measure watts and thermal throttling as well as FPS.
- Request **Pi AI HAT+ Hailo-8L only** if lightweight segmentation/detection is the bottleneck and its exported model, mask timestamps and end-to-end Pi integration are proven first. Hailo may offload semantic masks, but should not be pitched as a learned-SLAM accelerator.
- No cloud/edge server is needed for the first prototype. Offloading features introduces image bandwidth and variable network delay; a late pose/mask can be worse than a local classical estimate. If later explored, send keyframes only and enforce the existing RTP freshness deadline, sequence IDs, age limits and fallback to ORB/STM32-safe behavior.

## 6. Two-week prototype using the rig and data

**Days 1–2 — Freeze baseline.** Select the 24 Oct RGB-D bag(s), list camera topics/rates and existing timestamps; replay unchanged ORB-SLAM3. Save trajectory, tracked/lost states, map-point count, per-frame latency percentiles and resource/thermal logs. Record exact command/config and bag hashes. Reuse existing saved-run validity limits; do not call trajectory “accuracy” without ground truth.

**Days 3–5 — Feature sidecar.** Run XFeat sparse extraction/matching on sampled adjacent and keyframe pairs from the bag on Mac and Pi. Compare against ORB correspondences using inlier count/ratio after the same geometric verifier, time per pair, memory, and behavior under exposure/viewpoint changes. Log proposals only; do not inject them into online mapping yet. Try LightGlue only if XFeat fails the difficult-pair test and its runtime is acceptable.

**Days 6–8 — Failure stimulus and dynamic masks.** Capture repeatable static-scene passes with boxes plus a person crossing/occluding, if lab access permits. Compare ORB baseline, geometric outlier rejection, and conservative person mask. Keep semantic inference asynchronous and record mask age; late masks are dropped. If no person recording is available, mark this leg blocked and do not claim dynamic-scene results from static boxes.

**Days 9–10 — Recovery A/B.** On replay, invoke the learned matcher only at ORB tracking loss or a selected keyframe interval; stereo-RANSAC verify, then report candidate and accepted relocalizations. Do not modify ORB map state for the prototype. Show a side-by-side trajectory/map/overlay demo and list each failure.

**Days 11–12 — On-Pi budget.** Repeat at camera resolution and operating rate under the actual ROS nodes. Report p50/p95/p99 latency, CPU/RAM, temperature/throttling, pose age and missed camera frames. Compare lower resolution and 1–5 Hz sidecar operation. If detector masks miss the budget, only then test a supported Hailo model (or request Jetson loan for DROID/DPV).

**Days 13–14 — Decide.** Use a predeclared primary metric: successful recoveries per induced loss, with zero increase in stale pose output; secondary metrics are static-map persistence and p95 compute latency. Retain ORB-only if gains are absent, fragile, or consume tracking budget. Deliver scripts/config, bag IDs, raw CSVs, overlays, limitations, and a go/no-go note. No robot motion command or STM32 change is part of this prototype.

## References / source status

All cited paper links above were opened. Additional primary software references: [official ORB-SLAM3 repository](https://github.com/UZ-SLAMLab/ORB_SLAM3), [official LightGlue repository](https://github.com/cvg/LightGlue), [official XFeat repository](https://github.com/verlab/accelerated_features), [official DPVO/DPV-SLAM repository](https://github.com/princeton-vl/DPVO), [Raspberry Pi Hailo AI documentation](https://www.raspberrypi.com/documentation/computers/ai.html), and [NVIDIA Orin Nano Super announcement](https://developer.nvidia.com/blog/?p=93942). These source performance claims are platform-specific; no apples-to-apples WBR comparison has yet been run.
