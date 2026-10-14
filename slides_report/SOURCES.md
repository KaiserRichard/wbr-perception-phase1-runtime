# Evidence and provenance

Snapshot: 2026-10-14; historical baseline: 2026-10-13. All local paths below are relative to the repository root.
Source labels in speaker notes expand through this register; no evidence paths appear on slides.

| Label | Repository path | Used for |
|---|---|---|
| 14 October addendum | `experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md` | Authoritative revision-2 session summary: 8 GB Pi, short camera tests, failed card take, short RAM test, replay crash, patch 4 pending rebuild, USB stick and connectivity |
| 15 October lab runbook | `experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md` | Planned diagnostic demo: entry gates, rebuild, RAM capture, offline replay, plot/review, then live |
| Session facts | `experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md` | Authoritative current inventory, subsequent Pi builds and ordered hardware; §§A–F |
| N4A | `experiments/2026-10-13-n4a-euroc-mh01/` | `REPORT.md`, `provenance.txt`, `eval/ape_summary.txt`, trajectories and `power_window.log` |
| Pi snapshot | `experiments/2026-10-13-pi5-env-snapshot/` | `ADDENDUM_CAMERA_SWAP.md`, new-unit enumeration, calibration readback and tooling report |
| Pi build | `experiments/2026-10-13-orbslam3-pi-build/` | `build_orbslam3.sh`; summary identifies additional raw build/patch evidence on the Pi |
| N4B prep | `experiments/2026-10-13-n4b-d435i-prep/` | `n4b_plan.md`, `verification.md`, recorder, adapter patch, helpers and YAML |
| Phase A runbook | `experiments/2026-09-12-pi5-native-sensor-validation/PHASE_A_RUNBOOK.md` | Unchanged N1→N2→N3 dependency, exact raw profile and soak |
| Course gate contracts | `slides_course/main.tex` §§4.1–4.14 | Consistent N0–N7 definitions and acceptance criteria |
| Current-gate draft | `docs/NEXT_GATE.md` | OPEN N3 record/replay questions; not acceptance evidence |
| Project-state draft | `docs/PROJECT_STATE.md` | Read as historical/unverified; current session summary takes precedence |
| Ownership / evaluation planning | `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/ORB_SLAM3_OFFLINE_PREPARATION.md` | STM32 boundary, clocks, planned metrics and authorization |
| Sensor illustration | `slides_course/images/P04.png` → `slides_report/images/P04.png` | Reused conceptual image; no physical validation |

## Paper verification

Campos et al., *ORB-SLAM3: An Accurate Open-Source Library for Visual,
Visual-Inertial, and Multi-Map SLAM*, IEEE T-RO, 2021,
[DOI](https://doi.org/10.1109/TRO.2021.3075644).
Verified on 2026-10-13 against the
[accepted author manuscript, arXiv:2007.11898v2](https://arxiv.org/pdf/2007.11898v2):
Table II, PDF page 12 (printed page 11), ORB-SLAM3 stereo-inertial ATE row,
MH01 column: **0.036 m**. Section VII-A says results are medians of ten
executions. This corrects the source summary's “quoted from memory” limitation
for this deck only; the original experiment report is unchanged.

Our table uses three individual rigid-alignment RMSE values, not a median of
ten trials. Local unrounded results: 0.041461 / 0.036844 / 0.041604 m. Their
mean is 0.0399697 m (slide: 0.040 m); median 0.041461 m (slide: 0.0415 m).
The comparison supports similar accuracy on one sequence; it does not establish
exact statistical reproduction, real-time performance or broad correctness.

## Limits and resolved conflicts

- Active hardware is now the **8 GB Pi (7.8 GiB measured), same 32 GB microSD**. The 4 GB measurements remain historical N4A/build evidence. The addendum supersedes prior risk-table thread reports: no completed no-swap build or new measured EuRoC result is claimed. Power remains unresolved on the new board.
- `provenance.txt` records kernel 6.8.0-1065-raspi whereas the inventory summary
  mentions 6.8.0-1064-raspi. No single kernel version is asserted on-slide;
  original records are preserved and runtime hashes remain in provenance.
- The new camera SDK serial is **317422076650**; USB descriptor serial is
  **327743061057**. SDK/ASIC/firmware-update/descriptor fields remain distinct;
  old-unit receipts are not transferable.
- The authoritative summary reports native Pi builds and clean linkage for
  the recorder/adapter. The local Mac `verification.md` predates those builds
  and establishes only offline/synthetic helper behavior. Slides attribute
  the later build to the session summary, not to newly collected runtime logs.
- Recorder source and session facts name `stereo_imu.db3`. Earlier prep prose
  still describes `.bag`; the actual installed SDK container and successful
  file-only playback remains unqualified: first-frame replay crashed. Patch 4 initializes the current-keyframe pointer to nullptr; rebuild was interrupted by power loss. EuRoC never called the failing query; its historical results remain unchanged. The owner’s direct-library vs planned ROS 2 diagram is retained.
- N2 stays **IR1 640×480 Y8/15; gyro 200; accel 100 Hz**, 20→105→**300 s**.
  The N4 adapter's **two IR streams at 30 Hz** are an additional development
  profile, not a replacement or waiver. Rate/gap/content/health criteria remain
  unchanged. Calibration warning is retained verbatim in the deck.
- **87/178 = 48.9%**, rounded 49%, is the proportion of sampled live power
  flags. It is not an event count or exact elapsed-time duty cycle. Historical
  flags in the other 91 samples do not establish clean N0 power.
- Wall time includes vocabulary loading and was measured under faults; no
  per-frame latency or real-time acceptance is inferred from it. Pi UTC labels
  were offset by about 80 minutes before NTP correction.
- Stereo image payload is 18.432 MB/s in decimal units, before overhead. The
  17–19 MB/s probe is historical, not current recording qualification. Planned
  95 GB capacity implies about 57–86 image-only full takes; “55–90” preserves
  the source's approximate estimate, not a guaranteed take count.
- IMU noise is ASSUMED; factory geometry is nominal. No D435i ground truth,
  calibrated VIO, qualified live performance or robot-safety result exists.

No historical evidence, source utility, upstream source or project document was
modified. No raw evidence was manufactured and no gate was declared PASS.

## Revision 2 evidence limits

- 20 s still take delivered stereo/gyro/accel for 19 s, with a roughly 0.7 s shutdown gap. This is a diagnostic streaming observation, not N2 acceptance.
- 100 s moving take on microSD was unusable: gaps 0.3–2.9 s after 22 s; 1.66 GB / 100 s = 16.6 MB/s vs calculated 18.432 MB/s image payload. MicroSD blocking is a strong inference, not an isolated causal test. No kernel under-voltage or USB errors appeared during that take; this does not establish clean platform power.
- RAM recording is measured only for 15 s: IR 29.99 Hz, max gap 33 ms, zero dropped frames, gyro 200.2 Hz, accel 101 Hz; copied-take checksum OK. Successful 100 s RAM capture and post-patch replay remain unverified.
- RAM allocation 3.9 GB and estimated 100 s take 1.7 GB are planning budgets; full image-only payload is 1.8432 GB before overhead. Capacity and retained counts must be checked anew. RAM is a temporary diagnostic workaround; card staging is not qualified dataset storage.
- USB stick sustained-write probe is 1.09 MB/s with fsync, insufficient for recording; its data was untouched. Loose Ethernet and unverified 8 GB Wi-Fi remain connection risks in notes.
- The lab runbook is future work, not evidence of execution. N1 → N2 → N3, USB ≥5000M, exact N2 profile/timing thresholds and mandatory 300 s soak remain unchanged. A 100 s stereo demo cannot replace them. Room trajectory has no ground truth; calibrated accuracy and live performance remain OPEN.

Revision 2 changes only report files. Sources are read as historical/session-reported evidence; no camera, ORB-SLAM3, SSH, rebuild or helper execution occurred.
