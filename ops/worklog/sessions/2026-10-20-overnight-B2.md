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

## ONNX follow-up (same PR63)

- Continued assigned branch at `de19ccf`, clean status. Original PENDING result
  above and `direct-export/` retained as historical; new artifacts use
  `/private/tmp/wbr-overnight-20261020/B2/direct-onnx-export`.
- Installed only six missing binary wheels into external target; no compilation,
  Torch/NumPy reinstall, active backend install, training or live evidence write.
  Exact shell setup and commands (from assigned worktree):
  ```sh
  PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
  ONNX_DEPS=/private/tmp/wbr-overnight-20261020/B2/onnx-deps
  export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1
  nice -n 10 "$PY" -m pip install --only-binary=:all: --no-deps --target "$ONNX_DEPS" onnx==1.16.2 onnxruntime==1.19.2 protobuf==5.28.3 coloredlogs==15.0.1 humanfriendly==10.0 flatbuffers==24.3.25
  CHECKPOINT=/Users/quockaiser/wbr-evidence-archive/sim-ppo-v2-20261020-01/direct/seed-0
  OUT=/private/tmp/wbr-overnight-20261020/B2/direct-onnx-export
  PYTHONPATH="$ONNX_DEPS" nice -n 10 "$PY" -m sim.policy_export.export --checkpoint-dir "$CHECKPOINT" --out "$OUT"
  PYTHONPATH="$ONNX_DEPS" nice -n 10 "$PY" -m sim.policy_export.validate --checkpoint-dir "$CHECKPOINT" --export-dir "$OUT"
  PYTHONPATH="$ONNX_DEPS" nice -n 10 "$PY" -m unittest discover -s sim/policy_export/tests -v
  ```
- All commands exit 0. Legacy Torch 2.2.2 exporter needs no onnxscript. Import
  paths confirm NumPy1.26.4/Torch2.2.2 reused from backend; ONNX/ORT from target.
  Existing packaging26.3/sympy1.14.0 reused. Without scoped PYTHONPATH,
  `find_spec` still returns None for onnx/onnxruntime/onnxscript.
- Actual `policy.onnx`: 23609 bytes; SHA256
  `c119b8d7ceae28026c8ab29dc449dddb72abd23a83383a26f60d87a438f8ac5a`.
  Export and validator both run `onnx.checker.check_model`: PASS. Source
  checkpoint hash unchanged from initial run; normalization frozen.
- Extended validator: independent SB3 normalization/action-composition reference,
  both observation-clipping boundaries, ONNX output shapes/dtypes/finite checks,
  explicit ONNX/PyTorch and ONNX/C errors, dynamic batches 64 and 1, single-thread
  CPUExecutionProvider. Real directseed0 bounded parity PASS, atol/rtol3e-5:
  encoded absolute bound1000, LQR bound8Nm; max ONNX/PyTorch action8.94e-8,
  torque1.78814e-7Nm; ONNX/C action5.96e-8, torque1.19209e-7Nm;
  C/PyTorch action8.94e-8, torque1.78814e-7Nm. See new `parity.json`.
- Updated optional test loads saved tiny direct/residual fixtures and asserts
  actual graph/checker/runtime/C parity and both batch sizes. Original optional
  suite ran 5/5 in4.630s; final extended suite 5/5 in4.989s, **zero skips**.
  No full suite or simulator rollouts. `git diff --check` clean.
- README now records reproducible isolated commands and actual ONNX evidence;
  historical no-ONNX result is retained above. H7 estimate remains analytical,
  not measured. Real residual checkpoint, target compilation, timing and
  closed-loop/hardware validation remain outside this task; fixture residual
  inference is tested. No heavy dependency work remains for B2.
