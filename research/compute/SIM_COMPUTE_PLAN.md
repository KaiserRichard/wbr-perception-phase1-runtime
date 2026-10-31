# Staged simulation and compute plan

**Planning snapshot: 31 Oct 2026.** Machine specs are owner-reported unless stated. All sizing and setup times below are **ESTIMATES**, not benchmarks. Verify the model, machine and rates before a long run.

## Stages and first benchmark

| Stage | Heavy work and ESTIMATED resources | Best machine and fallback | First 10-minute benchmark |
| --- | --- | --- | --- |
| **S0 — planar twin + viewer** | Mostly one CPU physics loop; viewer drawing. ESTIMATE: 2–4 CPU cores, <4 GB RAM, no CUDA GPU. | Mac for daily editing and the already-working viewer. Fallback: any listed machine. | Same fixed 10 s balance/push traces, viewer off/on. Record physics steps/s, real-time factor, viewer frame rate, CPU/RAM and frame pauses. |
| **S1 — calibrated 3D, both five-bars and contact** | 3D constrained dynamics, contact solver and actuator/controller callbacks; one rollout is primarily CPU work. ESTIMATE: 4–8 fast CPU cores, 8–16 GB RAM, no GPU required for correctness. | Start on Mac for model/debug work; use the lab PC if inventory shows ≥8 useful cores and ≥32 GB RAM. Fallback: brother's 8-core/32 GB laptop or Training Station CPU. | Fixed candidate 1 kHz flat/contact trajectory (ESTIMATE; freeze after solver/convergence checks); record steps/s, real-time factor, solver time, peak RAM, contact/constraint counts and penetration/equality residuals. Change env count only after this single-env model is valid. |
| **S2 — rendered camera/depth in loop** | Physics plus image/depth rendering and perception at sensor rate; image work can dominate. ESTIMATE: 6–8 CPU cores, 16 GB RAM, 6–8 GB VRAM for modest parallel rendering; one 640×480 camera at 10 Hz may run without CUDA. | Mac for one low-rate camera loop; brother/Training Station for repeatable camera batches. Fallback: Stadium or cloud if many rendered envs are needed. | Fixed scene and camera at 640×480, 10 Hz, for 10 min. Record rendered frames/s, p50/p95 sensor-to-decision age, missed frames, physics rate, CPU/RAM/VRAM and output size. |
| **S3a — G1 governor RL** | CPU MuJoCo at 500 Hz plus a 100 Hz PPO governor, optimizer updates, checkpoint writes and paired evaluation. ESTIMATE: 8 CPU cores/16 threads, 16–24 GB RAM, 0 VRAM. Five 1M-transition seeds are the proposed G1 budget; the G1 runner is not yet in the legacy bundle. | Brother's laptop for a measured 12 h CPU session: its owner-reported 8-core/32 GB configuration is the best known free fit. Prefer the lab PC if inventory and benchmark show better CPU/storage. Fallback: Training Station only with confirmed ×3 credit and an offline bundle. | Run the frozen G1 environment through complete PPO updates and checkpoint I/O. Record completed transitions/s, update p95, peak RAM, CPU/temperature and evaluation time; project the exact budget. SRC_PLAN-v2's proposed laptop gate is **≥185.2 completed transitions/s**, update ≤60 s and paired evaluation ≤120 min; it is a gate estimate, not an observed rate. Then do its separate 15-minute offline portability smoke. |
| **S3b — later locomotion RL, many envs** | Contact-rich 3D physics across many parallel envs plus neural-network updates; images add rendering cost. CPU MuJoCo remains the correctness reference. ESTIMATE: CPU route 8–16 cores/32 GB RAM; GPU-batched Warp/MJX route 8+ CPU cores, 32 GB RAM and 12–24 GB VRAM, depending on env count. | First make a small CPU baseline. Then prefer a Linux lab GPU or cloud GPU after backend parity; Stadium 4090 is the strongest café option. Fallback: CPU MuJoCo on the laptop with fewer envs. | After JIT warm-up, sweep 1/16/64/256 envs (as memory permits) on identical fixed rollouts. Record steady env steps/s, compile time, PPO transitions/s, GPU utilization/VRAM, CPU/RAM and contact overflow. Compare matched CPU/GPU trajectories and model features before training. |
| **S4 — batch evaluation/domain randomization** | Many independent seeds, masses, friction, delays, sensors and held-out cases; usually physics throughput and artifact handling, not large NN training. ESTIMATE: 8–16 CPU cores/32 GB RAM; 12+ GB VRAM only if Warp batching or camera rendering wins the benchmark. | Lab PC with persistent storage when available; cloud for unattended sweeps; Stadium for a prepared short GPU batch. Fallback: brother's CPU laptop for smaller batches. | Run a fixed 10-minute case panel at 1/16/64 envs. Record completed cases/s, failures, peak memory, artifact-write rate and reproducibility/hash checks. Project the full panel from measured case throughput, not advertised GPU speed. |

The current `sim/twin3d` plant is a reduced virtual-leg contact model, not the calibrated two-five-bar mechanism. Its current 3D MJCF uses `implicitfast`; MuJoCo Warp does not support that integrator, so a GPU port needs an integrator decision and semantic parity checks. The existing perception option renders simulated depth in this same reduced plant. Treat S1/S2 as future model milestones, not existing validated capability.

The current RL path is Stable-Baselines3 PPO with `device='cpu'`; it does **not** send ordinary MuJoCo physics to the GPU. Existing protocol and legacy v2 results are not the proposed G1 runner. G1 is CPU-first. Only later batched locomotion makes GPU physics a candidate.

## Stage × machine fit

**OK** = sensible trial at the stated scale; **slow** = fallback or small scale; **not possible** = requested backend cannot run as specified; **?** = unknown lab configuration. For G1, GPU capability is irrelevant because this is a CPU workload. Windows without WSL2 cannot run NVIDIA MJX-JAX natively; Warp/PyTorch CUDA may run natively, but only after a compatible driver, model adapter and parity check. Existing project review does not authorize installing WSL2. Full Isaac Sim rendering needs at least 32 GB RAM and 16 GB VRAM; the café 4090 tier meets that floor, the other listed GPUs do not.

| Stage | Mac i9/16 GB/Intel | Brother i7/32 GB/3060 6 GB | Private 4060 8 GB/16 GB | Training 3060 12 GB/32 GB | Stadium 4090 24 GB/64 GB | Lab PC | GPU cloud |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S0 planar/viewer | OK | OK | OK | OK | OK | ? | slow |
| S1 constrained 3D/contact | slow | OK | slow | OK | OK | ? | OK |
| S2 one camera/depth loop | OK | OK | OK | OK | OK | ? | slow |
| S3a G1 CPU PPO | slow | OK* | slow | OK* | OK* | ? | slow** |
| S3b batched locomotion | not possible for CUDA | slow | OK*** | OK*** | OK | ? | OK*** |
| S4 batch evaluation/sweeps | slow | slow | slow | OK | OK | ? | OK*** |

`*` Only if the 10-minute rate plus the separate 15-minute offline smoke pass the G1 plan's time/RAM/checkpoint gates. `**` A GPU cloud VM is poor value for current CPU-only G1; a CPU VM may fit but needs its own quote/benchmark. `***` Means Warp/PyTorch route after adapter and driver testing, not native Windows JAX GPU. MJX-JAX runs best on large batches and can be much slower for one scene.

## Setup and operating cost (ESTIMATES)

| Machine | Cost / setup effort and constraints |
| --- | --- |
| Mac | $0 new compute cost; existing environment. Allow 0–1 h to pin/version a benchmark. 16 GB and no CUDA limit large batches; keep it as the development/reference machine. |
| Brother's laptop | No rental charge; borrow window about 12 h. Allow 1–3 h off-site to stage/test a portable offline CPU bundle and 15 min for the required smoke. Windows native MuJoCo CPU works. Native Windows NVIDIA JAX GPU is unavailable; Warp/PyTorch is a possible separate route. |
| Chợ Mơ Private | Owner-reported effective 7,333 VND/h at ×3; RTX 4060 8 GB, 16 GB RAM. Allow 1–2 h to stage USB bundle plus 15–30 min on site to verify GPU, package lock and export. Small RAM; disk resets at shutdown. |
| Chợ Mơ Training Station | Owner-reported effective 8,067 VND/h at ×3; RTX 3060 12 GB, 32 GB RAM. Same USB/reset/setup constraints. Best café balance for CPU G1 and moderate Warp batches. |
| Chợ Mơ Stadium | Owner-reported effective 16,500 VND/h at ×3; RTX 4090 24 GB, 64 GB RAM. Same reset/setup constraints. Reserve for measured GPU batching or full Isaac Sim, not CPU-only G1. |
| Lab PC | Reported as potentially free, but exact CPU/GPU/RAM/OS, permissions, disk persistence and setup are unknown. Allow 30–60 min for inventory, then estimate 1–4 h to prepare only the selected stack. No recommendation until inventoried. |
| RunPod GPU cloud | Current listed starting rates: RTX A5000 24 GB, 9 vCPU/25 GB RAM at $0.27/h; RTX 4090 24 GB, 6 vCPU/41 GB RAM at $0.89/h. Six hours is $1.62/$5.34 before storage/tax. Allow 1–3 h for a reproducible image, persistent artifacts and first parity run. GPU pods are overkill for CPU G1; CPU VM rates need a separate quote. |

The OEG page checked 31 Oct 2026 displayed no active promotion. Therefore the ×3 café credit and owner-reported effective prices above are **not currently confirmed**; do not book/top up until ×3 is explicitly available. Copy code, wheels, logs and checkpoints to USB before café shutdown. Cloud storage is separately billed; never leave the only result on an ephemeral disk.

## Recommended sequence

1. **Now:** keep S0 on the Mac. Use a 10-minute baseline to record the Mac's current physics/viewer capacity; continue model work there without buying hardware.
2. **S1:** first reconcile CAD/BOM masses, inertias, COM, linkage geometry and actuator/timing inputs. Build and validate the CPU contact model before moving backends. Use the inventoried lab PC if it has persistent storage; otherwise borrow the laptop for a measured headless run.
3. **S2:** add the camera/depth loop to the validated model. Benchmark one 10 Hz camera on the Mac, then move only if frame age/rate misses the target. Use a GPU station/cloud only if parallel rendering shows a measured gain.
4. **S3a:** finish/freeze the G1 runner and offline package first. Use CPU MuJoCo + CPU SB3; borrow the laptop only after its 10-minute throughput projection and 15-minute smoke satisfy SRC_PLAN-v2. If not, measure the lab PC; do not switch to a GPU just because one is available.
5. **S3b then S4:** after G1 review and S1 model validation, compare CPU MuJoCo against a small Warp/MJX batch. Use Training Station for a confirmed ×3, moderate GPU pilot; Stadium or cloud only if the 10-minute batch benchmark shows enough full-job time saved to justify its cost. Keep Isaac Lab optional: it needs a separate port/setup budget, and full Isaac Sim rendering has a 32 GB RAM/16 GB VRAM floor.

## Sources and check dates

- MuJoCo install/rendering and platform support, checked 31 Oct 2026: [Python install and viewer](https://mujoco.readthedocs.io/en/stable/python.html), [rendering/OpenGL](https://mujoco.readthedocs.io/en/latest/programming/rendering.html), [MJX implementations, batch behavior and feature support](https://mujoco.readthedocs.io/en/latest/mjx.html).
- JAX platform matrix, checked 31 Oct 2026: [JAX installation](https://docs.jax.dev/en/latest/installation.html) lists NVIDIA GPU on native Windows as unsupported and Windows WSL2 as experimental.
- Warp platform/driver requirements and MuJoCo Warp capability, checked 31 Oct 2026: [Warp installation](https://nvidia.github.io/warp/stable/user_guide/installation.html), [MuJoCo Warp](https://github.com/google-deepmind/mujoco_warp). Current CUDA 13 Warp wheels require NVIDIA R580+ and Turing-or-newer; check the installed driver before using them.
- Isaac Lab v3.0 requirements, checked 31 Oct 2026: [installation](https://isaac-sim.github.io/IsaacLab/v3.0.0/source/isaaclab/installation.html). The default Newton/Warp path and optional full Isaac Sim have different requirements; full Isaac Sim lists a 32 GB RAM / 16 GB VRAM workstation floor.
- GPU rental rates, [RunPod pricing](https://www.runpod.io/pricing), page says updated 8 Oct 2026; checked 31 Oct 2026. Availability and persistent storage can change the total.
- Café hardware/rates: [OEG Chợ Mơ](https://cyber.oeg.vn/tttm-cho-mo), checked 31 Oct 2026 (no active promotion shown); effective station prices/specs are owner-reported in [20 Oct compute strategy](../../ops/worklog/reviews/2026-10-20-cafe-compute-strategy.md), not a fresh public quote.
- Project source basis: [SRC_PLAN-v2.md](../../SRC_PLAN-v2.md), [SRC_RL_REVIEW.md](../../SRC_RL_REVIEW.md), [simulation roadmap](../explore/ROADMAP.md), [current reduced contact plant](../../sim/twin3d/model.py), [current CPU PPO trainer](../../sim/rl/training.py), and [current RL protocol](../../sim/rl/protocol.json).

## What to buy or borrow, and when

**Buy nothing now.** Keep the Mac as the S0/reference machine. Borrow the brother's laptop for G1 only if its measured CPU rate, memory and checkpoint/export projection fit the frozen 12-hour plan; otherwise use a lab PC only after its inventory and 10-minute benchmark pass. Use Chợ Mơ Training only after ×3 credit is confirmed and the offline bundle is ready. Book Stadium only when a measured Warp/camera benchmark predicts enough completion-time reduction versus Training to justify the price. Rent RunPod only after backend parity; start with the A5000 rate, and move to a 4090 only if the measured batch is GPU- or VRAM-limited. Do not buy an accelerator: the owner's purchase rule requires the X1 report first.
