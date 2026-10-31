# G1 bounded velocity-reference governor

Implements [PLAN-v2](../../../research/rl/PLAN-v2.md): CPU Stable-Baselines3 PPO
at100Hz, above the shared fixed500Hz delay-aware LQR on a separate **ASSUMED**
planar candidate. Source, model, case lists and baseline are frozen before
learning. No old checkpoints/results/gains are reused. The manifest's unresolved
assembly provenance blocks scientific release; this implementation supports
simulation plumbing and timing measurements now.

From the repository root, with the project's Python and RL requirements installed:

```sh
PY=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
"$PY" -m unittest discover -s sim/rl/g1/tests -v
"$PY" -m sim.rl.g1.runner smoke --out /absolute/new/g1-smoke
"$PY" -m sim.rl.g1.training --out /absolute/new/seed-0 --seed 0
"$PY" -m sim.rl.g1.training --out /absolute/new/seed-0 --seed 0 --resume
"$PY" -m sim.rl.g1.evaluation --development --out /absolute/new/development-lqr.json
"$PY" -m sim.rl.g1.evaluation --development --run /absolute/new/seed-0 --out /absolute/new/development-policy.json
"$PY" -m sim.rl.g1.evaluation --seeds-root /absolute/g1-run --out /absolute/g1-run/final --jobs 5
```

The direct training command is a component interface; the scientific queue is:

```sh
"$PY" -m sim.rl.g1.runner run --out /absolute/g1-run --jobs 5
```

For a split run, pass `--seeds 0,1,2` on one host and `--seeds 3,4` on the
other, with separate output roots and identical source. Each subset retains
all gates and writes `run-manifest.json`, the standard `seed-N/` folders and
`part-complete.json`, then stops before final evaluation. Merge completed parts
with `python -m sim.rl.g1.merge_runs --parts /part-a /part-b --out /new/merged`,
then evaluate with `--seeds-root /new/merged`. The merger checks code/config
identity, checkpoint integrity and complete unique seed coverage. See the
[Kaggle + Colab split workflow](cloud/CLOUD_README.md) for defaults, recovery,
and final evaluation on Mac or Kaggle.

It runs smoke first, checks the optional runtime cap and host readiness, runs the
20-case development LQR/headroom check and the single20min seed42 pilot, then
trains fresh seeds0–4 in parallel to exactly1M completed transitions each. A failed
pilot or numerical failure stops the queue. Five finals total5M actions; no
smoke/pilot weights enter them. Seed wall time is **unlimited by default**.
`--seed-wall-cap-min 90` restores the old café-session cap when requested;
the finite positive cap counts cumulative training wall time across resumes.
A capped unfinished seed stays PARTIAL with verified checkpoints. `--seconds`
on the training component is a separate optional segment bound for smoke/timing.
The old515min training/635min export timers no longer constrain the queue.
Cloud notebooks enforce their own global session soft stop and export artifacts.
The60s update watchdog,300s checkpoints and120min evaluation bound remain.

`host-readiness.json` in that run directory must contain evidence paths plus
true values for `report_assembly_resolved`, `windows_smoke_passed`,
`offline_bundle_verified`, and `host_and_usb_permitted`. These represent the
existing PLAN-v2 prerequisites, not new experimental choices. The current source
cannot substantiate them. Merely setting a flag does not resolve provenance.
`research/rl/bundle/run.bat` uses this queue; it no longer launches PPO v2.
`resume.bat` resumes the newest G1 queue and rejects changed source/model/config.
An interrupted pilot remains explicit and is not silently restarted.

`--jobs N` controls concurrent seeds and evaluation case workers (runner and
evaluation CLI). The default is `max(1, min(5, (os.cpu_count() or 1)//2))`;
`--jobs 1` retains serial execution. Processes use spawn, not fork. Each seed
owns its RNGs, normalizer, optimizer, logs and checkpoints. Parallel seeds advance
their eight environments locally with `DummyVecEnv`, avoiding forty extra IPC
workers; the serial path retains `SubprocVecEnv`. Environment ranks, sample
ordering and PPO batches are identical. A worker failure cancels pending jobs
and requests sibling STOP files, saving their last complete update/checkpoint.
Cases are partitioned into contiguous chunks; results are assembled in frozen
case order before computing strata or paired comparisons. No scientific recipe,
case, metric or threshold changes with `--jobs`.

Both paths set `torch.set_num_threads(1)` and OMP/OPENBLAS/MKL (plus macOS
VECLIB/NUMEXPR) thread environment variables to1 before worker imports. The
parallel regression test compares exact policy tensors, observation normalizers,
sampler/torch RNG states, optimizer loss logs, every scientific case metric and
stratum against serial execution. Wall-clock, CPU and inference timing receipts
remain actual measurements; these fields are necessarily different across runs.

Mac overnight command, from the repository root after installing the RL
requirements and preparing a run folder with the documented readiness evidence:

```sh
bash sim/rl/g1/run_mac.sh --out "$PWD/runs/g1-overnight" --jobs 5 > "$PWD/g1-overnight.log" 2>&1
```

On the measured Mac, the project venv uses G1-CODE's existing dependency overlay;
the Mac launcher above activates it when present and forwards all runner options,
including `--seed-wall-cap-min MINUTES` (omit for unlimited). Set `G1_PYTHON`
and `G1_ENV_FILE` to select another interpreter/overlay. For other examples source that file first. This
temporary overlay must still exist, or the same RL dependencies must be installed
in the selected Python. No environment/package changes were made for G1-PAR.

This runs smoke → development baseline → seed42 pilot → five fresh1M finals →
all1200 paired evaluation cases. Existing readiness/pilot/timing gates still
apply; the command stops if any fails. Windows: `run.bat --jobs 5` (or omit the
option for the default), and `resume.bat --jobs 5` resumes the same queue. Both
accept `--seed-wall-cap-min MINUTES`; omission means unlimited, including resume.

Reproduce the separate, development-only throughput measurement (fresh folder):

```sh
"$PY" -u -m sim.rl.g1.runner benchmark --jobs 5 --seconds 120 --out /absolute/new/g1-par-benchmark
```

It warms all five seeds through a completed update, then measures one shared120s
window. Only completed optimizer updates count; startup, end-to-end throughput,
and final checkpoint/drain time are reported separately in `benchmark.json`.
These partial timing runs count as neither scientific pilots nor final policies.

`config.json` freezes8 environments×250 steps, batch250,10 epochs,
two64-unit tanh layers, actor mean0/SD0.05, Adam3e-4, gamma0.99, GAE0.95,
clip0.2. BLAS and PyTorch each use one thread. No reward normalization/clipping
or best-checkpoint selection. `smoke.json` defines the600s development smoke.
`cases.json` enumerates all20 development and200 final cases before learning;
final noise seeds3000–3199 are shared across all controllers/training seeds.

The action is scalar a∈[-1,1]. Proposed delta=0.03a m/s passes magnitude, delta
slew≤0.1m/s² and accepted speed≤0.2m/s constraints. Position references and
scoring always follow the original command ramp. See [DECISIONS](DECISIONS.md)
for ambiguity resolutions, exact25-dimensional observation order/scaling,
reward sampling, causal predictor and the assumptions behind failed-window E.
The fixed inner LQR and plant implementations are unchanged outside this package;
owner-only `sim/parity/student.py::gain_schedule` is untouched.

Each seed writes `declaration.json`, per-episode return/length, every reward-term
sum, action mean/SD, precision/strict/recovery in `episodes.jsonl`, optimizer CSV,
`walltime-100k.jsonl`, wall-clock/CPU receipts and verified versioned checkpoints.
The runner writes `learning-curves.png`. Wall seconds/100k and sustainable
transitions/s include completed updates and checkpoint writes/reload. A60s hard
rollout/update watchdog preserves the previous complete checkpoint on a hang.
Counters in checkpoints always refer to completed optimizer updates. Simulator
state resets on resume; the RNG/sampler/normalizer/optimizer state survives.

Final evaluation requires five correctly seeded1M checkpoints, uses the exact200
cases, and reports every seed/stratum, failed counts, survival, strict, precision,
recovery, effort, caps/saturation, torque/request slew and inference time. The
primary interval uses five paired seed differences, df4. Numerical failure
invalidates the result; no partial-budget result can become a final PASS.
Traces can be retained through `evaluation.evaluate(..., trace=directory)`.

Laptop timing is **ESTIMATED** from measured Mac throughput divided by1.3.
The smoke retains its historical185.2 transitions/s café-budget diagnostic.
It blocks training only when a configured seed cap cannot fit1M transitions at
the measured rate; an unlimited run ignores that historical diagnostic.
Updates must still fit60s; projected paired evaluation must fit120min. Provenance, actual Windows offline
startup/USB/resume, the scientific pilot and all other PLAN-v2 boxes also gate GO.
A successful Mac smoke establishes none of those unmeasured claims.

Measured Mac smoke (2026-10-31):600.0047s total,170,000 completed transitions in
501.7969 training wall seconds,338.7825 transitions/s, max update12.5928s;
74k→170k after fresh-directory restore, zero-action parity PASS. All13 unit tests
pass, including a comparison-validity correction after smoke that does not run
in the training/smoke path. The original source hashes and one-line delta are
retained in [evidence](../../../ops/worklog/evidence/2026-10-31-g1-smoke/receipt.json).
Historical serial ESTIMATE at1.3× wall:5.33h five-seed training and6.19h paired evaluation;
the latter exceeds120min. **Laptop NO-GO.** No final policies/pilot claims.

G1-PAR measurement (2026-10-31, Mac8 cores/16 logical CPUs, torch2.2.2,
NumPy1.26.4, SB3 2.3.2): five single-thread training processes, unchanged8×250
recipe. After34.107s warmup, one120.009s window completed50,000 transitions:
**416.634 aggregate transitions/s** (1.230× the serial338.783/s reference).
The window counts only completed updates;2,000-step boundaries make this a
conservative short-window measurement. Including warmup, checkpoint/reload and
drain:70,000/160.667s=435.685/s. Every seed completed14,000 timing-only transitions;
max rollout/update21.885s. All15 tests PASS, including bit-identical serial versus
parallel weights/losses/normalizers/RNGs and scientific evaluation metrics.

At that measured window rate,5M training transitions project to**3.334h** on
this Mac. This is an extrapolation, not a completed scientific run. Concurrent
per-seed throughput is below185.2/s, projecting~200min/seed; an explicitly
configured90min cap would stop them PARTIAL. Parallel aggregate speed therefore does **not** establish
GO. The previous laptop estimate and all readiness/pilot/endpoint gates remain.
Receipts/test log: [G1-PAR evidence](../../../ops/worklog/evidence/2026-10-31-g1-par/).

Development-only evaluation timing used one unchanged case at each of the five
delays, with the partial timing policy (not final policies). Per-case simulation
and inference at five-way concurrency: baseline11.63–11.90s, policy11.83–11.96s.
Five-case pool walls21.528s/25.054s include startup/load. Allowing40 cases/worker
and loading each controller once gives `T200 = T5 + 39 * max(case_seconds)`:
baseline485.702s, each policy491.534s, all1200 cases**49.056min (0.818h)**.
Thus the **uncapped Mac projection** is3.334h training +0.818h evaluation
=**4.151h**, or~**4.684h for the whole queue** including600s smoke, the full1200s
pilot cap, and two20-case development panels. Add file/plot/export overhead.
This extrapolates short development measurements; final variants, learned final
policies, sustained thermals and USB performance are unmeasured. It does not
establish scientific completion. G1-CAP removes the default90min cap; the
queue still stops on unresolved readiness/pilot gates. Timing receipts remain
unaltered; a later receipt-only fix prevents local environments' shared CPU time
from being counted as eight separate worker processes (patch retained in evidence).
