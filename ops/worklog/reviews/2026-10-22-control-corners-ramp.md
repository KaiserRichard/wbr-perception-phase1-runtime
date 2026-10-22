# PR118 follow-up: combined corners and upright ramps — 22 October 2026

**Status: results validated; PR119 open.** Sources: combined `92d925b`, ramp `6a78f4b`, reporting fix `fdfcb81`. Conductor checks and PR120 found no unresolved material disagreement. Runtime/API, model, hardware and owner gain schedule unchanged.

## Measurements

- Old accepted ramp, read-only extraction of 8,001 finest true endpoints in inclusive 2–10 s: leg/body peaks **0.122053°/0.081556°**; global |x| peak **11.871 mm**; x(10)−x(2) **−11.836 mm**; max |x−x(2)| **12.389 mm**. The original +8/−6° initial recovery remains a confound.
- Combined panel: **30/30 strict PASS**, 10 s each, 0 scientific FAIL/0 execution ERROR. Two nominal 2 ms augmented DARE designs at L=.12/.20 m stayed fixed across all conditions/seeds. The original initial state, push, noise, caps and criteria were unchanged; no retuning. All five seed pairings cover 5,001 common ticks; noise is bit-identical per tick and maximum timestamp error from nominal ticks is 1.001e−12 s (tolerance 1 ns).
- The original combined command exited 1 after all 30 physical cases passed: its report compared MuJoCo timestamps bit-for-bit (`.028` vs `.027999999999999997` s) although sensor noise matched. Commit `fdfcb81` pairs noise by control tick and retains the evaluator's 1 ns time tolerance. Fresh `--summarize-existing` recovery exited 0 with **zero new rollouts/designs**; the original exit and artifacts are preserved.
- Upright ramp panel: **12/12 strict PASS**, 0 FAIL/0 ERROR, all duration and per-case checks passed. Two directions × 8/2/1 s quintics × scheduled/frozen-at-initial-length, seed 0; scheduled/frozen noise matched at every shared sensor timestamp (4,001–7,501 samples per pair). Moving-window peaks and displacement are in the table below; these small paired differences do not establish a scheduling benefit or necessity.

| Direction / duration | Scheduled leg/body (°) | Frozen leg/body (°) | Maximum change in x (mm), scheduled/frozen |
|---|---:|---:|---:|
| Extend / 8 s | .00955/.03505 | .00985/.03510 | .2288/.2205 |
| Extend / 2 s | .00562/.03013 | .00555/.03017 | .1816/.1736 |
| Extend / 1 s | .00501/.02999 | .00527/.03022 | .1086/.1023 |
| Retract / 8 s | .01041/.03498 | .01012/.03493 | .1948/.2026 |
| Retract / 2 s | .00552/.02934 | .00590/.02933 | .1583/.1635 |
| Retract / 1 s | .00481/.02944 | .00537/.02935 | .0912/.0955 |

The 20 ms moving/nonzero-torque refinement is a local numerical check, not full-trajectory accuracy. Required motor A/E torque includes same-stage ideal extension reaction plus balance moment; peaks were 1.233/1.239 Nm. **Real motor, gear and current limits and feasibility remain UNKNOWN.** The virtual hip-pair 4 Nm cap is not an individual-motor limit.

## Evidence and commands

Archive: `/Users/quockaiser/wbr-evidence-archive/sim-control-corners-20261022-01/`.

- Old window: `old-window-01/{extract.py,window.json,endpoints.csv}`.
- Combined original: `combined-01/study/` (30 cases and original exit); reporting-only recovery and all five pairings: `combined-analysis-01/analysis/summary.json`.
- Ramp: `ramp-01/study/summary.json`, per-case traces; refinement `ramp-01/tmpskrrycv4/refinement.json`.
- Report indices, exact production commands and original focused-suite receipts remain in the session log/archive. Both supervisor commands exited 0; one serial numerical process/thread, inherited niceness 20 retained.

- Conductor targeted regressions: combined noise-pair time-tolerance/rejection and ramp extension virtual-work/unchanged-dynamics tests both PASS; log `conductor-checks/targeted.log`. The 2–10 s old-window values were independently recomputed in `conductor-old-window.json`.
- Independent validation in open PR120: all 30 combined, 12 ramp, and 36 window results; one 10 s byte-exact replay; and motor conversion. No unresolved material disagreement.

These bounded assumed-model samples are not robustness bounds or hardware validation, and do not show scheduled gains improve control. The worker generated the report; the conductor owns review and merge after exact-head green CI.

**Recommendation:** Keep the sample and model boundaries explicit: the paired ramp does not establish a scheduling benefit, and motor feasibility remains UNKNOWN.

**Claude:** PR119 results validated; PR120 checked 30/12/36 windows, exact replay and motor conversion. Both PRs OPEN; hardware feasibility UNKNOWN.

## Claude review (2026-10-22)

**Decision: accepted (PR119 and PR120).** Read: this file, the independent review,
the session log, both README additions and `Plant.controls`
(`sim/fivebar/model.py:156`). Archives not re-read.

### Timestamp recovery: sound

- The exit 1 was a reporting false alarm. Different delays split integration
  intervals at different points, so accumulated MuJoCo time differs in the last
  bit (`.028` vs `.027999999999999997`). Pairing by control-tick index, with
  bit-identical noise and the evaluator's existing 1 ns tolerance, is the right
  test. The recovery ran no physics and kept the original exit and artifacts.
- Suggestion (non-blocking): derive reported time as `tick * dt` from an integer
  counter, rather than accumulating floats, so this class of mismatch cannot
  recur.

### Assumed motor-load mapping: consistent, one check to add

- `τ = Jᵀ[F_ext, −T_h]` with `β = θ − φ + π/2` matches the documented convention
  (hip moment does work `T_h(φ̇ − θ̇)`). The extension part is verified by the
  power identity (residual ≤ 9.45e−10 W), and an independent geometry rebuild
  matches all 512,000 stage records.
- Add (one-line test): check the **full** power identity
  `τᵀȧ = F_ext·L̇ + T_h·(φ̇ − θ̇)`, so the hip term's sign is covered by the same
  check, not only by convention.
- Peaks of 1.23/1.24 N·m per motor (|A|+|E| ≤ 2.45 N·m) are for **upright ramps
  with no push**. The push and combined-corner cases will need more torque.
  Compute the same motor A/E torques for the 30 corner cases before comparing
  with any motor datasheet. Feasibility stays UNKNOWN, as stated.

### What the ramp panel actually shows

- Starting upright removes the old confound. Peaks are 0.005–0.010° (leg) and
  ≤ 0.23 mm (x) for all ramp speeds up to 0.15 m/s, and the faster ramps have
  *smaller* moving-window peaks. That pattern means the windows are dominated by
  sensor noise: the ramp disturbance is below the noise floor.
- Scheduled versus frozen differ by < 0.0006°. In this model, over 0.12–0.20 m,
  one fixed gain is enough. That is a useful, model-bounded finding. The report
  correctly says scheduling *benefit* is not shown; it is fair to also say no
  *need* for scheduling was observed here.

### Combined corners

30/30 strict PASS, including the stronger sample (8 ms, 2× mass, δ 0.5, 36 N) at
both endpoint lengths, with two frozen nominal designs. Again no failure, so the
combined margin is still not located. That is fine for now; there is no reason
to push this axis further before hardware numbers exist.

**Next useful step is not more simulation margin** but real parameters: motor
and gear datasheet limits, measured mass and leg geometry, and measured loop
delay from the STM32 link test.
