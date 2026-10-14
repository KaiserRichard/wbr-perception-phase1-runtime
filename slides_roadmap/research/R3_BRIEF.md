# R3: Hardware/lab plan, timeline and critical path (read slides_roadmap/COMMON.md first)
Write `slides_roadmap/research/R3_plan.md` (aim 3–6 pages).
1. Hardware inventory needed per phase, from the repo facts plus your research: Pi 5 8 GB, 5.1 V/5 A
   supply, storage (128 GB card, NVMe option with Pi 5 HAT and its power cost), D435i + USB 3 cable,
   active cooler, AprilGrid calibration target (print size, rigid backing), camera/Pi mounts,
   STM32H7 board, robot chassis and battery, DC-DC converter, network (Wi-Fi/Ethernet), tripod/stand,
   measuring tape, optional external camera or lab motion capture. For each: needed in which phase,
   status (have / ordered / lab must provide / buy), and an approximate cost range if buying (cite).
2. Lab booking plan: which phases need the lab and which hardware at the same time, session length,
   what to prepare before each session so lab time is not wasted (scripts ready, data space, checklist).
3. Critical path from today (14 Oct 2026) to "camera SLAM running on the robot and sending health to
   the STM32": phases, dependencies, durations as realistic ranges, what can run in parallel (e.g.
   calibration prep while waiting for the supply; STM32 message spec on the Mac), and the shortest
   non-roundabout ordering. Identify steps that can be safely skipped or deferred and ones that must not.
4. Risk register: top 8 risks with likelihood, impact, early warning sign, mitigation.
5. Decision points where the owner must choose (e.g. ORB-SLAM3 vs alternative, ROS 2 on robot or not,
   link type, buy NVMe or not), each with recommended default.
End with a one-page week-by-week plan table.
