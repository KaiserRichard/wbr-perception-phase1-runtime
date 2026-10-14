# Evidence and provenance

Snapshot: 2026-10-13. All local paths below are relative to the repository root.
Short on-slide labels such as “N4A/REPORT.md” expand through this register.

| Label | Repository path | Used for |
|---|---|---|
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

- Current hardware is the measured temporary **4 GB / 32 GB microSD** Pi, not
  the historical project draft's 8 GB / NVMe target. An 8 GB build without swap
  is inferred in the facts, not demonstrated; the deck makes no such promise.
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
  file-only playback must be checked in the future gated take. The diagram
  uses “SDK recording” and does not imply a qualified ROS 2 bridge.
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
