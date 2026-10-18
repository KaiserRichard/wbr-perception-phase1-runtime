# N4B first D435i offline crash: startup state in LocalMapping

**INFERRED, strongly supported:** the reported SIGSEGV is an invalid dereference
of an **uninitialized** `LocalMapping::mpCurrentKeyFrame`, reached by the custom
D435i file runner's initialization telemetry. It is not evidence of a null
pointer being dereferenced after a successful null check. The existing Pi
“patch 4” initializes the correct pointer. It leaves a second indeterminate read
of `mFirstTs` in the same call. The proposed
[two-line patch](../patches/orbslam3/0001-initialize-localmapping-startup-state.patch)
initializes both members. **N4B remains OPEN; no patched Pi execution was verified
by this ticket.**

## Evidence and precision limits

All source line numbers below refer to official ORB-SLAM3 commit
`4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`, confirmed with read-only
`git -C third_party/ORB_SLAM3 log -1` in the shared checkout. The worktree's
submodule is absent. The source actually inspected was
`/Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime/third_party/ORB_SLAM3`.
`SHARED` below means that parent shared checkout, used read-only.
[Evidence hashes](../patches/orbslam3/evidence_manifest.json) identify the files
inspected; [source hashes](../patches/orbslam3/source_manifest.json) identify the
three source files retained for offline regression.

| Label | Saved evidence | What it establishes |
|---|---|---|
| MEASURED, historical report | `SHARED/experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md:9`, §5 | First-frame SIGSEGV; reported gdb chain `main → System::GetTimeFromIMUInit → LocalMapping::GetCurrKFTime`; patch 4 installed in the Pi copy; initial rebuild interrupted |
| SOURCE-SUPPORTED | `SHARED/experiments/2026-10-13-n4b-d435i-prep/stereo_inertial_d435i_file.patch:249–256` | `TrackStereo` returns, then the added telemetry calls `GetTimeFromIMUInit()>0`, before writing the tracking row |
| MEASURED, saved Pi command transcript | `SHARED/experiments/2026-10-14-codex-queue/codex_run.log:1390–1396` | Pi master at `0318313`, preceding `b02502e`, `22d869a`, `8e5dae6`, `bb35429`, `c9f26a1`; these are Pi-copy commits, not the official upstream pin |
| MEASURED, saved queue outcome | `SHARED/experiments/2026-10-14-codex-queue/OUTCOME.md`, paragraphs 1–5; `inspection/build-progress*.txt` | Queue stopped during build verification; no subsequent offline replay; library freshness/integrity unknown; loss of control and swap pressure, not a confirmed new OOM/power-loss event |
| SOURCE-SUPPORTED, plans only | Queue `rebuild_j1.sh`, `run_offline.sh`, `TICKET.md` | Prepared serial fallback and EuRoC replay commands; helpers were not deployed/executed by that queue |

**UNKNOWN:** a raw gdb `bt` transcript, instruction address, register/pointer
value, core file and the exact first-crash executable/library hashes were not
found in these evidence folders. Do not fabricate numbered stack frames or a
numeric pointer value. The only recovered backtrace is the reported call chain
above. The retained [real report fixture](../patches/orbslam3/tests/fixtures/real_saved_crash.json)
is that report, not an independently observed crash. The precise first bag path
is also not recorded in §5; the queue later names a 15-second still export with
445 images. This does not prove that export was the original crashing input.

The addendum reports an earlier power interruption. The queue outcome separately
documents a later unresponsive rebuild without establishing its termination.
Old successful build log lines and a pre-completion 4,811,704-byte library cannot
establish a complete patched build.

## Source mechanism

1. `include/LocalMapping.h:166` declares `KeyFrame* mpCurrentKeyFrame;` without
   initialization. `src/LocalMapping.cc:33–52` neither initializes it in the
   constructor initializer list nor assigns it in the body. `System.cc:195–197`
   constructs the mapper and starts its thread; allocation does not guarantee
   zero-filled object storage.
2. `src/LocalMapping.cc:298–304` first assigns the pointer when the mapper
   processes a queued keyframe. Returning from the first `TrackStereo` does not
   guarantee a processed keyframe. Stereo-inertial initialization can return
   with `not IMU meas` or `not enough acceleration`
   (`src/Tracking.cc:2335–2350`).
3. The custom runner patch calls `GetTimeFromIMUInit` immediately after
   `TrackStereo`, regardless of tracking/initialization state. In
   `src/System.cc:1339–1345`, the first expression calls `GetCurrKFTime()` and
   subtracts `mFirstTs` **before** testing `mpAtlas->isImuInitialized()`.
4. `src/LocalMapping.cc:1506–1514` checks `if (mpCurrentKeyFrame)` and, if true,
   reads `mpCurrentKeyFrame->mTimeStamp` at **1511**. An indeterminate pointer
   makes even the check undefined behavior; a nonzero garbage value can pass
   it and cause the reported SIGSEGV on dereference. The pointer involved is the
   mapper's keyframe pointer, not `mpLocalMapper`, a camera buffer or an IMU
   preintegration pointer.
5. `include/LocalMapping.h:96` likewise declares `double mFirstTs;` without
   constructor initialization. Its normal assignment is in
   `src/LocalMapping.cc:1209`, after sufficient temporal keyframes have been
   collected for `InitializeIMU` (`1192–1207`). After pointer-only patch 4,
   `GetCurrKFTime()` safely returns zero before any keyframe, but the subsequent
   subtraction still reads an indeterminate timestamp. This second defect is
   **SOURCE-SUPPORTED**, not a second measured SIGSEGV.

The custom first-frame telemetry exposes the defect. The official stereo
EuRoC loop calls `TrackStereo` (`Examples/Stereo-Inertial/stereo_inertial_euroc.cc:185`)
and does not call `GetTimeFromIMUInit` anywhere. The N4A monocular EuRoC example
also has no such call. Consequently an EuRoC run can succeed without exercising
this crash site; the earlier N4A results do not refute the startup bug.

## Existing patches and the proposed change

The shared `patches/` directory contains only an empty `orb_slam3_ros2/`
directory; it has no saved patch-4 or Settings diff. Pi commit subjects and
source inspection permit this reconstruction, with the limits below.

| Artifact / Pi commit | Recorded change | Relationship to this failure |
|---|---|---|
| `c9f26a1` | Pristine `4452a3c` copy | Pi history base, not proof of exact current binary bytes |
| `bb35429` | `c++17 patch` | Build compatibility; exact diff unavailable locally |
| `8e5dae6` | `C++17: replace bool++ on mnFullBAIdx` | Build compatibility, separate from keyframe startup. Upstream `include/LoopClosing.h:226` declares a bool; `src/LoopClosing.cc:985,1236,1809` increments it. Exact Pi replacement unavailable |
| Preparation `stereo_inertial_d435i_file.patch` | Adds recorded-file/headless mode, callback association, stream audits, tracking CSV and the initialization query to the RealSense example | Supplies the triggering accessor call; does not initialize LocalMapping |
| Patch 4, `22d869a` | `KeyFrame* mpCurrentKeyFrame = nullptr;` | Addresses the actual reported pointer at the actual accessor dereference; incomplete for the timestamp read |
| Settings fix `b02502e` | Skip Camera-2 print when `originalCalib2_` is null for Rectified stereo | Separate construction-time crash |
| Settings fix `0318313` | Initialize camera pointers to nullptr | Makes that guard meaningful; paired with preceding Settings guard |

The queue calls the two Settings fixes “patch 5”; their exact diffs were not
available. Source explains their necessity: `include/Settings.h:165–166` leaves
camera pointers uninitialized, and `src/Settings.cc:127–129` does not initialize
them. Rectified camera 1 is allocated at `227–239`. `readCamera2` allocates a
second camera only for PinHole or KannalaBrandt (`279–327`); Rectified only sets
baseline at `337–339`. Yet the stereo print block dereferences
`originalCalib2_` at `553–563`. `src/System.cc:79–84` prints Settings during
construction, before any frame. Initializing the pointers alone would turn
this into a null dereference unless the print is guarded. Patch 4 cannot fix
this Settings site, and the Settings fixes cannot fix `GetCurrKFTime`.

Our patch changes only the two LocalMapping declarations:

```cpp
double mFirstTs = 0.0;
KeyFrame* mpCurrentKeyFrame = nullptr;
```

The pointer uses the accessor's existing zero-return branch; `mFirstTs` uses
a numeric startup sentinel, later replaced by the first keyframe's timestamp.
The sentinel is not a measured epoch or a clock mapping. Meaningful elapsed
time still requires an initialized atlas and camera/keyframe timestamps in the
same source clock. No method, calibration, noise value, threshold or file input
policy changes. Default member initializers preserve layout and require C++11,
already required by pinned upstream. Rebuild the library and relevant callers.

This is a startup fix, not a thread-safety repair. `GetCurrKFTime` and
`GetTimeFromIMUInit` still access mapping state without a coherent synchronized
snapshot; the latter calls the former twice. Pointer writes, map resets and
keyframe lifetime merit separate review. Do not infer general race freedom
from the isolated probe.

**SOURCE-SUPPORTED search result:** no matching upstream GitHub issue text or
issue URL for these accessors/uninitialized-pointer defects was found in the
locally available Markdown/text documentation, including README,
Dependencies and Changelog. `Changelog.md:14,24,37` contains only generic bug-fix
entries. No upstream issue number or endorsement is claimed; no network was
used.

## Could D435i input trigger this?

**INFERRED:** input can prolong the pre-keyframe state that exposes the query,
but this accessor defect requires no particular corrupt input. Querying a newly
constructed mapper is enough to expose indeterminate state in the old source.
No supplied evidence demonstrates that timestamp units or an empty IMU vector
caused the reported crash.

| Input condition | Source behavior and implication |
|---|---|
| D435i camera IMU samples before first image | Normal acquisition ordering. The preparation association trims startup coverage and requires nonempty samples before `TrackStereo` (patch lines 222–243). It still queries initialization after the first accepted image, before a processed keyframe is guaranteed |
| Empty IMU vector | The custom runner skips empty batches (patch 233–238), but upstream EuRoC deliberately submits no IMU at `ni==0` (`stereo_inertial_euroc.cc:167–170`). `Tracking::PreintegrateIMU` handles no previous frame and empty queue by returning (`1627–1640`); later initialization can remain pending. Empty input is not proof of this dereference or a universally safe input path |
| Too few, too old, or misaligned IMU samples | `Tracking.cc:1652–1665` selects by timestamp; at `1677–1680` the message `Empty IMU measurements vector!!!` is emitted for **one** selected sample (`n=size-1==0`). Zero selected samples is a different path. Report this existing diagnostic/edge-case concern separately; this ticket does not modify Tracking |
| Units or clock mismatch | The RealSense file patch converts SDK timestamps from milliseconds to seconds at 173 and 192 and rejects mixed/changing domain enums at 153–156. Equal enums do not prove physical alignment. The EuRoC loader converts camera and IMU integer nanoseconds to seconds at 263 and 298. Passing seconds as EuRoC nanoseconds or converting twice corrupts timing and can block initialization or expose other failures |
| Tail coverage / timestamp search | Upstream EuRoC's IMU loop at 170–175 lacks an explicit end-index check. Insufficient IMU coverage is a separate possible out-of-bounds failure. Reuse the existing exporter/qualifier before replay; do not attribute a future loader crash to LocalMapping without a stack trace |

The IMU here is the **D435i BMI085 camera IMU**, not the STM32H7 body IMU.
The SDK route uses D435i hardware/global timestamp domain as recorded and
audited; the exported ROS route uses source `header.stamp` as documented by
`tools/n4b_offline`. Host steady-clock tracking durations are separate. No
subtraction between SDK, ROS, Linux monotonic/realtime or MCU clock domains is
introduced by this investigation.

## Offline validation completed

**MEASURED (Mac software):** the patch passed `git apply --verbose --check`
on a complete temporary copy of the read-only upstream tree, with `.git` and
`.DS_Store` omitted. The copy was under `patches/orbslam3/tmp/` and deleted;
[receipt](../patches/orbslam3/validation/full-copy/receipt.json) and verbatim
[Git output](../patches/orbslam3/validation/full-copy/stderr.txt) are retained.
Git discovery was bounded to the temporary directory to prevent parent-worktree
path filtering.

The checker separately applies it to saved exact source slices and compiles
the two actual declarations plus unchanged `GetCurrKFTime` and
`GetTimeFromIMUInit` bodies with stub dependencies. Both C++11 and C++17 probes
ran successfully. Full `LocalMapping.cc` compilation was **not** attempted:
the Mac has no configured ORB-SLAM3/OpenCV/Eigen/Pangolin build environment.
This probe is a limited syntax/behavior check, not full translation-unit or
library compilation. Nine unittest tests passed, including PASS/FAIL/BLOCKED
paths and a real saved crash-report fixture. Commands, criteria and limits are
in the [patch README](../patches/orbslam3/README.md), with
[saved test output](../patches/orbslam3/tests/last-run.log).

## Future Pi rebuild and discriminating reruns (not executed)

These are commands for a future **local Pi terminal**, with existing
dependencies, completed/stopped old builds, and no camera publisher/recorder.
They use the historical native build copy `~/orbslam3/ORB_SLAM3`, never the
repository's `third_party/`. The parent repo below is **ASSUMED** deployed at
`~/wbr-perception-phase1-runtime`; adjust the variable to its actual deployment.
Preserve both historical Settings fixes and C++17 compatibility patches. Stop
if those prerequisites or saved inputs are missing; no package installs are
part of this procedure. The marginal power/build conditions still limit what
a successful diagnostic can prove.

First verify no build is active, record source provenance, and apply the two
initializers to the existing Pi header. The adaptation accepts pristine or
already-patch-4 declarations, verifies the normalized entire header against
the pinned hash, and saves an exact diff and original header before writing.

```bash
set -euo pipefail
export T24_REPO="$HOME/wbr-perception-phase1-runtime"
export T24_ORB="$HOME/orbslam3/ORB_SLAM3"
export T24_RUN="$HOME/wbr-evidence/t24-$(date -u +%Y%m%dT%H%M%SZ)"
if pgrep -af '[c]make --build|[c]c1plus|[r]ebuild.sh'; then
  echo 'STOP: wait for and inspect the existing build'; exit 2
fi
mkdir -p "$HOME/wbr-evidence"
mkdir "$T24_RUN"
git -C "$T24_ORB" log -6 --oneline > "$T24_RUN/source-log.txt"
git -C "$T24_ORB" diff > "$T24_RUN/source-before.diff"
git -C "$T24_ORB" status --short > "$T24_RUN/source-status.txt"
python3 - <<'PY'
import difflib, hashlib, json, os
from pathlib import Path
orb, repo, run = (Path(os.environ[k]) for k in ('T24_ORB','T24_REPO','T24_RUN'))
path = orb/'include/LocalMapping.h'
old = path.read_text()
base = old.replace('double mFirstTs = 0.0;', 'double mFirstTs;').replace(
    'KeyFrame* mpCurrentKeyFrame = nullptr;', 'KeyFrame* mpCurrentKeyFrame;')
expected = json.loads((repo/'patches/orbslam3/source_manifest.json').read_text())
assert hashlib.sha256(base.encode()).hexdigest() == expected['files']['include/LocalMapping.h'], 'unexpected header; review instead of overwriting'
new = base.replace('double mFirstTs;', 'double mFirstTs = 0.0;').replace(
    'KeyFrame* mpCurrentKeyFrame;', 'KeyFrame* mpCurrentKeyFrame = nullptr;')
(run/'LocalMapping.h.before').write_text(old)
(run/'localmapping-applied.diff').write_text(''.join(difflib.unified_diff(
    old.splitlines(True), new.splitlines(True), fromfile='a/include/LocalMapping.h', tofile='b/include/LocalMapping.h')))
path.write_text(new)
PY
sha256sum "$T24_ORB/include/LocalMapping.h" "$T24_ORB/include/Settings.h" \
  "$T24_ORB/src/Settings.cc" > "$T24_RUN/source.sha256"
cmake --build "$T24_ORB/build" -j1 > "$T24_RUN/build.log" 2>&1
cmake --build "$T24_ORB/build" -j1 --target stereo_inertial_euroc \
  > "$T24_RUN/build-euroc.log" 2>&1
find "$T24_ORB/build" -name '*.o' -size 0 > "$T24_RUN/zero-byte-objects.txt"
test ! -s "$T24_RUN/zero-byte-objects.txt"
sha256sum "$T24_ORB/lib/libORB_SLAM3.so" \
  "$T24_ORB/Examples/Stereo-Inertial/stereo_inertial_euroc" > "$T24_RUN/artifacts.sha256"
export LD_LIBRARY_PATH="$T24_ORB/lib:$T24_ORB/Thirdparty/DBoW2/lib:$T24_ORB/Thirdparty/g2o/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
ldd "$T24_ORB/Examples/Stereo-Inertial/stereo_inertial_euroc" > "$T24_RUN/ldd.txt"
if grep -q 'not found' "$T24_RUN/ldd.txt"; then exit 2; fi
grep -F "libORB_SLAM3.so => $T24_ORB/lib/libORB_SLAM3.so" "$T24_RUN/ldd.txt"
```

Then run the existing **EuRoC route** on the still take. Reuse
`tools/n4b_offline/qualify_euroc.py` before replay and the existing runner for
hashes, command receipts, logs and exit status. The runner's
`--allow-unpatched` means the repository's verified-binary checksum manifest is
still UNKNOWN; here it is an explicit diagnostic override backed by the new
build receipts above, not evidence that the Pi build is qualified. Keep the
still take's exporter metadata, YAML and first/last IMU coverage available.

```bash
export T24_DATA="$HOME/wbr-evidence/2026-10-14-d435i-ramtest15s/euroc-export"
export T24_YAML="$HOME/wbr-runtime/n4b-prep-20261013/D435i_317422076650_stereo_inertial.yaml"
python3 "$T24_REPO/tools/n4b_offline/qualify_euroc.py" \
  --analyze-only "$T24_DATA" --outdir "$T24_RUN/input-qualification"
bash "$T24_REPO/tools/n4b_offline/run_n4b.sh" --allow-unpatched \
  "$T24_ORB" "$HOME/datasets/euroc/MH01" \
  "$T24_ORB/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt" \
  "$T24_ORB/Examples/Stereo-Inertial/EuRoC.yaml" "$T24_RUN/mh01"
bash "$T24_REPO/tools/n4b_offline/run_n4b.sh" --allow-unpatched \
  "$T24_ORB" "$T24_DATA" "$T24_DATA/times_ns.txt" "$T24_YAML" "$T24_RUN/still-euroc"
```

That route checks Settings and general regression, but **does not call the
crashing accessor**. For the discriminating test, rebuild the custom file
example from the preparation patch in a fresh bundle, reusing the completed
native target's generated compile/link recipe as the original runbook does.
This builds no recorder and opens no physical camera. `WBR_PREP` and the bag
path are deployment assumptions; the original RealSense `.bag` is required,
not the exported SQLite `.db3` or EuRoC directory. A saved bag replay may still
stall/drop IMU according to the queue; that is distinct from this pointer bug.

```bash
export T24_PREP="$T24_REPO/experiments/2026-10-13-n4b-d435i-prep"
export T24_BUNDLE="$T24_RUN/file-example"
mkdir -p "$T24_BUNDLE/source/Examples/Stereo-Inertial" "$T24_BUNDLE/bin"
cp "$T24_ORB/Examples/Stereo-Inertial/stereo_inertial_realsense_D435i.cc" \
  "$T24_BUNDLE/source/Examples/Stereo-Inertial/"
cp "$T24_PREP/d435i_input.h" "$T24_PREP/d435i_rs.h" \
  "$T24_BUNDLE/source/Examples/Stereo-Inertial/"
patch --dry-run -d "$T24_BUNDLE/source" -p1 < "$T24_PREP/stereo_inertial_d435i_file.patch"
patch -d "$T24_BUNDLE/source" -p1 < "$T24_PREP/stereo_inertial_d435i_file.patch"
python3 - <<'PY' > "$T24_RUN/build-file-example.log" 2>&1
import os, shlex, subprocess
from pathlib import Path
orb, bundle = (Path(os.environ[k]).resolve() for k in ('T24_ORB','T24_BUNDLE'))
target = 'stereo_inertial_realsense_D435i'
build = orb/'build'
recipe = build/'CMakeFiles'/f'{target}.dir'
settings = {}
for line in (recipe/'flags.make').read_text().splitlines():
    if ' = ' in line:
        key, value = line.split(' = ', 1)
        settings[key] = shlex.split(value)
link = shlex.split((recipe/'link.txt').read_text())
objects = [i for i, s in enumerate(link) if s.endswith('.o')]
assert len(objects) == 1 and link.count('-o') == 1, 'unexpected link recipe'
flags = sum((settings[k] for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')), [])
assert '-std=c++17' in flags, 'existing native C++17 configuration required'
obj, binary = (bundle/'bin'/f'{target}{suffix}' for suffix in ('.o',''))
source = bundle/'source/Examples/Stereo-Inertial'/f'{target}.cc'
compile_cmd = [link[0], *flags, '-c', str(source), '-o', str(obj)]
link[objects[0]] = str(obj)
link[link.index('-o')+1] = str(binary)
for cmd in (compile_cmd, link):
    print(shlex.join(cmd), flush=True)
    subprocess.run(cmd, cwd=build, check=True)
PY
export T24_FILE_BIN="$T24_BUNDLE/bin/stereo_inertial_realsense_D435i"
export T24_BAG="$HOME/wbr-evidence/2026-10-14-d435i-ramtest15s/take/stereo_imu.bag"
test -s "$T24_BAG"
sha256sum "$T24_FILE_BIN" "$T24_ORB/lib/libORB_SLAM3.so" "$T24_BAG" \
  "$T24_YAML" > "$T24_RUN/file-inputs.sha256"
ldd "$T24_FILE_BIN" > "$T24_RUN/file-ldd.txt"
if grep -q 'not found' "$T24_RUN/file-ldd.txt"; then exit 2; fi
grep -F "libORB_SLAM3.so => $T24_ORB/lib/libORB_SLAM3.so" "$T24_RUN/file-ldd.txt"
mkdir "$T24_RUN/file-replay"
cd "$T24_RUN/file-replay"
if /usr/bin/time -v "$T24_FILE_BIN" "$T24_ORB/Vocabulary/ORBvoc.txt" \
  "$T24_YAML" t24 --bag "$T24_BAG" --no-viewer > run.log 2>&1; then
  T24_RC=0
else
  T24_RC=$?
fi
printf '%s\n' "$T24_RC" > exit-status.txt
```

If the bag is missing, record BLOCKED for the original path; do not substitute
an EuRoC-only run as confirmation. If the custom run crashes, save a new
backtrace with the same binary, YAML and bag:

```bash
gdb -batch -ex run -ex 'thread apply all bt full' --args \
  "$T24_FILE_BIN" "$T24_ORB/Vocabulary/ORBvoc.txt" "$T24_YAML" \
  t24-gdb --bag "$T24_BAG" --no-viewer > "$T24_RUN/gdb.txt" 2>&1
```

**Confirming evidence:** a matching source/library receipt; gdb or tracking
CSV evidence that the early query executes before a processed keyframe and
returns zero safely; subsequent valid-keyframe queries still work; repeated
file runs reach later frames without the old stack. Lack of IMU initialization
on a still take is not a failure of this fix. No still take proves VIO quality.

**Refuting/redirecting evidence:** a verified newly built/loaded library still
crashes at the same member read after initialized startup state; a pointer that
was valid then freed/reset; a crash during Settings print, input loading or
preintegration; or a stack that never enters this accessor. Preserve source,
loaded-library paths, pointer value, all thread stacks and exact frame/input
position. Such results distinguish stale artifacts, races/lifetime errors and
different input defects from the startup hypothesis. No existing gate status
should change solely because these diagnostic commands complete.
