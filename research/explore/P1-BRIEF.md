# P1 prototype brief: object detection on the recorded D435i data (Mac + Pi timing)

Goal: the first visible AI capability on our own data. Run a small pretrained detector (YOLO11n or YOLOv8n, exported to
ONNX, run with onnxruntime) on color frames from the 24 Oct D435i bags. Fuse each detection box with the aligned depth
to get the object's distance. Allowed files: `research/explore/p1/**` only.

Steps:
1. Read the bags with `rosbags` `Rosbag2Reader` (AnyReader fails on the RealSense metadata). Bag root:
   `~/wbr-evidence-archive/mobile-demo-20261024-01/`; see the runs B-H13, B-H05, S1-empty, W1.
2. Detection runs on the color frames. For each box, take the median aligned depth inside it, giving the object distance.
   Compare with the tape distances in `lab-day-20261024/LAB_LOG.md` (branch `claude2/20261023-worker`; use `git show`).
3. Save overlay PNGs (5–10 frames) and one short MP4/GIF under `research/explore/p1/out/` (gitignored, except 3 PNGs).
4. Timing:
   - FPS on the Mac;
   - FPS on the Pi 5 CPU over `ssh wbr-pi5`. Copy the ONNX file plus 50 frames to `~/p1-bench/` on the Pi. Use a venv there
     with onnxruntime (`~/course-stage/cn-venv` already has it). Run `nice -n 10` with 1 and 4 threads.
     Do NOT touch `/dev/ttyAMA0` or the Nucleo.
5. `research/explore/p1/README.md`: commands, results table (MEASURED), honest limits. A COCO-trained model has no "box
   on the floor" or "step" class, so say what it does or doesn't detect and what fine-tuning would need.

Build first, fix from real errors. Don't commit; the coordinator commits.
