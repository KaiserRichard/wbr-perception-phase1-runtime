# Motor-load follow-up (2026-10-22)

## Result

- Added a full combined virtual-work identity check with nonzero extension and hip power. The direct targeted suite passed 6/6. Independent conductor arithmetic: motor power `2.8753884503122746 W`, extension plus hip `2.8753884502912475 W`, residual `2.10e-11 W`; reversed hip sign residual `-0.14 W`.
- Control CSV timestamps now use canonical `tick*DT` for reporting. A stubbed 15-tick regression confirms reported timestamps and unchanged mechanical substep times; it includes float-sensitive sums that differ from canonical ticks. No physical stepping changed; old saved evidence untouched.
- Offline analysis covers all 30 saved reduced-model cases and 150,030 control samples. Under the source-inventory five-bar geometry, 148,090 samples project and 1,940 are unreachable. Per-case unreachable counts, contiguous-interval counts and longest sampled gaps are retained in the CSV; no state is clamped or dropped from counts.
- The computed A/E values are the instantaneous balance-only virtual-hip mapping at reachable samples, using each saved reduced-model virtual hip torque. This is a cross-model diagnostic, not five-bar rollout evidence or a total hardware load. The source geometry inventory is not owner CAD/BOM evidence.
- Extension radial reaction is absent from the saved trajectories (150,030/150,030 samples); total required five-bar motor load is **UNKNOWN**. No reconstruction, gravity-only force, feasibility claim, or radial reaction model was introduced. Sampled control states also do not resolve within-interval reaction peaks.

## Provenance and limitations

Inputs: `/Users/quockaiser/wbr-evidence-archive/sim-control-corners-20261022-01/combined-01/study`, source commit `92d925ba7be174284d72ab9d7ad499d28bd8a733`, analysis `combined-analysis-01`, report `report-01`. The trajectories are the reduced planar model and record no five-bar extension reaction. Source geometry is the listed inventory `l1=l4=0.075 m`, `l2=l3=0.14 m`, `l5=0.08 m`; dimensions are not verified against the owner's assembly. Conductor independently matched all 30 IDs/150,030 rows and the 1,940 exclusions using serial-chain reach inequalities; 90 finite-difference inverse-Jacobian checks agreed within 1.51e-11 N·m. The separate link-bench RTT measures Pi↔MCU packet round trip and does not establish sensor-to-actuator loop latency.

Owner confirmed these inputs are unavailable. Still missing for a physical load or feasibility assessment: identified motor and gear model/revision for each A/E joint and wheel drive; owner assembly BOM/CAD with part masses, geometry, COM and inertia; measured end-to-end sensor-sample-to-actuator-torque latency/jitter evidence. Supplier examples in the parameter-source audit do not identify the owner's BOM.

Evidence outputs and reproduction source: `/Users/quockaiser/wbr-evidence-archive/sim-motor-load-followup-20261022-01/` (`analyze_saved.py`, `all30_balance_only.csv`, `summary.json`, logs). Reproduce from the repository root:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH="$PWD"
nice -n 10 /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python /Users/quockaiser/wbr-evidence-archive/sim-motor-load-followup-20261022-01/analyze_saved.py
```

Targeted test command:

```sh
PYTHONPATH="$PWD" /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python -m unittest sim.fivebar.tests.test_ramp_panel -v
```

**Recommendation:** defer further margin sweeps and datasheet comparisons until the actual assembly and timing inputs exist. PR122 contains this software follow-up; physical-load assessment remains blocked. No rollout, training or hardware access occurred.

## Claude review (2026-10-22)

**Decision: accepted (PR122 already merged green).** Both requested checks are now real tests, and the limits are stated honestly.

- **Power identity: done properly.** The new test checks motor power = extension power + hip power at a state where both terms are nonzero (> 1e-3 W), and asserts that the reversed hip sign misses by > 0.1 W. That closes the "hip sign only assumed by convention" gap from the PR119/120 review. The independent residual (2.1e-11 W, reversed sign −0.14 W) agrees.
- **Integer-tick time: correct, reporting only.** `control.csv` now writes `tick*DT`; physics, profile and controller times are unchanged, and the stubbed 15-tick test proves both. Minor: `segments.csv`/`stages.csv` still write the accumulated float `t`, so a join across files by exact time can still miss by one ulp. Join by tick index, or switch those rows too in a later touch of this file.
- **The 1,940 unreachable samples (1.3%) matter more than the report says.** They mean some saved reduced-model corner states have a leg length/angle the source five-bar geometry cannot reach. The corner PASS results are therefore partly in states the real leg cannot physically take. The report should say which cases they come from (per-case counts are in the archive CSV, which I cannot see) and whether they cluster in the large-push or long-leg cases. If they do, the five-bar workspace limit, not the controller, is the first constraint those cases hit.
- **The report omits the numbers it computed.** State the peak balance-only |A| and |E| over the 148,090 reachable samples (and the case they occur in), labelled as balance-only, so the next reader does not have to open the archive.
- **Radial reaction UNKNOWN: correctly not invented.** A cheap, clearly labelled lower bound would still help later: the static leg-axis load from the assumed body weight gives a floor on A/E torque at each leg angle. Optional; do it only when real mass arrives.
- **Latency wording is right:** Pi↔MCU packet RTT is not sensor-to-actuator loop latency.

**Recommendation agreed:** stop margin sweeps and datasheet comparisons until real motor/gear IDs, assembly mass/geometry and measured loop latency exist. Separate note: `CURRENT.md` still says "Reward remains owner exercise"; the owner has since said the v3 reward is for AI to implement, so whichever task starts v3 should remove that line.
