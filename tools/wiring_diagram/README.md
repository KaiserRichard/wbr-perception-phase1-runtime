# Wiring diagram renderer

Fritzing-style breadboard pictures from a YAML spec. Every wire is routed by
explicit waypoints written in the spec; the tool never routes by itself. It
resolves pin coordinates, draws the boards, checks the geometry and marks every
violation with a magenta circle. Method and checklist:
`ops/lab-assistant/skills/wbr-wiring-diagram/SKILL.md`.

```sh
PY=reports/2026-10-supervisor/figures/src/.venv/bin/python   # needs cairosvg, pyyaml (pillow for crops)
$PY tools/wiring_diagram/wiring_diagram.py SPEC --print-pins nuc 'D[0-9]'   # pin x,y on the canvas
$PY tools/wiring_diagram/wiring_diagram.py SPEC --output-dir OUT --grid      # OUT/<output>-grid.png, 50 px grid
$PY tools/wiring_diagram/wiring_diagram.py SPEC --output-dir OUT --strict    # svg/pdf/png, exit 1 on violation
$PY -m unittest discover -s tools/wiring_diagram/tests
```

## Spec

- `parts`: `{id, svg, fzp?, x, y, scale, rotation?, title?, title_xy?, svg_pin_prefix?, extra_pins?}`.
  Pins come from the `.fzp` (`connector` id or name -> breadboard-view `svgId` -> element centre,
  ancestor transforms applied), from SVG ids starting with `svg_pin_prefix`, or from
  `extra_pins` (`name: svgId` or `name: [x, y]` in the part's SVG units).
  `kind: breadboard` (`cols`, `pitch`) generates a half-size breadboard with holes `a1..j30`,
  rails `T-1, T+1, B-1, B+1 ...`.
- `components`: `{kind: resistor, from, to, ohms}` (colour bands from the value) and
  `{kind: led, anode, cathode, colour}` drawn on breadboard holes.
- `wires`: `{id, from, to, colour, via?, width?, dashed?}`. `via` items: `y=N` (move vertically),
  `x=N` (move horizontally), `[x, y]` (absolute corner). The final segment must line up with `to`.
- `notes`, `legend`: text placed by hand; the checker treats every text box as an obstacle.

## Checks

Diagonal segments; wires over a foreign part (only the escape segments on the wire's own
source/destination board are allowed, and sideways jogs there are limited to 25 px);
wires over text; parallel wires closer than 8 px (shared lane); a wire passing within 7 px of
another wire's pin; points off the canvas. Perpendicular crossings are allowed but counted.

## Parts

`parts/` holds Fritzing library drawings (CC-BY-SA 3.0, see `parts/PARTS_CREDITS.md`) and our
own `sn65hvd230_module.svg`.
