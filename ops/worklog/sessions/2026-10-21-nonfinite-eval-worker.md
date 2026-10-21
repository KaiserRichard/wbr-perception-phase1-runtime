# Nonfinite augmented metrics — codex-g, 2026-10-21

- Scoped PR102 follow-up; base `7dda0c6`, source-only fix commit `8e189d0f334909918d6867478c1e20664fa18236`. Only evaluator and one focused test file changed in that commit; this note is separate.
- Original independent in-memory finding preserved at `/private/tmp/wbr-control-linear-review-20261021/g-protocol-review/review.md`. New synthetic fixtures reproduced `ValueError: Out of range float values are not JSON compliant` before the fix, including zero-step failures. Raw failures and intermediate fixture errors retained outside git.
- Changed only truth-derived metric serialization: nonfinite summary components become JSON null after reduction, preserving finite components. Existing numerical failure/checks, thresholds, API, field names, raw CSV failures and stopping behavior remain intact; no global JSON writer change or exception suppression.
- Five focused tests cover NaN/+Inf/−Inf in all six coordinates initially/after one or two synthetic steps, no extra step, contaminated subinterval summaries, open-loop failure, finite PASS/ordinary FAIL, and actual caller continuation with mocked dynamics/synthesis.
- **21 tests PASS in 42.190 s:** five focused tests plus all 16 existing augmented tests. Finite PASS/FAIL metrics and both CSVs matched pre-fix bytes (six artifacts). No environment/build issue; read-only venv unchanged.
- Two caller-fixture errors were fixed from actual failures: missing `input_order`, then a zero mock gain causing undefined relative gain error. Production caller was unchanged.
- Evidence: `/private/tmp/wbr-control-linear-review-20261021/g-nonfinite-fix/` (`before-fix.log`, intermediate logs, `verified-tests.log`, `finite-byte-equivalence.log`, retained fixture artifacts). Early source handoff: `/private/tmp/wbr-control-linear-review-20261021/g-nonfinite-ready.md`, written before this note/PR.
- No 400-case/domain rerun, study/evaluation/training/Pi/hardware job, delegation, account probe, shared-checkout/student edit, or merge. Caller tests are synthetic; no new controller-performance result. Conductor owns independent testing and merge after green CI.

Passing command (choose fresh evidence/log paths for any rerun):

```sh
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  TMPDIR=/private/tmp/wbr-control-linear-review-20261021/g-nonfinite-fix \
  /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python -B \
  -m unittest sim.tests.test_augmented_eval sim.tests.test_augmented -v
```

## Restricted-domain integration repair

- Confirmed original PR107 remains OPEN. Merged `origin/main` `df545e4` (PR106 already merged, head `73971db`) into this existing branch via `07b8ccc`; PR105 was still OPEN at inspection. No rebase/force push or conductor-source change.
- Actual combined-source reproduction: caller ERROR `ValueError: Legacy or incompatible schedule domain; regenerate the restricted sweep and fit without reinterpreting old coefficients`; retained at `/private/tmp/wbr-control-linear-review-20261021/g-integration-fix/before-fixture-fix.log`.
- Fixture-only source commit `fec594ebbe9e1c68375a508805d1d6c005437e60`: use real `fit_polynomial` on constant nonzero 2x10 gains at both current `DOMAIN_M` endpoints (degree zero), carrying real shape/training-grid metadata, study label and design `dt_s`. Removed polynomial mock; real loader, polynomial evaluator, pole check, caller and reporting evaluator run. Explicit synthetic/no-physics labeling retained; no production/domain-validation edit.
- **44 tests PASS in 4.062 s, exit 0:** 5 reporting + 23 gain-schedule + 16 g linear tests. Retained numerical FAIL, ordinary FAIL and later two PASS records; strict JSON, numerical flags, fitted gain/radius and `[0,2,2,2]` steps checked. Existing 16 augmented tests were already green; no local repeat needed for fixture-only changes.
- Command below ran once, sequentially with one numerical-library thread, nice 10, read-only existing venv and bytecode disabled. Log: `g-integration-fix/combined-tests.log`; synthetic artifacts: `g-integration-fix/wbr-nonfinite-eval-2ks87yrr/` under the same evidence root.
- Early handoff: `/private/tmp/wbr-control-linear-review-20261021/g-integration-ready.md` includes source/tests/PR and current CI; same PR updated by regular push. Conductor owns green-CI merge. No study batch, training, Pi, hardware, deletion, other-account/chat/delegation, student edit, shared worktree/output edit or global logging change.

```sh
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  TMPDIR=/private/tmp/wbr-control-linear-review-20261021/g-integration-fix \
  nice -n 10 /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python -B \
  -m unittest sim.tests.test_augmented_eval \
  sim.gain_schedule.tests.test_fitting sim.gain_schedule.tests.test_geometry \
  sim.gain_schedule.tests.test_poles sim.gain_schedule.tests.test_runner \
  sim.fivebar.tests.test_linearize -v
```
