# R1b — independent estimator and mapping recommendation

Research date: 2026-10-14. Status: **research complete; estimator selection and hardware qualification OPEN**. This report was developed without reading `R1_algorithms.md`. Scores are engineering judgments, not benchmark results. External sources were inspected through web search; mutable upstream pages must be pinned before implementation.

## Decision from the requirements

**Default: finish the existing native ORB-SLAM3 stereo-inertial diagnostic route, qualify its local motion output before robot use, and add navigation mapping only when needed.** Keep OpenVINS as the first measured alternative for local VIO, and RTAB-Map as the preferred mapping candidate once reliable odometry exists. This is a staged recommendation for review, not approval to change architecture, messages, firmware or the node graph.

The requirements are: useful scene-relative motion on a Pi 5 8 GB CPU; a short route to a demonstrable result; later indoor navigation; and continued STM32-owned balance when perception fails. A trajectory plot, continuous local odometry, a globally corrected map, and an obstacle representation are different deliverables. Selecting one monolithic “best SLAM” obscures those differences. The existing [ownership decisions](../../docs/DECISIONS.md) and [architecture](../../docs/ARCHITECTURE.md) remain fixed.

For a robot driving demonstration, **wheel odometry + controller-owned body estimation + local depth obstacles may be sufficient before global SLAM**. However, this repository does not establish a ready encoder/body-state export, contact/slip handling or an approved perception-to-controller interface. It is therefore not presently a proven shortcut. If those already exist in the lab, this becomes the preferred first *robot* demo, while the camera estimator remains a separate qualification activity. A hand-carried camera-to-plot demonstration must not be described as robot integration.

## Starting evidence and its limits

| Repository evidence | Consequence for this decision |
|---|---|
| [13 October facts](../../experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md), sections C–E: native ARM build; three EuRoC MH01 stereo-inertial trials, ATE RMSE 0.0415/0.0368/0.0416 m; approximately 830 MB peak RAM | ORB has useful local reproducibility evidence and prepared adapters. This is not evidence that it wins on WBR motion. |
| Same source: 184 s input took 282–301 s on a 4 GB stand-in under undervoltage | Neither 20 Hz nor 30 Hz sustained operation on the target is established. Extra RAM does not establish extra processing throughput. |
| [14 October addendum](../../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md): 8 GB board boots, undervoltage persists; first D435i replay crashed; patch-four rebuild interrupted | The shortest existing route still has a build/runtime blocker. Its repair must be verified, not assumed. |
| Same addendum: 100 s microSD recording has 0.3–2.9 s gaps; 15 s RAM test has no dropped frames; USB stick measured 1.09 MB/s | These input/storage failures can defeat every estimator. RAM is a bounded diagnostic workaround, not qualified long-term storage. |
| [Calibration readiness](../../docs/D435I_VIO_CALIBRATION_READINESS.md) is for the older unit; October facts describe the replacement's nominal geometry, assumed noise and calibration warning | Do not transfer old-unit calibration. Preserve “IMU Calibration is not available”; camera–IMU time offset and unit-specific noise remain unresolved. |
| [Project state](../../docs/PROJECT_STATE.md), [next gate](../../docs/NEXT_GATE.md) and [evidence index](../../docs/EVIDENCE_INDEX.md) contain placeholders/historical summaries | Dated facts take precedence for observations; no current gate is promoted here. No Pi-side raw evidence was newly retrieved. |

The [brief deck](../../slides_brief/main.tex), [course gate ladder](../../slides_course/main.tex), [native bring-up](../../docs/RPI5_NATIVE_PERCEPTION_BRINGUP.md), [two-week plan](../../docs/NEXT_TWO_WEEKS_PERCEPTION_PLAN.md), and [lab runbook](../../experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md) support the distinction between diagnostic results and accepted performance. Historical proposed microSD capacity is not storage qualification.

## Candidate evidence

“No benchmark found” means none verified in this review, not proof that none exists. ARM compilation, Jetson GPU demonstrations and desktop frame rates cannot establish CPU-only Pi 5 throughput. Integration effort below is relative to this repository and is **inferred**, with no invented person-day estimates.

| Candidate and role | ARM/Pi performance evidence | Maintenance, Jazzy and licence | Fit, robustness risks and effort from here — inference |
|---|---|---|---|
| **ORB-SLAM3 stereo-inertial**: sparse multi-map SLAM | Local EuRoC results above are the strongest project-specific evidence; stable-power target throughput unknown. Upstream recommends a powerful computer for real time. | Official examples target ROS Melodic, not Jazzy. Upstream README remains V1.0-era; this project already needed compatibility/runtime patches. GPL-3.0. [Official repository](https://github.com/UZ-SLAMLab/ORB_SLAM3) | Lowest immediate estimator integration effort: existing recorder, adapter and plotting. IMU can constrain fast motion, but incorrect timing/calibration, blur and initialization remain risks. Sparse landmarks alone do not supply a navigation obstacle map. |
| **ORB-SLAM3 RGB-D**, evaluated here without IMU | No matched Pi RGB-D trial verified; stereo-inertial timing cannot be transferred. | Same core/maintenance/licence; official RGB-D example expects registered depth. [Official examples](https://github.com/UZ-SLAMLab/ORB_SLAM3#7-ros-examples) | Avoids inertial initialization but adds depth/image association, scale and registration checks plus a different capture profile. Depth holes and fast rotation remain concerns. Medium effort; not automatically easier than the prepared stereo path. |
| **OpenVINS**: filter-based local VIO | Installation guide discusses ARM portability. Pi 4 user report demonstrates attempted operation, also inconsistent outcomes; no controlled Pi 5 rate verified. [Install guide](https://docs.openvins.com/gs-installing.html), [issue 210](https://github.com/rpng/open_vins/issues/210) | Upstream ROS 2 support and evaluation tools exist. Jazzy/Ubuntu 24.04 PR **500 is open** at inspection, with build/run reports; this is not a supported Jazzy release guarantee. GPL-3.0. [Repository](https://github.com/rpng/open_vins), [PR 500](https://github.com/rpng/open_vins/pull/500) | Best first VIO challenger: bounded filter state, covariance and online calibration facilities are useful. Lower CPU demand than ORB is a hypothesis to test. Needs pinned build, data adapter/config and later global mapping. Online calibration cannot recover missing samples or remove observability requirements. Medium effort. |
| **VINS-Fusion**: optimization-based VIO with loop fusion | No controlled Pi 5 stereo-inertial throughput verified. A related VINS-Mono study reports ARM CM4 results, but uses a different pipeline/sensor experiment; not a VINS-Fusion benchmark. [ARM study](https://arxiv.org/abs/2406.13345) | Official setup is ROS 1/catkin; no official Jazzy path verified. README explicitly discusses ongoing reliability work. GPL-3.0. [Official repository](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion) | Stereo/IMU and online time/extrinsic calibration are relevant, but porting and optimizer load add work. “Fusion” does not mean ready WBR wheel/contact fusion. High effort without a lab-owned working port. |
| **Basalt**: VIO and mapping research stack | Current documented binaries include Ubuntu **amd64** and macOS **arm64**; Apple ARM is not Pi Linux evidence. No controlled Pi 5 benchmark verified. | Maintainer tags show 0.1.7 dated March 2026; do not dismiss it as abandoned. CMake/vcpkg source route, no official Jazzy integration verified. BSD-3-Clause core. [Maintainer README](https://gitlab.com/VladyslavUsenko/basalt/-/tree/master), [tags](https://gitlab.com/VladyslavUsenko/basalt/-/tags) | Technically credible challenger, but Linux ARM build, D435i adapter, calibration import and ROS boundary need qualification. Existing T265 support does not establish D435i support. High initial effort; reconsider for a demonstrated runtime advantage or permissive-core requirement. |
| **Kimera-VIO**: stereo VIO, optional loop closure/mesh | CPU implementation; no Pi 5 timing/RSS benchmark verified. “CPU” is not evidence of Pi capacity. | Official instructions tested on Ubuntu 20.04; ROS wrapper uses catkin. Dependencies include GTSAM, OpenGV, DBoW2 and Kimera-RPGO. BSD core; no official Jazzy path verified. [Official repository](https://github.com/MIT-SPARK/Kimera-VIO) | Rich mapping capabilities, but greater build/integration surface than this demo needs. Loop closure is disabled by default. Mesh generation does not itself validate traversability. High effort; disable optional workloads in any future comparison. |
| **RTAB-Map with own RGB-D/stereo odometry**: mapping-first route | Pi 5/Jazzy/D435 issue records show ARM64 use and integration failures, not a benchmark. No verified workload-matched sustainable rate. [Pi issue 1230](https://github.com/introlab/rtabmap_ros/issues/1230), [Jazzy example issue 1404](https://github.com/introlab/rtabmap_ros/issues/1404) | Maintained ROS 2 branch, explicit Jazzy release record. BSD-3-Clause core; optional dependencies have separate licences. [ROS repository](https://github.com/introlab/rtabmap_ros), [release record](https://github.com/introlab/rtabmap_ros-release), [core licence](https://github.com/introlab/rtabmap/blob/master/LICENSE) | Strongest route to occupancy/3D mapping and later navigation integration. Avoids requiring inertial initialization in a visual-odometry configuration. Own VO still needs good visual/depth inputs; mapping adds CPU/RAM/storage. Medium effort after N3 and reviewed depth/stereo extension. |
| **RTAB-Map with external odometry**: mapping behind a qualified local estimator | Whole-stack Pi performance unknown; odometry and mapping must be measured together. External odometry is explicitly supported. [ROS package roles](https://raw.githubusercontent.com/introlab/rtabmap_ros/ros2/README.md) | Same RTAB support; external estimator's maintenance/licence also applies. | Preferred later composition if wheel/body odometry or VIO is trustworthy. Medium-to-high effort now: no qualified external odometry interface exists here. Use one local odometry authority and one global correction authority; do not combine two independently jumping SLAM outputs blindly. |
| **DROID-SLAM; learning-based alternatives such as DPVO** | DROID's official demos require CUDA and a GPU with at least **11 GB GPU memory**. DPVO's documented setup also uses CUDA. Neither is a demonstrated CPU-only Pi route. [DROID requirements](https://github.com/princeton-vl/DROID-SLAM), [DPVO setup](https://github.com/princeton-vl/DPVO) | Research repositories; no official Jazzy integration verified. DROID BSD-3-Clause, DPVO MIT; model/third-party terms remain separate. [DROID licence](https://github.com/princeton-vl/DROID-SLAM/blob/main/LICENSE), [DPVO licence](https://github.com/princeton-vl/DPVO/blob/main/LICENSE) | Reject for the onboard default. Smaller learned methods are not excluded in principle, but must supply CPU ARM evidence. A GPU workstation could be an offline comparator if the lab confirms one; it is not the specified onboard system. |
| **No SLAM yet: wheel odometry + body IMU + depth obstacles** | No WBR timing or slip benchmark exists in inspected evidence. Expected lighter compute is an inference from omitting visual estimation/global mapping. | No single algorithm licence. Existing STM32 code/export unknown. Optional ROS `robot_localization` is Apache-2.0 with an upstream ROS 2 implementation; no install/runtime qualification here. [Package manifest](https://github.com/cra-ros-pkg/robot_localization/blob/ros2/package.xml) | Potential fastest controlled rolling demo if encoder/body-state interface already works. Wheel slip, contact loss, changing leg geometry and unbounded drift limit navigation. Body IMU remains STM32-owned; Pi may consume a reviewed estimate. Depth needs attitude/mount/time handling. Integration effort presently uncertain, not “zero.” |

Maintenance judgments above concern the observed integration surface, not a promise of maintainer response. No candidate is rejected merely because its paper is old. Licence labels identify core source only; they are not an audit of a combined distribution.

## Weighted decision table

Scale: **1** poor fit/high burden, **3** plausible but unverified/moderate burden, **5** strong fit/low burden. Weights are chosen for a small team needing a demo soon and a credible continuation. Unknown performance receives a conservative score, never a fictitious FPS. The scores include the effort of producing useful outputs, so an estimator-only candidate is penalized for mapping it does not yet provide.

| Criterion | Weight | Interpretation |
|---|---:|---|
| D: demo readiness | 30% | Remaining work from the actual repository state, not sunk effort alone |
| C: CPU/memory fit | 20% | CPU-only Pi feasibility and likelihood of bounded processing |
| R: WBR robustness | 20% | Expected continuity under rolling/pitch motion, calibration and failure observability |
| J: maintenance/Jazzy | 15% | Official integration, dependency burden and evidence of support |
| N: navigation path | 10% | Useful persistent mapping/obstacles and local/global separation |
| L: licence flexibility | 5% | Core permissive licensing versus copyleft integration constraints |

`total = (30D + 20C + 20R + 15J + 10N + 5L) / 5`, out of 100. **All component scores and totals are inferred decision aids.** No score is an acceptance threshold.

| Candidate | D | C | R | J | N | L | Total /100 | Main uncertainty |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ORB stereo-inertial | 5 | 3 | 3 | 2 | 3 | 2 | **68** | Stable-power live latency and replacement-camera VIO |
| RTAB-Map own odometry | 3 | 2 | 3 | 5 | 5 | 5 | **68** | Complete Pi load and visual odometry continuity |
| OpenVINS | 3 | 4 | 3 | 3 | 2 | 2 | **61** | Jazzy port qualification and matched Pi timing |
| No SLAM yet | 2 | 5 | 2 | 3 | 2 | 3 | **56** | Existing MCU export, wheel geometry/contact/slip |
| ORB RGB-D | 3 | 3 | 2 | 2 | 3 | 2 | **52** | New RGB-D input path and motion robustness |
| RTAB-Map + external odometry | 2 | 2 | 3 | 3 | 5 | 3 | **54** | External source unavailable; score assumes OpenVINS-class integration |
| Basalt | 2 | 3 | 3 | 2 | 3 | 5 | **53** | Linux ARM adapter/build and Jazzy boundary |
| VINS-Fusion | 2 | 3 | 3 | 1 | 3 | 2 | **47** | ROS 1 port and no measured runtime advantage |
| Kimera-VIO | 2 | 2 | 3 | 1 | 4 | 5 | **48** | Dependency/ROS port work and total Pi load |
| DROID/DPVO class | 1 | 1 | 3 | 1 | 3 | 5 | **36** | **Hard CPU-only deployment mismatch**, irrespective of score |

**Interpretation and sensitivity.** ORB and RTAB tie numerically: that is not precision or proof of equivalence. The tie is resolved by the immediate deliverable, currently camera-to-trajectory with existing native tooling. RTAB wins the mapping-first question. Moving ten weight points from D to N makes ORB **64** and RTAB **72**. If ORB demo readiness drops from 5 to 3 because repair reveals substantial new work, its total becomes **56**. If an existing wheel/body interface is demonstrated, raising no-SLAM D from 2 to 5 and J from 3 to 4 makes it **77**, enough to change the first robot-demo recommendation. One point on any criterion moves the total by 1–6 points; differences this small require experiments, not argument.

## Robustness implications for this robot

The following are **engineering inferences to validate on WBR**, not measured outcomes:

- All visual candidates need observable scene information. Test low texture, exposure/blur, people moving through view, rapid pitch/turns and short occlusion. Do not infer wheel-biped robustness from drone or handheld benchmark accuracy.
- Stereo-inertial VIO is a sensible primary candidate for nonplanar motion, but the camera IMU measures the camera, not the controller body. A rigid, characterized mount is required; articulated mounting needs a reviewed time-dependent transform.
- Online calibration in OpenVINS/VINS-Fusion is a useful estimator capability, not a substitute for trustworthy timestamps, excitation and calibration holdout checks. A new estimator will not repair a recording gap.
- Wheel/body odometry is useful during steady rolling; contact loss and slip invalidate naive wheel constraints. Do not add a permanent planar-motion assumption merely to make a plot look stable. Jump behavior requires separate controller-owned validation.
- Depth obstacles need range/invalid-pixel review and a correctly timed transform into the local planning frame. A pitching camera can otherwise make the floor appear to be an obstacle. Introduce depth load separately after the fixed raw gates; emitter-off stereo tracking and usable depth must be tested together before simultaneous deployment.

Later navigation should distinguish continuous local motion from global loop corrections. The coordinate convention is supported by [REP-105 source](https://github.com/ros-infrastructure/rep/blob/master/rep-0105.rst); exact publishers, frames and messages remain a design review. ORB map resets/loop corrections must not be relabeled as continuous odometry. OpenVINS local VIO needs a separate global mapping/localization layer if drift-bounded repeated navigation is required. For RTAB with external odometry, consume a qualified local estimate and avoid redundant visual odometry unless explicitly comparing it.

## Smallest evidence campaign that can change the choice

This is a future review plan, **not executed** and not a replacement experiment format.

1. **Restore prerequisites first.** Follow [Phase A](../../experiments/2026-09-12-pi5-native-sensor-validation/PHASE_A_RUNBOOK.md) and the lab runbook. Require `CAMERA AVAILABLE` before any camera or ORB execution. N0 health → N1 own-branch USB **≥5000M** → N2 **IR1 Y8 640×480/15, gyro/200, accel/100**, **20 → 105 → mandatory 300 s** with unchanged timing/health thresholds → N3 explicit record/replay. Stereo 30 Hz and depth are separately reviewed extensions, not weaker replacement gates. Acquisition stays Pi-local; large bags need separately qualified storage.
2. **Finish one current route.** Rebuild the already-applied crash fix in the isolated runtime copy, record linkage and hashes, then review offline D435i input before a live attempt. Preserve calibration warnings and failed attempts. Use the existing [exact command cards](../../experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md); do not improvise new paths or reset checkouts. Build success is not replay success.
3. **Freeze a fair comparison before adding alternatives.** First repeat the known dataset on stable power; then use identical qualified D435i stereo/IMU data and calibration provenance for ORB/OpenVINS. Use at least three repeats, as proposed in the existing two-week plan. Preserve originals and log each adapter's units, interpolation, dropped/rejected samples and frame convention. Offline processing measures reproducibility and throughput; separately paced replay/live measures queue growth and freshness. RGB-D comparisons need a separately qualified synchronized RGB-D input, so do not score them on absent data.
4. **Measure the decision variables.** Initialization success/time, all resets/loss intervals, trajectory coverage, reference-aligned ATE/RPE where ground truth exists, source-age P50/P95/P99 with clock uncertainty, queue depth, CPU/RSS, thermal/power and storage load. A room loop without ground truth establishes continuity, not accuracy. Navigation rate, maximum usable age, accuracy and outage budgets are **UNKNOWN** and must be reviewed before declaring a winner/PASS.
5. **Add mapping only after local motion is useful.** Test RTAB-Map with its own odometry if a near-term map becomes the main product; otherwise test it behind the qualified local estimator. Proposed load reduction: bounded map extent, downsampled depth and lower map update cadence while retaining local odometry cadence. Exact settings need measured quality/load trade-offs. N5 performance → N6 reviewed stale/reset/frame semantics with offline/synthetic fixtures → separately authorized N7 robot tests. Synthetic results establish tooling only.

| Observed evidence | Decision change |
|---|---|
| ORB cannot meet reviewed source-age/continuity budgets on stable-power qualified input; OpenVINS does on the same input | Switch local VIO to pinned OpenVINS after its Jazzy build and failure semantics are qualified. |
| Primary demo becomes occupancy mapping/navigation; RTAB own odometry sustains the reviewed workload | Prefer RTAB-Map own odometry for the first mapping demo; do not retain ORB merely because it was built first. |
| Working encoder/body estimate export, known geometry and adequate low-speed slip behavior already exist | Use no-SLAM local rolling/depth demo first; leave global navigation claims deferred. |
| IMU calibration remains unresolved, while separately qualified visual-only stereo/RGB-D tracks adequately | Use an explicitly visual-only diagnostic route. Existing stereo input may make stereo-only ORB a smaller ablation than RGB-D; neither is qualified VIO. |
| Basalt/Kimera/VINS-Fusion has a lab-maintained Jazzy/ARM build and matched evidence of a meaningful advantage | Recompute integration and runtime scores; reopen that candidate. |
| CPU-only constraint changes and a GPU machine is confirmed | Consider learning-based methods as a separate architecture/offline research decision. |

## Questions for the owner/lab

Confirm whether the next deliverable is a handheld trajectory, controlled robot rolling with obstacle display, or autonomous mapped navigation. Confirm whether encoder timestamps, body attitude/velocity and contact state are already exported and with what calibration. Confirm rigid camera mounting, supply/cooling, qualified recording storage, calibration target and independent trajectory reference availability. Set acceptable pose age, loss recovery, accuracy and mapping extent. GPU workstation access and commercial licence constraints are unknown; neither is assumed.

## Provenance and validation of this report

Read `R1b_BRIEF.md`, `COMMON.md`, repository instructions, the required local sources linked above and the primary upstream sources cited in the comparison. Did not read the other estimator report. Git was inspected read-only: branch `claude/project-thread-rhsrup`, HEAD `cf09251`, with substantial pre-existing dirty/untracked work. `COMMON.md` explicitly prohibits Git mutations, so no branch switch, commit or push was performed. Only this requested report was created under `slides_roadmap/`.

Validation is document-only: checked local link targets, candidate coverage, score arithmetic and weight sensitivity; no estimator, build, sensor, SSH, install or robot test ran. Web evidence does not certify current Pi packages. Useful read-only reproduction commands from repository root:

```bash
git status --short
git branch --show-current
git log -5 --oneline
cat slides_roadmap/research/R1b_BRIEF.md slides_roadmap/COMMON.md
cat slides_roadmap/research/R1b_algorithms_independent.md
```

Future build/manual validation commands remain in the linked lab runbook and must retain its prerequisites. No new runtime commands or tests are needed to validate this Markdown-only change.
