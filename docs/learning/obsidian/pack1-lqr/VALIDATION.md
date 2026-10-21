# Illustrated Pack 1 validation — 21 October 2026

- Python 3.12, NumPy 1.26.4, SciPy 1.15.3; CPU only, one numerical thread.
  Exercise passes scalar analytic/DARE agreement, Bellman identity, cart-pole
  controllability rank 4, DARE residual 4.40e-14, spectral radius 0.973677,
  toy-state decay and saved WBR matrix dimensions/source-array agreement.
- Added geometry/virtual-work checks pass: leg/body COM values match the
  8°/−6° example; generalized motor power equals relative-joint motor power,
  0.975025 W for the specified toy input/speeds. Expected output updated.
- Independent SymPy 1.14.0 check of the stated energies reproduces the printed
  mass matrix, Euler–Lagrange bias vector and COM push Jacobian exactly.
  This verifies the algebra for the stated surrogate, not MuJoCo/hardware parity.
- Eight supplied mechanical plates embedded beside worked explanations. Two
  computed plots retained; the earlier unused coordinate SVG is a legacy asset.
- Pack 1 lesson/toolkit/source notes: 293 math expressions, 45 displayed.
- Fresh ZIP extraction: local Markdown/image paths, YAML, table-of-contents
  anchors and cross-pack wiki destinations checked. Exactly one Python exercise
  per pack; extracted exercise stdout matches the bundled expected output.
- All 381 mathematical expressions across the three lessons/support notes
  (62 display equations) compiled with MathJax 3.2.2 with zero errors. New
  mechanics, Bellman and residual equations were rendered and visually inspected.
- PNG copies match the owner's originals byte for byte (11 copies across packs,
  nine distinct supplied images). They were reused under the owner's explicit
  permission; original generation/authorship history is unestablished. Caveats
  are adjacent to the embeds and in FIGURE_REVIEW_AND_PROMPTS.md.
- Live Obsidian/vault theme inspection was unavailable. Direct MathJax/asset
  checks are not a claim of a live Obsidian preview. All syntax uses built-in
  Obsidian features; no community plugin or network is needed for reading.
- No new MuJoCo rollout, training, gain synthesis, active-environment change,
  firmware/motor command or hardware test. Saved gain and torque evidence retained.
