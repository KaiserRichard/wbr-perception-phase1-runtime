# Clean-loop replay queue and review follow-ups — 2026-10-21

- Owner relayed Claude acceptance mergedPR88, then chose to keep AGENTS.md:
  no SLAM replay/heavy build on the Mac while PPO v2 trains. Pi use requires
  a fresh explicit owner statement that it is free. No AGENTS.md change.
- Branch chatgpt/20261021-clean-loop-replays from origin/main9a5bbae; existing
  untracked fuzz/build outputs preserved. No control source/environment changes.
- Actual setup: Intel x86_64 Mac, Docker available (16vCPU/8GiB VM), no ROS/ORB
  Mac replay runtime prepared yet. PPO supervisor75443 and eight workers active.
  Read-only setup inspection only; no replay, conversion or heavy build started.
- Created active15-minute thread follow-up wbr-perception-clean-loop-after-ppo.
  Start condition: supervisor receipt EXITED, final archive status COMPLETE or
  COMPLETE_WITH_FAILURES, no remaining batch training/evaluation workers.
  Missing PID or individual-seed completion is insufficient; unexplained death
  is a blocker, not permission. Existing control completion monitor untouched.
- Durable receipt: ~/wbr-evidence-archive/camera-recording-20261021-01/
  queued-clean-loop-replays.json, statusWAITING_FOR_PPO_V2. Input new MCAP SHA
  5749908bb94a6c9a7e5496f3c8b58db3596cf5f53f2542502a1468dcd97703c8;
  2215matched pairs; original stereo.yaml. Three fresh headless estimators,
  same input/config, source timestamps preserved, exclusive outside-git outputs.
- Each replay must report endpointm/%estimatedpath, resets/newmaps/merges,
  loss transitions, tracked/processed counts, measured steady-clock trackedFPS.
  Distinguish compute timing/paced throughput/source rate; no substituted15Hz or
  old lossy-loop endpoints. Mac platform is not Pi; no accuracy/groundtruth claim.
- Raw accel follow-up:15132samples; per-axis extrema x[-21.8002,18.1717],
  y[-39.2266,24.9775],z[-31.9108,24.8402]m/s². Exactly one y sample at nominal
  -4g (source1792552319.77441s); no consecutive near-rail flat top. Brief clipping
  remains plausible, not proven. JSON/hash/neighbor data in imu-clipping-check.json.
- Updated stale native README; restored the zero-default IMU-only offset term;
  explicit timestamp fault in SDK callback now flags/wakes the main loop, which
  handles the error. Recheck after SDK stop avoids late-fault success. Native
  recompilation/fault injection deferred under the PPO rule; patch tests run now.
- No camera/Pi access, new experiments, deletion or simulation/training changes.
