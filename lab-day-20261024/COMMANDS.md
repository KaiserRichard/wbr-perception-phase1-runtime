# Commands per run — 2026-10-24 (verified by Claude 2 at 08:50)

Run on the Pi in a Mac terminal: `ssh wbr-pi5-wifi` (Wi-Fi, 192.168.0.101).
Power: the 27 W wall supply (+ extension cord). Never the 900 mA power bank.
Each command records, stops by itself and prints topic counts + `throttled=`.
Use each RUN_ID once; the script refuses to overwrite.

Terminal 1 (keep open all session; kernel log for USB disconnects):

```bash
journalctl -kf | tee ~/wbr-evidence/mobile-demo-20261024-01/kernel-live.log
```

Terminal 2, RGB-D runs (`rgbd_run.sh RUN_ID SECONDS [live]`):

| Run | Command |
|---|---|
| LIVE | `bash ~/wbr-evidence/mobile-demo-20261024-01/setup/rgbd_run.sh LIVE 60 live` |
| S1 | `bash ~/wbr-evidence/mobile-demo-20261024-01/setup/rgbd_run.sh S1 10` |
| W1 | `bash ~/wbr-evidence/mobile-demo-20261024-01/setup/rgbd_run.sh W1 5` |
| B-H05 | `bash ~/wbr-evidence/mobile-demo-20261024-01/setup/rgbd_run.sh B-H05 5` |
| B-H12 | `bash ~/wbr-evidence/mobile-demo-20261024-01/setup/rgbd_run.sh B-H12 5` |
| B-H20 | `bash ~/wbr-evidence/mobile-demo-20261024-01/setup/rgbd_run.sh B-H20 5` |
| A1 | `bash ~/wbr-evidence/mobile-demo-20261024-01/setup/rgbd_run.sh A1 20` |

LIVE on the Mac: open Foxglove → Open connection → Foxglove WebSocket →
`ws://wbr-pi5.local:8765`. Add panels: 3D (topic `/wbr_obstacle_node/markers`),
Raw Messages (`/wbr_obstacle_node/advisory`), Image
(`/camera/camera/color/image_raw`). The node runs at about 7 Hz.

Terminal 2, stereo runs (ORB-SLAM3 runs live; first source the environment):

```bash
source ~/wbr-evidence/mobile-demo-20261024-01/setup/env.sh
```

| Run | Command |
|---|---|
| M1 | `python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py $R/M1 180` |
| L1 | `python3 /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py $R/L1 45` |

The stereo runner waits for a first ORB pose before recording. If it prints
"no tracked pose before recording", point the camera at a textured scene and
rerun with a new RUN_ID (e.g. M1b).

Smoke tests already done (keep, do not delete): T0-stereo-smoke (150/150 per
stream, ORB map 255 points), T1-rgbd-smoke, T2-live-smoke (node crashed, fixed),
T3-live-smoke (72 advisories in 10 s).
