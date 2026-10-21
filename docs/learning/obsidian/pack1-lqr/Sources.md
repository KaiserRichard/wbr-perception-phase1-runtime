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

All explanations and figures are newly authored for this pack. No external
figure is copied; references are for further study and mathematical verification.

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

## Figure reproduction

Run `python lqr_exercise.py --figures assets` in the extracted pack.

| Asset | Origin | Meaning/limits |
| --- | --- | --- |
| `assets/wbr-coordinates.svg` | Original deterministic schematic | Coordinate definitions only; no CAD dimensions or motor wiring convention |
| `assets/scalar-value-feedback.svg` | Computed scalar DARE example | Value parabola and exact scalar sample response |
| `assets/cartpole-response.svg` | 400 computed linear state transitions | Linear cart-pole, stated parameters/weights, 5deg start; no saturation/noise/delay |

No AI-generated image or measured WBR plot is included. SVGs preserve selectable
text; Obsidian can embed them directly. Numerical self-checks are in the one
learning script. Script runs, dependency versions and preview limits are recorded
in [VALIDATION.md](VALIDATION.md).

## Portability

`portable/SKILL.md` records the approved three-pack format and `portable/USER_PROFILE.md`
contains the learning-relevant preferences, without the rest of the personal
project profile. A future agent must read/install them; nothing promises automatic
cross-account memory. This ZIP needs no credentials, symlinks or machine-specific
absolute paths.
