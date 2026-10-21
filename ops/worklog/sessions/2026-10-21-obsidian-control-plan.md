# Obsidian LQR/RL/PPO proposal — 21 October 2026

- Owner requested research and a Claude review proposal first; later deliverable
  is an English Obsidian ZIP with tagged Markdown, technical images and a path
  into WBR implementation, simulation and measured experiments.
- Read root instructions, CURRENT, USER_PROFILE, research rules, existing guides,
  paper index, LQR/augmented-LQR code and v2 observation/reward/action code/config.
- Shared checkout was on camera-day with modified worklogs and generated fuzz/build
  artifacts. Left those changes and branch untouched; reused this chat's clean
  cafe-compute-review worktree, branching from origin/main at 28f1eb7.
- Checked the supplied course sites and primary LQR/PPO/GAE/residual sources.
  Residual RL is established; no exhaustive novelty search or new gap is claimed.
- Created the proposal and reusable skill; saved owner preferences in USER_PROFILE.
  Local skill installation and validation results follow below.
- Scope is documentation only. No lesson/images/ZIP yet, no fresh experiments,
  no change to active PPO, camera operations or the protected student exercise.
- Rollback: revert this documentation PR; the local skill copy can be replaced
  from the repository version. No runtime rollback is needed.
- Validation: bundled Python initially lacked PyYAML; the existing Python 3.11
  with PyYAML 6.0.3 ran `quick_validate.py` successfully. No dependency install.
  `python3 scripts/check_doc_links.py ops/worklog/reviews ops/skills/wbr-obsidian-lessons`
  found zero missing references; `git diff --check` passed. Proposal is 867 words.
- Installed the skill at `~/.codex/skills/wbr-obsidian-lessons/SKILL.md` and compared
  its bytes with the repository copy: identical. Future account access requires
  reading the repository profile/installing that skill, not shared account memory.
- Publication follows the normal feature-branch PR and green-CI merge workflow.
  Claude's content review is pending; this publication does not approve production.
