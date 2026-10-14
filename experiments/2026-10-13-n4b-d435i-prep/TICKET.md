# Ticket E: ORB-SLAM3 stereo-inertial config + N4B/N4C plan for the new D435i (Mac-only)

Work only inside this repository on the Mac. Do NOT ssh, use the network, install, commit or push.
Write files only under experiments/2026-10-13-n4b-d435i-prep/.

## Inputs
- experiments/2026-10-13-pi5-env-snapshot/rs_calibration_new_unit.txt : MEASURED factory calibration of the active unit
  (SDK serial 317422076650, firmware 5.17.3.10, BMI085), from `rs-enumerate-devices -c` on 2026-10-13.
- third_party/ORB_SLAM3 (upstream source, commit 4452a3c): Examples/Stereo-Inertial/stereo_inertial_realsense_D435i.cc,
  RealSense_D435i.yaml, EuRoC.yaml, and the Settings parser (src/Settings.cc) for the exact YAML schema (File.version "1.0").
- docs/D435I_VIO_CALIBRATION_READINESS.md, docs/ORB_SLAM3_OFFLINE_PREPARATION.md, docs/NEXT_GATE.md, AGENTS.md.

## Deliverables
1. `D435i_317422076650_stereo_inertial.yaml` for ORB-SLAM3 stereo-inertial, IR1+IR2 640x480 (rectified Y8 IR streams have
   ~zero distortion; check the calibration file), camera rate as chosen in (3), using:
   - IR1/IR2 intrinsics for the chosen resolution, stereo baseline from Extrinsic IR1->IR2 (MEASURED);
   - T_b_c1 (IMU body to left camera) derived from the factory Extrinsic IR1<->Gyro/Accel (MEASURED). Be explicit about direction
     and about the RealSense convention vs ORB-SLAM3's IMU.T_b_c1, and show the math. Note the D435i factory IMU extrinsic is a
     nominal mechanical value (INFERRED/SOURCE-SUPPORTED, cite the Intel doc if quoted in repo docs) and the IMU intrinsics are
     uncalibrated unless rs-imu-calibration was run (UNKNOWN for this unit; the SDK warns "IMU Calibration is not available").
   - IMU noise/random-walk values: use the upstream RealSense_D435i.yaml values as the starting point (SOURCE-SUPPORTED: upstream file),
     label ASSUMED for this unit, and state that an Allan-variance run is required for N4 qualification.
   - A side-by-side table: upstream RealSense_D435i.yaml value vs ours, with the source of each.
2. `n4b_plan.md`: the shortest credible path to (a) N4B offline stereo-inertial run on recorded D435i data and (b) N4C live,
   given that ORB-SLAM3 is being built natively on the Pi now (Pangolin 0.9.1, C++17, binaries in ~/orbslam3/ORB_SLAM3).
   Prefer ONE code path for offline and live: propose a minimal patch to stereo_inertial_realsense_D435i.cc that optionally reads a
   librealsense .bag file (rs2::config::enable_device_from_file, playback set_real_time(false)) and that can disable the viewer,
   and a matching tiny recorder (rs2::recorder or rs2::config::enable_record_to_file) that records IR1+IR2 Y8 640x480, gyro 200 Hz,
   accel 100/250 Hz (check what the D435i supports and what the upstream example requests), emitter OFF (explain why: projector dots
   break stereo feature tracking). Write the patch as `stereo_inertial_d435i_file.patch` against 4452a3c plus a
   `d435i_record.cpp`; do not apply to third_party. Include exact build/run commands for the Pi.
   Also cover: required motion for IMU initialization (what the user must do by hand, how long), success criteria to observe
   (initialization messages in the log, "IMU initialized", map count, tracking loss), storage budget per minute of IR1+IR2+IMU on the
   32 GB microSD (~17 GB free before the build), and the frames/timestamps chain (camera hardware timestamps vs IMU timestamps,
   global time setting) with what is MEASURED vs UNKNOWN.
3. A short `README.md` in that folder pointing to the above. Mark everything OPEN; nothing is PASS.
