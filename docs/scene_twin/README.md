# Recorded lab-day scene twin

A visual MuJoCo replay of **recorded detector packets**, with a WBR model and one
box. No dynamics, balance, jumping or controller execution. Detector measurements
are **not ground truth**. In particular, a box in `1-empty` represents a detector
false positive, not proof of a real obstacle.

Run from the repository root using the existing simulation environment:

```sh
VENV=~/Desktop/Research/wbr-lab-ops/.venv
RUN=~/wbr-evidence-archive/lab-day-20261025/4-approach
"$VENV/bin/mjpython" -m tools.scene_twin.view --run "$RUN" --speed 1.0
"$VENV/bin/python" -m tools.scene_twin.view --run "$RUN" --record /tmp/approach-twin --fps 10
python3 .github/run_unittest.py tools/scene_twin
```

Window mode requires `mjpython` on macOS. Headless recording uses plain Python
and still needs access to macOS CoreGraphics/OpenGL. Dependencies: MuJoCo, NumPy,
Pillow (already in that venv). Pure replay tests need only the standard library.
The recorder requires a new/empty output directory and writes all PNGs,
`frames.csv` and `scene_twin.gif`. It retains frame times while reducing GIF
spatial resolution if needed to keep the GIF below 3 MB (ASSUMED delivery limit).
`--fps` defaults to 10, `--speed` to 1 (ASSUMED presentation settings). At speed 2,
recording covers twice as much source time per playback second. GIF delay is
rounded to its centisecond resolution. A sampled render holds the most recent
packet; its overlay gives that packet's exact stamp. The endpoint can be shorter
than one render interval. PNGs preserve full render resolution; GIFs may shrink.

## Geometry and trajectory

Every source number has a status:

| Quantity | Value/source | Status |
|---|---|---|
| Advisory, height, distance, frame stamp | `packets.csv`, original live output | MEASURED detector output, not physical truth |
| Box height | Median of positive finite heights with advisory JUMP or STOP | INFERRED from MEASURED detector data |
| Box depth / width | 0.20 / 0.40 m | ASSUMED drawing geometry |
| Camera centre | x=+0.15 m, y=0, z=+0.15 m from axle | ASSUMED front-top of body; mounting/calibration unknown |
| Standing virtual leg | 0.12 m | ASSUMED inherited viewer pose |
| Pitch / roll / yaw | All zero | ASSUMED; **no IMU in these runs**, no pose estimate |
| Box face x | First valid distance + camera x offset | INFERRED coordinate anchor |
| Robot x | Box face minus smoothed distance minus camera x offset | INFERRED visual trajectory |
| Median window | Trailing three valid observations | ASSUMED smoothing choice; advisory is never smoothed |
| Missing height / all-missing distance | 0.01 / 1.0 m | ASSUMED placeholders, not measurements |
| Wheel radius and inherited robot geometry | Generator / [viewer parameter table](../../tools/imu_view/README.md#model-parameters) | SOURCE-SUPPORTED, ASSUMED or INFERRED as labelled there |
| Palette, viewpoint, image dimensions, frame rate | Code defaults | ASSUMED presentation only |

The front face is the **negative-x** face of the box. The chosen reference frame
is the first packet with positive finite distance; robot axle x is zero there,
so camera-to-face gap equals that packet's raw distance exactly. Invalid distance
(zero, negative, NaN or infinity) holds the last smoothed value without updating
the median history. Before any valid distance, the initial value is backfilled
from the first valid packet (ASSUMED); if none exists, use the labelled fallback.

`--motion auto` treats directory names starting with `4-approach` as moving and
other names as static (ASSUMED classification from run labels). Override using
`--motion static` or `--motion approach`. Static runs hold x=0 despite detector
jitter: raw distance remains in the overlay, and displayed camera gap stays at
the anchor. In approach mode the trailing median removes brief distance spikes
but introduces sample-dependent lag. It is not odometry or reconstructed camera
motion; detection switching can produce misleading motion. The wheels are at
the inherited wheel radius above the plane, so both tyres touch z=0. The box
centre z is half its height, so its bottom is exactly on that plane.

The original generator is called in memory. Ghost robots, reference post and
IMU drawings are removed from the copied XML; input files remain untouched.
The visible camera is a marker at the ASSUMED centre, not a calibrated sensor.
Wheels do not articulate or spin. Blue = JUMP_CANDIDATE, red = STOP_CANDIDATE,
green = NONE, grey = UNCERTAIN (ASSUMED display colours). Advisory flicker is
preserved from live packets. This does **not** replay the separately recomputed
old/new streams in the archive's `foxglove/FLICKER_REPORT.md`.

## Side by side with Foxglove

1. Open `<run>/camera-bag/*.mcap` locally in Foxglove and add an Image panel for
   `/camera/camera/color/image_raw`. The existing
   [bag tools](../../tools/bag_tools/README.md) describe the separate detector
   export/layout; an exported MCAP may have a different start time.
2. Launch this viewer with the same run at `--speed 1.0`, alongside Foxglove at
   playback speed 1.0 (ASSUMED manual comparison settings).
3. `t` is relative to the **first packet stamp**, not bag start. `bag-relative`
   is `(frame_stamp_ns - metadata.starting_time.nanoseconds_since_epoch)/1e9`.
   This origin is MEASURED bag **log time**. Negative values mean the packet
   precedes the bag. Such frames cannot be found in that bag.
4. Pause Foxglove and seek to the displayed bag-relative time as an approximate
   location. For exact matching, inspect the camera message `header.stamp` and
   compare `sec*1_000_000_000 + nanosec` to the full `frame_stamp_ns` overlay.
   Header time and rosbag receipt/log time differ: the displayed relative time
   is **not a claim of exact log-timeline alignment**. An exact header stamp
   might be absent because the bag or packet stream started late/dropped frames.
5. For repeatable comparisons, record PNGs and use `frames.csv` to select a
   frame/stamp, then seek the corresponding camera header stamp in Foxglove.
   There is no shared playback clock or automatic synchronisation; independent
   window playback may drift. Live window playback ends at the last packet.

If metadata is missing, the overlay explicitly says
`ASSUMED origin (bag UNKNOWN)`: its relative time is first-packet-relative only.
On this archive copy `1-empty` has no `camera-bag` directory and
`4-approach-r3` has no readable bag metadata; exact Foxglove alignment for these
runs remains unavailable. A missing origin is never silently called bag time.
The optional `/scene_twin/image` MCAP export is not implemented.

## Evidence and current limitations

See [run receipt](RUN_RECEIPT.md) and
[results status](../../tools/scene_twin/results/README.md).
The restricted worker session compiled and updated every recorded pose but could
not obtain a CoreGraphics rendering context. **No GIF/PNG evidence was produced
or visually inspected.** Window UI and the GIF size reduction path remain
unverified on an unrestricted graphical session. Numerical floor contact checks
are not a substitute for the requested visual inspection.
