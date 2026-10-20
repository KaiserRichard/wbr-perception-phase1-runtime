# Saved-evidence reporting

Run from the repository root; standard library only. The reporting module never
imports MuJoCo, NumPy, Torch, policy code, or the owner-only gain exercise.

```sh
PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 "$PY" -m unittest discover -s sim/rl/reporting/tests -v
"$PY" -m sim.rl.reporting \
  --v1-aggregate /Users/quockaiser/wbr-evidence-archive/sim-ppo-vs-lqr-20261020-01/evaluation/aggregate.json \
  --out /private/tmp/wbr-report-NEW
# Add --v2-archive /path/to/saved-v2-archive to compare direct/residual seeds.
# Either input can also be used alone.
```

The output directory must be new and outside this repository and supplied evidence
roots. It receives `comparison.md`, `comparison.csv`, `report.json` and seven SVG
plots: strict success, survival, duration, recovery, penalized recovery, command
effort, and applied effort. Figures stay outside git. JSON/CSV retain individual
delay/scenario conditions in addition to every seed's full-panel row.

The v1 reader uses `aggregate.json`, optional adjacent `policies.json`, and the
archived `source/sim/rl/protocol.json` when present. The archived protocol supplies
rates, expected conditions and seeds; no working-tree configuration is used.
Without it, rates are unknown and expected conditions/counts come from the saved
LQR panels. v1 aggregates do not contain joint survival events: the report leaves
survival unavailable instead of inferring it from mean duration or fall counts.

The v2 reader uses `run.json`, `status.json` (or `progress.json`), each declared
arm/seed's `status.json`, and `evaluation/outcomes.json`. When outcomes are not yet
assembled, it reads only `evaluation/d*-n*.json` compact metric files. Duplicate
or unexpected episode identities fail explicitly. Training status and evaluation
coverage are separate columns. Conditional extension seeds are shown as pending,
not scheduled, or undecided according to saved status and existing seed evidence.
Smoke data has its own version label and declared smoke denominator.

Missing policies with saved failure slots retain zero success, null physical
metrics and the saved recovery penalty. Unwritten slots stay unknown. All-slot
means require complete expected coverage; available-only diagnostics retain
counts. Null recovery stays null. Effort is integrated squared total issued or
applied torque per episode, separately for wheel and hip; shorter failed episodes
have less exposure. Duration is therefore displayed alongside effort.

For example, condition durations with one observed episode averaging 2 s and
three averaging 6 s give `(1*2 + 3*6)/4 = 5 s`. Recovery means 2 s for one
episode and 4 s for one of three episodes give available-only mean 3 s over 2/4
slots; their all-slot recovery mean is null. A seed with one observed success in
four expected slots has count 1, coverage 1/4 and unknown success rate, not 25%.

The frozen LQR reference appears once. Reusing it across seeds or versions does
not create independent LQR observations. All seed rows are retained, with no
best-seed selection, pooled episode intervals, or algorithm superiority claims.
v2 learned actions are held at 100 Hz in the current declaration; plant control
and residual LQR feedback remain 500 Hz. Rates are computed from saved
declarations, never assumed. Training recipe and action rate both change between
versions, so this comparison is descriptive.

Reads are capped at 16 MiB per JSON file, 64 MiB total, and 4096 files. Traces,
NPZ, checkpoints and optimizer logs are never loaded. Running archives are
non-atomic snapshots; incomplete or concurrently changing JSON produces an
explicit error and can be reported again into a fresh output directory. The
reader does not verify archive hashes or reconstruct metrics from trajectories.
