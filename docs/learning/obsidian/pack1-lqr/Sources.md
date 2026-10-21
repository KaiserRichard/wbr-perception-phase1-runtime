---
title: "Pack 1 — sources and provenance"
tags: [wbr, lqr, sources, reproducibility]
---

# Sources and provenance

Return to [[Pack 1 - LQR]]. Sources checked 21 October 2026.

## Primary readings

- [Russ Tedrake, Underactuated Robotics — LQR](https://underactuated.mit.edu/lqr.html): continuous/discrete optimal control and Riccati equations. Read after reproducing our Bellman expansion. Our notation uses $P$ for the value matrix and distinguishes sampled/continuous weights.
- [Tedrake — Cart-pole dynamics](https://underactuated.mit.edu/acrobot.html): background on the underactuated cart-pole. Our point-mass example explicitly defines an upright, right-lean angle; do not copy another source's angle convention unchanged.
- [SciPy solve_discrete_are](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_discrete_are.html): the DARE solved numerically, return value and solver limitations. Numerical exercise verified with SciPy1.15.3; the linked current manual can evolve.
- [SciPy cont2discrete](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.cont2discrete.html): zero-order-hold sampling used by the cart-pole exercise.
- [Roboticsbook §3.5](https://www.roboticsbook.org/S35_vacuum_decision.html): reconnect value/policy reasoning with your earlier reading. §6.6 becomes relevant in Pack2; Chapter7 is optional.
- [Obsidian embeds](https://obsidian.md/help/embeds) and [math formatting](https://obsidian.md/help/Editing+and+formatting/Advanced+formatting+syntax): built-in note links, embeds and MathJax support.

The mathematical walkthrough is authored for this pack. The owner supplied nine
WBR mechanical PNG plates and explicitly authorized reuse; eight are embedded here.
Their original authoring/generation history is not established. They are conceptual
teaching illustrations, not measured CAD or validation data. Original image bytes
are preserved. Captions qualify ambiguous angles, moving pivots, nominal versus
augmented feedback, and truth-state scoring. See
[Figure review and prompts](FIGURE_REVIEW_AND_PROMPTS.md) for all nine reviews.

## Project snapshot

Source repository: [WBR project](https://github.com/KaiserRichard/wbr-perception-phase1-runtime),
source commit `6b022c0d14b1e82bd1d2365b7e1eca0eaf309a86`.
This is the input snapshot before lesson creation, not a claim of a new run.

`data/wbr_gains.json` is a small read-only teaching extraction from:

- `sim/configs/assumed_planar.json`: state/input order and nominal Q/R.
- `sim/configs/assumed_actuator_noise.json`: full-precision saved nominal K.
- `sim/control_c/fixtures/recorded.json`: existing archived augmented gains for2/3/4/5ms.

Those augmented gains are recorded host-controller fixtures originating from
archive `sim-actuator-20261020-01`, not gains synthesized by this lesson.
The full archive is not bundled. The snapshot identifies source paths/commit.
Its role is interpreting matrix columns and computing one command; it does not
replace complete experiment provenance or validate closed-loop robot performance.

Nominal gain was synthesized for an assumed ideal rolling planar surrogate;
augmented gains model additional timing/lag. Neither is firmware gain parity or
an identified full five-bar robot. `sim/parity/student.py::gain_schedule` is not
read for its solution, implemented, changed or bypassed.

## Mechanical revision provenance

Mechanical walkthrough values come from `sim/configs/assumed_planar.json` at
`4f49447f6b494ad3dc7aaa68e5f52256f03bd7fc`; the four geometry values used by the
exercise are bundled in `data/mechanics.json`. All masses, COM offsets and
inertias are assumptions; the radius is a source constant, not a measurement.
The analytical mass/bias matrices are derived from the stated energies for that
surrogate. They are not a new numerical validation of the MuJoCo implementation.
The earlier gain-snapshot commit above remains unchanged.

## Figure reproduction

`python lqr_exercise.py --figures assets` regenerates only two numerical SVG plots.

| Assets | Origin | Meaning/limits |
| --- | --- | --- |
| `01_coordinates_and_angles.png` through `08_delay_lag_and_noise.png` | Owner-supplied plates, copied unchanged | Assumed planar coordinates, COM, energy, motor work, dynamics and control; captions explain limitations |
| `scalar-value-feedback.svg` | Computed scalar DARE example | Value parabola and exact scalar sample response |
| `cartpole-response.svg` | 400 computed linear transitions | Stated linear cart-pole; no saturation, noise or delay |
| `wbr-coordinates.svg` | Retained earlier schematic | Legacy asset, unused by the illustrated lesson |

Numerical plots remain distinct from conceptual plates. The image prompts name
future optional files; those files are not referenced as if they already exist.
Script runs and preview limits are in [VALIDATION.md](VALIDATION.md).

## Portability

`portable/SKILL.md` records the approved three-pack format and `portable/USER_PROFILE.md`
contains the learning-relevant preferences, without the rest of the personal
project profile. A future agent must read/install them; nothing promises automatic
cross-account memory. This ZIP needs no credentials, symlinks or machine-specific
absolute paths.
