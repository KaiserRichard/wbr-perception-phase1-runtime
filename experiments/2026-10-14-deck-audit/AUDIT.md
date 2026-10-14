# slides_course audit — 14 October 2026

The deck contains useful system explanations, but its main narrative is dominated by execution instructions, acceptance tables and evidence administration. Keep the physical and algorithm story; move implementation contracts to backup. Update the current-state story from the October 14 addendum before shortening it.

**Recommendation: 38 main frames**, built from 33 KEEP frames and five missing explanations. KEEP means retain the idea, with the corrections and simplifications below; it does not endorse the present wording. BACKUP means useful engineering detail for questions. CUT means remove the slide from the presentation, while preserving original experiment evidence.

## Scope and evidence

- Read-only audit of `slides_course/main.tex`, including speaker notes; `slides_report/main.tex` was read as supporting presentation context. Neither deck was changed.
- The request says 90 frames. The inspected course source has **91 explicit document frames**, including the final References frame; there are no document `\section` invocations producing extra divider frames. The table covers all 91 in source order. Printed subsection numbers repeat and skip, so use audit IDs and titles to locate frames.
- Current observations come from `experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md`, read alongside `experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md`. The October 13 N4A `REPORT.md` establishes the historical dataset results. N4B `README.md`, `n4b_plan.md` and `calibration_notes.md` establish preparation, intended behavior and limits; their earlier “never run” wording is superseded by the addendum's runtime observations.
- Relevant `docs/*.md` were consulted for ownership, calibration, gates, tooling and historical context. Historical/draft inventories do not override the dated session facts. No linked raw experiment files, upstream code, external papers or web pages were opened. Deck assertions alone do not verify experiment results.
- Git status, branch and recent history were inspected before writing. Existing changes were preserved. Branch: `claude/project-thread-rhsrup`; inspected HEAD: `cf09251`. No branch, stash, commit, install, SSH, network, camera command or ORB-SLAM3 execution was performed.
- This is a source-content audit, not a rendered PDF/layout or image-asset review. Figure references and conceptual placeholders do not establish that the reader will see an explanatory image.

Use one short status phrase where needed: **“Calibration unverified,” “Cause inferred,” “Rebuild incomplete,” “Paper value unverified,” “Diagnostic only”** or **“Integration planned.”** Keep provenance and detailed caveats in notes, without hiding a material limitation from the slide.

## 1. Frame-by-frame disposition

Reasons contain 5–10 words. Titles reproduce the inspected source; ID 01 has no LaTeX frame-title argument.

| ID | Frame title | Decision | Reason |
|---|---|---|---|
| 01 | WBR Perception Implementation (title) | KEEP | Identifies the system and its component scope clearly. |
| 02 | Contents | CUT | Eight section labels add navigation without explaining anything. |
| 03 | 1.1 Robot context | KEEP | Connects perception to navigation and independent robot balance. |
| 04 | 1.2 Engineering problem | KEEP | Explains why plausible poses can still be unusable. |
| 05 | 1.3 Objectives and research questions | BACKUP | Formal research questions repeat the system problem statement. |
| 06 | 2.1 Stereo geometry | KEEP | Shows how paired cameras recover metric scene depth. |
| 07 | 2.2 Visual-inertial estimation | KEEP | Introduces complementary image and inertial motion information. |
| 08 | 2.3 Odometry and mapping | KEEP | Explains local drift and corrections when revisiting places. |
| 09 | 2.4 D435i streams | KEEP | Identifies actual sensor inputs and changed camera ownership. |
| 10 | 2.5 ROS communication | KEEP | Explains ROS topics before discussing future robot integration. |
| 11 | 2.6 QoS compatibility | BACKUP | Delivery compatibility tables belong beside ROS troubleshooting details. |
| 12 | 3.1 Machine ownership | BACKUP | Deployment hashes and checkout policy concern engineering operations. |
| 13 | 3.2 Control boundary | KEEP | Makes perception and real-time controller responsibilities visually explicit. |
| 14 | 3.3 Physical platform | KEEP | Grounds the explanation in hardware actually used today. |
| 15 | 3.4 Sensor-to-pose execution path | KEEP | Essential overview needs the current direct SDK path. |
| 16 | 3.4 Topic and type contract | BACKUP | Exact topic names and message types support implementation. |
| 17 | 3.6 Queues and backpressure | KEEP | Explains how slow consumers produce stale sensor data. |
| 18 | 3.8 Storage qualification | KEEP | Actual recording failure makes storage central to understanding. |
| 19 | 3.10 Frame definitions | KEEP | Clarifies coordinate axes and what a pose means. |
| 20 | 3.11 Robot transform ownership | BACKUP | Detailed transform publishers matter during future ROS integration. |
| 21 | 3.12 Camera transform ownership | BACKUP | Internal sensor transform trees exceed the main explanation. |
| 22 | 3.13 Independent IMUs | KEEP | Prevents confusion between camera motion and controller sensing. |
| 23 | 3.14 Transform direction | BACKUP | Matrix direction and storage order support configuration debugging. |
| 24 | 3.15 Timestamp fields and domains | KEEP | Different clocks explain synchronization and misleading freshness claims. |
| 25 | 3.16 Where timestamps are stamped | BACKUP | Field ownership table elaborates the retained clock diagram. |
| 26 | 3.17 Global time | BACKUP | SDK clock mapping specifics belong in timing questions. |
| 27 | 3.18 Worked latency decomposition | BACKUP | Symbolic age bounds exceed the introductory timing explanation. |
| 28 | 3.19 Calibration register | KEEP | Separates usable factory geometry from unresolved inertial calibration. |
| 29 | 3.20 Stereo calibration | KEEP | Shows how wrong image geometry breaks stereo matching. |
| 30 | 3.21 Calibration capture | KEEP | Explains why target motion differs from demonstration motion. |
| 31 | 3.22 IMU noise | BACKUP | Allan analysis needs specialist context beyond system understanding. |
| 32 | 3.24 Algorithm threads | KEEP | Gives tracking mapping and loop closing distinct roles. |
| 33 | 3.25 Tracking | KEEP | Explains the steps converting sensor samples into pose. |
| 34 | 3.26 Mapping and Atlas | KEEP | Explains keyframes persistent structure and multiple map behavior. |
| 35 | 3.27 Inertial initialization | KEEP | Explains why movement is needed before inertial tracking. |
| 36 | 3.28 Settings audit before tuning | BACKUP | Parser groups and tuning keys are configuration reference. |
| 37 | 3.28 Numeric IMU settings contract | BACKUP | Noise discretization and parser keys are specialist details. |
| 38 | 3.29 Input association | BACKUP | Interpolation mathematics should support a simpler interval illustration. |
| 39 | 3.30 Planned health envelope | BACKUP | Proposed message field families exceed the ownership explanation. |
| 40 | 3.31 Health supervision | KEEP | Shows why heartbeat alone cannot validate perception output. |
| 41 | 3.32 Planned Pi-to-STM32 boundary | BACKUP | Receiver fields and unknown rates repeat the boundary. |
| 42 | 4.1 Gate dependencies and status | KEEP | Summarizes progression while separating dataset and camera evidence. |
| 43 | 4.2 N0: platform preflight | BACKUP | Inventory commands serve operators rather than system learners. |
| 44 | 4.2 N0: acceptance and diagnosis | BACKUP | Exact power memory and temperature criteria are reference. |
| 45 | 4.2 N0: physical inventory record | CUT | Repeats physical platform and preflight without new explanation. |
| 46 | 4.3 N1: own-branch USB and access | BACKUP | Shell arguments and receipt artifacts belong in runbooks. |
| 47 | 4.3 N1: acceptance and diagnosis | BACKUP | Permission classes and receipt age support gate execution. |
| 48 | 4.4 N2: staged native acquisition | BACKUP | Exact acquisition command belongs beside the preserved runbook. |
| 49 | 4.4 N2: reproduction and mandatory soak | CUT | Repeated shell commands crowd out the underlying purpose. |
| 50 | 4.5 N2: delivery criteria | BACKUP | Required timing thresholds must remain available without dominating. |
| 51 | 4.5 N2: content, health and acceptance | BACKUP | Acceptance artifacts and manual review support operator questions. |
| 52 | 4.5 Worked window-rate and boundary check | CUT | Symbolic rate arithmetic is validator material for agents. |
| 53 | 4.6 N3: one wrapper, bounded record | BACKUP | Detailed launch and recording commands are execution reference. |
| 54 | 4.7 N3: stop camera and replay | BACKUP | Domain isolation arguments exceed the offline replay concept. |
| 55 | 4.7 N3: PASS/FAIL matrix | BACKUP | Exact replay acceptance evidence supports implementation review questions. |
| 56 | 4.7 Storage prerequisite: no mount fallback | BACKUP | Mount identity and batch thresholds support storage qualification. |
| 57 | 4.7 Content checks beyond delivery rates | BACKUP | Stationary vector limits belong in sensor validation reference. |
| 58 | 4.8 Stereo extension | BACKUP | Preserving IR1 gates matters but repeats progression distinctions. |
| 59 | 4.9 N4A: camera-independent EuRoC baseline | KEEP | Known reference data separates algorithm and camera problems. |
| 60 | 4.9 N4A: estimator acceptance contract | BACKUP | Acceptance matrices obscure the completed baseline experiment story. |
| 61 | 4.10 N4B: offline D435i stereo | KEEP | Recorded camera replay explains repeatable acquisition failure diagnosis. |
| 62 | 4.10 N4B: input and run criteria | BACKUP | Detailed residual and coverage contracts support later review. |
| 63 | 4.10 N4B: immutable adapter provenance | BACKUP | Converter manifests and hash reconciliation are implementation bookkeeping. |
| 64 | 4.11 N4C: live stereo scheduling | KEEP | Contrasts replay diagnosis with live processing and freshness. |
| 65 | 4.11 N4C: live PASS/FAIL criteria | BACKUP | Unknown numeric bounds and timelines are performance reference. |
| 66 | 4.12 N5: reproducible measurement | BACKUP | Measurement commands and artifact lists support experiment execution. |
| 67 | 4.12 N5: measurement criteria | BACKUP | Percentiles and campaign contracts exceed the baseline result. |
| 68 | 4.13 N6: health semantics with fixtures | BACKUP | Synthetic receiver fixtures concern future interface implementation work. |
| 69 | 4.13 N6: planned acceptance table | BACKUP | Clock wrap and rejection contracts need specialist review. |
| 70 | 4.14 N7: staged controller boundary | BACKUP | Bench safety progression supports questions after ownership explanation. |
| 71 | 4.14 N7: planned acceptance table | BACKUP | Detailed controller fault traces belong in integration review. |
| 72 | 4.15 Reproduction and evidence | BACKUP | Bundle deployment and acceptance receipts are operational bookkeeping. |
| 73 | 4.16 Bottom-up diagnosis | KEEP | Connects symptoms to the earliest failing system layer. |
| 74 | 4.18 Bounded AI tickets | CUT | Agent delegation policy does not explain the system. |
| 75 | 5.2 ATE computation outline | BACKUP | Alignment equations support metric questions after intuitive explanation. |
| 76 | 5.3 RPE and pair policy | BACKUP | Relative error mathematics and pairing policies are specialist. |
| 77 | 5.4 Trajectory conversion and evo | CUT | Command flags and quaternion conversion are operator reference. |
| 78 | 5.6 Latency and loss | BACKUP | Percentile definitions and counter reconciliation support performance questions. |
| 79 | 5.7 Resource measurements | BACKUP | Resource instrumentation lists exceed the current blocker explanation. |
| 80 | 5.8 Accuracy results | KEEP | One simple baseline plot gives measured progress meaning. |
| 81 | 5.9 Timing results | BACKUP | Detailed wall durations add little beyond invalid timing. |
| 82 | 5.10 Resource results | BACKUP | Raw sample counts and empty panels obscure implications. |
| 83 | 6.1 Runtime and USB | BACKUP | Packaging tradeoffs repeat the retained physical platform explanation. |
| 84 | 6.2 Inputs and clocks | BACKUP | Experiment variable policy belongs beside exact profile reference. |
| 85 | 6.3 Algorithm and calibration | BACKUP | Tool selection and deferred fusion exceed current scope. |
| 86 | 7.1 Historical evidence | BACKUP | Old failure chronology supports provenance rather than understanding. |
| 87 | 7.2 Current evidence gaps | KEEP | Summarizes achieved work and remaining barriers to qualification. |
| 88 | 7.3 Changes since 2026-10-10 | CUT | Duplicates current state with obsolete platform and execution. |
| 89 | 7.4 Conditional roadmap | KEEP | Gives the owner concrete next steps with limits. |
| 90 | 8. Conclusion | KEEP | Closes on system purpose evidence and controller ownership. |
| 91 | References | BACKUP | Full bibliography supports followup without interrupting the narrative. |

**Disposition totals:** 33 KEEP, 51 BACKUP, 7 CUT. Do not append all 51 backup frames unchanged: consolidate them into question-driven groups for gates, ROS/QoS, transforms, clocks, configuration, calibration/noise, metrics, provenance, health and controller tests. Exact requirements remain in the source documents and selected backups. Removing a command slide does not change its engineering requirement.

### Resulting lean outline — 38 main frames

The order below follows purpose → physical system → estimation → evidence → next work. Reuse KEEP ideas, rewrite overloaded frames, and add M1–M5 from section 3. Other missing explanations improve retained frames rather than adding slides. The titles below are suggested plain-English titles, not edits already applied.

| Main | Suggested title / one idea | Existing frame or addition | Preferred visual |
|---|---|---|---|
| 01 | WBR perception: understanding the system | 01 | Platform overview; date October 14. |
| 02 | What navigation needs from perception | 03 | Robot, scene and estimated motion. |
| 03 | The Pi estimates; STM32 controls balance | 13 | Two ownership boxes and optional reference. |
| 04 | Why a plausible pose can be unusable | 04 | Fresh pose versus delayed pose. |
| 05 | The hardware used in this session | 14 | 8 GB Pi, camera, card and unresolved supply. |
| 06 | What the D435i supplies | 09 | Left IR, right IR, gyro and accelerometer. |
| 07 | The two IMUs have different jobs | 22 | Camera IMU and controller body IMU. |
| 08 | From camera samples to a trajectory | 15 | Direct SDK path; ROS path marked planned. |
| 09 | Where ROS 2 fits in robot integration | 10 | Publisher/topic/subscriber; integration planned. |
| 10 | A pose needs an origin and axes | 19; refine M6 | Camera-IMU pose versus robot-body pose. |
| 11 | Stereo turns image displacement into depth | 06 | Same point in two views; one relation. |
| 12 | Features let images describe motion | New M1 | Same fixed scene features across images. |
| 13 | Images and inertial data complement each other | 07 | Two cues feeding one motion estimate. |
| 14 | Motion samples bridge successive images | New M2 | Image interval containing gyro/accel samples. |
| 15 | Tracking estimates the current pose | 33 | Pair → matches → estimate. |
| 16 | Keyframes preserve useful views of the scene | 34 | Selected views linked to map points. |
| 17 | Tracking, mapping and loop closing share the work | 32 | Roles diagram; thread detail in notes. |
| 18 | Revisiting a place can correct accumulated drift | 08 | Local path and corrected map path. |
| 19 | Inertial initialization needs useful motion | 35; refine M9 | Translation and rotation before a short loop. |
| 20 | Why the infrared projector is off | New M3 | Fixed scene texture versus projected dots. |
| 21 | Calibration tells sensors how they relate | 28; refine M7 | Geometry known nominally; noise/offset unresolved. |
| 22 | Stereo points must match along the correct row | 29 | Rectified image pair with corresponding points. |
| 23 | Calibration motion and demonstration motion differ | 30 | Known target, room motion, stationary noise. |
| 24 | Timestamp units do not imply a shared clock | 24 | Device stamps and host arrival on separate lines. |
| 25 | Slow consumers can create old data | 17 | Queue growing behind a slow consumer. |
| 26 | The first long recording had large gaps | 18 | Capture → slow card → blocked recording; cause inferred. |
| 27 | RAM recording avoids writes during capture | New M4 | Capture to RAM; checksum copy afterwards. |
| 28 | A known dataset tests the algorithm separately | 59; refine M8 | EuRoC inputs and reference trajectory. |
| 29 | The baseline achieved about four centimetres ATE | 80; refine M8 | Three ATE results; intuitive position-error explanation. |
| 30 | The native build works; one repair remains incomplete | New M5 | Completed baseline → first-frame crash → pending rebuild. |
| 31 | Offline camera replay makes diagnosis repeatable | 61 | One recorded take replayed across trials. |
| 32 | Live estimation also has to keep up | 64 | Input cadence versus processing backlog; unverified. |
| 33 | Diagnose the first failed layer | 73 | Hardware → input → timing/calibration → estimator. |
| 34 | A heartbeat does not guarantee a fresh pose | 40 | Fresh/stale/invalid states; integration planned. |
| 35 | Camera gates and dataset tests prove different things | 42; refine M10 | Separate EuRoC branch and N1 → N2 → N3. |
| 36 | What is established, and what remains open | 87; refine M10 | Baseline done; diagnostic capture; rebuild/power/calibration open. |
| 37 | The next diagnostic sequence | 89 | Resume rebuild → RAM take → offline → live. |
| 38 | What this system can currently claim | 90 | Motion-estimation evidence plus remaining qualification limits. |

For main frame 35, retain USB **≥5000M** and the mandatory **300-second N2 soak**, with the exact raw profile identified once: IR1 Y8 640×480/15, gyro/200, accel/100. The stereo development profile is separate: IR1 + IR2 Y8 640×480/30, gyro/200, accel/100, emitter OFF. Keep all timing thresholds unchanged in backup; do not reinterpret a 15-second RAM test as N2 acceptance.

For every main frame: one explanatory claim, an actual explanatory diagram, and a short implication. Remove on-slide command blocks, manifests, raw sample denominators, detailed parser keys and repeated gate disclaimers. Define abbreviations at first use; avoid introducing FAST, BRIEF, YAML, UUID, LQR and VMC in the main narrative when their plain-English role suffices. Explain root mean square error (RMSE) and Absolute Trajectory Error (ATE) when presenting the baseline; describe SE(3) as one rotation and translation, without scale fitting. Do not display an unverified paper comparator as established fact.

## 2. Factual corrections and missing current facts

These apply to visible text and notes, including frames destined for backup. A dated October 13 statement is not historically false; it becomes misleading when presented as the October 14 current state. Either update it or label it historical. “No gate PASS” remains correct throughout.

Source abbreviations in the table resolve to these exact permitted files:

- **F13:** `experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md`.
- **F14:** `experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md`.
- **N4A:** `experiments/2026-10-13-n4a-euroc-mh01/REPORT.md`.
- **Plan:** `experiments/2026-10-13-n4b-d435i-prep/n4b_plan.md`.
- **Cal:** `experiments/2026-10-13-n4b-d435i-prep/calibration_notes.md`.
- **Tools:** `docs/PERCEPTION_TOOLING_ARCHITECTURE.md`.

| Frame title / ID | Wrong, stale or unsupported statement | Correct statement / short label | Source file |
|---|---|---|---|
| Title / 01; 3.3 Physical platform / 14; 7.2 Current evidence gaps / 87 | The deck's current snapshot is October 13; “today: 4 GB / Ubuntu stand-in.” | Current update is October 14: the 8 GB Pi booted the unchanged 32 GB card and reported 7.8 GiB RAM. Preserve the 4 GB setup as the historical N4A platform. | F14 item 1; F13 §A; N4A Setup. |
| 4.2 N0: physical inventory record / 45; 7.3 Changes since 2026-10-10 / 88 | 8 GB remains only the target or an unobserved inventory choice. | An 8 GB boot was observed. Later Wi-Fi reachability failed after moving the card back; the cause and final operating state are **“Unverified.”** Do not imply continuously healthy availability. | F14 items 1, 7. |
| 3.4 Sensor-to-pose execution path / 15 | The only complete diagram routes input through ROS topics, a ROS bag and a planned stereo adapter. | Current development programs use librealsense directly: camera → recorder → recording file → patched example → ORB-SLAM3 → trajectory → evaluation; live mode reads the camera directly. Keep ROS/N3 separately **“Integration planned.”** | F13 §E; Plan “One input path”; `slides_report/main.tex`, “Data path” for the presentation distinction. |
| 3.8 Storage qualification / 18; 4.7 Storage prerequisite / 56; 7.2 Current evidence gaps / 87 | Storage is described only as a future qualification task; card arithmetic is the main evidence. | The 100-second microSD take was unusable: repeated 0.3–2.9 s gaps after 22 s. Card writes blocking recording are a strong inference, **“Cause inferred.”** No under-voltage or USB errors appeared in the kernel log during that take; this does not establish healthy power generally. | F14 item 3. |
| 3.8 Storage qualification / 18; 4.10 N4B: offline D435i stereo / 61; 7.4 Conditional roadmap / 89 | No RAM-recording workaround is explained; all recording waits for qualified persistent storage. | A 15-second RAM test produced IR 29.99 Hz, maximum gap 33 ms and zero observed dropped frames; copy to card passed checksum. `/dev/shm` was 3.9 GB; a 100-second take is approximately 1.7 GB. **“Diagnostic only.”** Long-take reliability and storage qualification remain open. | F14 item 4; Tools ownership/limitations. |
| 3.8 Storage qualification / 18; 3.3 Physical platform / 14; 7.2 Current evidence gaps / 87 | The unsuitable 64 GB USB stick is omitted, potentially leaving it as an apparent alternative. | The tested stick is USB 2.0 and achieved 1.09 MB/s with fsync; it is unusable for this recording load. Its data was untouched. Do not substitute capacity for throughput qualification. | F14 item 6; F13 §E payload budget. |
| 4.10 N4B: offline D435i stereo / 61; 7.2 Current evidence gaps / 87; 7.3 Changes since 2026-10-10 / 88 | “Both binaries are built; neither has run on this camera”; “Programs BUILT, never run”; offline mode never run. | Recorder trials now exist: a short still take, an unusable hand-moved card take and a clean short RAM test. The offline estimator smoke test crashed on its first frame. No successful D435i trajectory or N4B qualification is established. | F14 items 2–5. |
| 3.29 Input association / 38 | Notes say “No camera behavior measured.” | Stream delivery has been measured in diagnostic recordings. The helper's complete association/rejection behavior and calibrated timing remain **“Unverified.”** Recording rates alone do not validate the estimator input path. | F14 items 2–5; Plan input/coverage limitations. |
| 4.11 N4C: live stereo scheduling / 64 | “Built” suggests the current executable is ready despite the later crash and interrupted repair. | No successful live estimator run is documented. The first-frame offline crash led to patch 4; rebuilding was interrupted by power loss. Resume and verify the rebuild before a new diagnostic estimator run: **“Rebuild incomplete.”** | F14 item 5 and final plan. |
| 4.9 N4A baseline / 59; 7.2 Current evidence gaps / 87; 7.3 Changes since 2026-10-10 / 88 | Build progress is not explained, or the October 13 three-patch baseline is treated as the latest ready build. | Native ORB-SLAM3 was built with three compatibility patches and completed three EuRoC trials. A fourth patch initializes `LocalMapping::mpCurrentKeyFrame` to `nullptr`; its rebuild is incomplete. Say **“Three initial patches; fourth repair pending rebuild.”** EuRoC did not call the crashing function. | F13 §§C–D; F14 item 5; N4A Setup/Results. |
| 4.9 N4A baseline / 59; 5.8 Accuracy results / 80 | “Done” or measured accuracy could be read as complete qualification. | The three known-dataset trials are complete: mean ATE RMSE 0.040 m, one map, no resets, initialized IMU. N4A remains OPEN because timing was invalid under under-voltage and further acceptance work is pending. D435i accuracy is unverified. | F13 §D; N4A Status, Results, limits. |
| 4.9 N4A baseline / 59; estimator acceptance contract / 60; 5.3 RPE / 76; 5.8 Accuracy results / 80 | N4A RPE is “CALCULATED,” with exact translation/rotation results and pair counts attributed to files outside this ticket's fact sources. | N4A explicitly says “No RPE”; the permitted session facts/addendum supply no RPE results. The deck's later calculation may exist, but is **“Unverified in permitted sources.”** Remove its numbers from the main result and mark the backup claim unverified until the owner extends the evidence set. | N4A “Not verified / limits”; F13 §D; F14. |
| 5.8 Accuracy results / 80 | Paper 0.036 m is shown as a verified ten-run median; notes say its table was verified. | The permitted N4A report and F13 quote approximately 0.036 m from memory and explicitly require table verification. Use **“Paper value unverified”** or omit the comparator. The ten-run statistic is not verified by these experiment sources. Do not import verification solely from either deck. | F13 §D; N4A Results and limits. |
| 5.8 Accuracy results / 80 | Sim(3) values are displayed to six decimal places although the allowed N4A report supports only rounded values. | If retained in backup, use the report's 0.0189 / 0.0238 / 0.0223 m and label scale fitting separately. Additional digits are **“Unverified in permitted sources.”** Main slide needs only rigid-alignment ATE and its meaning. | N4A Results table. |
| 3.28 Numeric IMU settings contract / 37 | “Do not … replace unresolved noise with example values” can imply the current runnable configuration has no numeric noise settings. | Unit-specific noise is unknown, but the development candidate explicitly copies numeric upstream noise values as **ASSUMED**. They enable diagnostics, not calibrated qualification. Keep the continuous-time conversion rules in backup. | F13 §E; Cal “Upstream versus candidate”; Plan. |
| 6.2 Inputs and clocks / 84 | Stereo starts at the retained 15 Hz baseline; emitter-off is only a separate future trial. | N2 remains IR1/15 unchanged. The built N4 development path selects paired IR/30, gyro/200, accel/100 and emitter OFF. Explain projector dots versus scene features; 30 Hz stereo is not N2 qualification. | F13 §E; Plan exact profiles/emitter discussion. |
| 7.4 Conditional roadmap / 89; 8. Conclusion / 90 | “Repair power next” is the entire actionable story; the pending repair, RAM take and actual diagnostic sequence are absent. | Show the addendum's diagnostic plan: resume patch-4 rebuild → 100-second hand-moved RAM take → offline replay and plot → live run. All remain OPEN; the 5 A supply and calibration are still missing. Keep formal N1 → N2 → N3 requirements separate and unchanged. | F14 item 5 and “Tomorrow's shortest path”; Plan prerequisites. |
| 3.3 Physical platform / 14; 4.1 Gate status / 42; 7.2 Current gaps / 87; 8. Conclusion / 90 | An 8 GB board or incoming supply/card could be read as resolving the platform blockers. | The 8 GB Pi showed under-voltage within three minutes on the same 5 V/3 A supply. The 5.1 V/5 A supply and 128 GB card were ordered; no stable-power fix or qualified replacement storage is documented. **“Power unresolved.”** More RAM does not verify rebuild success or real-time speed. | F13 §§A,C,F; F14 items 1,5. |

### Camera identity: already correct, preserve it

Frame 09 and frame 88 already identify the new camera correctly: **SDK serial 317422076650**; **USB descriptor/ASIC serial 327743061057**, firmware 5.17.3.10, BMI085. There is no wrong active serial to replace in the inspected course source. Move full identifiers to notes or an identity backup; the main stream diagram needs the unit change and its consequence.

The September SDK 243322073847 / USB 251843061466 pair in frame 09's notes is explicitly historical. Preserve that distinction. SDK, ASIC, firmware-update ID and USB descriptor serial remain separately named fields even where readback values coincide. Old N1/N2/calibration do not transfer. Sources: F13 §B; Cal “Sources and classifications.”

### Avoid copying unresolved claims from slides_report

The supporting deck helps explain the direct SDK versus planned ROS paths, but it also carries stale “never camera-run” wording. Its “Blockers” frame claims the 8 GB Pi fixes RAM/no-swap and an 8 GB EuRoC rerun is done. Those claims are **unverified in the permitted session facts**; F13 labels swap-free building on 8 GB as inferred, and F14 records an interrupted rebuild. Do not import them into the course audit's current status. Its paper-table verification also does not resolve the experiment sources' explicit caveat. No edits to that deck are proposed or performed by this ticket.

## 3. Missing explanations the owner needs

Ten gaps are listed below. M1–M5 add main frames; M6–M10 replace or improve retained material. Suggested sentences are grounded in the permitted sources; proposed visuals are conceptual illustrations, not experimental evidence.

| ID | Missing explanation | One-sentence suggested slide | Source / destination |
|---|---|---|---|
| M1 | How image features become motion constraints | Show the same fixed scene features matched between stereo views and successive images, then show those matches constraining camera pose. | Plan emitter discussion; course 32–33; new main 12. |
| M2 | What inertial processing does between images | Show gyro and accelerometer samples between two image timestamps, with acceleration interpolated onto gyro times and the interval used for inertial prediction before visual correction. | F13 §E; Plan input association; new main 14. |
| M3 | Why the emitter is OFF | Show that projected dots depend on the camera's projector, while tracking needs features belonging to the fixed scene, so this development profile disables the emitter. | F13 §E; Plan emitter discussion; new main 20. |
| M4 | Why RAM recording addresses the observed failure | Show capture writing to RAM and copying to the card afterwards, explaining that the short test avoided recording gaps but longer reliability remains unverified. | F14 items 3–4; new main 27. |
| M5 | Why a successful baseline and a crash coexist | Show that EuRoC ran with the initial build, while the D435i smoke test called a different function and exposed an uninitialized pointer whose repair still needs rebuilding. | F13 §§C–D; F14 item 5; new main 30. |
| M6 | What the trajectory actually represents | Label the exported pose as the camera IMU/body in the SLAM world, then show that robot-body pose requires the separately defined mount transform. | Plan success observations; `docs/ARCHITECTURE.md`; revise 19/main 10. |
| M7 | Which calibration questions remain unanswered | Separate image projection, sensor geometry, camera–IMU timing and inertial noise, marking factory geometry nominal, noise assumed and physical alignment unverified. | F13 §E; Cal; revise 28/main 21. |
| M8 | What the baseline error means for this project | Overlay estimated and reference paths conceptually, explain ATE as position mismatch after one rotation and translation, and state that about four centimetres on MH01 says nothing yet about D435i accuracy. | F13 §D; N4A; revise 59/80, main 28–29. |
| M9 | Why and how the owner should move the camera | Illustrate translations and rotations followed by a small loop and a still ending, explaining that this diagnostic motion helps inertial initialization and is not target calibration. | F13 §E; Plan success observations; revise 35/main 19. |
| M10 | What each kind of evidence allows the owner to conclude | Contrast completed EuRoC trials, diagnostic camera recordings and still-open hardware/calibration gates, without treating any demonstration as qualified live VIO. | F13/F14; N4A; Plan; revise 42/87, main 35–36. |

## Audit validation and reproduction

Validation is static and local: all document frames and notes were read, dispositions were checked for complete coverage and 5–10-word reasons, and the outline was checked against the KEEP set and five additions. No runtime or hardware validation is implied. The source restriction leaves later RPE calculations, external paper details, successful long RAM recording, completed patch-4 rebuild, calibrated D435i accuracy and real-time performance unverified.

Reproduce the frame count from the repository root without compiling either deck:

```bash
python3 - <<'PY'
from pathlib import Path
import re
text = Path('slides_course/main.tex').read_text()
document = text.split(r'\begin{document}', 1)[1]
frames = re.findall(r'\\begin\{frame\}', document)
print('Explicit document frames:', len(frames))
print('Document section invocations:', len(re.findall(r'\\section(?:\[[^\]]*\])?\{', document)))
PY
```

Inspected source SHA-256 values, for matching this report to another thread's version:

```text
slides_course/main.tex
f96ac47afb5362c51b5219d6a6b4a329b854657f8182bbada669722fab454089
slides_report/main.tex
71c8bcb7889385944ad0c9a63153f9060f0668f2c3f51c802132a959fc617919
experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md
84080e89ae8b5c196ffc760a935c04774c484ec0a43b0f70faf68e487a222cd7
experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md
9dae15c3001c6a39366414054f850f41b6c94b9a6d5a3e9b93385607ecd1c36d
```

Only this `AUDIT.md` was written. Existing ticket material and historical evidence were left unchanged.
