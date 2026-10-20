# 2026-10-20 — codex-g frozen PPO outcome audit

- Read-only worker for conductor codex-b; read AGENTS, CURRENT, research rules, profile and frozen protocol in full.
- Clean detached worktree at `e821212`; fetched origin and created `chatgpt/20261020-ppo-outcome-audit` from `origin/main`. Runtime diff against training source `608222b` empty.
- Run: `/private/tmp/wbr-augmented-20261020/ppo-full-conductor-01`. No implementation defect found in inspected observation/action/reward/end/budget paths; completed physical failures, not infrastructure failures.
- Independently enumerated 960 outcome slots: LQR 160/160 PASS, PPO 0/800; 680 falls, 120 displacement violations, no numerical/training failures. Five equal seed differences −1 produce SD 0 and CI [−1,−1], conditional on frozen seeds/noise/model/budget.
- Counted all 750,000 training transitions; loaded five finite final checkpoints/optimizer states; 150,000 steps, 1,500 PPO epochs, 6,000 Adam steps each. Read all optimizer logs, 15 sampled training chunks, seven selected evaluation traces; 21 deterministic action probes matched exactly.
- Training: 2,783 completed physical terminations plus five partial final episodes; only 10/1,379 started push episodes received force (nine full, one partial). Sparse push exposure is measured; causal explanation remains INFERRED without ablation.
- Full report: `/private/tmp/wbr-augmented-20261020/ppo-outcome-g-report.md`.
- New diagnostics: `/private/tmp/wbr-augmented-20261020/ppo-outcome-g-diagnostics-PeMfIb/`; exact commands and evidence in report. `audit.py`, `extra.py`, `config-check.py` exited 0 using the prescribed backend, inference CPU threads 1; stderr logs empty. Effective scenario/acceptance settings match protocol; four LQR designs match original archive byte-for-byte.
- No training, runtime/config/protocol/gain changes, broad tests, full rehash, workers, account launches, hardware, PR, merge or Claude review. Only this repository receipt was written; shared logs left untouched as scoped.
