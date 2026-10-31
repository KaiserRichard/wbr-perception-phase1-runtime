# G1 on Kaggle CPU or interactive Colab

These notebooks package the existing G1-PAR runner for a cloud CPU host. They
install the repo's scientific pins in an isolated Python 3.12 environment:
MuJoCo **3.3.7**, Stable-Baselines3 **2.3.2**, Gymnasium **0.29.1**, PyTorch
**2.2.2+cpu**, NumPy **1.26.4**, SciPy **1.15.3**, Matplotlib **3.10.3**.
The `+cpu` wheel is the Linux CPU build of the repo's `torch==2.2.2` pin;
see [PyTorch's previous-version CPU installation instructions](https://pytorch.org/get-started/previous-versions/).
Other dependencies are resolved at installation and captured in
`g1-run/cloud-packages.txt`; this is not a complete Linux transitive lockfile.
Python 3.12 comes from the host, or pinned `uv==0.9.7` provisions Python 3.12.12.
The notebook kernel keeps its own packages; no kernel restart is needed.

**Completion is gated.** The notebook runs the actual 600-second smoke and then
`python -u -m sim.rl.g1.runner run --out ... --jobs <os.cpu_count()>`.
That queue runs development checks, the seed-42 pilot, and the selected fresh
1M-transition seeds only when the existing gates pass. Notebook defaults split
the five seeds: **Kaggle 0,1,2; Colab 3,4**. A subset stops after training;
final paired evaluation runs after merging all five. It resumes
verified seed checkpoints automatically. G1-CAP makes seed wall time unlimited
by default. Set `SEED_WALL_CAP_MIN` to finite positive minutes to pass
`--seed-wall-cap-min` through the supervisor to the runner. Its budget counts
cumulative training wall time across resumed segments. The scientific recipe,
cases, rewards, metrics, pilot and readiness gates stay unchanged. Source identity
still rejects changed code on resume; use the same rebuilt bundle throughout a run.
Cloud speed has not been measured. See [G1 README](../README.md).

## Split across Kaggle and Colab, then merge and evaluate

Build **one** `g1_code.zip` and use that identical bundle on both hosts and the
evaluation host. The first code cell is tagged `parameters`: Kaggle sets
`SEEDS = [0, 1, 2]`, Colab sets `SEEDS = [3, 4]`. Each passes `--seeds` through
the supervisor to the runner. For a single host, set `SEEDS = [0,1,2,3,4]`;
that retains the full queue and automatic final evaluation. CLI equivalents:

```sh
python -u -m sim.rl.g1.runner run --out /absolute/kaggle-part --seeds 0,1,2 --jobs 3
python -u -m sim.rl.g1.runner run --out /absolute/colab-part --seeds 3,4 --jobs 2
```

Each host independently runs the unchanged smoke, readiness checks, development
baseline and seed-42 pilot before its selected final seeds. Each part keeps the
standard `seed-N/` layout (checkpoints, episode logs, optimizer logs, receipts,
curves). `run-manifest.json` records the selected seeds, source-file identity,
aggregate SHA-256 `code_hash`, training configuration/hash, and training status.
The hash covers the runtime Python modules, frozen scientific JSON, shared plant
and LQR modules, PLAN-v2 and parameter manifest; it uses working-tree bytes,
not just a Git commit. A subset completes with `part-complete.json` and a
`TRAINED` manifest/cloud status. This means its training finished; it does not
mean a five-seed scientific comparison passed.

1. Kaggle: keep `SEEDS = [0,1,2]`; use **Save Version → Save & Run All
   (Commit)** for background execution. Download its saved `g1-recovery.zip`.
2. Colab: keep `SEEDS = [3,4]`; mount Drive for durable checkpoints in
   `MyDrive/G1/output/g1-run`. **Keep the tab open** and run interactively.
   Obtain the second `g1-recovery.zip` from Drive. Resume partial sessions with
   the same bundle, seed list, job count and part folder until training finishes.
3. Extract the two archives into **different parent folders**; both contain a
   directory named `g1-run`. For example, `parts/kaggle/g1-run` and
   `parts/colab/g1-run`. Never overlay their contents. Use a fresh merged root:

   ```sh
   python -m sim.rl.g1.merge_runs \
     --parts /absolute/parts/kaggle/g1-run /absolute/parts/colab/g1-run \
     --out /absolute/g1-merged
   python -u -m sim.rl.g1.evaluation \
     --seeds-root /absolute/g1-merged --out /absolute/g1-merged/final --jobs 4
   ```

The merger requires every seed 0–4 exactly once, matching code/config hashes
across parts and the current source, completed budgets, correctly seeded
declarations/state, and hash-verified policy/normalizer/state checkpoints. It
rejects missing/duplicate seeds, failed/partial/corrupt or mismatched parts,
and existing destinations. It copies each seed byte-for-byte and retains each
part's smoke/pilot/readiness evidence under `g1-merged/parts/`. It never trains
again. Final evaluation still requires exactly 1M transitions for each seed.
Interrupted copies retain a `.merging-*` staging directory; the final root is
published only after copied checkpoints verify. Inputs remain usable.

**Mac evaluation:** run the commands above from this same source tree with the
project Python and its existing RL dependency overlay (if present):

```sh
source /private/tmp/wbr-g1-env.sh  # only if using the existing Mac overlay
PY="$HOME/Desktop/Research/wbr-lab-ops/.venv/bin/python"
"$PY" -m sim.rl.g1.merge_runs --parts /absolute/parts/kaggle/g1-run /absolute/parts/colab/g1-run --out /absolute/g1-merged
"$PY" -u -m sim.rl.g1.evaluation --seeds-root /absolute/g1-merged --out /absolute/g1-merged/final --jobs 5
```

**Kaggle evaluation:** in a separate private CPU notebook, attach the same code
bundle and both recovery archives as private inputs. Copy the parameter,
source-unpack and dependency-install cells from `kaggle_g1.ipynb` (cells defining
`REPO` and `PYTHON`); omit the training/supervisor cells. Immediately after the
parameter cell, run the following line to skip automatic single-run recovery
discovery, which would otherwise find two candidates:

```python
(OUTPUT_ROOT/'g1-run').mkdir(parents=True, exist_ok=True)
```

With Internet enabled for setup, run the source/dependency cells, then this code
cell. Replace input paths with the actual attached archives. If Kaggle expanded
them automatically, pass those separate `g1-run` input directories directly to
the merger instead of extracting ZIPs:

```python
import os
import subprocess
safe_unpack('/kaggle/input/kaggle-part/g1-recovery.zip',
            Path('/kaggle/working/parts/kaggle'))
safe_unpack('/kaggle/input/colab-part/g1-recovery.zip',
            Path('/kaggle/working/parts/colab'))
env = dict(os.environ, PYTHONPATH=str(REPO))
merged = '/kaggle/working/g1-merged'
subprocess.run([str(PYTHON), '-m', 'sim.rl.g1.merge_runs', '--parts',
                '/kaggle/working/parts/kaggle/g1-run',
                '/kaggle/working/parts/colab/g1-run', '--out', merged],
               cwd=REPO, env=env, check=True)
subprocess.run([str(PYTHON), '-u', '-m', 'sim.rl.g1.evaluation',
                '--seeds-root', merged, '--out', merged+'/final',
                '--jobs', str(os.cpu_count() or 1)], cwd=REPO, env=env, check=True)
```

Use **Save & Run All (Commit)** with output saving for this evaluation notebook;
download the saved `g1-merged/final/` baseline, per-seed metrics and comparison.
The final evaluator consumes the merged root on either host. This separate
evaluation cell has no training supervisor; retain outputs within the service's
session limit. Local tests establish exact policy/optimizer/normalizer/RNG,
loss and scientific-metric equality for tiny uninterrupted independent seeds
versus a 3+2 split and merge, with multiple worker counts and both environment
backends. Timing, host metadata and checkpoint IDs naturally differ between
fresh executions. Bitwise equality across different CPU architectures/libraries
is not established by a local test; use the same pinned dependencies. Resuming
an interrupted seed resets its active episodes as documented and is not the
same trajectory as uninterrupted training. Splitting seeds itself does not
reset or share any state.

## Kaggle: private upload to background execution

1. From the repo root, build the current working-tree source (including G1-PAR):

   ```sh
   bash sim/rl/g1/cloud/make_bundle.sh
   ```

   This creates `sim/rl/g1/cloud/g1_code.zip`. An optional first argument selects
   another output path. It includes only the G1 source/tests/configs, its four
   shared simulation modules, the old config needed by a regression test,
   requirement files, PLAN-v2/parameter manifest, cloud files, and a source hash
   manifest. No venv, credentials, data, existing results, or checkpoints enter
   the bundle. Rebuild after changing code. No commit is required.

2. Create an account at [Kaggle](https://www.kaggle.com/). Open your profile's
   **Settings → Phone verification**, verify your phone, and enable notebook
   **Internet** access. Internet is needed for pip and, when necessary, Python
   downloads. The location of the Internet switch can vary; look under notebook
   **Settings / Session options**. See [Kaggle's verification discussion](https://www.kaggle.com/product-feedback/255038).

3. Open **Datasets → New Dataset**, upload `g1_code.zip`, give it a name such as
   `g1-private-code`, select **Private**, and create the dataset. Keep source and
   notebook private. Kaggle may expand an uploaded zip: the notebook supports
   either `g1_code.zip` or its expanded `G1_BUNDLE_MANIFEST.json` and source tree.
   See [dataset documentation](https://www.kaggle.com/docs/datasets).

4. Open **Code → New Notebook → File → Import Notebook → Upload**, and import
   `kaggle_g1.ipynb`. Choose **CPU / Accelerator: None**, enable **Internet**, and
   use **Add Input / Add Data** to attach your private code dataset.
   Leave the notebook's path settings blank for automatic discovery when exactly
   one code bundle is attached. It prints the actual logical CPU count and uses
   that count as `--jobs` (usually four).

5. If readiness has already been established, attach the actual
   `host-readiness.json` and its evidence separately, and set `READINESS_JSON`
   to that input path. The four existing keys are `report_assembly_resolved`,
   `windows_smoke_passed`, `offline_bundle_verified`, `host_and_usb_permitted`.
   Evidence paths must be meaningful and accessible. Cloud execution does not
   establish Windows/offline/USB/provenance evidence. Missing evidence remains
   a recorded stop; the notebook never invents true flags.

6. Click **Save Version → Save & Run All (Commit)**, with output saving enabled
   if offered. Choose the background execution option, rather than a quick save
   that only stores the notebook. No cell requires an interactive prompt. Once
   the version is running, you can close the browser or turn off your computer.
   The service executes the notebook; the supervisor prints a heartbeat every
   minute and stores full runner logs. See [Kaggle's background execution explanation](https://www.kaggle.com/general/232625).

7. Return to the saved version and inspect its **Output** tab. Download
   `g1-recovery.zip`, and inspect `g1-run/cloud-status.json`, `cloud-smoke.log`,
   `cloud-run.log`, and the learning curves. **A green notebook execution alone
   is not a successful experiment:** the execution cell deliberately allows
   later output cells to run after a G1 failure. Only `g1-run/complete.json`
   together with `g1-run/final/` establishes a completed queue. Missing final
   metrics means no final result; a split part instead needs `part-complete.json`
   and a `TRAINED` manifest before merge. A stopped-run status/log explains an
   unfinished part.

The [Kaggle notebook specifications](https://www.kaggle.com/docs/notebooks)
currently list four CPU cores, 30 GB RAM, a roughly **12-hour CPU session limit**,
and 20 GB of saved `/kaggle/working` space. Limits/hardware can change. The
Kaggle supervisor uses a **global11.5-hour soft stop**, measured from the first
configuration cell and including unpack/install time. It blocks queued seeds,
requests active trainers to finish their update and save a verified checkpoint,
writes `g1-run/RESUME.md` plus `resume-note.json`, and exports `g1-recovery.zip`.
The old515/635-minute café timers are removed. Colab retains its configurable
11-hour session budget, with the same checkpoint/note/export behavior. None
guarantees artifacts will be saved if the platform forcibly kills a session first.

## Checkpointing and resume

- Live run: Kaggle `/kaggle/working/g1-run`; Colab
  `MyDrive/G1/output/g1-run`. The source/venv live outside saved output.
- G1 already saves verified, versioned training checkpoints every **300 seconds**
  and at training exit. This exceeds the requested ten-minute frequency without
  changing frozen `config.json`. Saves occur after a complete optimizer update;
  update/file-I/O time adds to the nominal interval.
- Every **600 seconds**, and at normal/failure exit, the supervisor refreshes
  learning curves and atomically replaces `g1-recovery.zip`. The archive includes
  logs/results and only the newest hash-verified complete checkpoint per run
  folder. Incomplete checkpoint generations are excluded. Raw output retains
  all generations. A checkpoint contains policy, optimizer, observation
  normalizer, samplers, RNG state, counters, and identity. Active episodes reset
  when resumed, as in the existing runner.
- Kaggle `/kaggle/working` is output storage for the current version, **not a
  durable live backup across fresh runtimes**. Download a saved recovery archive;
  upload it as another **private dataset**, or attach the previous version's
  saved outputs through Add Input. The notebook discovers `g1-recovery.zip` or
  an expanded `g1-run/cloud-status.json`. Set `RESUME_SOURCE` explicitly if there
  is more than one candidate. A fresh notebook restores it into `/kaggle/working`
  before running. Merely clicking Save & Run All again does not reattach old
  outputs. Unsaved files from a killed runtime may be unavailable.
- Reuse the **same code bundle, seed list, job count, and run folder** on resume. G1 rejects
  source/config/model/seed mismatches. A retained complete smoke is reused;
  completed seeds are validated, and partial final seeds resume within their
  remaining configured seed budget, or without a wall cap by default. Failure/watchdog records and an
  interrupted or failed smoke/pilot stop the queue for inspection; they are
  never silently retried. A transport STOP request is recorded and cleared on
  resume. Do not run two sessions against the same output folder.
- To start an intentionally separate experiment, select a new `OUTPUT_ROOT` and
  do not select old recovery input. Keep previous evidence intact.

## Colab: interactive execution with Drive

1. Upload `g1_code.zip` to `MyDrive/G1/input/` in Google Drive.
2. Open [Colab](https://colab.research.google.com/), choose **File → Upload
   notebook**, and upload `colab_g1.ipynb`. Select a CPU runtime.
3. Run the path cell and authorize `drive.mount('/content/drive')`. Checkpoints,
   logs, curves and recovery archive go directly to `MyDrive/G1/output/`.
4. Keep the tab open and run all remaining cells interactively. On a runtime reset, remount Drive and
   run all cells again: the retained run is detected without uploading it again.
   Download the recovery archive and results through Drive.

Colab's free runtimes can disconnect or be reclaimed earlier than the notebook's
budget; keep this workflow interactive. It provides no unattended completion
guarantee. Drive I/O is slower and may fail/quota-limit; preserve its error logs.
See [Colab's runtime and Drive FAQ](https://research.google.com/colaboratory/faq.html).

## Wall-time ESTIMATE for four vCPU

**MEASURED on the Mac (8 physical / 16 logical CPUs):** five single-thread PPO
workers completed 50,000 transitions / 120.009 s = **416.634 aggregate steps/s**,
or **83.327 steps/s per active worker**. Development evaluation projected
49.056 min (0.818 h) for 1,200 cases at five-way concurrency. These are short
timing runs, not completed final policies; see the
[G1-PAR receipt/review](../../../../ops/worklog/reviews/2026-10-31-g1-par.md).

**ASSUMPTION:** each cloud vCPU sustains one Mac timing worker's throughput.
Scale the **five active workers**, not all 16 logical CPUs: four workers give
`416.634 × 4/5 = 333.307 aggregate steps/s` while all four are busy.
Cloud CPU generation, sharing, thermals, and Drive I/O are unmeasured.

| Component | Uncapped four-vCPU ESTIMATE |
| --- | ---: |
| Naive training lower bound, 5M / 333.307 | 4.17 h |
| Actual five-seed schedule on four workers: two waves × 1M / 83.327 | **6.67 h** |
| Paired evaluation, 0.818 × 5/4 | **1.02 h** |
| Smoke 600 s + pilot cap 1,200 s + development panels ~148 s | **0.54 h** |
| Queue total, before installation/plot/export overhead | **8.23 h** |

The fifth seed cannot use the three idle workers in its final wave: each seed
keeps the frozen eight-environment recipe. Therefore 4.17 h is not the full
training forecast. The two-wave calculation assumes equal worker speeds and
1M transitions for every seed; evaluation scaling ignores small pool rounding.

**This is a planning ESTIMATE, not a completion claim.** At83.327 steps/s,
each seed would need **~200 minutes**. G1-CAP permits that duration by default;
an optional90-minute cap still requires at least185.185 steps/s per seed.
The guarded notebook stops on readiness/pilot/evaluation gates, an explicitly
configured seed cap, or its global session soft stop, preserving PARTIAL artifacts.
No complete cloud run is claimed. The cloud smoke records actual host speed;
the notebook preserves that receipt and every failure reason.

## Local validation scope

Validate with `nbformat.validate` and compile each Python code cell; run
`bash sim/rl/g1/cloud/make_bundle.sh`. The notebooks contain their complete
bootstrap/supervisor code, so no helper script is fetched from a public repo.
The allowlist bundle uses the working tree and includes tests; its manifest
records every included file hash and HEAD as provenance, without pretending
uncommitted code is represented by HEAD alone. Linux installation, Kaggle UI,
Drive authorization, actual cloud runtime/throughput, and end-to-end scientific
completion require those services and are not established by local parsing.
