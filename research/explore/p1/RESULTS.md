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
