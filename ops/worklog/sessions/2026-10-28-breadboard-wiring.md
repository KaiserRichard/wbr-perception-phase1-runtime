# Fritzing-style bench wiring illustration — 2026-10-28

- Added `reports/2026-10-supervisor/figures/src/make_breadboard.py`, the custom
  `parts/sn65hvd230_module.svg`, and part attribution in `PARTS_CREDITS.md`.
- Script resolves Fritzing connector IDs from the supplied FZP files, composes
  the Pi, Nucleo, GY-521 and CAN modules, then writes the SVG, PDF and PNG.
- Ran with the requested scratchpad virtualenv Python; command exited 0. Output
  PNG is 2400 × 1660. Viewed the PNG at original resolution and adjusted board
  backing, module pin layout, rail and LED placement, and labels.
- This is an illustration, not a continuity check. The 120 Ω CAN terminations
  are explicitly marked not measured. No report TeX or `main.tex` was changed.
- Second pass: replaced curved routes with orthogonal, rounded-corner paths; moved the Pi left, Nucleo center, CAN/IMU column right, and drew a half-size breadboard with the LED row.
- Regenerated all three outputs with the scratchpad venv Python. Full-size PNG inspection showed some power-feed and annotation congestion in the right column; continued iteration moved module power into an outer gutter, though the diagram still has congested right-side feed lines and is not report-ready.
- Third pass: updated `make_breadboard.py` pin targets to explicit FZP connector IDs, documented CN7/CN10 header mapping, added centre-distance assertions and the wire/XY table, and removed duplicate termination notes. The final script table/self-check ran successfully, but output regeneration is blocked here: active `python3` lacks CairoSVG, network access prevented installation, and TeX's SVG package requires unavailable Inkscape. PNG/PDF are stale relative to the edited SVG; do not use them until rerendered in the CairoSVG environment.
- Fourth pass: corrected Pi UART targets to the Arduino D2/D8 connector holes and retained Arduino GND. CAN1 sources resolve to SDA/SCL (PB9/PB8); CAN2 to CN10-30/CN10-16 (PB13/PB12); MPU SCL/SDA and four LED signals resolve to their specified header holes. Removed floating CAN net labels.
- Added red/black rail feeds to VCC/GND on both CAN modules and explicit routes for resistor/anode and LED cathode/GND connections. All 29 electrical polylines are collected and self-checked so first/last route points equal the corresponding ledger endpoints.
- Rendered with `reports/2026-10-supervisor/figures/src/.venv/bin/python reports/2026-10-supervisor/figures/src/make_breadboard.py`; exit 0, endpoint self-check 29/29. Generated PNG/PDF/SVG at `reports/2026-10-supervisor/figures/`; inspected PNG at original resolution. No `main.tex` edits and no commit.

## Claude 2 takeover (supersedes the passes above and the codex-e auto-router rounds)
- Rewrote `tools/wiring_diagram/wiring_diagram.py`: no router; wires by explicit waypoints
  (`y=N`, `x=N`, `[x,y]`); `--print-pins`, `--grid`, `--strict`; generated breadboard,
  resistors (bands from ohms) and LEDs; checks diagonal, foreign-part, text, shared-lane
  (<8 px), pin-clearance, off-canvas; crossing count printed.
- Parts moved to `tools/wiring_diagram/parts/` (one copy); unused Fritzing LED/resistor files removed;
  CAN module redrawn with real header order 3V3/GND/CTX/CRX and CANH/CANL terminal.
- Bug found by zooming: GY-521 pins were one pitch low because ancestor `<g transform>` was
  ignored; resolver now applies the full transform chain (unit test added).
- Pi GND corrected to the CN5 GND next to AVDD (previous spec used the POWER header GND).
  Resistors from `tools/link_bench/README.md` + owner: 330 ohm, blue 150 ohm (old TikZ `wiring.png`
  still says 220 ohm and a green PC7 LED).
- Render: `.venv/bin/python figures/src/make_breadboard.py` -> `check: PASS`, 30 wires, 33 crossings;
  7 unit tests OK. No `main.tex` edit.
