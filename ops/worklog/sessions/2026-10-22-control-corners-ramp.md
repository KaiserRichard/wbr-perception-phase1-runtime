# PR118 combined corners / ramp follow-up — 2026-10-22

- Owner assigns codex-i implementation/experiments; parent alone independently checks and merges. Dedicated branch `chatgpt/20261022-control-corners-ramp`; no other workers/accounts, training, Pi/SSH or hardware actions.
- Read root/sim AGENTS, profile/CURRENT and accepted PR118 appended review. Existing runtime/projection/API and owner gain_schedule untouched.
- Read-only old-window extraction: `/Users/quockaiser/wbr-evidence-archive/sim-control-corners-20261022-01/old-window-01/extract.py`, executed with `nice -n 10 /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python <extract.py>`; exit0. 8,001 finest true endpoint states inclusive 2..10 s: leg0.122053336°, body0.081556326°, global |x|0.0118709384m; x(10)-x(2)=-0.0118359089m, max |x-x(2)|0.0123888728m. Initial recovery remains a confound.
- Early receipt `/private/tmp/wbr-control-combined-20261022/i-ready.md` saved after extraction.
- Combined matrix declared in module/README: 2 lengths ×3 conditions ×5 seeds; exactly two fresh nominal 2ms designs, actual errors only after design. Source committed before production; run receipts to follow.
- Documentation scope: append two module READMEs, this session/review, relevant CURRENT control line only; no DOCUMENTATION_LOG/DECISIONS.
