# WBR research rules

The project's research standard, from the owner's project instructions. Every agent
applies it in every mode.

## Project

WBR (Wheel-Biped Robot) Phase-1 perception/runtime research on a Raspberry Pi 5
(8 GB, Ubuntu, ROS 2 Jazzy), Intel RealSense D435i (on loan), ORB-SLAM3.

**Ownership boundary.** The Pi owns perception, SLAM, VIO (visual-inertial
odometry), mapping and non-hard-real-time estimation. The STM32H7 owns hard-real-time
body estimation, balancing, LQR, VMC, FSM, actuator and motor safety. If ROS, SLAM or
the Pi fails, the robot must not lose balance.

**IMU boundary.** The D435i camera IMU (`imu_camera`, for perception) and the STM32
body IMU (`imu_body`, control side) are different. No multi-IMU fusion before frames,
timestamps, calibration and ownership are established for each.

## Frames and timestamps

Treat frames (world, map, odom, base_link, body, imu_body, camera, camera_optical,
imu_camera, left_camera, right_camera) and timestamps as first-class design objects.
Distinguish sensor capture time, device timestamp, driver timestamp, ROS header
stamp, publish time, receipt time, processing start/end and output time. Never
subtract values from different clock domains without a defined relationship.

## Evidence standard

Evidence before confidence. Architecture before implementation. Measurement before
optimization. Known baseline before adaptation. Failure characterization before
workaround. Understanding before automation.

Label every claim: **SOURCE-SUPPORTED**, **MEASURED**, **CALCULATED**, **INFERRED**,
**ASSUMED**, **UNKNOWN**. Never declare a gate PASS without explicit evidence. A
tool PASS is evidence for review, not a gate PASS.

## Debugging order

hardware -> USB/device -> raw sensor -> clocks/timestamps -> driver -> ROS ->
topics/QoS -> calibration -> ORB-SLAM3 -> trajectory -> evaluation.
Do not tune SLAM to hide a broken sensor or runtime layer.

## Gate ladder (labels may evolve; evidence matters more)

N0 platform, N1 physical D435i access, N2 raw sensor qualification, N3 ROS 2 pipeline
and rosbag record/replay, N4A known-dataset ORB-SLAM3 baseline, N4B D435i offline
stereo-inertial, N4C D435i live stereo-inertial, N5 evaluation/profiling, N6
perception-health interface, N7 WBR integration boundary. Current state lives in
`docs/PROJECT_STATE.md` and `docs/NEXT_GATE.md`, never assumed from memory.

## Evaluation and adaptation

Later metrics: ATE, RPE, initialization success, tracking loss/relocalization,
P50/P95/P99 latency, dropped frames, queue depth, CPU load/frequency/temperature,
memory, throttling. Do not attempt every metric at once.
Adaptive runtime path: static characterization -> rule-based policy -> ablation ->
contextual/simple learned policy -> RL only if justified.

## Simulation and learned control (MuJoCo, RL vs LQR)

- **Simulation only.** Nothing trained here goes to the STM32, motors or the real
  robot without a separate reviewed plan. The STM32 LQR/VMC/FSM stays the authority
  on hardware. Label all results **SIMULATION**.
- **Baseline first.** Before any RL training, reproduce the LQR baseline in the same
  MuJoCo model: linearization point, Q/R weights, gains, and its closed-loop
  behaviour (recovery from push/tilt, steady-state error, effort). Record where the
  model parameters come from (CAD, measured, guessed = ASSUMED).
- **Fair comparison.** Same model, same initial-state distribution, same disturbance
  set (pushes, slopes, sensor noise/delay, parameter perturbations), same control
  rate and actuator limits, same episode length. Pre-declare the metrics before
  running: success/fall rate, recovery time, peak tilt, tracking error, control
  effort/torque peaks, and robustness under model mismatch.
- **Statistics.** Multiple training seeds (at least 5) and many evaluation episodes
  per condition; report mean with a confidence interval, and keep failed seeds.
- **Sim-to-real honesty.** Report what the simulator omits (motor dynamics, backlash,
  sensor delay, contact model). An RL win in nominal simulation is not evidence of
  a hardware win; robustness tests under perturbation matter more.
- **Ladder.** LQR baseline -> LQR with tuned gains / gain scheduling -> RL residual
  or RL policy, and only claim RL is better where the evidence says so.
- Code lives in this repository under `sim/` (create it on a `chatgpt/...` branch);
  training outputs (checkpoints, logs, videos) stay out of git, with paths and
  hashes recorded in the session log.

## Sources

Prefer peer-reviewed papers, then standards, manufacturer docs, official project
docs, upstream source, maintainer issues, and secondary articles only when needed.
Separate what a source says from our interpretation.

## Recommendations

For an important recommendation, write: problem -> mechanism -> evidence ->
experiment -> decision. Be direct; do not automatically agree with the owner's
hypotheses.
