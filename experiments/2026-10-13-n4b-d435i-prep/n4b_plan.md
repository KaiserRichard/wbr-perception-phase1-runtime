# N4B offline and N4C live — OPEN

Prepared on the Mac only. No camera, SDK process, ORB executable, SSH, network,
installation, commit or push was run. Every gate is **OPEN**. Commands below
are future **local Pi terminal** instructions, not evidence of execution.

## Shortest credible sequence

1. Finish the already initiated native Pi build in `~/orbslam3/ORB_SLAM3`.
   Pangolin 0.9.1 / C++17 and that path are supplied task context, not newly
   verified artifacts. Preserve native build fixes/logs; inspect compiler/link
   flags, source identity and library hashes once the build finishes.
2. After the user explicitly says **CAMERA AVAILABLE**, requalify the new unit
   using [Phase A N1→N2→N3](../2026-09-12-pi5-native-sensor-validation/PHASE_A_RUNBOOK.md).
   [NEXT_GATE](../../docs/NEXT_GATE.md) still identifies N3; this proposal does
   not advance it or waive it. Old-unit receipts do not transfer. Fresh N1 must
   select SDK `317422076650` and separately attest descriptor `327743061057`,
   USB **≥5000M**, permissions, stable power/cooling and actual topology.
   Correct old hard-coded SDK selection in a separately reviewed runtime bundle.
3. N2 stays **IR1 Y8 640×480/15, gyro/200, accel/100**, native raw streams,
   20 s → 105 s → mandatory **300 s soak**. Keep all timing thresholds: IR
   14.25–15.75 Hz, gyro 190–210, accel 95–105, image gaps ≤0.20 s, motion gaps
   ≤0.05 s, positive stamp/frame steps, no missing image frame numbers, original
   health/fault criteria and raw logs. Qualify separate dataset storage before
   recording; take fresh N1 after its qualification. Complete the unresolved N3
   record/replay and timing evidence without live/replay contamination.
4. Build this isolated example and recorder against the completed native
   libraries. Capture a **60–90 s** guided take with both IR streams **30 Hz**,
   gyro **200 Hz**, accel **100 Hz**, emitter OFF, no other camera process.
   This is an additional N4 development profile, not a replacement N2 profile.
   Attest actual stereo delivery and timing independently at 30 Hz.
5. Finalize/hash the librealsense bag and logs. Inspect decoded IR pixels,
   stream inventory, counts, domains, motion and boundary coverage. Run the
   same driver with `--bag ... --no-viewer` for N4B. Repeat on the identical
   immutable bag and YAML; preserve all failures and run-specific outputs.
6. Only after review of N4B input/initialization/tracking evidence, use that
   binary and YAML without `--bag` for N4C. Measure live processing, dropped
   frames, health and latency. Neither milestone constitutes calibrated VIO
   accuracy. Allan variance, IMU intrinsic/extrinsic and temporal calibration
   remain prerequisites to N4 qualification.

## One input path and exact profiles

The [unapplied patch](stereo_inertial_d435i_file.patch) targets only
`Examples/Stereo-Inertial/stereo_inertial_realsense_D435i.cc` at
`4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`. Copy the two supporting headers
[d435i_input.h](d435i_input.h) and [d435i_rs.h](d435i_rs.h) alongside the patched
example. No core algorithm, System API, CMake file, node graph or custom dataset
format change is proposed. This replaces the example's fragile acquisition
section; merely adding two flags would leave known input errors in place.
The original GPL notice remains on the patched source.

- `--bag FILE` uses `rs2::config::enable_device_from_file(FILE,false)` (no
  looping). Resolve the recorded device without querying physical cameras and
  set `rs2::playback::set_real_time(false)` **before** pipeline start. The file
  branch does not write live sensor options and does not substitute arrival
  time for recorded timestamps. Disconnecting the camera is a useful future
  file-only validation after CAMERA AVAILABLE, not a present requirement.
- `--no-viewer` supplies `false` to the existing System viewer argument. The
  default still enables it. Headless runtime still links Pangolin because the
  upstream library and included headers require it.
- Both branches explicitly select IR1/IR2 **Y8 640×480/30**, gyro
  **MOTION_XYZ32F/200**, accel **MOTION_XYZ32F/100** and verify the resolved
  profiles and SDK serial. No depth/RGB stream or rate fallback is allowed.
  The new enumeration lists accel **400/200/100**, gyro **400/200**; **250 Hz
  is not supported by this unit's readback**. The upstream example explicitly
  requests IR/30 but leaves both motion rates unspecified; its 200/60 Hz
  comments are not a capability measurement. IMU.Frequency 200 is the resulting
  gyro-grid input rate, with bracketed accel interpolation.
- The shared input helper rejects nonfinite and duplicate/backward samples,
  rejects interior motion gaps >50 ms, and interpolates only inside valid accel
  brackets. It sends gyro samples through the first timestamp at/after each
  image, once; pinned `Tracking.cc` retains this final endpoint internally.
  Uncovered startup gyros/images and EOF images are explicitly counted. A
  useful dataset needs enough leading/trailing coverage; discarded boundaries
  are reviewed, not hidden as a clean run.
- Own cloned image pixels with SDK row strides, preserve image order in an
  eight-pair queue (≈4.92 MB pixels), bound motion queues, and fix the upstream
  interpolation overwrite. Playback waits for queue space; live overload
  fails explicitly. No silent latest-image overwrite. A 10 s backpressure
  timeout, 5 s coverage timeout and ≤1 ms pair-skew guard are **development
  guards**, not changes to N1/N2 or calibrated synchronization thresholds.
- Load vocabulary before starting capture; handle EOF/SIGINT/SIGTERM; stop
  pipeline, shut down SLAM and save trajectories into fresh run directories.
  SDK integration/EOF/callback scheduling still needs real-file validation.
  Non-real-time playback does not make SLAM's mapping threads deterministic;
  compare repeated runs and keep state/reset histories.

[d435i_record.cpp](d435i_record.cpp) uses `enable_record_to_file`, exclusive new
output directory, a bounded duration (1–120 s), callbacks for all four selected
streams, full-precision timestamp/IMU audit CSV and normal stop/finalization.
Both programs retain SDK INFO/warning logs in fresh files; keep them unfiltered.
The SDK handles bag serialization. The callback counts are observations at the
application layer; they do not establish that every hardware sample was stored.
Reconcile stored-frame decode counts and timestamp steps against them.

Emitter OFF is set/read back before live streaming in both programs. Projector
dots are actively projected texture whose motion/view dependence can break
stereo feature tracking and temporal feature identity. Use real, static scene
texture and diffuse light. Disabling the emitter is a runtime stream option,
not a calibration/firmware write. Exposure, motion-correction and global-time
settings are preserved; motion-correction/global-time values are logged. Record
exposure metadata and inspect blur; do not infer calibrated inertial readings
from motion correction being enabled. Never run recorder and SLAM concurrently.

## Future Pi build in a separate bundle

Use already supplied, checksum-verified Mac files in a fresh Pi runtime bundle;
transport is outside this Mac-only task. Do not reset/copy over either checkout
or apply the patch to `~/orbslam3/ORB_SLAM3`. The following reads the existing
native build's generated compile/link recipes, builds only an isolated example,
and reuses completed libraries. It introduces no install or full rebuild.
Stop on any command failure and preserve stdout/stderr; do not hide a missing
target/dependency. These commands assume the current build uses Unix Makefiles
and has the RealSense example target; other generators require review.

```bash
# Future local Pi terminal, after native build completion; CAMERA AVAILABLE
# is additionally required before any ORB or camera-dependent execution.
set -euo pipefail
export WBR_ORB="$HOME/orbslam3/ORB_SLAM3"
export WBR_PREP="$HOME/wbr-perception-phase1-runtime/experiments/2026-10-13-n4b-d435i-prep"
export WBR_BUNDLE="$HOME/wbr-runtime/n4b-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$HOME/wbr-runtime"
mkdir "$WBR_BUNDLE"
cd "$WBR_PREP"
sha256sum -c SHA256SUMS
mkdir -p "$WBR_BUNDLE/source/Examples/Stereo-Inertial" "$WBR_BUNDLE/bin"
cp "$WBR_ORB/Examples/Stereo-Inertial/stereo_inertial_realsense_D435i.cc" \
   "$WBR_BUNDLE/source/Examples/Stereo-Inertial/"
cp d435i_input.h d435i_rs.h "$WBR_BUNDLE/source/Examples/Stereo-Inertial/"
cp d435i_record.cpp d435i_rs.h "$WBR_BUNDLE/source/"
cp D435i_317422076650_stereo_inertial.yaml "$WBR_BUNDLE/"
printf '%s  %s\n' \
  b03a2c6ca6ad3d5d729a6afd22a2efad1e4f6500ed2fee7885b4e3fa607e66af \
  "$WBR_ORB/Examples/Stereo-Inertial/stereo_inertial_realsense_D435i.cc" \
  | sha256sum -c -
patch --dry-run -d "$WBR_BUNDLE/source" -p1 < stereo_inertial_d435i_file.patch
patch -d "$WBR_BUNDLE/source" -p1 < stereo_inertial_d435i_file.patch

python3 - "$WBR_ORB" "$WBR_BUNDLE" <<'PY'
from pathlib import Path
import shlex, subprocess, sys
orb, bundle = map(lambda s: Path(s).resolve(), sys.argv[1:])
build = orb/'build'
target = 'stereo_inertial_realsense_D435i'
recipe = build/'CMakeFiles'/f'{target}.dir'
settings = {}
for line in (recipe/'flags.make').read_text().splitlines():
    if ' = ' in line:
        key, value = line.split(' = ', 1)
        settings[key] = shlex.split(value)
link = shlex.split((recipe/'link.txt').read_text())
objects = [i for i, s in enumerate(link) if s.endswith('.o')]
assert len(objects) == 1, 'review unexpected target link recipe'
assert link.count('-o') == 1, 'review unexpected output flag'
flags = sum((settings[k] for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')), [])
assert '-std=c++17' in flags, 'native C++17 build must complete first'
obj = bundle/'bin'/f'{target}.o'
binary = bundle/'bin'/target
source = bundle/'source/Examples/Stereo-Inertial'/f'{target}.cc'
compile_cmd = [link[0], *flags, '-c', str(source), '-o', str(obj)]
link[objects[0]] = str(obj)
link[link.index('-o')+1] = str(binary)
for cmd in (compile_cmd, link):
    print(shlex.join(cmd), flush=True)
    subprocess.run(cmd, cwd=build, check=True)
PY

# Use the same already-installed librealsense as ORB; no installation here.
pkg-config --modversion realsense2
c++ -std=c++17 -O2 -Wall -Wextra -pthread \
  $(pkg-config --cflags realsense2) "$WBR_BUNDLE/source/d435i_record.cpp" \
  -o "$WBR_BUNDLE/bin/d435i_record" $(pkg-config --libs realsense2)
sha256sum "$WBR_BUNDLE/bin/"* "$WBR_ORB/lib/libORB_SLAM3.so" \
  "$WBR_ORB/Thirdparty/DBoW2/lib/libDBoW2.so" \
  "$WBR_ORB/Thirdparty/g2o/lib/libg2o.so" "$WBR_ORB/Vocabulary/ORBvoc.txt" \
  > "$WBR_BUNDLE/build-sha256.txt"
ldd "$WBR_BUNDLE/bin/stereo_inertial_realsense_D435i" > "$WBR_BUNDLE/ldd.txt"
```

Preserve compile/link commands and logs, original CMake cache/flags/link recipe,
Pi native patches, OS/kernel/compiler, librealsense/Pangolin/OpenCV versions,
library paths/hashes, vocabulary/config/headers/patch hashes and parent source
commit. Library paths in the existing recipe refer to the preserved native
build; retain those libraries for this bundle's lifetime. `pkg-config` must
select the same SDK used by ORB, not an unrelated installation. `ldd` must have
no missing libraries. Building remains OPEN until compiled on the Pi.

## Storage and a future recording command

IR payload per pair is `2*640*480*1=614,400 B`. At 30 Hz that is **18.432 MB/s**,
**1.10592 GB/min = 1.02997 GiB/min**. Gyro/200 + accel/100 raw XYZ floats add
`300*12*60=216,000 B/min` before timestamps, serialization and metadata. Audit
CSV adds roughly a few MB/min depending on metadata. Bag indexing, overhead,
compression behavior, recorder backlog and peak write speed are **UNKNOWN**.
Budget **1.5 GB/min** provisionally; measure finalized file size and peak writes.
90 s is ≈1.659 GB pixels alone; 300 s stereo is ≈5.530 GB pixels alone.

The [snapshot](../2026-10-13-pi5-env-snapshot/CODEX_INSPECTION.md) measured about
**17 GiB available before build** on a nominal 32 GB microSD. Even ignoring all
overhead this is only ≈16.5 min; with a provisional 5 GiB OS reserve and 1.5
GB/min budget it is ≈8.6 min **before subtracting build/swap growth**. Those are
arithmetic limits, not capture authorization. The build script may add a 4 GiB
swap file. Recheck `df -B1`, swap and build sizes. Repository policy keeps
microSD for OS/tools/small logs; GB-scale bags and Allan recordings require
separately qualified storage. No fallback to a directory on `/` is proposed.

```bash
# Future Pi only: mount/storage qualification, new-unit N1/N2/N3 and
# CAMERA AVAILABLE must already be documented. Substitute the actually
# qualified mount; merely creating this directory does not qualify storage.
export WBR_DATA=/mnt/wbr-qualified-data
findmnt -T "$WBR_DATA" -o SOURCE,TARGET,FSTYPE,OPTIONS
df -B1 "$WBR_DATA"
swapon --show
test "$(findmnt -n -o SOURCE -T "$WBR_DATA")" != "$(findmnt -n -o SOURCE -T /)"
test "$(df -B1 --output=avail "$WBR_DATA" | tail -1)" -gt 3221225472
mkdir -p "$WBR_DATA/n4b"
export WBR_TAKE="$WBR_DATA/n4b/take-$(date -u +%Y%m%dT%H%M%SZ)"
# Recorder creates WBR_TAKE exclusively; tee log stays outside until it exists.
set -o pipefail
"$WBR_BUNDLE/bin/d435i_record" "$WBR_TAKE" 90 \
  2>&1 | tee "$WBR_DATA/n4b/$(basename "$WBR_TAKE")-record.log"
sha256sum "$WBR_TAKE/stereo_imu.bag" "$WBR_TAKE/timestamps.csv" \
  > "$WBR_TAKE/SHA256SUMS"
du -B1 "$WBR_TAKE/stereo_imu.bag"
```

Monitor free space, continuous kernel logs, power/temperature/CPU/RSS while
recording; normal SIGINT handles a fault and finalizes the partial bag. Preserve
that partial take and classify it. Never kill -9 to make the duration fit.
The tiny recorder neither qualifies mounts nor monitors health by itself;
reuse the existing gate/health tooling with a reviewed new-unit selection.
Qualified storage must sustain more than the 18.432 MB/s payload plus measured
overhead with margin; apply the storage runbook and review against this profile.

## Hand motion for initialization

Keep the Pi stationary and cool. Move **the camera** with cable slack and strain
relief; do not rock the USB/power connector. Face a well-lit scene with static,
nonrepeating texture at several depths, avoiding blank walls, mirrors and
moving people. Within the first 1–2 s begin smooth translation, so a long
stationary prefix does not provoke an initialization reset.

For the next **20–30 s**, translate left/right, up/down and forward/back roughly
10–30 cm, mixing changes in speed with slow/moderate roll, pitch and yaw
roughly ±15–30°. Keep texture visible in both IR views, avoid blur, sudden
impacts, rapid spins, pure rotation and constant-velocity planar-only motion.
Then continue a small room loop for **30–50 s**, revisit the original view and
end with **5–10 s stationary**. A 60–90 s take gives initialization and refinement
time; it is not a duration-based guarantee. A separately planned stationary
calibration record may use a stationary prefix; this VIO take prioritizes early
excitation. It is not a Kalibr target dataset or Allan-variance experiment.

Pinned `LocalMapping::InitializeIMU` requires ≥10 keyframes and ≥1 s stereo
keyframe span before attempting initialization. Insufficient translation can
print `Not enough motion for initializing. Reseting...`; early initialization
is followed by refinement around accumulated motion times >5 s and >15 s.
These are algorithm conditions, not promises that a one-second take suffices.

## Future N4B and N4C commands and observations

```bash
# Future N4B, only after input evidence review and CAMERA AVAILABLE.
# Stop all live camera publishers/recorders first. Same binary/YAML for both modes.
export LD_LIBRARY_PATH="$WBR_ORB/lib:$WBR_ORB/Thirdparty/DBoW2/lib:$WBR_ORB/Thirdparty/g2o/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export WBR_RUN="$WBR_DATA/n4b/offline-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$WBR_RUN"
cd "$WBR_RUN"
sha256sum "$WBR_TAKE/stereo_imu.bag" \
  "$WBR_BUNDLE/D435i_317422076650_stereo_inertial.yaml" > inputs.sha256
set -o pipefail
/usr/bin/time -v "$WBR_BUNDLE/bin/stereo_inertial_realsense_D435i" \
  "$WBR_ORB/Vocabulary/ORBvoc.txt" \
  "$WBR_BUNDLE/D435i_317422076650_stereo_inertial.yaml" n4b \
  --bag "$WBR_TAKE/stereo_imu.bag" --no-viewer 2>&1 | tee run.log
rg -n 'IMU initialized|maps in the atlas|Creation of new map|Not enough motion|LOST|lost|reset|Reseting|OPEN:' run.log

# Future N4C: review N4B first; live health logging and guided motion required.
export WBR_RUN="$WBR_DATA/n4b/live-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$WBR_RUN"
cd "$WBR_RUN"
set -o pipefail
timeout --signal=INT --kill-after=30s 90s \
  "$WBR_BUNDLE/bin/stereo_inertial_realsense_D435i" \
  "$WBR_ORB/Vocabulary/ORBvoc.txt" \
  "$WBR_BUNDLE/D435i_317422076650_stereo_inertial.yaml" n4c \
  --no-viewer 2>&1 | tee run.log
# timeout normally returns 124: preserve it and review normal shutdown logs;
# forced KILL or missing finalization is a failed attempt, never a success.
```

Preserve each exit status (`pipefail`), log and output hash. Proposed observations
for a **reviewable development run**, all currently OPEN:

- Correct four profiles, SDK identity, paired readable IR pixels; full source
  and config provenance. Bag decode must reconcile recorded raw counts/stamps
  against recorder CSV and driver input audit. No missing interior frame numbers,
  nonfinite/reversed stamps, unexplained large gaps or mixed/changing domains.
  Tiny boundary exclusions must be reported and explained, not called lossless.
- See atlas creation, actual keyframes and initialization/refinement logs.
  The literal `IMU initialized` line is **added by this patch**, tied to the
  existing `System::GetTimeFromIMUInit()>0`; stock pinned code sets the internal
  flag without that literal line. It is not a hard-coded success announcement.
  `*_tracking.csv` records its per-frame value, so resets/loss of initialization
  remain visible. Global BA messages alone do not prove initialization.
- Track state from `Tracking.h`: -1 SYSTEM_NOT_READY, 0 NO_IMAGES_YET,
  1 NOT_INITIALIZED, 2 OK, 3 RECENTLY_LOST, 4 LOST, 5 OK_KLT.
  Inspect 3/4 intervals, reset/new-map messages, state fraction and duration
  after initialization. For the short controlled first take, target sustained
  state 2 and one map without repeated resets. Keep failures; an output trajectory
  or nonzero initialization flag does not establish accuracy.
- `SaveTrajectoryEuRoC` prints `There are N maps in the atlas` and per-map KF
  counts. Expect one stable map for the simple take; explain any extras and map
  switches. The exporter chooses the largest map, so a plausible trajectory can
  hide losses in other maps. Inspect atlas logs and state timeline alongside it.
  Require nonempty finite trajectories, monotonic stamps and useful coverage.
  The inertial EuRoC exporter writes **IMU/body poses in the SLAM world** for
  both frame and keyframe trajectories; the `*_BodyTrajectory.txt` output is
  not an optical-camera pose or ground-truth world frame.
- Review received/processed/prefix/tail/pending counters; no unexplained interior
  loss or queue error. At 30 Hz live, process an image every ≈33.3 ms on average
  with bounded backlog; report per-frame processing time, peak RSS and wall/data
  duration. A file run slower than real time may be useful N4B evidence, but
  does not qualify N4C throughput. Repeat the same bag before going live.
- No new power/thermal/USB/kernel faults, forced shutdown or storage exhaustion.
  Initialization and continuity are development observations; ATE/RPE require
  reference trajectories and a documented alignment, currently unavailable.

## Frames and timestamps: measured versus unknown

| Stage | Evidence / classification | Remaining OPEN condition |
|---|---|---|
| IR1/IR2 optical frames and SDK extrinsics | MEASURED enumeration; see [math](calibration_notes.md) | Physical calibration accuracy, actual pair delivery and exposure timing |
| IMU gyro/accel frames | MEASURED SDK identity alignment; nominal mechanical interpretation INFERRED | Bias/scale/alignment calibration, true device-specific noise |
| Hardware acquisition clocks | UNKNOWN for a new streaming interval | Read every stream's domain; do not assume a single clock just from fps |
| `GLOBAL_TIME_ENABLED` | Old-unit docs report 1; **new-unit state UNKNOWN** | Shared code logs current value and preserves it; compare domains and startup transitions |
| Global-time mapping | SOURCE-SUPPORTED via repository's SDK global reader citation | Mapping toward host time does not measure exposure-to-IMU time offset; host clock steps/drift remain possible |
| SDK frame stamps | API gives double milliseconds, saved at 17-digit precision | Capture original stamp/domain/number plus steady/UTC arrival, exposure metadata and full-precision motion |
| Bag storage/playback | SDK .bag, not a ROS2 rosbag2 directory | Verify stored pixels, metadata and recorded timestamp/domain preservation on installed SDK; no playback wall-time substitution |
| ORB input | SDK ms ×1e-3 to seconds; left IR stamp used; accel interpolated at gyro stamps | Same ordered domain required; camera–IMU offset UNKNOWN, no invented correction applied |
| Host arrivals | Audited at callback observation | These include transport, scheduling and logging; subtraction is not pure USB latency |
| ORB trajectory stamps | Pinned EuRoC exporter multiplies input seconds by 1e9 | Verify domain/units and coverage; do not compare to UTC ground truth without clock characterization |

Preserve domain changes rather than relabeling them. The driver deliberately
stops on mixed/changing domains; diagnose with the saved partial bag/audit and
a separately labeled timestamp experiment. An option readback of 1 is not a
measurement of synchronization. Host global timestamps do not prove hardware
IR/IMU exposure alignment; hardware-relative timestamps must not be mixed with
UTC. After calibration, document offset sign and apply it exactly once in a
reviewed derived input path; never rewrite raw bags. No offset key is invented
in the current Settings schema. The repo's existing global-time source link is
[global_timestamp_reader.cpp](https://github.com/realsenseai/librealsense/blob/v2.58.4/src/global_timestamp_reader.cpp),
already cited in [readiness](../../docs/D435I_VIO_CALIBRATION_READINESS.md);
it was not fetched during this network-free task.

## Limitations and remaining work

Mac synthetic checks prove input association and artifact consistency only.
No librealsense/OpenCV development headers were found in the checked standard
Mac include roots, so recorder/driver SDK compilation and OpenCV FileStorage
parsing remain OPEN. Pi libraries, exact SDK bag semantics, backpressure/EOF,
SIGINT, all-frame reconciliation, image quality, timing/calibration, VIO behavior
and live throughput need future validation. Existing historical evidence and
project gate docs are unchanged. This folder supersedes the earlier proposed
EuRoC conversion only as a **review proposal for this ticket**, not an approved
project-wide data-format decision or an N3 bypass.

Future manual SDK checks: with a camera-free file-mode run after CAMERA
AVAILABLE, confirm a missing/corrupt bag fails without selecting a live device;
replay a finalized short take twice and reconcile all four streams; confirm
EOF drains and exits without hanging, and SIGINT stops/finalizes cleanly in
both modes. Confirm `--no-viewer` works with DISPLAY unset. Inspect native
record/playback metadata for equal recorded stamps/domains and calibration.
Exercise queue overload or missing coverage with labeled synthetic SDK fixtures
when such fixtures are available; preserve the failures. These checks remain
OPEN and do not substitute for physical motion, health or N4 accuracy validation.
