# WBR Obsidian learning packs

Approved sequence, owner relaying Claude's review on 21 October 2026:

| Pack | Archive | Content/status |
| --- | --- | --- |
| 1 | `pack1-lqr.zip` | LQR derivation, one-page toolkit, scalar/cart-pole script and saved WBR gains |
| 2 | `pack2-rl-ppo.zip` | RL→PPO; one tiny GAE/clipping script |
| 3 | `pack3-residual-experiment.zip` | Residual control; plot saved torque traces; mismatch experiment design |

Each named directory is the maintainable source for its ZIP. Archives deliberately
duplicate those source bytes for easy import; do not edit the ZIPs directly.
Unzip each delivered pack into the same Obsidian vault; keep relative assets.
Future wiki-links resolve after the corresponding pack arrives. No vault settings
or community plugins are bundled. Source/figure provenance is inside each pack.

**Illustrated revision, 21 October 2026:** Pack 1 now develops the mechanics from
the owner's supplied plates before deriving LQR; Packs 2 and 3 connect those
mechanics to learning and residual timing. Eight plates are local to Pack 1,
Plate 09 is local to Pack 2, and Plates 04/08 are also local to Pack 3. Deliberate
asset duplication keeps each pack readable offline. Replace old pack folders
when importing this revision.

Each pack has exactly one learning script plus expected console output. Computed
plots remain deterministic SVGs; owner-supplied technical PNG plates are preserved
unchanged and qualified beside their embeds. All nine are reviewed in
[FIGURE_REVIEW_AND_PROMPTS.md](FIGURE_REVIEW_AND_PROMPTS.md), which includes five
standalone English prompts with exact output filenames. This series does
not change a training protocol or run hardware. The candidate later study uses
training delays2–5ms, held-out6–10ms, and delay-aware LQR as baseline; novelty is
unproven. Current control pilot rules apply to any future training.

Reproduce Pack 1 from its directory in a separate Python3.11/3.12 environment:

```sh
python -m pip install numpy==1.26.4 scipy==1.15.3 matplotlib==3.10.3
python lqr_exercise.py
python lqr_exercise.py --figures assets
```

Compare against `expected-output.txt`; see the main lesson for tolerances,
commands, expected behaviour and failure symptoms. The exercise includes
Bellman-identity, DARE-residual, stability and gain-dimension checks.

Packaging: from this directory, use Python's `zipfile` to include every regular
file under `pack1-lqr/` with the same relative path, excluding `__pycache__` and
virtual environments. Check extraction to a fresh folder, local assets, MathJax
syntax and expected script output before publishing a revised ZIP.
