# Camera and MuJoCo twin on one Foxglove timeline

The [layout](layout.json) places the recorded D435 color image on the left and
the rendered MuJoCo pose on the right, with raw/gated advisory and gate phase
below the twin. Both MCAP files use one Foxglove playback and seek control.
The camera recording stays unchanged; the converter only reads rendered inputs.

## Render, then convert

Run these commands from this worktree's repository root. Rendering is a
**conductor command**, outside the worker sandbox, with access to macOS graphics.
Use the existing environment; no installation or network is needed.

```sh
PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
SOURCE=~/wbr-evidence-archive/lab-day-20261025/3-box13
EXPORT=~/wbr-evidence-archive/foxglove-twin-20261030-01

"$PYTHON" -m tools.jump_gate.demo \
  --packets "$SOURCE/packets.csv" \
  --record "$EXPORT/jump-render" --fps 10 --jump-at 20

"$PYTHON" -m tools.foxglove_twin.to_mcap \
  "$EXPORT/jump-render" "$EXPORT/twin.mcap" --fps 10
```

The render directory must be new or empty. The converter requires a new output
file and refuses to overwrite an existing one. Its optional output argument
defaults to `~/wbr-evidence-archive/foxglove-twin-20261030-01/twin.mcap`.
It creates output parents as needed and rejects outputs inside the render input
directory or the source `lab-day-20261025` archive. Keep new outputs in the
separate export directory above. A failed conversion can leave a partial output;
use a fresh filename when retrying rather than treating it as a completed MCAP.

The converter detects either `timeline.csv` or `frames.csv`. Exactly one must
exist. For jump recordings, **pass the same `--fps` to render and convert**.
The default is 10 in both commands. The jump recorder exports a CSV row for each
gate tick, while PNGs sample those ticks at the render rate. The converter uses
`min(frame_index / fps, last_tick_time)` and the last tick at or before that
time, matching
[demo.record](../../tools/jump_gate/demo.py) and
[Timeline.at](../../tools/jump_gate/timeline.py). It checks the contiguous
five-digit PNG names and expected frame count. FPS is not stored in this CSV;
the count check cannot distinguish every possible incorrect FPS.

For the scene-only replay, these are the alternative conductor commands:

```sh
"$PYTHON" -m tools.scene_twin.view \
  --run "$SOURCE" --record "$EXPORT/scene-render" --fps 10 --speed 1
"$PYTHON" -m tools.foxglove_twin.to_mcap \
  "$EXPORT/scene-render" "$EXPORT/scene-twin.mcap"
```

`frames.csv` explicitly names each PNG and its source stamp, so conversion needs
no FPS or speed argument. This CSV has no raw/gated advisory, reason, confidence
or gate phase: these advisory fields export as JSON `null`, and phase is
`UNKNOWN`. Use the jump recording for the full advisory and phase display.
The converter neither recovers these fields from image overlays nor invents them.

## Open both files and import the layout

1. In Foxglove, use **File > Open local files** and **multi-select both**:
   `~/wbr-evidence-archive/lab-day-20261025/3-box13/camera-bag/camera-bag_0.mcap`
   and `~/wbr-evidence-archive/foxglove-twin-20261030-01/twin.mcap`.
   Confirm both files are selected before opening. Opening each file separately can
   replace the current source instead of combining them.
2. In **Layouts > Import from file**, select
   `docs/foxglove_twin/layout.json` from this worktree.
3. Play, pause or seek with the shared playback bar. The Image panels select
   `/camera/camera/color/image_raw` and `/twin/image`. The Raw Messages panel
   selects `/twin/advisory`; State Transitions selects `/twin/phase.message`.
   Image annotation synchronization is disabled; it is separate from the shared
   MCAP timeline and would otherwise require matching annotation messages.
4. To inspect acquisition alignment, pause and inspect the camera message's
   `header.stamp` alongside the twin overlay's full `frame_stamp_ns`.
   Camera log times and camera acquisition times can differ, as described below.

For the scene-only alternative, select `scene-twin.mcap` as the second file;
the same layout works and explicitly shows unavailable gate data.

If the file chooser requires both files in one directory, the conductor can
create a link to the original camera MCAP in the new export directory, then
Command-click `camera-bag_0.mcap` and `twin.mcap` there. This adds a link without
copying or changing the camera recording. Run once; an existing link is retained.

```sh
ln -s "$SOURCE/camera-bag/camera-bag_0.mcap" "$EXPORT/camera-bag_0.mcap"
```

## What aligns and where the timestamp comes from

[scene_twin.read_packets](../../tools/scene_twin/replay.py) reads
`packets.csv`'s `frame_stamp_ns` directly with `int`, into `Packet.stamp`.
[scene_twin.view.record](../../tools/scene_twin/view.py) writes that exact
selected packet stamp to `frames.csv`. Jump replay uses the same reader;
[jump_gate.timeline.export_csv](../../tools/jump_gate/timeline.py) writes the
selected packet's stamp to `timeline.csv`, including when a packet is held.

The source stamp is a **camera header stamp**, not the Pi monotonic clock:
[the obstacle ROS node](../../ros2/wbr_obstacle_node/wbr_obstacle_node/node.py)
computes `sec * 1_000_000_000 + nanosec` from the incoming depth image header,
and [AdvisoryCore.process](../../ros2/wbr_obstacle_node/wbr_obstacle_node/core.py)
preserves it in its advisory and packet. Color frames can be matched by equal
header stamps when the recording contains that synchronized color frame.
The recording may lack an exact match because of different stream timestamps,
dropped frames or different recording/packet start and end times.

The exporter sets **MCAP `log_time`, `publish_time` and the compressed image's
`timestamp` to that exact integer `frame_stamp_ns`**. JSON image timestamps use
`{sec, nsec}` from integer division; PNG bytes use base64. All channels have JSON
message encoding and JSON Schema (`jsonschema`) schemas; no Protobuf, ROS
serialization, camera decoding or MuJoCo import is needed for conversion.
The existing [bag converter](../../tools/bag_tools/foxglove_demo.py) supplies the
`Writer`, schema/channel registration and message-writing pattern; that version
uses ROS CDR, whereas this exporter registers JSON schemas explicitly.

| Topic | Schema | Payload |
| --- | --- | --- |
| `/twin/image` | `foxglove.CompressedImage` | PNG, frame ID `twin`, exact source timestamp |
| `/twin/advisory` | `wbr.twin.Advisory` | `raw`, `gated`, `phase`, `reason`, `confidence` |
| `/twin/phase` | `wbr.twin.Phase` | `message`: gate phase string only |

Each rendered PNG produces one message on each topic. Advisory confidence is
the CSV's `gated_confidence`; raw confidence in the jump demo is ASSUMED 1.0,
not a measured probability. Phase means `gate_phase`, distinct from the synthetic
pose's phase. Advisory messages and phase use the same log and publish stamp as
their corresponding image.

## Limits

- The two files share playback, but the original camera bag is scheduled by its
  MCAP **receipt/log times**, while the twin is scheduled by **header stamps**.
  Receipt latency remains visible as an offset; this exporter does not retime
  the original camera messages or establish zero-latency frame synchronization.
- Rendering samples and holds packets. Duplicate source stamps remain duplicate
  MCAP times, in render sequence order. Several synthetic poses or phases can
  share one timestamp; Foxglove can show only the last message at that instant.
  Synthetic time within a held packet is intentionally not substituted for the
  requested source camera stamp. Some samples can precede the camera recording.
- Advisory and phase are sampled at the PNG render rate, so transitions between
  renders are omitted. State Transitions displays exported samples, rather than
  the complete 100 Hz gate CSV or physically measured jump transitions.
- Twin geometry and robot pose remain inferred/assumed or synthetic, as described
  in [scene_twin](../scene_twin/README.md) and [jump_gate](../jump_gate/README.md).
  No physical jump, calibrated pose, dynamics or ground-truth accuracy is claimed.
- The worker verified MCAP round trips and layout JSON structure. MuJoCo rendering
  and Foxglove layout import/playback require the conductor's graphical session;
  neither was attempted in the worker sandbox. No camera archive, hardware,
  shared checkout, environment or Git history was changed.

## Verification

```sh
~/Desktop/Research/wbr-lab-ops/.venv/bin/python \
  .github/run_unittest.py tools/foxglove_twin
python3 tools/lint_markdown.py \
  docs/foxglove_twin/README.md docs/foxglove_twin/RUN_LOG.md
```

Tests create tiny PNGs with Pillow in temporary directories, convert both CSV
formats and read the output with `mcap.reader`. They verify topics, message
counts, schema names/encoding, exact log/publish/image timestamps, unchanged PNG
bytes, jump tick selection, custom FPS and held stamps. They also exercise
input/output guards. See the [worker run log](RUN_LOG.md) for actual results.

## Conductor check (2026-10-30)

- Converted the 601-frame jump-gate render (`--jump-at 20`) to `~/wbr-evidence-archive/foxglove-twin-20261030-01/twin.mcap`, 54 MB.
- Topics: 601 messages each on `/twin/image`, `/twin/advisory` and `/twin/phase`.
- Twin stamps run 1792900867.686–927.598 s. The 3-box13 camera bag runs 868.590–1063.779 s. Overlap: 59.0 s (MEASURED by reading both MCAPs).
- The Foxglove GUI has not been opened yet; the owner verifies the side-by-side view.
