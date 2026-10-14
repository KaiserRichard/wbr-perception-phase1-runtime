# Native Pi 5 sensor validation, 2026-09-12

> **Camera-free takeover complete:** See [TAKEOVER_REPORT.md](TAKEOVER_REPORT.md)
> for verified tooling readiness, tests, the final Pi runtime bundle and remaining
> physical/package blockers. This is not a new N1/N2/N3 hardware PASS.

> **Phase A preparation update, 2026-09-12:** The camera is unavailable.
> Hardware execution is gated on the user's exact `CAMERA AVAILABLE` message.
> The dated observations below and [manifest.json](manifest.json) are frozen
> historical evidence, not a present-state inventory. Follow the
> [Phase A runbook](PHASE_A_RUNBOOK.md) for the next N1 → N2 → N3 sequence and
> [evidence reconciliation](EVIDENCE_RECONCILIATION.md) for verified findings
> and missing originals. A final **300-second native SDK soak is required**;
> no historical N2 PASS exists. MicroSD may host small evidence only; recording
> requires separately qualified storage. The planned WD PC SN530/JMS583 has
> no qualification result, and UUID `1017-F615` belongs to a different
> historical device. New runs use unique directories and fresh provenance.
> SDK device serial, ASIC serial, firmware-update ID and USB descriptor serial
> remain separate fields, even where historical values happen to coincide.

**Current revalidation, 2026-09-12 09:56–09:58 UTC: N1 REGRESSED / BLOCKED;
N2 BLOCKED BY N1; N3 NOT STARTED.** The user-reported C↔C cable/path negotiates
**480 Mb/s**, behind two USB 2.0 hubs at `4-1.1.2`. Normal-user SDK enumeration
works (USB descriptor `2.1`), but HID/IIO access is denied. `/dev/sda1` is
currently unmounted; `/mnt/wbr-data` resolves to the microSD. No current
streaming or Pi data writes were performed.

Current raw diagnostics and full SDK output are in
[`usb-revalidation-20260912T095610Z/`](usb-revalidation-20260912T095610Z/).
The [manager report](../../docs/PI5_NATIVE_SENSOR_VALIDATION_2026-09-12.md) and
[manifest](manifest.json) contain the reconciled verdict. The original
manifest is preserved in the new evidence directory for provenance/rollback.

Recovery found successful historical 20-second smoke and 105-second capture
with three passing 30-second timing windows, plus IR image inspection.
No five-minute soak or final N2 PASS was established. Those tests used the
previous A↔C 5000 Mb/s setup and do not validate the current cable/path.
Historical storage write+fsync was only 0.944 MB/s.

## Initial-session notes retained below (historical, superseded where dated)

Manager report: [current gate status](../../docs/PI5_NATIVE_SENSOR_VALIDATION_2026-09-12.md).
Exact operations: [COMMANDS.md](COMMANDS.md). Current state: [manifest.json](manifest.json).

The target is native Ubuntu ARM64 on the physical Pi, controlled by SSH from
the Mac. SDK device serial **243322073847** matches the September 8 audit. ASIC/USB
serial **251843061466** is a distinct identifier field for this camera; the
earlier different-camera inference was incorrect.

Raw data, bags and full session logs belong on USB UUID `1017-F615` at
`/mnt/wbr-data/wbr-perception-phase1/2026-09-12/`. These repository files retain
small reports, setup code/configuration, package metadata and results. No bag
or sustained stream has been recorded at the time of the initial manifest.

No application build is needed for package inspection. `inspect_dependencies.py`
uses the Pi's preinstalled `python3-apt`; it does not change apt state.
The SDK archive has been checksum-verified and contains its own CLI tools.

Validation plan: verify device and IIO access as richard after manual setup;
enumerate SDK sensors; then measure explicit IR1 640×480 Y8/15, gyro/200 and
accel/100 with continuous kernel logs. Require three 30-second windows and a
five-minute soak, valid image samples, finite IMU values and strictly
increasing timestamps. Thresholds and limitations are in the manifest.
No N2 PASS from enumeration, no N3 before clean N2, and no SLAM here.

Permission helper checks performed: preview of all 18 required IIO controls;
`udevadm verify` PASS; dry-run trigger restricted to this camera subtree.
The helper's default mode is read-only. Sensor opening, streaming and
persistence across physical reattachment still require live verification.
