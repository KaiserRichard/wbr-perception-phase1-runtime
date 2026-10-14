# Phase-6 sources and provenance — 2026-10-13

Read FINAL deck A (`slides_report/main.tex`, README, SOURCES, REVIEW_LOG) and FINAL deck B (`slides_progress/main.tex`, README, REVIEW_LOG) before curation. Their role split guides cuts: A is advisor summary; B teaches today's build/evaluation/programs/next steps; C retains detailed operational contracts and diagrams.

The pre-curation `main-v3-109p.tex` was already present and byte-identical to incoming `main.tex` (SHA-256 `87bebeaba4369818ebc07fe15c57305799c671570321bcc7adca5ec98874126e`); preserved rather than overwritten. The matching PDF backup and all Phase-1–5 historical QA records remain unchanged. Current branch `claude/project-thread-rhsrup`, HEAD `da4d630`; inspected Git status/history, no mutation.

October sources (repository-relative):

- `experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md`: authoritative inventory, new camera fields and subsequent Pi build status. The older Mac verification receipt remains historical; successful Pi build is reported by these facts, not independently inspected in this task.
- `experiments/2026-10-13-n4a-euroc-mh01/REPORT.md`: rigid-alignment ATE 0.0415 / 0.0368 / 0.0416 m; mean 0.040 m; one map/no resets/initialized each run; durations 301 / 282 / 284 s; RSS 823 / 828 / 828 MiB; 87/178 live-power samples and maximum sampled 63 °C. These are saved historical trial observations, not new runs.
- `experiments/2026-10-13-pi5-env-snapshot/ADDENDUM_CAMERA_SWAP.md`: device 317422076650; descriptor / ASIC value 327743061057; 5000 Mbps enumeration only. Firmware-update ID remains separately recorded, not inferred from another serial field. Old-unit receipts do not transfer.
- `experiments/2026-10-13-n4b-d435i-prep/`: `verification.md`, `d435i_input.h`, candidate YAML, calibration notes and plan. Helper fixtures are offline/synthetic only; factory transform NOMINAL, unit noise ASSUMED, time offset UNKNOWN. Candidate SDK recorder/estimator are built, never run on the camera.
- `experiments/2026-10-13-orbslam3-pi-build/`: build provenance is summarized in facts/B; no additional build or upstream edit here.
- Existing C sources and gate contracts remain as audited in `PHASE3_SOURCES.md`. Exact USB >=5000M, raw profiles, rate/gap thresholds and mandatory 300-second soak are unchanged. Full teaching text and commands from merged pages are retained in destination speaker notes, including `accept-n2`.

Re-verified [Campos et al., accepted T-RO manuscript, arXiv:2007.11898v2](https://arxiv.org/pdf/2007.11898v2): Table II, PDF page 12, MH01 stereo-inertial ATE = 0.036 m; §VII-A uses median of ten executions. Our three-run mean is a different statistic. Similar magnitude on one dataset supports this algorithm/build path, not statistical equivalence, D435i accuracy, real-time operation or robot qualification. Original source reports are not modified.

N4A remains OPEN under C's inherited acceptance contract: N0 power prerequisite unresolved, ATE/RPE contract incomplete, accepted accuracy/continuity budgets UNKNOWN. Stable-power rerun and acceptance review remain required. Ordered supply/card do not qualify power or bulk storage. The temporary 4 GB / 32 GB microSD inventory does not replace the 8 GB / qualified storage target.

Inherited OS academic Beamer skill, template preamble and layout/playbook/reviewer rules read through read-only Git/files. Same preamble/theme/fonts/palette/canvas retained. No camera, capture, ORB experiment, Pi/SSH, network, firmware, calibration, controller, install, deployment, Git index/branch/stash/commit/push action. Document builds/QA only. The Phase-6-specific authorization permits only B's reference-number edits plus rebuild outside C; all other user work preserved.
