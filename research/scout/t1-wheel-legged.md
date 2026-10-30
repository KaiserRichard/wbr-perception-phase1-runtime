# T1 — Perception-aware wheel-legged robots: literature and paper opportunities

Research scout, 2026-10-30. Scope: wheel-bipedal locomotion, relevant wheeled quadrupeds, depth terrain assessment, and three candidate contributions. This is a targeted review, not an exhaustive novelty certification.

## Context and evidence limits

- Read `README.md`, `ops/worklog/CURRENT.md`, `ops/USER_PROFILE.md`, and `research/scout/BRIEF.md`. No `ops/worklog/reviews/2026-10-30-*.md` files were present. `gh pr list` failed with `error connecting to api.github.com`; open PRs were not inspected.
- The brief reports Pi 5 + D435i floor/box perception (height ±1 cm; distance within 5 cm at 1 m), advisory-only MCU messages, 300 ms expiry, and 630/630 UART echoes with 2.83 ms median round-trip time (RTT). These are supplied project results, not independently revalidated here; sample distributions and experimental conditions are unspecified.
- The robot is expected in November 2026. Neither those tabletop measurements nor assumed-parameter planar simulation establishes obstacle traversal, landing stability, or closed-loop safety on hardware.
- All linked reference entries below were opened through the web tool. Publisher/author abstracts and full texts are distinguished; a preprint is not evidence of peer review. **DM-jump remains UNVERIFIED** as an identifiable robotics work.

## What the literature already establishes

| Platform / research line | Supported capability and sensing distinction | Consequence for this project |
| --- | --- | --- |
| **Ascento** | The original robot combines balancing, rolling, jumping and recovery [P1]. Later work explicitly studies contact switches and impacts in trajectory optimization [P3]. Blind reinforcement learning (RL) subsequently demonstrated 15 cm stair climbing using a selectable climbing mode [P2]. | A balancing robot that jumps, or selects a climbing mode, is established prior art. Jump demonstration alone does not establish perception-driven takeoff. |
| **DIABLO** | Six degrees of freedom, direct-drive joints, linear quadratic regulator (LQR) balance, MCU motion/jump/recovery control, and an ARM onboard computer connected by UART; the paper also describes a watchdog [P4]. It does not validate a depth-driven terrain-to-jump pipeline. | Splitting Linux perception and MCU control, UART communication, and a watchdog cannot carry the novelty claim. |
| **TRON1, wheeled configuration** | Contact-Triggered Blind Climbing (CTBC) uses wheel contact and proprioception to initiate learned climbing; its 2026 revision reports continuous 20 cm stairs on TRON1 and transfer to Cowarobot R0 [P5]. No depth camera is needed for this behavior. | “Add vision to climb a step” must beat a credible contact-triggered alternative in anticipation, collision avoidance, or task completion. |
| **TRON1, legged configuration** | AME-2 uses depth-derived elevation and uncertainty, odometry, attention, and RL; it demonstrates platform/gap/stair negotiation. CPU mapping is reported around 5 ms and policy inference around 2 ms on the stated onboard i7 setup [P6]. | This is strong adjacent perceptive-biped evidence, **not a wheeled-TRON1 traversal result**. Uncertainty-aware terrain representations and CPU deployment already exist. |
| **Unitree B2-W** | The manufacturer's page advertises perceptual/motor integration for discrete terrain, continuous 20–25 cm stairs, and i5/i7 compute with optional Orin NX [W1]. | Industrial capability reference, not a reproducible peer-reviewed comparison. Teleoperation, configuration and manufacturer caveats prevent inferring a specific autonomous RGB-D algorithm. |
| **Autonomous wheeled quadrupeds** | Lee et al. integrate learned locomotion, mobility-aware navigation and city-scale planning, with real urban deployments [P7]. | Hierarchical perception/navigation plus a separate locomotion controller is established; wheel-bipeds still require separate balance and contact validation. |
| **Depth-based mode selection** | Wang and Lin classify seven terrain categories from RGB, then use depth-derived height variation and a reduced-order model to select leg/wheel operation [P8]. | A terrain classifier followed by a locomotion-mode switch is especially close prior work. |
| **Compact depth-based locomotion** | Plozza et al. evaluate resource-constrained quadruped locomotion with D435/ToF elevation mapping and optional visual-inertial odometry (VIO). Their setup uses an i7 NUC plus Orin Nano [P9]. | “Low-cost/depth-aware locomotion” is crowded. A single Pi and camera would be a resource reduction, requiring measured cost, energy and task trade-offs. |

**DM-jump status:** Searches for `"DM-jump" robot`, `"DMJump" robot`, `"DM-Jump" wheeled robot`, and vision-guided wheel-legged jumping did not identify a reliable robotics paper or official project. Authors, year, venue, implementation and claimed capabilities are unknown. Do not invent a citation, identify it with an unrelated jump-control model, or claim novelty against it. Resolve its identity before submission; this is a coverage limitation, not evidence of absence.

Depth geometry is also mature: spatial uncertainty in RGB-D/stereo elevation mapping for small legged robots predates this project [P10]. Geometric labels such as STEP/STOP differ from semantic terrain classes such as grass/gravel and from physical properties such as friction or bearing strength. A fitted floor and visible box height cannot establish the latter properties.

## Credible contribution boundary for Pi 5 + D435i + MCU

The defensible opening is a **measured relationship between sensing limits, compute budget and wheel-biped decisions**, rather than a new platform architecture. None of the opened sources establishes that exact contribution on this hardware; this remains a research hypothesis, not a confirmed literature gap.

- **Decision validity under motion:** evaluate whether current depth observations support a complete wheel corridor, step edge and landing region as body pitch changes. Mark missing/occluded depth unknown rather than free. The brief's 3–12 cm JUMP_CANDIDATE is an obstacle class, not a verified jump envelope.
- **Compute versus useful information:** measure capture-to-decision latency and MCU reception age while ORB-SLAM3 competes for Pi resources. UART RTT is not exposure-to-action age; sustained throughput is not a deadline guarantee. Report dropped frames, thermal behavior, memory and measured electrical power.
- **Robot-specific limits:** derive and identify the admissible approach speed, clearance, traction, actuator and landing conditions. Normalize obstacle heights by wheel radius and robot size when comparing platforms; raw maximum step height is misleading.
- **Honest scope:** without robot trials, contributions are perception/embedded-system evidence. Hardware obstacle negotiation requires independently demonstrated balance, measured robot parameters and validated execution; simulated LQR push recovery does not supply these.

## Three candidate papers

### 1. Selective depth-based obstacle advice with a measured wheel-biped validity envelope

**Question:** Can a simple CPU-only geometric method abstain on unsupported terrain while retaining useful step detections under camera pitch, partial visibility and poor depth?

**Method / potentially new result:** Estimate floor and obstacle geometry with uncertainty, require observed support across both wheel paths and the prospective landing region, and output candidate/stop/unknown. Calibrate acceptance on held-out scenes; quantify the relationship between accepted coverage and dangerous false acceptance within a stated operating domain.

**Closest work:** RGB-D mode selection [P8], spatially uncertain terrain maps [P10], and AME-2's uncertain depth maps [P6]. The possible increment is robot-specific, experimentally calibrated acceptance on a single-camera Pi system, with explicit negative evidence and resource measurements. RANSAC, thresholds, uncertainty and abstention individually are insufficient novelty.

**Decisive evidence:** Compare current single-frame RANSAC/height thresholds, temporal geometric filtering, and the proposed corridor/uncertainty checks on identical recorded inputs. Hold out obstacle instances, materials and sessions; include occluded landings, slopes, drop-offs and invalid depth. Report false acceptance, missed hazards, accepted coverage, calibration and latency with trial-level confidence intervals. After hardware arrival, verify approach/stop behavior; claim successful jumping only if executed and measured.

**Novelty risk: HIGH.** A threshold-tuning study will resemble [P8/P10]. It needs a principled decision rule and a meaningful failure benchmark; abstention must not win by stopping everywhere. Feasible perception study before arrival; locomotion claims deferred.

### 2. Speed- and uncertainty-dependent validity of terrain advice on a wheel-biped

**Question:** When does old obstacle geometry become unusable for stopping or initiating an already validated maneuver, and can a task-derived validity rule outperform the fixed 300 ms timeout?

**Method / potentially new result:** Combine bounded range error, motion since capture and measured braking/actuation delay into a conservative approach envelope. For a static obstacle and constant forward speed, an illustrative stopping condition is \(\hat d-\epsilon_d-v\tau > v t_a+v^2/(2a_{\min})+m\), where distance/error/margin are metres, age and actuator delay seconds, and validated minimum deceleration is positive. This is a candidate model, not a safety proof: body balance, variable speed, slopes, traction and clock uncertainty require treatment. Jump initiation needs a separate experimentally identified launch window.

**Closest work:** DIABLO's MCU/computer split and watchdog [P4], plus integrated wheeled locomotion/navigation [P7]. The potential contribution is experimentally predicting decision failures from capture age and approach dynamics. A freshness protocol alone overlaps T2; this T1 idea concerns obstacle geometry and physical approach limits. AoI/runtime-assurance novelty requires T2's separate literature review.

**Decisive evidence:** Compare fixed 300 ms expiry, tuned fixed expiry, speed-only expiry and the proposed geometry/uncertainty rule. Inject processing delay, backlog and message loss while replaying matched approaches; measure accepted-invalid decisions and unnecessary stops at matched completion rates. Hardware validation must measure stopping distance, speed and MCU action timestamps. Start with stopping, not jumping.

**Novelty risk: MEDIUM–HIGH, unresolved beyond T1.** Stopping-distance formulas, watchdogs and timeouts are established. Publication value depends on a validated bound, failure prediction across speeds and workloads, and a clear difference from generic freshness supervision. A fixed-expiry implementation report is insufficient.

### 3. When is SLAM worth its cost for local wheel-biped obstacle decisions?

**Question:** Under a single-camera Pi budget, when does persistent mapping improve decisions enough to compensate for processing age, odometry errors and compute contention?

**Method / potentially new result:** Compare current frame-local geometry, short-history geometry aligned by measured orientation/motion, and SLAM-registered local mapping on identical scenes and hardware. Test visibility loss during body pitch and approach. Seek a reproducible boundary where memory helps, where stale geometry harms, and where compute should be allocated to new depth observations instead.

**Closest work:** Plozza et al. already ablate VIO and sensor configuration [P9]; AME-2 explicitly compares mapping designs [P6]. A generic “with/without SLAM” ablation is therefore not new. The possible increment is a wheel-biped motion/visibility benchmark linking mapping choice to incorrect physical decisions, resource use and acquisition age on a single Pi.

**Decisive evidence:** Synchronize exposure, processing and advisory logs; use independent obstacle/trajectory ground truth, not ORB-SLAM3 as its own reference. Sweep approach speed, pitch, texture, occlusion and concurrent workload. Measure decision errors, useful detection lead time, map registration error and power; match sensor inputs and tune baselines fairly. Before arrival, a measured camera-motion rig can test perception only; later robot trials establish task outcomes.

**Novelty risk: HIGH.** [P9] is close experimental prior art. A carefully released failure dataset and repeatable compute/decision trade-off can support a systems paper; merely porting a mapper to Pi is weak. Feasibility is relatively good before robot arrival.

## Opened reference register

Full author lists are included. “Preprint” is the verified dissemination venue when a conference/journal venue was not established; no acceptance is implied.

- **[P1]** Victor Klemm, Alessandro Morra, Ciro Salzmann, Florian Tschopp, Karen Bodie, Lionel Gulich, Nicola Küng, Dominik Mannhart, Corentin Pfister, Marcus Vierneisel, Florian Weber, Robin Deuber, Roland Siegwart. **“Ascento: A Two-Wheeled Jumping Robot.” 2019, IEEE ICRA.** [Opened full text](https://arxiv.org/html/2005.11435v1). The arXiv deposit is 2020; conference year is 2019. Author spelling follows the opened arXiv version.
- **[P2]** Simon Chamorro, Victor Klemm, Miguel de la Iglesia Valls, Christopher Pal, Roland Siegwart. **“Reinforcement Learning for Blind Stair Climbing with Legged and Wheeled-Legged Robots.” 2024, IEEE ICRA, pp. 8081–8087.** [Opened author abstract](https://arxiv.org/abs/2402.06143); conference metadata also appears in [P5]'s references.
- **[P3]** Victor Klemm, Yvain de Viragh, David Rohr, Roland Siegwart, Marco Tognon. **“Non-Smooth Trajectory Optimization for Wheeled Balancing Robots with Contact Switches and Impacts.” 2023, IEEE Transactions on Robotics, early access.** [Opened author publication record](https://marco-tognon-robotics.com/content/non-smooth-trajectory-optimization-wheeled-balancing-robots-contact-switches-and-impacts). DOI: 10.1109/TRO.2023.3326334. Full article not inspected; do not infer autonomous perception from its title.
- **[P4]** Dingchuan Liu, Fangfang Yang, Xuanhong Liao, Ximin Lyu. **“DIABLO: A 6-DoF Wheeled Bipedal Robot Composed Entirely of Direct-Drive Joints.” 2024, arXiv preprint 2407.21500, v3.** [Opened full text](https://arxiv.org/html/2407.21500v3).
- **[P5]** Rankun Li, Hao Wang, Qi Li, Zhuo Han, Yifei Chu, Linqi Ye, Wende Xie, Wenlong Liao. **“CTBC: Contact-Triggered Blind Climbing for Wheeled Bipedal Robots with Instruction Learning and Reinforcement Learning.” 2025; revised 2026, arXiv preprint 2509.02986, v3.** [Opened full text](https://arxiv.org/html/2509.02986v3); [opened author-hosted 2026 manuscript](https://ctbc-for-wheeled-bipedal-robots.github.io/static/pdfs/RA_L_2026.pdf). Filename alone does not establish RA-L acceptance.
- **[P6]** Chong Zhang, Victor Klemm, Fan Yang, Marco Hutter. **“Agile and Generalized Legged Locomotion via Attention-Based Neural Map Encoding.” 2026, arXiv preprint 2601.08485, v3 (AME-2).** [Opened full text](https://arxiv.org/html/2601.08485v3).
- **[P7]** Joonho Lee, Marko Bjelonic, Alexander Reske, Lorenz Wellhausen, Takahiro Miki, Marco Hutter. **“Learning Robust Autonomous Navigation and Locomotion for Wheeled-Legged Robots.” 2024, Science Robotics 9(89), eadi9641.** [Opened author-hosted manuscript](https://junja94.github.io/learning_robust_autonomous_navigation_and_locomotion_for_wheeled_legged_robots/assets/paper/AOW_preprint.pdf). DOI: 10.1126/scirobotics.adi9641.
- **[P8]** Ting-Hao Wang, Pei-Chun Lin. **“A Reduced-Order-Model-Based Motion Selection Strategy in a Leg-Wheel Transformable Robot.” 2022, IEEE/ASME Transactions on Mechatronics 27(5).** [Opened institutional abstract and metadata](https://scholars.lib.ntu.edu.tw/entities/publication/e2ca58bb-ee17-4d98-89d7-9fca9f59efd0). DOI: 10.1109/TMECH.2021.3126606.
- **[P9]** Davide Plozza, Patricia Apostol, Paul Joseph, Simon Schläpfer, Michele Magno. **“Robust Reinforcement Learning-Based Locomotion for Resource-Constrained Quadrupeds with Exteroceptive Sensing.” 2025; revised 2026, arXiv preprint 2505.12537, v2.** [Opened full text](https://arxiv.org/html/2505.12537v2).
- **[P10]** Dominik Belter, Przemysław Łabecki, Péter Fankhauser, Roland Siegwart. **“RGB–D Terrain Perception and Dense Mapping for Legged Robots.” 2016, International Journal of Applied Mathematics and Computer Science 26(1).** [Opened publisher abstract and metadata](https://reference-global.com/article/10.1515/amcs-2016-0006). DOI: 10.1515/amcs-2016-0006.
- **[W1, product documentation, not a paper]** Unitree Robotics. **“Unitree B2-W: Go Further with Higher Efficiency.”** Undated manufacturer page, accessed 2026-10-30. [Opened specifications and caveats](https://www.unitree.com/mobile/b2-w/). Manufacturer claims are not independently validated here.
