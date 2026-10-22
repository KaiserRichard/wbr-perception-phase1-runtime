# Motor workspace report follow-up — 2026-10-22

- Read root/sim agent guidance, CURRENT, USER_PROFILE, PR122 report and PR123 review.
- Created `chatgpt/20261022-motor-workspace-report` from `origin/main`; when PR123 merged, fast-forwarded normally to `a826f6c` and retained its Claude appendix verbatim.
- Read only the immutable saved motor analysis and original combined-corners study. No rollouts, training, Pi/hardware, model/runtime/test changes, or tests.
- Retained exact attribution in `/Users/quockaiser/wbr-evidence-archive/sim-motor-load-followup-20261022-01/review123-followup-01/`: `verify_saved.py`, `verify_saved.log`, `case-attribution.csv`, `case-attribution.json`.
- Verification matched all 30 IDs, 150,030 raw control samples, 148,090 reachable, 1,940 excluded, per-case saved counts/peaks and timestamps within 1 ns. Exclusions are A-side outer reach only: L20 combined-target 5×151 (3.019% each; group 755/25,005); L20 stronger-sample 5×237 (4.739% each; group 1,185/25,005). Both groups' first/last exclusions fall after 3.000–3.150 s; push-only attribution is unsupported because mass, delay and wheel-map offsets co-vary.
- Global balance-only peaks: A 0.40542578868132084 N·m, `L20_stronger_sample_seed1` tick 10; E 0.35224760632453234 N·m, `L12_stronger_sample_seed1` tick 9. Not total motor torque; radial reaction absent.
- Updated the report body to one-page scope before preserved Claude appendix. Updated only the motor-load summary bullet in CURRENT. No DOCUMENTATION_LOG/DECISIONS change per `sim/AGENTS.md`.
- PR123 merged during work; branch fast-forwarded normally to `a826f6c`. Retained exact command/results and source limits in archive `receipt.json`; no rerun or tests. Documentation PR and exact-head CI pending; parent merges only after green CI.
