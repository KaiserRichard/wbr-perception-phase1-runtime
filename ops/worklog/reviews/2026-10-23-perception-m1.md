# Perception M1 — ground plane, offline depth, box-ahead advisory (Claude 2)

Owner-assigned, 2026-10-23. Target: end of Oct 2026 lab demo on a mobile robot
(stand-in for WBR): good ORB-SLAM3 lab map, then box-ahead detection producing
an advisory message for the STM32 (no actuation from the Pi).

## Wave 1 — status PARTIAL (built and checked offline, not merged)

| Branch | What | Checked by Claude 2 |
|---|---|---|
| `claude2/20261023-ground-plane` | `tools/ground_plane/`: synthetic depth renderer, RANSAC+SVD floor plane, obstacle height labels, fixed-mount baseline, eval, real-SGBM check | Tests rerun OK. Fixed two scoring bugs (recall capped by sub-threshold box pixels; per-bin recall counted false positives) and two plane-gate bugs found on real data (sign-flipped normals accepted, planes through the camera). |
| `claude2/20261023-stereo-depth` | `tools/stereo_depth/`: MCAP IR pairs -> OpenCV SGBM depth | Tests rerun OK; contact sheet inspected. |

Key numbers (CALCULATED, synthetic flat floor, 45 scenes): per-frame plane
precision/recall 0.995/0.984; fixed-mount assumption 0.069/0.995 overall, and
precision falls to 0.16 at 1.5 deg pitch and 0.03 at 6 deg. Real SGBM
(MEASURED, no ground truth): 2215/2215 stereo pairs, baseline 0.04991 m, mean
valid-depth fraction 0.53, 148/148 frames gave a floor plane with only ~10%
inlier support; glossy tiles mirror objects. Host (Mac) timing only.

## Wave 2 — running
- `claude2/20261023-obstacle-decision` (codex-g): clusters, box distance/height/width, temporal filter, advisory enum, PROPOSED TerrainAdvisory codec on link_proto framing.
- `claude2/20261023-lab-runbook` (codex-d): mobile-robot lab runbook (L1 map, L2 box matrix in RGB-D mode, Scenario-C mitigation).
- `claude2/20261023-map-export` (codex-a): ORB map points/trajectory -> PLY + top-down figures.

## Open
- Scenario C disconnects: no data on the Mac (AGY inventory); root cause UNKNOWN.
- Camera height on the mobile robot: ASSUMED 0.30 m; estimated per frame anyway.
- Advisory message type is PROPOSED; STM32 firmware owner review is needed before any firmware use.
