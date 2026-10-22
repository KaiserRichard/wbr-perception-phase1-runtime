# Five-bar prescribed-length ramp worker — 22 October 2026

- Read root/sim guidance, CURRENT/profile, accepted PR110 review and a/b handoffs. Stress-first marker confirms the measured 48 N reduced-model fall; delayed five-bar local study handoff is complete.
- Preserved i's `sim/fivebar/ramp.py`; added robust SIGINT receipt handling and six focused mechanics/profile/controller tests. Source commit `99bd24c` precedes production evidence.
- First CLI invocation: run-01, exact protocol command, stopped by SIGINT before measurement to honor source-before-rollout ordering. Partial CSV/model/schedule and supervisor `child_exit_code=-2` retained; no result claimed.
- Focused suite first exposed unequal refinement durations (one 1 ms vs one 0.5 ms step); corrected fixture to compare equal elapsed time. Final focused suite: 6/6 PASS.
- Production run-02 completed 15 s mechanics but exited 2 at JSON serialization: `full_duration` retained a NumPy `bool_`. All CSV/model/schedule outputs, traceback and supervisor receipt are preserved. Fixed by converting the duration flag to a native `bool`; regression suite now 7/7 PASS, commit pending before rerun.
- Final production CLI: pending run-03 receipt and metrics at `/Users/quockaiser/wbr-evidence-archive/sim-control-margins-20261022-01/fivebar-ramp/`.
- No model/config/gain/runtime, PPO, owner-only parity function, Pi or hardware changes.
