# LED test wiring — Nucleo-F446RE + Raspberry Pi 5 (2026-10-25)

Advisory display only. No motors. Disconnect power before changing wires.

## Parts
- 4 LEDs: green, yellow, red, blue (5 mm or 3 mm).
- Resistors: 330 Ω for green, yellow, red; 150 Ω for blue (blue needs ~3 V,
  330 Ω would make it very dim). Anything 220–470 Ω works for the first three.
- Small breadboard, ~10 male-female + male-male jumper wires.

## LED circuit (same for each LED)
Nucleo pin → resistor → LED anode (long leg) → LED cathode (short leg, flat
side) → GND rail. About 4 mA per LED (CALCULATED: (3.3 − 2.0 V) / 330 Ω);
the F446 pin limit is 25 mA.

| LED | Nucleo Arduino pin | MCU pin | Meaning |
|---|---|---|---|
| Green | D4 | PB5 | NONE: path clear |
| Yellow | D5 | PB4 | JUMP_CANDIDATE |
| Red | D6 | PB10 | STOP_CANDIDATE |
| Blue (any LED, optional) | D9 | PC7 | UNCERTAIN (also yellow blinking 4 Hz) |
| (rail) | GND | GND | breadboard ground rail |

All off with red blinking 2 Hz = no link or advisory older than 300 ms.
LD2 (on-board green) = link accepted, as before.

## UART + power (unchanged from 24 Oct, tools/link_bench/results/20261024-nucleo/README.md)
| Pi 5 header | Nucleo |
|---|---|
| pin 8 (GPIO14 TXD) | D2 (PA10, USART1 RX) |
| pin 10 (GPIO15 RXD) | D8 (PA9, USART1 TX) |
| pin 6 (GND) | GND |
| pin 2 (5 V) | E5V, jumper JP5 on E5V (no USB cable) |

Baud 460800 (bench firmware default).

## Check before powering
1. LED legs the right way round (long leg towards the resistor/pin side).
2. No wire between Pi 5 V and any Nucleo pin other than E5V.
3. Common ground: Pi GND, Nucleo GND and the breadboard rail connected.

## Operator test
1. Flash the new bench firmware (Claude 2 gives the command after review).
2. Run the live chain; with nothing ahead GREEN should light.
3. Place the obstacle on the line, push the rig slowly toward it; the moment
   RED (or YELLOW for a low box) lights, stop and tape-measure camera front →
   obstacle front. Note the LED, the measured distance and the box height.
