---
name: wbr-obsidian-lessons
description: Create mathematics-first WBR robotics and control lesson packs for Obsidian, with Markdown, local technical figures, exercises, project experiments and a portable ZIP. Use for substantial learning materials, not ordinary brief questions.
---

# WBR Obsidian lessons

## Owner's learning preferences

- Write in English unless the owner explicitly requests another language.
- The owner studies with Obsidian and wants the mathematics behind algorithms,
  not just configuration recipes. Their EE/embedded and robotics background is
  substantial. They have encountered RL notation but want a refresher; LQR needs
  deeper teaching. They partly read Roboticsbook Chapter 6 and have not read 7.
- Short proposals and chat updates; complete derivations in the actual lessons.
  Do not confuse a request for concise reporting with a request to omit teaching.
- Use WBR examples: balance and push recovery, LQR versus PPO, then residual PPO.
  End lessons with implementation, simulation, tests, measurements and interpretation.
- Prefer restrained mechanical/engineering visuals, monochrome where practical.

## Scope and research

1. Read the repository's `AGENTS.md`, `ops/USER_PROFILE.md`, current worklog and
   relevant source/config before explaining project behaviour. Preserve concurrent
   changes and ongoing experiments. Do not write or duplicate the owner's protected
   `sim/parity/student.py::gain_schedule` solution.
2. Respect a requested proposal review before dependent production. For the current
   LQR/RL/PPO series, Claude's approval has arrived with the amendments below;
   do not ask for that approval again. New experiments still need their own scope.
3. Verify external readings and use primary papers/official documentation for
   technical claims. Suggested anchors are Roboticsbook, MIT Underactuated Robotics,
   Hugging Face Deep RL theory, original PPO/GAE/residual papers and the project's
   pinned implementation docs. Distinguish paper, implementation, hypothesis and
   measured result. Do not call an idea a research gap without a literature review.

## Teaching pattern

- Give intuition, a notation/dimensions table, assumptions, mathematical derivation,
  a small worked numerical example, project-code connection, common mistakes and
  self-check questions with answers. Use Must Know / Good to Know / Skip For Now
  where this helps scope, rather than assigning an entire textbook by default.
- Bridge LQR and RL through Bellman optimality. Distinguish quadratic cost weights
  from the RL Q-function, reward from probability ratio, state from observation,
  simulation tick from policy transition, and training noise from deterministic
  evaluation. Explain discount and sampling-time differences before equating costs.
- Check algebra and toy calculations. Explain the conditions behind optimality and
  stability statements; neither PPO clipping nor a residual cap is a safety proof.
- Reuse maintained project guides/glossaries instead of creating divergent facts.

## Deliverable

Provide a ZIP containing a main `.md` lesson with table of contents and YAML
tags, local `assets/`, source/provenance notes, exercises/answers and minimal
opening instructions. Supporting notes/code are optional when useful. Preserve
relative paths so extraction into an existing vault works offline; avoid required
community plugins, remote-only image embeds and absolute author-machine paths.

Use Obsidian MathJax `$...$` and `$$...$$`, with clean multiline equations and
defined symbols. Prefer normal relative Markdown image embeds for portability.
Keep one main reading path; use linked notes only when they improve navigation.

Technical figures use Matplotlib/SVG or another deterministic diagram tool. AI
images, if requested, are labelled decoration only; they do not carry exact
geometry, equations or measured results. Include sources/reuse rights for
third-party figures. Never invent plots, CAD dimensions or hardware parameters.

## Approved three-pack sequence (owner relayed Claude review, 2026-10-21)

- Pack 1 LQR first, delivered immediately when ready; its toolkit is a one-page
  refresher. One CPU-light Python script checks scalar LQR by hand, solves DARE
  on a cart-pole, and reads saved WBR gains without touching the protected exercise.
- Pack 2 RL to PPO: one small script computes GAE and PPO clipping on a tiny rollout.
- Pack 3 residual + experiment: one script plots LQR/residual torque from saved
  runs; do not fabricate unavailable data. Candidate question: residual PPO versus
  delay-aware LQR, training delays 2–5 ms and held-out testing 6–10 ms. Check the
  literature before any gap claim; specify the controller's delay knowledge.
- Store each ZIP under `docs/learning/obsidian/`, retaining maintainable sources.
  Each pack needs expected script output, YAML tags, MathJax, relative `assets/`,
  Obsidian callouts and wiki-links between packs. Label future links pending until
  their destination pack is delivered. Do not delay Pack 1 to finish later packs.

Before delivery, extract the ZIP to a fresh folder; check local links and assets;
inspect Obsidian math and figures; run included examples. Retain unresolved limits
explicitly rather than claiming a preview or experiment ran when it did not.

## Project and portability

Conclude with a scoped simulation/test plan: question, baselines, variables,
frozen evaluation, seeds, metrics, compute, commands/expected outputs and evidence
paths. Keep assumed model parameters separate from identified hardware data.
Follow repository authorization for training and all hardware actions.

Keep this skill's canonical copy in the repository and install a matching copy
in the current account's skill directory when requested. Record preferences in
the repository owner profile. Another account must receive/read those files or
install the skill; do not promise automatic cross-account memory. Include the
portable instructions/profile in a future lesson ZIP when account migration is
part of the owner's request.
