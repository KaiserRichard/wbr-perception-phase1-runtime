# ORB-SLAM3 stereo-inertial settings check

This tool checks that a flat OpenCV FileStorage ORB-SLAM3 Settings YAML is
internally plausible for stereo-inertial use and matches a selected image/IMU
stream profile and calibration reference. It uses only Python's standard
library and supports the scalar and `!!opencv-matrix` subset used by ORB settings.

## Run on the Pi

Run from the repository root with Python 3.12 and a **fresh output directory**.
For the named D435i N4B profile, the config selects the stream and its matching
factory camera and provisional IMU references:

```bash
python3 tools/orb_settings_check/check_orb_settings.py \
  /path/to/D435i_317422076650_stereo_inertial.yaml \
  --outdir /path/to/evidence/orb-settings-check-2026-10-18 \
  --profile d435i_n4b
```

`--fps` is the frame rate declared by the selected stream profile, not a measured
delivery rate. For the upstream EuRoC fixture profile:

```bash
python3 tools/orb_settings_check/check_orb_settings.py \
  /path/to/EuRoC.yaml --outdir /path/to/evidence/euroc-settings-check \
  --profile euroc_mh01
```

The named profiles and all numeric tolerances are in
`tools/orb_settings_check/config/check_config.json`. The EuRoC profile's
baseline/noise reference comes from the upstream example fixture and exists to
exercise the validator. For a real setup, pass that setup's camera-chain and IMU
calibration files instead. A plain calibration camchain must contain
`cam1.T_cn_cnm1`; the IMU YAML must use the continuous-time SI field names from
`calibration/lab/config/imu_d435i_provisional.yaml`.

To re-evaluate retained evidence without original paths or hardware, use a new
output directory:

```bash
python3 tools/orb_settings_check/check_orb_settings.py \
  --analyze-only /path/to/evidence/orb-settings-check-2026-10-18 \
  --outdir /path/to/evidence/orb-settings-check-analysis
```

Exit codes follow the lab contract: 0 PASS, 1 FAIL, 2 BLOCKED, 3 usage/internal
error. Each run writes `result.json`, the settings copy, the config copy, and
the calibration copies used. Result criteria refer to those files and include
measured values, thresholds, source/rationale, and status. Do not reuse an
output directory containing evidence from an earlier run.

## Criteria

| Criterion | Meaning |
|---|---|
| `opencv_yaml`, `required_settings`, `viewer_settings` | Header/version and fields needed for stereo-inertial ORB Settings parsing, chosen according to `Camera.type`. |
| `camera_type` | `PinHole`, `Rectified`, or `KannalaBrandt8` is declared. Rectified uses ORB's `Stereo.b`; the other stereo types use `Stereo.T_c1_c2`. |
| `camera_profile`, `imu_profile_rate` | Width, height, image fps and `IMU.Frequency` agree with a named or explicit profile. Explicit profile values are caller supplied. |
| `stream_values`, `stereo_depth_threshold`, `operating_flags` | Dimensions/rates and stereo depth threshold are positive and well-formed; present integer boolean flags are 0 or 1. |
| `intrinsics` | Positive focal lengths, fx/fy within the configured tolerance, and principal points inside the image. |
| `transform_geometry` | OpenCV 4x4 transforms have orthonormal rotation blocks, determinant +1, a homogeneous final row, and translations below the configured bound. |
| `stereo_baseline` | Stereo transform/scalar baseline agrees with the selected factory/camchain reference within the configured relative tolerance. |
| `imu_noise_positive` | Gyro/accel white noise and random walk values exist and are positive. |
| `imu_noise_calibration` | ORB noise values match the selected calibration's continuous-time SI densities. The repository calibration values already use ORB's expected density units, so the source-to-ORB unit conversion is identity (factor 1); ORB applies its sample-rate scaling internally. |
| `extractor_sane` | Feature count, scale factor, pyramid levels and FAST thresholds lie in configured bounds. |
| `viewer_values` | Viewer dimensions/scales are positive and bounded; viewpoint values are finite. |
| `optional_flags` | Reports `IMU.InsertKFsWhenLost`, `Camera.RGB` and `Viewer.imageViewScale` when present. This is informational. |

All chosen numeric bounds are marked **PROPOSED** with rationale in the config.
They are screening policies, not measured acceptance limits. Upstream schema
requirements are labeled **SOURCE-SUPPORTED** in code and the result.

## What this cannot prove

A PASS means only that the settings file parses under the supported subset and
matches the supplied profile/calibration references within configured bounds.
It does not prove the YAML loads in OpenCV/ORB-SLAM3, image delivery at the
declared rate, camera/IMU timestamp mapping or offset, continuous-time noise
accuracy, extrinsic calibration accuracy, visual tracking, N4B/N4C gate status,
or Pi runtime/performance. For the EuRoC fixture, values are SOURCE-SUPPORTED
from an upstream example; the pass is fixture behavior, not a project gate PASS.
No timestamp arithmetic is performed, and no camera clock is mapped to an IMU
clock. D435i camera IMU settings do not describe the STM32 body IMU.

## Local checks

```bash
python3 -m unittest discover -s tools/orb_settings_check/tests -v
```

`tests/last-run.log` records the completed fixture suite. Fixtures include the
attributed upstream EuRoC settings and exercise a saved D435i candidate with
its repository factory camchain and provisional IMU reference.

When a `provenance.json` from `make_orb_yaml.py` is beside the input settings,
the check also verifies the generated `orbslam3.yaml` against its recorded hash
and requires the checked file to match it byte-for-byte. Use `--provenance` to
point at the sidecar when it is elsewhere. This confirms provenance/output
identity; it does not validate the calibration inputs themselves.
