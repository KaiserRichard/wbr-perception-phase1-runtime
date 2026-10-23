# Lab checklist — 2026-10-24 (one controlled, reusable dataset)

Goal: one well-measured dataset that serves all offline work for the Oct 31
demo: ORB-SLAM3 lab map, depth accuracy, box measurement, local map. Commands
and stop rules are in [RUNBOOK.md](RUNBOOK.md); use run root
`~/wbr-evidence/mobile-demo-20261024-01`. No motor commands from the Pi.

## 1. Bring / prepare

- [ ] About 5 obstacles of whatever is at hand (books, shoe boxes, cardboard
      boxes, a brick, a stool). Exact sizes do not matter; the spread does:
      one ~2–4 cm, one ~5 cm, one ~8–10 cm, one ~12–15 cm, one ≥ 20 cm.
      Rigid, flat top, matte, not black, width ≥ 15 cm. Measure each and
      write the measured height on it.
- [ ] **Wall target:** a real flat, plain wall is enough (no board needed).
- [ ] Tape measure (5 m), steel ruler or caliper (box heights), phone
      inclinometer app or angle ruler, small bubble level, masking tape,
      marker pen, printed run sheet.
- [ ] Screwdriver / hex keys for the mount, zip ties or velcro for cable strain
      relief, short known-good USB 3 cable (+ a spare).
- [ ] Power for a moving rig: the 27 W Pi supply plus an extension cord long
      enough for the push route (or a power bank that supplies 5 V / 5 A).
- [ ] Camera mount rigid on the mobile robot; cable strain relief and slack.
      The robot is **pushed by hand** (no motors): push slowly and smoothly,
      about walking-slow (~0.2–0.3 m/s), no jerks or lifting.
- [ ] Stay on the **floor**, not a table (the robot drives on the floor; table
      edges and height change the geometry). If the floor is glossy, lay a
      matte area (cardboard sheets, carpet, a mat, about 1 x 3 m) for S1/B runs,
      and repeat B2 (5 cm at 1 m) once on the bare glossy floor as a hard case.

## 2. Rig geometry (fix once, never change during the session)

- [ ] Camera facing forward, **tilted down ~10°** (floor visible from ~0.4 m;
      a level camera at 0.3 m loses a 5 cm box closer than ~0.55 m).
- [ ] Measure and write down: camera height (floor → lens centre), tilt (deg,
      down positive), lateral offset from robot centre. Photo of the mount.
- [ ] Stability: press/tap the camera; it must not move. Re-measure height and
      tilt at the end of the session.

## 3. Runs (in this order; ~2.5 h)

| ID | Mode | What | Needs ORB | Ground truth to record |
|---|---|---|---|---|
| P0 | — | Preflight (RUNBOOK §1), `dmesg -w` running all session | – | serial, FW, 5000M, power |
| S1 | RGB-D | Static 10 s, empty floor | no | camera height/tilt (tape) |
| W1 | RGB-D | Static 5 s, facing a flat wall perpendicularly at **1.00 m** | no | tape distance lens→wall |
| W2 | RGB-D | Same at **2.00 m** | no | tape distance |
| B1–B5 | RGB-D | Static 5 s, box 3/5/8/12/20 cm, front face at **1.00 m**, centred | no | box h/w, distance, lateral offset |
| B6–B8 | RGB-D | Static 5 s, **5 cm** box at 0.5 / 1.5 / 2.0 m | no | same |
| A1 | RGB-D | Slow approach (operator drives, ~0.2 m/s) from 3 m to 0.5 m toward 5 cm box | optional | start/stop floor marks |
| A2 | RGB-D | Same toward 20 cm box | optional | same |
| M0 | Stereo | 30 s motion check (RUNBOOK §2) | yes | – |
| M1 | Stereo | Lab map, 180 s: tape-marked start, slow loop through the lab, return to the start mark | yes | start mark, return offset (tape) |
| M2 | RGB-D | 60–120 s corridor drive with 2–3 boxes placed on the path (local-map demo data) | yes | box positions on floor (tape from start mark) |
| L1 | Stereo or RGB-D | Straight **3.00 m** drive between two tape marks, stop, return | yes | 3.00 m (tape) |

Run B1–B8 as one static camera pose (move only the box). Do the stereo map runs
after the static runs so a USB problem does not cost the controlled data.

## 3b. Frame rate (decided 2026-10-23)

Use **RGB-D at 15 Hz**, not the RUNBOOK's 30 Hz: pass `fps:=15` to
`d435_camera.launch.py` and `--fps 15` to `sdk_to_yaml.py`. CALCULATED,
uncompressed: colour 921.6 kB + raw depth 614.4 kB + aligned depth 614.4 kB
per frame → 32 MB/s at 15 Hz vs 64 MB/s at 30 Hz. The card is rated 50 MB/s
write (manufacturer, peak sequential), so 30 Hz cannot fit. Morning check: a
1 GB write test with sync on the evidence disk. If sustained write is below
~45 MB/s, drop the raw depth topic (aligned only: 23 MB/s). Stereo map runs
stay at 15 Hz (8.8 MB/s measured).

## 4. Topics and metadata per run

- RGB-D (RUNBOOK §3 `record.sh rgbd`): `/camera/camera/color/image_raw`,
  `/camera/camera/color/camera_info`, `/camera/camera/depth/image_rect_raw`,
  `/camera/camera/depth/camera_info`, `/camera/camera/aligned_depth_to_color/image_raw`,
  `/camera/camera/aligned_depth_to_color/camera_info`, `/tf_static`,
  `/d435_orb/pose`, `/d435_orb/status`.
- Stereo (verified runner): `/camera/camera/infra{1,2}/image_rect_raw` +
  `camera_info`; keep `capture_summary.json`, `slam.log`, `stereo.yaml`.
- Every run folder: one row in `run_sheet.csv`, `camera-parameters.yaml`
  (`ros2 param dump /camera/camera`), kernel log excerpt, a phone photo of the
  scene with the tape visible.

## 5. PASS / FAIL (decided before looking at results)

| Check | When | PASS |
|---|---|---|
| Capture validity | after each run (Pi) | all topics present, image count ≥ 95% of rate × duration, no USB reset in `dmesg` |
| Camera stability | S1 offline | fitted floor height std ≤ 5 mm, pitch std ≤ 0.3° over 10 s; start/end tape height differ ≤ 5 mm |
| Depth accuracy | W1/W2 offline | wall depth within **2%** of tape (D435 datasheet class) at 1 m and 2 m |
| Box measurement | B1–B8 offline | height error ≤ 1.5 cm and distance error ≤ 5 cm up to 1.5 m |
| Advisory | B, A offline | 3–12 cm → JUMP_CANDIDATE, 20 cm → STOP_CANDIDATE, empty → NONE (current assumed thresholds) |
| ORB tracking | M1, M2, L1 | tracking OK ≥ 95% of frames, no reset/new map |
| ORB metric check | L1 offline | 3.00 m segment length error ≤ 5 cm; return-to-start error reported (not PASS/FAIL) |

FAIL is still evidence: keep every run, never overwrite.

## 6. Save and hand over

1. Keep everything under the run root on the Pi; never delete a failed run.
2. Copy to the Mac with checksums (RUNBOOK §4) into
   `~/wbr-evidence-archive/mobile-demo-20261024-01/`.
3. On the Mac: `check_capture.py` on each RGB-D bag (RUNBOOK §3).
4. Tell Claude 2 the archive path; offline evaluation (`tools/obstacle_decision/eval_runs.py`,
   map export, local map) starts from there.

Run sheet: `run_sheet.csv` uses metres and the column names read by
`tools/obstacle_decision/eval_runs.py` (`bag_path` relative to the run root;
`wall_distance_m` only for W1/W2; leave unused cells empty).
