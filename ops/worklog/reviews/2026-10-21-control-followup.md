# Control follow-up — 21 October 2026

Owner resumed control work, prioritizing j/k. Both were initially busy; after fresh idle/quota checks, **j completed videos and gain synthesis/fitting; k completed the mechanics study using Astra Ultra**. No unrelated session was interrupted. Owner explicitly allowed j for these control tasks; d/h remain excluded, g/k share one pool. Camera ownership, student gain exercise and training recipe stayed unchanged.

| Work | Actual result / review |
|---|---|
| Saved PPO comparison, PR95 | Table and seven SVGs; counts independently checked: direct strict59/800, survived760/800; residual0/480, survived480/480; one reused LQR reference. Missing legacy learning curves remain unavailable. |
| B3 videos, j, PR97 | Two 640×480 MP4s, 300frames/10s each. Conductor independently decoded both and inspected six frames. Illustrations, not acceptance tests. [Run note](2026-10-21-lqr-clips.md). |
| A4 mechanics, k, PR99 | All9 dt/epsilon cases executed in150.709s; finite results, no numerical failures. Open-loop tilt stops at0.29575–0.296s, not5s of balance. Conductor checked identities/accounting and independently reproduced one coarse case exactly in6.96s. [Run note / PR99](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/99). |
| A3 gain schedule, j | All76 assumed-model designs and four degree3 fits completed. Conductor independently checked all matrix shapes/finite values and reconstructed entry-wise fit residuals. **400 nonlinear cases UNRUN.** [Run note](2026-10-21-gain-sweep.md). |

The initial A4 attempt hit its120s wall budget and produced no final JSON; retained separately. k's later run used a fresh output and600s cap. Initial A3 command/setup errors were retained before correction. No parameters, numerical thresholds or polynomial degree were tuned. Backend environment unchanged; FFmpeg was installed in an isolated dependency directory.

Evidence roots under `~/wbr-evidence-archive/`:
- `sim-control-followup-20261021-01/comparison/`: comparison.md/csv, report.json, seven SVGs, generated with `python3 -m sim.rl.reporting --v1-aggregate <v1>/evaluation/aggregate.json --v2-archive <v2> --out <new-directory>`.
- `sim-lqr-clips-20261021-01/`: balance/push MP4s, metadata and contact sheet; source235550e, existing `sim.video` CLI.
- `sim-fivebar-dynamics-20261021-01/`: nine-case JSON and run receipt; source140a11b, existing `sim.fivebar.compare` CLI.
- `sim-gain-sweep-20261021-01/`: sweep/fit manifests and retained attempts; source140a11b, existing `sim.gain_schedule` CLI.
Exact commands/configs and limitations are in the linked run notes. No media or generated gains entered git.

**Recommendation:** retain the reduced baseline: five-bar mass and wheel-reaction discrepancies persist under the sampled refinements. A3's0.12–0.30m hypothetical rigid-leg family exceeds A4's~0.211m reach; no transfer claim. The400-case nonlinear study remains pending. Future RL requires the reviewed pilot recipe and episode-length/return recording; no v3 training was launched.
