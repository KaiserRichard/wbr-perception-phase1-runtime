# Reachable control validation — 21 October 2026

Documentation closeout: **22 October 2026**. PR102 follow-up is **COMPLETE**:
[400 unique identities and metrics verified][final]; acceptance is separately
**PASS for both controllers**, not inferred from completion or exit 0.
Merged features: [PR103][pr103], [PR104][pr104], [PR106][pr106], [PR107][pr107].

| Controller | Strict PASS (FAIL) | Seeds 0, 1, 2, 3, 4 (PASS/total each) | Peak displacement (m) | Worst recovery (s) |
|---|---:|---|---:|---:|
| Fresh DARE | 200/200 (0) | 40/40, 40/40, 40/40, 40/40, 40/40 | 0.172102885 | 2.896 |
| Cubic fitted | 200/200 (0) | 40/40, 40/40, 40/40, 40/40, 40/40 | 0.172108663 | 2.898 |

[Observed maxima][summary] are descriptive, not performance-improvement claims;
none of these summary metrics is unavailable. Zero falls, numerical failures
or cap violations occurred. All 400 cases completed 10 s, 5,000 control steps
and 5,001 noise samples; all 200 paired noise hashes matched. All 200 pushes
applied the full 0.9 N·s over 0.15 s.

**Model boundary.** This is an ASSUMED fixed-length **reduced** family: fixed
mass, COM scaled by length and inertia by length squared. Geometry covers only
two fixed posture rays; nonlinear results do not validate five-bar dynamics,
hardware or the full workspace. Sampled poles/cases establish neither continuum
nor changing-length stability; gain-entry errors are not stability evidence.

**Ordered evidence.** [Reduced/five-bar A/B comparison][comparison] at
0.12/0.16/0.20/0.21 m, with fresh reduced nominal gains and no actuator delay/lag,
found all 36 local refinements stable: five-bar pole radius approximately
0.99749–0.99767, decay 0.796–0.859 s. This is not model parity: mass differences
and actual acceleration map $M^{-1}G$ remain explicit. The approximately 17%
generalized torque-map difference is not a whole-$B$ percentage error.

[Stages 2–3][stages] selected 0.12–0.20 m: upright extension limit 0.211246 m,
104° start limit 0.201791 m, only 1.791 mm upper margin. Nine lengths × four
delays produced 36 fresh designs and four cubic fits. All 32 fresh midpoint
checks passed: [radius][numeric] 0.997434974361–0.997676790315, margin
0.00232321–0.00256503, decay 0.778719–0.859878 s. [Independent conductor checks][independent]
matched radii exactly; separately reconstructed coefficients differed by at
most 4.44e-16. The final evaluation's 20 local checks also passed.

**Nonlinear panel.** Five lengths 0.12/0.135/0.16/0.185/0.20 m × delays
2/3/4/5 ms × two controllers × seeds 0–4 × balance/push = 400.
The [unchanged protocol/configs][context] retain initial tilts, 5 ms actuator
lag, noise, 2/4 N·m caps, final-second settling and five-second recovery deadline.

**Interruption and recovery.** The [original batch][original] stopped after
271 completed PASS cases; cause, exit time/code and total duration are UNKNOWN.
[Recovery][recovery] reused those 271 without replay and evaluated only 129 new
cases, plus 20 local design checks: exit 0, **2022.950900 s (33.716 min)**.
The interrupted partial CSVs remain preserved. Both phases used unchanged
production source `d4b4249`; Intel Mac, serial, approximately one CPU observed,
no Pi or training.

**Reproduction/evidence.** [Session notes][session] index exact commands,
configs, raw metrics, resource samples and exits: comparison `f1086c9`,
sweep/fit `90e6e50`, nonlinear `d4b4249`. Final authority is
`evaluation-resume-01/conductor-summary.json`, not interim root `report.md`.
[Recovery script][script] preserves `../evaluation-01/...` artifact references.
Reporting fixes retain numerical FAIL/null metrics; independent combined tests
44/44, prior augmented tests 16/16 and merged-feature CI passed.

**Recommendation for Claude:** audit this completed milestone and its limits.
Frozen PPO v2 strict seeds [39,20,0,0,0] place all 59 successes in two of five;
legacy learning curves are unavailable. Any future full v3 requires ≥5 seeds
per arm after a reviewed pilot; no v3 launched.

[final]: /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study/receipts/conductor-final-validation.json
[summary]: /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study/evaluation-resume-01/conductor-summary.json
[comparison]: /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/fivebar/conductor-run-01/comparison.json
[stages]: /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study/receipts/stages-2-3.json
[numeric]: /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study/receipts/numeric-summary.json
[independent]: /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study/receipts/conductor-validation.json
[context]: /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/run-context.json
[original]: /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study/receipts/nonlinear-01.json
[recovery]: /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study/receipts/nonlinear-resume-01.json
[script]: /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/reachable-study/receipts/resume_remaining.py
[session]: ../sessions/2026-10-21-control-linear-review.md
[pr103]: https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/103
[pr104]: https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/104
[pr106]: https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/106
[pr107]: https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/107

## Claude review (2026-10-22)

**Decision: accepted.** The PR102 follow-up was done in the requested order. The
limits are stated plainly, and the "17% is a generalized torque-map difference,
not a whole-B error" correction to my earlier wording is right. Read: this file,
the session notes and the README diff. Archives not re-read.

### 271 + 129 recovery: sound

- Both phases used the same clean source `d4b4249`, fit and configs. The 271
  reused cases were validated by identity and metrics, not replayed. Only the
  129 missing cases ran. The interrupted partial CSVs were kept, not reused.
- All 200 DARE/fitted noise-hash pairs match. If any pair was split across the
  two phases (likely, since 271 is odd), that is good evidence the noise stream
  is reproducible across processes; worth confirming in the manifest.
- The case after #271 completed normally in recovery, so the interruption was
  not a deterministic crash in that case. The cause stays UNKNOWN, as reported.
- Gap (optional, about 1 min): noise hashes do not prove the *dynamics* output is
  bit-identical across processes. Rerun 2–3 of the reused 271 cases into a fresh
  path and compare `metrics.json` exactly. If they match, the reuse is fully
  justified rather than assumed.

### Model limits: correctly stated; what 400/400 does and doesn't show

1. **Zero failures means the panel is not discriminating.** 400/400 PASS with
   worst recovery 2.9 s (deadline 5 s) and peak 0.172 m shows these conditions
   are inside the controller's comfort zone. It says nothing about margin. A
   stress test is needed to find where it breaks.
2. **DARE vs fitted are nearly identical** (peak 0.1721029 vs 0.1721087 m), so the
   cubic fit costs essentially nothing within 0.12–0.20 m.
3. **The five-bar check was nominal (no delay or lag)**, while the nonlinear panel
   used 2–5 ms delay plus 5 ms lag on the reduced model only. Reduced-model gains
   on the five-bar *with* delay remain unchecked.
4. **Fixed length only.** Changing the length while balancing, which is what gain
   scheduling is for, is untested.
5. 0.20 m sits 1.79 mm from the 104° start limit, so the top of the range is at
   the edge of the reachable region. That's fine, but keep it in mind.

### Next (CPU-light, no lab)

(a) Stress to failure on the reduced model: push magnitude sweep, design/run
delay mismatch (design 2 ms, run 5–10 ms), mass and torque-map mismatch. This is
also the baseline the residual-PPO research question needs. (b) Five-bar linear
check with delay augmentation. (c) A slow length-ramp case (0.12 → 0.20 m over a
few seconds) with the fitted schedule.
