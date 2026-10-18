# T5 independent review

## Verdict

**APPROVE-WITH-FIXES** — confirmed defects were fixed in this worktree and the requested tests and real-data validation pass.

## Ranked findings

1. **High — failed engine execution could be reported as an accuracy PASS.** `evaluate.py` originally ignored the engine exit code, despite the README saying nonzero runs are not accuracy evidence. It now requires exit code 0; nonzero is FAIL and absent/unreadable exit evidence is BLOCKED. It reads the ticket's new per-run `exit_code.txt` and supports the saved N4A bundle's `runs.log` format. Regression tests cover missing, nonzero, and legacy evidence (`evaluate.py:38-52, 158-175`; `tests/test_accuracy.py`).
2. **High — parallel launches using different output directories could overlap.** The original lock was inside each output directory. The runner now uses a shared host lock at `${TMPDIR:-/tmp}/wbr-stereo-inertial-euroc.lock` and checks all requested run directories before writing provenance (`run_euroc.sh:10-17`).
3. **Medium — pose output could be chosen ambiguously.** A run containing both `f_*.txt` and a supported trajectory fallback was silently treated as unambiguous. All supported output names are now counted together; zero or multiple candidates block that run (`evaluate.py:32-36`). Regression test added.
4. **Medium — pose fraction above 1 could pass the minimum coverage criterion.** The evaluator now bounds the ratio using a configured `max_pose_fraction` threshold of 1.0, with a CALCULATED rationale. Regression tests cover above-bound, missing, and in-range fractions (`thresholds.json`; `evaluate.py:103-109, 187-193`).

## Verification

- `python3 -m unittest discover -s tools/eval_pipeline/accuracy/tests -v` — 10 tests passed, including real N4A saved-evidence validation. Exact output is saved in `tests/last-run.log`.
- `bash -n tools/eval_pipeline/accuracy/run_euroc.sh` — exit 0.
- Real-evidence evaluation returned `status=PASS`; SE3 ATE RMSE was 0.041461294, 0.036844344, and 0.041603883 m, reproducing the N4A report values to its precision. Updated outputs are in `validation/`.
- `git diff --check` — clean.

## Remaining open items

- The Pi runner itself was not executed, per the ticket's software-only constraints. Pi `flock`, library resolution, `vcgencmd`, storage, and engine behavior remain unverified.
- Phrase-based initialization, tracking-loss, and reset parsing can miss or overcount messages. Pose fraction is a row-count proxy and does not prove temporal coverage.
- The MH01 thresholds are PROPOSED and the saved validation is offline evidence, not a Pi gate PASS or a D435i accuracy result.
