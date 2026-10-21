# Clean marked-loop stereo replays — Intel Mac, 2026-10-21

**Result:** exactly three successful fresh headless visual-stereo replays. Every
run processed all 2,215 recorded pairs. Tracking/map behaviour was not identical;
replay 3 lost tracking and merged a second map, despite its small endpoint.

## Input, runtime and traceability

- PPO release verified: supervisor EXITED0 at 05:13:27 UTC, final batch COMPLETE,
  no batch workers. Work began after this gate; no Pi/control/training changes.
- Archive: `~/wbr-evidence-archive/camera-recording-20261021-01/clean-loop-mac-01/`.
  Original: adjacent `mcap-marked-loop-01/sensor-bag/sensor-bag_0.mcap`.
- MCAP SHA256: `5749908bb94a6c9a7e5496f3c8b58db3596cf5f53f2542502a1468dcd97703c8`.
- Settings SHA256: `889b17951bf0994ae0177e307eb77d9ac0742e25deeacce9d88ca868ef8bebe4`.
  SDK-derived rectified D435i intrinsics/baseline; 640×480, 15 Hz, 800 features.
- Host: Intel Mac / macOS 15.7.9; Ubuntu 22.04 x86_64 Docker, 4 CPUs / 5 GiB.
  GCC 11 / OpenCV 4.5.4. These are **Mac results, not Pi performance**.
- Tool commit: `da905cd814a52596da45a633767898225fa624f7`; archived source tar.
  ORB `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`, Pangolin
  `7364b59a58045d1c429b146e44f6f088fd1cc518`. Full compatibility diff and
  source/runner/vocabulary/203 loaded-library hashes: `runtime-provenance-measured.json`.
- Local ORB compatibility: C++17, portable ISA flags, private bool generation
  counter→int, and skip an invalid Rectified camera2 diagnostic dereference.
  This differs from the accepted Pi source/binary; no binary-equivalence claim.
- Merged prerequisites: [PR87](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/87),
  accepted review [PR88](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/88),
  follow-ups/queue [PR90](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/90).
  Milestone publication: [PR92](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/92);
  final current-head CI/merge receipt is saved in the archive.

## Results

Endpoint is first-to-last **online tracked camera pose** separation. Percentage
is 100×endpoint / sum of consecutive online-pose distances.

| Replay | Endpoint m | Estimated path m | Endpoint % | Tracked / processed | Measured tracked FPS |
|---|---:|---:|---:|---|---:|
| 1 | 0.018319 | 14.267 | 0.128 | 2215 / 2215 | 15.005 |
| 2 | 0.005408 | 14.322 | 0.038 | 2215 / 2215 | 15.004 |
| 3 | 0.006263 | 15.997 | 0.039 | 2152 / 2215 | 14.578 |

| Replay | Completed reset markers | New maps after initial | Merges completed | Loss transitions | Loop detected |
|---|---:|---:|---:|---:|---|
| 1 | 0 | 0 | 0 | 0 | no |
| 2 | 0 | 0 | 0 | 0 | yes |
| 3 | 0 | 1 | 1 | 2 | no |

All runs started with one map. Replay 3 then created map 1 and completed one
merge; zero reset markers does not mean uninterrupted tracking. Its 63
nontracked frames are tracking failures, not missing recorded input. Replay 2
logged `*Loop detected`; completed loop correction is not independently
established by this log. Replay 3 logged a merge, distinct from loop detection.

## Timing and resource scopes

Tracked FPS = tracked frames / steady first Track start to last Track end,
including pacing/IO. Each run used original timestamp differences at 1×.
Recorded header span is 147.606893311 s; interval rate is 14.999299493 Hz.
Track-compute quotient excludes pacing/IO and is **not an unpaced capacity test**.

| Replay | Steady span s | Sum TrackStereo s | Track-compute quotient FPS | Track call p95 ms | Average CPU % | Sampled peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 147.621720 | 51.445 | 43.056 | 36.07 | 114.9 | 589.6 |
| 2 | 147.622730 | 74.396 | 29.773 | 71.59 | 154.0 | 593.1 |
| 3 | 147.620149 | 54.970 | 39.149 | 39.53 | 121.1 | 599.2 |

CPU uses full process lifetime (loading/shutdown included), one core=100%;
RSS was sampled every 200 ms. Steady tracking spans exclude loading/shutdown.
Full process walls were 154.115 / 154.434 / 155.592 s. No power/thermal,
sensor-to-output latency or Pi throttling measurement is claimed here.

## What was actually verified

- Four tiny MCAP fixture tests and 18 existing replay-metric tests PASS.
- Native build05/link PASS; three measured processes exit0 and finish workers.
- Original MCAP hash rechecked. Decoder preserved all 2,215 exact matching
  stereo headers and round-tripped every PNG against original mono8 pixels.
- Independent copied-evidence validation PASS: all original headers match
  attempts/completions in order, counters 1…2215, zero application drops,
  finite published poses, first/last input stamps retained, recomputed
  endpoints/path/FPS and sums agree. No completed run was selected/discarded.
- Retained actual failures: Pi-local revision not upstream; C++17 bool++;
  missing explicit g2o build; CMake cache source-path mismatch; Python3.10
  hash API; transient partial shared-file read; one pre-frame startup SIGSEGV.
  That failed startup made zero Track calls and is separate from these runs.

Reproduce with `scripts/camera_day/offline/README.md`. Exact successful
commands are in archived `commands.md` and `three-replays-02/progress.json`.
Raw timing/poses/map events/stdout: `three-replays-02/`; analysis:
`analysis-02/`; independent checks: `validate_results.py` and
`independent-validation.json`; full errors/exits: `logs-final/`.

## Interpretation and remaining limits

The endpoint separations are 1.83 / 0.54 / 0.63 cm, but they do not establish
accuracy or identical tracking across runs. Start/end alignment is reported
by the owner, without independent ground truth. Online coordinates can jump
at optimization, loss/reinitialization or merge: replay 3 has a 1.115 m
maximum consecutive online-pose step. Its path/percentage include that effect.
Replay 2 also has a loop-detection event and a 0.127 m maximum pose step.
No older lossy-loop endpoint was reused. Native IMU callback fault injection
from PR90 remains a separate deferred SDK task; these runs are visual only.

Recommendation for review: accept complete input coverage and the reported
repeatability limits; do not turn small endpoint values into a drift-accuracy
or robust-tracking claim. Review the map events before comparing trajectories.
