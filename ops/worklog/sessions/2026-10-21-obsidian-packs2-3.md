# RL/PPO and residual lesson completion

- Followed owner's approved sequential delivery: Pack1 sent immediately when
  ready; mergedPR83 after exact-head green checks. New branch for remaining packs.
- Wrote two lessons, one CPU-light script each, expected output, three SVG figures,
  and small real saved-command/metric extract with source/provenance notes.
- Existing v1 LQR source commit781d702; residual frozen v2 f1b5ee7. Paired saved
  5ms push/noise1000 with residual training seed0; checked all5000times/noise samples
  and initial states. Kept every fifth command for display and copied full metrics.
- First plot script run failed because old LQR metrics lack `survived`; fixed by
  deriving it from full-duration/no-fall checks. Re-ran successfully. Clarified
  total torque difference is not learned delta and corrected explicit feedback path.
- Pack2 math checks/figure1.013s; Pack3 two figures3.043s. MathJax72expressions,
  16display,no errors. SVGs inspected; browser/native UI unavailable, no actual
  Obsidian preview claim. Small package extraction and expected-output checks run.
- No new simulation/training, camera work, motor action or protected gain schedule.
  Current v2 untouched. Proposed mismatch study and novelty review remain future work.
- Checked official Obsidian heading-link syntax; switched all three reading maps
  to exact-heading wiki anchors and rechecked/repacked Pack1 as a portability fix.
- Staged whitespace check exposed Matplotlib's trailing spaces inside SVG paths;
  removed them in assets and each figure writer, then rebuilt/rechecked all ZIPs.
