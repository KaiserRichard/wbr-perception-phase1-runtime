# Offline replay queue and Claude follow-ups

2026-10-21. The owner chose to wait for PPO v2; no new replay result is claimed.

- An active thread follow-up checks completion every15minutes. It requires an
  EXITED supervisor, a terminal batch report and no remaining batch workers.
  The camera bag/settings are already on the Mac; Pi use needs new owner consent.
- The new bag has2215equal stereo headers. Three fresh headless visual runs are
  queued, with endpointm/%path, resets/maps/merges, loss transitions and tracked
  FPS measured on a steady clock. No heavy runtime setup starts before PPO ends.
- Docker is available on this Intel Mac; ORB/ROS replay runtime is not yet built.
  Provision/debug it after the wait condition clears, then preserve inputs,
  exact sources/settings/commands, per-frame timing, trajectories and raw logs.
- Queue: `~/wbr-evidence-archive/camera-recording-20261021-01/queued-clean-loop-replays.json`.
  Follow-up id: `wbr-perception-clean-loop-after-ppo`.

## IMU clipping check

Re-read15132raw accelerometer samples. The largest vector norm was44.69m/s²,
which is not itself a per-axis clipping test. Axis extrema (m/s²):

| Axis | Minimum | Maximum |
|---|---:|---:|
| x | -21.8002 | 18.1717 |
| y | -39.2266 | 24.9775 |
| z | -31.9108 | 24.8402 |

The y sample at1792552319.77441s equals the float32 representation of -4g.
No near-rail repeated-value plateau was found. The D435i/BMI085 specification
lists ±4g per axis ([D400 datasheet, table4-24](https://www.realsenseai.com/wp-content/uploads/2022/04/Intel-RealSense-D400-Series-Datasheet-April-2022-v2.pdf#page=91)).
One rail hit is consistent with a brief saturation event, not proof; an isolated
sample and the absence of a plateau cannot prove clipping absent or present.
Input hash, extrema and hit index are in archived `imu-clipping-check.json`.

## Small code/documentation follow-ups

- Corrected the stale claim that upstream acceleration hold behaviour remained.
- Restored the upstream IMU-only offset (milliseconds, default0); recorded accepted
  data used0, so these edits do not change those historical timestamps/results.
- Callback timestamp faults now set an atomic flag and wake the main loop. The
  main thread reports/stops the run; a post-SDK-stop check catches late faults.
- Real-source patch tests passed. Native recompilation and fault injection are
  explicitly deferred until the runtime can be built after PPO finishes.

## Recommendation
Keep the accepted single-run claims unchanged. Treat the isolated rail hit as
possible clipping. Complete the three queued visual replays before interpreting
new-loop repeatability; endpoint values remain internal consistency, not accuracy.
