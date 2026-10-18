# ORB settings validator report

## Built

Added `check_orb_settings.py`, a Python standard-library parser/validator for
OpenCV FileStorage Settings version 1.0, including `!!opencv-matrix` transforms.
It checks type-specific stereo-inertial fields, image/profile dimensions and
rates, intrinsics, rigid transforms, translation/baseline plausibility, IMU
noise positivity and calibration agreement, ORB extractor settings, Viewer
values, and reports optional flags. Every numeric policy threshold is in
`config/check_config.json` with a source or rationale; locally selected bounds
are marked PROPOSED.

The tool writes the common `result.json` contract with PASS/FAIL/BLOCKED status,
criteria, host and UTC metadata, retained raw inputs and SHA-256 hashes. Its
`--analyze-only` path re-runs checks from saved evidence. The parser is limited
to the flat settings subset and OpenCV matrix nodes used by ORB settings; it is
not a general YAML parser.

## Evidence and checks

- **PASS, fixture tooling only:** upstream ORB-SLAM3 EuRoC Stereo-Inertial
  example copied with attribution and checked against its named EuRoC profile.
- **PASS, fixture tooling only:** saved D435i development candidate checked
  against `calibration/lab/config/camchain_factory_317422076650.yaml` and
  `calibration/lab/config/imu_d435i_provisional.yaml`.
- **PASS, generated-output consistency:** ran the existing
  `tools/n4b_offline/make_orb_yaml.py` into a temporary directory, then checked
  its `orbslam3.yaml`; the checker matched the provenance output hash. No
  generator output was retained in this worktree.
- **PASS/FAIL/BLOCKED coverage:** tests exercise valid settings, malformed
  intrinsics/rotation/profile/rate/noise/baseline/extractor parameters, absent
  input, and saved-evidence re-analysis.
- **Test result:** `python3 -m unittest discover -s
  tools/orb_settings_check/tests -v` ran 8 tests successfully; captured in
  `tests/last-run.log`.
- No hardware, camera, serial device, Pi, OpenCV runtime or ORB engine was used.

These results show fixture behavior only. They do not promote N4B/N4C and do not
verify that any settings are accurate for a physical camera or IMU. D435i noise
values remain ASSUMED provisional values, and camera/IMU clock association is
UNKNOWN. Translation plausibility bounds are PROPOSED screening thresholds.

## Proposed commit message

`Add ORB-SLAM3 stereo-inertial settings validator`
