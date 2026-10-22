# PR118 follow-up: combined corners and upright ramps — 22 October 2026

**Status: complete for diff review; PR119, no merge.** Sources: combined `92d925b`, ramp `6a78f4b`, reporting fix `fdfcb81`. No accepted runtime/API, model, hardware or owner gain schedule changed.

## Measurements

- Old accepted ramp, read-only extraction of 8,001 finest true endpoints in inclusive 2–10 s: leg/body peaks **0.122053°/0.081556°**; global |x| peak **11.871 mm**; x(10)−x(2) **−11.836 mm**; max |x−x(2)| **12.389 mm**. The original +8/−6° initial recovery remains a confound.
- Combined panel: **30/30 strict PASS**, 10 s each, 0 scientific FAIL/0 execution ERROR. Two nominal 2 ms augmented DARE designs at L=.12/.20 m stayed fixed across all conditions/seeds. The original initial state, push, noise, caps and criteria were unchanged; no retuning. All five seed pairings cover 5,001 common ticks; noise is bit-identical per tick and maximum timestamp error from nominal ticks is 1.001e−12 s (tolerance 1 ns).
- The original combined command exited 1 after all 30 physical cases passed: its report compared MuJoCo timestamps bit-for-bit (`.028` vs `.027999999999999997` s) although sensor noise matched. Commit `fdfcb81` pairs noise by control tick and retains the evaluator's 1 ns time tolerance. Fresh `--summarize-existing` recovery exited 0 with **zero new rollouts/designs**; the original exit and artifacts are preserved.
- Upright ramp panel: **12/12 strict PASS**, 0 FAIL/0 ERROR, all duration and per-case checks passed. Two directions × 8/2/1 s quintics × scheduled/frozen-at-initial-length, seed 0; scheduled/frozen noise matched at every shared sensor timestamp (4,001–7,501 samples per pair). Moving-window peaks and displacement are in the table below; these small paired differences do not establish a scheduling benefit or necessity.

| Direction / duration | Scheduled leg/body (°) | Frozen leg/body (°) | Scheduled/frozen max |x−x(start)| (mm) |
|---|---:|---:|---:|
| Extend / 8 s | .00955/.03505 | .00985/.03510 | .2288/.2205 |
| Extend / 2 s | .00562/.03013 | .00555/.03017 | .1816/.1736 |
| Extend / 1 s | .00501/.02999 | .00527/.03022 | .1086/.1023 |
| Retract / 8 s | .01041/.03498 | .01012/.03493 | .1948/.2026 |
| Retract / 2 s | .00552/.02934 | .00590/.02933 | .1583/.1635 |
| Retract / 1 s | .00481/.02944 | .00537/.02935 | .0912/.0955 |

The targeted 20 ms moving/nonzero-torque refinement compared h=1/.5/.25 ms and projection epsilon 1e−6/5e−7; it is a local numerical check, not full-trajectory accuracy. Required motor A/E torque includes same-stage ideal extension reaction plus balance moment; largest sampled magnitudes were 1.233/1.239 Nm. **Real motor, gear and current limits and feasibility remain UNKNOWN.** The virtual hip-pair 4 Nm cap is not an individual-motor limit. No statistical generalization is supported by the ramp's single seed.

## Evidence and commands

Archive: `/Users/quockaiser/wbr-evidence-archive/sim-control-corners-20261022-01/`.

- Old window: `old-window-01/{extract.py,window.json,endpoints.csv}`.
- Combined original: `combined-01/study/` (30 cases and original exit); reporting-only recovery and all five pairings: `combined-analysis-01/analysis/summary.json`.
- Ramp: `ramp-01/study/summary.json`, per-case traces; refinement `ramp-01/tmpskrrycv4/refinement.json`.
- Compact report/index: `report-01/{combined-per-seed.csv,ramp-true-endpoint-windows.csv,paired-sensor-window-comparisons.json,required-motor-peaks.csv,ramp-table.md,report-receipt.json}`. Supervisor plans, logs and real exits are retained beside each run.
- Exact production commands: `python -m sim.gain_schedule.combined --out <freshdir>` and `python -m sim.fivebar.ramp_panel --schedule /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study/fit-01/schedule.json --out <freshdir>`. Final recovery: `python -m sim.gain_schedule.combined --out <freshdir> --summarize-existing <combined-01/study>`.
- Focused suites on the read-only venv: `python -m unittest sim.gain_schedule.tests.test_combined -v` (**4 passed**) and `python -m unittest sim.fivebar.tests.test_ramp_panel -v` (**5 passed**). Both supervisor commands exited 0. One serial numerical process/thread; inherited niceness 20 was retained without restart.

These are bounded assumed-model samples, not robustness bounds, hardware validation or a claim that scheduled gains improve control. The report is worker-generated; the conductor owns independent review and merge after exact-head green CI.

**Claude handoff:** Review PR119 and this measured evidence; assess whether the timestamp recovery and torque mapping are sound while retaining the UNKNOWN hardware-feasibility boundary.
