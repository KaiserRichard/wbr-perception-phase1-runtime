# C1-T13 — home supervisor video, 30 October 2026

Target: **4 min 25 s** (20 + 35 + 35 + 55 + 50 + 70 s); trim loading/typing between takes.
No D435i at home: all camera scenes are **recorded**. Only the MPU6050 and isolated CAN bench are live.
Keep every real motor disconnected. Keep the installed **T3 bench_twin v2**; do not flash or run the old AGV/LED restore scripts.
Use 460800 **8N1** on Pi `/dev/ttyAMA0`, not the older docs' 115200. One UART reader/writer at a time.
Checked by Claude 1 on 30 Oct: ssh wbr-pi5 works, and `pi_loop.py` at 100 cmd/s ran on this exact bench (99/s, 0 lost). GUI steps (Foxglove, MuJoCo viewer) were not tested; they are marked UNVERIFIED.
T1/T3/T4 are absent from this coordinator checkout; the existing task worktrees below contain their source. No checkout/merge is needed.

## 0) Five-minute prep (off camera)

- **0–1 min:** power the existing Pi/Nucleo bench, BOOT0 out; leave firmware/wiring unchanged. Confirm only the isolated CAN1↔CAN2 transceiver pair is connected. Put the phone in landscape with the MPU6050, Nucleo, LEDs and Mac visible.
- **1–2 min:** Mac Terminal, one tab for all Mac snippets below; a second tab can hold SSH diagnostics. Paste:

```sh
REPO="$HOME/.worktrees/wbr-c1-coord"
T1="$HOME/Desktop/Research/wbr-wt-t1-physics"
T2="$HOME/Desktop/Research/wbr-wt-t2-command"
T3="$HOME/Desktop/Research/wbr-wt-t3-fw"
T4="$HOME/Desktop/Research/wbr-wt-t4-foxglove"
VENV="$HOME/Desktop/Research/wbr-lab-ops/.venv"
ARCHIVE="$HOME/wbr-evidence-archive"
YOLO="$HOME/wbr-evidence/c1-20261030/p1-run/out"
DEMO=$(mktemp -d /tmp/wbr-demo-t13.XXXXXX)
export OPENBLAS_NUM_THREADS=1
cd "$REPO"
open -a Foxglove
```

- **2–3 min:** arrange Foxglove large, Terminal readable at 18–20 pt, and space for the MuJoCo viewer; keep Safari/Preview ready for saved images. Hide private notifications.
- **3–4 min:** **Cmd+Shift+5 → Record Selected Portion → Options → microphone / save location**; capture the app area, then stop with the menu-bar stop button. Phone records hardware; use a spoken “scene one” to align takes.
- **4–5 min:** try each scene once before recording. If a scene fails, use its saved fallback and say “replay”; retain the 3–6 min target. Do not spend recording time installing/building.

## 1) Hardware bench — 20 s, phone

**Goal:** show what physically exists at home: Pi 5, F446RE, MPU6050, two CAN transceivers and LEDs.
**Mac command — UNVERIFIED SSH runtime:**

```sh
ssh -o ConnectTimeout=8 wbr-pi5 'hostname; date'
```

**Window / film:** phone pans across the powered bench, follows UART and CAN wiring, then shows the SSH terminal; hold each view for 3–4 s.
**Say:** “This is the live Pi-to-STM32 bench with an MPU6050 and four firmware-emulated DM motors on an isolated CAN loop.”
**Success:** powered boards and both transceivers visible; SSH responds at `192.168.50.2`; no physical motors connected.
**If it fails:** check existing Pi power/network, then `ssh -o ConnectTimeout=8 richard@192.168.50.2` (**UNVERIFIED** fallback); if still offline, film the bench and label the following screen scenes as replay.
**LED note:** T3 uses green/yellow/red/blue for NONE/JUMP/STOP/UNCERTAIN; stale advisory turns all off. Idle LEDs can be dark; do not claim the old image's blinking behavior or induce a firmware change.

## 2) Live IMU tilt — 35 s, screen + phone insert

**Goal:** show measured board tilt becoming a complementary-filter attitude visualization; this is not balance control.
**Mac command — UNVERIFIED live transport; viewer flags confirmed:**

```sh
cd "$REPO"
ssh wbr-pi5 'stty -F /dev/ttyAMA0 460800 raw -echo cs8 -parenb -cstopb && cat /dev/ttyAMA0' \
  | "$VENV/bin/mjpython" -m tools.imu_view.view --stdin --save "$DEMO/imu-live.csv"
```

**Window / film:** MuJoCo IMU viewer. Keep chip side up/X arrow forward and hold still for its first **2 s**. Film flat 5 s, X-arrow end down 8 s, Y-arrow edge up 8 s, then hold a tilt 5 s; phone includes hand and screen.
**Say:** “The solid robot follows the live MPU6050 complementary filter, while the ghosts show accelerometer-only and gyro-only estimates.”
**Success:** flat near 0° (about ±2°); nose-down gives positive pitch, Y-edge-up positive roll; solid model holds the tilt. No translation or yaw estimate is claimed.
**If it fails:** garbling → verify 460800/8N1; wrong sign → correct board orientation. Close viewer and Ctrl-C its pipeline before scene 3; confirm its remote `cat` has ended. Do not start another UART owner.
**Saved fallback, Mac (say “recorded hand motion”):**

```sh
"$VENV/bin/mjpython" -m tools.imu_view.view --replay "$ARCHIVE/imu-view-live-20261030/imu_view_run.csv"
```

## 3) Four fake DM motors / CAN STAT — 35 s, screen

**Goal:** show real UART/CAN transport and measured feedback counters; motor dynamics/temperatures are synthetic.
**Mac commands — UNVERIFIED Pi staging/runtime; source and options confirmed.** These copy only three Python files into a fresh Pi folder. Start with a fresh normal application session and no other UART user; the runner starts command sequence at zero.

```sh
if PI_DEMO=$(ssh wbr-pi5 'mktemp -d "$HOME/wbr-demo-t13.XXXXXX"') && test -n "$PI_DEMO"; then
ssh wbr-pi5 "mkdir -p '$PI_DEMO/tools/bench_twin_fw' '$PI_DEMO/tools/link_proto/py'"
scp "$T3/tools/bench_twin_fw/"{pi_loop.py,host.py} "wbr-pi5:$PI_DEMO/tools/bench_twin_fw/"
scp "$T3/tools/link_proto/py/link_proto.py" "wbr-pi5:$PI_DEMO/tools/link_proto/py/"
PI_PY=/usr/bin/python3  # has pyserial (checked 30 Oct)
ssh wbr-pi5 "$PI_PY '$PI_DEMO/tools/bench_twin_fw/pi_loop.py' /dev/ttyAMA0 --rate 100 --seconds 10 --raw-log '$PI_DEMO/rx.jsonl'" \
  | tee "$DEMO/can-all.jsonl" | grep --line-buffered -E '"event": "(stat_baseline|stat_delta|writer_total)"'
fi
```

**Window / film:** enlarge Terminal; film `stat_baseline`, successive `stat_delta` rows and final `writer_total`; pause on the completed output to explain it. IDs round-robin **6, 8, 0, 1**.
**Say:** “Zero-target commands traverse CAN1 to CAN2's four fake DM motors, and these STAT deltas expose feedback, rejected commands and transport losses.”
**Success:** `sent_s` and `fed_back_s` track roughly 100 aggregate/s during writing, `rejected_s`/`lost_s`/drop-error deltas zero, then rates fall during the 2.2 s drain. Deadline misses are reported, not hidden. No enable command is sent; every target/gain/torque is zero.
**If it fails:** no STAT → stop and check UART ownership/baud; rising loss → inspect the existing isolated CAN wiring off camera. Old-sequence rejection → stop all UART processes, BOOT0 out, reset normal application once, rerun with a fresh raw-log name; never reset into a fitted-BOOT0 bootloader.
**Missing `serial` only — UNVERIFIED recovery:** `ssh wbr-pi5 "python3 -m venv '$PI_DEMO/venv' && '$PI_DEMO/venv/bin/pip' install pyserial"`; set `PI_PY="$PI_DEMO/venv/bin/python"` and rerun with a new `--raw-log` filename. If unresolved, show scene 4's recorded BUS data and label it recorded.

## 4) Foxglove four areas — 55 s, screen; RECORDED

**Goal:** explain BRAIN/BODY/BUS/TWIN together without suggesting a synchronized live robot.
**Mac commands:** stage links to the three existing MCAPs in one chooser folder; originals stay unchanged.

```sh
mkdir "$DEMO/foxglove"
ln -s "$ARCHIVE/lab-day-20261025/3-box13/camera-bag/camera-bag_0.mcap" "$DEMO/foxglove/camera.mcap"
ln -s "$ARCHIVE/foxglove-twin-20261030-01/twin.mcap" "$DEMO/foxglove/twin.mcap"
ln -s "$ARCHIVE/bench-twin-foxglove-20261030-01/bench_twin.mcap" "$DEMO/foxglove/bench.mcap"
open "$DEMO/foxglove"
open -R "$T4/docs/bench_twin_foxglove/layout.json"
```

**App:** Foxglove → Open local files, select **all three links together**; import **`~/Desktop/Research/wbr-wt-t4-foxglove/docs/bench_twin_foxglove/layout.json`** via Layouts → Import from file. Opening files separately replaces the source.
**Panels:** BRAIN Image `/camera/camera/color/image_raw` + Raw Messages `/brain/advisory`; BODY Plot `/body/imu.{pitch_rad,roll_rad,pitch_rate_rad_s,roll_rate_rad_s}` and `/body/leg_length.length_m` + State Transitions `/body/jump_phase.phase`; BUS Plot `/bus/stats.{rate_hz,errors,busy}` + Raw Messages `/bus/motor_feedback`; TWIN 3D `/twin/scene`, fixed frame **`base_link`**, plus its raw messages. Four named areas contain eight panels, not four individual panels.
**Film:** play at 1× in the first camera minute; spend 15 s on image/advisory, 15 s on BODY/BUS, seek around packet-relative 20 s for the synthetic phase, then 15 s on the schematic. Camera/twin overlap is about 59 s.
**Say:** “This recorded dashboard combines camera advice, measured IMU and CAN traces, and a schematic twin; capture alignment is arbitrary and jump phases and zero motor feedback are synthetic.”
**Success:** camera changes, plots populate, phase changes, scene entities appear; `/brain/advisory` exposes raw/gated outputs. This recording contains no ORB pose.
**If it fails:** blank panels → reselect all files and seek into their overlap; 3D → enable `/twin/scene` and fixed frame `base_link`. If import/playback fails, use the verified 24 Oct fallback below and describe it as camera/depth/advisory only:

```sh
open "$ARCHIVE/mobile-demo-20261024-01/foxglove-demo"
```

Open `B-H05.mcap` there and import its `foxglove_demo_layout.json`: Color image, ground-aligned detector 3D, advisory height/distance. GUI import/playback remains UNVERIFIED in this session.

## 5) MuJoCo physics twin — 50 s, screen; SIMULATION

**Goal:** show stand, drive and jump physics, and distinguish the saved 8 cm obstacle result from the interactive flat-ground demo.
**Mac commands:** T1's runner is headless and has no `--viewer`; use the existing T2 viewer of the T1 plant.

```sh
cd "$T1"
python3 -m sim.twin3d.check "$ARCHIVE/twin3d-20261030-01/runs/corrected" --out "$DEMO/t1-check.json" > "$DEMO/t1-check.txt"
python3 -c 'import json,sys; x=json.load(open(sys.argv[1])); print("T1 saved batch PASS:",x["passed"],"jumps:",x["jump_passes"],"/",x["jump_runs"])' "$DEMO/t1-check.json"
cd "$T2"
"$VENV/bin/mjpython" -m sim.twin3d_cmd.teleop_viewer
```

**Window / film:** Terminal result 5 s; viewer stand 8 s, press **W six times** for a 0.30 m/s target and film 10 s, then **R** to reset, **Space once** for a stationary jump/landing, **R** to rearm. Film phase, pitch, length and actual velocity overlay; Esc quits. Viewer GUI/runtime is UNVERIFIED here; source/keys confirmed.
**Say:** “This assumed planar contact model balances, drives and jumps under physics, while the separate saved T1 obstacle batch cleared an 8 cm box in ten of ten seeds.”
**Success:** upright stand, wheel-driven motion, CROUCH→THRUST→RETRACT→SETTLE and landing; saved batch PASS. The T2 viewer has **no box**; 8 cm clearance is the saved T1 result (42.4–46.0 mm minimum wheel margin), not this keyboard take.
**If it fails:** missing module → use the exact task-worktree `cd` above; GUI/port failure → close this viewer and film `$DEMO/t1-check.txt` in TextEdit (`open -a TextEdit "$DEMO/t1-check.txt"`). If checker fails, retain output and say FAIL; do not substitute the scripted jump-gate animation as physics. Ideal actuators/virtual legs are uncalibrated; this is not hardware jump validation.

## 6) ORB-SLAM3 replay + YOLO overlays — 70 s, screen; RECORDED

**Goal:** show visual translation/map evidence, then object-detection outputs from bags; these are separate runs, not one live fused pipeline.
**Mac commands:**

```sh
ORB="$ARCHIVE/lab-day-20261025/MAP-2m-r3-foxglove"
open "$ORB"
open -a Safari "$YOLO/p1-detections.gif"
open -a Preview "$YOLO/overlay-B-H05-0000.png"
```

**App / panels:** Foxglove open **`$ORB/MAP-2m-r3-foxglove.mcap`** alone; import **`$ORB/map_demo_layout.json`** (use the folder just opened). Left = infrared Image; right = red `/orb/path` and `/d435_orb/map_points` in 3D, fixed frame **`map`**; bottom = `/d435_orb/pose.pose.position.z`. This is the **25 Oct stereo replay**, not the 24 Oct RGB-D bags.
**Film:** 30 s of ORB playback/path, 25 s Safari GIF, 15 s Preview B-H05 still. GIF/overlays use **24 Oct** B-H13/B-H05/S1-empty/W1 bags; the raw bags under `mobile-demo-20261024-01/*/rgbd-bag` are SQLite `.db3`, not the exported Foxglove MCAPs.
**Say:** “ORB-SLAM3 reconstructs camera motion from a recorded stereo run, while YOLO finds familiar objects in the 24 October bags but misses the books, so obstacle geometry still needs depth.”
**Success:** red path/sparse points appear; GIF animates with COCO boxes/depth labels; B-H05 shows the book limitation. Pitch/roll are IMU estimates; translation here is visual SLAM, never acceleration double integration.
**If it fails:** map panel blank → fixed frame `map`, enable both topics and seek forward; fallback `open -a Preview "$ARCHIVE/lab-day-20261025/MAP-2m-r3-check/topdown.png"`. GIF fails → `open -a Preview "$YOLO/overlay-B-H13-0000.png"`; label stills. Do not rerun inference/SLAM while filming.
**Closing caption:** “Live IMU + isolated CAN bench; archived camera perception; assumed simulation. No real motors driven.” End recording, keep original takes and trim only pauses/loading.

**Source trail:** all 19 files in `ops/demo-src/` read (the two T5 lab-day bodies are identical); T1 `sim/twin3d/{run,check,model}.py`, T2 `sim/twin3d_cmd/teleop_viewer.py`, T3 `tools/bench_twin_fw/{pi_loop,host}.py`, T4 layout JSON, coordinator IMU/bag tools, and the named local archives checked. Recorded MCAP topic counts checked; no UART, firmware or motor action executed for this guide.
