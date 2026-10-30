# C1-T12 — R0 v2: bounded command governor under unseen delay

2026-10-30. Planning only; no training, network, commit, purchase or motor authority.
Labels: **SOURCE-SUPPORTED** = local source or owner-supplied fact, not necessarily measured;
**INFERRED** = reasoning/procedure; **ASSUMED** = unvalidated parameter, threshold or forecast.
All proposed numerical settings below are ASSUMED; procedures are INFERRED unless labelled otherwise.
This supersedes [PLAN](PLAN.md); applies every CHANGE/DROP in [review §1](REVIEW-2026-10-30.md).

## Evidence and model contract

- SOURCE-SUPPORTED: [v2](../../sim/rl/RESULTS_V2_2026-10-20.md) underperformed LQR: direct strict59/800, residual0/480; LQR160/160 on the old plant. V3 seed42 degraded precision (E0.292→0.447→0.826) and remains stopped; see [receipt](../../ops/worklog/reviews/2026-10-22-v3-pilot-result.md).
- INFERRED: weak precision incentives, insufficient experience and noise amplification are hypotheses, not proven causes. Deterministic evaluation jitter is not exploration noise. New data must answer a new question.
- SOURCE-SUPPORTED: WBR uses DM-J4310 hips, DM-H6215 wheels, DM CAN; DM-jump input provenance is PS2 + UART. No micro-ROS or RobStride in WBR; those references belong only in separate AGV material.
- SOURCE-SUPPORTED: [params_manifest.yaml](params_manifest.yaml) records report body/leg/wheel3.5/0.2/0.7 kg, l1=l4=0.075 m, l2=l3=0.14 m, l5=0.08 m, radius0.0603 m, body ownership, units and exact legacy discrepancy locations/consumers.
- SOURCE-SUPPORTED limitation: report PDF/page and leg/wheel per-side versus combined definitions are absent from supplied local artifacts. Resolve with report/CAD/BOM before generating a report-labelled plant; never silently double masses. All inertias remain ASSUMED, including geometry-derived rod inertias. Null tensors mean unknown, not zero.
- INFERRED: first study uses a newly hashed reduced planar model at fixed0.16 m equivalent leg, explicitly an ASSUMED reduction, not a physical five-bar. Keep old configs/results/gains under old hashes. Re-synthesize LQR for the new model; old160/160 is not new-model evidence.
- SOURCE-SUPPORTED: current `sim/fivebar/model.py::Plant.controls` and `sim/fivebar/geometry.py::Geometry.wrench` implement a separate planar virtual-work adapter; `sim/rl/v2.py` does not use it. Neither is a complete two-leg 3D rolling-contact model or validated DM actuator envelope.

## ONE first scientific experiment: G1

**Hypothesis [INFERRED]:** a learned bounded velocity-reference governor above fixed delay-aware LQR, trained at2–5 ms sensor-to-actuation delay, improves strict tracking under unseen6–10 ms delay without degrading ordinary-delay precision. The result, including a negative result, concerns generalization of this supervised command interface on an assumed plant; it is not a v2 reward retry or a novelty claim.

**Arms [INFERRED]:** (A) frozen LQR + deterministic command ramp; (B) exactly the same LQR/ramp + governor. Only B learns. No direct-torque arm, terrain, hops or backend comparison in G1. No reused v2/v3 weights. Baseline synthesis/development≤2 workstation-hours, recorded separately before release; use existing permitted fixed operating-point synthesis, never reproduce the owner's schedule. Baseline gains stay fixed across tested delays; design at5 ms, with a causal predictor using timestamped history and known delay in both arms.

**Interface [ASSUMED design, not implemented]:** 500 Hz plant/LQR,100 Hz governor. Policy returns one normalized scalar a∈[-1,1]; proposed Δv=0.03a m/s, slew≤0.1 m/s²; total accepted speed≤0.2 m/s. LQR receives original x reference and v_cmd+Δv (no cumulative position-reference drift); scoring always uses the original command. Zero a reproduces baseline bit-for-bit in deterministic paired traces. No torque/gain output. Shared causal observation: six estimated tracking errors, commanded speed, last five accepted Δv samples, last five command pairs, causal torque estimates and measured request age; no true state, future delay or push phase. Baseline may ignore inputs; no privileged actor observations. Freeze scaling/filter/history before final runs.

**Task [ASSUMED]:** 10 s episodes, x_ref(0)=0; ramp speed linearly0→command over first1 s; x_ref(t)=integral of that ramp. Initial x,leg angle,rates zero; pitch±5°. Signed6 N horizontal body-COM pushes at3.0 s for0.15 s. Training draws commands0,±0.1,±0.2 m/s, pitch uniformly±10°, push uniformly±6 N and delay uniformly2–5 ms, independently per episode. Train only on nominal assumed inertia/COM/lag, with declared IMU noise. Record every sampler/RNG stream.

**Frozen final panel [ASSUMED]:** exactly200 cases =5 delays{2,5,6,8,10} ms ×5 commands{0,-0.1,+0.1,-0.2,+0.2} ×2 pitches{-5,+5}° ×2 push signs ×2 variants. Variant0: nominal inertia/COM,5 ms lag, pitch noise SD0.1°, gyro0.01 rad/s. Variant1: all COM pitch/rolling inertias×1.2, body COM×1.1,8 ms lag, noise SD×2. Masses unchanged; friction absent in this no-slip reduction. Lexicographic order as listed assigns noise seeds3000–3199; same noise sequence/case for all arms/seeds. Reference=80 cases (40/delay), difficult=120 (40/delay); difficult weights1/3 each, no post-hoc reweighting. Development uses a separate20-case list with seeds2000–2019: delays{2,5,6,8,10} ×commands{0,+0.2} ×push signs, pitch+5°, variant0. Freeze both lists/hashes before learning; never tune against final cases.

**Timing [INFERRED]:** implement timestamped zero-order-held command events inside each2 ms integration interval; split integration at arrival times, including5 ms=2.5 ticks. No rounding5→6 ms. Predictor must use the same fractional delay semantics. Validate actual event times from traces; refine any future contact timestep jointly for all controllers.

**Metrics and pass criteria [ASSUMED, frozen before pilot]:**

| Metric | Definition / required threshold |
| --- | --- |
| Survival | No numerical failure, body collision, abs(pitch)>30°, abs(leg)>30°, or abs(x−x_ref)>1.5 m; ≥95% in each seed. Numerical failures also invalidate the run. |
| Stationary strict | All six errors continuously within (0.02 m,0.03 m/s,1° leg,1° pitch,0.05 rad/s each angular rate) in final1 s; first sustained1 s recovery within5 s of start and push end. |
| Moving strict | Final2 s RMSE(v−v_cmd)≤0.03 m/s and RMSE(x−x_ref)≤0.02 m; max absolute leg/pitch≤1°, angular rates≤0.05 rad/s throughout that window; same recovery deadline relative to these instantaneous bounds. |
| Overall engineering | Strict≥95% of200 cases for EACH of five seeds, with no delay stratum >5 percentage points below LQR; all accepted request/actuator caps respected. |
| Primary research endpoint | Difficult-stratum strict gain B−A≥10 percentage points averaged over five training seeds; lower two-sided95% paired seed-level t interval (df4)>0. Overall/reference strict regressions≤5 points. All engineering criteria also required. |
| Precision E | Mean over final2 s of (1/6)Σ(e_i/t_i)², using original moving x/v references and the six tolerances above; report per seed/stratum, including failures with separate failed counts, never survivor-only superiority. |
| Secondary diagnostics | Recovery time, x/v RMSE, peak angles/rates, ∫τ²dt, peak/saturation time,500 Hz torque slew,100 Hz request slew, rejected/clipped requests, policy inference time. No endpoint switching to rescue failure. |

INFERRED: compare paired case outcomes and five seed differences, not1000 independent policy replications. The five-seed interval is imprecise and baseline-shared; report each seed plus interval/limitations. If development LQR≥95% in every stratum, stop for no headroom; if final LQR reaches that ceiling, report it and do not change tasks/metrics after seeing results.

**Learning [ASSUMED]:** five independent seeds0–4, one1M-transition final policy each;5M total at100 Hz=50,000 simulated seconds. PPO: two64-unit tanh layers, Gaussian scalar clipped to[-1,1], initial actor mean zero, initial normalized SD0.05; Adam lr3e-4, gamma0.99, GAE0.95, clip0.2,10 epochs,8 envs×250 steps/update, batch250. Save observation normalizers; no reward clipping/normalization or best-checkpoint selection. Zero-residual identity uses deterministic mean, not stochastic samples.

Let q=e/t in order(x,v,leg,pitch,leg_rate,pitch_rate). Reward/action =1−q_x²−q_v²−0.5(q_leg²+q_pitch²)−0.25(q_leg_rate²+q_pitch_rate²)−0.01Σ(τ/τlim)²−0.05((a−a_prev)/0.1)²−0.1a². A2 cm error costs1; position weight2500 m⁻²=625×v2's4. This arithmetic is SOURCE-SUPPORTED; benefit untested. Fall penalty −ceil((10−t)/0.01) is ASSUMED; unbounded running costs mean it cannot guarantee against cost avoidance. Score failure independently. Log every reward sum, return, episode length, E, strict count, recovery and action mean/SD versus transitions.

**Pilot [INFERRED]:** after measured portability, run exactly one seed42 development pilot, stop at FIRST of20 min or1M transitions. Stop rollout/update exceeding60 s; incomplete updates are not completed experience. Target≈200k steps within that cap; plot return/episode length versus steps. Require last5-min mean return>first5-min mean return with no shorter mean episode length, plus survival regression≤5 points and E increase≤10% against paired development LQR; noise-on/off diagnostics may vary noise alone with fixed cases. Count all pilot experience separately, never warm-start finals. Pilot FAIL ends this recipe without seed/reward fishing. Check deterministic zero-governor/LQR traces before pilot; fix actual plumbing errors only.

## One unattended12 h CPU run on borrowed i7-11800H

- SOURCE-SUPPORTED (owner):8 cores/16 threads,32 GB; Mac v2 reference≈450 s per process. Unit/workload transfer is not independently verified; historical v2 batch17.51 h is a different receipt, not a normalization of that per-process reference.
- ASSUMED forecast: conservatively budget450 s per100k transitions for a single v2-like job (work-unit attribution ASSUMED pending receipt), then1.2× Windows/governor overhead:450×10×1.2=5,400 s per1M-transition job. Five SERIAL jobs=27,000 s=7.5 h; use one PPO parent,8 environment subprocesses, one BLAS/PyTorch thread each; no concurrent experiments/rendering. CPU only, RAM≤24 GB. Do not assume8× speedup from8 cores. Confirm the reference work unit locally; the measured G1 throughput gate below overrides this forecast.
- ASSUMED allocation (minutes):0–15 restore/host receipt;15–35 one pilot;35–65 paired checks/baseline;65–515 five jobs≤90 min each;515–635 all final evaluations;635–665 export/reload;665–720 contingency. Baseline design and bundle preparation happen off-site; no unattended debugging or tuning.
- INFERRED gate from smoke/off-site measurement: sustainable F≥1M/5400=185.2 completed transitions/s including updates/checkpoint copies, one update≤60 s, and full paired evaluation projected≤120 min at measured evaluation speed. Use measured G1 F, not legacy F, to certify fit. Reforecast from actual receipt; if it does not fit, NO-GO rather than quietly reducing seeds/budget.
- INFERRED: stop each job at90 min and mark PARTIAL if1M unfinished; a failed/numerically invalid job stops the queue. Never compare incomplete/unequal budgets as final. Wall-clock watchdog starts export by minute635 and exits by720; bounded updates and backup watchdog required. No sleep/shutdown/USB removal during run, thermal throttling logged.
- INFERRED: count12 seat/CPU wall-hours plus actual process CPU-hours, evaluation, prep/pilot hours and0 GPU-hours. This replaces the three-visit promise. Historical2–6 GPU-h was a reservation within12 GPU-h ceiling, not extra12 h; any later GPU study counts cumulative device-active time and CPU seat-hours separately, with no payment authorized here.

## Safe boundary and later task ladder

- SOURCE-SUPPORTED: `sim/parity/student.py::gain_schedule` is owner-only: no edit, duplicate implementation, scheduling surrogate or bypass. G1 stays at a fixed leg operating point. Direct torque, if studied later at matched100 Hz with500 Hz baseline/plant, is simulation-only and has no hardware route.
- INFERRED proposed physical interface: Pi sends versioned {sequence,timestamp,mode,Δv,confidence}; STM32 authenticates format/mode, checks finite/range/age in one clock domain, clamps magnitude AND slew, owns reference generation, balance, joint mapping, speed/thermal/current limits, watchdog and fallback. ASSUMED candidate freshness limit30 ms; rejection/timeout removes learned correction and retains baseline. Caps alone are insufficient; this design is not implemented or authorized for motors.
- SOURCE-SUPPORTED: legacy2/4 N·m pair caps,5 ms lag and COMs are ASSUMED, not DM specs. G1 may use these disclosed simulation limits; physical claims require joint torque-speed/thermal envelopes, axial loads and both contacts, with adapter sign/unit/order verification.
- INFERRED later ladder only after G1 review: flat tracking →10/20 mm steps →20/40 mm hops, full floating-base3D two-five-bar model with rolling contacts and validated mapping first. Later proposal: five fresh seeds/learned arm,10M each including curriculum (100M/rung for residual/direct); no fixed reservation until measured F fits. Baseline effort≤2 h/rung, all pretraining/debug experience disclosed.
- ASSUMED later flat criteria retain G1 six tolerances,±5/±10° starts,0/±0.1/±0.2 m/s,6 N×0.15 s pushes and≥95% strict. Use exactly enumerated200 cases before training; no unspecified factor lists or selected videos.
- ASSUMED step panel: direction{up,down}×height{10,20}mm×speed{0.1,0.2}m/s×friction{0.5,0.8}×delay{2,5,10}ms×4 variants{nominal,noisy,payload,inertia}=192 +8 nominal anchors (2 directions×2 heights×2 speeds,friction0.8,delay2 ms). Difficult=64 delay10 ms cases, equal weights. Variants change only: nominal; noise SD×2; body mass/inertia×1.1; all COM inertias×1.2, respectively. Other settings match nominal. Enumerate seeds3000–3199 in displayed factor order before release.
- ASSUMED step baseline=LQR+slow/extend/cross/settle with identical terrain input age/noise; strict≥90%/seed, both wheels≥0.30 m beyond edge by8 s, no fall/body collision, peak roll/pitch≤15°, final2 s speed RMSE≤0.03 m/s,pitch≤2°, no envelope/joint/singular-closure breach.
- ASSUMED hop panel: height{20,40}mm×pitch{−2,+2}°×friction{0.5,0.8}×delay{2,5,10}ms×8 variants=192 +8 nominal anchors (height×pitch×friction,delay2 ms); difficult=64 delay10 ms cases, equal weights. Eight variants are the full product noise SD scale{1,2}×body mass scale{1,1.1}×all COM inertia scale{1,1.2}; other settings nominal. Enumerate seeds3000–3199 in displayed order before release. Hop rise=max(base z)−base z at settled pre-crouch stand, not from crouch bottom.
- ASSUMED hop baseline=deterministic crouch/thrust/retract/settle+grounded LQR/flight-landing modes; strict≥90%/seed, both wheels airborne≥20 ms, requested rise reached,recontact≤3 s,settle≤5 s, final1 s position≤0.02 m,pitch/roll≤2°,speed≤0.03 m/s; no collision/fall/envelope/closure breach; phase timeout1 s fails.
- SOURCE-SUPPORTED: [jump lesson](../../docs/lessons/05_wbr_jump_sequence.md) gives crouch0.08 m,thrust0.21 m,retract captured stand,settle; counters≥10 are scheduling-dependent, not contact proof; left `leg_right_set` ambiguity unresolved. INFERRED: verify reach/contact/timeout, use phase prior only.
- ASSUMED later research benefit retains≥10-point difficult strict gain, positive lower95% seed-level interval, overall regression≤5 points and all engineering thresholds; roll/pitch>30° or body collision=fall. Terminal failure fails unfinished objectives. No load safety claim without radial reaction data.

## Borrowed-laptop GO/NO-GO — every box must be true

All boxes are INFERRED prerequisites; unchecked means NO-GO for the12 h scientific job. No Windows execution was performed in C1-T12.

- [ ] Report page/assembly membership resolved, new model/manifest hashes frozen, all inertias/COM/lag/limits explicitly ASSUMED; no old gains/results relabelled. Pi board/runtime memory identity reconciled separately (3.9 GiB runtime versus claimed8 GB); no Pi sizing assumption.
- [ ] G1 runner, supervised reference adapter, fractional delay, frozen train/development/final cases, LQR and zero-action parity actually run off-site; source/model/protocol/normalizer hashes and exact launch/evaluate commands included. Current `research/rl/bundle` is legacy v2 only: it cannot launch G1 unchanged.
- [ ] Laptop owner permits extracted Python/uv/scripts, local writes/USB; exact Windows x64 version, free local/USB space, power/sleep/automatic-wipe times known. No admin, global PATH/registry/activation, policy changes, driver update/reboot, compiler, downloads or network needed at runtime.
- [ ] One USB directory AND identical ZIP contain pinned standalone Python build +uv.exe, licenses, hashed exact CPU wheel lock and all transitive MuJoCo/NumPy/SciPy/Gymnasium/SB3/PyTorch/serialization wheels, frozen source+patch, models/manifest, protocols, baseline, launch/setup/smoke/train/resume/export entry points and hash manifest. Recreate local venv offline with `--no-index --find-links --require-hashes`; never relocate a prebuilt venv. Cache/temp local; downloads disabled. Exact ABI/runtime dependencies tested.
- [ ] CPU MuJoCo+CPU PPO headless is default. CUDA PPO alone does not accelerate ordinary MuJoCo. Isaac Lab is dropped from mandatory payload. MJX CPU optional only if separately tested/locked; native Windows CUDA JAX unsupported per local review; existing permitted WSL2 only, no WSL installation. Warp optional only with working bundled WBR adapter and actual pinned wheel/driver test. Every backend switch gets new identity/semantic verification, never pooled resume curves.
- [ ] **15-minute Windows smoke of `research/rl/bundle` passes BEFORE overnight use**, on this borrowed machine with network disabled; retain exact commands/errors/timings. The existing legacy launcher is `run.bat 0`: its own setup+real PPO smoke remains bounded at10 min; zero-minute timed training must not turn this check into a scientific run. This ticket does not modify that launcher. G1 release must additionally substitute its frozen source/protocol and pass the same lifecycle.
- [ ] Smoke0–2 min: extract/verify hashes, offline setup, host/version/path/startup receipt.2–5: real seed42 flat rollout +≥1 complete optimizer update, finite losses/components.5–7: USB verified checkpoint/clean stop/fresh-directory restore;7–9:≥1 further update, counters increase and deterministic actions agree within1e-6, optimizer/RNG/normalizer restored.9–10: export/reload/receipt (existing10-min deadline retained).10–15: separate interrupted-process recovery from newest verified checkpoint, G1 LQR/zero-action trace comparison≤1e-9 on deterministic state/command, G1 throughput/update/RAM/thermal receipt. Missing ANY window fails; no silent extension. Legacy lifecycle success alone does not certify G1 parity or throughput.
- [ ] Five-wall-minute checkpoints at completed updates (≤60 s/update), controlled stop and exit: save actor/critic, optimizer/scheduler, normalizers, Python/NumPy/torch/device RNGs,sampler/curriculum,rollout position,steps,simulated seconds,updates,all hashes/device receipt. Save simulator state if supported; otherwise episode reset with explicit discontinuity. Versioned USB write→hash/reload verification→completion marker; preserve previous verified version, log copy time/checkpoint age. Newest complete hash-compatible restore only; reject mismatch/skip corruption, no bitwise future-trajectory claim.
- [ ] Measured G1 F/evaluation/update/RAM meet12 h bounds; locked no-sleep power and thermal behavior tested; watchdog/STOP and newest-checkpoint recovery exercised. USB capacity includes all retained versions, two owner-controlled copies verified where available. Final30 min reserved for export/reload; USB failure stops training and preserves error/evidence.

## Transfer, stopping and completion

1. INFERRED: reconcile CAD/BOM, assembled masses, COM, linkage reach/signs, loaded radius, IMU/encoder frames, limits and sensor-to-torque age/jitter; inertia sensitivity precedes physical inference.
2. INFERRED: compare kinematics/static loads/lag/delay to recorded or separately authorized bench data; verify joint order, DM CAN encoding/saturation, axial reactions and both contacts.
3. INFERRED: export frozen actor+normalizers/history; compare Python/export numerics and STM32 supervisor outputs with replay/processor-in-loop under realistic Pi sensing load, no motor authority; measure worst-case scheduling/inference.
4. INFERRED: inject stale/NaN/range faults, restart/loss/disconnect; demonstrate MCU rejection, retained balance/fallback before separately authorized secured flat-floor trials. Steps/hops need later explicit scope and repeated hardware evidence. SOURCE-SUPPORTED: STM32 always owns balance/safety; no flashing/actuation authorized here.
5. INFERRED: pilot failure closes G1 recipe; insufficient throughput closes this compute route; completed negative five-seed result closes this task/hypothesis, not all RL. Retain all failures/partial checkpoints. No extra seed,reward retune,best-checkpoint or endpoint switch. Larger task needs distinct preregistration/review.
6. SOURCE-SUPPORTED: accelerator purchase only after X1 report; X2/S1 or a successful smoke do not authorize buying. INFERRED: RL remains a simulation track; portability is infrastructure evidence, not scientific novelty or transfer.
7. INFERRED: completed milestone report includes hashes/assumptions, all five seeds and baseline, paired cases/intervals, curves/components, actual seat/CPU/GPU hours, failures and limits; Claude reviews only that completed milestone. Sessions2–3, ten-policy completion and step/hop execution are not promised.

## CHANGE/DROP traceability (INFERRED implementation of review)

| Review §1 row | Applied here |
| --- | --- |
| owner-only schedule | Fixed operating point; no schedule reproduction/bypass |
| direct torque/rates; direct-policy arm | G1 reference governor only; later direct comparator simulation-only, matched100 Hz |
| report manifest | YAML ownership/units/page blocker/inertias plus legacy file:line audit |
| five seeds /10M | G1 five×1M; later10M/arm proposal conditional on measured throughput |
|200 cases; rung metrics/interval | Explicit G1 allocation, equal difficult weights, moving path/E and hop stand-rise definitions |
|500 Hz / fractional delay | Timestamped intra-tick arrival integration |
| early abort | No cost-avoidance guarantee; failure scored separately |
| VMC/speed limits | Actual separate controls/wrench adapter identified; legacy pair caps disclosed |
| pilot/components | One first-bound pilot, curves/improvement, E,60 s update stop |
| Warp; Isaac DROP | Tested adapter/driver prerequisite; Isaac excluded from mandatory bundle |
| portable bundle | Offline exact payload, five-minute verified checkpoints, new-directory resume/export |
| three sessions | Portability measured first; one budgeted12 h scientific batch, later visits unpromised |
| stopping/compute | Recipe-only closure; CPU seat-hours,2–6 reservation within12 GPU-h ceiling |
| transfer/purchase | Staged bench/replay/fault validation; X1 prerequisite |
| AGV references DROP | No RobStride/micro-ROS in WBR contract |
