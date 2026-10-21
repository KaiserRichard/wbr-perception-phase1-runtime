# Camera day — visual pose milestone and replay results

2026-10-21 +07. **Visual stereo/RGB-D and ROS pose demonstrated. Sustained
stereo-inertial tracking remains unresolved.** No gate or accuracy approval.

## Actually run
- Pi: aarch64, 3.9 GiB RAM; SG128 card boots with expanded 113 GiB root.
- Borrowed D435i `317422076650`, firmware `5.17.3.10`, USB 5000M, mount retained
  on mobile robot. No calibration write, firmware change or motor command.
- Native viewer disabled (`false`); no Xvfb used for final native runs.
- Stationary 30-second trials: stereo 30 Hz/1,250 features tracked 27.96 FPS
  with 45 application callback overwrites; clean 30 Hz/800-feature repeat tracked
  29.76 FPS with zero overwrites; 15 Hz/800 tracked 14.90 FPS. All zero observed
  tracking-loss transitions. These short stationary runs do not establish moving
  performance. Initial 800-feature trial overlapped compilation and is excluded
  from the clean comparison; final helpers also add cleanup instrumentation.
- Native RGB-D 15 Hz/800 tracked 14.65 FPS, zero observed loss transitions.
  Both visual modes published real `PoseStamped` in ROS 2; RGB-D topic rate
  reached 14.79 Hz in a short CLI window. Pose optical frame, not robot-body pose.
- Stereo-inertial ran twice with SDK-derived camera-to-IMU transform and assumed
  upstream noise settings. Initialization was transient, followed by motion/bad-IMU
  resets; final trajectories empty. Source threshold was not relaxed.
- `vcgencmd get_throttled`: `0x0` in all recorded native/replay before/after checks.

## One cart recording, three fresh replays
Use **loop03**, captured 09:00:30–09:03:00 despite chat quota interruption. Bag
contains 148.18 s, 1.9 GiB: 1,928 left / 2,219 right / 1,203 depth images.
Recorder reported **1,318 transport-lost messages**. Owner reports returning after
about 120 s and standing still for the final 30 s; position/heading alignment was
not independently measured. Loop01/02 remain evidence but have endpoint errors.

Each replay used a new estimator, 640×480/15 Hz/800 features, 0.5× playback,
identical YAML and the same hashed sensor bag. Only sensor topics were played;
old pose/status topics were excluded. All estimator/player/recorder/export exits
were zero. Each produced 1,924 statuses with contiguous processed counters and
matched the first and last recorded left-image stamps; four recorded left images
had no observed status. Original camera frames already missing from the bag
cannot be recovered. These are partial tracking histories, not complete capture.

| Replay | Endpoint m* | % estimated path* | Path m* | Poses / processed | Loss episodes | Loop detected | Maps / merges |
|---|---:|---:|---:|---:|---:|---|---|
| Replay 1 | 0.6963 | 3.379% | 20.605 | 1723 / 1924 | 15 | yes | 4 / 3 |
| Replay 2 | 0.6957 | 3.386% | 20.545 | 1819 / 1924 | 18 | yes | 2 / 1 |
| Replay 3 | 0.6927 | 3.339% | 20.748 | 1690 / 1924 | 15 | no | 4 / 2 |

*Endpoint = Euclidean distance between first/last exported online poses;
path = sum of consecutive 3D pose distances; percent = 100 × endpoint/path.
**These numbers are not pure drift accuracy:** losses, resets, relocalizations and
map merges can jump the online world frame and inflate path length. No external
ground truth or final globally optimized atlas trajectory was used. Similar
endpoint values do not imply similar intermediate trajectories or accuracy.

“Loop detected” is an explicit ORB `*Loop detected` event; “no” means absent from
that run's complete saved log. Completed loop correction is UNKNOWN; map merges
are counted separately. Loss episodes are observed OK→lost transitions, not every
lost frame. Replay internal tracking FPS is unavailable: ROS status has no steady
processing timestamps; neither bag timestamps nor slowed playback are substituted.

## Evidence and reproduction
- Pi evidence: `/home/richard/wbr-evidence/camera-day-20261021-01/`.
- Raw input: `ros-stereo-loop-03/sensor-bag/`; SHA-256 of `sensor-bag_0.db3`:
  `b4f28e61d3d90cb547b4bf6e85cd6ff2236816ac255d0a70ab5f7c2f90438e1a`.
- Batch: `loop03-replays-01/`: supervisor source, progress, three run logs,
  small output bags, TUM files, frame CSVs, export hashes and coverage receipts.
- Mac archive: `~/wbr-evidence-archive/camera-day-20261021-01-final/`;
  `analysis/results.json`, `analysis/replay_metrics.md` and trajectory figure.
  Bulk sensor bags remain on Pi; copied small output bags match exporter hashes.
- Actual commands: serial `cmake --build .../wbr-camera-ros-build-20261021-04/build/wbr_orb_node --parallel 1`;
  native launches/settings and build recipes in [native README](../../../scripts/camera_day/native/README.md);
  exact capture/replay commands in archived `capture_loop.py` and `replay_batch.py`.
  Replay scripts require fresh output directories; existing evidence is protected.
- Conductor independently passed 7 native-helper, 18 metric and 14 exporter tests,
  rebuilt ROS binaries, checked library resolution, and exported real recordings.
- Final full SDK calibration readback is byte-identical to the initial readback
  (SHA-256 `567c08f57953aef175577550314cfe37ff0b704c54a0a641c6eabdc8dd57baef`).
  Temporary receive-buffer sysctls restored to 212,992 bytes; all owned camera/
  replay processes stopped. Initial Xvfb install remains present but unused.

## Merged implementation PRs
[77 — native ROS build/link](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/77),
[79 — replay metrics](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/79),
[80 — headless native runs](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/80),
[81 — pose/status export](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/81).
All merged after current-head CI passed; this report itself is not Claude approval.

## Recommendation for Claude review
Accept the visual bring-up as demonstrated; do not accept robust mapping, pure
endpoint-drift accuracy, qualified recording or sustained inertial tracking.
Next isolate recorder transport losses with a focused change, then retry motion
with continuous-map tracking and suitable IMU excitation while preserving the
borrowed mount. No thresholds, calibration or robot-control ownership changes.
