# Lab log — 2026-10-24

Written by the lab assistant (ChatGPT Work / Codex) as the owner reports.
Claude 2 reads this file; do not delete entries, only append.

## Setup (fill once, re-measure at the end)

| Item | Start | End |
|---|---|---|
| Camera serial (from preflight) | 317422076650 | |
| Camera height floor → lens centre (m) | 0.290 (tabletop → lens centre) | |
| Camera tilt, down positive (deg) | 10 | |
| Power source label (V / A) | UNKNOWN (wall supply reported 5.10 V / 5.00 A; printed label not reported) | |
| Floor type / lighting | Matte artificial-wood tabletop, 0.80 m wide / bright lab lighting, desk lamp off | |

## Runs (one entry per run, in order)

### Setup deviation
- Claude 2 approved using a long matte tabletop instead of the glossy lab floor.
- Camera is centred and points along the table length; lateral offset was not measured.
- Static-run boxes will be centred on the camera line; the ±25 cm corridor remains clear.
- Final obstacle heights (cm): 2.45, 4.50, 8.38, 13.15, 26.35.
- W1 vertical target is available at 1.00 m.

<!-- Template:
### HH:MM  RUN_ID  (mode)
- What was done:
- Measurements:
- Problems / deviations:
- Status: DONE / REDO / SKIPPED (why)
FOR CLAUDE 2: <one line, e.g. "W1 recorded, please check bag">
-->

## End-of-day summary

- Runs done:
- Runs skipped / failed and why:
- Open questions for Claude 2:

### 09:20  B-H02 (rgbd) — bag folder S1/ (owner placed the book; S1 empty-table run still to do)
- What was done: static 10 s, book 2.45 cm on the camera line at about 1 m.
- Measurements: book height 0.0245 m; distance UNKNOWN exact (about 1 m); width UNKNOWN.
- Result (Claude 2, offline on Mac): 137/137 plane valid; camera height 0.291 m (tape 0.290);
  pitch 11.3 deg (inclinometer 10); plane height std 2.1 mm, pitch std 0.20 deg (stability PASS);
  obstacle height 3.30 cm (+0.85 cm), distance 1.020 m, width 24.3 cm; advisory JUMP_CANDIDATE 135/137.
- Topic counts ~137 per stream in 9.2 s; throttled=0x0.
- Status: DONE

### 09:35  B-H02-old marked SUPERSEDED
- Owner: book was not placed at exactly 1.00 m; rerun as B-H02. Bag S1/ kept (not deleted).

### 09:38  B-H02 (rgbd)
- Static 10 s, book 2.45 cm (width 23.7 cm), front edge 1.00 m by tape, on the line.
- Result: 138/138 plane valid; camera height 0.2914 m (tape 0.290); pitch 11.3 deg;
  height std 2.0 mm, pitch std 0.20 deg; obstacle h 3.27 cm (+0.82), d 1.018 m (+1.8 cm),
  w 24.9 cm (+1.2); advisory JUMP_CANDIDATE 135/138. Counts 130–138 / 9.2 s; throttled=0x0.
- Status: DONE

### 09:45  S1 (rgbd) — bag S1-empty/
- Static 10 s, strip empty up to the desk-lamp pole (~1.42 m, inside the corridor) and the wall (~1.60 m).
- Result: 110/110 plane valid; camera height 0.2932 m; pitch 9.63 deg (B-H02: 11.34 deg -> camera
  likely moved ~1.7 deg between runs); height std 1.5 mm, pitch std 0.13 deg (stability PASS).
  Nearest obstacle 1.424 m, 0.64 m tall = lamp pole + wall -> STOP_CANDIDATE (correct).
  Within 1.3 m: 2/110 single-frame detections (1.8%); centre wall depth 1.622 m axial ~ 1.60 m horizontal.
- Status: DONE

### 09:52  B-H05 (rgbd)
- 2 books 4.50 cm at 1.00 m. Result: 110/110 plane; cam h 0.2957, pitch 9.90; h std 3.3 mm, p std 0.29 deg;
  obstacle h 5.18 cm (+0.68), d 1.023 m (+2.3 cm), w 27.5 cm (+3.8); advisory JUMP 105 / STOP 3 / UNC 2. throttled=0x0.
- Status: DONE
- Owner correction: offset stack, measured width 24.8 cm -> width error +2.7 cm.

### 09:58  B-H08 (rgbd)
- 4 books, height re-measured 8.5 cm, at 1.00 m. Result: 139/139 plane; cam h 0.2964, pitch 10.06; h std 3.7 mm, p std 0.33 deg (slightly above 0.3);
  obstacle h 9.31 cm (+0.81), d 1.017 m (+1.7 cm), w 28.4 cm (tape width UNKNOWN); advisory JUMP 134 / STOP 3 / UNC 2. throttled=0x0.
- Status: DONE

### 10:03  B-H08-rep (bag folder B-H26/) — started too early by Claude 2
- The 4 books were still in place: valid repeat of B-H08. h 9.32 cm (B-H08: 9.31), d 1.017 m, w 28.5 cm.
- Width: tape 23.7 cm -> +4.7 cm (B-H08 same). The 26.35 cm stack will be recorded as B-H26b.

### 10:07  B-H26 (rgbd, bag B-H26b/)
- 4 boxes 26.35 cm at 1.00 m. Result: 109/109 plane; cam h 0.2950, pitch 10.03; h std 2.8 mm, p std 0.25 deg;
  obstacle h 25.37 cm (-0.98), d 0.984 m (-1.6 cm), w 25.0 cm (tape 22.1-22.2: +2.9); advisory STOP 107 / UNC 2. throttled=0x0.
- Status: DONE

### 10:12  B-H13 (rgbd)
- 2 boxes 13.3 cm at 1.00 m. Result: 110/110 plane; cam h 0.2952, pitch 10.02; h std 3.7 mm, p std 0.33 deg;
  obstacle h 13.56 cm (+0.26), d 1.013 m (+1.3 cm), w 26.1 cm (+3.9); advisory STOP 108 / UNC 2. throttled=0x0.
- Status: DONE

### 10:20  B-H05-D0p5 (rgbd, bag B-H05-D0p5b/; folder B-H05-D0p5 = INVALID, recorded during adjustment)
- 4.6 cm books at 0.50 m. Result: 110/110 plane; cam h 0.2924, pitch 9.80; h std 9.3 mm, p std 0.72 deg (less table visible);
  obstacle h 5.39 cm (+0.79), d 0.531 m (+3.1 cm), w 24.8 cm (0.0); advisory JUMP 108 / UNC 2. throttled=0x0.
- Status: DONE

### 10:45  Pi power loss (cable), rebooted; mDNS slow, Claude 2 uses IP 192.168.0.101
### 10:47  B-H05-D1p3 (rgbd)
- Owner: books at 1.30 m by tape, close to the wall and lamp pole.
- Result: nearest cluster d 1.383 m, h 0.576 m, w 0.50 m = books merged with the lamp pole -> STOP 134/136.
  Centre depth 1.486 m axial. Camera pitch 11.42 deg (was 9.8 before power loss): camera likely bumped.
- Status: DONE (limitation case: adjacent objects merge into one cluster)

### 10:55  W1 (rgbd)
- Wall 1.00 m by tape. Centre depth 1.023 m axial; pitch 11.85 deg -> horizontal 1.023*cos(11.85)=1.001 m (error +0.1 cm).
  Nearest corridor obstacle 0.837 m = lamp pole. throttled=0x0. Status: DONE

### 11:00  W2 (rgbd)
- Wall 1.50 m by tape. Centre ROI 1.437 m is the TABLETOP (centre ray reaches the table at 0.29/tan(11.8 deg)=1.39 m) -> evaluate from wall points offline.
  throttled=0x0. Status: DONE (data OK, check method needs the wall points)
