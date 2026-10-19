---
name: wbr-camera-hw-check
description: Check the D435i camera hardware link on the Pi (USB3 speed, serial, kernel log, binding), then optionally run lab card B (lab/d435i_raw). Use after plugging in the camera or when the camera misbehaves.
---

# Camera hardware check

Read `ops/lab-assistant/INSTRUCTIONS.md` first. Power check must be clean first
(`wbr-power-check` step 2). Only one camera owner at a time: no ROS camera node
running during these steps.

## Step 1 [PHYSICAL]
Camera plugged **directly** into a blue USB3 port on the Pi with the USB3 data
cable. No hub, no USB stick or card reader on the other USB3 port.

## Step 2 [PI] USB link
```sh
lsusb | grep -i 8086:0b3a
lsusb -t
sudo dmesg | grep -i -E "usb|uvc|voltage" | tail -n 25
```
- `lsusb` must show `8086:0b3a` (Intel RealSense D435i).
- In `lsusb -t`, find the branch whose `Driver=uvcvideo` lines belong to the camera.
  That branch must say **5000M**. 480M means USB2: stop, reseat the cable, try the
  other blue port, swap the cable; one change at a time, recheck after each.
- Kernel lines with `reset`, `disconnect`, `under-voltage` or `xhci ... error` after
  plug-in: stop and report.

## Step 3 [PI] Identity
```sh
source /opt/ros/jazzy/setup.bash
python3 -c "import pyrealsense2 as rs; [print(d.get_info(rs.camera_info.name), d.get_info(rs.camera_info.serial_number), d.get_info(rs.camera_info.firmware_version), d.get_info(rs.camera_info.usb_type_descriptor)) for d in rs.context().devices]"
```
Expect `Intel RealSense D435I 317422076650 5.17.3.10 3.2`. A different serial means
a different camera: stop, its evidence does not count. If pyrealsense2 is missing,
use `rs-enumerate-devices -s` if it exists; otherwise identity is UNKNOWN.

## Step 4 [PI] Card B, raw IR + camera IMU (60 s smoke test)
Only if steps 2 and 3 are clean and the user says the camera is authorized for
capture ("CAMERA AVAILABLE"). Camera on a still, rigid surface for the whole run.
```sh
cd ~/wbr-perception-phase1-runtime
OUT=~/wbr-evidence/d435i-raw-$(date +%Y%m%d)-01
python3 lab/d435i_raw/check.py --capture --static --config lab/d435i_raw/profiles/n3_640x480_30.yaml --outdir "$OUT"; echo "exit=$?"
python3 ops/lab-assistant/show_result.py "$OUT/result.json"
```
Then ask the user to open a few `.pgm` images from both left and right IR in that
folder and describe them (scene visible? all black/white? corrupted lines?).
A clean 60 s run is a smoke test. The N2 soak is 300 s: repeat with `--seconds 300`
in a new folder only after the user reviews the 60 s result.

## Interpret
- Missing binding/device/profile = BLOCKED, not FAIL of the camera.
- `latency_policy PASS` means latency was withheld; latency stays UNKNOWN.
- Raw PASS does not qualify the ROS driver path (cards C and D, still blocked).

## Report
USB speed of the camera branch, serial, firmware, kernel messages, card B folder,
exit code, criterion table, operator notes on the images. Labels: MEASURED.
