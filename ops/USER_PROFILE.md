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

## Learning materials (owner request, 2026-10-21)

- Uses **Obsidian**. Substantial lessons should arrive as one ZIP containing a
  main Markdown lesson with YAML tags, local linked/embedded images, sources,
  exercises/answers and minimal opening instructions. Assets must remain usable
  after extraction into an existing vault; use Obsidian MathJax for equations.
- Wants mathematical understanding before algorithm research: intuition,
  assumptions, notation/dimensions, derivations, worked examples and tests of
  understanding. Knows RL mathematical language but needs refreshing; has not
  studied LQR deeply. Tie LQR, RL, PPO and residual control to the actual WBR code.
- Has studied much of Roboticsbook, partly read Chapter 6, not Chapter 7;
  previously studied RL including the Hugging Face course. Avoid assuming either
  complete mastery or no prior knowledge.
- Prefers clear mechanical/technical illustrations over decorative colour.
  Generated images are welcome; exact equations and measured plots need verified
  mathematics/data. Reused images need attribution and appropriate reuse rights.
- Connect learning to implementation, MuJoCo simulation, fair comparisons,
  reproducible tests and measurements. Do not present an interesting idea as a
  confirmed research gap without checking the literature.
- Claude approved the proposal with changes (owner relayed, 2026-10-21): deliver
  three ZIPs in order under `docs/learning/obsidian/`: LQR first (send immediately),
  RL→PPO second, residual/experiment third. One-page toolkit inside Pack 1;
  one CPU-light script with expected output per pack. Technical figures use
  Matplotlib/SVG, AI images only labelled decoration. Use YAML tags, MathJax,
  relative assets, wiki-links and callouts. Do not request the same review again.
- Candidate experiment: residual PPO versus delay-aware LQR, train delay2–5ms,
  test6–10ms; no research-gap claim before literature review. New training is
  separate from lesson production and follows current control experiment rules.
- Portable instructions: [Obsidian lesson skill](skills/wbr-obsidian-lessons/SKILL.md).
  These repository files support continuity across accounts; account memory does
  not transfer automatically.
