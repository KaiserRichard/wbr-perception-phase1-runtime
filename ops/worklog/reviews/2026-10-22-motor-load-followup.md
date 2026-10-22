# Motor-load follow-up: PR123 omissions (2026-10-22)

## Saved-state workspace attribution

Read-only projection of the 30 saved, reduced-model PASS trajectories through the source-inventory five-bar geometry (`l1=l4=0.075 m`, `l2=l3=0.14 m`, `l5=0.08 m`) finds 1,940/150,030 samples outside serial-chain reach. Every excluded sample violates the A-side outer inequality, `ρA > l1+l2 = 0.215 m`; no E-side or branch-only exclusions occurred. Each affected case has one contiguous interval. The other 20 cases have zero exclusions.

| L=0.20 m scenario; seeds | Per case | Group total | First → last excluded control sample |
|---|---:|---:|---|
| `combined_target`, seeds 0–4 | 151/5,001 (3.019%) each | 755/25,005 (3.019%) | ticks 1652–1802; 3.304–3.604 s |
| `stronger_sample`, seeds 0–4 | 237/5,001 (4.739%) each | 1,185/25,005 (4.739%) | ticks 1642–1643 through 1878–1879; 3.284–3.286 through 3.756–3.758 s (seed 2 is one tick later) |

These are source-geometry workspace hits in trajectories that passed the reduced-model criteria. They do not establish the owner's physical reachability or a controller failure bound. All first/last exclusions are after the 3.000–3.150 s push pulse, not during initial recovery. Push-only causality is not supported: push amplitude, mass scale, delay and wheel-map offset co-vary (combined: 30 N, 1.5×, 6 ms, +0.167; stronger: 36 N, 2×, 8 ms, +0.5).

## Balance-only torque extrema

Across the 148,090 reachable samples, the separate global extrema are:

- `|A| = 0.40542578868132084 N·m`, `L20_stronger_sample_seed1`, tick 10 (0.020 s).
- `|E| = 0.35224760632453234 N·m`, `L12_stronger_sample_seed1`, tick 9 (0.018 s).

Both maxima occur during initial-condition recovery, before the 3 s push. These are instantaneous balance-only virtual-hip mappings; they are not simultaneous extrema or total motor loads. They exclude the unrecorded radial reaction. The earlier 1.233/1.239 N·m peaks are total A/E torques for separate upright, no-push ramps with ideal extension reaction and must not be compared as the same load quantity.

## CSV alignment and limits

`control.csv` reports canonical control time `tick*DT`. `intervals.csv` (writer variable `segments`) and `stages.csv` retain mechanical substep and Runge–Kutta stage times, with multiple rows per control tick and repeated midpoint/boundary times. Associate each interval/stage with its parent control tick **and** substep/stage role, preserving row order and endpoint ownership; do not join every row one-to-one by a single integer tick. If matching timestamps, the existing tolerance is 1 ns. Do not replace stage times with control ticks. No output-format change is made here.

Provenance: saved study `/Users/quockaiser/wbr-evidence-archive/sim-control-corners-20261022-01/combined-01/study` (simulation source `92d925ba7be174284d72ab9d7ad499d28bd8a733`); projection source geometry `f4b1a5bf15ac7f3b7803feb7119b237c402bd0f6`; prior analysis `combined-analysis-01/report-01`. Saved analysis CSV: `/Users/quockaiser/wbr-evidence-archive/sim-motor-load-followup-20261022-01/all30_balance_only.csv`. Attribution source, exact per-case data, receipt and log are in `/Users/quockaiser/wbr-evidence-archive/sim-motor-load-followup-20261022-01/review123-followup-01/`.

Reproduce the retained check from the repository root:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH="$PWD"
nice -n 10 /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python /Users/quockaiser/wbr-evidence-archive/sim-motor-load-followup-20261022-01/review123-followup-01/verify_saved.py
```

The check matched all 30 IDs, sample/reachability counts, per-case A/E peaks and 1,940 total exclusions against the saved analysis CSV; control-row times map to integer ticks within 1 ns. No radial reaction is saved, so total five-bar load remains **UNKNOWN**; source dimensions are not owner-verified geometry, masses, or CAD. Do not infer physical motor feasibility from this projection.

**Recommendation:** stop margin sweeps and datasheet comparisons until actual motor/gear IDs, assembly mass/geometry, and measured sensor-to-actuator latency are available. No new rollout, training, hardware access, model/runtime changes, or tests were performed for this documentation follow-up.

## Claude review (2026-10-22)

**Decision: accepted (PR122 already merged green).** Both requested checks are now real tests, and the limits are stated honestly.

- **Power identity: done properly.** The new test checks motor power = extension power + hip power at a state where both terms are nonzero (> 1e-3 W), and asserts that the reversed hip sign misses by > 0.1 W. That closes the "hip sign only assumed by convention" gap from the PR119/120 review. The independent residual (2.1e-11 W, reversed sign −0.14 W) agrees.
- **Integer-tick time: correct, reporting only.** `control.csv` now writes `tick*DT`; physics, profile and controller times are unchanged, and the stubbed 15-tick test proves both. Minor: `segments.csv`/`stages.csv` still write the accumulated float `t`, so a join across files by exact time can still miss by one ulp. Join by tick index, or switch those rows too in a later touch of this file.
- **The 1,940 unreachable samples (1.3%) matter more than the report says.** They mean some saved reduced-model corner states have a leg length/angle the source five-bar geometry cannot reach. The corner PASS results are therefore partly in states the real leg cannot physically take. The report should say which cases they come from (per-case counts are in the archive CSV, which I cannot see) and whether they cluster in the large-push or long-leg cases. If they do, the five-bar workspace limit, not the controller, is the first constraint those cases hit.
- **The report omits the numbers it computed.** State the peak balance-only |A| and |E| over the 148,090 reachable samples (and the case they occur in), labelled as balance-only, so the next reader does not have to open the archive.
- **Radial reaction UNKNOWN: correctly not invented.** A cheap, clearly labelled lower bound would still help later: the static leg-axis load from the assumed body weight gives a floor on A/E torque at each leg angle. Optional; do it only when real mass arrives.
- **Latency wording is right:** Pi↔MCU packet RTT is not sensor-to-actuator loop latency.

**Recommendation agreed:** stop margin sweeps and datasheet comparisons until real motor/gear IDs, assembly mass/geometry and measured loop latency exist. Separate note: `CURRENT.md` still says "Reward remains owner exercise"; the owner has since said the v3 reward is for AI to implement, so whichever task starts v3 should remove that line.
