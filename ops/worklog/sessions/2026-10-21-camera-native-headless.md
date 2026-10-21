# Camera native headless worker — 2026-10-21

- Scope: assigned codex-i worker; owner-authorized viewer=false and borrowed
  D435i317422076650 supersede historical no-camera/no-IMU instructions.
  **No camera/SDK enumeration, native live executable or Xvfb was launched by
  this worker.** Conductor owns all live sessions and merge.
- Read AGENTS.md, CURRENT.md, USER_PROFILE.md and bringup SKILL.md. Central logs,
  ROS wrapper/launch, simulation/training and student.py were left untouched.
- Pi read-only inspection: `ssh wbr-pi5`, hostname wbr-pi5, aarch64, RAM3983MiB.
  Existing ORB examples, build flags/link commands and library were available.
- Saved source/readback snapshots: `/private/tmp/wbr-camera-native-readback-20261021`.
  Input evidence: `/home/richard/wbr-evidence/camera-day-20261021-01/rs-enumerate.txt`,
  stereo.yaml and rgbd-ros.yaml. SDK text SHA256:
  `567c08f57953aef175577550314cfe37ff0b704c54a0a641c6eabdc8dd57baef`.
- Exclusively created `/home/richard/wbr-camera-native-20261021`; tool copy at
  `/home/richard/wbr-camera-native-tools-20261021`. Copied only three example
  sources, patched private copies, reused existing ORB libraries/flags.
- Build command: `python3 /home/richard/wbr-camera-native-tools-20261021/native_headless.py build`.
  All three compiled/linked sequentially on Pi, no concurrent compilers and no
  ORB library rebuild. First build succeeded at `20261021T011638.950567Z`;
  cleanup/metric corrections rebuilt at `011854.641818Z` and `012104.589718Z`.
  Every build/patch log remains under private `logs/`; no compile failure occurred.
- Final receipt: `logs/build-20261021T012104.589718Z-receipt.json` confirms original
  source/System header/library hashes unchanged and records binary/header/settings
  hashes. `file` and `readelf -d` confirm three AArch64 ELF binaries linked to
  libORB_SLAM3.so/librealsense2.so.2.58 with original library RUNPATH.
- Executables in private `bin/`: stereo_realsense_D435i,
  rgbd_realsense_D435i, stereo_inertial_realsense_D435i; all viewer=false.
- Fixes: SIGINT/SIGTERM flag checked; timed frame waits; finite duration/watchdog;
  capture stop then Shutdown/worker wait then TUM export; empty-map guard;
  exception cleanup before callback captures unwind; image clones/owned frames;
  retained SDK extrinsics lifetime and correct column-major display; first-real-
  accel gate and removal of racing initial buffer clear.
- Metrics: attempts.csv before each Track; frames.csv around returned/thrown
  Track with state/OK-only tracked flag/exact atlas IMU init/source timestamp and
  frame counters/cadence/slot overwrites; summary separates processed/tracked FPS,
  startup/loss/reset frames and loss transitions. No inferred camera-drop count.
- RGB-D: removed IMU requests and all sensor-option writes; runtime queries native
  frame depth units and converts Z16 to float metres, YAML factor1. Live units
  remain unobserved by worker. Stereo/inertial also have no sensor-option writes.
- Device IMU transform derived from IR1->Gyro/Accel readback (identity R;
  t=[-0.00552000012248755,+0.00510000018402934,+0.011739999987185]m).
  Cross-checked ORB Settings/ImuTypes/Frame semantics and unpermuted SDK XYZ;
  no further device query required. Noise explicitly ASSUMED upstream defaults.
- Prepared six YAMLs: three modes × (30FPS/1250features,15FPS/800features), with
  explicit200Hz gyro/accel for inertial. An additional stereo30FPS/800features
  YAML appeared externally in the private area; the helper did not generate it.
- Local targeted proof: `WBR_ORIGINAL_EXAMPLES=/private/tmp/wbr-camera-native-readback-20261021 python3 -m unittest discover -s scripts/camera_day/native -p 'test_*.py' -v`:
  **7 tests passed**, including real-source patch application and a tiny C++
  metric fixture; logs `/private/tmp/wbr-camera-native-readback-20261021/tests-01.log`
  and `tests-final.log` (rerun after final build-receipt helper change).
- `git diff --cached --check` reports unified-patch blank context lines (required
  leading space); output preserved in the snapshot directory as
  `diff-check-patch-context.log`. The check excluding `native/*.patch` passes;
  all three patch files applied with zero fuzz in the targeted tests.
- Read-only parallel review confirmed transform direction and identified
  post-start exception cleanup, cancellation-before-capture, failed-call receipts,
  export checks and unsafe automatic atlas output; all addressed in final build.
- Documentation changes: `scripts/camera_day/native/README.md` contains exact
  conductor commands, paths, settings derivation, metric definitions and limits.
  This worker session is the sole worklog edit; central documentation/decision
  accounting remains with conductor.
- Limits: no live tracking/FPS/IMU initialization/trajectory/shutdown claim.
  Installed-ORB private-member compatibility shim is source/hash-specific;
  retained upstream IMU hold/resampling and multi-map TUM semantics are documented.
  Upstream unused-variable/sign-compare warnings remain; no warning was fatal.
