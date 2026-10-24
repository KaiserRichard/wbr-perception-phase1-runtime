# Lab checklist — Monday, 2026-10-26

Keep camera mount, exposure/profile, power and lighting fixed. Push by hand only; no motor commands. Make a new run directory each time and retain failed runs. Pi run root: `$HOME/wbr-evidence/lab-day-20261026`.

## Before runs

- [ ] Measure camera height and down-tilt; photograph mount, wiring and scene. Tape a 3.00 m straight course and mark start/end.
- [ ] Confirm D435 serial `317422076650`, USB `5000M`, Pi supply/throttle, free space, and Nucleo UART wiring from `tools/link_bench/results/20261024-nucleo/README.md` (Pi pins 8/10/6 → D2/D8/GND; Pi 5V pin 2 → Nucleo E5V, JP5 on E5V).
- [ ] Start a saved kernel watcher in another terminal: `sudo dmesg -w | tee "$HOME/wbr-evidence/lab-day-20261026/dmesg-live.log"`.
- [ ] For stereo runs use the verified 15 Hz capture runner and settings below. Check every output path is new.

## M1 — stereo lab map, 180 s

**Owner:** carry/push slowly through the lab with overlapping textured views, one loop, and return to the start mark. Do not lift or jerk the camera.

```bash
RUN="$HOME/wbr-evidence/lab-day-20261026/M1-lab-map"
python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py "$RUN" 180
```

Record return offset, path/turns, start/end pose photos, duration, `capture_summary.json`, `slam.log`, bag info, `stereo.yaml`, camera pair counts/rates, tracking/loss/reset/map changes, and dmesg events. Keep all files on failure.

## L1 — stereo 3.00 m tape line

**Owner:** place two tape marks exactly 3.00 m apart; move straight and slowly from first to second, then stop. Keep direction and camera mount noted.

```bash
RUN="$HOME/wbr-evidence/lab-day-20261026/L1-3m-line"
python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py "$RUN" 30
```

Record measured tape distance, start/end marks, elapsed time, lateral deviation, photos, capture summary, paired IR counts, tracking/loss/reset/map changes, and dmesg. Do not treat the 30 s capture as a fixed-distance trajectory; note the actual motion interval.

## A1 — approach toward a box (RGB-D)

**Owner:** set a measured ~5 cm box on the floor; mark a 3.00 m start from its near face; slowly push straight toward it and stop at a safe distance. No contact.

Start camera in terminal 1:

```bash
source /opt/ros/jazzy/setup.bash
source /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash
ros2 launch wbr_orb_node d435_camera.launch.py mode:=rgbd serial:=317422076650 width:=640 height:=480 fps:=30
```

In terminal 2, run the verified RGB-D recorder (Ctrl-C once after the approach):

```bash
RUN="$HOME/wbr-evidence/lab-day-20261026/A1-approach"
mkdir "$RUN"
bash /home/richard/wbr-pi-camera-day-20261021/scripts/camera_day/record.sh rgbd "$RUN/rgbd-bag"
```

Record box height/width, exact start and stopping distances from camera front plane, camera height/tilt, floor/material/light, motion duration, photos, topic counts, ORB status/pose, and dmesg. Preserve full bag and logs.

## LIVE — camera + detector + UART advisory + Nucleo, fan on

**Owner:** aim camera at the same box, power the fan, and keep hands clear of blades and wiring. Use the documented UART wiring. Nucleo must run bench firmware; ROM-bootloader flash/backup procedure is `tools/link_bench/pi/stm32boot.py` and Nucleo README. Log any reboot/flash actions and preserve the existing backup; do not assume bootloader GO is needed after this VTOR fix.

1. Run the same RGB-D camera launch above and start the live obstacle node as deployed on the Pi; save `/advisory`, markers, `/d435_orb/status`, and terminal output (actual node launch syntax is not present in this worktree; use the installed lab launch command and record it verbatim).
2. Capture a fresh short RGB-D bag while the box is visible, then send that bag through detector and UART to Nucleo:

```bash
OUT="$HOME/wbr-evidence/lab-day-20261026/LIVE-uart"
python3 tools/link_bench/pi/advisory_link.py --port /dev/ttyAMA0 --out "$OUT" --bag "$HOME/wbr-evidence/lab-day-20261026/A1-approach/rgbd-bag" --rate 1.0 --stride 1
```

Record verbatim commands, fan state/speed, wiring and power photos, box distances, detector decisions, sent/echoed/lost counts, RTT percentiles, rejected echoes/stale events, UART port/baud, Nucleo reset state, and all errors. This bag replay is camera-derived detector→UART evidence; label it separately from any genuinely live camera-to-UART execution. Do not claim end-to-end live operation unless the live node itself feeds the UART bridge.

## Closeout

- [ ] Stop camera/ROS processes and kernel watcher. Do not delete failed outputs.
- [ ] Save one run-sheet row per ID with owner, time, path, configuration, physical measurements, result and limitations; checksum the complete run root before copying.
