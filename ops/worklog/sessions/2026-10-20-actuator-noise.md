# Actuator delay, torque lag, and body IMU noise worker — 2026-10-20

- Assigned worktree `sim-lqr-push/wbr-lab-ops`, branch
  `chatgpt/20261020-actuator-noise`; clean start at `417c1e2`.
- Read root/ancestor AGENTS, CURRENT, owner profile, research rules and approved
  Claude review. Worker scope overrides generic conductor merge/shared-log rules.
  No other workers launched; no hardware/shared checkout/learner exercise edits.
- Before implementation: ran `.venv/bin/python -m sim.run_planar --config
  sim/configs/assumed_planar.json --out
  /private/tmp/wbr-actuator-nominal-before-20261020-01`, exit 0.
  Balance recovery 1.732 s, push 2.714 s, zero-control fall 0.182 s.
- Predeclared `sim/configs/assumed_actuator_noise.json` before any augmented run:
  unchanged referenced/hash-locked nominal config, exact delays 2/3/4/5 ms,
  seeds 0..4, same three 10 s protocols/thresholds, 5 ms pair torque constants,
  body-only 0.1 degree / 0.01 rad/s independent zero-bias noise. All ASSUMED.
- Froze `synthesize(Plant(base_cfg))` K, verified exact array equality against
  `~/wbr-evidence-archive/sim-lqr-20261020-01/conductor/linearization.json`.
  Little-endian float64 K SHA256
  `fd1c16dccb418a4949caffcab67fc8e4c4f16d22ec19e7929bbd04acceda5acf`.
- Runtime mechanism: exact command arrival events, exact first-order lag endpoint
  and mean; MuJoCo RK4 holds that mean on <=0.25 ms substeps. Coupled mechanics
  are a numerical approximation, to be checked by convergence.
- Primary references consulted: MuJoCo 3.3.7 computation/stateful actuator
  documentation and SciPy solve_discrete_are documentation. No hardware parameter
  inference from these references.
- Documentation edits recorded here: created this session log and the explanatory
  provenance/protocol/API docstrings in augmented config/runtime.
- First augmented command: `.venv/bin/python -m sim.run_augmented --config
  sim/configs/assumed_actuator_noise.json --out
  /private/tmp/wbr-actuator-fixed-20261020-01`, log
  `/private/tmp/wbr-actuator-fixed-20261020-01.log`, exit 1.
  The 2 ms / seed 0 balance and push cases failed unchanged settling/recovery
  checks; their CSV/JSON remain. This observed failure authorized conditional
  augmented design. Open-loop artifact serialization then failed:
  `TypeError: Object of type bool_ is not JSON serializable`. Fixed by converting
  acceptance-check values to Python bool; no criteria changes. Failed directory
  retained unchanged.
- Initial actual-runtime checks: bitwise zero-effects nominal equivalence for 10
  steps; exact analytical lag/causality at 2/3/5 ms, all passed, exit 0.
- Documentation: created `sim/augmented.md` with API, equations, primary sources,
  assumed/ideal sensor distinctions, integration limits and experiment semantics.
  Published its API contract and source paths immediately to
  `/private/tmp/wbr-augmented-20261020/runtime-contract.md`.
- Added conditional augmented DARE only after the observed fixed-gain failure;
  unchanged six-state Q and command R; actual runtime transition differentiation.
- Tests command `.venv/bin/python .github/run_unittest.py sim/tests`, exit 0:
  25/25 passed, zero skips, including all original 11 tests (51.719 s).
  Log `/private/tmp/wbr-actuator-tests-20261020-01.log`.
  New checks cover exact timing, analytical lag/effort, seeded cached body-only
  noise/statistics, caps, causal reconstruction, bitwise zero-effect regression,
  pulse impulse, mechanical refinement, actual-history linearization replay,
  Riccati/pole/prediction checks and failed-frozen/successful-augmented integration.
- Conditional synthesis smoke run (all delays), exit 0: state dimensions
  10/12/12/14, full controllability rank, maximum pole modulus about 0.997543901;
  DARE relative residuals 5.58e-13, 1.91e-12, 3.98e-13, 2.83e-12.
- Documentation: added the extension link in `sim/README.md`; documented the
  conditional synthesis and behavioral tests through their module docstrings.
  Shared CURRENT/DECISIONS/DOCUMENTATION_LOG and review files remain untouched.
