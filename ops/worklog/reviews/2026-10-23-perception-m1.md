# Perception M1 — ground plane, local map, box-ahead advisory (Claude 2)

Owner-assigned, 2026-10-23. Target: end-Oct 2026 lab demo on a hand-pushed
mobile rig (stand-in for WBR): ORB-SLAM3 lab map, depth-based box detection,
local map, advisory message for the STM32. No actuation from the Pi.
Status: **PARTIAL** — built and checked offline; nothing merged; no real-box
or ground-truth data yet (lab capture 2026-10-24).

## Branches (all pushed, none merged)

| Branch | What | Supervisor checks / fixes |
|---|---|---|
| `claude2/20261023-ground-plane` | RANSAC+SVD floor plane, obstacle labels, synthetic eval, real-SGBM check | Fixed: recall counted sub-threshold box pixels; per-bin recall used predictions; prior gate accepted flipped normals (seat undersides); planes through camera centre |
| `claude2/20261023-stereo-depth` | MCAP IR pairs -> SGBM depth | Rectification check, sparse-vs-SGBM agreement, invalid pixels now black (were coloured as 0 m) |
| `claude2/20261023-obstacle-decision` | Clusters, box distance/height/width, N-of-M filter, advisory, PROPOSED TerrainAdvisory codec | Fixed: front-face distance used min (biased short, max 8.2 cm at 2 m) -> p5 (max 3.4 cm) |
| `claude2/20261023-bag-eval` | Replay RGB-D bags (SQLite or MCAP) + run-sheet evaluator incl. empty-floor and wall runs | Found record.sh writes SQLite; evaluator required MCAP and box values on every row -> fixed (codex-b) |
| `claude2/20261023-map-export` | ORB map points/trajectory -> PLY, top-down/side PNG | Fixed: tracking state table off by one (2 is OK in ORB_SLAM3 Tracking.h) |
| `claude2/20261023-local-map` | 2.5D elevation grid, gravity alignment from floor plane | Tests rerun OK; synthetic only |
| `claude2/20261023-ros-obstacle-node` | ROS 2 node: advisory JSON/bytes, markers, points; no serial | Tests rerun OK; Pi build UNVERIFIED |
| `claude2/20261023-replay-full` | `--seconds/--rate` for map replay; long stereo capture notes | Tests rerun OK; Pi run UNVERIFIED |
| `claude2/20261023-lab-runbook` | RUNBOOK, `CHECKLIST_2026-10-24.md`, run sheet, capture checker | RGB-D at 15 Hz (32 MB/s vs 50 MB/s card rating; 30 Hz = 64 MB/s) |

## Numbers (label)

- Floor/obstacle, synthetic flat floor, 45 scenes (CALCULATED): per-frame plane
  P/R 0.995/0.984; fixed-mount precision 0.16 at 1.5 deg pitch, 0.03 at 6 deg.
- Box geometry, synthetic, 80 cases (CALCULATED): height |err| mean 1.5 mm,
  max 5.6 mm; distance |err| mean 1.3 cm, max 3.4 cm.
- Local map, synthetic (CALCULATED): height RMSE 4.25 mm gravity-aligned vs
  115.6 mm unaligned; obstacle P/R 1.00/0.964.
- Real IR stereo, 21 Oct loop (MEASURED): 2215/2215 pairs, baseline 0.04991 m,
  ORB-match vertical offset median 0.000 px; sparse-vs-SGBM |rel| p50 4%
  (agreement, not accuracy); floor plane inlier support ~10%; glossy tiles.

## ORB-SLAM3 evidence (AGY audit, spot-checked against CURRENT.md)

- Ground truth only on public EuRoC MH01 (Pi, stereo-inertial): ATE RMSE
  0.037–0.042 m over 3 runs. No ground truth on our camera.
- Our camera: 147.6 s handheld loop, Mac replays: 2 of 3 runs lost no frames,
  1 lost 63 frames with a map merge; R1/R2 agreement RMS 10 mm (repeatability,
  not accuracy). No moving live run verified end to end. Map merges/loop
  closures cause pose jumps (1.115 m in one replay) that a local map must reject.
- Not yet trusted for metric depth fusion. 24 Oct plan adds a tape-measured
  3.00 m segment and return-to-start mark.

## Previous team report (AGY extraction, jump section read by Claude 2)

- Old robot: 3.5 kg body, 0.06 m wheels, five-bar 75/140 mm, DM-J4310 hips
  (7 Nm peak), DM-H6215 wheels, STM32H723 at 400 Hz, BMI088, no camera.
- Hardware evidence: balance, disturbance recovery, 5 cm sinusoidal terrain,
  slope, step DOWN, one jump on flat ground (flight 300 ms, take-off prep
  200 ms, approach ~0.8 m/s). Jumping onto steps: simulation only, heights not
  reported. Obstacle clearing on hardware: NOT demonstrated.
- CALCULATED from the reported flight time (ballistic, same take-off and
  landing height): apex COM rise ~ g t^2 / 8 = 0.11 m; forward travel in flight
  ~0.24 m; travel during the 200 ms prep ~0.16 m. These bound, but do not
  establish, a clearable height for OUR robot. The advisory's 0.03–0.12 m
  jump band stays ASSUMED; advisory = JUMP_CANDIDATE, never permission.

## Open / decisions for Claude 1

1. `tools/perception_health/SPEC.md` enum is off by one against ORB_SLAM3
   Tracking.h (NOT_INITIALIZED=1, OK=2). Not changed; needs an owner decision.
2. TerrainAdvisory message type is PROPOSED; STM32 firmware owner review needed.
3. Merge order once 24 Oct data is evaluated: ground-plane -> obstacle-decision
   -> bag-eval -> local-map -> ros node; others independent.
4. Scenario C disconnects: root cause UNKNOWN (data only on the Pi).
