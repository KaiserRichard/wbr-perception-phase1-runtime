# Validation and evidence limits

- Python3.12, NumPy1.26.4, Matplotlib3.10.3; plot script ran CPU only. A successful
  run with two figures took3.043s in the current shared workload; not a speed claim.
- Read existing archives only. Checked all5000timestamps and noise samples match
  between baseline/residual cases, and initial physical states match. Preserved
  complete metrics for this case in evidence.json. No checkpoint was loaded.
- CSV retains every fifth sample (1000rows,0..9.99s). This is unfiltered display
  thinning. Metrics come from original full-rate records. Torque trace differences
  are not the network residual; the component was not directly logged.
- Older LQR metrics omit `survived`; the script derives it from full_duration and
  no_fall checks. Initial direct field access failed and was fixed before delivery.
- Checked finite CSV values, strictly increasing times, torque limits, expected
  stdout, MathJax equations, SVGs, ZIP extraction and local note/image links.
  The signal diagram was corrected to explicitly route feedback to both controllers.
- Live Obsidian UI unavailable; no claim of an actual vault/theme preview.
- Candidate6–10ms mismatch study is a proposed specification, not a result or
  implemented benchmark. The source's four-delay environment is insufficient
  without a separate versioned adaptation. No pilot/full run launched.
- Literature boundary: two original residual papers consulted; the targeted
  balancing/delay search is incomplete. IEEE11202537 full text inaccessible.
  No novelty/gap or sim-to-real assertion. Primary sources are linked in the lesson.
