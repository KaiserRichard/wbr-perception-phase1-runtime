# Configuration review — OPEN

This is a runnable development candidate for SDK serial **317422076650**, firmware
**5.17.3.10**, IMU **BMI085**. It does not qualify N4. All hardware, timing,
calibration, offline VIO and live VIO conclusions remain **OPEN**.

## Sources and classifications

- **M — MEASURED readback:** [2026-10-13 factory enumeration](../2026-10-13-pi5-env-snapshot/rs_calibration_new_unit.txt),
  produced by `rs-enumerate-devices -c`. This classification describes observed
  SDK values, not a new independent optical or inertial calibration experiment.
- **U — SOURCE-SUPPORTED:** pinned [RealSense_D435i.yaml](../../third_party/ORB_SLAM3/Examples/Stereo-Inertial/RealSense_D435i.yaml),
  commit `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`.
- **S — SOURCE-SUPPORTED:** the same commit's [Settings.cc](../../third_party/ORB_SLAM3/src/Settings.cc),
  [ImuTypes.cc](../../third_party/ORB_SLAM3/src/ImuTypes.cc),
  [Frame.cc](../../third_party/ORB_SLAM3/src/Frame.cc) and
  [EuRoC.yaml](../../third_party/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC.yaml).
- **A — ASSUMED:** an operating/tuning choice for this unit, subject to measurement.

The SDK serial is distinct from ASIC serial `327743061057`, firmware-update ID
`327743061057`, and separately observed USB descriptor serial `327743061057`.
The [swap addendum](../2026-10-13-pi5-env-snapshot/ADDENDUM_CAMERA_SWAP.md)
establishes that old SDK serial `243322073847` is a different unit. Its tests and
calibration results do not transfer.

## Rectified stereo schema

The new enumeration's IR1 and IR2 640×480 Y8 blocks (lines 326–334 and 414–422)
both give `fx=fy=386.953308105469`, `cx=321.034301757812`,
`cy=241.040130615234`, Brown Conrady coefficients `[0,0,0,0,0]`.
These are the SDK rectified stream projections; physical lens distortion has
not been independently measured. No second software rectification is proposed.

`File.version: "1.0"`, `Camera.type: "Rectified"`, `Camera1.*` and `Stereo.b`
follow the actual Settings parser. For Rectified, it does not read `Camera2.*`
or distortion coefficients; identical right projection is assumed. Thus IR2
values are documented here and in the YAML comment rather than added as unused
keys. Do not substitute the EuRoC PinHole schema or legacy `Camera.bf`/`Tbc`.

The measured SDK transform IR1→IR2 is `R=I`, `t=[-0.049912553280592,0,0] m`.
The right camera center in left coordinates is `-R^T t=[+b,0,0]`.
ORB wants the positive magnitude `Stereo.b=0.049912553280592 m` and computes
`bf=fx*b≈19.31382761 pixel·m`. There is no sign reversal of disparity.

## Transform direction and math

Let `c1` denote the SDK left IR optical frame and `b` the SDK gyro/body frame.
RealSense extrinsics **from A to B** act on points as
`p_B=R_BA p_A+t_BA` in metres. The API rotation array is column-major; OpenCV
matrix `data` is row-major. Identity rotation makes that distinction numerically
invisible here. Keep the raw SDK IMU axes; do not additionally rotate to a ROS
camera_link, ENU, NED or controller body convention.

The new file's IR1→Gyro and IR1→Accel both give:

```text
R_bc = I
t_bc = [-0.00552000012248755, +0.00510000018402934, +0.011739999987185] m
T_bc = [ I  t_bc ]
       [ 0   1  ]
p_b = T_bc p_c1
```

Gyro↔Accel is identity with zero translation in the readback; shared physical
alignment is still unmeasured. The reverse Gyro/Accel→IR1 readback is:

```text
T_cb = inverse(T_bc) = [ R_bc^T  -R_bc^T t_bc ]
                      [   0          1      ]
t_cb = [+0.00552000012248755, -0.00510000018402934, -0.011739999987185] m
T_cb T_bc = I
```

**ORB's actual `IMU.T_b_c1` is `T_bc`: camera→body**, despite the upstream
RealSense comment saying “Transformation from body-frame (imu) to left camera”.
The EuRoC comment says camera→body. The executable evidence is stronger:
`ImuTypes.cc` sets `mTcb=mTbc.inverse()` and `Frame.cc` sets
`T_cw=T_cb*T_bw`. Therefore the YAML must use the IR1→Gyro transform directly.
Using the reverse readback under this key would invert all three translation
signs incorrectly. A camera-origin test gives `p_b=t_bc`; body origin maps to
`p_c1=-t_bc`. The positive Y value corrects the upstream example's negative Y.

The numbers are **MEASURED SDK readback**, while their interpretation as nominal
mechanical/CAD geometry is **INFERRED / SOURCE-SUPPORTED**, not per-unit IMU
alignment calibration. [Repository calibration readiness](../../docs/D435I_VIO_CALIBRATION_READINESS.md)
documents the SDK fallback and links the official
[librealsense parser v2.58.4](https://github.com/realsenseai/librealsense/blob/v2.58.4/src/ds/ds-calib-parsers.cpp).
Its earlier raw fallback logs concern the old unit; the new numeric values match
that nominal geometry. No Intel document with a mechanical-calibration quotation
was found in the requested repository docs, and no online source was fetched.
The SDK source URL is an existing repository citation, not a newly verified
claim about the currently installed binary.

The SDK warning reported in the ticket is **“IMU Calibration is not available”**;
the full warning preserved for the old unit is “IMU Calibration is not available,
default intrinsic and extrinsic will be used.” The new calibration text itself
does not include a warning line. Preserve new raw SDK stderr during later tests
and do not silently attribute old warning logs to this serial.

New gyro/accel readback gives identity sensitivity, zero bias, zero noise
variance and zero bias variance (lines 471–488). These are not evidence of a
noiseless IMU. Whether `rs-imu-calibration` was ever run successfully for this
unit is **UNKNOWN**; treat IMU intrinsics as uncalibrated until evidence resolves
the warning/defaults. No calibration tool or firmware operation is authorized
by this preparation. Spatial/temporal calibration and a stationary full-precision
Allan-variance run are required before N4 qualification. Choose duration from
the desired averaging times, normally hours rather than this 60–90 s VIO take;
use qualified storage and a separately reviewed procedure.

## Upstream versus candidate

All upstream entries below are **U**. Candidate values marked **U+A** reuse
example values as assumptions for this unit. Noise units are continuous-time
density units, not SDK variance-array entries.

| Key / quantity | Upstream RealSense_D435i.yaml | Candidate | Candidate source |
|---|---|---|---|
| File.version / Camera.type | `"1.0"` / `Rectified` | same | S: exact parser schema |
| Camera1.fx / fy (px) | 382.613 / 382.613 | 386.953308105469 / same | M: IR1 640×480 |
| Camera1.cx / cy (px) | 320.183 / 236.455 | 321.034301757812 / 241.040130615234 | M: IR1 |
| IR2 fx/fy/cx/cy | implicit same rectified projection | same as IR1 | M: IR2; S: no Camera2 keys read |
| Distortion | implicit ideal rectified pinhole | five zeros, omitted from schema | M: both IR blocks; S |
| Stereo.b (m) | 0.0499585 | 0.049912553280592 | M: magnitude of IR1→IR2 t_x |
| Camera.width / height | 640 / 480 | same | M capability; A selection |
| Camera.fps | 30 | 30 | M capability; A choice to match example and motion |
| Camera.RGB | 1 | 1 | U+A; ignored for Y8 |
| Stereo.ThDepth | 40.0 | 40.0 | U+A; close threshold ≈1.9965 m |
| IMU.T_b_c1 rotation | identity | identity | M readback; nominal physical interpretation |
| IMU.T_b_c1 t_x (m) | -0.005 | -0.00552000012248755 | M IR1→Gyro |
| IMU.T_b_c1 t_y (m) | -0.005 | +0.00510000018402934 | M; direction established by S |
| IMU.T_b_c1 t_z (m) | +0.0117 | +0.011739999987185 | M IR1→Gyro |
| IMU.InsertKFsWhenLost | 0 | 0 | U+A |
| IMU.NoiseGyro (rad/s/√Hz) | 1e-3 | 1e-3 | U+A; Allan variance required |
| IMU.NoiseAcc (m/s²/√Hz) | 1e-2 | 1e-2 | U+A; Allan variance required |
| IMU.GyroWalk (rad/s²/√Hz) | 1e-6 | 1e-6 | U+A; Allan variance required |
| IMU.AccWalk (m/s³/√Hz) | 1e-4 | 1e-4 | U+A; Allan variance required |
| IMU.Frequency | 200.0 | 200.0 | U+A: gyro-grid input, not accel rate |
| ORBextractor.nFeatures | 1250 | 1250 | U+A |
| ORBextractor.scaleFactor / nLevels | 1.2 / 8 | same | U+A |
| ORBextractor.iniThFAST / minThFAST | 20 / 7 | same | U+A |
| Viewer.KeyFrameSize / KeyFrameLineWidth | 0.05 / 1.0 | same | U+A |
| Viewer.GraphLineWidth / PointSize | 0.9 / 2.0 | same | U+A |
| Viewer.CameraSize / CameraLineWidth | 0.08 / 3.0 | same | U+A |
| Viewer.ViewpointX/Y/Z/F | 0.0 / -0.7 / -3.5 / 500.0 | same | U+A; `--no-viewer` for Pi |

Noise densities are left continuous-time: the pinned tracking setup applies
`sqrt(IMU.Frequency)` scaling to measurement noise and inverse scaling to walks.
Do not apply that conversion twice. Bias, scale, actual sample rates and
camera–IMU time offset remain **UNKNOWN**, rather than assumed calibrated to zero.
