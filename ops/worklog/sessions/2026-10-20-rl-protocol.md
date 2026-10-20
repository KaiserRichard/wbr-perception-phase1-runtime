# 2026-10-20 RL protocol — codex-k worker for codex-f

- Assigned branch `chatgpt/20261020-rl-protocol`, clean start `417c1e216b86f99aabff9dfdd5a58c560bcbbe56`.
- Read AGENTS, CURRENT, USER_PROFILE, RESEARCH_RULES and final Claude approval.
- Doc edit: `sim/rl/protocol.json` predeclares 5 × 150000 direct-torque PPO steps,
  20 paired held-out noise seeds per condition, fixed settings, retained failures
  and seed-level paired uncertainty; no WBR training or winning claim.
- Read actuator contract; fixed 15-entry padded common observation, runtime seed
  mapping and unchanged control-sample acceptance. Implementation not verified here.
- Doc edit: `sim/rl/README.md` adds primary PPO/Gymnasium sources, equation,
  runnable dependency/test/CartPole smoke commands and explicit limitations.
- Added `sim/rl/requirements.txt` and nine stdlib protocol tests; no plant edits.
- Actual install exit 0: Python3.12.13/x86_64; Torch2.2.2, SB3 2.3.2,
  Gymnasium0.29.1, NumPy1.26.4, MuJoCo3.3.7; no global installs/extras/TLS bypass.
- Actual CPU/one-thread CartPole PPO `learn(64)` exit 0, 64 steps, finite changed
  parameters; SMOKE ONLY. `pip check` exit 0. Protocol tests 9/9, no skips.
- Reusable environment: `/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv`.
- Raw install/smoke logs, versions and contract snapshot in its parent directory.
- Read-only lookup `ci.yml` absent (exit 1); actual `tests.yml` and generic
  `sim/*/tests` discovery read successfully; no workflow edit needed.
- Doc edits outside git: `protocol-steering.md`, `protocol-pr-body.md`, and
  `protocol-report.md` / `protocol-audit-report.md` under `/private/tmp/wbr-augmented-20261020/`.
- PR [46](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/46) opened unmerged; exact commands/hashes in report.
- This named session log records its own documentation changes; shared logs untouched.
- Recommendation: conductor verifies plant and PR, then assigns wrapper/full seeds.
