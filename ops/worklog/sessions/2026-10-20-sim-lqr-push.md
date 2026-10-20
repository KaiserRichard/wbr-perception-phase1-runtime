# Simulation track — 2026-10-20

- Scope: assigned worktree/branch `chatgpt/20261020-sim-lqr-push`; initial HEAD
  `5b6ab4e0b5f9ceccf0a6a5eb1e9f34acc2e89876`, initially clean.
- Read root AGENTS, CURRENT, RESEARCH_RULES, USER_PROFILE, session start/end
  skills and previous simulation source inventory. No nearer AGENTS exists.
  Track instructions override shared-checkout, shared-note and merge workflows.
- No other workers, hardware commands, parity files, source gains or RL.
- Installed isolated Python 3.12 `.venv`; install log:
  `/private/tmp/wbr-conducting-20261020/sim-evidence/install.log`.
- Before first run: declared protocol v1 in `sim/configs/assumed_planar.json`:
  independent leg +8° / body −6°; 6 N world +x body-COM force at 3 s for 0.15 s
  (0.9 N s); 10 s runs; 45° fall; 1.5 m displacement bound; final 1 s within
  [0.02 m, 1°, 1°, 0.03 m/s, 0.05 rad/s, 0.05 rad/s]; recovery by 5 s;
  identical zero-control run must grow tilt 5× and fall by 5 s.
- Model: 3 coordinates / 6 states, two torque inputs, ideal rolling reduction,
  independent leg/body pitch, wheel inertia retained, wheel reaction included;
  no spring, damping, stabilizing actuator or contact stabilization.
- Documentation edit ledger: created this track session log and documented
  parameter provenance, unused upstream geometry and predeclared protocol in
  the new config. Future documentation edits are recorded here.
- Primary references read: MuJoCo 3.3.7 computation and XML reference;
  SciPy `solve_continuous_are`, `solve_discrete_are`, `cont2discrete`.
  Pinned DM-jump source inventory checked against local audit files; no code copied.
- First actual run: `.venv/bin/python -m sim.run_planar --config
  sim/configs/assumed_planar.json --out
  /private/tmp/wbr-conducting-20261020/sim-evidence/run-01` exited 0:
  BALANCE PASS (1.732 s recovery), PUSH PASS (2.714 s after pulse end),
  OPEN_LOOP PASS (unactuated fall at 0.182 s, 45.164°). No saturation or warnings.
  No tuning or threshold changes. CSV/JSON/XML/plot and hash-verified original
  source snapshot retained there; stdout in adjacent `run-01.log`.
- `.venv/bin/python -m unittest discover -s sim/tests -v`: all 11 tests passed,
  2.228 s; `sim-evidence/tests-01.log`. Covers independent nonlinear equations,
  force/actuator signs, actual MuJoCo clipping, energy, Riccati residuals,
  finite differences, dt consistency and required positive/negative controls.
- Added full environment version lock (`sim/requirements.lock`); primary
  versions: Python 3.12, MuJoCo 3.3.7, SciPy 1.15.3, NumPy 1.26.4,
  Matplotlib 3.10.3. No global installation.
- Documentation edit ledger: created `sim/README.md` with exact run/test commands,
  generated MJCF/reduction derivation, parameter provenance, primary references,
  predeclared criteria, first actual results and limits. Updated this log with
  actual outcomes and documentation changes. No shared/canonical documents edited.
- Minimal CI update: install locked simulation dependencies, explicitly discover
  `sim/tests`, run the real CLI after the existing suite.
- Preserved failures: no unexpected simulation/test failure. The deliberately
  zeroed-controller negative test fails balance and retains its trajectory in
  `/private/tmp/wbr-planar-negative-*` (platform temp-directory equivalent).
  Initial file search
  reported absent `sim/`; a Python-path glob had no match. Both were bounded
  discovery errors, not physics failures; source package was then created.
- After adding push-specific peak/final-window diagnostics,
  `.venv/bin/python .github/run_unittest.py sim/tests` again passed 11 tests,
  0 skipped, 2.131 s; `sim-evidence/tests-02.log`. Inspected generated plot.
- Final clean-commit reproduction command (artifacts and outcome to be recorded
  in the external track report after committing):
  `.venv/bin/python -m sim.run_planar --config sim/configs/assumed_planar.json
  --out /private/tmp/wbr-conducting-20261020/sim-evidence/run-final`.
- Documentation edit ledger: updated this log with repeat discovery, intentional
  negative-test evidence, exact final command and external-report destination.
  `/private/tmp/wbr-conducting-20261020/sim-report.md` is the external handoff
  document for final commit/PR/CI and exact committed-run outcomes; it will be
  created after push without modifying shared notes.
- Physical mass/COM/inertia and motor/contact data remain unknown; full fivebar,
  gain parity, hardware performance and RL remain unclaimed.
- Recommendation: conductor reviews the assumed reduction and collects CAD/lab
  parameters before fivebar VMC or RL. Leave this feature PR unmerged.
