# Ticket: D435i VIO demo helpers (Mac-only)
Do NOT ssh, use the network, install packages, commit or push. Write only under experiments/2026-10-14-d435i-demo/.
Python 3 with matplotlib/numpy may or may not be installed system-wide; if missing, use the venv at
/private/tmp/claude-501/-Users-quockaiser-Desktop-Research-wbr-perception-phase1-runtime/b0d6bb0d-3154-4534-810a-f519c739918e/scratchpad/evo-venv/bin/python (has numpy/matplotlib via evo); state which you used.

1. `plot_run.py RUN_DIR [--gt GT_TUM]`: reads ORB-SLAM3 trajectory files in EuRoC export format
   (`f_*.txt`: timestamp_ns tx ty tz qx qy qz qw; also `kf_*.txt`), and optionally `timestamps.csv` from d435i_record
   (stream,index,frame_number,sdk_ms,domain,host_steady_ns,host_utc_ns,x,y,z,exposure_us) and a power log with lines
   `UTC throttled=0x... EXT5V_V temp=..'C frequency(0)=...`. Outputs `RUN_DIR/demo_plot.png` (top view XY, side view XZ,
   path colored by time, keyframes marked, start/end markers, equal axes, meters) and `RUN_DIR/demo_stats.json`
   (duration, path length, extent, number of poses/keyframes, pose rate; if timestamps.csv: per-stream rate and max gap;
   if power log: fraction of samples with live bits 0-3 set). If --gt given, also ATE via simple SE3 Umeyama alignment
   (implement with numpy; cross-check against evo on experiments/2026-10-13-n4a-euroc-mh01/run1 vs eval/gt_data.tum:
   evo gave RMSE 0.041461 m; report your value).
2. Test it on experiments/2026-10-13-n4a-euroc-mh01/run1 (with GT) and commit nothing. Save that plot as an example.
3. `DEMO_SLIDE.md`: a one-page advisor-facing summary template (English) with placeholders for: setup, data path
   diagram in words (D435i USB3 -> librealsense -> recorder .db3 -> ORB-SLAM3 stereo-inertial -> trajectory), N4A EuRoC
   result (ATE 0.037-0.042 m over 3 runs vs ~0.036 m paper, see experiments/2026-10-13-n4a-euroc-mh01/REPORT.md),
   D435i offline and live results, and an honest "limits" box (under-voltage %, factory calibration, IMU noise assumed,
   OPEN status). Keep it short.
4. `DEBUG_GUIDE.md`: if ORB-SLAM3 on D435i fails, map log symptoms ("Not enough motion for initializing", repeated
   "Creation of new map", "Fail to track local map", no IMU initialized, timestamps backward) to likely causes and the
   one check to run for each. Cite ORB-SLAM3 source lines from third_party/ORB_SLAM3 where useful.
