# Session facts for the deck — 2026-10-13 (Pi 5 4 GB stand-in, new D435i)

Source of truth for new slides explaining today's work. Every number here has an evidence file; cite the path.
Labels: MEASURED / CALCULATED / SOURCE-SUPPORTED / INFERRED / UNKNOWN. Nothing below is a gate PASS.

## A. Platform today (MEASURED)
- Raspberry Pi 5 **4 GB** (temporary; target is 8 GB), Ubuntu 24.04.4, kernel 6.8.0-1064-raspi, ROS 2 Jazzy binary, booting from a **32 GB microSD** (no NVMe). 5 V / 3 A supply.
- Power: `vcgencmd get_throttled` live under-voltage (`0x50005`) under load — 46 events during the build, **87 of 178 samples (49 %)** during SLAM runs. A 5.1 V / 5 A supply and a 128 GB V30/A2 microSD (KIOXIA EXCERIA G3) are ordered.
- Pi clock was 80 min behind with no internet; fixed 2026-10-13 ~09:45Z by joining Wi-Fi (NTP synced). Pi-side UTC labels before that are offset (see N4A report).
- Evidence: `experiments/2026-10-13-pi5-env-snapshot/`, `experiments/2026-10-13-orbslam3-pi-build/` (power log on the Pi).

## B. New camera (MEASURED, `experiments/2026-10-13-pi5-env-snapshot/ADDENDUM_CAMERA_SWAP.md`)
- Active D435i: SDK serial **317422076650**, USB/ASIC serial **327743061057**, FW 5.17.3.10, BMI085, USB 3.2 @ 5000 Mbps. Old unit (Sep evidence): SDK 243322073847 / USB 251843061466. Old N1/N2/calibration do not transfer.
- Two serials per camera: udev + IIO helper match the **USB** serial; ROS `serial_no` and N1/capture tooling match the **SDK** serial. udev now allows both units (backup `/var/backups/wbr-udev-2026-10-13/`).
- Codex updated N1/N2 tooling: single `ACTIVE_UNIT` definition, `--diagnostic-latched-power` mode → results `OPEN_DIAGNOSTIC`, never PASS (55/56 tests pass). Report: `experiments/2026-10-13-pi5-env-snapshot/CODEX_TICKET_SERIAL_POWER_REPORT.md`.

## C. ORB-SLAM3 native build on the Pi (MEASURED, `experiments/2026-10-13-orbslam3-pi-build/`)
- Upstream 4452a3c copied to `~/orbslam3/ORB_SLAM3`; repo checkout untouched. Pangolin v0.9.1 (built in 178 s).
- Three minimal patches for Ubuntu 24.04 / GCC 13: (1) C++11→C++17 and drop `-march=native`; (2) Sophus unit tests off (their `-Werror=array-bounds` fails on aarch64; ORB-SLAM3 only uses Sophus headers); (3) `mnFullBAIdx++` on a `bool` → `= true` (C++17 forbids bool++; identical C++11 semantics).
- Main library compile ≈71 min at `-j2`; needed 4 GB + 4 GB temporary swap (RAM fell to 130 MB free). INFERRED: on 8 GB this builds without swap.

## D. N4A — "Known-dataset baseline" (MEASURED, `experiments/2026-10-13-n4a-euroc-mh01/REPORT.md`)
What it is, for the slide:
- **EuRoC MH01** = public drone dataset (ETH Zurich): stereo grayscale cameras 20 Hz + IMU 200 Hz flown in a machine hall, with **ground truth** position from a laser tracker / motion capture. 184 s, 3,682 stereo frames.
- We ran the **unmodified upstream** example `stereo_inertial_euroc` with the upstream `EuRoC.yaml` on the Pi, 3 times, headless.
- **ATE (Absolute Trajectory Error)**: align the estimated path to ground truth with one rigid transform (SE(3): rotation + translation, no scale for stereo-inertial), then take the RMS of the position differences. evo `evo_ape tum … -a`.
- Results: ATE RMSE **0.0415 / 0.0368 / 0.0416 m** (mean 0.040 m), 1 map, no resets, IMU initialized every run, peak RAM ≈830 MB. ORB-SLAM3 paper (Campos et al., T-RO 2021) reports ≈0.036 m for this case (SOURCE-SUPPORTED, verified in Table II: MH01 = 0.036 m, SE(3) alignment).
- Meaning: the **algorithm + our ARM64 build + patches reproduce published accuracy** on a dataset where the right answer is known. This isolates "is ORB-SLAM3 itself working?" from "is our camera/calibration/timing working?" — the core of the "known baseline before adaptation" rule.
- Does NOT prove: anything about our D435i, its calibration, timestamps, or real-time speed. Speed invalid: 282–301 s wall for 184 s of data (INFERRED ≈60–70 ms/frame, slower than 20 Hz) while the CPU was throttling from under-voltage.

## E. D435i programs (built on the Pi, OPEN; design `experiments/2026-10-13-n4b-d435i-prep/`)
Two small programs, written by Codex, built by Claude on the Pi in `~/wbr-runtime/n4b-20261013T080913Z/bin/`:
1. **`d435i_record`** — a recorder. Opens the D435i via librealsense (no ROS), streams **IR1 + IR2 (left/right infrared, 640×480 Y8, 30 Hz)**, **gyro 200 Hz**, **accel 100 Hz**, **IR emitter OFF** (the projector's dot pattern would create fake features that move with the camera), and writes everything with the camera's own timestamps into one librealsense recording file (`stereo_imu.db3`, rosbag2 format since librealsense 2.56) plus `timestamps.csv`. Budget ≈18.4 MB/s ≈1.1 GB/min (CALCULATED).
2. **`stereo_inertial_realsense_D435i`** (patched upstream example) — runs ORB-SLAM3 stereo-inertial on the D435i. Same program for both modes:
   - `--bag FILE` → **offline (N4B)**: plays the recording back frame-by-frame (not real-time), so the same data can be re-run and debugged identically;
   - no `--bag` → **live (N4C)**: reads the camera directly.
   - `--no-viewer` → no GUI (Pi runs headless).
   Patch also fixes upstream input handling (IMU samples between images, accel interpolated onto the gyro timeline, rejects backward/duplicate timestamps and gaps >50 ms).
- Config `D435i_317422076650_stereo_inertial.yaml`: intrinsics fx=fy=386.95, cx=321.03, cy=241.04 @640×480, stereo baseline 0.0499 m, camera→IMU transform from factory extrinsics (nominal, not calibrated). IMU noise values copied from upstream RealSense example = **ASSUMED** (needs Allan variance). SDK warns "IMU Calibration is not available".
- Pipeline for the slide: D435i (USB 3) → librealsense → [record to .db3] → playback → patched example (IMU preintegration + stereo ORB features) → ORB-SLAM3 tracking / local mapping / loop closing → trajectory file → evo.
- Next physical step: user moves the camera by hand ≈60–90 s (first 20–30 s translate 10–30 cm in all axes with ±15–30° rotations, then a small loop, end 5–10 s still). IMU init needs ≥10 keyframes and motion; log should show "IMU initialized", 1 map, no "Not enough motion… Reseting".
- Status: built, linkage clean (`ldd` no missing libs), **never run on the camera yet**. N1 on the new unit stopped at the clock prerequisite (now fixed).

## F. Storage decision (CALCULATED)
- 32 GB card: 13 GB free; September write probe ≈19 MB/s (worst 17) ≈ stereo rate 18.4 MB/s → no margin.
- 128 GB V30 card: ≈95 GB usable for data after OS/tools/headroom ≈ 55–90 test takes of 60–90 s; copy takes to the Mac after each session.
- Migration plan: clone the whole 32 GB card to an image on the Mac, write to 128 GB, grow root, keep the 32 GB card as backup.
