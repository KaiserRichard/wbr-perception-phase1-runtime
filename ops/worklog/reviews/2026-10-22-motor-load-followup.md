# Motor-load follow-up (2026-10-22)

## Result

- Added a full combined virtual-work identity check with nonzero extension and hip power. The direct targeted suite passed 6/6. Independent conductor arithmetic: motor power `2.8753884503122746 W`, extension plus hip `2.8753884502912475 W`, residual `2.10e-11 W`; reversed hip sign residual `-0.14 W`.
- Control CSV timestamps now use canonical `tick*DT` for reporting. A stubbed 15-tick regression confirms reported timestamps and unchanged mechanical substep times; it includes float-sensitive sums that differ from canonical ticks. No physical stepping changed; old saved evidence untouched.
- Offline analysis covers all 30 saved reduced-model cases and 150,030 control samples. Under the source-inventory five-bar geometry, 148,090 samples project and 1,940 are unreachable. Per-case unreachable counts and contiguous intervals are retained in the CSV; no state is clamped or dropped from counts.
- The computed A/E values are the instantaneous balance-only virtual-hip mapping at reachable samples, using each saved reduced-model virtual hip torque. This is a cross-model diagnostic, not five-bar rollout evidence or a total hardware load. The source geometry inventory is not owner CAD/BOM evidence.
- Extension radial reaction is absent from the saved trajectories (150,030/150,030 samples); total required five-bar motor load is **UNKNOWN**. No reconstruction, gravity-only force, feasibility claim, or radial reaction model was introduced. Sampled control states also do not resolve within-interval reaction peaks.

## Provenance and limitations

Inputs: `/Users/quockaiser/wbr-evidence-archive/sim-control-corners-20261022-01/combined-01/study`, source commit `92d925ba7be174284d72ab9d7ad499d28bd8a733`, analysis `combined-analysis-01`, report `report-01`. The trajectories are the reduced planar model and record no five-bar extension reaction. Source geometry is the listed inventory `l1=l4=0.075 m`, `l2=l3=0.14 m`, `l5=0.08 m`; dimensions are not verified against the owner's assembly. The separate link-bench RTT measures Pi↔MCU packet round trip and does not establish sensor-to-actuator loop latency.

Still missing for a physical load or feasibility assessment: identified motor and gear model/revision for each A/E joint and wheel drive; owner assembly BOM/CAD with part masses, geometry, COM and inertia; measured end-to-end sensor-sample-to-actuator-torque latency/jitter evidence. Supplier examples in the parameter-source audit do not identify the owner's BOM.

Evidence outputs and reproduction source: `/Users/quockaiser/wbr-evidence-archive/sim-motor-load-followup-20261022-01/` (`analyze_saved.py`, `all30_balance_only.csv`, `summary.json`, logs). Reproduce from the repository root:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH="$PWD"
nice -n 10 /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python /Users/quockaiser/wbr-evidence-archive/sim-motor-load-followup-20261022-01/analyze_saved.py
```

Targeted test command:

```sh
PYTHONPATH="$PWD" /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python -m unittest sim.fivebar.tests.test_ramp_panel -v
```

No full simulation, training, hardware access, or raw-data copy was performed. Claude review requested for this completed software/evidence milestone; physical load remains unknown.
