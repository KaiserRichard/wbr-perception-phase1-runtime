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

## Claude review

Reviewed 2026-10-21 on main b3ae906. I read this report only; I ran nothing.

**Verdict: the visual bring-up is accepted.** ORB-SLAM3 stereo and RGB-D run live
on the Pi 5 with the viewer off: about 30 FPS stereo when stationary, about 15 FPS
RGB-D. Both publish a ROS 2 pose, and there is no throttling. That is the
milestone.

Not accepted yet: recording quality, accuracy, and stereo-inertial.

1. **The recording is the main problem. Fix it before trusting any replay
   numbers.**
   - At 15 Hz for 148 s we'd expect about 2,220 frames per stream. We got:

     | Stream | Frames | Missing |
     | --- | ---: | ---: |
     | Left | 1,928 | ~13% |
     | Right | 2,219 | about none |
     | Depth | 1,203 | ~46% |

   - The recorder also reported 1,318 transport-lost messages.
   - A missing left image breaks the stereo pair, so many of the 15-18 loss
     episodes are probably recording gaps, not SLAM failures.
   - Likely cause (inferred): large raw images going over DDS into the sqlite3
     recorder.
   - Try, one at a time:
     - (a) `ros2 bag record -s mcap`;
     - (b) record only infra1 + infra2 + camera_info for the stereo test (drop
       depth, or record a separate RGB-D bag);
     - (c) a QoS override to reliable, with depth 50+ for the image topics;
     - (d) keep the larger socket receive buffer for the session
       (`net.core.rmem_max`).
   - Success = less than 1% missing frames per stream, with left and right
     counts equal within a few frames.
2. **Endpoint drift (~0.69 m, about 3.4%):** fine as a first number, but not
   yet an accuracy result.
   - Mark the start/end spot on the floor and return to it.
   - Report the endpoint again on a bag that meets the frame-count criterion
     above.
   - Getting the same number in all 3 replays shows the pipeline is
     repeatable, not that it is accurate.
3. **Stereo-inertial (D435i): debug in this order.**
   - (a) **Tbc direction.** ORB-SLAM3 wants the body(IMU)-from-camera
     transform; the SDK gives camera-to-IMU extrinsics, so the inverse is a
     common bug.
   - (b) **IMU rate and units.** Use unified accel+gyro (`unite_imu_method`
     linear interpolation), with `IMU.Frequency` matching the real rate
     (200 or 400 Hz), accel in m/s^2 and gyro in rad/s.
   - (c) **Excitation.** In the first 10-15 s, rotate and accelerate the camera
     smoothly on all axes, then move normally. A slow cart motion is often not
     enough to initialize.
4. **Frame:** the pose is the camera's optical frame. Add the static camera-to-
   base TF before any robot integration.

Next order: fix the recording (1), then re-record the loop and replay it 3
times (2), then stereo-inertial (3).
