---
name: wbr-power-check
description: Check Raspberry Pi 5 power, throttling and temperature, then run lab card A (lab/power_usb). Use for any under-voltage, throttling, reboot or "check power" request.
---

# Power check

Read `ops/lab-assistant/INSTRUCTIONS.md` first. Do not clear or hide earlier
throttle history; it is evidence.

## Step 1 [PHYSICAL]
Confirm the supply is the **27 W, 5.1 V / 5 A** one (read its label aloud). The old
5 V / 3 A supply FAILS by design; never waive that.

## Step 2 [PI] Quick reading (camera may be unplugged)
```sh
vcgencmd get_throttled; vcgencmd measure_temp; vcgencmd pmic_read_adc EXT5V_V
printf 'declared supply: %d mA\n' 0x$(od -An -tx1 /proc/device-tree/chosen/power/max_current | tr -d ' \n')
vcgencmd get_config usb_max_current_enable
```
Expect: `0x0`, temperature below 80 C, EXT5V about 5.0 to 5.2 V, 5000 mA, and
`usb_max_current_enable=1` (or 5000 mA declared, which enables full USB current).
- 3000 mA declared: wrong supply or no USB-PD negotiation. Stop; swap cable/supply.
- `0x50000` or `0x50005`: under-voltage happened (bit 16) and/or is happening (bit 0).
  Stop acquisition. Check supply, cable, and whether something else draws power.
- `vcgencmd: command not found` or permission denied: report it; do not install.

## Step 3 [PI] Card A, the formal tool (60 s idle window)
Pick a new folder name each time (`-01`, `-02`, ...).
```sh
cd ~/wbr-perception-phase1-runtime
OUT=~/wbr-evidence/power-idle-$(date +%Y%m%d)-01
python3 lab/power_usb/check_power_usb.py --out "$OUT" --duration 60; echo "exit=$?"
python3 ops/lab-assistant/show_result.py "$OUT/result.json"
```

All ten criteria must be PASS: `raw_integrity`, `under_voltage`, `ext5v`,
`temperature`, `window_coverage`, `supply`, `usb_link`, `usb_topology`,
`kernel_log`, `load_window`. Exit 1 = FAIL, 2 = BLOCKED (missing evidence).

## Interpret
- Idle PASS does **not** cover streaming load. Say so in the report.
- `usb_link` checks the camera (8086:0b3a) at 5000M; a 5000M root hub alone proves nothing.
- FAIL on `supply` or `under_voltage`: fix power before anything else; no camera work.

## Report
Output folder path, exit code, each criterion status, raw readings. Labels: MEASURED.
