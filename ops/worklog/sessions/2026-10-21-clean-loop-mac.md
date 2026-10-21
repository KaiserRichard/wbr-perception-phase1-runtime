# Three clean-loop stereo replays on Mac — 2026-10-21

- PPO gate at05:28UTC: supervisor EXITED0 at05:13:27, batch COMPLETE, no workers.
  Rechecked after the follow-up interruption. No control/PPO changes or Pi access.
- Feature branch chatgpt/20261021-clean-loop-replays updated to main162f841;
  unrelated untracked fuzz/build outputs preserved. Tool commit da905cd.
- Intel Mac / Ubuntu22.04 x86_64 Docker,4CPU/5GiB. Archive:
  ~/wbr-evidence-archive/camera-recording-20261021-01/clean-loop-mac-01.
- Built pinned ORB4452a3c/Pangolin7364b59, GCC11/OpenCV4.5.4. Actual errors fixed:
  Pi-local727f3cbd not upstream; C++17 bool++→int; explicit g2o build; cached
  runner source path restored to /repo; Rectified diagnostic skipped nonexistent
  camera2. Full compatibility diff retained; differs from accepted Pi binary.
- Extraction01 failed final receipt (Python3.10 hash API),02 partial shared-file
  read. Streaming SHA/frozen tools/new exclusive03 succeeded:2215equal headers,
  original MCAP SHA5749908b…97703c8, every PNG round-tripped to original pixels.
- Build03 startup SIGSEGV happened before any Track call; retained empty failed
  batch. Repaired build05 exit0. Exactly3successful runs in three-replays-02,
  new process/System/atlas each, viewer=false, original timestamps paced1×.
- Runs06:05:28–06:13:12UTC; all exit0,all2215pairs processed,zero input/application
  drops. Tracked2215/2215/2152; loss transitions0/0/2; reset markers0/0/0;
  new maps afterinitial0/0/1; merges0/0/1; loop detectionno/yes/no.
- Endpointm0.018319/0.005408/0.006263; pathm14.267/14.322/15.997;
  percent0.128/0.038/0.039. R3 maximum online pose step1.115m: no accuracy claim.
- Paced trackedFPS15.005/15.004/14.578 from147.62s steady spans;
  Track-compute quotients43.056/29.773/39.149FPS, not maximum capacity tests.
  Source interval rate14.9993Hz; loading/shutdown excluded from steady spans.
- CPU114.9/154.0/121.1% (one core=100); sampled peakRSS589.6/593.1/599.2MiB.
  Per-call timings, exact commands/exits, all poses/map events/stdout preserved.
- Native compile/link,18metric tests,4MCAP fixture tests PASS. Independent copied
  evidence checks PASS: every header/attempt/completion, counters, pose stamps,
  finite values, full boundaries, recomputed endpoint/path/FPS and original hash.
- Review2026-10-21-clean-loop-mac.md; REPORT.md/commands.md/analysis/validation/
  source tar/native binaries/provenance/failed logs archived. Current-head CI
  must pass before merge; final publication and retirement receipts go outside git.
