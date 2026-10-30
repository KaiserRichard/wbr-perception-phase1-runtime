# X4 — High-level autonomy and human–robot interaction

**Scope.** Language-grounded object-goal navigation, person following, navigation over uneven ground, and the edge-offload path. This is a research map and prototype proposal, not a motion authorization. The STM32 remains the balance and actuator authority; the Pi/server may propose goals and bounded navigation intents only.

## 1. State of the art: useful reference points

| Work | Contribution and relevance |
|---|---|
| Ahn et al., **“Do As I Can, Not As I Say” (SayCan)**, CoRL 2022, [paper/project](https://saycan-corl.github.io/) | Selects language-planned skills using both instruction relevance and estimated skill success. Key lesson: constrain language planning to a small, explicit skill/API set; a fluent plan is not evidence that a skill is safe or available. |
| Shah et al., **“LM-Nav: Robotic Navigation with Large Pre-Trained Models of Language, Vision, and Action”**, CoRL 2022, [PMLR paper](https://proceedings.mlr.press/v205/shah23b.html) | Composes a language model, image–language matching and a learned visual navigation model for long-horizon natural-language navigation on a real mobile robot. Strong precedent for modular “go to landmark” autonomy without end-to-end WBR training. |
| Driess et al., **“PaLM-E: An Embodied Multimodal Language Model”**, ICML 2023, [PMLR paper](https://proceedings.mlr.press/v202/driess23a.html) | Trains a large multimodal model on robot sensor inputs and tasks. Impressive embodied reasoning, but its scale/training/data make it a reference point, not a Pi deployment plan. |
| Huang et al., **“Visual Language Maps for Robot Navigation”**, ICRA 2023, [paper](https://arxiv.org/abs/2210.05714), [code](https://github.com/vlmaps/vlmaps) | Projects vision-language features into a 3D map, allowing open-vocabulary object and spatial queries to produce map locations. Closest precedent for “go to the red box” grounded in our RGB-D/SLAM map. Their repo notes real-robot navigation limitations; semantic localization does not solve traversability. |
| Brohan et al., **“RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control”**, CoRL 2023, [PMLR paper](https://proceedings.mlr.press/v229/zitkovich23a.html) | Joint vision-language-action model for robot manipulation. Demonstrates broad semantic transfer, but outputs embodied actions and assumes extensive data/compute; not appropriate as a WBR balance or motor controller. |
| Miki et al., **“Elevation Mapping for Locomotion and Navigation using GPU”**, IEEE/RSJ IROS 2022, [IEEE paper](https://ieeexplore.ieee.org/abstract/document/9981507/), [open preprint](https://arxiv.org/abs/2204.12876) | Maintains a geometric elevation map for navigation and legged locomotion, with GPU processing and robot demonstrations. Relevant to five-bar terrain, but GPU throughput and robot-specific foothold/control interfaces are not established on our Pi. |
| Nav2 maintainers, **“Dynamic Object Following”**, [Nav2 documentation source](https://github.com/ros-navigation/docs.nav2.org/blob/rolling/docs/tutorials/general_tutorials/navigation2_dynamic_point_following/navigation2_dynamic_point_following.md) (living docs; opened 2026-10-30) | Documents following a moving target pose using standard Nav2 planning/control and behavior-tree components; explicitly leaves target detection out of scope. A person detector/tracker must supply a stable, filtered target pose. |

## 2. What would look “wow” in a demo

1. **“Go to the red box, then stop beside it.”** The robot resolves an open-vocabulary phrase against a live RGB-D/SLAM map, displays the selected object and confidence, plans a path, then approaches only while local obstacle/freshness checks remain valid. Show the map, detections, selected target, path and changing status on one screen.
2. **“Follow me, keep a metre away.”** Person detector/tracker provides a target pose; Nav2 follows a filtered standoff point. Lost identity, occlusion, target jump or stale pose cancels following and requests a stop. Demo first with an operator-controlled wheeled base or simulation.
3. **“Go to the red box across the low step.”** Add an elevation/traversability layer and show the system choosing a geometrically feasible route, or explicitly refusing when clearance/height confidence is insufficient. For this WBR, an honest refusal on an unsupported obstacle is more credible than a language model claiming it can jump it.

The visible AI contribution is semantic goal selection and interaction. The actual motion remains a conventional, inspectable navigation stack; the current robot balance loop stays local to the MCU.

## 3. What is researchable for us

**Best-fit question:** can a freshness-aware, edge-offloaded semantic-goal system improve commandability while preventing stale or ambiguous scene interpretations from becoming navigation goals on a resource-limited WBR?

- Compare a fixed closed-set detector (“red box” from known labels) with an offloaded open-vocabulary/VLM query on the same recorded RGB-D scenes. Score target grounding, false-goal rate, abstention, capture-to-result age, network bytes, and CPU load. Use an operator-confirmed target as ground truth.
- Add map/pose uncertainty and semantic-target age to the goal contract. Require target identity, 3D position, frame, capture stamp, sequence/session, confidence, and expiry; reject late, reordered, or untransformable results. On expiry or SLAM reset, discard the goal and show `STALE/RELOCALIZE`.
- Compare target-only semantic grounding against geometry-aware navigation with the depth obstacle detector/elevation layer. Measure goal completion in replay/simulation, minimum clearance, false stops, stale-result rejection, and age percentiles under bandwidth/compute contention.
- Novelty risk is **high** for generic language navigation, VLMaps or Nav2 person following. A defensible contribution would be the measured freshness/uncertainty contract across the VLM–SLAM–Nav2–MCU boundary on a resource-constrained wheel-biped, validated on the arriving platform. Until then, pitch this as a prototype study, not a confirmed research gap.

## 4. Feasibility on our hardware

| Platform | Plausible role | Published compute evidence and limit |
|---|---|---|
| Pi 5 8 GB, CPU only | ROS 2, ORB-SLAM3, depth geometry, command parser, low-rate small detector, target/map glue. Start here; do not run a large VLM in the control path. | Ultralytics’ [Pi 5 benchmark](https://docs.ultralytics.com/guides/raspberry-pi) reports YOLO26n at **7.79 FPS** and YOLO11n at **6.79 FPS** at 640 input with ONNX. This is detector-only benchmark data, not concurrent ORB-SLAM3 + Nav2 throughput; measure end-to-end load on our Pi. |
| Pi 5 + Hailo-8L AI HAT+ | Accelerate supported vision models (detection/segmentation); CPU remains responsible for ROS and mapping. | Raspberry Pi documents the AI Kit/HAT+ Hailo-8L at **13 TOPS**; that TOPS figure is not an FPS or a VLM benchmark. Model conversion/support and the full camera-to-goal latency need testing. [Official docs](https://www.raspberrypi.com/documentation/computers/ai.html) |
| Pi 5 + AI HAT+ 2 (Hailo-10H) | Candidate local small LLM/VLM, if supported models and latency meet the task; useful when network access/privacy matters. | Official specs: **40 TOPS INT4**, 8 GB dedicated memory, local LLM/VLM support. TOPS does not predict token rate or visual-query latency; no opened vendor source gave an end-to-end robot VLM FPS. It occupies the Pi PCIe path, so check interaction with current storage. [Official product docs](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html) |
| Lab edge server via RTP | Best first place for open-vocabulary/VLM inference. Send selected low-rate frames/crops; return a compact, timestamped semantic result. Pi retains SLAM, geometry, stale-result rejection and local stop behavior. | Our RTP streaming/freshness-supervisor coursework is an architectural starting point, not a measured WBR network/latency guarantee. Test frame-age distribution, jitter, loss, reconnect and queueing under the actual path; never treat server receipt time as image capture time. |
| Jetson Orin Nano Super 8 GB (lab request option) | Local GPU inference for multiple vision models and small VLM experiments without server dependency. Better if sustained on-robot AI is the priority. | NVIDIA lists up to **67 INT8 TOPS** after current software update; not directly comparable with Hailo INT4 TOPS and not a task FPS. Obtain current model-specific latency/power on the exact stack before choosing. [Official guide](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/index.html) |

**Now:** tabletop RGB-D/recorded-data semantic goals and simulated Nav2 are feasible; live person following and robust map-to-navigation integration are unverified. The 24 Oct bag contains boxes on a table, not a walking person or navigation sequence. **After arrival:** add body-camera extrinsics, vibration/motion data, wheel/leg odometry and local MCU interface; verify SLAM resets and person-relative motion before any robot movement. Nav2, elevation mapping and dynamic-target following are integrations to prototype, not claims of existing WBR capability.

## 5. Hardware/compute to request

1. **Request access to the existing CN edge-AI server first**, including its GPU/model inventory, network path, RTP encoder/decoder settings, API, and permission to log capture-to-result timestamps. This is the cheapest route to a convincing language-guided demo and tests the already-built coursework path.
2. **Borrow a Jetson Orin Nano Super 8 GB** for a short comparative evaluation if CN round-trip age is too variable or robot privacy/offline operation matters. Compare the same detector/VLM and input rate, with power, thermal, latency and model revision logged.
3. **Do not buy an Hailo-8L solely for language interaction.** It accelerates supported perception networks but does not itself provide a general VLM. Consider AI HAT+ 2 only after a specific supported VLM and measured latency solve a local-inference need; check PCIe storage conflict first.
4. Keep the existing Pi 5 as the primary ROS/SLAM and freshness supervisor regardless of accelerator. No added accelerator has permission to issue motor torque or bypass local obstacle/failsafe handling.

## 6. Two-week prototype plan using our rig/data

**Week 1 — Ground language in recorded geometry (no robot motion).**

- Days 1–2: inventory the 24 Oct D435i bags, labels, calibration and timestamps; select/annotate a small fixed set of box frames. Define command set (“red box”, “nearest box”, “box left of …”), target identity/position scoring and reject/abstain rules before measuring.
- Days 3–4: baseline closed-set object detector + depth centroid; compare to a remote open-vocabulary/VLM query on matching frames. Return only label, 3D point, confidence, capture stamp and sequence. Preserve raw-frame IDs and model versions.
- Day 5: replay target outputs against the bag’s camera poses/map; visualize target, pose, confidence and age. Record precision/recall or target accuracy, false-goal/abstention counts, p50/p95/p99 capture-to-result age, bytes/frame and Pi CPU/RAM. Treat tabletop localization as tabletop evidence.

**Week 2 — Navigation and freshness under controlled faults.**

- Days 6–7: feed accepted goals to a Nav2 simulation with a robot footprint and static map; show “go to red box” selecting, planning and reaching a goal. Add dynamic-point-following simulation with a moving person target; detector is simulated or replayed, so this is not live following.
- Days 8–9: inject delayed, reordered, repeated and missing server responses; RTP disconnect/reconnect; stale frames; ambiguous targets; SLAM reset/pose jump. Verify expired or invalid responses cannot update the goal and the supervisor transitions to stop/relocalize.
- Day 10: repeat a frozen scenario matrix with CPU/ORB load and a declared network condition. Produce one demo clip and a short result table with failure cases and limitations. If end-to-end navigation cannot be connected in two weeks, deliver the faithful bag-to-map visualization plus Nav2 simulation and state the integration gap.

**Exit criterion:** reproducible semantic target selection and Nav2 simulation; all injected expired/invalid results rejected; latency/accuracy/false-goal evidence saved. This does not establish live WBR autonomy, person-following performance, terrain traversal, or safe physical motion.
