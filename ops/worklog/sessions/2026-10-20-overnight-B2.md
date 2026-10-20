# Overnight B2 — deterministic policy export

- Scope: only `sim/policy_export/` and this log; assigned branch/worktree retained;
  initial git status clean, branch `chatgpt/20261020-policy-export`, base `6fbe9a3`.
  Read AGENTS, USER_PROFILE, CURRENT, RESEARCH_RULES, v2 config/runtime/encoding.
- Added completed-checkpoint SB3 exporter: frozen float64 VecNormalize arithmetic
  then float32 actor, deterministic Gaussian mean, clipping/scaling, residual caps,
  per-tick LQR composition, generated C99/header, source hashes and manifest.
  No simulator/observer/LQR synthesis or motor integration is exported.
- Actual backend: PyTorch 2.2.2, SB3 2.3.2; ONNX/ORT/onnxscript absent.
  No installs or active environment mutations; ONNX export/check/runtime parity
  explicitly PENDING, optional test skips. Isolated dependency work is queued.
- Completed direct seed-0 source read only:
  `~/wbr-evidence-archive/sim-ppo-v2-20261020-01/direct/seed-0`, status COMPLETE,
  checkpoint_reload PASS. `final.zip` SHA256:
  `a56055e3d995348e677880f5d52f59e8d64e6406dbda90f3bb39ae180a78f7cc`.
- Commands (all Python runs used OPENBLAS/OMP/VECLIB_MAXIMUM/MKL thread counts 1
  and `nice -n 10`; `PY` is the owner-specified backend Python):
  - `$PY -m sim.policy_export.export --checkpoint-dir /Users/quockaiser/wbr-evidence-archive/sim-ppo-v2-20261020-01/direct/seed-0 --out /private/tmp/wbr-overnight-20261020/B2/direct-export`
    → exit 0; actual `policy.c`, `policy.h`, `manifest.json`; no ONNX file.
  - `$PY -m sim.policy_export.validate --checkpoint-dir /Users/quockaiser/wbr-evidence-archive/sim-ppo-v2-20261020-01/direct/seed-0 --export-dir /private/tmp/wbr-overnight-20261020/B2/direct-export`
    → exit 0; 64 vectors, encoded absolute bound 1000, LQR bound 8 Nm;
    independent frozen SB3/VecNormalize reference PASS. Max errors raw/bounded
    8.9406967e-8, held/composed 1.9371510e-7 Nm; tolerance atol/rtol 3e-5.
    Host C compiled `cc -std=c99 -O2 -Wall -Wextra -Werror -ffp-contract=off -shared -fPIC ... -lm`.
  - `$PY -m unittest discover -s sim/policy_export/tests -v`
    → first run 5 tests in 6.969 s: 4 passed, 1 ONNX skipped. Covers saved tiny
    fixture direct/residual, SB3/C parity, epsilon/observation/action clipping,
    current-tick LQR change, correction/total caps, encoder, nonfinite input,
    incomplete checkpoint and unsupported activation rejection. No training.
    Final repeat after finite-parameter/feature-extractor guards: 3.011 s,
    again 4 passed and 1 ONNX skipped.
  - `git diff --check` → clean (repeated after final edits).
- README documents generated artifacts, commands, float32 composition interface,
  external 500 Hz causal LQR / held 100 Hz correction, and analytical H7 estimate:
  5184 MACs, 5314 weights+biases, 128 tanh; assumed 400 MHz/model coefficients
  give 27542–86872 cycles (68.9–217.2 us). Not measured, not a WCET bound.
- Limits: finite-vector host forward inference only; completed real residual seed
  not loaded (tiny residual fixture used); no closed-loop rollouts, STM32 build,
  hardware cycles, flash/motor commands, purchases, training or live evidence edits.
  Conductor owns central documentation/decision/morning review updates and merge.
