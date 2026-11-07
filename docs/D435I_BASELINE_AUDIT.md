# D435i Phase-1 Baseline Audit

## 1. Executive Summary

**Audit execution: controlled root A/B COMPLETE; non-root test identifies an IMU permission failure. Sensor pipeline remains NO-GO for baseline bags or D435i VIO.** The audit resumed after reattachment on 2026-09-08, approximately 19:13–19:17 Asia/Ho_Chi_Minh (UTC+07), without repeating completed source/version work. The camera remained on USB 2.1 / 480M. In isolated 30-second root runs, two-IR delivered 23 IR1 images with 18 incomplete-frame notifications; IR1-only delivered 15 images with 15 notifications. Disabling IR2 did not restore stable images. A separate non-root GID-44 test opened IR1 but failed to open the IMU's IIO scan controls with `Permission denied`. USB disconnected again at 19:15:51, without overlapping camera containers. Raw/combined sample correlation strongly supports COPY behavior despite live method-2 readback. No bag or SLAM was started.

Sections 2–6, 8–10 and the original evidence retain the initial 18:50–19:01 observations where marked; the resumed results in sections 7 and 16 supersede earlier untested/final-state claims.
| Item | Status | Evidence / limit |
|---|---|---|
| USB detection | FAIL continuity | Reattached at 480M; survived root A/B; disconnected again at 19:15:51; absent finally |
| Docker device access | PARTIAL / IMU FAIL | Root streams; GID 44 opens IR1, but IIO scan-element access fails for non-root |
| RealSense detection | PASS | D435i serial 243322073847, firmware 5.17.3.10; historical within this audit, absent finally |
| IR1 stability | FAIL | Resumed A: 23 images/30 s; B: 15 images/30 s at requested/opened 15 FPS |
| IR2 stability | FAIL | Resumed A: 22 images/30 s; B explicitly disabled IR2 |
| gyro | PARTIAL | Present, near-zero mean; 167.279 Hz received versus 200 Hz profile |
| accel | PARTIAL | Present at 100.697 Hz; approximately 9.758 m/s²; continuity lost with device |
| combined IMU | PARTIAL | Resumed A/B approximately 153/155 Hz; sample correlation supports COPY with method 2 |
| ROS discovery | PASS | Live topics/messages received; later bounded no-daemon node checks found `/camera` with both middleware implementations |
| rosbag readiness | FAIL | Stability gate failed; no bag recorded or replayed |
| ORB-SLAM3 readiness | NOT TESTED | Never started; local benchmark and D435i execution decisions below are NO-GO |

No commit, push, source revision change, upstream edit, device permission change, firmware write, system configuration change, or SLAM launch was performed. Only temporary camera containers and inspection/probe processes were run. Camera containers were stopped at the end; stopped audit containers remain for review. The host ROS daemon was restarted during diagnosis. Existing `USB.txt` was appended, preserving the earlier evidence.

## 2. Exact Runtime Environment

| Component | Observed value |
|---|---|
| Parent HEAD | `1b16be7b62b45eecc608a03f2f6f377e8ace8a9b` |
| Initial Git status | `?? experiments/` |
| ORB_SLAM3 | `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4` |
| ORB_SLAM3_ROS2 | `efd7acd9ea31bfdbcd843a4c90eeaa85f7e80dd8` |
| Embedded ORB_SLAM3 | `0f29ad5f563269a13109d81eb886916cc5960136` |
| realsense-ros checkout | `9a11121700cb4780e273e34141f6402fe184321d` (`4.58.4`) |
| Calibration submodule | `92ad7a5b4ad9616b98221ae140301f8bbc0a0782` |
| Runtime-version source tag, inspected without checkout | realsense-ros `4.58.1`, SHA `53aceeac29e2e848e5e1ede5430124f07b2fe924` |
| Docker / Compose | `29.2.1`, build `a5c7197` / `v5.1.0` |
| Ubuntu | `24.04.4 LTS`, Noble |
| Kernel | `7.0.0-31-generic`, `#31~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC`, x86_64 |
| ROS | Jazzy, host and container |
| Runtime realsense-ros package | `4.58.1-1noble.20260615.150439` |
| Runtime librealsense package | `2.58.1-1noble.20260524.190754`; startup built/running SDK both 2.58.1 |
| Image | `realsense:latest`; full immutable image ID in `HOST.txt` |
| Host identity | richard 1000:1000; includes video 44, plugdev 46, docker 984 |
| Image identity | richard 1001:1001; groups initially `[1001]` |

**OBSERVATION:** The checked-out ROS wrapper version differs from the running package. **HYPOTHESIS:** The image installs distro binaries rather than building the pinned checkout. **EXPERIMENT:** Read `camera.Dockerfile`, package XML and `dpkg-query` in the image. **EVIDENCE:** Dockerfile installs `ros-jazzy-realsense2-camera`; runtime reports 4.58.1, checkout is 4.58.4. **CONCLUSION:** Confirmed version mismatch. Pinning the source repository alone does not pin this runtime image's ROS package. No revisions were changed.

The execution sandbox itself failed before shell startup (`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`); diagnostics then ran using approved host execution. This is a diagnostic-runner limitation, not sensor evidence.

## 3. USB and Device Detection

Initial exact entry:

```text
Bus 005 Device 002: ID 8086:0b3a Intel Corp. Intel(R) RealSense(TM) Depth Camera 435i
Bus 005 root: xhci_hcd/4p, 480M
  Port 003, device 2, interfaces 0–4: Video, uvcvideo, 480M
  Port 003, device 2, interface 5: Human Interface Device, usbhid, 480M
Bus 006 root: xhci_hcd/4p, 5000M (no camera beneath it)
/sys/bus/usb/devices/5-3/speed = 480
```

The D435i was on the USB 2.x path despite a USB 3.x root hub existing. SDK reports USB type `2.1`. Host `/dev/video0..5` were `root:video`, mode `0660` with an ACL marker. Camera HID was `/dev/hidraw3`, `root:root`, `0600`; its sysfs path contains `5-3:1.5/0003:8086:0B3A.0004`. Other hidraw devices are QEMU tablets. No IIO device names were enumerated; `/sys/bus/iio/devices` was empty at final inspection. Kernel logged hid-sensor-hub report-ID warnings during root camera startup. At this initial inspection the live SDK IMU backend was unproven. The resumed non-root failure identifies the HID/IIO sysfs scan-control path (section 16); hidraw permissions alone do not establish the SDK's access requirements.

**OBSERVATION:** Corruption occurred on a 480M connection. **HYPOTHESIS:** USB bandwidth, passthrough scheduling, cable/port, or device/firmware faults could contribute. **EXPERIMENT:** Measure the current stream; attempt an IR1-only test; inspect kernel history. **EVIDENCE:** Both IR streams opened; incomplete-frame logs, a Left MIPI error, later UVC probe errors and USB disconnect. **CONCLUSION:** USB 2.x attachment is proven; USB 2.x as the cause of corruption is **UNCERTAIN**. No USB 3.x A/B test was possible.

Kernel chronology:

```text
18:51:50 hid-sensor-hub ... No report with id 0xffffffff found
18:54:31 uvcvideo 5-3:1.2: Failed to set UVC probe control : -32 (exp. 48).
18:54:32 usb 5-3: USB disconnect, device number 2
18:54:32 realsense2_came[...] segfault ... in librealsense2.so.2.58.1
```

At 19:01:23, `lsusb` no longer listed 8086:0b3a, `/dev/video*` and camera hidraw3 were absent. Cause of disconnection is **UNCERTAIN**. The attempted second process overlapped the first before this event (section 7), so this event cannot be attributed solely to a single-stream setting or the physical USB link.

## 4. Docker Device Permissions

Inspected both `third_party/ORB_SLAM3_ROS2/docker-compose.yaml` and its included `ros2_realsense_d435i_camera_calibration/docker-compose.yaml`, plus rendered Compose configuration and actual image/container configuration.

The `realsense` service uses host network and IPC, `privileged: true`, `/dev:/dev`, and device cgroup rules `c 81:* rmw` / `c 189:* rmw`. There is no supplementary `group_add`; the Dockerfile selects a named user built with UID/GID 1001. Compose sets `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` but does not set domain 42. Privileged mode and cgroup allowance do not grant this non-root UID discretionary filesystem permission to open mode-0660 video devices.

Safe experiment: identical temporary image/device mounting, Python `os.open(..., O_RDWR|O_NONBLOCK)` followed immediately by close; no streaming ioctl or writes in this permission probe.

| Identity | Actual groups | `/dev/video0..5` | `/dev/hidraw3` |
|---|---|---|---|
| Image normal user, 1001:1001 | 1001 | All EACCES | EACCES |
| Root, 0:0 | 0 | All OPEN OK | OPEN OK |
| Image user plus `--group-add 44` | 44, 1001 | All OPEN OK | EACCES |

**OBSERVATION:** Host richard can be in video while container richard cannot open video. **HYPOTHESIS:** Host supplementary groups are not inherited. **EXPERIMENT:** Three identity tests and normal/root node startup. **EVIDENCE:** Group lists above; normal service logs repeated permission errors and no devices, root opens and streams. **CONCLUSION:** Confirmed. Numeric GID 44, not matching the username, is the verified non-root video fix.

Recommended persistent fix to review, **not applied**: an override in our repository adding `group_add: ["44"]` and explicit domain/transport variables. Retain a non-root UID; align UID/GID with host 1000 only if required for output-file ownership. That alignment alone is not the video access fix. The resumed group-44 streaming test now identifies denied IIO scan controls. For complete non-root IMU, review narrowly scoped host RealSense IIO rules for the recreated device nodes, then repeat the test after attachment is restored. Do not infer that container-side udev configuration fixes host nodes. No broad permission grant is recommended. The initial non-root attempt was confounded. The isolated resumed test now establishes a concrete IIO scan-element permission failure (section 16); GID 44 alone is insufficient for IR1+IMU. No host permission fix was applied.

## 5. ROS 2 Discovery

Host environment was `ROS_DOMAIN_ID=42`, `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`, `ROS_DISTRO=jazzy`. Both audit Compose runs explicitly injected domain 42; Docker environment inspection confirmed domain 42 and UDPv4. The direct non-root experiment also explicitly set both.

Host additionally inherited `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`. The image has FastDDS RMW libraries and no RMW override; its default is FastDDS. UDPv4 is a FastDDS setting, not an instruction to CycloneDDS. Middleware identity is therefore not identical even though the requested two environment settings match.

**OBSERVATION:** Early `ros2 node list` returned no names while `ros2 topic list -t` and actual subscriptions worked; `ros2 param dump /camera` stalled and was terminated. **HYPOTHESIS:** Discovery timing/daemon state, cross-RMW graph behavior, or node responsiveness. **EXPERIMENT:** Stop the daemon, then bounded `--no-daemon --spin-time 3` checks with host CycloneDDS and a temporary FastDDS override. **EVIDENCE:** Both later checks found `/camera` while the camera node was running without a physical device. The FastDDS parameter query responded `Parameter not set` in this no-device state; it is not a valid measurement of the earlier initialized camera parameter. **CONCLUSION:** Node/topic discovery is demonstrated. Middleware mismatch as the cause of the earlier stall is **UNCERTAIN**. Use bounded CLI queries and consistent middleware for the next rate comparison; do not globally change shell configuration from this audit.

Actual important topics, without assuming default names:

| Topic | Type | Live evidence |
|---|---|---|
| `/camera/image_raw` | `sensor_msgs/msg/Image` | IR1 messages received |
| `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | IR1 intrinsics received |
| `/camera/infra2/image_rect_raw` | `sensor_msgs/msg/Image` | IR2 messages received |
| `/camera/infra2/camera_info` | `sensor_msgs/msg/CameraInfo` | Discovered |
| `/camera/gyro/sample` | `sensor_msgs/msg/Imu` | Received |
| `/camera/accel/sample` | `sensor_msgs/msg/Imu` | Received |
| `/camera/imu` | `sensor_msgs/msg/Imu` | Combined samples received |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | One transient-local message with 11 transforms received |
| `/tf` | Not discovered | No dynamic TF publisher proven |
| `/diagnostics` | Not discovered | No diagnostics publisher proven |

Also discovered: `/camera/{gyro,accel}/imu_info` (`realsense2_camera_msgs/msg/IMUInfo`), motion and infrared metadata (`realsense2_camera_msgs/msg/Metadata`), `/camera/extrinsics/depth_to_{accel,gyro,infra1,infra2}` (`realsense2_camera_msgs/msg/Extrinsics`), `/rosout`, `/parameter_events`. Full actual list: `ROS_TOPICS.txt`.

## 6. Camera Stream Results

Root startup reported `RealSense ROS v4.58.1`, SDK built/running `2.58.1`, `Intel RealSense D435I`, serial `243322073847`, firmware `5.17.3.10`, USB `2.1`, Sync Mode Off. JSON `/config/advanced.json` loaded through the existing Compose command. No extra device preset writes were deliberately issued; the existing launch itself loads this preset.

Opened profiles: IR1 and IR2 Y8 640×480 at 15 FPS; accel MOTION_XYZ32F 100 Hz; gyro MOTION_XYZ32F 200 Hz. Color and depth disabled. IR2 is not explicitly enabled in the Compose command but was actually opened by its runtime defaults/configuration. Therefore two-IR current behavior is established by logs, not by assumption.

IR1 message: `/camera/image_raw`, `sensor_msgs/msg/Image`, 640×480, `mono8`, step 640, little endian, frame `camera_infra1_optical_frame`. IR2 frame is `camera_infra2_optical_frame`.

Controlled measurement: **2026-09-08T11:52:52.533677+00:00 to 2026-09-08T11:53:22.534577+00:00**, 30.001 s. Simultaneous host `rclpy` subscriptions used sensor-data best-effort QoS. Received rate is `(N−1)/(last arrival−first arrival)`; stamp rate uses header stamps. These are observed subscriber rates, not direct hardware acquisition rates. Startup/discovery losses and DDS/host scheduling can affect counts. No image-pixel quality assessment was performed; complete ROS messages alone would not prove artifact-free images.

| Topic | Received count | Arrival Hz | Stamp Hz | Max stamp gap (s) | Nonpositive stamp steps |
|---|---:|---:|---:|---:|---:|
| `/camera/image_raw` | 45 | 1.469 | 1.461 | 26.065096 | 0 |
| `/camera/infra2/image_rect_raw` | 45 | 1.469 | 1.461 | 26.065096 | 0 |
| `/camera/gyro/sample` | 5018 | 167.279 | 167.121 | 0.030469 | 0 |
| `/camera/accel/sample` | 3021 | 100.697 | 100.515 | 0.039307 | 0 |
| `/camera/imu` | 4634 | 154.506 | 154.356 | 0.035317 | 0 |
| `/camera/camera_info` | 43 | 1.402 | 1.401 | 26.065096 | 0 |

In this exact window, logs contain **17** `Incomplete video frame detected` and **17** `Frame Corrupted` occurrences. These are paired parts of the same notifications, not 34 independent corrupt frames. Warning frequency is approximately 0.567 notifications/s; it is not a reliable count of all dropped frames. Whole-run startup also contains a duplicated Left MIPI hardware-error notification; none occurred inside the measured window. A missing-default-configuration-file warning and the IMU calibration warning also occurred. The latter was emitted before data collection, and collection continued.

**CONCLUSION:** Two-IR image delivery fails a useful baseline at 15 FPS. Substantial frame gaps plus device-originated corruption notifications are sufficient for NO-GO, regardless of uncertainty in DDS rate loss attribution.

## 7. Monocular-First Bandwidth Experiment

**Completed after reattachment.** Root Case A and root Case B used the same immutable image, existing advanced JSON preset, mounts, host network/IPC, domain 42, UDPv4, FastDDS RMW, 640×480 Y8 at 15 FPS, gyro 200 Hz, accel 100 Hz and `unite_imu_method:=2`. Color/depth were disabled. Only `enable_infra2` changed. Opened profiles and bounded parameter readbacks confirm A enabled IR2 and B disabled it. Each container was stopped and its exited state captured before the next launch; the runner refused to launch with any running container. A premature request to run B was refused by this guard and did not start a container. Host process/device-owner checks showed no competing camera process.

| Measurement | Root A: IR1 + IR2 + IMU | Root B: IR1 + IMU |
|---|---:|---:|
| Local collection window, 2026-09-08 | 19:13:33–19:14:03 | 19:14:48–19:15:18 |
| Duration | 30.003 s | 30.001 s |
| IR1 / IR2 count | 23 / 22 | 15 / 0 |
| IR1 count / full window (Hz) | 0.767 | 0.500 |
| IR1 arrival rate between first/last received image (Hz) | 2.660 | 14.959 |
| IR1 maximum internal stamp gap | 6.514566 s | 0.066403 s |
| Raw gyro / accel / combined count | 4903 / 2996 / 4580 | 5016 / 3024 / 4658 |
| Raw gyro / accel / combined arrival Hz | 163.404 / 99.864 / 152.666 | 167.173 / 100.778 / 155.436 |
| Paired incomplete-frame notifications within window | 18 | 15 |
| Live method readback | 2 | 2 |
| IMU calibration fallback warning | Present | Present |
| Result | FAIL stability | FAIL stability |

**Measurement caveat:** The original observer's `(N−1)/(last arrival−first arrival)` rate and internal max-gap exclude silence at window boundaries. In B the 15 images span only about 0.936 seconds of the 30-second window. Its near-15-Hz burst and 66-ms internal maximum gap are **not** a stability PASS. A's IR1 messages span about 8.271 seconds. Whole-window counts make the missing delivery explicit. There was no pixel-quality assessment; the rate and corruption failures already reject recording readiness. Warning counts represent notifications, not a complete dropped-frame count.

**OBSERVATION:** Incomplete frames and severely deficient whole-window image delivery occur in both isolated root cases. **HYPOTHESIS:** Removing IR2 would restore stable acquisition on this link. **EXPERIMENT:** Same-settings sequential A/B, changing only IR2. **EVIDENCE:** `A_*`, `B_*`, `RESUME_SUMMARY.json`. **CONCLUSION:** Removing IR2 is insufficient under the tested conditions. The modest notification-count difference from one window per case does not establish a causal bandwidth improvement. USB 2.x, VM passthrough, physical transport, device state and the preset remain possible contributors; no verified USB3/native-host comparison was available.

The earlier attempted B remains excluded: it used non-root identity and briefly overlapped the initial root run before USB loss at 18:54:32. Its original evidence is preserved in `VIDEO_GROUP_INITIAL_LOG.txt` and `RUNTIME_CONTAINERS.jsonl`. The resumed A/B above is independent of that invalid comparison.

**Shutdown limitation:** All resumed containers ended with exit code 137 following bounded `docker stop -t 5`; they were stopped, but graceful SDK shutdown was not demonstrated. A finished at 19:14:16.807 before B started at 19:14:34.527; B finished at 19:15:30.810 before C started at 19:15:47.380. No simultaneous access occurred. Residual device state after forced shutdown is a remaining experimental limitation.

## 8. IMU Results

All three topics are `sensor_msgs/msg/Imu`:

| Stream | Topic | frame_id | Received Hz | Profile Hz |
|---|---|---|---:|---:|
| Raw gyro | `/camera/gyro/sample` | `camera_gyro_optical_frame` | 167.279 | 200 |
| Raw accel | `/camera/accel/sample` | `camera_accel_optical_frame` | 100.697 | 100 |
| Combined | `/camera/imu` | `camera_imu_optical_frame` | 154.506 | Nominal gyro cadence when united |

With no commanded motion, mean gyro was `[-0.003623, -0.004711, -0.002115] rad/s`, consistent with small stationary bias. Mean accel was `[0.137452, -4.406202, -8.702900] m/s²`; mean vector magnitude was `9.758213 m/s²`, approximately gravity. The camera's physical stationarity was not independently observed over SSH; these measurements are consistent with it, not proof of placement. Per-axis standard deviations and complete first samples are in the JSON evidence.

Received header stamps were strictly increasing on each measured topic (zero duplicate/backward steps). Maximum observed gaps: gyro 30.469 ms, accel 39.307 ms, combined 35.317 ms. Stamps use epoch-scale seconds close to host collection time, but this does not verify inter-sensor clock synchronization, timestamp latency, or precise image–IMU offset. No long-duration clock-drift test was performed.

Raw gyro's acceleration zeros and raw accel's angular velocity zeros are unused fields, not failed sensors. Combined messages contain both vectors; orientation covariance starts with `-1`, so orientation is not estimated. **CONCLUSION:** Raw and combined motion collection works in the root baseline, but delivered gyro/combined rates and later USB disappearance prevent a stable-stack PASS. Source-backed IMU unification caveat is below.

## 9. Calibration Findings

IR1 camera_info was received despite the IMU warning:

```yaml
topic: /camera/camera_info
frame_id: camera_infra1_optical_frame
width: 640
height: 480
distortion_model: plumb_bob
D: [0, 0, 0, 0, 0]
K: [388.5274353027344, 0, 319.10430908203125,
    0, 388.5274353027344, 239.55616760253906,
    0, 0, 1]
R: [1, 0, 0, 0, 1, 0, 0, 0, 1]
P: [388.5274353027344, 0, 319.10430908203125, 0,
    0, 388.5274353027344, 239.55616760253906, 0,
    0, 0, 1, 0]
```

**OBSERVATION:** SDK emitted `IMU Calibration is not available, default intrinsic and extrinsic will be used.` **HYPOTHESIS:** IMU EEPROM calibration retrieval failed or data is unavailable. **EXPERIMENT:** Inspect exact SDK v2.58.1 source and received camera_info/TF. **EVIDENCE:** `src/ds/ds-calib-parsers.cpp`, `mm_calib_handler` lines 17–36 catches an exception while retrieving IMU EEPROM; `get_imu_eeprom_raw` lines 57–62 issues MMER. The warning discards the specific exception, so it cannot distinguish transport failure from unavailable/malformed calibration. `dm_v2_imu_calib_parser` lines 124–252 provides fallback IMU scales/biases and mechanical extrinsics. **CONCLUSION:** Default IMU calibration is being used in this run; the underlying reason is **UNCERTAIN**, not proof the camera permanently lacks factory calibration. [Official SDK source v2.58.1](https://github.com/realsenseai/librealsense/blob/v2.58.1/src/ds/ds-calib-parsers.cpp).

Camera_info has plausible nonzero focal lengths and a valid structure for the active rectified IR stream. The IMU warning does not by itself invalidate image intrinsics. Geometric accuracy was not independently calibrated or validated against a target.

Camera-to-IMU transforms exist in `/tf_static`, and depth-to-gyro/accel extrinsics topics were discovered. Both camera_link-to-motion-frame translations received are approximately `[-0.01174, -0.00552, 0.00510] m` in ROS camera-link coordinates, with identity rotation before the optical-frame transform. These are compatible with the SDK's D435i CAD fallback after coordinate conversion. Their presence is not proof of per-device extrinsic calibration. Full transform tree is saved in `TF_STATIC.json`.

This warning did not immediately block sensor messages, so it is not independently a bag-collection blocker. For VIO, IMU bias/scale, noise, axis conventions, camera-to-IMU transform direction and timing must be verified. Compare with `third_party/ORB_SLAM3_ROS2/config/Monocular-Inertial/RealSense_D435i.yaml`: that static example uses fx=fy=382.613, cx=320.183, cy=236.455, 30 FPS, a nontrivial `IMU.T_b_c1`, and nominal 200 Hz/noise parameters. Live intrinsics and 15 FPS differ. The YAML is not established calibration for this serial number; do not copy live TF into its matrix without checking convention/direction. No YAML was overwritten.

## 10. unite_imu_method Findings

Inspected both pinned checkout 4.58.4 and local Git tag 4.58.1 corresponding to the runtime package version, using `git show` without changing revisions. Exact excerpts with line numbers are saved in `IMU_SOURCE.txt`.

| Method | Declared meaning | Implemented operation when selected |
|---|---|---|
| 0 | NONE | Raw motion callback remains; no united callback on ordinary motion path |
| 1 | COPY | Cache most recent acceleration; emit gyro vector plus cached acceleration using gyro timestamp |
| 2 | LINEAR_INTERPOLATION | Buffer gyro readings between accelerometer samples; interpolate acceleration at gyro timestamps and publish when the next accel sample brackets them |

Important callback trace (4.58.1 line numbers):

1. `include/base_realsense_node.h:146`: enum NONE, COPY, LINEAR_INTERPOLATION → 0,1,2.
2. `src/parameters.cpp:109–159`, `setDynamicParams`: registers `unite_imu_method`, sets `_imu_sync_method`, warns about re-enabling streams. Runtime startup warning confirms this setter path was triggered; exact live readback was not obtained before disconnect.
3. `src/rs_node_setup.cpp:147–150`: `imu_callback_function` first invokes raw `imu_callback(frame)`, then, if configured method is nonzero, invokes **`imu_callback_sync(frame)` without passing the method**.
4. `rs_node_setup.cpp:177–180`: a motion sensor uses this callback. `src/ros_sensor.cpp:57–92,250–265` stores it and passes the forwarding callback to `rs2::sensor::start`.
5. `include/base_realsense_node.h:323`: omitted second argument defaults to **COPY** (pinned 4.58.4 header line 322).
6. `src/base_realsense_node.cpp:428–456`: `imu_callback_sync` switches on the passed argument, not the member setting. COPY helper lines 399–412; interpolation helper lines 354–395; united message creation lines 334–347 uses gyro timestamp.
7. A separate `multiple_message_callback` path explicitly receives `_imu_sync_method`; this does not establish its use for this ordinary D435i Motion Module.

**OBSERVATION:** Method 2 was requested and combined IMU was received. **HYPOTHESIS:** It performs interpolation. **EXPERIMENT:** Trace parameter → motion-sensor callback → synchronization switch. **EVIDENCE:** Both inspected versions omit the method argument on the relevant callback and default to COPY. **CONCLUSION:** The inspected source's ordinary motion path selects COPY for either nonzero setting. Merely setting 2 is not evidence that interpolation is used. For the installed binary, the source/version match supports this inference, but exact binary provenance/patches and sample-by-sample interpolation were not verified: at that stage actual packaged-binary behavior was **UNCERTAIN**. The resumed sample correlation in section 16 now strongly supports COPY in the installed binary, with live method-2 readback; “method 2 definitely interpolates” is rejected. No source was modified.

## 11. Rosbag Readiness

**NO-GO after resumed root A/B as well.** The user-required stability gate was not met. No short recording, `ros2 bag info`, or replay was performed; those are **NOT TESTED**, not successful. No empty/test dataset was manufactured. `data/bags/2026-09-08/` was not created because there is no valid bag to place there.

The existing `.gitignore` rule `data/bags/*` covers a future `data/bags/2026-09-08/audit_probe/metadata.yaml` and `test.mcap`, verified with `git check-ignore -v`. Existing `*.db3` and `*.mcap` rules provide additional coverage. Raw bags remain ignored.

After a stable isolated IR1-only run, record a short bag with actual `/camera/image_raw`, `/camera/camera_info`, `/camera/gyro/sample`, `/camera/accel/sample`, `/camera/imu`, `/tf_static`, plus `/tf` and `/diagnostics` if they exist. Verify transient-local TF capture, topic counts, timestamp gaps, and clean recorder stop. Run bag info; stop the live camera before replay so replay visibility cannot be mistaken for live data. This remains future work, not an accomplished test.

## 12. ORB-SLAM3 Readiness

| Requested path | Decision | Reason |
|---|---|---|
| Official EuRoC benchmark | **NO-GO for execution in this audited workspace today** | No dataset in `data/datasets` beyond `.gitkeep`, executable/benchmark validation not performed, and user explicitly deferred SLAM. D435i faults do not technically block a saved EuRoC benchmark; this is an unverified local prerequisite decision, not a camera dependency claim. |
| Saved D435i rosbag → mono-inertial ORB-SLAM3 | **NO-GO** | No validated bag; unstable images; calibration and actual unification behavior not validated. |
| Live D435i → mono-inertial ORB-SLAM3 | **NO-GO** | USB device absent finally; stable IR1+IMU and complete non-root path not proven. |

ORB-SLAM3 was not started or modified. Controller and STM32 code were untouched.

## 13. Failure Analysis

| Observation | Hypothesis | Evidence | Confidence | Next Experiment |
|---|---|---|---|---|
| Normal user cannot open video; root succeeds | Missing container supplementary video group | UID/groups plus all-six open tests and actual startup logs | High, confirmed | Resumed C opened IR1; fix demonstrated IIO scan-control access before repeating full non-root streaming |
| GID 44 cannot open hidraw3 | Backend may require additional device-specific access | 0600 root-owned hidraw; no complete non-root stream | High for mode/access; resumed C identifies IIO scan-control dependency | Review narrowly scoped host RealSense IIO permissions; hidraw changes alone are not justified |
| IR frames have long gaps and incomplete notifications | Two-IR bandwidth or USB passthrough issue | 480M; 17 notifications/30 s; 26.065 s image gap | High observation, low causal confidence | Completed root A/B: both fail; next compare verified USB3/native-host and controlled graceful teardown |
| Left MIPI hardware error | Device/internal transport issue | Startup notification in root run | High occurrence, UNCERTAIN cause | Repeat minimal stream on verified USB3/native Linux with same camera |
| USB disconnect and SDK crash during attempted B | Device/passthrough fault and/or concurrent camera access | Kernel disconnect; overlapping containers; SDK segfault | High chronology, UNCERTAIN cause | Resumed USB loss recurred during isolated C; overlap is not required for recurrence; cause still uncertain |
| Gyro and combined delivered below nominal | SDK loss, DDS/QoS delivery, or host scheduling | 167.279 and 154.506 Hz received | Medium; measurement method is clear, loss location unknown | Matched-RMW A/B still below nominal; next locate loss with publisher/backend instrumentation on stable USB |
| Topic data visible, early node list empty/query stalled | Discovery timing/daemon or service responsiveness | Later bounded checks find node under both RMWs | High evidence, UNCERTAIN cause | Resumed A/B queries succeeded; retain bounded matched-RMW queries |
| IMU calibration warning | EEPROM unavailable/read failed | Exact SDK catch path; fallback-compatible TF | High fallback, UNCERTAIN root cause | Re-read under reliable USB; distinguish transport failure from persistent calibration state |
| Method 2 requested, callback defaults COPY | Requested interpolation bypassed on ordinary motion path | Matching-version and pinned source agree | High source finding; binary behavior UNCERTAIN | Completed correlation supports COPY; assess runtime callback fix and validate after reliable transport |
| Runtime 4.58.1 versus checkout 4.58.4 | Package-based Docker build bypasses pinned source | Dockerfile, dpkg and Git | High, confirmed | Decide/document exact runtime build provenance before reproducibility claims |

## 14. Recommended Next Actions

### MUST DO NEXT

1. Restore attachment again and test a verified USB3/native-Linux path if available. Controlled root IR1-only already failed on the current USB2/VM path; simply disabling IR2 is not sufficient. Keep tests exclusive and establish graceful SDK shutdown before repeating sustained measurements.
2. Address the demonstrated non-root IIO scan-control access failure using narrowly scoped host RealSense device rules/groups after checking the recreated nodes. Supplementary video GID 44 fixes the video path only. No system permission changes were made in this audit.
3. Once IR1+IMU delivery is stable, validate sustained timing/image quality and actual unification behavior, then short bag/info/replay. Do not start D435i SLAM before those gates pass.

### GOOD TO DO SOON

- Use an explicit, repository-owned runtime override for domain 42, UDPv4, group 44 and IR2 disabled after reviewing the evidence; pin the actual image/package provenance.
- Matched FastDDS A/B is complete; extend timing duration and inspect pixels after transport stability improves.
- Investigate persistent EEPROM warnings on a reliable connection and verify camera/IMU calibration conventions for this serial.

### DEFER

- ORB-SLAM3 launch, final S00/S01/S02 collection, stereo operation, calibration replacement, firmware updates and upstream source fixes until the sensor baseline is proven.

## 15. Evidence Appendix

All evidence is under `experiments/2026-09-08-d435i-baseline/`:

- `HOST.txt`: date, Git SHAs/status, OS/kernel/Docker/ROS, package versions, image ID, bag-ignore checks.
- `FINAL_CHECKS.txt`: final Git status, unchanged submodule SHAs, no running containers, camera still absent.
- `USB.txt`: preserved earlier evidence plus live initial/final topology, modes, HID/IIO checks.
- `DOCKER_DEVICE_ACCESS.txt`: rendered Compose, image identity, exact three-way device-open commands and results.
- `CURRENT_NORMAL_LOG.txt`: normal service fails to enumerate due to permissions.
- `CURRENT_ROOT_LOG.txt`: full root startup and subsequent frame notifications.
- `CURRENT_ROOT_RATES.json`: complete 30-second simultaneous measurements and first messages.
- `SENSOR_RATES.txt`: window boundaries, paired warning counts, topic rates/samples.
- `CAMERA_INFO.txt`, `TF_STATIC.json`: received camera intrinsics and transforms.
- `ROS_TOPICS.txt`: actual discovery and bounded RMW comparison; early empty node output is described above.
- `VIDEO_GROUP_INITIAL_LOG.txt`: failed/confounded initial single-IR attempt and no-device retry. Not a valid bandwidth comparison.
- `KERNEL_LOG.txt`: report errors, UVC probe failures, disconnect and SDK crash chronology.
- `RUNTIME_CONTAINERS.jsonl`: actual container commands, users, environment, mounts and state snapshots.
- `IMU_SOURCE.txt`: line-numbered pinned and runtime-tag source excerpts; `IMU_NOTES.md`: interpretation limits.
- `LIBREALSENSE_CALIB_SOURCE.txt`: official v2.58.1 source URL and numbered source used for calibration analysis.
- `measure_topics.py`: read-only simultaneous subscriber used for the live measurement.

Commands actually used (the complete container argv is in JSONL; exact permission probe invocations in DOCKER_DEVICE_ACCESS.txt):

```bash
git rev-parse HEAD
git status --short
git submodule status --recursive
docker --version
docker compose version
uname -a
cat /etc/os-release
lsusb
lsusb -t
ls -l /dev/video* /dev/hidraw*
id
getent group video
cat /sys/bus/usb/devices/5-3/speed
ls -l /sys/class/hidraw
find /sys/bus/iio/devices -maxdepth 2 -name name -exec cat {} \;
docker compose -f third_party/ORB_SLAM3_ROS2/docker-compose.yaml config
docker image inspect realsense:latest
docker compose -f third_party/ORB_SLAM3_ROS2/docker-compose.yaml run -d --no-deps --name d435i-audit-current -e ROS_DOMAIN_ID=42 realsense
docker compose -f third_party/ORB_SLAM3_ROS2/docker-compose.yaml run -d --no-deps --user 0:0 --name d435i-audit-root -e ROS_DOMAIN_ID=42 realsense
docker exec d435i-audit-root printenv ROS_DOMAIN_ID FASTDDS_BUILTIN_TRANSPORTS ROS_DISTRO
source /opt/ros/jazzy/setup.bash
ros2 daemon stop
ros2 node list
ros2 topic list -t
python3 experiments/2026-09-08-d435i-baseline/measure_topics.py 30
ros2 param dump /camera  # stalled; terminated; no usable dump
printenv RMW_IMPLEMENTATION ROS_DOMAIN_ID FASTDDS_BUILTIN_TRANSPORTS ROS_DISTRO
timeout 10 ros2 node list --no-daemon --spin-time 3
RMW_IMPLEMENTATION=rmw_fastrtps_cpp timeout 10 ros2 node list --no-daemon --spin-time 3
RMW_IMPLEMENTATION=rmw_fastrtps_cpp timeout 10 ros2 param get /camera unite_imu_method
journalctl -k --since '2026-09-08 18:50:00' --no-pager
git -C third_party/realsense-ros show 4.58.1:realsense2_camera/src/rs_node_setup.cpp
git -C third_party/realsense-ros show 4.58.1:realsense2_camera/src/base_realsense_node.cpp
git -C third_party/realsense-ros show 4.58.1:realsense2_camera/src/parameters.cpp
git -C third_party/realsense-ros show 4.58.1:realsense2_camera/src/ros_sensor.cpp
git -C third_party/realsense-ros show 4.58.1:realsense2_camera/include/base_realsense_node.h
git check-ignore -v data/bags/2026-09-08/audit_probe/metadata.yaml data/bags/2026-09-08/audit_probe/test.mcap
docker stop -t 5 d435i-audit-current
docker stop -t 5 d435i-audit-root
docker stop -t 5 d435i-audit-video
docker ps
```

Logs were captured with `docker logs --timestamps`. The calibration source was fetched read-only from the official `v2.58.1` raw GitHub URL. No package installation was performed. Docker root test and three permission probes use the already-built image. All test containers are stopped; no destructive Docker cleanup was run.

Final `git status --short`:

```text
?? D435I_BASELINE_AUDIT.md
?? experiments/
```

## 16. Resumed Live Audit: Additional Findings and Final State

### Non-root Case C: concrete IMU access failure

C used B's IR1-only configuration, with identity changed to `richard` (1001:1001) plus supplementary GID 44. It detected serial 243322073847 and opened IR1 Y8 640×480×15. At 19:15:50.978 it failed while starting Motion Module:

```text
Failed to open scan_element /sys/devices/pci0000:00/0000:00:04.0/usb5/5-3/5-3:1.5/0003:8086:0B3A.0005/HID-SENSOR-200076.4.auto/iio:device1/scan_elements/in_anglvel_x_en Last Error: Permission denied
```

The logs also identify denied y/z/timestamp scan controls and a trigger/current_trigger warning. This establishes use of the HID/IIO path and a specific non-root access blocker; it does not establish every required permission. No chmod, udev, group membership, firmware, upstream source or system configuration changes were made. Because the device disappeared, recreated-node modes and a narrowly scoped permission fix still require live verification. GID 44 alone is **FAIL for complete IR1+IMU**, although video opening succeeds.

Kernel chronology: status-URB failure at 19:15:49, USB disconnect of device 3 at 19:15:51. C then reports missing `/dev/video0` and no devices. Its later 30-second observer window receives zero messages on every measured topic; this is a failed-start observation, **not a valid sensor-rate or corruption comparison**. No overlapping camera process is evidenced. The non-root permission error precedes the disconnect, but causation is not proven; forced teardown of earlier cases, device/USB/passthrough state remain potential contributors. The C container was stopped once its device-loss logs were inspected; no further sensor starts were attempted.

### Installed-binary IMU behavior

The resumed observer preserves raw header stamps and six motion-vector components in `A_RATES.json` and `B_RATES.json`. Both initialized camera nodes returned `Integer value is: 2`. `analyze_resume.py` compares united samples with raw gyro values at exactly equal captured stamps, exact raw acceleration vectors, and timestamp-bracketed linear interpolation. Numeric stamp comparisons use epoch seconds as floating point; interpolation tolerance is 1e-6 m/s². Cross-topic subscriber losses and callback order limit exact matching.

| Correlation | A | B |
|---|---:|---:|
| United samples | 4580 | 4658 |
| Exact raw gyro stamp + angular vector match | 3096 | 3251 |
| United acceleration equals some received raw accel vector exactly | 4578 | 4655 |
| Samples bracketed by received raw accel timestamps | 4579 | 4658 |
| Exact match to timestamp-preceding raw accel | 3490 | 3363 |
| Samples where copy and interpolation differ by >1e-5 m/s² | 4557 | 4648 |
| Of those, match preceding-sample COPY exactly | 3471 | 3353 |
| Of those, match bracketed interpolation within 1e-6 m/s² | 0 | 0 |

**Conclusion:** Strong empirical support for COPY-like behavior in this installed binary despite method 2, consistent with the already-inspected callback default. The “any raw vector” check alone is not temporal proof (stationary/quantized vectors can repeat); preceding-sample and distinguishable-interpolation checks provide additional evidence. Incomplete raw-topic delivery and callback ordering prevent classifying every united sample or proving exact binary provenance. No method-1 A/B or source fix was performed.

All received streams in A/B had zero nonpositive timestamp steps. Gyro/combined arrival rates remained below the requested 200 Hz with matched FastDDS. Accel norms averaged approximately 9.758 m/s² in A and 9.778 m/s² in B; no physical motion was commanded or independently observed. Calibration fallback warnings persisted in A, B and C. `/camera` discovery and bounded parameter reads succeeded in A/B; this does not locate the cause of the original discovery stall.

### Evidence and final state

New evidence is saved beside, without overwriting, the initial run:

- `run_resume.py`: exact sequential experiment runner and exclusivity guard; `measure_resume.py`: original observer extended to retain raw IMU samples.
- `A_COMMAND.json`, `B_COMMAND.json`, `C_COMMAND.json`: exact Docker argv using the prior container's immutable image and mounts.
- `{A,B,C}_INSPECT.json`, `_STATE_AFTER.json`, `_START.txt`, `_STOP.txt`: identities, settings and lifecycle evidence.
- `{A,B,C}_HOST_OWNERS.txt`, `_USB_BEFORE.txt`, `_USB_AFTER.txt`: isolation and topology observations.
- `{A,B,C}_RATES.json`, `_PARAMETERS.txt`, `_LOG.txt`: simultaneous observations, bounded queries and timestamped full logs. C has no valid initialized parameter readback or sensor samples.
- `analyze_resume.py`, `RESUME_SUMMARY.json`: reproducible whole-window rates, notification counts and IMU correlation.
- `RESUME_KERNEL_LOG.txt`, `C_LOG_SNAPSHOT.txt`, `RESUME_FINAL_CHECKS.txt`: second disconnection and final stopped/absent state.

All audit containers are stopped; resumed exit codes are 137, not graceful-shutdown passes. USB 8086:0b3a and camera video nodes are absent at the resumed final check. No bag was recorded/replayed because both controlled root image configurations failed stability. No SLAM was launched. Completed static/source/version work was retained rather than repeated. Only the audit document and experiment evidence/scripts were added or updated; Git status remains `?? D435I_BASELINE_AUDIT.md` and `?? experiments/`.
