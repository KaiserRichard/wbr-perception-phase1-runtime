# Q3 — repeatable run harness (component C8), dir: tools/run_harness/
Read queue/tasks/COMMON_QUEUE.md first. Python CLI that, given a run spec YAML (engine binary + args template, vocabulary,
settings yaml, EuRoC dataset dir, times file, repeats N, optional ground truth), runs the engine N times headless,
captures stdout/stderr, wall time, exit code, trajectory files, and writes a run receipt per repeat: input hashes (dataset
manifest, settings, binary), git rev, host info, timestamps (UTC + monotonic), status (OK / CRASH / NO_TRAJECTORY / TIMEOUT).
Then: convert trajectory to base_link via tools/frames when a mount is given, compute ATE/RPE via
tools/trajectory_eval when ground truth exists, else reference-free continuity metrics (path length, jumps > threshold,
reset/segment count, tracking-state counts parsed from ORB logs: "IMU initialized", "Reseting", "Fail to track", map count).
Failed runs stay in the denominator. Tests use a fake engine script that writes scripted trajectories/logs (success,
crash, partial, reset). Provide example spec for ORB-SLAM3 stereo_inertial_euroc on the Pi (paths marked TO-FILL).
