# Portable learning preferences

English unless explicitly asked otherwise. Senior-undergraduate EE/robotics level.

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
  deterministic plots. The later illustrated-revision request below supersedes
  the original restriction to decorative AI images. Use YAML tags, MathJax,
  relative assets, wiki-links and callouts. Do not request the same review again.
- Candidate experiment: residual PPO versus delay-aware LQR, train delay2–5ms,
  test6–10ms; no research-gap claim before literature review. New training is
  separate from lesson production and follows current control experiment rules.
- Portable instructions: [Obsidian lesson skill](SKILL.md).
  These repository files support continuity across accounts; account memory does
  not transfer automatically.

- Illustrated revision (2026-10-21): mechanical teaching must use polished technical
  plates at least comparable to the owner's nine supplied WBR figures. Explain
  geometry, COM, reactions and derivations beside the plate; a crude stick figure
  or a detached gallery is insufficient. Reuse supplied plates with captions
  qualifying assumptions/errors. Provide English prompts with exact output filenames
  for additional generated illustrations; verify conceptual art against the maths,
  and keep measured plots reproducible. Do not claim generated art is validated CAD.
