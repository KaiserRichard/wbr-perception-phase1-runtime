# Pi ORB stereo / pose — 2026-10-20

- Assigned worktree: `/Users/quockaiser/.codex/worktrees/pi-orbslam-pose/wbr-lab-ops`;
  branch `chatgpt/20261020-pi-orbslam-pose`, clean starting HEAD `5b6ab4e`.
  Read root/ancestor AGENTS, CURRENT, owner profile, research rules and bring-up
  skill. No nested AGENTS found in this checkout.
- Owner facts supersede CURRENT: no camera this afternoon; Pi has 4 GB RAM and
  slow 32 GB microSD. No motors/STM32, shared checkout, storage or sim changes.
- One connectivity attempt:
  `ssh -o BatchMode=yes -o ConnectTimeout=8 -o ConnectionAttempts=1 wbr-pi5
  'printf "HOST="; hostname; uname -m; head -5 /proc/meminfo; df -h /;
  test ! -r /etc/os-release || cat /etc/os-release'`.
  Exit 255: `ssh: connect to host 192.168.50.2 port 22: Operation timed out`.
  No further SSH attempts; Pi identity, RAM, current installs/data unverified.
- Ran `make -C ros2/wbr_orb_node test`: exit 0, all 19 tests passed, none skipped.
  The C++17 ROS-free core compiled on macOS x86_64; fake-engine tests only.
  Log: `/private/tmp/wbr-conducting-20261020/pi-host-test-initial.log`.
  Neither `colcon` nor `ros2` is on this Mac's PATH. No ROS/ORB build or pose run.
- Inspected local package.xml, CMakeLists, config/defaults, README, node and engine
  interfaces: local real engine uses IMU_STEREO; odometry requires measured
  camera-IMU geometry. No launch file exists in this package.
- Read pinned upstream wrapper files through GitHub:
  `efd7acd9ea31bfdbcd843a4c90eeaa85f7e80dd8`; package `orb_slam3_ros2`,
  executable `imu_mono_node_cpp`, output `orb_odom`. Only mono/IMU-mono;
  no stereo subscription. Its timer stamps a cached transform with `now()` and
  has no tracking-state guard. It expects nested gjcliff ORB fork
  `0f29ad5f563269a13109d81eb886916cc5960136`, not the stock ORB build.
  Source copies: `/private/tmp/wbr-conducting-20261020/pi-upstream/`.
  No submodule checkout or upstream source modification.
- Existing Mac EuRoC MH01: `/Users/quockaiser/datasets/euroc/MH01`; cam0 and cam1
  each list 3,682 frames and their first PNG exists. Both CSV SHA-256:
  `62db628a8e6358f43df81e66ddb4597ab40b19a10f3d6cd80cc04d590b5adb12`.
  First/last epochs: `1403636579763555584` / `1403636763813555456`.
  Metadata receipt: `/private/tmp/wbr-conducting-20261020/pi-existing-dataset.json`.
  No data download, copy into git, full pixel validation or dataset SLAM run.
- Documentation edit record:
  - `ops/lab-assistant/skills/wbr-orbslam3-bringup/SKILL.md`: corrected 8 GB/-j3
    assumption to 4 GB/-j1; no-camera branch, bounded SSH, actual wrapper gap.
  - New adjacent `offline-stereo.md`: existing MH01 identity, exact stock stereo
    build/run/provenance commands, viewer behavior, real ROS package build
    preparation and explicit remaining stereo/source-stamp implementation gap.
  - `ros2/wbr_orb_node/README.md`: documented missing stereo-only support,
    corrected ORB path, dedicated checkout example and serial colcon builds.
  - This session log records all documentation edits; shared CURRENT, DECISIONS,
    DOCUMENTATION_LOG, AGENTS and canonical gate documents remain untouched.
- Documentation validation: `git diff --check` passed; Python extracted all
  12 bash/sh command blocks from the three edited guides and ran `bash -n`;
  all parsed. All relative Markdown links resolved. No Pi commands were executed.
- External conductor handoff document:
  `/private/tmp/wbr-conducting-20261020/pi-report.md`, populated after PR creation
  with the exact commit, PR URL, commands/results and outstanding blockers.
  Connectivity receipt: adjacent `pi-connectivity.txt` (transcribed tool output,
  not a second SSH run). No milestone completion is claimed.
- No threshold changes, synthetic success, intermediate review or milestone
  review file. Implementation changes to the preferred upstream wrapper require
  conductor assignment outside this track's allowed files.
- **Recommendation:** owner restores Pi/Ethernet/reachable address; run existing
  native stereo MH01, then implement stereo/source-stamped tracking in the
  existing upstream wrapper. Camera return is required for live evidence.
