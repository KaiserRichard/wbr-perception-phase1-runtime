# T26 interface findings

## R26-01 — standard ROS IMU CDR is rejected by the exporter (OPEN)

**MEASURED software reproduction:**
`test_review.ReviewTests.test_standard_cdr_export_R26_01` invokes the documented
`tools/n4b_offline/db3_to_euroc.py` CLI on a temporary bag containing standard
CDR Image and Imu messages. It returns exit 1 with `ERROR: truncated CDR`.
The test is marked `unittest.expectedFailure` with this ID, as T26 requires.

**SOURCE-SUPPORTED in repository:**
`tools/n4b_offline/db3_to_euroc.py:28` aligns fields against byte zero of the
encapsulation rather than the CDR body beginning at byte four. Image fields
only require four-byte alignment; IMU doubles require eight-byte alignment and
are read four bytes late. Compare the body-relative alignment in
`lab/rosbag_qual/bag_core.py:31`. For the fixture's `camera_imu` frame ID, the
first quaternion starts at byte 28 and the complete message is 324 bytes.
`test_standard_cdr_imu_fields_and_alignment` checks those offsets independently.
The original rehearsal writer mirrored the exporter defect and hid it.

The exporter is outside T26 ownership and was left unchanged. The full standard
synthetic bag still exercises rosbag qualification and drift recovery. For
later stages only, `test_compatibility_pipeline` copies that bag to the explicitly
named `exporter-compatibility.db3` and replaces IMU padding with the exporter's
legacy layout. It preserves topic identities, all header/receive timestamps,
image payloads, and the intended IMU values. This is an isolated test-fixture
workaround, **not proof that standard ROS bags export successfully**. Fixing the
tool should make the expected-failure test unexpectedly succeed; then remove
the marker and compatibility fixture after review.

No additional blocking interface mismatch was observed in the exercised path.
Separate gyro/accel streams correctly produce `driver_method: UNKNOWN`.
The direct converter and sender CLIs work over a PTY. Their startup imports
consume real time, so the test explicitly schedules the last synthetic pose
into the declared affine raw-clock mapping and continues unavailable reports
while preparing it. No pose acquisition stamp is renewed to disguise age.

All results are synthetic tooling evidence, not any sensor, estimator, Pi,
physical link, STM32 safety, or project gate PASS.
