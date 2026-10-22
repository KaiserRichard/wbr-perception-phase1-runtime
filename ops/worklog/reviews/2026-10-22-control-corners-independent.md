# Independent control-corners review — 22 October 2026

**Complete; no material disagreement.** Independent review of [PR119](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/119), following [PR118](2026-10-22-control-margins.md). The full original review is copied verbatim to [review-detailed.md](/Users/quockaiser/wbr-evidence-archive/sim-control-corners-20261022-01/independent-k/review-detailed.md). Evidence root: `E=/Users/quockaiser/wbr-evidence-archive/sim-control-corners-20261022-01/independent-k`.

**Provenance.** Checked source commits: combined `92d925ba7be174284d72ab9d7ad499d28bd8a733`; ramp `6a78f4bbd2b8200d62fd18356e66ad7e6ec60e43`; reporting-only `fdfcb8138ceaf3427c221bce9a9771437c88e00c` inspected separately. Own receipts are `$E/<label>/execution.json`, with exact commands, source commit, exit status and adjacent logs/checkers: `native-02`, `replay-01`, `replay-comparison-01`, `recovery-map-01`, `summaries-final`, `final-receipts`. The archive retains reproduction commands and failed attempts. All final checkers exit0; `replay-01` checker exit1 was tuple/list comparison after successful physics; persisted comparison passed without rerunning.

**Controller/dynamics.** Nominal 2 ms DARE gains remain fixed across combined conditions/seeds. Native checks confirm mass and COM-inertia scaling without geometry changes, six-measurement controller isolation, previous-clipped-command observer ordering, separate physical delay histories, wheel reaction mapping and completed-case reuse. Scheduled ramps receive exact prescribed length; frozen gains use initial length. Neither controller receives physical torque/model-error truth. Moving-length dynamics retain velocity, acceleration and curvature coupling.

**Motor virtual work.** For motor angles $a=(a_A,a_E)$, $\beta=\theta-\phi+\pi/2$ and $J=\partial(L,\beta)/\partial a$,

$$
\tau=J^T[F_{ext},-T_h]^T,\qquad \Delta\tau^T\dot a=F_{ext}\dot L.
$$

$T_h$ is virtual hip torque; $\Delta\tau$ is the extension-only motor contribution. Motor torques are N·m; $F_{ext}$ is N, $\dot L$ m/s, $\dot a$ rad/s and power W. Native extension projection is $[0,0,0,F_{ext}]$, with coordinate-force units **[N, N·m, N·m, N]**. Native power residual ≤9.45e−10 W; independent motor-angle differences agree within 4.83e−10 N·m. At t=2.35 s of the 1 s extension, same-stage total A/E torques are [−0.962940,1.554010] N·m; full inputs and short-segment sensitivity checks remain archived.

**Evidence.** Exactly one saved 10 s case was independently replayed: L=0.20 m, delay=8 ms, mass/inertia=2×, δ=0.5, push=36 N, seed=3, identical committed source/config/saved K. **PASS**; every serialized metric equal; observer/control/interval CSVs, condition JSON and model XML byte-identical. No other full rollout was repeated.

From saved raw results, all **30 reduced cases** reproduce strict checks, peaks, recovery, saturation and effort: seeds0–4 each 6 PASS. Each seed's six cases share all 5,001 noise samples; timestamps differ by ≤1.78e−15 s. Original production exit1 was exact timestamp-bit comparison; the reporting fix preserved evidence without new rollouts. The original ramp's 2–10 s window matches 8,001 finest endpoints; initial recovery overlaps that window.

All **12 upright ramps PASS**: six scheduled/six initial-length-frozen, **seed0 only**. All **36** inclusive before/moving/after windows, recovery/final criteria and **six timestamp/noise pairs** reproduce. Moving peaks exclude initial conditions and separate leg/body angles. Independent geometry reconstruction matches all 512,000 same-stage motor records within 1.34e−15 N·m; simultaneous maximum |A|+|E|=2.451992 N·m. Final producer summaries/comparisons agree.

**Limits/recommendation.** Accept scoped simulation evidence. Reduced state-error/RMSE integrals were **not independently recomputed**; whole-grid warning diagnostics were **not independently regenerated**. Held interval-mean actuator torque within RK stages is a finite-step approximation. Ideal-extension loads do not establish motor feasibility: motor/gear/current limits remain **UNKNOWN**; the virtual 4 N·m hip-pair cap is not an individual motor rating. Five reduced sensor seeds and seed0 ramp pairs establish no generalization, continuous robustness, hardware transfer, scheduling necessity or superiority. Conductor alone checks current-head green CI and merges.
