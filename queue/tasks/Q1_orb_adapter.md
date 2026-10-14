# Q1 — native estimator adapter (component C4), dir: tools/vio_adapter/
Read queue/tasks/COMMON_QUEUE.md first. C++17 library with:
1. Engine-agnostic interface: feed stereo pair (capture epoch ns + domain, two Y8 images) and IMU samples; get an
   EstimateSnapshot {source epoch, estimator sequence, tracking state enum (STARTING, INITIALIZING, TRACKING, LOST,
   FAULT), reset counter, map/epoch id, T_world_camera (named frames), validity/reason flags, covariance availability =
   UNAVAILABLE unless the engine provides it}. A heartbeat never advances estimate sequence or source epoch.
2. Input side reuses the association logic of d435i_input.h (copy with attribution, keep its tests' intent): stereo pairing by
   exact epoch, IMU bracket checks, accel interpolated onto gyro epochs, bounded queues, rejection counters.
3. ORB-SLAM3 binding (orb_engine.cpp) compiled ONLY with -DWBR_WITH_ORBSLAM3 and ORB include/lib paths: map TrackStereo's
   returned Tcw (camera-from-world; cite include/System.h at upstream 4452a3c) to T_world_camera, GetTrackingState ->
   enum, map change/reset (MapChanged, GetLastBigChangeIdx, Atlas map id if available; cite) -> reset counter/epoch.
   Not compiled here; keep it small and reviewable.
4. Fake engine for tests with scripted init -> tracking -> loss -> reset -> new map; tests that stale epochs never escape,
   reset increments counter and invalidates, frame names are enforced.
5. euroc_replay tool (C++ or python driver) that reads the EuRoC export + times_ns.txt and feeds the adapter (fake engine on
   Mac), producing a snapshot log; run it on the real export with the fake engine to prove input association on real data
   (report counts, rejections). Makefile `test` target.
