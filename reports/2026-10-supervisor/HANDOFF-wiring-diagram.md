# Handoff: breadboard-style wiring diagram + skill (2026-10-28)

**Status 2026-10-28: done.** Picture `figures/breadboard-wiring.png` (strict PASS); method in `ops/lab-assistant/skills/wbr-wiring-diagram/SKILL.md`.

## Goal
1. A clean Fritzing-style "breadboard view" picture of the F446 bench (real board drawings, coloured wires pin to pin) for the supervisor report.
2. A reusable skill so later diagrams are made the same way by ChatGPT/Codex/Claude.

## Where things are (branch `claude2/20261026-supervisor-report`, worktree `~/Desktop/Research/wbr-wt-c2-report`)
- `tools/wiring_diagram/` — codex-e's tool: YAML spec -> SVG/PDF/PNG; pin lookup from Fritzing `.fzp` (connector svgId -> element centre), header-grid pins for morpho, checker (endpoint match, collinear overlap, part crossing, label overlap; magenta circles on violations), unit tests (`python3 -m unittest discover -s tools/wiring_diagram/tests`). Part files + `PARTS_CREDITS.md` (Fritzing parts, CC-BY-SA 3.0).
- `reports/2026-10-supervisor/figures/src/bench_wiring.yaml` — bench spec (currently broken layout: breadboard part points at the CAN module SVG, LEDs missing).
- `reports/2026-10-supervisor/figures/src/make_breadboard.py` — entry point. Renderer: `reports/2026-10-supervisor/figures/src/.venv/bin/python` (has cairosvg; recreate with `python3 -m venv .venv && .venv/bin/pip install cairosvg pyyaml` if missing).
- `reports/2026-10-supervisor/figures/wiring.pdf/.png` — the correct, simple TikZ pin diagram (source `figures/src/wiring.tex`). Use as ground truth for pins.

## What failed and why
Six codex-e rounds tried automatic routing (free curves, then A*, then channels). It never converged: shared lanes, wires on wrong headers, stubs. Do NOT try an auto-router again.

## Method that should work (deterministic)
1. Fix layout by hand in the spec: Pi top-left, Nucleo centre, CAN#1, CAN#2, GY-521 in a right column, half-size breadboard (draw a simple breadboard SVG: hole grid + red/blue rails) with 4 resistor+LED pairs below the Nucleo.
2. Add a `--print-pins` mode that prints every resolved pin's canvas x,y.
3. For every wire write explicit waypoints (`via: [[x,y],...]`), orthogonal, each wire on its own lane (>=10 px apart), leaving each header perpendicular, never crossing a board or label.
4. Render, run the checker with `--strict`, LOOK at the PNG, adjust waypoints, repeat until clean.

## Bench connections (verified against the firmware README)
| Wire | From | To |
|---|---|---|
| UART TX | Pi pin 8 (GPIO14) | PA10 = Arduino D2 |
| UART RX | Pi pin 10 (GPIO15) | PA9 = D8 |
| GND | Pi pin 6 | Arduino GND (next to AVDD) |
| USB | Pi USB-A | Nucleo mini-USB (power + ST-Link) |
| CAN1 TX/RX | PB9 = D14/SDA, PB8 = D15/SCL | CAN#1 CTX / CRX |
| CAN2 TX/RX | PB13 = CN10-30, PB12 = CN10-16 | CAN#2 CTX / CRX ("fake motor") |
| CAN bus | CAN#1 CANH/CANL | CAN#2 CANH/CANL (120 Ω on modules, not measured) |
| I2C | PB6 = D10, PB7 = CN7-21 | GY-521 SCL / SDA |
| Power | POWER header 3V3 / GND | breadboard rails -> every module VCC/GND |
| LEDs | PB5 = D4 green CLEAR, PB4 = D5 yellow JUMP/blink UNCERTAIN, PB10 = D6 red STOP/blink no Pi data, PC7 = D9 green UNCERTAIN | 220 Ω -> LED -> GND rail |

## Review checklist (from today's failures)
- Every wire traceable end to end; no two wires share a segment; no stubs.
- Each Nucleo end on the right header row (Arduino vs morpho; top vs bottom).
- No text crossed by a wire; titles not overlapped; nothing clipped.
- Colours match the legend; 3V3 red and GND black only.
- Credits for Fritzing parts in the caption.

## Then
- Write the skill: `ops/lab-assistant/skills/wbr-wiring-diagram/SKILL.md` (sources for board drawings, spec format, the waypoint method, the checklist above, commands).
- Do not edit `main.tex` while ChatGPT is editing the report; tell the owner the `\includegraphics` line instead.
- Commit to this branch and push. Repo rules: AGENTS.md (no force-push, no merge without green CI).
