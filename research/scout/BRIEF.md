# Research scouting brief (2026-10-30). The owner wants a publishable paper, not only demos

Context (read for facts, don't redo the work):
- `README.md`, `ops/worklog/CURRENT.md`, `ops/worklog/reviews/2026-10-30-*.md` (if present on this branch).
- The open PRs (`gh pr list`).

What exists (MEASURED unless marked):
- **Hardware:** a wheel-bipedal robot (WBR) arrives in Nov 2026: STM32H723, BMI088, RobStride motors on CAN, micro-ROS to a Pi 5.
- **Perception on a Pi 5 + RealSense D435i:**
  - ORB-SLAM3;
  - per-frame RANSAC floor plane, giving box height within ±1 cm and distance within 5 cm at 1 m;
  - a TerrainAdvisory (NONE / JUMP_CANDIDATE 3–12 cm / STOP / UNCERTAIN) sent over COBS+CRC UART to the MCU, advice only, stale after 300 ms;
  - 630/630 echoes, RTT P50 2.83 ms.
- **Simulation:** planar MuJoCo + LQR (160/160 push recovery, parameters ASSUMED); PPO RL baseline (weak); processor-in-the-loop with the C controller 160/160.
- **OS course work:** an age-of-information (AoI) / freshness supervisor on an STM32 FreeRTOS (FRESH/HOLD/FAILSAFE).
- **CN course work:** RTP/RTCP video to an edge AI server.

Write ONE file `research/scout/<your-topic>.md`. Do not commit. Do not edit any other file. Rules:
- English.
- Every paper cited with title, authors, year, venue and a working link that you opened. Mark UNVERIFIED if you could not open it. Never invent a citation.
- Be honest about novelty: name the closest prior work and what would actually be new.
- At most ~150 lines.

Topics (one per worker):
- **T1 (wheel-legged)** `t1-wheel-legged.md`:
  - state of the art in perception-aware wheel-legged / wheel-bipedal robots: Ascento, Diablo, Tron1, Unitree B2W, DM-jump, and step/obstacle negotiation, jumping and terrain classification with depth cameras;
  - which gaps a low-cost system (Pi 5 + D435i + MCU) can credibly fill;
  - 3 candidate paper ideas with novelty risk.
- **T2 (freshness / AoI)** `t2-freshness-safety.md`:
  - AoI and data-freshness for perception-to-control links in robots and edge systems;
  - runtime monitors, staleness and timeouts in the ROS 2 / micro-ROS context, safety supervisors;
  - is "perception advisory with freshness contract to a safety MCU" new enough?
  - 2–3 candidate paper ideas.
- **T3 (venues)** `t3-venues.md`:
  - realistic venues for a student-led paper in 2027 with deadlines: Vietnamese/regional IEEE conferences (ATC, RIVF, NICS, KSE, ICCE-Vietnam, ISCIT), IROS/ICRA/Humanoids workshops, journals (e.g. JRM, Robotics MDPI, IEEE Access, Sensors);
  - HUST student research awards;
  - page limits, review style, typical acceptance;
  - which fits which idea.
- **T4 (evidence plan)** `t4-evidence-plan.md`, no web needed:
  - from the repo's existing data and tools, list the experiments a paper would need: baselines, ablations, number of trials, statistics, threats to validity;
  - list what can be done before the robot exists vs after;
  - which existing results are reusable as-is and which are weak (single camera, tabletop, ASSUMED parameters).

Done = the file exists and follows the rules. End your final message with the file path.
