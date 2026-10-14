# D435i stereo-inertial VIO — advisor demo

**Status: OPEN · Date: [date] · Question: can the Pi sustain a continuous, credible VIO trajectory?**

**Setup:** D435i [SDK serial; separate ASIC/firmware/USB IDs] · Pi 5 [RAM] ·
[OS / librealsense / ORB-SLAM3 revisions] · USB3 [measured ≥5000M] ·
[supply / cooling / qualified storage] · [raw stereo + IMU profiles].

**Data path:** D435i USB3 → librealsense → recorder `.db3` + `timestamps.csv`
→ ORB-SLAM3 stereo-inertial → body/IMU trajectory → Mac plot + diagnostics.
Capture stays local to the Pi; offline and live execution are separate results.

| Evidence | Result to show |
|---|---|
| N4A: EuRoC MH01, three Pi runs | SE3 ATE RMSE **0.037–0.042 m**, mean 0.040 m; one map each. Paper comparator ≈0.036 m, quoted by the local report and **not independently verified**. [Report](../2026-10-13-n4a-euroc-mh01/REPORT.md). |
| D435i offline replay | [take/hash, duration, poses/keyframes, IMU init, map resets, trajectory figure, GT source + ATE if available; otherwise “no GT”]. **OPEN / unmeasured** until evidence exists. |
| D435i live | [take/hash, tracking continuity, measured wall-clock rate/latency, CPU/RSS, power health]. **OPEN / unmeasured** until evidence exists. |

> **Limits:** N4A live under-voltage/throttling: **87/178 samples (48.9%)**;
> timing is invalid as a platform measurement. D435i under-voltage: [bit-0 %,
> sample count, window]; any live bit 0–3: [%]. Factory calibration is retained,
> not experimentally qualified; IMU noise is assumed, not measured. No D435i
> accuracy claim without GT. **OPEN**: N1 → N2 (mandatory 300 s soak) → N3,
> calibration, offline replay and live qualification. This Mac helper proves
> tooling only; camera execution requires explicit `CAMERA AVAILABLE`.

**Next evidence:** [stable power + gate receipts] → [offline D435i replay] →
[live result with honest limitations]. Example: [N4A run1 plot](example_run1/demo_plot.png).
