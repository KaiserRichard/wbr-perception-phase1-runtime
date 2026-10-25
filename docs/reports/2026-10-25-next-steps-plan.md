# Terrain Advisory Integration: Next Phase Plan

**Purpose:** supervisor-meeting plan for connecting camera obstacle advice to the robot controller while preserving local motor and jump authority.

**Evidence labels:** **VERIFIED** means present in inspected local source/docs, not hardware qualification. **UNKNOWN** means not established by those files. **ASSUMED** marks a proposed plan or acceptance threshold. All unmeasured thresholds below require owner agreement.

## 1. Target board fit and scope

- **Current candidate is not the jumping WBR:** `Microros_H723_USB` documents a CtrBoard-H7 STM32H723 differential wheeled base with two RobStride/CyberGear actuators, BMI088 IMU, LCD, USB CDC, and micro-ROS Agent transport (`docs/hardware.md:7-18`). Its `/cmd_vel`, `/cmd_mit`, `/cmd_torque`, `/motor_enable` interface controls wheels (`docs/topics.md:17-27,32-52`). **VERIFIED:** this is distinct from the five-bar jumping WBR analyzed in `docs/proposals/DM_JUMP_INTEGRATION_ANALYSIS.md:6-23`.
- On the H723 wheeled firmware, add `sub_terrain_advisory`, message storage, callback, entity bit/cleanup, and registration in `Core/Src/freertos.c::create_entities()` alongside existing subscriptions (`:93-115,530-546,600-674,741-759`). This is the `defaultTask`/`StartDefaultTask` micro-ROS loop (12 KB stack per `docs/development.md:16`; task created in `freertos.c:200-205,273-282`), not the motor task. `spin_some` runs with a 1 ms timeout (`freertos.c:362-369`).
- **Executor:** currently `rclc_executor_init(..., 4, ...)` has four subscription handles (`/cmd_vel`, `/motor_enable`, `/cmd_mit`, `/cmd_torque`); enlarge capacity to **5** and add the new subscription. Publishers are outside this executor handle count (`freertos.c:654-674`).
- **QoS and payload:** use Best Effort, Keep Last depth 1, `std_msgs/msg/Float64MultiArray`, exactly eight finite values in the contract order; validate code/ranges and do not refresh receive time on invalid input (`docs/interfaces/TERRAIN_ADVISORY_TOPIC.md:5-28,30-42`; example `:13-18,31-63`). H723 command topics keep their existing QoS and callbacks. Advisory handling must not write motor commands or delay the command executor.
- **Memory:** reserve static storage for eight doubles (64 bytes) plus the ROS message struct and advisory snapshot; avoid dynamic allocation in callback. This is a lower-bound payload estimate, not total middleware cost. The H723 build config sets `RMW_UXRCE_MAX_SUBSCRIPTIONS=5`, `MAX_HISTORY=4` and publisher pool 10 (`micro_ros_stm32cubemx_utils/microros_static_library/library_generation/colcon.meta:43-48`); five subscriptions fit the configured pool exactly. Measure micro-ROS minimum heap, RTOS heap, and task stack watermark after entity creation (`freertos.c:156-157,768-772`; `docs/development.md:72`). **UNKNOWN:** actual heap/stack headroom and any pool config used by the deployed binary.
- Keep advisory isolated from `/cmd_vel` and motor state. Existing wheel command watchdog is 500 ms (`User/Config/robot_config.h:63-69`); RC E-stop, RC link loss, and `/motor_enable` behavior are described in `docs/topics.md:40-52`. These are wheeled-base protections, not proof of WBR safety.
- **Reusable:** topic contract/validation, Best Effort micro-ROS subscription pattern, bounded storage, sequence/age telemetry, F446 reference code and Pi publisher are reusable concepts (`tools/microros_f446/README.md:40-57`; `ros2/wbr_obstacle_node/wbr_obstacle_node/node.py:18-47,52-80`). **UNKNOWN for WBR board:** controller MCU/RTOS, micro-ROS presence, USB CDC route, spare executor/pool capacity, display interface, local jump FSM API, E-stop/arming semantics, and board-owner integration effort. Do not transplant H723 motor/RC assumptions to WBR.

## 2. Phased integration and gates

### P1 — Board subscriber, motors disabled

- **Work:** on the selected board add receive/validate/freshness state and LCD indication only. Keep hardware E-stop engaged and `motor_enable=false`; keep all jump/motor outputs unchanged. Display code, distance, confidence, and `STALE/UNCERTAIN`.
- **Test / exit:** send valid NONE/JUMP/STOP/UNCERTAIN, malformed length/NaN/out-of-range, pause >300 ms, disconnect/reconnect USB. LCD must match valid values, reject invalid values without refreshing age, go uncertain when stale, and recover on valid data. Confirm motor-enable remains false and no actuator output changes.
- **People / equipment:** firmware owner, target controller board + display, Pi or ROS host, USB data cable, bench power with motors physically disconnected or E-stop verified. **UNKNOWN:** which WBR board and safe disabled-output procedure.

### P2 — Live camera-to-board latency and application ACK

- **Work:** connect D435 → Pi camera/depth → `wbr_obstacle_node` → board. Add a board ACK carrying the last accepted sequence on `/terrain_advisory_ack` (F446 example already echoes accepted sequence every 100 ms: `tools/microros_f446/README.md:44-49`). **ASSUMED:** ACK means validated application receipt, not mere USB/Agent delivery. Record Pi publish and ACK receipt monotonic times against sequence; do not compare Pi and MCU clock epochs.
- **Test / exit:** run for a declared duration, save per-sequence publish-to-ACK latency, missing/duplicate/out-of-order sequences, publish rate and stale intervals; inject USB unplug/replug and confirm P1 safe stale behavior. Agree a latency percentile/drop limit before declaring pass. **UNKNOWN:** required control latency threshold.
- **People / equipment:** P1 setup, live D435, Raspberry Pi 5, ROS 2/micro-ROS Agent, storage for logs, firmware owner for ACK publisher.

### P3 — ORB-SLAM3 and obstacle node together on Pi

- **Work:** run live ORB-SLAM3 stereo/RGB-D path and obstacle node concurrently, with camera publisher, map/pose outputs, and advisory enabled. Existing obstacle publisher has depth-1 best-effort input/output and callback rate limiting (`node.py:20-47,52-70`).
- **Test / exit:** sustained representative capture with logs of ORB tracked rate/status, depth/advisory rate, processing and end-to-end ACK latency, dropped frames, CPU per process, Pi temperature/throttling, and memory. Repeat stationary and moving-camera scenes; preserve rosbag/logs. Use `tools/orb_checks` on saved replay bags for pose/status/trajectory summaries and `tools/local_map/from_bag.py` for exploratory height-map artifacts; these are offline diagnostics, not live safety evidence (`tools/orb_checks/README.md:11-25`; `tools/local_map/README.md:57-67,86-94`). **ASSUMED:** define minimum rate and maximum temperature/CPU margin with owner before pass. Saved camera A/replay evidence exists, but concurrent live load is **UNKNOWN** (`ops/worklog/CURRENT.md`, Hardware section).
- **People / equipment:** Pi 5, D435 and USB cable, board from P2, cooling/power, lab operator; camera software owner for runtime setup.

### P4 — Jump-gating design; owner approval; simulation first

- **Design invariant:** an operator jump request **AND** fresh `JUMP_CANDIDATE` **AND** an owner-approved distance window are necessary, then local balance/contact/clearance/arming/E-stop checks still decide. Stale, NONE, STOP, UNCERTAIN, invalid data, or lost link can never initiate a jump (`docs/interfaces/TERRAIN_ADVISORY_TOPIC.md:35-42`; `DM_JUMP_INTEGRATION_ANALYSIS.md:38-40`). No jump command or torque authority is delegated to Pi.
- **Simulation check:** `sim/` contains a MuJoCo reduced planar balancer and five-bar modeling/analysis, but the documented planar model explicitly omits jumping, impact, five-bar kinematics and variable leg length (`sim/README.md:1-15,90-97`; `sim/fivebar/`). **UNKNOWN:** validated jump/contact simulation. First add/identify a jump-capable model and test gate logic across approach distance, stale/dropout, false positives (including near 0.12 m), and operator cancel; simulation is not permission to run hardware.
- **Approval / exit:** owner approves distance window, freshness threshold, required local vetoes, test scenarios, and a written firmware-state transition design. Show simulation traces and prove no advisory-only initiation before implementing any FSM changes.
- **People / equipment:** owner, firmware owner, simulation/control reviewer; development workstation. No robot motion.

### P5 — Supported and tethered robot tests

- **Entry:** P1–P4 evidence reviewed; WBR firmware owner and owner approve; physical E-stop and independent disable confirmed; jump gate is local and bounded. **UNKNOWN:** approved stand/tether/clearance arrangement and safe commissioning limits.
- **Test / exit:** first run wheels/legs unloaded on a rated stand with no jump trigger; inject advisory and faults while verifying local vetoes. Then tethered low-energy tests in a cleared area, starting with inhibited requests and progressing only through individually approved cases. Log IMU/state, operator request, advisory sequence/age/distance, FSM transitions, motor commands, E-stop and video. Any unexplained transition, stale acceptance, or tracking loss stops progression.
- **People / equipment:** WBR firmware owner and operator physically at E-stop, rated robot stand, restraint/tether, clear test area, Pi/camera, power isolation and video/logging. No unsupported free jump.

## 3. Risk register and evidence tests

| Risk | Test / containment | State |
|---|---|---|
| USB link drop or Agent restart | Unplug/restart during P1/P2; verify no valid ACK, board freshness expires locally, LCD uncertain, motors remain disabled; verify reconnect starts uncertain until a fresh valid packet. | Likely path is USB CDC on target only if board supports it; WBR route **UNKNOWN**. |
| Stale or malformed advisory accepted | Invalid length, NaN/Inf, bad enum, duplicate sequence; verify no timestamp refresh; pause traffic through 300 ms boundary and verify `UNCERTAIN`. | 300 ms is interface proposal, owner must ratify for WBR. |
| False JUMP near 12 cm | Create controlled obstacle/range sweep around detector upper `jump_max_h=0.12 m` (see `ros2/wbr_obstacle_node/wbr_obstacle_node/core.py:23-29`); record code/confidence/distance and ground truth; simulate gate with false positives. Never use this as a hardware trigger before P4 approval. | Detector threshold exists; false-positive rate **UNKNOWN**. |
| Range-edge flicker | Sweep obstacle across configured range boundary with and without `range_hysteresis_m`; record code transitions and sequence; compare enabled/disabled hysteresis and persistence. | Default hysteresis 0.10 m; real-scene performance **UNKNOWN** (`node.py:26-28,63-65`). |
| Pi CPU/thermal contention | P3 simultaneous ORB + obstacle workload; log CPU, rates, temperatures, throttle flags, drops, ACK latency and memory; repeat expected lab duration. | Concurrency evidence **UNKNOWN**. |

## 4. Meeting decisions and dependencies

- Confirm whether P1 target is H723 wheeled demonstrator or actual jumping WBR board; the two are not interchangeable.
- Assign board/firmware owner and reserve their time for subscriber, ACK, build, and safety review. Confirm Pi-to-board cable/connector and disabled-motor procedure.
- Approve P2 latency/drop criteria, P3 CPU/temperature/rate limits, P4 local vetoes and distance window, and P5 stand/tether setup before those gates.
- No motion-control change is implied by this plan. Current jump trigger evidence is PS2 R1 hold; the UART `J` field is parsed but not connected to the jump FSM (`DM_JUMP_INTEGRATION_ANALYSIS.md:21-23`).

**File:** `docs/reports/2026-10-25-next-steps-plan.md`
