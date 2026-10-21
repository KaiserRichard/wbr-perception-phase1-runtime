# Sparse ORB map-point milestone — conductor review

**Done: scoped implementation and offline validation; not published.** Branch
`chatgpt/20261021-orb-map-points`, base `7c72a23`. No PR or merge (owner requested
one local commit for conductor review). Runtime source did not change after the
successful Pi build/replay; subsequent changes harden the test harness and docs.

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
  the public unbounded pointer-vector copy. Audited ownership and lock ordering
  against repo pin `4452a3c4` and actual clean Pi build `727f3cbd`; relevant map
  source/header files identical. System differences are existing empty-map
  trajectory-save guards. Independent read-only review found no new lock inversion.
- Persistence: separate optional MCAP recording, demonstrated readable after the
  live processes stop. Existing camera record scripts/MCAP, sensor launch settings,
  earlier evidence, ORB native build, shared checkout and hardware untouched.
- Files: package `src/d435_node.cpp`, two map headers, CMake/Makefile, cloud C++
  test, bounded replay/closed-bag checker/cleanup test, README/MAP_POINTS guide;
  this review and task session log. No raw bag or checkpoint in git.

## Commands and results

| Validation | Result |
| --- | --- |
| `make -C ros2/wbr_orb_node test` | PASS: cloud layout/endian/finite/header/empty/bounds/rate assertions; 19 existing Python tests plus new SIGTERM cleanup test (20 total). |
| Targeted cleanup rerun after final harness guard | PASS in 0.967 s; stub child groups absent. |
| Serial isolated colcon, `WITH_ORB_SLAM3=ON`, `BUILD_TESTING=ON`, Release, `-j1`, 170+10 s timeout | PASS exit 0, 2 min 0 s. Existing native ORB library linked, not rebuilt. Upstream header warnings retained. |
| `ctest --test-dir .../build/wbr_orb_node --output-on-failure` | PASS 1/1, 0.01 s; actual ROS PointCloud2 message type. |
| `tests/replay_map_points.py`, domain 187, localhost, test-topic remaps, `--playback-duration 20 --rate 0.3` | PASS in 79.645866 s, including persistence validation. No camera process. |
| Closed separate MCAP checker | PASS: 20 nonempty clouds, 337–1,046 actual ORB points; all finite; FLOAT32 XYZ at 0/4/8, 12-byte stride, `slam_world`. All source stamps matched recorded input plus pose/status/metadata. |
| Cleanup receipt | Player, SLAM and recorder exit 0; no task-owned process groups remain. Existing domain-0 bridge/player still running untouched. |

292 frames produced tracked poses/statuses over 19.4008125 source seconds, last
application drop counter 0. This is not proof of zero DDS losses or full-bag
coverage. Minimum cloud source interval: 1.000038086 s. Map ID and initial KF ID
were both 0 throughout. Initial ORB log reports creation of 337 actual points;
last snapshot contains 1,046. The retained MCAP is 243,033 bytes, SHA-256
`fc57e3071cd3c219e7493d101113d52f15a8022ee7f8107bfd45dcf9c96f6c75`.

Attempt 01 stopped **before playback** after 19.76 s: simulated-time recorder
waited for `/clock`, while harness waited for subscription before starting player.
Both owned children exited 0. Fixed readiness to `Listening for topics`; attempt
02 passed. Both attempts and the exact successful harness source are retained.
Final harness additionally catches SIGTERM, reports validation timeout, requires
clean exits, and enforces remaining validation time under the 180-second budget;
those changes were host-tested without repeating the real replay.

## Evidence and reproduction

- Pi source/build/install: `/home/richard/wbr-orb-map-points-20261021-01/`.
- Pi evidence: `/home/richard/wbr-evidence/orb-map-points-20261021-01/`.
- Mac archive: `/Users/quockaiser/wbr-evidence-archive/orb-map-points-20261021-01/`.
  `replay-02/{receipt.json,validation.json,map-bag/}` proves the successful run;
  `build-01.log`, `ctest.log`, hashes and `processes-after.txt` retain provenance;
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

**Recommendation for conductor:** review the scoped commit, independently open
`replay-02/map-bag` in Foxglove with fixed/display frame `slam_world`, then publish
through normal CI/review. A later explicitly scoped test can exercise reset/merge
replacement and contention; this short successful test does not authorize a full
148-second replay or live hardware run. Re-audit the compatibility helper before
any ORB upgrade or executor/thread change.

Claude handoff: review this file with the scoped commit and retained closed-MCAP
validation; implementation/offline evidence pass, live Foxglove and discontinuity
stress remain unverified. No Claude dispatch or PR action performed by this worker.
