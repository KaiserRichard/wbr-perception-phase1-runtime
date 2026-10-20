# Overnight A2 — plain C delay-aware LQR

- Assigned worktree/branch: `sim-lqr-push/wbr-lab-ops`,
  `chatgpt/20261020-lqr-c`; initial status clean, initial HEAD `6fbe9a3`.
  Read AGENTS, USER_PROFILE, CURRENT, RESEARCH_RULES and controller/runtime/config.
- Added `sim/control_c/`: C99 fixed-state controller, existing per-delay archived
  gains, 2/4 N m clipping, 5 ms torque filter, newest-first clipped history.
  Fractional 3/5 ms arrivals split into exact 1 ms intervals; feedback precedes
  prediction/history insertion. Reset removes torque and pending history.
- Source: read-only `~/wbr-evidence-archive/sim-actuator-20261020-01`.
  Extracted 64 archived seed-0 balance ticks per delay; recorded 14 synthetic
  Python-runtime ticks per delay for saturation/reset (256 + 56 total).
  No gain synthesis, long simulation, training, environment mutation or hardware.
- Fixture command: single-thread BLAS/OMP, `PYTHONDONTWRITEBYTECODE=1`, `nice -n 10`,
  assigned backend Python `-m sim.control_c.record_fixtures --archive
  /Users/quockaiser/wbr-evidence-archive/sim-actuator-20261020-01`.
  Result: four profiles, 256 archived ticks, 56 synthetic ticks.
- First C build/run: `cc -std=c99 -O2 -Wall -Wextra -Werror -pedantic
  -ffp-contract=off sim/control_c/wbr_lqr.c sim/control_c/tests/host.c -lm
  -o sim/control_c/.build/host`; `sim/control_c/.build/host --unit` passed.
- Done command (same single-thread environment and niceness):
  `/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
  -m unittest discover -s sim/control_c/tests -v`.
  **6/6 passed, 0.633 s**; recorded max absolute error `1.8596235662471372e-15`
  against required `1e-6`; independent analytical max `4.440892098500626e-16`.
  Build/report: `sim/control_c/.build/parity-1kx6aknf/`; no failed build/tests.
- Tests cover requested/clipped commands, before/after torque and full history,
  exact 2/3/4/5 ms arrivals, both saturation signs/channels, pending and nonzero
  torque resets, repeated reads, separate instances, invalid input atomicity.
- Documentation: added `sim/control_c/README.md` describing API, timing derivation,
  worked 5 ms example, binary64 precision, commands and scope. This session log
  is the only worklog changed; conductor owns central documentation/decisions.
- Limitations: recorded-input controller parity only; no new closed-loop plant
  acceptance, float32/fixed-point validation, STM32 build/deployment, hardware
  timing or motor action. Heavy pending: none for the assigned bounded task.
- Publication: task PR to main, no merge; URL and final commit are recorded in
  `/private/tmp/wbr-overnight-20261020/A2/result.json`.
