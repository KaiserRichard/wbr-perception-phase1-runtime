# Independent review — T1 power and USB qualification

Verdict: **APPROVE-WITH-FIXES**

The implementation satisfies the T1 scope after the targeted fixes below. The
result contract, replay mode, fixture coverage, evidence labels, and hardware
limitations are preserved. No physical Pi, camera, USB, or serial device was
accessed.

## Findings, ranked

1. **Medium — PMIC command selected no channel.** `check_power_usb.py:120-125`
   invoked `vcgencmd pmic_read_adc` without the repository-established
   `EXT5V_V` argument. On the target Pi this could return usage/error output,
   causing every EXT5V criterion to block instead of recording the requested
   rail. Fixed to invoke `vcgencmd pmic_read_adc EXT5V_V`, with a collector
   regression test.

2. **Medium — malformed successful PSU configuration could be ignored.**
   `check_power_usb.py:370-390` treated a successful but unparsable
   `usb_max_current_enable` response as if the optional command were merely
   unavailable. With a valid 5 A device-tree value that could produce PASS from
   contradictory evidence. Fixed: malformed successful output now BLOCKS;
   nonzero/unavailable command output remains tolerated when the device-tree
   declaration is present, as documented. Added a regression test.

3. **Low — window coverage accepted arbitrary nonempty UTC labels.**
   `check_power_usb.py:361-365` previously checked only truthiness for
   `clock_realtime_utc`, so a corrupted label could satisfy the clock contract.
   Fixed with strict ISO-8601, timezone-aware UTC validation and a regression
   test. Host duration arithmetic remains exclusively CLOCK_MONOTONIC.

4. **Low — multiple matching cameras were treated as an identified target.**
   `check_power_usb.py:392-412` could PASS when two matching cameras were both
   at SuperSpeed, although VID/PID alone cannot select the bench camera. Fixed
   to BLOCK ambiguous matching-camera snapshots and added a regression test.

## Requirement audit

- Throttle sampling and all eight documented throttle bits: PASS; decoding is
  reused from `tools/runtime_observer/resource_sampler.py`.
- Under-voltage current/history behavior: PASS; current bit 0 and newly rising
  historical bit 16 fail, missing/cleared evidence blocks, and pre-existing
  history is disclosed rather than misattributed.
- `measure_volts`, PMIC EXT5V_V, configured voltage threshold: PASS.
- 5 A negotiation evidence and USB-current flag: PASS after finding 2.
- D435i sysfs identity, speed, topology, and before/after stability: PASS.
- Kernel dmesg/journal capture, prefix/boot validation, configured fault
  matching, and saved matches: PASS.
- Optional load process-group lifecycle, idle labeling, and exit handling:
  PASS.
- Temperature from firmware and thermal zones: PASS.
- PASS/FAIL/BLOCKED/usage exit codes and `result.json`: PASS.
- `--analyze-only` replay without live commands: PASS.
- Real-evidence fixture and required README/REPORT/test log: PASS.

## Verification after fixes

Commands run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s lab/power_usb/tests -v
Ran 56 tests in 5.642s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/runtime_observer/tests -v
Ran 20 tests in 0.337s
OK (skipped=1)

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile lab/power_usb/check_power_usb.py lab/power_usb/tests/test_power_usb.py
git diff --check
```

The complete owned-suite output is saved in [tests/last-run.log](tests/last-run.log).
The historical real-evidence replay remains expected **BLOCKED** with exit 2;
fixture success is not a hardware gate PASS.

## Remaining open items

- No live Pi run was possible here, so actual firmware command availability,
  PMIC calibration, negotiated current, kernel permissions, thermal behavior,
  and new-unit D435i stability remain UNKNOWN.
- The 4.75 V, 80 °C, timing, and 5 A acceptance policies remain PROPOSED or
  software declarations where documented; they do not prove electrical supply
  capability or sampled-transient absence.
- Sampling is sequential and periodic; events between samples can remain
  UNKNOWN. A load process lifetime does not prove camera frame delivery or
  useful work.

Proposed commit message remains:

```text
lab: add replayable Pi 5 power and D435i USB qualification check
```
