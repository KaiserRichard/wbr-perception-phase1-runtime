# Three-pack lesson series complete

- Pack1 was delivered first and merged inPR83 after both checks passed. Remaining
  archives: docs/learning/obsidian/pack2-rl-ppo.zip and pack3-residual-experiment.zip.
- Pack2: Bellman/value→policy gradient→GAE→PPO, hand-worked rollout and both clip
  signs. One CPU-light script; all reference values asserted; one technical SVG.
- Pack3: residual composition, bias/stability, one script plotting a matched saved
  5ms push case and a signal diagram. Baseline strictPASS, residual strictFAIL but
  survives. No claim from one case; plot shows total issued command, not delta.
- Source data: existing v1 baseline and v2 residual seed0, noise1000. All5000
  timestamps/noise samples and initial truth matched. Include1000display rows
  plus full-rate metrics; thinning is explicitly unsuitable for computing peaks.
- Validation: scripts/expected output, extracted ZIP paths/YAML/wiki-links,
  MathJax72expressions/16display, SVG visual inspection. Live Obsidian unavailable
  and disclosed. Pack2 script+SVG1.013s; Pack3 two figures3.043s, illustrative timings.
- New experiment remains a specification: train2–5ms, test6–10ms with matched stale
  delay knowledge. Explain missing environment support, no oracle advantage,
  required reward/pilot/learning-curve checks and held-out evaluation. No gap claim.
- Limitations: no fresh training, protected-exercise solution, hardware or runtime
  change. Original residual papers consulted; targeted delay novelty review incomplete.
