# Validation and provenance

- Python3.12/NumPy1.26.4/Matplotlib3.10.3, CPU only. Script plus SVG generation
  ran in1.013s in the shared workload (one observation, not a benchmark claim).
- Hand-checked TD residuals, backward GAE, value targets, all clipped surrogate
  contributions and both advantage signs. True terminal versus timeout example
  checked separately. Assertions passed; expected console output is bundled.
- Figure is an exact plot of mathematical functions, newly authored, not sampled
  robot data. Regenerate with the same learning script and inspect both signs.
- Pack2/3 together:72math expressions/16display compiled using MathJax3.2.2 with
  no errors. SVG previews visually inspected. YAML, local paths and extraction
  checked; wiki-links resolve when the three packs share one vault.
- Obsidian's live UI was unavailable. Direct MathJax/SVG checks do not claim an
  actual Obsidian session/theme check. No community plugin is required.
- Project explanations read at source6b022c0/Pack1; primary links appear in the
  main lesson. Original PPO/GAE equations are distinguished from SB3 details.
- No training, environment changes, policy selection or real robot control.
