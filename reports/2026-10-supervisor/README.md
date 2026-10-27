# Supervisor progress report

Vietnamese progress report; discussion and editing notes are in English.

Build in this directory:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

The editable document is `main.tex`; its compiled eight-page output is `main.pdf`.
All figures are local in `figures/`. The revision adds no LaTeX packages.

## Evidence and scope

- Owner confirmed D435i on 2026-10-27. The report date remains 26/10/2026.
  The original dense-map image's D435 label is retained and explained in its caption.
- Results retain bench/offline/replay scope; they do not validate deployment on WBR.
- EuRoC is the recorded stereo-inertial experiment using dataset IMU data.
  `3,639` denotes matched pose/reference samples, not stereo image pairs.
  See `tools/eval_pipeline/accuracy/validation/run*/rpe_1m/result.json` and
  `experiments/2026-10-13-n4a-euroc-mh01/REPORT.md` in the runtime checkout.
- The height/distance plots contain all recorded box cases, including the
  B-H05-D1p3 clustering failure. The six-run corrected-error summary is a subset.
  See `tools/obstacle_decision/results/lab-20261024/README.md`, `evaluation.md`
  and `run_sheet_used.csv`.
- Dense-map 225 frames / 354,244 points and 5.76 mm plane-fit RMS refer to the
  growing-map output, not the earlier dense-map variant. A 1 cm voxel parameter
  is not an absolute accuracy measurement.
- UART 139/139 is obstacle recording B-H08; the synthetic round-trip times and
  later micro-ROS acknowledgement counts are distinct tests.
- All original photo/video/date and CAN/IMU placeholders remain, relocated where
  necessary. No experimental or source-result figures were edited.

## External illustration attribution

`figures/visual-slam-reference.png` is **Visual SLAM ORB-SLAM2** by **Alejandro
Silvestri**, downloaded unmodified from Wikimedia Commons. It illustrates camera
input and sparse-map output only; it is not ORB-SLAM3 experiment evidence or a
comparison of algorithms.

- Source and author: https://commons.wikimedia.org/wiki/File:Visual_SLAM_ORB-SLAM2.png
- Original file: https://upload.wikimedia.org/wikipedia/commons/3/38/Visual_SLAM_ORB-SLAM2.png
- License: Creative Commons Attribution-ShareAlike 4.0 International,
  https://creativecommons.org/licenses/by-sa/4.0/
- Accessed: 2026-10-27. No cropping, recolouring or image-content changes.

The report retains its original ORB-SLAM3 paper and Intel D400 datasheet citations;
the Commons attribution is the new illustration source.
