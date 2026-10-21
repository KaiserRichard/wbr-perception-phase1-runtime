# Camera recording and one inertial attempt — 2026-10-21

- Owner relayed Claude acceptance of visual bring-up, then requested recording
  fixes, a marked loop and one excitation attempt before leaving the lab.
- Branch chatgpt/20261021-camera-recording-mcap from origin/main b3ae906.
  Existing untracked fuzz binaries/build output preserved; shared checkout untouched.
- Sequential live 640×480/15 Hz trials, each with the same visual SLAM running:
  MCAP broad topics 412/424 images, 12 missing left/112 transport losses;
  stereo-only best-effort 408/407 (one startup right image);
  reliable depth100 445/445; reliable+4MiB rmem max/default 895/895.
  Last two had identical stereo headers, no observed nominal gaps/transport losses.
- New marked loop mcap-marked-loop-01: supervisor 09:53:03–09:55:33+07,
  bag147.607s,2215left/2215right and2215CameraInfo each; equal headers, no observed
  gaps/transport losses. Owner confirms marked position/original heading by
  09:55:03 and held through stop. Physical alignment is not independently measured.
- Full new MCAP copied to Mac; SHA256 verified:
  5749908bb94a6c9a7e5496f3c8b58db3596cf5f53f2542502a1468dcd97703c8.
  Archive ~/wbr-evidence-archive/camera-recording-20261021-01; failed pilot bags
  retained on Pi; small logs/quality receipts copied. No deletion/calibration writes.
- New focused recorder and header-quality CLI; 50 camera-day tests PASS, including
  6 new recording tests; 7 native tests PASS with patches on real saved sources.
- Native interpolation bug found: computed linear interpolation was overwritten
  with the latest acceleration; image callbacks also padded unsynchronized gyros.
  Added bracketing accel-to-gyro interpolation, pending-sample retention, source
  timestamp logging, SDK body-from-camera Tbc verification and200Hz checks.
  Isolated build ~/wbr-camera-inertial-unified-20261021-01 compiled/linked exit0.
- Owner says robot is heavy. Explained pitch/roll/yaw; instructed wheels-on-floor
  planar starts/stops/turns for10–15s, without lifting or disturbing the mount.
  Single75s attempt exit0:1121processed/1116tracked,14.8741trackedFPS,
  4 observed loss transitions,965exported camera poses/72keyframe poses.
  Final initialized928frames/61.8049s, VIBA1/2completed; earlier resets retained.
  Measured gyro200.1825Hz/accel202.2514Hz; nominal200Hzunified gyro grid.
  STOP cue late; stationary tail shorter than15s. Only one attempt performed.
- Larger receive buffers intentionally retained for the session as requested;
  no persistent sysctl file. Replays/endpoint analysis not yet run on the new bag.
- Calibration final SDK output byte-identical; all camera/SLAM/recorder/ROS daemon
  processes stopped. Pi-free receipt10:15:21+07; first self-matching inspection
  retained diagnostically, final receipt excludes inspection ancestors. Throttle0x0.
- Mac archive176artifacts SHA256verified, including complete loop and IMU raw
  samples/frames/trajectory/build logs. CodePR87; documentation CI pending.
