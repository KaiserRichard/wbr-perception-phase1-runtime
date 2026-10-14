# D435i demo helpers — Mac offline receipt, 2026-10-14

Created [plot_run.py](plot_run.py), [DEMO_SLIDE.md](DEMO_SLIDE.md), and
[DEBUG_GUIDE.md](DEBUG_GUIDE.md). The example uses checksummed copies of the
historical N4A run1 trajectories; the original experiment was not modified.
The plot is [example_run1/demo_plot.png](example_run1/demo_plot.png), with
machine-readable results in [demo_stats.json](example_run1/demo_stats.json).

## Reproduce from the repository root

Plotting and synthetic tests used system Python
`/Library/Frameworks/Python.framework/Versions/3.11/bin/python3` (Python 3.11,
NumPy 1.26.4, Matplotlib 3.10.9). No packages were installed.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experiments/2026-10-14-d435i-demo/test_plot_run.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/2026-10-14-d435i-demo/plot_run.py \
  experiments/2026-10-14-d435i-demo/example_run1 \
  --gt experiments/2026-10-13-n4a-euroc-mh01/eval/gt_data.tum
```

An independent evo core API cross-check used the existing venv **only for evo**:

```sh
PYTHONDONTWRITEBYTECODE=1 \
  /private/tmp/claude-501/-Users-quockaiser-Desktop-Research-wbr-perception-phase1-runtime/b0d6bb0d-3154-4534-810a-f519c739918e/scratchpad/evo-venv/bin/python \
  experiments/2026-10-14-d435i-demo/crosscheck_evo.py
```

For another local result directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experiments/2026-10-14-d435i-demo/plot_run.py RUN_DIR
# Add --gt GT_TUM only when a compatible ground truth trajectory is available.
```

During this ticket, RUN_DIR must remain beneath this demo directory. Copy inputs
there before invoking the helper; its normal output location is RUN_DIR itself.
Rerunning replaces only `demo_plot.png` and `demo_stats.json`.

## Input and metric conventions

- Exactly one `f_*.txt`; optional `kf_*.txt` with the same suffix. Ambiguous pairs
  are rejected. Eight whitespace-separated columns: `timestamp_ns tx ty tz qx qy
  qz qw`; comments/blank lines allowed. Nonfinite values, zero quaternions and
  duplicate/backward trajectory timestamps are rejected, never sorted away.
- TUM GT timestamps are seconds. SE3 Umeyama fits rotation + translation with
  **scale fixed at one**; ATE is translation error. Association uses the nearest
  sample within 0.02 s from the sparser trajectory, no interpolation/time offset,
  with earlier samples winning ties. This follows evo and can reuse a denser
  sample. Stationary/collinear matches cannot constrain this alignment.
- Epoch nanoseconds are divided by `1e9`, matching historical TUM conversion.
  Multiplication by `1e-9` changes floating-point nearest-sample ties and gave
  0.041455999 m during development; the final code gives 0.041461294 m.
- Upstream frame export is rebased to the first body pose; keyframe export
  retains map coordinates. See [System.cc:689–695](../../third_party/ORB_SLAM3/src/System.cc#L689),
  [753–762](../../third_party/ORB_SLAM3/src/System.cc#L753), and
  [1098–1101](../../third_party/ORB_SLAM3/src/System.cc#L1098). The plot reconciles
  them using one shared full pose (timestamp within 1 µs), validates other shared
  positions (rejects residual >0.01 m), and records the transform/residual in JSON.
  It does not alter either input. XY/XZ are export-frame projections, not proof
  of gravity alignment; GT alignment is used for ATE only.
- Duration = last minus first exported timestamp; path length = summed adjacent
  position distances; extent = max minus min along each axis; rate = `(N-1)/span`.
  Exported pose rate is **not measured processing throughput**. Missing/lost
  frames may bias these summaries; the upstream exporters retain the largest map.
- Optional `timestamps.csv` is grouped by `(stream,index)` in acquisition order,
  preserving separate IR1/IR2. SDK timing is in seconds after ms conversion;
  host-steady diagnostics and SDK domains are also reported. Nonpositive SDK
  steps invalidate rate; mixed domains invalidate SDK rate/max gap. Single
  samples have no rate/gap. These diagnostics do not implement N1/N2/N3 gates.
- Optional power samples are discovered in one local `.log`/`.txt` containing
  UTC-prefixed `throttled=0x...` records; summary rows without UTC are ignored.
  Multiple candidate logs are rejected to avoid double counting. Fraction means
  samples with **any live bit 0–3**, plus each bit separately and under-voltage
  bit 0; historical bits 16–19 are excluded. Fractions are not time-weighted.
  No parent-directory log is silently assigned to a run. The N4A power window
  covers all three runs, so it was not copied into the run1 example.

## Observed validation

Eight synthetic tests passed ([receipt](test_results.txt)): plot/JSON generation,
keyframes, separate IR timing, reversed SDK time, mixed domains, live/history
power bits, empty optional evidence, single poses, malformed/nonfinite input,
ambiguous trajectories, nonidentity keyframe coordinate reconciliation, epoch
conversion, rigid alignment without scaling/reflection, degenerate alignment,
association and nonoverlap. These fixtures prove tooling only.

Historical run1: **3,678 poses**, **126 keyframes**, **183.850 s**, **81.524 m**
exported path length, **20.000 Hz** exported pose rate. ATE RMSE:
**0.041461294158 m** with **3,639 associations**; independent installed evo gives
the same value, matching the stored **0.041461 m** to six decimals
([cross-check receipt](evo_crosscheck.txt)). All 126 keyframes shared timestamps;
maximum position residual after coordinate reconciliation was **7.09 µm**.

Manual validation performed: viewed the saved PNG; confirmed time colorbar,
aligned keyframe marks, start/end markers, meters and equal axes in both panels.
No new D435i result, camera gate or real-time performance claim is made.

## Provenance and scope

Inspected root Git status, branch, five recent commits, ticket, N4A report and
evaluation files, N4B recorder/audit code, and local ORB-SLAM3 source before edits.
Used existing feature branch `claude/project-thread-rhsrup`, root HEAD `cf09251`;
no Git metadata was changed. Existing modified/deleted/untracked work, including
this folder's `CODEX_TICKET.md` and `codex_run.log`, was preserved.
ORB-SLAM3 source pin: `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`.
Input hashes are in example JSON; [SHA256SUMS](SHA256SUMS) covers new deliverables,
copied trajectory inputs and validation receipts, excluding caches and itself.

All deliverables and explicit file operations are beneath this directory. Scope
exception: the initial dependency probe, and the first evo import before cache
configuration, caused Matplotlib to create automatic caches in the system
temporary directory. Subsequent imports configure caches beneath this directory;
Python bytecode writes were disabled. This was an unintended violation of the
requested write boundary, not a source/evidence modification.

No SSH, network, install, commit, push, ORB-SLAM3 executable, SDK/camera process,
sensor capture or firmware/calibration action was performed. No source was built;
the Python helper requires no build step. Source citations/paper comparison were
read locally; the ≈0.036 m paper comparator remains unverified as the N4A report
states. D435i offline/live results and hardware/calibration qualification remain
**OPEN**.
