# Lab work on the Pi

Build first, fix when it breaks. See `AGENTS.md` for the general flow.

## Setup facts
- Pi 5, Ubuntu 24.04, ROS 2 Jazzy, user `richard`. SSH: `ssh wbr-pi5`
  (direct Ethernet, Pi at 192.168.50.2). Repo on the Pi:
  `~/wbr-perception-phase1-runtime`. ORB-SLAM3: `~/orbslam3/ORB_SLAM3`.
- Camera: RealSense D435 (no IMU), SDK serial 048622071151. Plug it into a blue
  USB3 port. Power: the 27 W supply.
- Root disk is the 32 GB microSD with ~6 GB free; the 128 GB card migration is in
  `skills/wbr-storage-migrate` when more space is needed.

## How to work
- Do the real task directly (e.g. run ORB-SLAM3). Install missing packages as needed.
- If it fails, read the error and fix that. Typical quick checks only when the error
  points there: `lsusb -t` (camera should be 5000M), `vcgencmd get_throttled`
  (0x0 is good), `dmesg | tail`.
- Run commands yourself over SSH when you can; ask the owner only for physical
  actions (plug, unplug, move the camera, power).
- Keep the old `lab/` qualification tools for later if useful; they are not
  prerequisites.

## Always ask first (owner types `CONFIRM <action> <target>`)
- `dd`, formatting, partitioning, deleting data.

## Skills
- `skills/wbr-orbslam3-bringup`: camera + ORB-SLAM3 running on the Pi.
- `skills/wbr-storage-migrate`: move the system to the 128 GB card.
- `skills/wbr-evidence-copy`: copy a run folder to the Mac with checksums.
