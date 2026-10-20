# Owner profile (for agents)

How to work with the owner of this project. Agents read this with `AGENTS.md`.

## Who
- Nguyễn Quốc Khánh (GitHub `KaiserRichard`), 4th-year Electronics and
  Telecommunications Engineering student at Hanoi University of Science and
  Technology (HUST), moving toward robotics research (graduate study in Japan).
- Research interest: timing-aware perception on resource-limited robot computers,
  and making edge-computer outputs trustworthy to a real-time controller. Now also
  exploring learned control (RL) for the wheel-biped robot, in simulation, against
  the existing LQR baseline.

## Skills (skip beginner explanations of these)
- Embedded: STM32 (F446RE, FreeRTOS, UART/DMA, timers), PCB design and bring-up,
  C/C++, bare-metal firmware.
- Embedded Linux: Raspberry Pi 5, Ubuntu, real-time scheduling, power/throttle
  monitoring.
- Robotics: ROS 2 Jazzy, RealSense, ORB-SLAM3, trajectory evaluation, frames and
  clock domains; also Gazebo, RViz, Nav2, ros2_control, Isaac Sim/Lab (from CV).
- ML: PyTorch, ONNX quantization and profiling; some multi-objective RL survey work.
- Research method: pre-declared validity rules, evidence labels, keeping failed runs.

## Language and style
- Always reply in **English**, even when the owner writes Vietnamese or mixed
  Vietnamese-English (they use technical work to practise English). Switch only if
  explicitly asked ("reply in Vietnamese", "trả lời bằng tiếng Việt").
- Write at a senior-undergraduate EE/robotics level. Expand an abbreviation the
  first time, then use it.
- Be direct and evidence-first: problem -> mechanism -> evidence -> experiment ->
  decision for important recommendations. No motivational filler. Disagree when the
  evidence says so.

## Working preferences
- Decide reversible engineering choices yourself and report results; do not ask
  yes/no questions about them. Ask only for physical actions, irreversible steps
  and real decisions.
- End results with a clear Recommendation for what to do next.
- Keep everything in files (`ops/worklog/`), so another agent (Claude) can pick up
  cold. Claude is an occasional reviewer with limited quota.
- Codex accounts are shared across tasks; check one is idle before using it.
