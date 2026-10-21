# Camera recording fix and single excitation attempt

2026-10-21 +07. Previous visual bring-up accepted by Claude (owner relayed;
review appended to the earlier milestone file). This report covers the narrower
morning scope before the owner leaves the lab.

## Recording result

Pi5/aarch64/3.9GiB, borrowed D435i317422076650 on its original mount; 640×480,
15Hz images, visual SLAM800features, viewer off. All trials used a fresh path.

| Sequential trial | Left / right images | Missing versus recorded CameraInfo | Transport losses |
|---|---:|---|---:|
| MCAP, broad original topics | 412 / 424 | left12/424=2.83%;right0 | 112 |
| MCAP, stereo-only, best-effort | 408 / 407 | left0;right1/408=0.245% at startup | 0 observed |
| Stereo-only, reliable image history100 | 445 / 445 | 0 observed | 0 observed |
| Same plus4MiB rmem max/default | 895 / 895 | 0 observed | 0 observed |
| Fresh marked loop, final settings | 2215 / 2215 | 0 observed | 0 observed |

The final three rows have equal image headers and no nominal-rate internal
gaps. Header/CameraInfo and nominal-rate checks meet the requested observed
<1% target; hardware prefix/tail and independently measured production counts
remain unknown. No causal claim that MCAP alone or receive buffers alone fixed
all losses. Original failed runs remain on the Pi.

Marked loop: supervisor09:53:03–09:55:33+07, finalized bag147.607s,
1,363,690,189bytes. Owner confirms exact marked position/original heading by
09:55:03 and held until09:55:33. Physical alignment is user-reported, not ground
truth. Only IR1/IR2 images and CameraInfo were recorded; old poses/depth/TF were
excluded. Publishers offered reliable QoS; image reader history100. Session
rmem_max/default4194304 retained as requested; no persistent kernel config.

## Inertial attempt

Prepared a new private native build, leaving the ORB library and original source
unchanged. Found and corrected the example's overwritten interpolation result
and latest-accel padding of unsynchronized gyros. Unified native samples now
use two bracketing accel samples at gyro timestamps; pending samples survive
image processing. Raw SDK samples are logged for actual-rate checks. This is
native unification, not a ROS unite_imu_method setting.

Runtime checks compare configured IMU.T_b_c1 against SDK IR1→Gyro extrinsics
(body-from-camera, metres), IMU.Frequency200 and active200Hz gyro/accel profiles.
Noise assumptions and ORB initialization thresholds unchanged. Explained
pitch/roll/yaw; heavy robot stays on its wheels for planar starts/stops/turns.
One75s native attempt completed, exit0 and graceful trajectory export. SDK
Tbc/profile/frequency checks passed. Raw gyro14960samples:200.1825Hz; accel15132:
202.2514Hz on their source clocks, no nonpositive timestamp intervals. Unified
IMU follows the gyro time grid; the setting is nominal200Hz, not an assertion
that both measured clocks are exactly200. Units are SDK rad/s and m/s².

Processed1121frames, tracked1116 (14.8741trackedFPS),4 observed loss transitions;
initialization/reset episodes remain in the log. The final initialized segment
spans928frames/61.8049s through the end. VIBA1 and VIBA2 completed; final export
965camera poses/72keyframe poses. Two explicit loop detections, without an
accuracy or repeatability claim. This is one successful retained initialized
segment, not broad robustness validation. Planar excitation only; gyro norm
peak4.48rad/s and accel norm peak44.69m/s² recorded, without attributing cause.

Cue timing was imperfect: the STOP cue arrived late, so the final stationary
hold was shorter than the planned15s. Exact physical execution/cue times are not
independently measured. No second attempt was run, respecting the one-run scope.

## Evidence, tests and handoff

- Pi root: `/home/richard/wbr-evidence/camera-day-20261021-01/`.
- Mac: `~/wbr-evidence-archive/camera-recording-20261021-01/` contains the complete
  new loop, quality/log/config receipts, physical-endpoint receipt and isolated
  native build sources/headers/binary/build logs.
- New loop MCAP SHA256:
  `5749908bb94a6c9a7e5496f3c8b58db3596cf5f53f2542502a1468dcd97703c8`;
  independently hashed Mac copy matches Pi.
- Commands: `python3 recording_trial_reliable.py NEW_RUN 150` in archived
  sourcedROS environment; `stereo_bag_quality.py NEW_RUN/sensor-bag OUTPUT --fps 15`; `bash single_inertial_attempt.sh` for the one
  bounded attempt. Exact commands/source snapshots are archived.
- Local50camera-day tests and7native-helper tests PASS, including real-source
  patch application; isolated Pi inertial compile/link exit0. No heavy simulation
  or training was run or changed. New focused recorder is `record_stereo.sh`.
- Three replays/endpoint analysis of the new bag have not been run; morning scope
  prioritizes physical capture and hardware release. Previous replay endpoint
  values belong to the older lossy loop and must not be reused for this bag.
- All176copied artifacts, including the full new loop, passed SHA256 verification.
- Final SDK readback is byte-identical to the initial readback
  (SHA256567c08f57953aef175577550314cfe37ff0b704c54a0a641c6eabdc8dd57baef).
  All camera/SLAM/recorder processes and the ROS daemon stopped; final Pi-free
  process receipt at10:15:21+07 excludes the inspection's own process ancestors.
  Earlier self-matching diagnostic snapshot retained. Throttling0x0.
- Code/reproduction changes: PR87; documentation publication/CI pending at this
  checkpoint. Feature revision9ae50e8; source/binary hashes in archived receipts.

## Recommendation for later review
Accept the observed recording-quality target and this retained initialized
inertial segment. Review the archived raw data at the cafe; next run the three
fresh visual replays on the new bag and report endpoints with map/reset context.
Do not reuse the old lossy loop's endpoint values or claim ground-truth accuracy.

## Claude review (2026-10-21)

**Decision: accepted.** PR #87 was already merged; no revert needed.

Checked against `scripts/camera_day/native/stereo_inertial_unified.patch` and the
numbers above (code read only; raw archive on the Mac not re-read).

- **IMU interpolation: correct.** Each gyro sample waits for an accel pair with
  `a.t <= g.t <= b.t`, then interpolates linearly; gyro samples older than the
  first accel are dropped, never extrapolated, and pending gyro samples survive
  image processing. Gyro and accel vectors are now pushed together, so the old
  size-mismatch padding is gone. The image wait now also requires IMU coverage up
  to the image time; samples after the image stay in ORB's IMU queue, so nothing
  is double-counted.
- **Tbc direction: correct.** `get_extrinsics_to(imu)` gives `p_imu = R p_cam + t`,
  which is ORB's `T_b_c1`; the check reads the SDK's column-major rotation as
  `Rbc[j*3+i]`. Rotation is identity here, so the translation sign is what
  actually distinguishes direction, and it is checked.
- **Rate handling: fine.** Gyro 200.18 Hz and accel 202.25 Hz on source clocks;
  the unified stream sits on the gyro grid, so `IMU.Frequency: 200` matches.
- **Evidence: supports the stated claims, no more.** 2215/2215 over 147.6 s at
  15 Hz is about 2214 expected, so the <1% recording target is met. The inertial
  claim is one run that initialized and stayed initialized for its last 61.8 s.
  The 1116 "tracked" frames include visual-only frames before IMU init, so tracked
  FPS is not an inertial-quality metric.

Small follow-ups (not blocking):

1. Accel norm peak 44.69 m/s² (about 4.6 g) may be near the accelerometer's range.
   Check per-axis maxima in `imu_raw.csv` for flat-topped samples; if clipped,
   use gentler excitation next time.
2. `native/README.md` still says the upstream accel hold behaviour is retained
   ("IMU startup ..." paragraph); the follow-up section supersedes it. Fix the
   wording on the next docs edit.
3. The unified patch drops `+offset` from IMU stamps. Harmless while `offset = 0`,
   but if anyone sets it, images and IMU would silently diverge.
4. `throw` inside the SDK motion callback runs on a librealsense thread; prefer
   setting a flag and stopping from the main loop. It never fired here.

Next (no lab needed): three visual replays of the new bag with endpoint and
reset context. Later lab run: one stereo-inertial run on the marked loop, so the
visual and visual-inertial endpoints can be compared on the same path.
