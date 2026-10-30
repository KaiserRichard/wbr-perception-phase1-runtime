# R0 — Reopen RL through a bounded task ladder

2026-10-30 · Research plan only; no training, spending, deployment or firmware change executed.
Owner reopened the research axis; the stopped v3 recipe remains stopped. This is a new protocol, not a retry of seed 42.
Cafe GPU/VRAM, CPU/RAM, Windows version, driver, writable space, internet and execution restrictions: **PENDING owner configuration**.
Use DM-J4310 hip motors and DM-H6215 wheel motors; **no micro-ROS**. STM32 retains balance/motor safety; Pi supplies sensing/advisory data.
Single future parameter manifest: team-report body/leg/wheel masses **3.5/0.2/0.7 kg**, five-bar **0.075/0.14/0.08 m**, wheel radius **0.0603 m**; inertias **ASSUMED**.
Preserve the report's assembly/per-side definitions in that manifest before implementing dynamics; do not silently double masses or substitute legacy values.
The main-branch parameter audit describes the older assumed plant (2.0/0.5/0.6 kg), not this new parameter source; retain old results under their original model hashes.
Never edit or duplicate `sim/parity/student.py::gain_schedule`; use a separately named, frozen baseline design outside that owner exercise.

## 1. Why v1–v3 failed: measurements versus hypotheses

| Factor | MEASURED in assumed simulation | INFERRED limitation; concrete new change |
|---|---|---|
| Precision objective | v2 reward charged only 0.16% of alive reward at 2 cm; direct strict 59/800, survival 760/800; residual strict 0/480, survival 480/480. | Survival and precision incentives differ; use tolerance-normalized costs and log every component (§3). No causal ablation yet. |
| Sample budget / CPU | v1: 150k transitions/seed at 500 Hz, only 300 simulated seconds; strict 0/800 versus LQR 160/160. v2: eight 3M-transition runs took ~17.51 h wall total. | Underexposure may matter; GPU-batched physics may buy more experience, but larger budgets alone did not solve v2. Measure end-to-end throughput; cap a new matched-budget experiment. |
| Direct torque / rates | v1 direct PPO acted at 500 Hz; v2 direct at 100 Hz while LQR stayed 500 Hz. v2 passes per seed were [39,20,0,0,0]. | Fast torque exploration and differing rates complicate credit assignment/comparison. Start residual-on-LQR; compare direct at the same 100 Hz policy rate and same 500 Hz plant/base tick. Report rate asymmetry to LQR. |
| Noise / oscillation | v2 residual final-window leg/body-rate breaches: 480/480 and 477/480; saved traces show rate variation. Evaluation was deterministic. | Noise amplification is plausible, not established; use identical causal observations/history and paired noise-on/off development diagnostics. Freeze any filter before final evaluation; never credit exploration noise for deterministic jitter. |
| v3 objective trade | Seed42: strict 16→16→11/16; survival always16; normalized error E 0.292→0.447→0.826. Two final position breaches; three recovery-deadline failures. | Learning degraded a passing base; constant-offset explanation is incomplete. Preserve zero-residual identity and precision guardrails; seek headroom on new tasks instead of changing the old acceptance screen. |

Sources read from `origin/main`: [v1](../../sim/rl/RESULTS_2026-10-20.md), [v2](../../sim/rl/RESULTS_V2_2026-10-20.md), [v3 proposal](../../ops/worklog/reviews/2026-10-21-v3-research.md), [v3 result and corrected attribution](../../ops/worklog/reviews/2026-10-22-v3-pilot-result.md).

## 2. Task ladder and frozen comparison

All numerical criteria below are **proposed simulation criteria**, fixed before new training; no hardware capability claim. No rung advancement from a selected seed/video.
Build/run the flat task first and debug actual errors. Extend to a floating-base 3D model with both five-bars, wheel/contact geometry, joint torque mapping and actuator envelopes before steps/jumps; the old six-state plant cannot represent them.
Use report geometry/masses, documented assumed inertia/COM/friction and motor delay/lag; vary assumptions in held-out panels. Missing torque-speed/thermal data limits conclusions to simulation.
Training seeds **0–4 per learned arm per rung**, five independent policies, all retained. Pilot seed42 is development-only and excluded from final results.
Each rung: residual and direct arms receive **10M aggregate policy transitions/seed**, including curriculum, identical command/terrain sampling and optimizer-update allocation; 100M transitions total/rung. Count simulated seconds too (100 Hz → 100k s/seed).
Fixed baseline gets no training; cap its development at **2 workstation-hours/rung**, freeze before learned-arm final runs, disclose tuning effort. Pilot/debug transitions are recorded separately; no free warm-start experience.
Both learned arms start fresh per rung; reuse weights only in a separately declared transfer experiment charged for all pretraining. Stop incomplete runs as PARTIAL, never compare unequal budgets as final results.
For each rung freeze **200 held-out 10 s cases**: task factors below × delays2/5/10 ms × noise/payload/friction variants in a versioned manifest; same cases/observations/saturation for every controller, training seed and baseline. Keep development seeds2000–2019 separate from final3000–3199.
Use 500 Hz physics/control tick initially; resolve shorter contact times by refining the timestep for every controller together before freezing. Truth is for scoring/critic only, actor uses deployable sensor/history inputs.

| Rung / held-out factors | Baseline frozen before learning | Pass criteria for **each of five seeds** |
|---|---|---|
| 1. Balance + speed tracking: stationary starts ±5°, ±10°; commands0, ±0.1, ±0.2 m/s; signed6 N×0.15 s pushes. Separate10 ms-delay stress stratum from2–5 ms reference. | Delay-aware LQR at500 Hz with command feedforward/reference generator; same estimates and known delay as actor. Recompute for new model, do not reuse legacy160/160 as new evidence. | ≥95% cases complete without fall; stationary cases satisfy original six tolerances throughout last1 s and recovery≤5 s. Moving cases: final2 s speed RMSE≤0.03 m/s, path error≤0.02 m, pitch/leg-angle error≤1°, both angular rates≤0.05 rad/s. ≥95% strict overall; no reference stratum >5 percentage points below baseline. |
| 2. Low step: ascent/descent10/20 mm, approach0.1/0.2 m/s, friction0.5/0.8; identical height input to actor/baseline. | LQR + deterministic slow/extend/cross/settle state machine; same terrain age/noise. | ≥90% strict: both wheels cross, travel≥0.30 m beyond edge by8 s; no body-ground collision/fall; peak absolute roll/pitch≤15°; final2 s speed RMSE≤0.03 m/s and pitch≤2°. No joint-limit/singular-closure or actuator-envelope breach. |
| 3. Jump: commanded vertical hop20/40 mm on flat floor; initial pitch±2°, friction0.5/0.8. | Four-phase crouch/thrust/retract/settle reference + LQR where grounded; deterministic flight/landing mode controller. | ≥90% strict: both wheels airborne≥20 ms, base rise reaches requested height, recontact by3 s, no body-ground collision/fall; settle by5 s with position error≤0.02 m, pitch/roll≤2°, speed≤0.03 m/s for final1 s. No envelope/joint/closure breach; phase timeout≤1 s triggers failure. |

Fall = body-ground collision or |pitch|/|roll|>30°; a terminated episode fails every unfinished objective. Log peak torque, saturation time, joint speed, contact impulse and effort ∫τ²dt; absent radial load data precludes motor-load safety claims.
At rung1 retain original stationary tolerances: position0.02 m, translation rate0.03 m/s, both planar angles1°, both angular rates0.05 rad/s; add roll safety for3D.
A rung passes engineering criteria only when all five seeds pass. Research benefit additionally requires ≥10 percentage-point mean strict gain over the strongest baseline on its predeclared difficult stratum, positive lower95% paired seed-level t interval (df4), and no >5-point overall regression. Report each seed and paired case outcomes; do not treat episodes as independent training replications.
If baseline already achieves≥95% on every stratum, report no success headroom; do not secretly switch to effort as the primary outcome. Freeze a new task proposal before any further training.
Jump prior: [source lesson](../../docs/lessons/05_wbr_jump_sequence.md): crouch0.08 m (<0.10 transition), thrust0.21 m (>0.18), retract to captured stand length (<stand+0.01), settle. Both sides qualify; source counters≥10 are scheduling-dependent, not contact proof.
Use these as reference structure/phase observations and bounded residuals; verify reachable geometry and add simulated contact/timeout checks. The source's left use of `leg_right_set` remains UNKNOWN; do not port it as established intent.

## 3. Reward and action design

At100 Hz let q_i=e_i/t_i, with t=(0.02 m,0.03 m/s,1°,0.05 rad/s,1°,0.05 rad/s); moving x reference integrates commanded speed, stationary x remains fixed.
Proposed dense reward: r = 1 − [q_x² + q_v² + 0.5(q_leg²+q_pitch²) + 0.25(q_leg_rate²+q_pitch_rate²)] −0.01Σ(τ_j/τlim_j)² −0.05Σ((a_j−a_prev,j)/0.1)² −0.1Σ(δτ_j/c_j)²; omit last term for direct.
A lone2 cm error costs **1.0 per action**, cancelling alive1; coefficient on x² is1/(0.02²)=**2500 m⁻²**, versus v2's4 m⁻²:625× larger. At1 cm the cost is0.25. This makes precision explicit; it does not guarantee learning.
Keep quadratic precision costs unbounded within physical termination limits; log distributions to detect domination. No hidden reward clipping; normalize observations with saved statistics, not the reported reward components.
Set fall/early-abort penalty to remaining possible alive reward: −ceil((10−t)/0.01), preventing an early fall from avoiding future negative costs versus receiving zero thereafter; it cannot guarantee preference over arbitrarily negative continued trajectories. Track falls directly.
Step/jump add phase-reference tracking and terminal success+10 only after all strict conditions; freeze coefficients/scales in rung protocol. Score geometry, timing and recovery separately from return; no best-checkpoint selection.
Residual arm: zero final actor weights/bias, deterministic initial δτ=0, LQR recomputed every2 ms; hold correction10 ms. Start c_j=10% of documented simulated per-joint limit, stochastic SD=0.05c_j; cap total command and log every clipped component.
Direct arm: same actor observations/history,100 Hz held torque, total caps and action-rate penalty. Rate penalty acts on normalized policy output a; additionally log actual500 Hz torque slew, including base-controller changes.
Use current joint-level VMC mapping and speed-dependent limits; old aggregate2/4 N·m caps are legacy assumptions, not DM motor capability. If only constant caps are available label them ASSUMED; no physical deployment.
Before full runs, actually run deterministic zero-residual and baseline trajectories together; repair any mismatch from the trace. Pilot once for20 min/≤1M transitions; require no survival regression>5 points and no precision-E deterioration>10% on fixed development cases. A failed pilot ends that recipe; no seed/reward fishing.
Save return, length, all reward sums, strict success, recovery, saturation, residual mean/SD and E versus steps. Noise-on/off diagnostics are causal tests only when noise is the sole changed input.

## 4. Windows cafe compatibility matrix

Official pages opened2026-10-30; pin a coherent release set during bundle preparation. Installation in a user directory is an engineering inference, **not proof cafe policy permits it**. Never depend on a driver update, reboot, Docker or administrator privileges.

| Stack | Official installation / platform facts | Without admin rights at this cafe |
|---|---|---|
| MJX/JAX | [`pip install mujoco-mjx`](https://mujoco.readthedocs.io/en/stable/mjx.html); [JAX matrix](https://docs.jax.dev/en/latest/installation.html): NVIDIA CUDA on Linux, WSL2 experimental; native Windows CUDA unsupported. | User venv works only inside already provisioned Linux/WSL2 with suitable host driver. [Installing WSL requires admin and restart](https://learn.microsoft.com/en-us/windows/wsl/install). New WSL unavailable under constraints; existing WSL GPU path **UNVERIFIED**. CPU JAX is not the planned GPU route. |
| MuJoCo Warp, native API + PyTorch PPO | [Official install](https://github.com/google-deepmind/mujoco_warp#Getting-started): `pip install mujoco-warp`; [Warp install](https://nvidia.github.io/warp/latest/user_guide/installation.html) supplies Windows x86-64 wheels and bundled CUDA components, no system toolkit needed. | Potential native Windows user-venv route with existing compatible NVIDIA driver. Match pinned wheel/runtime to driver; no source-build/toolchain assumption. Batched WBR closure/contact support, PPO adapter, restart determinism and no-admin execution **UNVERIFIED**. Using Warp through MJX still inherits JAX's platform constraint. |
| Isaac Lab + Isaac Sim on Windows | [Release2.3 install/requirements](https://docs.nvidia.com/isaaclab/2.3/isaac-lab/local-installation): Windows11,32 GB RAM,16 GB VRAM, Python3.11 for Sim5.x; recommends Windows driver580.88. | User-space pip/binary install potentially possible if all existing prerequisites, RTX support, disk and permissions fit. No-admin operation **UNVERIFIED**; missing driver/runtime needs staff. Large downloads/cache and custom model port make this a separate learning option, not a first-session migration. |
| SB3 + CPU MuJoCo | [SB3 install](https://stable-baselines3.readthedocs.io/en/master/guide/install.html) documents Windows environments; [MuJoCo pip](https://mujoco.readthedocs.io/en/stable/python.html#installation) bundles native library. | User-local Python/venv + binary wheelhouse should avoid admin if application execution/runtime dependencies are allowed; actual cafe run **UNVERIFIED**. Use headless CPU physics and CPU small-MLP PPO; installing CUDA PyTorch alone does not accelerate CPU MuJoCo. |

Try the prepared native Warp end-to-end job; fix actual errors up to the setup cap, then run CPU fallback. Select no stack solely from advertised GPU FPS. Native Warp candidate status does not establish a portable training implementation.

## 5. Portable bundle and recovery contract

Proposed artifact, prepared off-site before session1 (not implemented by this plan):
```text
WBR-R0.zip / USB WBR-R0/
  setup.ps1                    # sole setup entry: -Stack warp|cpu|mjx|isaac; -Offline
  python/  wheelhouse/<stack>/  locks/<stack>.txt  licenses/
  source/  models/parameters.yaml  protocols/  baselines/  manifests/SHA256SUMS
  jobs/                        # train/eval/export entry points + frozen case lists
  runs/<protocol>/<arm>/seed-N/{checkpoints,metrics,traces,videos,receipt.json}
  cache/                       # optional disposable kernels/assets, never evidence
  README.md                    # extract, setup, run, resume, export; no secrets
```
`setup.ps1` uses a user-writable local directory, user-local Python and hash-locked wheels; recreates venv after extraction (never ships a relocatable venv), records versions/driver/device, launches the actual flat train→save→resume job. PowerShell policy/application blocks are recorded, not bypassed.
Keep separate Windows and Linux/WSL locks/wheels; no universal binary bundle claim. If user Python needs a missing system runtime, fall back to an already functioning staff-provided runtime or end the compute attempt.
Checkpoint **every5 min**, at update boundaries, with ≤one-update extra delay recorded; temp-write then atomic rename, previous checkpoint retained. Include actor/critic, optimizer/scheduler, normalizers, RNGs, sampler/curriculum, transition counters and config/model hashes.
Serialize simulator/env state if supported; otherwise record reset-on-resume and discontinuity, restore RNG/sampler and never claim bitwise trajectory continuation. Exercise an interrupted run before spending full-run time.
Copy each completed checkpoint + metrics + SHA manifest to USB; every30 min copy to a second owner-controlled location when reachable. Budget final30 min to export everything, verify destination hashes and reload copied checkpoint; push small source/config/receipts or copy them, keep large evidence off git. No credentials in ZIP; no shutdown before verified copy.

## 6. First three cafe sessions: exact 2 h core + optional 2 h

Off-site prerequisites: runnable bundled flat model/runner/CPU fallback, frozen development protocol and compiled wheelhouse; step/jump models may follow later. Do not spend all cafe time writing the trainer.
Minute ranges below are elapsed time on one PC/GPU; GPU-hours are reserved accelerator-active allowances, **not measured throughput or promised completion**. Export time is part of each session.

| Session | Mandatory0–120 min | Optional120–240 min, decided before starting extension | Required output / GPU allowance |
|---|---|---|---|
| 1: make portability real | 0–30 extract/setup and launch actual flat PPO; fix observed errors, CPU fallback at30. 30–60 train/checkpoint/interrupt/resume and time export (setup+first export≤60 min, preserving historical pilot bound). 60–90 run WBR batched throughput/memory, baseline/noise traces. 90–120 final export/hash/reload. | 120–150 restore from USB into fresh user directory;150–210 profile batch sizes and one20 min development pilot;210–240 export. | Device/OS/driver receipt, usable locked bundle, measured transitions/s including optimizer, simulated-seconds/s, VRAM peak, startup/export time, restored checkpoint; **0.5–1.5 GPU-h** (CPU fallback0). |
| 2: bounded development | 0–20 restore/launch;20–40 one20 min pilot if not already completed (otherwise analyze it);40–70 frozen development snapshots/baseline;70–90 diagnose results and freeze protocol only if screens pass;90–120 export. No second pilot after a failure. | 120–210 start full rung1 seeds0–4 across both arms in fixed round-robin update blocks only if pilot passed and frozen budget fits;210–240 export. | Pilot curves/components, no-headroom check, frozen case/config hashes, start receipts or explicit FAIL; **0.5–2 GPU-h**. |
| 3: matched evidence | 0–20 restore;20–75 resume all ten rung1 jobs at equal allocation;75–90 evaluate completed final checkpoints or label partial progress;90–120 export/reload. | 120–180 continue fixed jobs;180–210 final paired evaluation if all complete;210–240 export. Never start rung2 while rung1 incomplete. | Ten full-budget policies + paired200-case panels each if feasible; otherwise honest transition counts/checkpoints and continuation estimate. Per-seed table, failures, compute receipt; **1–2.5 GPU-h**. |

Total reservation **2–6 GPU-h** over6–12 seat-hours; compilation/evaluation may use the GPU too, so record actual device-active allocation separately. CPU fallback records CPU-hours and does not promise completion in three visits.
Estimate after session1: T_train=100M/(3600F) GPU-h for rung1 at measured aggregate training throughput F; at F=10k/s →2.78 h, at1k/s →27.78 h, plus startup/evaluation/export (illustrations, not forecasts). Three rungs total300M transitions before pilots/ablations; do not promise those in three sessions.
If projected work exceeds remaining allocation, stop at partial evidence and rescope before another paid visit. Respect [D-20261020-CAFE and later ×3 purchasing clarification](../../ops/worklog/DECISIONS.md) and [compute review](../../ops/worklog/reviews/2026-10-20-cafe-compute-strategy.md): no new deposit or assumed current pricing; this plan does not authorize Isaac migration/payment.

## 7. Risks and closing RL again

Risks: unmeasured inertia/COM and motor envelopes, five-bar constraint/backend mismatch, contact timestep artifacts, Windows locks/driver incompatibility, wiped local disk, reward gaming, seed variance, baseline ceiling, and simulated gains that vanish under delay/noise. No novelty or sim-to-real claim from this plan; [X2](../explore/x2-rl-locomotion.md) is a literature map, not hardware truth (its RobStride/micro-ROS references are superseded here).
Close this new recipe immediately if its single development pilot fails precision/survival screens; retain the failure and do not tune against the same panel. If all baseline strata have≥95% strict success, close that task's superiority study for lack of headroom.
Close the reopened RL axis after one completed five-seed-per-arm rung with neither arm meeting both engineering and research-benefit criteria; also close the cafe route after two visits unable to restore/export or deliver the fixed budget within a predeclared **12 GPU-h total ceiling**. Infrastructure failure is not evidence RL is ineffective.
No progression to steps/jumps on a failed rung; no additional seed, checkpoint selection or endpoint switch to rescue a result. Any reopening requires a new owner decision and distinct question/data, with old failures retained.
Milestone review artifact must contain model assumptions, frozen hashes, all seeds/baselines, paired intervals, actual compute, failure traces and limitations; Claude reviews the completed milestone. No motors, STM32 flashing or physical jump is authorized.
