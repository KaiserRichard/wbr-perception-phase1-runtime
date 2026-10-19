---
name: wbr-lab-preflight
description: First 10 minutes of a WBR lab session on the Raspberry Pi 5. Use at the start of every lab day, before plugging in the camera or running any lab tool.
---

# Lab preflight

Goal: confirm the Pi, repo, power state and Python camera binding before anything
else. Camera **unplugged** for steps 1 to 3. Read `ops/lab-assistant/INSTRUCTIONS.md` first.

## Step 1 [PHYSICAL]
- Pi on the **27 W (5 A)** supply, cooler attached, Ethernet if available.
- Camera **not** plugged in yet. Only one microSD card in the Pi.

## Step 2 [PI] Identity and repo
```sh
hostname; uname -m; lsb_release -ds; uptime
cd ~/wbr-perception-phase1-runtime && git status -sb && git pull --ff-only && git log --oneline -1
```
Expect `wbr-pi5`, `aarch64`, Ubuntu 24.04. If `git status` shows local changes or
another branch, stop and ask the user; do not stash, reset or switch branches.

## Step 3 [PI] Power, temperature, disk
```sh
vcgencmd get_throttled; vcgencmd measure_temp; vcgencmd pmic_read_adc EXT5V_V
printf 'declared supply: %d mA\n' 0x$(od -An -tx1 /proc/device-tree/chosen/power/max_current | tr -d ' \n')
df -h / ; lsblk -o NAME,SIZE,MODEL,MOUNTPOINT
```
Read `get_throttled` as bits: bit 0 under-voltage now, bit 1 frequency capped now,
bit 2 throttled now, bit 3 soft temperature limit now; bits 16 to 19 are the same
events "since boot". Expect `throttled=0x0`, declared supply 5000 mA, EXT5V about
5.0 to 5.2 V (the power tool's PROPOSED floor is 4.75 V). Any non-zero bit: stop and
go to `wbr-power-check`.

## Step 4 [PI] Camera binding
```sh
source /opt/ros/jazzy/setup.bash
python3 -c "import pyrealsense2 as rs; print('pyrealsense2 OK', rs.__file__)"
```
If the import fails: card B is BLOCKED. Record the exact error for the handoff. Do
not install anything. Ask the user whether to use the C++ RAM recorder fallback.

## Step 5 [PHYSICAL then PI]
Plug the camera directly into a **blue USB3 port** with the USB3 data cable, then
run `wbr-camera-hw-check`.

## Report
Summarize: host/OS, repo commit, throttled value, temperature, EXT5V, declared
supply, free space on `/`, pyrealsense2 OK/FAIL. Label each MEASURED.
