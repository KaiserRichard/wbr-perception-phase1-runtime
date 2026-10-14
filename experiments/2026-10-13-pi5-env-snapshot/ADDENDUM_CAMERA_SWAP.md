# Addendum — camera swap found after the Codex review (2026-10-13)

CODEX_INSPECTION.md was written from `snapshot.txt` (taken 04:19 UTC with the D435i unplugged).
The camera was plugged in and the Pi rebooted at ~04:20 UTC; see `camera_plug_check.txt`.

- **MEASURED:** connected D435i USB descriptor serial `327743061057`, 8086:0b3a, 5000 Mbps, bcdDevice 51.13,
  4 UVC video nodes + hidraw0 + iio:device0 (accel_3d) / iio:device1 (gyro_3d).
- **SOURCE-SUPPORTED:** every earlier evidence file refers to a different unit (USB/ASIC `251843061466`,
  SDK device serial `243322073847`, firmware 5.17.3.10). The user confirmed (2026-10-13) the new unit is the active camera.
- **CHANGED (user-approved):** `/etc/udev/rules.d/99-wbr-d435i.rules` and `/usr/local/libexec/wbr-d435i-iio-permissions`
  now allow both serials; backups in `/var/backups/wbr-udev-2026-10-13/`. MEASURED after reload: hidraw0, IIO controls,
  enable_sensor, video nodes = `root:video 0660`. See `udev_change_2026-10-13.txt`. Non-root SDK/ROS streaming NOT yet verified.
- **Consequence for Section 5:** the old SDK serial `243322073847` is hard-coded in `n3-baseline.yaml` (`serial_no`),
  `n1_precheck.py`, `sdk_capture.py`, `run_sdk_capture.py` and tests. With the new unit, the proposed physical readback
  test would fail to find the device. The new unit's SDK serial and firmware are UNKNOWN until enumerated
  (`rs-enumerate-devices` from the sourced ROS environment).
- **Consequence for gates:** N1/N2 receipts and any calibration belong to the old unit; they do not transfer.
  N1 (identity, firmware, USB, permissions) must be re-run for `327743061057` before N2/N3.
- **MEASURED (later, as user `richard`, no sudo; `rs_enumerate_new_unit.txt`):** SDK device serial `317422076650`,
  ASIC/USB serial `327743061057`, firmware `5.17.3.10` (same as the old unit), USB type 3.2. Enumeration only; no streaming.
  Replace `243322073847` with `317422076650` wherever tooling selects the device (`serial_no`, N1 EXPECTED).
