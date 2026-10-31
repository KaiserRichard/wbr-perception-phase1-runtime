# P1 results (2026-10-30, run outside the sandbox)

Model: YOLO11n COCO, ONNX opset 12, 640x640, sha256 71325a29...c1c9. ONNX Runtime CPU provider. Raw outputs are in `results/`.

| Platform | Measure | FPS | Status |
|---|---|---:|---|
| Mac (Intel), 4 bags, 391 paired frames | model only | 22.4 | MEASURED |
| Mac | pipeline (preproc + infer + NMS + box-depth median) | 18.8 | MEASURED |
| Mac, 50-frame bench | inference only | 17.0 | MEASURED |
| Pi 5, 1 thread, 500 inferences | inference only | 2.43 | MEASURED, throttled=0x0 |
| Pi 5, 4 threads, 500 inferences | inference only | 3.43 | MEASURED, throttled=0x0, 56.5 C |

What the detector sees: the stable lab furniture (chair, tv, laptop, dining table, cup) in every frame. Each frame has about three detections, and the overlays confirm the boxes are real objects.
It found **zero `book` detections in B-H05**, even though the books are clearly visible at 1.00 m (`results/overlay-B-H05-0000.png`). So the planned book-depth versus tape comparison has no data. As expected, the boxes, steps and wall are not COCO classes.

Implications (INFERRED): at 640 px, YOLO11n on the Pi CPU (3.4 FPS) is too slow to run alongside ORB-SLAM3 on the Pi. To go faster, the options are a smaller input (320 px), int8 quantization, an accelerator (X1 question), or offload. The obstacle use case needs either a fine-tuned hazard label set or the existing depth-geometry path, not COCO classes.

## Live Pi Camera v2 (2026-10-31)

`live_cam.py` reads I420 frames from `rpicam-vid` (Raspberry Pi libcamera built into `/opt/rpi-cam`; Ubuntu 24.04 has no Picamera2). Settings: 1280×720 capture, letterboxed to 640, same YOLO11n ONNX (sha256 71325a29…c1c9), 5 warm-up + 100 measured frames, CPU governor switched to `performance` for the runs and then restored to `ondemand`. Raw JSON and two overlays are in `results/live/`.

| Threads | Capture (ms, mean) | Infer + NMS FPS | End-to-end FPS | Throttled | Status |
|---:|---:|---:|---:|---|---|
| 1 | 4.1 | 2.43 | 2.40 | 0x0 | MEASURED |
| 4 | 4.1 | 3.44 | 3.38 | 0x0 | MEASURED |

The live numbers match the 30 Oct frame bench (2.43 / 3.43), so camera capture adds almost nothing; inference is the bottleneck.
**Scene caveat:** the camera was facing a dark, out-of-focus surface. The only detections were `keyboard` at ~0.27 (12–16 boxes in 100 frames), which are likely false positives, so these overlays say nothing about detection quality. Re-aim the camera at a lit scene before taking demo overlays. The Pi Camera v2 has no depth; distance fusion stays on the D435i bag path (`run_p1.py`, Mac pipeline 18.8 FPS above).

Command (on the Pi): `. /opt/rpi-cam/env.sh && ~/p1-live/.venv/bin/python live_cam.py --model ~/p1-bench/yolo11n.onnx --threads 4 --frames 100`
