# Bag tools

## Offline Foxglove detector demo

Create an MCAP containing the recorded color and aligned depth streams, camera
calibration and static transforms, plus the current `wbr_obstacle_node` output
recomputed for each aligned depth frame:

```sh
python tools/bag_tools/foxglove_demo.py /path/to/rgbd-bag /path/to/RUN.mcap
```

The input must be a rosbag2 SQLite directory with `metadata.yaml` and the
RealSense color/aligned-depth topics. Unknown RealSense Metadata connections are
ignored. Detector state is reset at the beginning of each bag. The output
advisory JSON deliberately contains the requested six fields only.

In Foxglove, use **File > Open local file** to open the MCAP. Import
`foxglove_demo_layout.json` from the **Layouts** menu (Import from file) to get
the color Image panel, ground-aligned detector 3D panel, and advisory Raw
Messages panel. Each depth frame adds `/tf` from `wbr_ground` to
`camera_depth_optical_frame`, and `/wbr_obstacle_node/depth_points` carries
camera-frame XYZ plus height above the fitted floor. The 3D panel uses
`wbr_ground`; recorded `/tf_static` is retained unchanged.
