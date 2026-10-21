# Headless stereo replay on an Intel Mac through Linux Docker

This path consumes a finalized stereo MCAP without camera/Pi access. The
recorded images go directly to native `ORB_SLAM3::System::STEREO`, viewer off;
there is no ROS graph, DDS transport, motor interface or calibration write.
The existing ROS/Pi launch path is unchanged. This measures another platform,
not Raspberry Pi performance.

Do not install/build/convert/replay on the Mac while the owner's PPO v2 batch
is active. The queued task requires terminal supervisor/batch receipts and no
remaining training/evaluation workers. Pi use needs a fresh owner release.

## Runtime and execution

`Dockerfile` captures the dependency/source provisioning. The actual session
used the same steps interactively in an exclusive container; setup failures and
repair logs remain in the archive. To reproduce the provisioning image:

```bash
docker build -t wbr-offline-stereo scripts/camera_day/offline
```


Use an isolated Ubuntu 22.04 container with bounded resources (the actual run
uses 4 CPUs / 5 GiB), a read-only input archive, and a read-only repository mount.
Inside the container install `build-essential cmake git ca-certificates
libopencv-dev libeigen3-dev libboost-serialization-dev libssl-dev libglew-dev
libgl1-mesa-dev libepoxy-dev python3-pip python3-numpy python3-opencv zlib1g-dev
libjpeg-dev libpng-dev`. Install `rosbags==0.11.0` for offline CDR/MCAP decoding.
No ROS installation or RealSense SDK is required for visual replay.

Create `/work/Pangolin` at v0.9.1, commit
`7364b59a58045d1c429b146e44f6f088fd1cc518`, and `/work/ORB_SLAM3` at
`4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4` (the repository submodule
pin). The Pi local build revision `727f3cbd` is not an upstream tree. Preserve exact
commit IDs, local compatibility diff and library hashes
in the result archive. The builder applies the same C++17/portable-ISA choices
as the existing Pi build, only in this isolated source copy. It also changes
the upstream private `mnFullBAIdx` generation counter from bool to int because
C++17 rejects incrementing bool. The full diff is retained, and this is a source
compatibility difference from the accepted Pi binary. A second local fix skips
the diagnostic camera2 print for Rectified input: upstream never allocates that
object for this mode. This fixes a pre-frame startup crash without changing the
calibration/model used for tracking. Build g2o explicitly before linking ORB:

```bash
bash /repo/scripts/camera_day/offline/build_runtime.sh /work /repo
python3 /repo/scripts/camera_day/offline/extract_stereo.py \
  /evidence/mcap-marked-loop-01/sensor-bag /work/clean-pairs-03 --expected-pairs 2215
python3 /repo/scripts/camera_day/offline/run_batch.py \
  /work/runner-build/replay_stereo /work/ORB_SLAM3/Vocabulary/ORBvoc.txt \
  /evidence/mcap-marked-loop-01/stereo.yaml /work/clean-pairs-03 /work/three-replays \
  --pace-rate 1
python3 /repo/scripts/camera_day/offline/analyze_batch.py \
  /work/three-replays /work/analysis
```

All evidence output directories are exclusive-created. Retain failed logs and
use a different path for any repair/retry. Input timestamps remain integer
nanoseconds in manifests/poses; ORB's interface receives double seconds. Decode
only IR1/IR2; both header lists must be identical and contain2215frames. Mono8
pixels are stored as lossless PNGs; each PNG is decoded again and compared with
the original pixels. No sorting, trimming, dropped-frame filling or calibration
transformation occurs. The saved YAML must match640×480/15Hz/800features and the
borrowed D435i's read-only SDK-derived intrinsics/baseline.

Each replay starts a separate process/System/atlas. Every pair is processed once
in reader order, paced against recorded source differences. Slow processing can
run behind schedule, but this runner never drops pairs to catch up. Outputs:

- `attempts.csv`: flushed immediately before each Track call, so an incomplete
  call is distinguishable from a completed frame row.
- `frames.csv`: source timestamp, ORB tracking state, publication flag, cumulative
  processed count, zero application drops, steady Track start/end and map ID.
- `CameraTrajectory.txt`: finite tracked online camera poses, original source
  stamps. World frame may jump at resets/merges/closure; no continuous odometry.
- `map-events.csv`: current-map ID changes (including initial map), which may
  reflect resets or merges. Native stdout reset/new-map/merge markers are counted
  separately; a current-map change is not automatically a reset.
- `FinalAtlasTrajectory.txt` and `KeyFrameTrajectory.txt`: separate final exports
  for context; they may cover only an atlas subset. Online endpoint metrics use
  the explicitly named online trajectory, not a stitched final map.
- `summary.json`, batch commands/exits/progress and complete stdout logs.

Tracked FPS = tracked calls divided by the measured first Track start to last
Track end, including pacing/IO gaps. Track-compute FPS = tracked calls divided
by the sum of all TrackStereo call durations, including nontracked calls but
excluding pacing/IO. Neither is substituted with nominal15Hz or recorded source
rate. Loop detection does not alone prove completed loop correction.

Endpoint = first-to-last online pose distance; path = sum of consecutive online
pose distances; percent=100×endpoint/path. Physical start/end alignment is
owner-reported, not ground truth. Resets/merges/loop closure can jump coordinates
and inflate path; do not interpret these as pure continuous-map drift accuracy.

## Verification and limitations

Actual validation must include successful native compile/link, MCAP extraction
receipt/hash,2215equal image headers and pixel round-trips, three zero exits,
2215contiguous processed rows per run, finite trajectories and source boundaries.
Failure symptoms include mismatched pairs/types/size, malformed timestamps,
nonzero process exits, missing summaries, worker shutdown timeout or differing
pose/publication counts. Keep the failed run as evidence.

Rollback: use the existing ROS/Pi replay tools when that platform is authorized;
new files/container can be left idle. No original source, bag, camera settings,
training environment or robot runtime is overwritten. Large datasets, extracted
images, binaries, dependency downloads and raw logs stay outside git.

For the decoder's small MCAP fixture tests (inside this container):

```bash
python3 -m unittest discover -s /repo/scripts/camera_day/offline \
  -p test_extract_stereo.py -v
```

Tests cover stride-aware pixel preservation and integer source stamps, duplicate
and mismatched header rejection, wrong type/count rejection, and exclusive output
creation. They do not establish native tracking or endpoint accuracy.

## Archived TrackStereo frame budget

Analyze the three already completed runs without starting a replay or Docker
workload. The input directory must contain `replay-1/frames.csv` through
`replay-3/frames.csv`; output is exclusive-created:

```bash
python3 scripts/camera_day/offline/track_budget.py \
  /path/to/three-replays-02 /path/to/new-j-budget-output
```

The reader rejects a changed header, malformed rows, non-increasing source
stamps, non-contiguous processed counters, and non-positive or overlapping
serial Track intervals. It counts all calls strictly above 66.7 ms using
integer nanoseconds and also reports the exact 1/15 s test
`15 * duration_ns > 1,000,000,000`. Each run's directory contains a JSON
summary plus a histogram CSV and SVG. Histogram bins are shared across runs,
lower-inclusive/upper-exclusive milliseconds, and account for every call.
Percentiles use nearest rank; tracked-only counts select
`pose_published=true` as logged by the replay runner.

These no-drop 1× offline replays absorb compute overruns. Counts are budget
misses, not observed live camera drops or a direct forecast of latest-image
queue drops. Measurements are from Intel Mac x86_64 Docker and do not transfer
to the Pi.

Focused tests:

```bash
python3 -m unittest discover -s scripts/camera_day/offline -p test_track_budget.py -v
```
