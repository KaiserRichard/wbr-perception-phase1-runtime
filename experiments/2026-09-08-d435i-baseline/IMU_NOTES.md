# IMU evidence limitations

The simultaneous host probe received raw gyro, raw accel, combined IMU and static transforms in CURRENT_ROOT_RATES.json. This was a CycloneDDS subscriber receiving the FastDDS camera publisher, with best-effort sensor QoS. Arrival rates are subscriber-observed rates, not proof of hardware sample production rates. All received per-topic timestamps were strictly increasing.

No physical motion was commanded. The near-zero gyro mean and approximately 9.758 m/s² acceleration norm are consistent with a mostly stationary camera; physical stationarity was not independently observed. Raw gyro acceleration fields and raw accel angular-velocity fields are zero by design, not additional measurements. Combined orientation covariance begins with -1: no orientation estimate is provided.

Runtime ROS package 4.58.1 differs from pinned 4.58.4. Both source versions call imu_callback_sync(frame) without passing the configured mode on the ordinary motion-sensor path; the header defaults that argument to COPY. Mode 2 therefore does not establish actual interpolation. Source excerpts and tag SHA are in IMU_SOURCE.txt. No binary instrumentation or dynamic value-correlation experiment was completed before USB loss; exact packaged-binary behavior remains UNCERTAIN.

The calibration warning occurs in librealsense 2.58.1 IMU EEPROM read fallback, not camera_info creation. Static transforms received contain CAD-compatible fallback translations; transform existence does not prove device-specific calibration.
