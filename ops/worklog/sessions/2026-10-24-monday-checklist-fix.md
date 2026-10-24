# 2026-10-24 evening — Monday checklist fix (Claude 2, owner request)

For any later session (Claude 1, the other Claude 2, ChatGPT): `lab-day-20261026/CHECKLIST.md` changed.

- A1 camera at `fps:=15` (was 30). Reason, MEASURED 2026-10-24: microSD sustained write 56.3 MB/s
  (1 GB `dd` with fsync); RGB-D colour + raw depth + aligned depth = 32 MB/s at 15 Hz, 64 MB/s at 30 Hz.
  All 24 Oct RGB-D runs used 15 Hz.
- A1 now starts ORB-SLAM3 RGB-D (`d435_slam.launch.py mode:=rgbd`) with
  `~/wbr-evidence/mobile-demo-20261024-01/setup/rgbd-ros-15fps.yaml` (copy of the 21 Oct
  `rgbd-ros.yaml` with `Camera.fps` 30 -> 15), so the bag records `/d435_orb/pose` and `/status`
  for the local map. `record.sh rgbd` already records those topics.
- Kernel watcher: `journalctl -kf` (works without sudo on this Pi) instead of `sudo dmesg -w`.
- Not changed: M1, L1, LIVE, `live_chain.sh` (already 15 Hz).
