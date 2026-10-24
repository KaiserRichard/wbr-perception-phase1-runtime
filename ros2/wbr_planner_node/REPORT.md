# Planner implementation report

## Commands and results

Host validation (Mac has no ROS 2 installation):

```text
~/Desktop/Research/wbr-venvs/perception/bin/python -m unittest discover -s ros2/wbr_planner_node/test -v
Ran 4 tests in 3.019s
OK
box sequence core runtime ms/frame: mean=109.68, max=127.22
clear sequence core runtime ms/frame: mean=118.72, max=136.76
```

The test renderer provides a 15 cm box on the 1.5 m line, clear-floor sequence,
missing pose, >1 m/s pose jump, and no-floor frame. In the box case the chosen
lateral shift is at least 0.30 m; the clear case returns `GO_STRAIGHT`. Shell syntax validation: `bash -n lab-day-20261025/path_live.sh` passed; Python
syntax compilation passed for core, ROS adapter, launch file, and setup file.

The core uses only NumPy and repository modules `tools/ground_plane/plane.py`
and `tools/local_map/{fuse,grid}.py`. Runtime imports in those files do not
require SciPy, OpenCV, or Matplotlib. Bag replay utility dependencies do not
enter the live path. Host timing is a Mac measurement, not a Pi performance
claim.

## Limitations

- Pi build, CPU load with ORB-SLAM3, live synchronization and Foxglove display
  have not been tested; ROS 2 is absent on this Mac.
- The planner searches straight parallel corridors with one fixed 3 m goal.
  It does not generate a dynamically feasible curve or optimize speed.
- Dynamic obstacles and uncertainty-aware obstacle tracking are not modeled;
  the elevation grid accumulates observed cells.
- Gravity alignment depends on seeing enough floor in the first valid frame.
  ORB-SLAM3 loop closure/reset can alter `slam_world`; frame continuity is not
  handled across map resets.
- A no-pose frame yields `NO_POSE` and is not fused. The ROS adapter publishes
  that advisory but map outputs require an initialized plane.
