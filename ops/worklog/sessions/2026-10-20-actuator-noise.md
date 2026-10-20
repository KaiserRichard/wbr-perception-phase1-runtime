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

- Continuation by codex-g, assigned by codex-f, starts from clean `aad5710`.
  Inspected nearest/root and ancestor AGENTS, CURRENT, owner profile, research
  rules, approved Claude review, original brief and continuation brief.
  No other workers/accounts launched.
- Retained prior runs: `fixed-20261020-01` has the serialization traceback;
  `complete-20261020-02` has 37 completed per-case JSON files, with only the 2/3 ms
  regimes in the partial phase summary; `committed-20261020-03` is empty.
  None is a completed matrix, none was overwritten, and no experiment process
  remained at inspection.
- Reproduced integer-input `lag_interval` truncation: for initial `[0,0]`,
  command `[1,-2]`, constants `[.005,0]`, dt `.002`, the first endpoint/mean
  were `0/0` instead of `0.32967995/0.17580012`. Convert all inputs to float;
  preserve the exact endpoint, mean and squared-effort equations.
- Added bounded spawned process execution to `sim/run_augmented.py`, default
  `--jobs 4`, serial `--jobs 1`. One independent runtime/output per case, ordered
  parent aggregation, full fixed-phase barrier before conditional design.
  No config, gain, noise, integration, acceptance or CSV/JSON format changes.
- Actual short execution: `/usr/bin/time -p .venv/bin/python -m unittest
  sim.tests.test_augmented.AugmentedTests.test_integer_lag_inputs_preserve_fractional_endpoint_mean_and_effort
  sim.tests.test_augmented.AugmentedTests.test_serial_and_process_cases_have_identical_artifacts`
  redirected to `/private/tmp/wbr-actuator-continuation-smoke-20261020-01.log`,
  exit 0, 2 tests, unittest 5.539 s / wall 8.30 s.
  Synthetic 40 ms two-delay/two-seed fixture compares every artifact byte in both
  controller branches at jobs 1 and 4. Its expected acceptance failures are
  retained and are not reported as ten-second protocol evidence.
- Documentation edits: appended this continuation record; added process ownership,
  phase ordering, CLI default and synthetic-test limits in `sim/augmented.md`;
  documented worker entry point and phase semantics in runner docstrings and
  synthetic/analytical regression intent in test comments. Refreshed external
  `/private/tmp/wbr-augmented-20261020/runtime-contract.md` from that API document.
  Primary references: MuJoCo 3.3.7 stateful actuator computation and Python 3.12
  `concurrent.futures.ProcessPoolExecutor`; no measured speedup claim.
