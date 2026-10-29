# Final lab runbook — 30 Oct 2026
**Scope:** one session before the 31 Oct deadline. Robot Operating System (ROS) 2 and red-green-blue plus depth (RGB-D) are used below. Push/carry by hand only; no motor commands. Keep camera mount, profile, power and lighting fixed. Preserve failed runs. **Pass** below means the documented operation completed and its evidence was retained; it is not a system safety or accuracy claim.

## 0 — Nucleo-F446RE image check (mandatory first)
Stop the micro-ROS agent before touching the universal asynchronous receiver-transmitter (UART). A text banner is not documented for the AGV `canfix01` image (**UNVERIFIED**); do not identify an image from LEDs alone. The inertial measurement unit (IMU)/controller area network (CAN) image prints `PIN`, `LOOP`, `NORM`, `I,...`, and `STAT` at 115200 baud. The link-bench image uses 460800 baud binary protocol; LD2 indicates link, and external red blinking at 2 Hz means no/stale advisory. These behaviors are clues, not definitive image identification.
**Read-only flash identification:** `flash_safe.py` with no `--flash` (same readback path as `stm32boot.py`, with a quiet-line bootloader sync) reads the full 512 KiB twice, compares the reads and writes a backup/SHA file on the Pi; it does not erase or write Nucleo flash. It does require BOOT0 + RESET to enter read-only memory (ROM) bootloader, so the running application is reset. Open it before fitting BOOT0/pressing RESET; remove BOOT0 and press RESET afterward. Compare backup prefix with candidate `.bin` files using the command below. No match means **UNVERIFIED — STOP**. Do not use `flash.sh` for identification: it writes.
```bash
# On the Mac, from the repository root (main): stage the LED image on the Pi (it is not there as of 30 Oct 00:30).
scp tools/link_bench/firmware/prebuilt/link_bench_f446.bin wbr-pi5:~/imu-can-bench/link_bench_f446.bin

ssh wbr-pi5
mkdir -p ~/wbr-evidence/lab-day-20261030
pkill -f "micro_ros_agent serial" || true   # the agent owns /dev/ttyAMA0
cd ~/imu-can-bench
python3 ./flash_safe.py --port /dev/ttyAMA0 --out "$HOME/wbr-evidence/lab-day-20261030/step0-readback"

# When it says it is waiting: fit BOOT0 (CN7 pin 5 to 7), then press RESET.

# After read completes: remove BOOT0, then press RESET.
BACKUP="$HOME/wbr-evidence/lab-day-20261030/step0-readback/flash-backup.bin"   # written by stm32boot.py backup()
for IMG in ~/imu-can-bench/*.bin ~/course-stage/fw/*.bin; do
  cmp -s -n "$(stat -c %s "$IMG")" "$IMG" "$BACKUP" && echo "MATCH $IMG"
done
sha256sum "$BACKUP"
```
The loop covers every image on the Pi: `imu_can_bench*.bin`, `agv_f446_home_canfix02/03/04*.bin`, `link_bench_f446.bin`, the canfix01 image and the course OS images. Image references: IMU/CAN `imu_can_bench.bin` SHA-256 `937c2857…721025a7`; `canfix01` `wbr-agv_f446_home_canfix01.bin` SHA-256 `f614cde0…ecf296`; LIVE needs the LED image `link_bench_f446.bin`, SHA-256 **`bf5721b44c0d9eafa4b5b53fb75f1ceec8c6e3c72a0c81d5a6bfd7635fe003ed`** (checked-in file and `SHA256SUMS` agree; the `07f0af8d…` value in `LED_REPORT.md` is stale, from before commit `d29beae` added the 4 Hz yellow UNCERTAIN blink). If the loop prints `MATCH …link_bench_f446.bin`, skip the flash below.
`flash.sh`, `restore_canfix01.sh`, `flash_safe.py` and `stm32boot.py` are already in `~/imu-can-bench/` on the Pi (checked 30 Oct 00:30). Flash the LED image as follows. `flash.sh` backs up twice, then **writes** (mass erase, program, verify, and start image). At “waiting for bootloader”: fit BOOT0 → press RESET → allow flash/write/verify → remove BOOT0 → press RESET.
```bash
cd ~/imu-can-bench
./flash.sh "$HOME/imu-can-bench/link_bench_f446.bin" bf5721b44c0d9eafa4b5b53fb75f1ceec8c6e3c72a0c81d5a6bfd7635fe003ed "$HOME/wbr-evidence/lab-day-20261030/step0-link-led-flash"
```
After the session, restore the AGV image. This command **writes** flash; at its bootloader prompt fit BOOT0 → press RESET → allow restore/verify → remove BOOT0 → press RESET. Its default image path and SHA are embedded in the script.
```bash
cd ~/imu-can-bench
./restore_canfix01.sh
```
**0 PASS:** readback matches `link_bench_f446.bin` or the LED-image flash verifies. **FAIL/STOP:** no candidate match (record the backup SHA; nothing is lost because the backup is kept), backup/read/verify failure, or wrong image; do not proceed to LIVE. M1, L1 and A1 do not use the Nucleo and may run anyway.

## Preflight (before M1)
```bash
ssh wbr-pi5
rs-enumerate-devices
vcgencmd get_throttled
df -h "$HOME"
```
Confirm RealSense serial `317422076650` and universal serial bus (USB) `5000M`, throttle exactly `throttled=0x0`, and sufficient free space for bags. **UNVERIFIED:** a numeric free-space minimum is not specified in the sources. **Preflight PASS:** all three checks meet those conditions; **FAIL:** stop on any mismatch. Start the saved kernel watcher in another terminal:
```bash
mkdir -p "$HOME/wbr-evidence/lab-day-20261030"
journalctl -kf | tee "$HOME/wbr-evidence/lab-day-20261030/kernel-live.log"
```
Run LIVE and P1 from the Pi checkout `cd ~/wbr-demo-20261026` (GIT_REVISION `7d8862c`; its `live_chain.sh` and `path_live.sh` are byte-identical to main, checked 30 Oct). Evidence root: `$HOME/wbr-evidence/lab-day-20261030`; make each output new and retain failures. For each run record owner/time, command, setup, physical measurements, outcome and limitations; checksum the complete root before copying.

## M1 — stereo lab map, 180 s
Slowly carry/push through overlapping textured views, complete one loop and return to the start mark; do not lift or jerk the camera. Record return offset, path/turns, start/end pose photos, duration, `capture_summary.json`, `slam.log`, bag info, `stereo.yaml`, pair counts/rates, tracking/loss/reset/map changes and kernel events.
```bash
RUN="$HOME/wbr-evidence/lab-day-20261030/M1-lab-map"
python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py "$RUN" 180
```
**M1 PASS:** capture completes and all run evidence is retained. **FAIL:** command error or missing capture/log evidence.

## L1 — stereo 3.00 m line
Tape marks exactly 3.00 m apart; move straight and slowly between them. Record actual motion interval, distance, lateral deviation, direction, mount, photos, paired infrared (IR) counts, tracking/loss/reset/map changes and kernel events. The 30 s capture is not a fixed-distance trajectory.
```bash
RUN="$HOME/wbr-evidence/lab-day-20261030/L1-3m-line"
python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py "$RUN" 30
```
**L1 PASS:** capture completes and measurements/evidence are retained. **FAIL:** command error or missing evidence.

## A1 — RGB-D 15 Hz approach + ORB-SLAM3
Use a measured ~5 cm box; mark 3.00 m from its near face; push slowly toward it and stop safely without contact. Keep three terminals. Record box size, camera height/tilt, start/stop distances from camera front plane, floor/light, motion time, photos, topic counts, pose/status and kernel events.
Terminal 1:
```bash
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
ros2 launch wbr_orb_node d435_camera.launch.py mode:=rgbd serial:=317422076650 width:=640 height:=480 fps:=15
```
Terminal 2:
```bash
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
ros2 launch wbr_orb_node d435_slam.launch.py mode:=rgbd vocabulary:=/home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt settings:=/home/richard/wbr-evidence/mobile-demo-20261024-01/setup/rgbd-ros-15fps.yaml
```
Wait for `ros2 topic echo /d435_orb/pose --once` to print a pose. Terminal 3; press Ctrl-C once after the approach:
```bash
RUN="$HOME/wbr-evidence/lab-day-20261030/A1-approach"
mkdir "$RUN"
bash /home/richard/wbr-pi-camera-day-20261021/scripts/camera_day/record.sh rgbd "$RUN/rgbd-bag"
```
**A1 PASS:** pose appears and RGB-D bag/log evidence is retained. **FAIL:** no pose, recorder error, or missing evidence.

## LIVE — camera → Pi → Nucleo + LEDs
Verify D4/PB5 green, D5/PB4 yellow, D6/PB10 red, optional D9/PC7 blue; each LED has a series resistor to GND. UART: Pi pin 8→D2, pin 10→D8, pin 6→GND; no Pi 5 V to Nucleo except documented E5V/JP5 supply arrangement. Aim at the box, fan on, hands clear; approach slowly and stop when red (or yellow for a low box) lights. LEDs are advisory only. Set ROS 2 Jazzy up in the shell first.
```bash
pkill -f "micro_ros_agent serial" || true
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
cd ~/wbr-demo-20261026
RUN="$HOME/wbr-evidence/lab-day-20261030/LIVE-chain-$(date +%Y%m%d-%H%M%S)"
RECORD=1 DURATION=60 bash lab-day-20261026/live_chain.sh "$RUN"
```
Keep `summary.json`, `packets.csv`, `camera.log`, `record.log`, camera bag and wiring/power photos. Record fan state/speed, distances, LED/decision, sent/echoed/lost counts, dropped frames, receipt-to-before-write latency, round-trip time (RTT) percentiles, rejects/stale events, port/baud and reset state. **LIVE PASS:** script completes, packets echo and expected LED response is observed; **FAIL:** script/echo/LED evidence fails. No advisory is motor control.

## P1 — live path test (last)
Run the 90 s advice-only planner test. In Foxglove use `ws://<pi-address>:8765`, fixed frame `wbr_map`, grid/markers and raw `/wbr_planner_node/suggestion`; record display, suggestions, logs and bag. The planner has no motor or serial interface.
```bash
cd ~/wbr-demo-20261026
# REQUIRED override: the script's default PLANNER_SETUP (~/wbr-demo-ws-20261024) has no wbr_planner_node.
PLANNER_SETUP=/home/richard/wbr-demo-ws-20261025/install/setup.bash \
  bash lab-day-20261025/path_live.sh "$HOME/wbr-evidence/lab-day-20261030/P1-path-test" 90
```
The 25 Oct workspace's planner source equals main and rebuilt cleanly on 30 Oct.
**P1 PASS:** script completes with bag/logs and planner suggestions retained. **FAIL:** setup, pose, planner, bag or display evidence missing.

## Stop and cleanup
```bash

# After A1, stop camera/SLAM/recorder with Ctrl-C; after LIVE/P1, scripts stop their children on exit.

# Stop the saved kernel watcher with Ctrl-C. Do not delete failed outputs.

# Restore canfix01 using the Step 0 command; keep its flash log and readback backup.
find "$HOME/wbr-evidence/lab-day-20261030" -type f -print0 | sort -z | xargs -0 sha256sum > "$HOME/wbr-evidence/lab-day-20261030.SHA256SUMS"
```
Save one run-sheet row per ID and checksum the complete evidence root before copying. Stop if image identity, camera enumeration, throttling, storage, UART, or evidence capture fails. The link bench is diagnostic only; no motor control is present.
