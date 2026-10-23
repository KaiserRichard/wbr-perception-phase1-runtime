# Box-ahead obstacle estimate and jump advisory

Offline NumPy prototype for estimating box geometry from a depth frame and
filtering it into an informational STM32 advisory. **The Pi does not grant jump
permission.** Balance, jumping, actuation, and safety remain entirely owned by
the STM32. There is no transport, ROS node, camera access, or hardware action.

`detect.process_frame(depth_m, K, params, state)` fits the floor with the
existing `tools/ground_plane/plane.py`, constrained to a camera-facing normal
within 30°; it reuses the last plane for up to three frames when a fit fails.
Optical-frame `(x right, y down, z forward)` maps to ground coordinates
`(forward=z, lateral=−x, up=n·p+d)`. A 2 cm grid and connected components
produce front-face distance, 95th-percentile height, lateral width, depth
extent, and point count. ASSUMED defaults include 0.25 m corridor half-width,
0.02 m minimum obstacle height, and 0.3–3.0 m range.

`decide.update` applies a 3-of-5 temporal confirmation, EMA geometry, and a
two-frame clearing hysteresis. Jump height limits are ASSUMED at 0.03–0.12 m;
taller confirmed objects produce STOP_CANDIDATE. Invalid plane near a tracked
obstacle also produces STOP_CANDIDATE; otherwise plane failure is UNCERTAIN.
Optional forward speed yields distance/speed time-to-contact.

`advisory_codec.py` is a PROPOSED type-4 message using the existing COBS and
CRC-32C framing. See [ADVISORY_SPEC.md](ADVISORY_SPEC.md). Firmware owner review
is required before any firmware use.

## Run

From the repository root:

```sh
~/Desktop/Research/wbr-venvs/perception/bin/python -m unittest discover -s tools/obstacle_decision/tests -v
MPLCONFIGDIR=/private/tmp/wbr-mpl-cache MPLBACKEND=Agg ~/Desktop/Research/wbr-venvs/perception/bin/python tools/obstacle_decision/evaluate.py
```

Evaluation writes `results/metrics.json`, `results/height_error.png`, and
`results/confusion.png`. The sweep uses 80 deterministic synthetic boxes:
heights 0.03/0.05/0.08/0.12/0.20 m, front distances 0.5/1.0/1.5/2.0 m,
camera pitch 0°/3°, disparity noise sigma 0.1 px and two seeds. Camera height
0.30 m is ASSUMED. Empty-floor and out-of-corridor controls are included.

## Limits

Synthetic renderer only; no real-box validation, no RealSense camera validation,
no ROS integration, no Pi timing or transport. Corridor and decision thresholds
are assumptions, not robot clearance/jump capabilities. Synthetic geometry
does not model reflective surfaces, multipath, motion distortion, camera
extrinsic error, floor irregularity, or real depth holes. Advisory names are
candidates only and must never be interpreted as permission to jump.
