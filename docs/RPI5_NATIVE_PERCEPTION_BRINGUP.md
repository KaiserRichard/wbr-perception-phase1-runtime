# 1. Target architecture

**Preparation only, 2026-09-09. Raspberry Pi hardware is unavailable. Nothing in this document has been validated on a Raspberry Pi.** No packages were installed, camera or SLAM processes started, images built, commits made, or changes pushed during this task. Only this plan was created. Commands below are future instructions, not execution evidence.

Control path:

```text
MacBook → SSH / VS Code Remote SSH → Raspberry Pi 5
        → Ubuntu 24.04 64-bit ARM64 → ROS 2 Jazzy → D435i native USB3
Later:  → ORB_SLAM3_ROS2 → WBR
```

Actual sensor-data direction:

```text
D435i → direct USB3 → Pi Linux kernel → native librealsense / realsense-ros
      → ROS topics → gated rosbag recording / replay
      → later ORB-SLAM3 VIO → future WBR integration
```

| Layer | Previous UTM path | Intended Pi path |
|---|---|---|
| Physical attachment | D435i attached through Mac / UTM USB passthrough | D435i cabled directly to a Pi USB3 port |
| Virtualization | Mac → UTM/QEMU → Ubuntu x86_64 guest | **UTM/QEMU guest and USB passthrough disappear** |
| Linux | Ubuntu guest kernel | Ubuntu ARM64 kernel on physical Pi |
| Driver packaging | RealSense in Docker, sharing the guest kernel | Native SDK and ROS wrapper for the first baseline |
| Container layer | Device mounts, container UID/GIDs, privileges, environment | **Initially absent**; reconsider only after native stability |
| Control | Mac controls the VM | Mac controls the Pi over SSH; USB and local ROS acquisition do not traverse SSH |

Removing virtualization changes an important variable; it does not establish the cause of the UTM failures or promise that the camera will work. Mac/UTM topology is project context; saved Linux evidence establishes x86_64, QEMU-style devices, and guest-visible 480M USB. See the [Docker architecture review](DOCKER_RUNTIME_ARCHITECTURE_REVIEW.md) and [baseline audit](../D435I_BASELINE_AUDIT.md).

# 2. Machine roles

| Machine | Role |
|---|---|
| MacBook | Research, control, Codex, Obsidian, Git, SSH and VS Code Remote SSH. Keep private SSH keys here. |
| Pi 5 | Primary physical D435i acquisition target; intended edge runtime, live SLAM, and eventual WBR deployment. Achievable SLAM performance remains unmeasured. |
| Lab workstation | Native x86 reference platform; heavy benchmarking, simulation, profiling, GPU workloads, and physical hardware cross-checks. |
| UTM | Development and offline sandbox: source inspection, documentation and saved-data work. Its failed USB baseline is historical evidence, not a substitute for native testing. |

The Pi's future perception output does not transfer hard-real-time balance, torque, CAN, or safety ownership from STM32H7; the existing [README](../README.md) retains that separation.

# 3. Pi base-system preparation

Every command is labeled **[MAC]**, **[PI]**, or **[PHYSICAL]**. These are location labels, not shell syntax: omit the label when typing. A label on a multiline command applies to its continuation lines. [PI] always means the future physical Pi, never today's Ubuntu VM. Commands run in a VS Code remote terminal are [PI]. Example user `richard`, hostname `wbr-pi5`, and SSH alias `wbr-pi5` are editable administrative defaults. Replace `PI_IP` with the address learned at boot.

**PREPARE NOW**

- [MAC] Select the official **Ubuntu 24.04 LTS ARM64 Raspberry Pi image**, with Server proposed for the initial SSH workflow. Save its filename, download URL and published checksum; verify the download. Do not substitute the generic amd64 installer or silently move to a newer Ubuntu release. Ubuntu lists Pi 5 support for 24.04 in its [board installation guide](https://ubuntu.com/hardware/docs/boards/how-to/ubuntu_supported/raspberry-pi/).
- [MAC] Prepare the imager settings: hostname, non-root sudo user, timezone, network credentials and the Mac's public SSH key. If the chosen Ubuntu image/imager does not apply these settings, use its supported cloud-init/headless setup or a local console on arrival. Never put private keys or Wi-Fi secrets in Git.
- [MAC] Reuse an appropriate existing SSH key, or create a dedicated key at a new, unused filename. Prepare an SSH config entry and VS Code Remote SSH connection. No Pi connection can be checked today.
- [MAC] Review repository access, including private parent-repository access and recursive submodules. Prefer a scoped read-only Pi credential for GitHub; do not copy the Mac private key to the Pi. The SSH login key and GitHub clone authentication serve different purposes.
- [MAC] Save this plan locally for arrival: it is uncommitted and therefore **will not appear in a fresh Git clone**. Transfer the document separately if needed, without committing or pushing for this task.
- [PHYSICAL] Prepare a USB3 data cable, direct Pi USB3 port access, suitable PSU, active cooling, boot medium and storage options. Record the Pi RAM size when known.
- [MAC] Prepare an experiment manifest containing image checksum, OS/kernel, Pi model/RAM, PSU/cable/port, camera serial/firmware, repository revisions, runtime packages, SDK backend, ROS environment, settings, times, and results. All Pi result fields remain `NOT TESTED`.

Optional new key, only if this filename does not already exist:

```text
[MAC] ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_wbr_pi5 -C wbr-pi5-control
[MAC] cat ~/.ssh/id_ed25519_wbr_pi5.pub
```

**RUN WHEN PI ARRIVES**

1. [PHYSICAL] Flash the chosen removable boot medium after checking its identity and contents; install cooling, connect network and suitable power, and boot with the D435i initially unplugged. Complete first-boot/cloud-init setup.
2. [PI] At the initial console, verify Ubuntu 24.04 and ARM64. Install SSH/Git/basic diagnostics on the Pi, set the intended hostname, and enable SSH. Use the prepared non-root user; create it through installation if absent.

```text
[PI] cat /etc/os-release
[PI] uname -a
[PI] dpkg --print-architecture
[PI] sudo hostnamectl set-hostname wbr-pi5
[PI] sudo apt update
[PI] sudo apt install openssh-server git ca-certificates curl locales usbutils v4l-utils acl build-essential cmake ninja-build pkg-config python3-venv
[PI] sudo systemctl enable --now ssh
[PI] hostname -I
[PI] ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Expected architecture: `uname -m` is `aarch64`; Debian package architecture is `arm64`. Compare the SSH host fingerprint with the Pi console on the first Mac connection. Install the public key through imager/cloud-init or the initial console's `~/.ssh/authorized_keys` with directory mode 700 and file mode 600. Keep the console/session available until a second key-authenticated session succeeds. Password-login hardening follows that check, not before it.

For login, use the private-key filename with `-i`:

```text
[MAC] ssh -i ~/.ssh/id_ed25519_wbr_pi5 richard@PI_IP
```

Configure `~/.ssh/config` on the Mac with alias `wbr-pi5`, `HostName PI_IP`, `User richard`, `IdentityFile ~/.ssh/id_ed25519_wbr_pi5`, and `IdentitiesOnly yes`. Open that host through VS Code Remote SSH. Prefer Ethernet for repeatability; local sensor measurements stay on the Pi regardless of control network.

3. [PI] Establish repository access and clone the parent and all nested submodules. Ordinary recursive initialization uses recorded gitlinks; do not use submodule remote-update mode to advance branches.

```text
[PI] git clone --recurse-submodules git@github.com:KaiserRichard/wbr-perception-phase1-runtime.git ~/wbr-perception-phase1-runtime
[PI] cd ~/wbr-perception-phase1-runtime
[PI] git submodule update --init --recursive
[PI] git rev-parse HEAD
[PI] git submodule status --recursive
[PI] git status --short
```

If GitHub SSH credentials are not available, configure an authorized HTTPS credential flow; this is an access prerequisite, not a reason to copy credentials into the repository.

4. [PI] Install ROS 2 Jazzy using its [official Debian installation procedure](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html), including UTF-8 locale, Universe, ROS apt source/key setup and the required Noble update suites. The [official documentation source](https://raw.githubusercontent.com/ros2/ros2_documentation/jazzy/source/Installation/Ubuntu-Install-Debs.rst) also lists the ARM64 package status. Follow that repository setup before the commands below; do not use obsolete key instructions or amd64-only downloads.

```text
[PI] locale
[PI] sudo apt update
[PI] sudo apt install ros-jazzy-ros-base ros-dev-tools ros-jazzy-rosbag2 ros-jazzy-tf2-tools ros-jazzy-rmw-fastrtps-cpp
[PI] source /opt/ros/jazzy/setup.bash
```

These are intended package names, not package resolution verified on the Pi. Install sensor packages using section 5. Defer ORB/Pangolin/PCL build dependencies until section 10. Source builds may later need `libusb-1.0-0-dev`, `libudev-dev`, `libssl-dev`, OpenCV, Eigen, Boost serialization, Mesa/OpenGL development libraries and a pinned Pangolin/Sophus provision; resolve the exact set for the chosen source revisions then.

5. [PI] Enable/check the installed time synchronization service. Use UTC in machine-readable experiment timestamps and record Asia/Ho_Chi_Minh offsets for comparison. Wait for synchronization before measuring; no clock stepping or manual time changes during a run. Host NTP does not prove camera-to-IMU timestamp alignment.

```text
[PI] sudo timedatectl set-timezone Asia/Ho_Chi_Minh
[PI] sudo timedatectl set-ntp true
[PI] timedatectl status
[PI] date --iso-8601=seconds
[PI] df -h
[PI] lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS,MODEL
[PI] free -h
```

6. [PHYSICAL] Provide active cooling and a PSU with sufficient Pi/USB load margin. Raspberry Pi documents a 5A supply recommendation for Pi 5 and a USB budget of 1.6A with a suitable supply versus 600mA with a 3A supply; the fan also shares that peripheral budget. Do not assume a laptop charger supplies the required profile or override current limits to compensate for inadequate power. See [official power and cooling guidance](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html).
7. [PI] Separate source, build artifacts and datasets. For planning, IR1 Y8 640×480×15 is **4.608 MB/s image payload**, about **138 MB/30 seconds** or **16.6 GB/hour**, before ROS serialization, IMU, metadata and storage overhead. These are arithmetic estimates, not throughput measurements. Choose SD versus SSD/NVMe with management; reserve at least twice the estimated probe size plus 10 GB OS/build headroom before a probe. Long sessions require their own capacity budget and backup policy. Avoid USB storage competing with the camera during the first sensor-only test; test the chosen recording storage after that gate. Do not assume swap compensates for insufficient runtime RAM or protects SD endurance.

# 4. ARM64 compatibility audit

Inspection anchor: parent HEAD `144746c072b6655b82a5a1d71898a91aaab05b07`; working tree initially clean. Recursive submodules:

| Source | Recorded revision |
|---|---|
| Official ORB_SLAM3 | `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4` |
| ORB_SLAM3_ROS2 | `efd7acd9ea31bfdbcd843a4c90eeaa85f7e80dd8` |
| Wrapper's embedded ORB_SLAM3 | `0f29ad5f563269a13109d81eb886916cc5960136` |
| Calibration submodule | `92ad7a5b4ad9616b98221ae140301f8bbc0a0782` |
| realsense-ros | `9a11121700cb4780e273e34141f6402fe184321d` (`4.58.4`) |

Classification meanings: **PASS FROM STATIC INSPECTION** clears only the named source-level concern; **LIKELY COMPATIBLE** has supporting platform/source evidence but no target test; **REQUIRES BUILD TEST ON PI** means package/build/link/runtime behavior is unresolved; **KNOWN BLOCKER** identifies a concrete incompatibility in the current artifact/configuration or a proven defect blocking the stated use. None means Pi validation.

Path abbreviations below: O = `third_party/ORB_SLAM3`; W = `third_party/ORB_SLAM3_ROS2`; C = `W/ros2_realsense_d435i_camera_calibration`; R = `third_party/realsense-ros`. They refer to repository paths, not shell variables.

| Item / evidence | Classification | Migration consequence / required check |
|---|---|---|
| Ubuntu 24.04 + Jazzy ARM64; official Ubuntu board matrix and ROS package platform documentation linked above | LIKELY COMPATIBLE | Supported platform combination; actual Pi boot, package resolution and USB kernel behavior still untested. |
| All three Dockerfiles: [tools](../docker/Dockerfile.jazzy-tools), [wrapper](../third_party/ORB_SLAM3_ROS2/Dockerfile), [camera](../third_party/ORB_SLAM3_ROS2/ros2_realsense_d435i_camera_calibration/camera.Dockerfile) use `ros:jazzy-ros-base`; no forced amd64 platform in inspected Docker/Compose files | PASS FROM STATIC INSPECTION | No recipe-level x86 base restriction. Official ROS image metadata advertises `amd64, arm64v8`; mutable tags and dependency availability still require target resolution/build. See [official image definitions](https://raw.githubusercontent.com/docker-library/official-images/master/library/ros). |
| Seven existing project images inspected read-only today: all `linux/amd64` (inventory below) | KNOWN BLOCKER | These artifacts cannot be reused as native ARM64 runtime images. Rebuild for ARM64 later; CPU emulation is outside the native baseline. This says nothing about unpublished remote images. |
| W/docker-compose.yaml, `base.deploy.resources.reservations.devices`: `driver: nvidia`, count 1, GPU capability; inherited by `orb_slam3` | KNOWN BLOCKER | Stock Pi 5 cannot satisfy the current NVIDIA reservation. Future Pi-specific Compose must remove that requirement. It is not a mandatory CUDA dependency of the ORB core source. |
| Full checkout file scan excluding `.git`: no ELF files or `.so`, `.a`, `.deb`, `.whl`, `.AppImage` candidates found | PASS FROM STATIC INSPECTION | No discovered prebuilt executable/library payload to migrate in this checkout. Vocabulary archives are model data, not CPU executables. Rebuild all future libraries and avoid copying VM build/install trees. Compressed arbitrary payloads were not exhaustively unpacked. |
| O/CMakeLists.txt and W/ORB_SLAM3/CMakeLists.txt release flags; both DBoW2 CMake files; official g2o release flags: `-march=native` | REQUIRES BUILD TEST ON PI | Host-tuned flag is not intrinsically x86-only. Validate native AArch64 compiler handling and generated code. It is unsuitable as an unexplained cross-build/distribution policy. Embedded g2o's corresponding native flags are commented out. |
| Inspected ORB core/vendor C/C++/CMake/shell sources: no explicit `-msse`, `-mavx`, x86 intrinsic-header or amd64/x86_64 requirements found | PASS FROM STATIC INSPECTION | Clears the searched hard-coded ISA patterns only; does not establish full portability of dependencies or compiler-generated code. |
| O/build.sh: bare `make -j` for dependencies and `-j4` at top; embedded build.sh: bare `-j`, `-j16`, plus removal of its build directory | REQUIRES BUILD TEST ON PI | Plan controlled stage builds starting with one job, increasing only with measured RAM/thermal margin. Do not invoke these helpers unchanged. An environment parallelism variable alone does not override explicit shell `make -j16`. |
| Both ORB trees require OpenCV 4.4 discovery, Eigen, Pangolin, Boost serialization and crypto; old CMake policies/C++11 flags; wrapper uses C++17 and PCL 1.14 | REQUIRES BUILD TEST ON PI | Resolve exact Noble ARM64 packages, ABI and compiler compatibility. A newer compiler and dependency set is not proven by source inspection. |
| W/Dockerfile requests `ros-jazzy-pangolin`; W/CMakeLists.txt requires external Sophus and Pangolin; both ORB libraries compile viewer code | REQUIRES BUILD TEST ON PI | Verify package candidates, CMake exports and OpenGL linkage. SSH/Remote SSH does not provide a local GL context. Disabling runtime viewer does not automatically remove Pangolin's build dependency. Establish a headless mode separately. |
| W/CMakeLists.txt requires embedded `ORB_SLAM3/build/ORB_SLAM3Config.cmake`, installs generated `.so` files; W/Dockerfile's ORB and colcon builds are commented out | REQUIRES BUILD TEST ON PI | Dependency image is not a built SLAM application. Build embedded ORB/dependencies before wrapper. The official O checkout is a different revision and cannot silently replace the embedded export. |
| Docker apt lists use architecture-neutral names; no explicit x86-only apt package found, but include PCL/Nav2/RViz/RealSense and unversioned dependencies | REQUIRES BUILD TEST ON PI | Architecture-neutral names do not prove ARM64 availability or compatible versions. Query apt on Pi and save the resolution; sensor-first installation excludes these optional heavy stacks. |
| R/realsense2_camera/CMakeLists.txt requests SDK ≥2.58.0; GPU extension depends on build options; SDK is not a submodule here | REQUIRES BUILD TEST ON PI | Resolve and record the native SDK, backend, headers/runtime and udev provenance. Do not assume Pi kernel/DKMS support from an Ubuntu package name. |
| Camera image installs binary ROS wrapper 4.58.1 and SDK 2.58.1 in yesterday's evidence; pinned R source is 4.58.4 | KNOWN BLOCKER | Current source pin does not pin the executable runtime. Blocks a claim of reproducible source-to-runtime correspondence; decide package or source pinning before declaring a reproducible baseline. |
| R/src/rs_node_setup.cpp (under realsense2_camera) calls `imu_callback_sync(frame)`; header default is COPY; yesterday's sample evidence agrees | KNOWN BLOCKER | Blocks claiming that method 2 demonstrably interpolates on this inspected path. Raw acquisition can proceed. Test combined behavior separately; do not silently patch upstream or assume an ARM build fixes it. |
| C Compose assumes UID/GID 1001, no supplementary device groups; yesterday GID 44 fixed video access but not IIO controls | REQUIRES BUILD TEST ON PI | Host/container access issue, not ISA-specific. Native non-root video, HID/IIO permissions must be proven with the selected SDK backend. Never copy a numeric VM group or `/dev/videoN` assignment as a Pi fact. |
| [scripts/env.sh](../scripts/env.sh) derives root from its path and sets domain 42 / FastDDS UDPv4 | PASS FROM STATIC INSPECTION | No hard-coded user-home or CPU architecture in this helper. It does not select an RMW; explicitly align publisher and observer RMW for measurements. |
| W/entrypoint.sh expects `/opt/ros/jazzy` and optional `/ros2_ws/install`; Compose uses `/ros2_ws`, `/config`, `/dev`, X11 and DISPLAY; legacy build_ros.sh targets ROS1 | REQUIRES BUILD TEST ON PI | Container paths are not native install instructions. Do not source old VM overlays or use legacy ROS1 builders for Jazzy. Native ROS2 launch and display behavior need separate validation. |
| Existing [measurement helper](../experiments/2026-09-08-d435i-baseline/measure_resume.py) uses Python/rclpy and hard-coded `/camera/...` topic names | LIKELY COMPATIBLE | No CPU-specific code found. Match remaps, Python/ROS dependencies and QoS; compute whole-window and boundary metrics as described below. |

Read-only local image inventory, 2026-09-09; short IDs uniquely identified these inspected images:

| Local image tag | ID prefix | Architecture |
|---|---|---|
| `orb_slam3:latest` | `5ccdbcfbc024` | linux/amd64 |
| `orb_slam3_ros2-base:latest` | `10481515179c` | linux/amd64 |
| `cam2image:latest` | `ba57d5885fea` | linux/amd64 |
| `charuco_calibration:latest` | `cd19023c27c7` | linux/amd64 |
| `realsense:latest` | `f05425cd25e9` | linux/amd64 |
| `rviz:latest` | `28e875cb7ea1` | linux/amd64 |
| `checkerboard_calibration:latest` | `f23d882c1412` | linux/amd64 |

# 5. Native-first RealSense plan

First architecture: **D435i → native Pi Linux → native librealsense/realsense-ros → local ROS topics**. No Docker, RViz, SLAM, depth, color, point cloud, or bag writer in the first sensor experiment.

This makes each boundary observable: USB identity/speed/disconnects in Linux; the actual Pi kernel and selected SDK backend; native udev/group permissions under the login user; SDK device/profile/errors; and local ROS discovery/QoS/timestamps. Docker would add device mounts, cgroups, UID/GID translation, container package provenance and namespace settings. It would still share the same Pi kernel and cannot repair USB negotiation by itself.

Proposed first installation path is the native ROS-distributed SDK/wrapper package pair **if Noble ARM64 candidates resolve together**. Record exact candidates before installation and the installed versions afterward. It does not execute the pinned R checkout. Management must choose whether to retain binary pinning or move to source pinning for reproducibility.

```text
[PI] apt-cache policy ros-jazzy-librealsense2 ros-jazzy-realsense2-camera ros-jazzy-realsense2-description
[PI] apt-cache show ros-jazzy-librealsense2 ros-jazzy-realsense2-camera
[PI] sudo apt install ros-jazzy-librealsense2 ros-jazzy-realsense2-camera ros-jazzy-realsense2-description
[PI] dpkg-query -W 'ros-jazzy-*realsense*'
[PI] ros2 pkg prefix realsense2_camera
[PI] ros2 pkg prefix librealsense2
```

The install line is conditional on real `arm64` candidates and reviewed dependency resolution. If unavailable or unsuitable for the actual Pi kernel, stop that installation path and plan a pinned **native** SDK build plus a dedicated ROS workspace containing only the wrapper and its required message/description packages. Do not run a root-level colcon build across both ORB checkouts. Keep system packages and source SDK prefixes distinct; do not leave competing SDK libraries or duplicate udev rules on the search path.

Backend decision must be explicit: first assess the stock kernel/native V4L2 and motion path for the selected SDK. If it cannot support the device reliably, evaluate the SDK's RSUSB userspace backend as a separate controlled build. Do not blindly run x86 HWE patch scripts or install generic RealSense DKMS packages on the Pi's `raspi` kernel. The [SDK distribution guide](https://github.com/realsenseai/librealsense/blob/master/doc/distribution_linux.md) advertises ARM packages but lists specific DKMS kernel support; this is not Pi 5 kernel validation. The [native installation guide](https://github.com/realsenseai/librealsense/blob/master/doc/installation.md) describes headless builds and backend/kernel considerations. Its old [Raspbian guide](https://github.com/realsenseai/librealsense/blob/master/doc/installation_raspbian.md) targets Pi 3 and includes armhf-era dependencies; do not transplant that recipe to Noble ARM64.

Inspect/install the matching SDK's documented udev rules on the Pi, inspect effective groups and actual video/HID/IIO controls, reconnect after rules are applied, and log in again after group changes. Successful non-root streaming is the proof. A root workaround or video-only permission probe is insufficient. Record firmware; no firmware write or advanced JSON preset load is part of this experiment.

After native stability passes, a later native-versus-Docker A/B must hold hardware, runtime versions, profiles, middleware, measurement windows and observer constant. Reintroduce only the camera service with an ARM64 image and explicit non-root permissions.

# 6. First physical Pi experiment

**Purpose:** establish native USB3 IR1 + raw gyro + raw accel continuity. No ORB-SLAM3 and no rosbag recording. Perform the test on the Pi; SSH carries control and logs only.

1. [PHYSICAL] Put the camera stationary on a desk facing a textured, normally lit scene. Connect it directly with the USB3 data cable to a Pi USB3 port. Do not use a hub for this first topology. Record cable/port, PSU, cooling, serial, firmware and camera orientation.
2. [PI] Verify identity `8086:0b3a` and the **camera's own branch** at `5000M` in the USB tree. A 5000M root with the camera at 480M fails this target. Capture before/after topology and kernel logs. Check for competing camera processes; keep all viewers and auto-start services stopped.

```text
[PI] lsusb -d 8086:0b3a
[PI] lsusb -t
[PI] id
[PI] ls -l /dev/video* /dev/hidraw*
[PI] ls -l /sys/bus/iio/devices/
[PI] pgrep -af 'realsense|rs-enumerate|orb_slam|ORB_SLAM'
[PI] fuser -v /dev/video* /dev/hidraw*
```

Device paths/backends vary; absent IIO nodes alone are not a diagnosis. Resolve permissions using the installed backend. Exit code 1 from a process search can simply mean no matches.

3. [PI] In each measurement terminal, enter the repository and source the same ROS environment. In the first terminal create an evidence directory; reuse its printed absolute path as `PI_RUN` in the other terminals. Give every later case its own directory.

```text
[PI] cd ~/wbr-perception-phase1-runtime
[PI] source /opt/ros/jazzy/setup.bash
[PI] source scripts/env.sh
[PI] export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
[PI] export PI_RUN="$HOME/wbr-evidence/$(date -u +%Y%m%dT%H%M%SZ)-pi5-native-raw"
[PI] mkdir -p "$PI_RUN"
[PI] echo "$PI_RUN"
[PI] lsusb -t > "$PI_RUN/usb-before.txt"
[PI] sudo journalctl -k -b -o short-iso > "$PI_RUN/kernel-before.txt"
```

4. [PI] Start one foreground native node, **only on arrival**, with explicit settings and stable names matching the existing observer. First inspect installed parameter documentation; if a parameter is unsupported, resolve that version difference before streaming rather than accepting defaults. Proposed profiles match yesterday: IR1 640×480 Y8 at 15 FPS, gyro 200 Hz, accel 100 Hz. `unite_imu_method=0` leaves them raw. No advanced JSON is loaded.

```text
[PI] set -o pipefail
[PI] ros2 run realsense2_camera realsense2_camera_node --ros-args \
  -r __node:=camera -r __ns:=/ \
  -r /camera/infra1/image_rect_raw:=/camera/image_raw \
  -r /camera/infra1/camera_info:=/camera/camera_info \
  -p enable_color:=false -p enable_depth:=false -p enable_infra:=false \
  -p enable_infra1:=true -p enable_infra2:=false \
  -p depth_module.infra_profile:=640,480,15 -p depth_module.infra1_format:=Y8 \
  -p enable_gyro:=true -p enable_accel:=true -p gyro_fps:=200 -p accel_fps:=100 \
  -p unite_imu_method:=0 -p enable_sync:=false \
  -p pointcloud.enable:=false -p align_depth.enable:=false \
  2>&1 | tee "$PI_RUN/camera.log"
```

5. [PI] In another identically configured terminal, wait 10 seconds after all three **requested profiles are reported opened**, then inspect actual topics and readbacks. A fallback profile is a failed configuration for this experiment. Confirm IR2/color/depth have no image publisher and combined IMU is not publishing for the raw case.

```text
[PI] timeout 10 ros2 topic list -t
[PI] timeout 10 ros2 param dump /camera > "$PI_RUN/parameters.yaml"
[PI] timeout 10 ros2 topic info /camera/image_raw --verbose
[PI] timeout 10 ros2 topic echo /camera/camera_info --once --qos-reliability best_effort > "$PI_RUN/camera-info.yaml"
[PI] timeout 10 ros2 topic echo /camera/image_raw --once --qos-reliability best_effort > "$PI_RUN/ir1-sample-1.yaml"
[PI] python3 experiments/2026-09-08-d435i-baseline/measure_resume.py 30 > "$PI_RUN/window-1.json"
[PI] python3 experiments/2026-09-08-d435i-baseline/measure_resume.py 30 > "$PI_RUN/window-2.json"
[PI] python3 experiments/2026-09-08-d435i-baseline/measure_resume.py 30 > "$PI_RUN/window-3.json"
[PI] timeout 10 ros2 topic echo /camera/image_raw --once --qos-reliability best_effort > "$PI_RUN/ir1-sample-2.yaml"
```

The observer subscribes to all named streams simultaneously with sensor-data QoS; IR2 and combined count zero is expected in this raw case. It starts a fresh ROS node each invocation. Discovery delay counts against its boundary criterion: if observer discovery causes an ambiguous failure, use a warmed persistent observer in a new, documented test, without declaring this result a pass. Do not replace this measurement with a burst-only CLI frequency number.

**Exact metric definitions using existing JSON:** let `T=duration_seconds`, `N=count`, `r=arrival_hz`. Whole-window rate is `N/T`. For `N≥2`, received span is `(N−1)/r`. The **total unobserved boundary time** is `B=max(0,T−span)`; start and end silence are nonnegative and sum to B, so **B bounds either edge gap conservatively**. Use `max(B,max_arrival_gap)` as a conservative worst arrival gap, and report `max_stamp_gap` separately. Zero/one message, missing metrics or invalid rates fail. This needs no new implementation script; record the arithmetic and inputs with the results. The old helper does not directly save separate first/last arrival offsets, so do not report B as a measured individual edge gap.

Count corrupted/incomplete notifications inside each JSON wall-clock window and across the complete startup-to-stop log. A paired `Incomplete video frame detected` / `Frame Corrupted` message is one notification, not two lost frames. Preserve raw logs. The two image-echo commands save full pixel arrays for offline rendering/inspection before authorizing bags; verify 640×480 mono8, correct buffer length and a plausible scene without garbled pixels. After the stationary measurement windows, move a visible object through the scene and capture another separately named sample with the same command to check that image content responds. Do not infer frozen delivery merely because a stationary scene looks unchanged. The existing observer checks metadata/timing, not pixels; passing it alone is insufficient.

6. [PI] Keep a further **five-minute sensor-only soak**, observed using the same helper with duration `300`, after the three short windows pass. Apply the same rates/gaps and log checks. This is a readiness sample, not a guarantee of all-day stability.

```text
[PI] python3 experiments/2026-09-08-d435i-baseline/measure_resume.py 300 > "$PI_RUN/soak.json"
```

7. [PI] Stop the camera with Ctrl-C in its foreground terminal, wait for node exit and release of device ownership, then capture USB/kernel state. A forced kill, crash, permission error, USB reset/disconnect or unexplained stall fails the run. Do not immediately start another publisher on an uncertain device state.

```text
[PI] pgrep -af 'realsense2_camera|ORB_SLAM|orb_slam'
[PI] fuser -v /dev/video* /dev/hidraw*
[PI] lsusb -t > "$PI_RUN/usb-after.txt"
[PI] sudo journalctl -k -b -o short-iso > "$PI_RUN/kernel-after.txt"
```

**Combined IMU is a separate experiment.** Only after raw acquisition passes, relaunch the same single node/settings in a new evidence directory, replacing method 0 with **1**; repeat three 30-second windows. Stop fully, then repeat separately with **2**. Verify actual parameter readback and retain raw gyro/accel alongside combined samples. Check rate, timestamp monotonicity, gyro stamp/vector correspondence, and acceleration against both latest-sample COPY and bracketed linear interpolation. Use a subsequent labeled gentle-motion window, after stationary continuity checks, if stationary quantization makes the algorithms indistinguishable. Do not use indistinguishable samples as evidence of interpolation. Preserve the raw baseline unchanged. Method 2 is not an interpolation PASS unless distinguishable sample-level evidence demonstrates it; the current source finding predicts a problem on its ordinary callback path.

# 7. Comparison against UTM baseline

Reference date: **2026-09-08**, not a synthetic estimate. Primary comparison is resumed **root B, IR1 + raw/combined IMU**, 19:14:48–19:15:18 UTC+07, duration 30.001 s. It shares image/motion profiles with the intended Pi test but had method 2, Docker/root, and the advanced JSON preset. The Pi raw-native experiment deliberately changes several layers; this is an operational comparison, not a controlled causal A/B.

| Metric | UTM | Pi 5 native |
|---|---|---|
| USB speed | Camera at USB 2.1 / **480M**; 5000M root existed without camera beneath it | NOT TESTED |
| IR1 frames / 30s | B: **15**; controlled two-IR A: 23 | NOT TESTED |
| whole-window FPS | B: **0.500**; A: 0.767 (`N/T`) | NOT TESTED |
| max frame gap | B: internal header gap **0.066403 s**, arrival gap 0.071040 s; boundary silence total **≈29.065 s**, individual edges not saved. A: internal header gap 6.514566 s | NOT TESTED |
| corruption notifications | B: **15** paired incomplete/corrupted notifications in window; A: 18 | NOT TESTED |
| gyro rate | B: **167.173 Hz** first/last arrival rate; **167.195 Hz** whole-window, 5016 messages; requested 200 | NOT TESTED |
| accel rate | B: **100.778 Hz** first/last arrival rate; **100.797 Hz** whole-window, 3024 messages; requested 100 | NOT TESTED |
| combined IMU rate | B: **155.436 Hz** first/last arrival rate; **155.262 Hz** whole-window, 4658 messages; method 2 readback, COPY-like evidence | NOT TESTED |
| USB disconnect | **Yes in the resumed session at 19:15:51**, during subsequent non-root C, not inside B's 30-second window; absent at final check | NOT TESTED |
| IMU calibration warning | **Present**, default motion calibration fallback; cause of retrieval failure unresolved | NOT TESTED |

Sources: [RESUME_SUMMARY.json](../experiments/2026-09-08-d435i-baseline/RESUME_SUMMARY.json), [B measurement](../experiments/2026-09-08-d435i-baseline/B_RATES.json), [B log](../experiments/2026-09-08-d435i-baseline/B_LOG.txt), [USB history](../experiments/2026-09-08-d435i-baseline/USB.txt), [IMU notes](../experiments/2026-09-08-d435i-baseline/IMU_NOTES.md), and [audit sections 7 and 16](../D435I_BASELINE_AUDIT.md).

B's 14.959-Hz first/last rate described about **0.936 seconds of images**, not continuous 30-second acquisition. From duration minus received span, its boundary silence sums to about 29.065 seconds; at least one edge is therefore at least 14.532 seconds. Initial pre-resumption two-IR data separately had 45 IR1 images and a 26.065096-second internal header gap; do not mix that earlier gap into B's row. No UTM raw-only method-0 experiment was recorded. No pixels were assessed, no bags recorded and no SLAM run in that audit.

# 8. Sensor gate

These are **proposed engineering acceptance thresholds**, not manufacturer specifications or measured Pi capability. Do not relax them retrospectively to label a failing experiment as a pass. Every required condition must pass; missing evidence is **NOT TESTED / NO-GO**.

| Requirement | PASS | FAIL / NO-GO |
|---|---|---|
| USB identity and link | `8086:0b3a`; camera branch negotiates 5000M before, during and after run | Absent, 480M, or only root hub at 5000M |
| Ownership and profiles | One native, non-root publisher; opened IR1 640×480 Y8/15, gyro 200, accel 100; other images disabled | Root-only access, IIO/HID denial, competing process, profile fallback |
| IR1 delivery | Each 30-second window: 14.25–15.75 whole-window FPS (about 428–472 images for exactly 30 s); same rate band for soak | Too few/many messages or burst-only delivery |
| No long image gaps | Internal arrival and header gaps ≤0.20 s; conservative boundary B ≤0.20 s in every window and soak | Any limit exceeded; missing/nonfinite metric |
| Raw gyro | 190–210 whole-window Hz; internal arrival/header gaps and B ≤0.05 s | Rate or continuity failure |
| Raw accel | 95–105 whole-window Hz; internal arrival/header gaps and B ≤0.05 s | Rate or continuity failure |
| IMU contents/time | Finite vectors, strictly increasing per-topic stamps; stationary mean gyro-vector norm ≤0.10 rad/s, mean accel norm 9.0–10.5 m/s²; inspect axes/frames | NaNs, backward/duplicate stamps, implausible stationary values, unexplained clock discontinuity |
| IR1 image and camera_info | Plausible sampled image pixels; camera_info received with matching resolution/optical frame and finite nonzero focal lengths; matching image/info timestamps observed | Missing/mismatched info, invalid intrinsics, malformed/garbled/frozen samples |
| Corruption | Zero incomplete/corrupted-frame notifications throughout evaluated run, including startup/soak | Any such notification; repeated notifications emphatically fail |
| USB/process/power continuity | No camera disconnect/reset, driver crash, repeated reconnect, undervoltage or thermal-throttling event; orderly shutdown | Any occurrence or unexplained process loss |
| Calibration provenance | Record warning presence, intrinsics, IMU info and static transforms | Warning is concealed or calibration provenance claimed without evidence |

Raw sensor-gate PASS permits **only a short diagnostic probe bag of the validated raw stream set**. An IMU calibration fallback warning may coexist with stable raw transport, but must label that probe **default IMU calibration / not VIO-qualified**. It blocks final VIO datasets and live VIO until its cause and calibration adequacy are resolved; available camera_info/TF do not prove calibrated IMU extrinsics.

Combined gate is additional: preserve raw gate results, require combined rate 190–210 whole-window Hz, arrival/header gaps and B ≤0.05 s, monotonic finite data, consistent frames/timestamps, and measured algorithm behavior matching the chosen method. If method 2 behaves like COPY, interpolation fails even if rate passes. A raw diagnostic probe may proceed after the raw gate; adding `/camera/imu` or declaring a combined-IMU dataset ready requires the combined gate as well.

# 9. Rosbag gate

**Only after the relevant sensor gate passes:** restart the same validated native profile, verify it is stable, then record a **30-second probe** on the selected local storage. Record IR1, camera_info, raw gyro and accel, their IMU info, relevant extrinsics and `/tf_static`; include `/camera/imu` only if its separate gate passed. Inspect the actual graph for exact auxiliary topic names. Document unavailable optional diagnostics; required calibration/context topics cannot silently disappear.

Preflight the installed Jazzy bag CLI help, storage plugin availability and topic QoS. Use a fresh output directory. The explicit SQLite3 example avoids making a long-term storage-format decision. Verify transient-local `/tf_static` capture and use a reviewed QoS override if automatic matching does not capture it. Do not use broad all-topic recording to hide a missing topic list.

```text
[PI] ros2 bag record --help
[PI] ros2 bag play --help
[PI] df -h "$HOME/wbr-evidence"
[PI] ros2 bag record -s sqlite3 -o "$PI_RUN/probe_raw" /camera/image_raw /camera/camera_info /camera/gyro/sample /camera/accel/sample /camera/gyro/imu_info /camera/accel/imu_info /tf_static
```

[PI] Stop the recorder with Ctrl-C after 30 seconds and wait for successful metadata finalization. The command is a minimum raw set: append the discovered extrinsics topics before executing. Observe sensor rates/logs during recording to detect storage-induced degradation. Do not publish a bag still being written.

```text
[PI] ros2 bag info "$PI_RUN/probe_raw"
```

[PI] **Stop the live camera**, wait for device release, and confirm no live sensor publisher. Replay in an isolated ROS domain, with the observer in that same domain, to prevent accidental mixing with live topics. Start the observer before playback. If using ROS simulation time, set consumer `use_sim_time=true` consistently and request the player's clock; the existing helper's arrival measurements use monotonic wall time and do not need simulation time.

```text
[PI] export ROS_DOMAIN_ID=43
[PI] ros2 bag play "$PI_RUN/probe_raw" --clock
```

Probe PASS requires readable metadata/storage, expected message types and counts compatible with the actual recording duration and sensor gate rates, replay of **every recorded required topic**, preserved header timestamps/ordering and camera_info/TF, no unexplained reader errors, and no live-camera collision. Compare stored topic counts from bag info against a warmed observer covering the entire single playback; partial observation cannot establish equality. At 1× replay, examine arrival pacing separately from recorded header timing. Discrepancies require investigation and a new probe, not a silent count tolerance. The fixed-window helper may support timing inspection but does not automatically prove full-playback count equality.

After replay passes, retain a manifest/checksum and copy the completed probe to backup. Only then plan **S00 → S01 → S02 → S03**. The inspected repository does not define a complete authoritative S00–S03 protocol (the audit mentions S00–S02 as deferred). Keep these identifiers reserved; agree objectives, motion, duration, lighting, calibration status and expected failure modes before collecting. Do not invent historical meanings or call today's diagnostic probe S00. Final VIO sessions also require calibration and combined-IMU readiness where used.

# 10. ORB-SLAM3 deployment sequence

Execute one stage at a time, with saved evidence and a stop condition at each transition:

| Stage | Planned work and exit condition |
|---|---|
| Official EuRoC baseline | Use the independent official ORB_SLAM3 checkout, known EuRoC data/configuration, recorded revisions and evaluation convention. Prefer Lab for the native x86 reference. Demonstrate trajectory output and tracking/evaluation results; no baseline success is claimed here. Offline Lab/Mac preparation can occur independently of Pi sensor readiness. |
| Pi ORB-SLAM3 build validation | After Pi sensor gate, provision exact dependencies and build dependency stages with bounded parallelism. Validate AArch64 library identity/linkage, headless/viewer behavior, memory and thermal margin; run the same saved EuRoC case. Compilation alone does not prove live throughput. |
| Saved D435i bag readiness | Use only a bag that passed record/replay, with resolved calibration for VIO use. Inspect timestamps, image format, intrinsics, frames and raw/combined IMU semantics independently before connecting a SLAM consumer. |
| ORB_SLAM3_ROS2 | Build its separate embedded ORB revision and CMake export first, then the wrapper in an isolated workspace. Map the validated bag topics and calibration to the wrapper; replay and establish tracking/trajectory behavior. Do not treat the official core and modified embedded core as interchangeable. |
| Live D435i VIO | Replace validated replay with the validated live source while holding wrapper/calibration/settings constant. Check initialization, drift, loss/recovery and output timing. |
| Performance profiling | Measure acquisition loss, processing latency, queue growth, frame processing rate, CPU/RAM, thermals and storage under representative sustained load. Decide resolution/rate/compute placement from evidence. No promise of real-time Pi SLAM is made. |
| WBR integration | Only after sensing, replay, VIO and performance gates: define frame/time/output contract and failure handling with WBR. Preserve STM32 safety/control ownership; stage deployment before robot motion. |

This sequence means no single launch combining a new ARM build, new camera backend, first bag and first live VIO. EuRoC dataset preparation and the existing Lab reference role are useful now; execution of builds/benchmarks is outside this documentation-only task.

# 11. What must remain deferred

Before the physical Pi raw sensor gate passes, deliberately defer:

- Any rosbag recording, including a short probe; S00/S01/S02/S03 collection and claims of replay readiness.
- Pi ORB-SLAM3 builds/runs, wrapper deployment, live VIO, SLAM tuning and end-to-end performance claims. Offline planning and independent Lab EuRoC work do not require Pi USB readiness.
- Docker installation for this baseline, ARM64 image builds/deployment, Compose redesign implementation, native-versus-container A/B, NVIDIA workarounds and GUI/X11 setup.
- Stereo IR2, color, depth, point clouds, extra streams, higher FPS/resolution and advanced JSON presets in the baseline; introduce later one variable at a time.
- Firmware updates, calibration replacement, broad device permission changes, speculative kernel patching, SDK/IMU source fixes, overclocking or forced USB power limits. Necessary narrowly scoped native SDK/udev setup belongs to bring-up; corrective changes after an observed failure require a separately logged experiment.
- Combined IMU tuning until raw stability; interpolation claims until sample evidence; final VIO datasets until calibration is adequate.
- WBR runtime integration, service auto-start, unattended acquisition, robot motion and deployment decisions based on assumed Pi performance.
- Package installation on the Ubuntu VM to simulate the Pi; QEMU/emulated ARM results presented as native hardware validation.

No commit or push is part of this task. Hardware availability does not retroactively turn this plan into a validated deployment.

# 12. Pi arrival checklist

- [ ] [PHYSICAL] Fit cooling, identify boot medium, use suitable power and a direct USB3 data cable; record Pi RAM/model and camera details.
- [ ] [MAC] Flash/verify Ubuntu 24.04 ARM64 for Pi, set hostname/user/network/public key; retain this uncommitted plan separately.
- [ ] [PI] Boot with camera unplugged; confirm OS/ARM64, finish setup, install base packages, enable SSH and synchronize time (section 3).
- [ ] [MAC] Verify Pi host fingerprint, test key login and connect VS Code Remote SSH.
- [ ] [PI] Clone with recursive submodules; record revisions; provision Jazzy and resolve one native SDK/wrapper pair plus correct udev permissions.
- [ ] [PI] Check disk/RAM, exact runtime versions and time sync; establish a new evidence directory and identical observer environment.
- [ ] [PHYSICAL] Attach D435i directly to Pi USB3; keep camera stationary and other USB workloads absent.
- [ ] [PI] Verify `8086:0b3a` and camera branch at 5000M, non-root permissions and no competing publisher.
- [ ] [PI] Execute section 6 raw-only test: explicit profiles, three 30-second windows, pixel/info checks, five-minute soak, complete logs and orderly stop.
- [ ] [PI] Evaluate every section 8 raw criterion; failure or missing evidence means stop and diagnose. All Pi table entries stay `NOT TESTED` until measured.
- [ ] [PI] After raw PASS, test combined methods separately; after the relevant sensor PASS, record/info/stop-camera/replay the short probe. End the day here if later gates are not ready.

# 13. Questions requiring management decisions

These are unresolved decisions, not access requests. The Pi primary target, Ubuntu 24.04 ARM64, Jazzy, direct USB3 first test and Lab reference role are already decided.

| Decision | Options / information needed |
|---|---|
| Native RealSense versus Docker after baseline | Retain native acquisition, containerize it after matched A/B, or native driver plus containerized consumers. Decide from stability and maintenance evidence. |
| ORB-SLAM3 compute placement | Pi live execution is the long-term intent. Determine whether all workloads fit Pi, whether Lab offload is needed during development, and acceptable latency/power/accuracy limits. Do not silently relocate the target. |
| ARM64 Docker strategy | Pi-native builds versus a managed multiarchitecture builder/registry; per-architecture immutable tags/digests; ownership of Pi/Lab Compose variants and headless operation. Existing images are amd64. |
| Runtime source pinning | Exact apt package/dependency versions and archive retention versus SDK/wrapper source SHAs with build manifests. Choose SDK backend and account for the observed source/runtime mismatch and combined-IMU defect. |
| Storage strategy | Boot/recording SD versus SSD/NVMe, capacity, endurance, power/USB contention, bag format/compression, retention and Lab/Mac backup destination. Pi RAM size and storage hardware remain unspecified. |
| Lab as required reference | Lab remains the native x86 reference/heavy-compute machine. Decide which gates require a scheduled Lab hardware cross-check, especially if Pi reproduces USB corruption or IMU calibration warnings. This is about mandatory use/availability, not removing its assigned role. |
| Calibration and dataset qualification | Owner and method for resolving IMU fallback, verifying camera–IMU calibration, choosing combined-IMU semantics, and defining S00–S03 protocols. |
| Acceptance and operations | Ratify proposed gate thresholds before testing; decide Server versus Desktop if a local viewer becomes necessary, long-run duration, dataset ownership and eventual unattended-service policy. |

Until those choices and hardware tests are complete, this document establishes preparation and explicit gates only.
