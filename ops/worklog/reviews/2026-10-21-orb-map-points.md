# Sparse ORB map-point milestone — conductor review

**Done: scoped implementation and corrected offline validation.** Branch
`chatgpt/20261021-orb-map-points`, based on `7c72a23`; worker implementation
commit `476d38d` is followed by the conductor's lock-order correction. Final
validation below uses the corrected runtime and recorder gate.

## Change and source basis

- D435 visual node publishes `~/map_points` PointCloud2 and `~/map_points_info` JSON.
  Existing pose/status content stays unchanged. Current-map finite, non-bad XYZ;
  1 Hz default/max; rate check before collection; 50,000 candidate default cap;
  bounded pointer/value buffers; map locks released before ROS serialization.
- `Tcw` is inverted for existing camera pose; MapPoint world positions already
  share `slam_world`. Snapshots replace all previous points, including empty
  snapshots on untracked inputs when collection succeeds. Metadata IDs/counters
  are sampled diagnostics, not guaranteed reset/merge epochs.
- Reused native typed Atlas helper; two isolated typed Map member pointers avoid
  the public unbounded pointer-vector copy. Audited against repo pin `4452a3c4`
  and clean Pi build `727f3cbd`; relevant map source/header files are identical.
  Conductor review caught a reverse lock order in the first commit's active-map
  recheck: it called `Atlas::GetCurrentMap()` while holding `mMutexMapUpdate`.
  The correction removes that second Atlas lookup. The selected Map remains
  alive at this pin because `RemoveBadMaps()` does not delete retired Maps;
  documentation now states a concurrent switch can yield one just-retired-map
  snapshot, identified by metadata. No Atlas lock is acquired under map-update.
- Persistence: separate optional MCAP recording, demonstrated readable after the
  live processes stop. Existing camera record scripts/MCAP, sensor launch settings,
  earlier evidence, ORB native build, shared checkout and hardware untouched.
- Files: package `src/d435_node.cpp`, two map headers, CMake/Makefile, cloud C++
  test, bounded replay/closed-bag checker/cleanup test, README/MAP_POINTS guide;
  this review and task session log. No raw bag or checkpoint in git.

## Commands and results

| Validation | Result |
| --- | --- |
| `make -C ros2/wbr_orb_node test` | PASS after final harness change: cloud layout/endian/finite/header/empty/bounds/rate assertions and 20 Python tests. |
| Targeted cleanup rerun after final harness guard | PASS in 0.967 s; stub child groups absent. |
| Serial isolated colcon, `WITH_ORB_SLAM3=ON`, `BUILD_TESTING=ON`, Release, `-j1`, 170+10 s timeout | PASS exit 0, 2 min 0 s. Existing native ORB library linked, not rebuilt. Upstream header warnings retained. |
| Corrected isolated Pi build and `ctest --test-dir .../build/wbr_orb_node --output-on-failure` | PASS; actual ROS PointCloud2 test 1/1. Build used existing native ORB library, not a native rebuild. |
| `tests/replay_map_points.py`, domain 187, localhost, test-topic remaps, `--playback-duration 20 --rate 0.3` | Final replay-04 PASS in 79.75 s, including persisted-bag validation. No camera process. |
| Closed replay-04 MCAP checker | PASS: 20/20 nonempty clouds, up to 965 actual ORB landmarks; all finite; FLOAT32 XYZ at 0/4/8, 12-byte stride, `slam_world`. Cloud stamps matched source MCAP and matching pose/status/metadata. |
| Cleanup receipt | Player, SLAM and recorder exit 0; no task-owned process groups remain. Existing domain-0 bridge/player still running untouched. |

Final replay-04 produced 294 tracked poses/statuses over 19.5342 source seconds;
`application_dropped=0` is not proof of zero DDS loss or full-bag coverage. The
20 cloud source intervals were at least 1 s; all snapshots remained in map 0,
with no reset/merge exercised. The final MCAP SHA-256 is
`13e207d0ddca8545c9a968b2b93c166184229d2097e340114258b41ebc984098`.

Attempt 01 stopped **before playback** after 19.76 s: simulated-time recorder
waited for `/clock`, while harness waited for subscription before starting player.
Replay-03 later exposed a second startup race: transient-local cloud reached the
recorder before volatile status subscription discovery completed. Its validator
correctly failed on the unmatched first cloud. The harness now uses wall-time
receive stamps and waits for `All requested topics are subscribed` before player
startup. Replay-04 passed. Failed and passing runs are retained.
Final harness additionally catches SIGTERM, reports validation timeout, requires
clean exits, and enforces remaining validation time under the 180-second budget.
The Pi build after the lock-order correction and replay-04 use this final harness.

## Tomorrow's operator runbook

`LAB_DAY_EXECUTION.md` covers a fresh SSH/power/USB/storage preflight, sequential
25/75/45-second captures with the archived runner, per-run stereo checks, a
bounded first-20-second map replay, and Mac copy/Foxglove steps. An independent
read-only review led to explicit per-run settings checks, an optional domain-201
diagnostic, fail-fast validation, a 3 GiB free-space reserve, and clearer checksum
output. All 14 Bash command blocks pass `bash -n`; package tests pass 20/20.
This is an operator plan, not a live run: latest SSH timed out, and current
hardware readiness must be checked in the lab. Full-duration export and GUI
appearance remain unverified.

## Evidence and reproduction

- Pi source/build/install: `/home/richard/wbr-orb-map-points-20261021-01/`.
- Pi evidence: `/home/richard/wbr-evidence/orb-map-points-20261021-01/`.
- Mac archive: `/Users/quockaiser/wbr-evidence-archive/orb-map-points-20261021-01/`.
  `replay-04/{receipt.json,validation.json,map-bag/}` proves the final run;
  replay-03 preserves the recorder-race failure. `build-02-lock-order-fix.log`,
  `ctest-02-lock-order-fix.log`, hashes and earlier build evidence retain provenance;
  `host/` holds tests and exact source audit copies.
- Input is the pre-existing Pi marked stereo `.../camera-day-20261021-01/mcap-marked-loop-01/sensor-bag`.
  Earlier live archive and codex-g pose/status replay archive unchanged.
- Full reproducible build/short replay/standalone bag-check commands, parameter
  contracts, transformation derivation and Foxglove settings are in
  [MAP_POINTS.md](../../../ros2/wbr_orb_node/MAP_POINTS.md).

## Limitations and proposed follow-up

No live hardware, RGB-D replay, Foxglove bridge/GUI inspection, real reset/merge,
cap-overflow or lock-contention stress was performed. No live throughput or
accuracy conclusion. Map changes can happen between pose and snapshot; IDs can
survive reset/merge. Keep Foxglove decay at zero and treat clouds as replacements.
Try-lock skips can postpone stale-cloud clearing. Separate MCAP needs graceful
recorder shutdown; abrupt interruption may lose queued data. It preserves point
geometry, not a reloadable ORB atlas.

**Recommendation for conductor:** review the corrected branch, independently
open `replay-04/map-bag` in Foxglove with fixed/display frame `slam_world`, then
publish through normal CI/review. A later separately authorized test can exercise
reset/merge replacement and contention; this short replay does not authorize a
full 148-second replay or live hardware run. Re-audit compatibility before any
ORB upgrade or executor/thread change.

Claude handoff: review this file and `LAB_DAY_EXECUTION.md` with the corrected
branch and retained closed-MCAP validation; implementation/offline evidence pass,
live lab readiness, full-duration export, live Foxglove and discontinuity stress
remain unverified.
