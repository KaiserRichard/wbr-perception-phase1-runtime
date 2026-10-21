# 2026-10-21 — camera day

- Owner reauthorized build-first camera work: native stereo, RGB-D, ROS pose,
  2–3 minute bag, three replay trajectories; no qualification/review stop.
- Fetched origin and fast-forwarded lab worktree to `8195d7f` (PR74), then
  created `chatgpt/20261021-camera-day`. Existing untracked host build artifacts
  preserved. Re-read rewritten AGENTS, CURRENT, profile and bring-up skill.
- AGENTS already contains Conducting Codex; no duplicate section added.
- SSH `wbr-pi5` works: `richard@192.168.50.2`; Wi-Fi `192.168.0.107` at readback.
  Pi is aarch64 with 3.9 GiB RAM, not the historical 8 GB board. Build serially.
- Storage MEASURED: SG128 SDXC, 123849408512 bytes; root `/dev/mmcblk0p2`,
  113 GiB filesystem / 88 GiB available. Kernel records successful EXT4 growth;
  no I/O/EXT4 corruption messages in inspected boot log, zero failed units,
  `throttled=0x0`. Evidence/runtime/repo readable; no whole-image comparison.
- `rs-enumerate-devices -s`: no device detected. Native stereo launch likewise
  reports no connected device; no SLAM tracking or calibration readback yet.
- Native stereo/RGB-D executables and ORB library already exist. ROS camera
  package installed: `4.58.4-1noble.20260902.181721`. No active display manager
  or DISPLAY. Stock RGB-D example requests camera IMU; D435 adaptation pending.
- Requested owner connect camera to blue USB3 and identify D435 vs D435i.
- g idle/shared-alias and quota check passed; Astra Ultra ROS build worker launched
  in separate worktree/branch `chatgpt/20261021-camera-ros-build`. Own private Pi
  source/build only; conductor owns camera. Worker receipts in
  `/private/tmp/wbr-camera-day-20261021/ros-worker*`.
- Assumed MuJoCo/LQR milestone already completed; independent PPO v2 supervisor
  active. No duplicate simulation/training or protected exercise edits.
- Pending: native ROS build; connected-camera calibration/live runs; bag/replay/
  trajectories and final milestone review. No pose/milestone completion claim.
- Documentation change set: DOC-20261021-CAMERA-DAY.

- 07:58 +07: D435i317422076650/FW5.17.3.10 detected at5000M; calibration
  readback and separate stereo/rgbd-ros settings saved under Pi evidence
  `camera-day-20261021-01`. No camera calibration write/firmware/robot config edit.
- Native stereo attempt1 aborted on missing X display; Xvfb installed. Bounded
  attempt2 initialized733map points, with repeated dropped-frame messages;
  moving trajectory and throughput unverified. ROS build3 pending Pangolin fix.
- Owner requested short raw Markdown report before further work; delivered
  `reviews/2026-10-21-camera-day-status.md`. No further experiment started for report.

- Owner relayed Claude changes: native viewer=false,15FPS or800features trial;
  log measuredtrackingFPS/loss transitions/throttling; include native stereo-inertial
  on the now-connectedD435i; preserve mount during cart/power-bank motion; mark
  identical start/end and report3replay endpointdrift(m,%path) plus closure events.
- ROS build4 succeeded after installed RPATH fix. Conductor independently rebuilt
  alltargets(exit0), verified no missing libraries and expected missing-settings
  startup(exit1,LD_BIND_NOW=1). PR77/head567c765 merged after bothCIchecksSUCCESS.
- Idle/quota checks passed fori/g. i/AstraUltra prepares private headless native
  copies/metrics/inertial config; g/Sol prepares replay analysis. Separate
  worktrees/branches, no concurrentcamera ownership; conductor runs live tests.
- Requested owner prepare cart/powerbank and a marked loop; motion pending.

- Owner confirms manual cart/whole-mobile-robot motion; camera stays on mount.
- SDKcalibration readback after native baseline matches original fulloutput SHA256
  `567c08f57953aef175577550314cfe37ff0b704c54a0a641c6eabdc8dd57baef`.
- Live headlessROS stereo01: initialized614points; statusstate2/pose_publishedtrue.
  First CLIecho failed before type discovery; explicitgeometry_msgs/PoseStamped
  echo returned actualslam_world pose. Throttling before/after0x0. Driver/node
  bounded55s and stopped; no concurrentnativecamera process. Initial livepose
  success is not a movingloop, bodypose or performance result.
- Main merged into camera branch preserving concurrent overnight documentation;
  CURRENT hardware updated without rewriting old results. Native3mode and replay
  helpers pending; no further milestone approval claimed.

- Headless native viewer=false runs (30s each): stereo30Hz/1250features
  27.96state-OKFPS,0loss transitions,45callbackoverwrites; clean stereo30Hz/800
  repeat29.76FPS/0loss/0overwrites; stereo15Hz/80014.90FPS/0loss/0overwrites;
  RGBD15Hz/80014.65FPS/0loss/0overwrites. Allthrottlingbefore/after0x0;
  native trajectories finite. Initial800trial overlappedrebuild, retained separately.
- Inertial trials90s/60s: both transiently setIMU-initialized(25/17frames), then
  bad-IMU/motion resets; finalTUMempty. Motion retry userreported and timedwith
  cartmountpreserved. SourceTracking.cc2347checks averageacceldifference<0.5;
  LocalMapping reportsinsufficientmotion. No sustainedinertialsuccess claim.
- ROSRGBD15Hz/800 actualPoseStamped+state2; CLIposeHz14.79(shortwindow), not
  internaltrackinglatency. Saved193poses/193statuses; realexportexit0 exactmatches.
- Sensorbag smoke14.24s/159.8MiB: left171,right183,depth94; recorderreports103
  transportlostmessages. Preservefailure. Nextloopchangesonlyimagehistory10->100
  in sessioncopiedQoS; no threshold/calibration/systemkernel changes.
- One functionalvisualreplay0.5x: freshORBmap,170poses/170statuses exported and
  matched originalinput. Inputbagalreadyhaslosses; not the requestedmarkedloop
  or3repeatabilityruns. Sourcebagand3smallrawbagsstayPi; metadata/TUM/logs archived
  to~/wbr-evidence-archive/camera-day-20261021-01-initial,189/189SHA256verified.
- Calibrationreadback afterheadless/ROS/inertial matches originalfullSDKhash.
- PR79/e9e6828 metrics:independent18testsPASS;PR80/98f5819 native:independent7tests
  PASS+liveexecution;PR81/0885bba exporter:independent14testsPASS+real193poseexport.
  AllmergedonlyafterbothCIchecksSUCCESS. PR80mainb046191,PR81main28f1eb7.
- Capture-supervisorsource storedPiunder camera-day-20261021-01/capture_loop.py;
  privateprocessgroups,150sbound,profile15Hz/800,source/configsnapshots andnewpaths.
  Syntaxchecked only; actualmarkedcaptureawaitsownerready. Cartloopinstruction:
  markposition+heading,returnby120s,standstilllast30s. No exact3replayclaimyet.
