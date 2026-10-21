# Camera PR93 follow-up — open-loop endpoint, replay agreement and timing tails

2026-10-21. Owner-authorized Mac-only continuation; no lab/Pi needed.

## Corrected interpretation

- Of the original three runs, only replay1 provides a no-loop/no-merge/no-loss
  open-loop figure: 1.83cm over14.27m. The owner's return-position/heading error
  was not measured. Claude's estimate of a few centimetres is an inference, not
  a calibrated uncertainty bound; do not claim0.13% accuracy.
- Replay2's loop correction and replay3's loss/new map/merge make their small
  endpoints unsuitable as drift figures. Original tracking-loss result:
  **1of3runs lost tracking**. Different map histories are not repeatable tracking.
- Paced15trackedFPS only shows keeping up with1× playback. The no-drop runner
  absorbs overruns; neither these counts nor tails directly measure live drops.
  Every runtime/timing result here is Intel Mac/Linux x86_64, not Pi performance.

## One fresh replay with loop closing disabled

Hypothesis: remove place-recognition correction/merging and retain one continuous
start-to-return map, so the endpoint is not pulled back by loop/merge correction.
The conductor ran exactly one new estimator/atlas with the existing headless
binary, all2,215original stereo pairs, original source stamps and1× pacing.
Only an appended `loopClosing: 0` in a new YAML changed estimator settings.

| Metric | Observed |
|---|---:|
| Process exit | 0 |
| Processed / tracked | 2215 / 2215 |
| Loss transitions / map changes | 0 / 0 |
| Maps including initial / reset markers | 1 / 0 |
| Loop / completed merge markers | 0 / 0 |
| First-to-last online endpoint | 0.025485075m |
| Estimated within-segment path | 14.198600517m |
| Endpoint / estimated path | 0.17949% (descriptive ratio, **not accuracy**) |

The segment analyzer found one map0segment covering the entire recorded interval,
including the stationary tail. It stops the first candidate at the first loss,
map/state change or declared pose jump, and never joins across a break. Declared
jump boundaries are0.25m/45degrees per consecutive tracked frame; these are
unvalidated diagnostics, not guarantees of uninterrupted physical odometry.
No boundary triggered in this run. Every original header also matches the
attempt, completed-frame and published-pose stamp in order.

This2.55cm return endpoint remains conditional on unmeasured physical alignment;
it is not ground-truth drift accuracy. Local mapping/bundle adjustment remains
active, so online poses are not raw odometry. The inspected upstream mode gates
both loop correction and merging, and bypasses keyframe DB insertion. It can
busy-poll queued keyframes; there is no performance comparison to enabled runs.
K also found a potential upstream disabled-mode uninitialized`mpCurrentKF` read
in the loop thread. This unchanged binary's single run did complete, but that
success does not establish general safety of the mode; source evidence is saved.
No speculative runtime patch or second run was made.

## Rigid agreement of original replays1and2

Matched all2,215exact integer source timestamps. Fit replay2positions to replay1
with Umeyama SE(3), proper rotation determinant+1, scale fixed at1. No interpolation,
trimming or stereo scale adjustment. Fit and residuals use the same samples.

| Metric | Before fit m | After fit m |
|---|---:|---:|
| RMS Euclidean position difference | 0.025700952 | 0.009977410 |
| Median | 0.016693385 | 0.006658158 |
| p95 (linear percentile) | 0.040769750 | 0.012041390 |
| Maximum | 0.099151104 | 0.113615177 |

The aligned RMS is9.98mm, with maximum113.62mm. Least squares minimizes squared
error, not maximum error. This quantifies agreement of these two online position
streams, including replay2's loop effects; it does not establish deterministic
map history, orientation agreement, ground-truth accuracy or population reliability.
The fitted transform, ranks, hashes and all stamped residuals are archived.

## TrackStereo calls exceeding the frame budget

Strict integer tests: `duration_ns > 66,700,000` and exact15Hz
`15*duration_ns > 1,000,000,000`. Both thresholds gave identical counts here.
Each denominator is all2,215completed calls; tracked-only counts use the logged
publication flag. Times come from each call's steady start/end, excluding pacing.

| Original replay | >66.7ms calls | All-call % | Tracked-call overruns | p95ms* | Maxms |
|---|---:|---:|---:|---:|---:|
| 1 | 6 | 0.271 | 6 | 36.087 | 144.116 |
| 2 | 135 | 6.095 | 135 | 71.697 | 512.931 |
| 3 | 14 | 0.632 | 12 | 39.541 | 487.859 |

*This table uses nearest-rank percentiles from j's standard-library analyzer.
The prior report used linear percentiles: p95=36.068/71.593/39.525ms. The
71.6ms review figure and71.7ms here differ only by that declared estimator;
integer overrun counts do not depend on percentile convention.

All three histograms use identical explicit bins and count2,215calls each.
CSV/SVG outputs and a verified Matplotlib PNG/SVG figure stay in the archive.
An over-budget call need not cause exactly one live drop: live queue policy,
other processing and scheduling matter. No Pi, thermal, power or live-drop
inference is made from these Mac results.

## Evidence, implementation and verification

- Archive: `~/wbr-evidence-archive/camera-recording-20261021-01/claude-review-followup-01/`.
  `REPORT.md`, `COMMANDS.md`, `openloop-process.json`, derived YAML, native log,
  `replay-openloop-1/`, `conductor-openloop-analysis-01/`,
  `conductor-alignment-01/`, `conductor-budget-01/`, stamped residuals/histograms.
- Original MCAP SHA256 unchanged:
  `5749908bb94a6c9a7e5496f3c8b58db3596cf5f53f2542502a1468dcd97703c8`.
  Original YAML SHA889b1795…ebe4; derived YAML
  `64ee7eb4cdc6d74afed1d0238717a9e7dea327889eacca31feb221ff7fd4221a`.
- Existing native source/binary/platform: PR92 atda905cd; ORB4452a3c with archived
  compatibility edits, GCC11/OpenCV4.5.4, Ubuntu22.04, Docker4CPU/5GiB. Full
  baseline versions and loaded-library hashes referenced in archive provenance.
- Implementation: codex-j [PR94](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/94),
  sourcecf04fa4; codex-k [PR96](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/96),
  sourceafce7d3. Preceding review [PR93](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/93).
  Final exact-head CI and merge receipts are retained in archived`publication.json`.
- Shared-account idle/quota checks passed. j became busy before initial dispatch;
  conductor waited for release, then used it. k owns alignment/segments; j owns
  timing/histograms. Dedicated branches/worktrees; conductor independently ran
  both results and owns merging. No worker touched the shared runtime checkout.
- Tests independently run:15alignment+14segment+5budget=34PASS, no skips.
  Threshold equality/exact rational comparison, strict stamps, known rigid fit,
  reflection/no-scale/degeneracy, loss/map/jump segmentation and coverage tested.
  These focused suites require explicit commands; generic CI does not discover them.
- CLI outputs match independent geometry/SVD/integer-count calculations.
  Native exit0/complete boundaries/all2,215headers/attempts/completions/pose stamps
  verified. Seven copied native artifacts match container SHA256. Original bag
  hash rechecked; no completed run was repeated or selected.
- Existing container stopped after copy; no Pi/SSH/calibration/motor/STM32,
  control/PPO environment/evidence or owner gain-schedule changes. The earlier
  three-replay automation remains paused; this task did not create a new one.

Recommendation for Claude: accept the conditional open-loop endpoint, rigid
position-agreement metric and measured budget counts with these scopes. Any
accuracy claim needs independent return/trajectory truth; do not treat corrected
endpoints or1× paced throughput as substitutes.
