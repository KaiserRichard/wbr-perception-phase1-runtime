# Ticket: switch N1/N2 tooling to the new D435i unit + latched-power diagnostic mode

Repository: this checkout (Mac, canonical). Tooling dir: experiments/2026-09-12-pi5-native-sensor-validation/
You must NOT ssh to the Pi, touch hardware, install packages, commit or push. Edit only files in the tooling dir
and write one report file. Keep diffs small and in the existing code style.

## Facts (MEASURED 2026-10-13, see experiments/2026-10-13-pi5-env-snapshot/rs_enumerate_new_unit.txt, camera_plug_check.txt)
Active unit (user-confirmed): SDK device serial 317422076650, ASIC serial 327743061057, firmware-update ID 327743061057,
USB descriptor serial 327743061057, firmware 5.17.3.10, USB type 3.2, 5000 Mbps. IMU type not yet read (expected BMI085; verify in N1, do not assume).
Old unit (historical evidence only): SDK 243322073847, ASIC/USB 251843061466.
Pi: 4 GB RAM now (was 8 GB). vcgencmd get_throttled = 0x50000 (bits 16 and 18 latched: under-voltage occurred,
throttling occurred; live bits 0-3 clear). No better power supply is available today; the user explicitly chose to run anyway,
with all results recorded as OPEN, never PASS.

## Required changes
1. Replace hard-coded old-unit identifiers (n1_precheck.py EXPECTED and line ~28, sdk_capture.py DEVICE_SERIAL and identity check,
   run_sdk_capture.py only if it is used by phase_gate.py — otherwise leave historical files unchanged as provenance,
   n3_baseline.yaml serial_no, tests) with ONE shared definition of the active unit (e.g. in validation_common.py),
   so a future swap is a one-line change. Keep the old values documented in a comment as historical.
   Note the corrected historical N3 YAML lives under experiments/2026-09-13-.../n3-physical-20260913T072201Z/; do NOT edit it.
2. Add an explicit opt-in flag (e.g. --diagnostic-latched-power) to n1_precheck.py and phase_gate.py n2 that:
   - accepts throttled values whose ONLY set bits are latched history bits 16-19 (mask 0xF0000), and still FAILS on any live bit 0-3;
   - also applies to health_monitor.py sampling during runs (live bits 0-3 still stop the run);
   - writes "power_mode": "diagnostic_latched_history" and the raw throttled value into every result.json;
   - forces any verdict that would be PASS to be "OPEN_DIAGNOSTIC" (accept-n2 must refuse to issue N2_ACCEPT PASS from such inputs).
   Without the flag, behavior is unchanged (0x0 required).
3. Memory: if any check assumes 8 GB, leave thresholds (512 MiB MemAvailable) as they are; just report what you find.
4. Update/add unit tests for: new identity accepted, old identity rejected, flag off + 0x50000 rejected, flag on + 0x50000 accepted
   as OPEN_DIAGNOSTIC, flag on + 0x50005 rejected, accept-n2 refuses diagnostic inputs.
5. Run: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s experiments/2026-09-12-pi5-native-sensor-validation -p 'test_*.py' -v
   (tests needing ROS/Pi may skip on the Mac; report which).
6. Build and verify a new runtime bundle per PHASE_A_RUNBOOK.md, but put it in
   experiments/2026-10-13-pi5-env-snapshot/bundles/wbr-runtime-<UTC>  (not /tmp), with bundle_runtime.py build + verify.

## Report
Write experiments/2026-10-13-pi5-env-snapshot/CODEX_TICKET_SERIAL_POWER_REPORT.md: files changed (with a short diff summary),
test output summary, bundle path + SHA256SUMS hash, anything you could not do, and risks. Use MEASURED/INFERRED/UNKNOWN labels.
