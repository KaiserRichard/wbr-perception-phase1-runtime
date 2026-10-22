# V3 residual pilot result — 2026-10-22

**FAIL — seed 42.** One or more pre-declared engineering screens failed. Simulation on the assumed plant; one pilot attempt.
Archive: [sim-v3-pilot-20261022-01](/Users/quockaiser/wbr-evidence-archive/sim-v3-pilot-20261022-01); source `14df6df271d411c90461fa7cd19938153de2deff`. Implementation [PR126](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/126); Claude approval [PR127](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/127).

**Saved-v2 diagnostic:** signed residual/cap pairs (axis 0/1) at physical upright; LQR columns are signed mean and mean absolute residual/cap on saved inputs.

| V2 seed | Upright 2 ms | 3 ms | 4 ms | 5 ms | LQR mean | LQR mean abs |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 0.2940184/0.09846598 | 0.3351827/0.03234971 | 0.1629317/0.01777953 | -0.003447663/0.06333885 | 0.1543501/-0.05364602 | 0.4724166/0.1497702 |
| 1 | -0.3866981/0.02069759 | -0.008605269/-0.02820325 | 0.4225276/-0.08593278 | 0.7023451/-0.03248987 | -0.07560007/0.02296402 | 0.2715093/0.1197333 |
| 2 | -0.02597606/0.1489505 | 0.2091306/0.1333448 | 0.3232159/0.1417201 | 0.3163522/0.2083799 | 0.2337602/-0.01349543 | 0.4104114/0.1308245 |
Saved LQR input counts, seeds 0/1/2: 1000/1000/1000. Frozen normalization; offline queries, not residual-controller rollouts.

**Run:** `COMPLETE`, exit 0; stop `target_transitions_and_minimum_duration`; 260,000 aggregate transitions / 130 completed updates / 256 completed episodes (8 environments, 2,000 transitions/update; target 200,000). Train / evaluation / budget / recorded wall seconds: 460.1012/420.7304/603.4633/890.6843; supervisor wall including startup/cleanup 899.2273 s. Minimum-duration overshoot / maximum-budget overrun seconds: 3.463328/0.
Budget starts after snapshot-0 preparation, includes the 100k evaluation and update overhead, excludes final evaluation; stop at the first complete update reaching both 200k/600 s or reaching 1,200 s. Initialization parity: PASS; checkpoint reload: PASS.

**Development snapshots:** fixed seeds 2000/2001 × delays 2/3/4/5 ms × balance/push; frozen statistics. $E=\operatorname{mean}_{cases}\max_{i,t\in[9,10]}|e_i(t)|/t_i$.

| Snapshot | Rows / unique / full 10 s (each /16) | Strict /16 | Survival /16 | Leg-rate violations /16 | E |
|---|---:|---:|---:|---:|---:|
| snapshot-0 | 16/16/16 | 16 | 16 | 0 | 0.2924333 |
| snapshot-100k | 16/16/16 | 16 | 16 | 0 | 0.4472931 |
| final | 16/16/16 | 11 | 16 | 0 | 0.8260701 |

**Saved-metric failure attribution (closeout):** compare `final/development.json`'s
`final_window_max_abs_error` against `sim/rl/protocol.json` tolerances; no rerun.
Only the two 2 ms balance cases breach a final-window tolerance, both position
(limit 20 mm). The remaining three failures hold all six tolerances over the
final second but exceed the separate 5 s recovery deadline.

| Delay / scenario / noise seed | Final-window position maximum | Failure / recovery after event |
|---|---:|---|
| 2 ms / balance / 2000 | 21.800625 mm | Position; no qualifying recovery |
| 2 ms / balance / 2001 | 20.869877 mm | Position; no qualifying recovery |
| 5 ms / balance / 2000 | 5.521203 mm | Recovery 5.288 s > 5 s |
| 5 ms / balance / 2001 | 7.165076 mm | Recovery 8.988 s > 5 s |
| 5 ms / push / 2001 | 8.553488 mm | Recovery 5.838 s > 5 s after pulse end |

Thus position explains two of five strict failures; saved summaries do not
identify which state delayed recovery in the other three. Final-panel maxima
for the other five states are all below tolerance. The reported 0.126773 Nm
wheel value (`0.3169334 × 0.4`) is the last rollout's deterministic **mean
absolute** residual, not a signed stationary torque measurement. The constant
bias mechanism is Claude's interpretation, not an additional measured result.

**Owner disposition:** FAIL accepted; result PR128 merged. Stop this v3 line;
no reward tuning, retry, full training or new RL experiment. Claude review
PR129 remains the owner's merge. Recommendation: prioritize hardware data;
any future RL proposal should use cases where the LQR baseline fails (the
review mentions 45 N push / 10 ms delay), with separate authorization.

**Screens:** complete/nonduplicate/full panels PASS; initial strict=16 PASS; final strict=16 FAIL; final survival=16 PASS; leg-rate 0 ≤ 0 PASS. E-end 0.8260701 ≤ 0.9E-100k=0.4025638 FAIL; E-end ≤ E-zero=0.2924333 FAIL.

| Completed-episode window | Episodes | Mean raw return | Mean length (policy actions) | Mean alive / precision loss / fall |
|---|---:|---:|---:|---:|
| First: end step ≤ 50,000 | 48 | 583.6263 | 1000 | 1000/416.3737/0 |
| Last: end step > 210,000 | 48 | 659.8651 | 1000 | 1000/340.1349/0 |
Return last > first: **PASS**; length last ≥ first: **PASS**; ≥100k transitions and both windows nonempty: PASS. Window membership uses episode-end aggregate transitions; raw returns precede normalization and timeout bootstrap.
Mean allocated episode losses, first→last: x 81.87387→158.3967, leg 49.12975→31.15524, body 18.46165→31.25473, xdot 24.83746→20.54127, legdot 83.03804→41.39258, bodydot 72.6599→27.9479, command 86.37299→29.44646. No residual penalty.
Return / precision-loss reconstruction maximum absolute errors: 1.932676e-12/1.080025e-12.

**Exploration:** axis 0/1 pairs; residual caps 0.4/0.8 Nm.

| Point | log-std | Gaussian SD/cap | Sampled mean abs residual/cap | Deterministic mean abs residual/cap |
|---|---:|---:|---:|---:|
| Initial theory | -1/-1 | 0.3678794/0.3678794 | expectation 0.2927907/0.2927907 | 0/0 |
| First update (2000) | -1.013713/-1.014751 | 0.3628691/0.3624927 | 0.297929/0.2960772 | 0/0 |
| Last update (260000) | -1.734443/-2.04759 | 0.1764985/0.1290455 | 0.3496092/0.1701051 | 0.3169334/0.1330655 |
Initial Gaussian SD=0.1471518/0.2943036 Nm; initial sampled expectation includes action clipping. Log-std/SD are post-update; residual magnitudes summarize the preceding rollout. First-update values are not timestep-zero measurements.

Curves: [episode return/length versus transitions](/Users/quockaiser/wbr-evidence-archive/sim-v3-pilot-20261022-01/pilot/learning-curves.svg).
Verification: recorded 35 tests PASS in 20.545 s; diagnostic/pilot exit 0 ([test/diagnostic receipt](/Users/quockaiser/wbr-evidence-archive/sim-v3-pilot-20261022-01/session-context.json), [pilot command/receipt](/Users/quockaiser/wbr-evidence-archive/sim-v3-pilot-20261022-01/pilot-execution.json)). Stdlib recomputation of saved panels/windows agrees with recorded summaries/screens; recorded screens.pass=false. Return is a weak screen; these outcomes provide no causal, significance, PPO/LQR superiority, or hardware result. Held-out 1000–1019 untouched; no checkpoint/seed selection or full-run launch.
**For Claude:** review this one-seed pilot and its external evidence against the declared screens before any further experiment.

## Claude review (2026-10-22)

**Decision: FAIL accepted as reported (PR128 merged, CI green).** The run followed the protocol: one seed, fixed budget, no early stop, no checkpoint choice, parity and reload PASS, reward terms reconstruct the return to 1e-12. The verdict stands on the pre-declared screens.

**What the numbers say.**
- **v2 bias confirmed.** The saved v2 residual policies output large non-zero means at physical upright (up to 0.70 of cap, sign varying by seed and delay). The v2 failure mode was a learned offset, as hypothesised.
- **v3 learned a new offset.** By the end, the deterministic mean |residual| is 0.32 of cap on axis 0 (wheel, 0.13 N·m) and 0.13 on axis 1, starting from exactly 0. The training-loss breakdown shows the trade it made: position loss roughly doubled (82 → 158), while leg/body rate and command losses fell to between a third and a half. Total return rose (584 → 660), so the optimizer did what the reward asked.
- **Why that breaks strict acceptance.** The LQR has no integral term, so a constant wheel-torque offset settles into a constant position error. A steady x offset costs the bounded reward little per step, but strict acceptance needs every state inside tolerance over the last second. That matches strict 16 → 11 and E rising 0.29 → 0.45 → 0.83. *Inferred, not shown:* the report should list which state is outside tolerance in the five failing cases; I expect x.
- **The fall penalty never acted.** Every training episode ran the full 1,000 actions; there were no falls. The termination-incentive fix was correct but untested here.
- **Leg-rate violations are 0 at every snapshot.** v2's failure mode did not recur, but this is one seed, not a causal result.

**Recommendation: stop the v3 residual line here.** Do not tune β, Q or the seed to rescue this pilot. That would be fitting the screen. The deeper issue is the one the proposal already named: LQR passes 16/16 strict on these cases, so a residual has no headroom on this panel and can only trade one error for another. If RL is resumed later, give it a problem LQR fails: the stress cases from PR115 (45 N push, 10 ms delay, 8× mass). Judge it on recovering those, with a matched LQR-only control and a fresh pre-declared protocol. Until then, hardware data (motor/gear, mass/geometry, loop latency) is the higher-value work.
