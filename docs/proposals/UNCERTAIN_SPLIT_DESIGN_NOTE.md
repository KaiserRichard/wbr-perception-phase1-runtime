# Design note: splitting terrain `UNCERTAIN`

**Scope.** Design only; no runtime/interface changes are made here. The Pi–MCU
link specification is marked candidate/proposed and requires firmware owner
review ([`SPEC.md`](../../tools/link_proto/SPEC.md), lines 1–7).

Evidence labels: **KNOWN** means directly supported by checked-in code/docs;
**INFERRED** is a consequence of those facts; **ASSUMED** is a proposed safety
policy; **UNKNOWN** means this checkout does not establish the fact. Line
references below identify the evidence for current behavior.

## Current behavior

- **KNOWN:** Advisory values are `NONE=0`, `JUMP_CANDIDATE=1`,
  `STOP_CANDIDATE=2`, `UNCERTAIN=3` ([`decide.py`](../../tools/obstacle_decision/decide.py),
  lines 6–7). The detector configuration uses a 2 cm minimum obstacle height
  and a 3 cm minimum jump-band height ([`core.py`](../../ros2/wbr_obstacle_node/wbr_obstacle_node/core.py),
  lines 12–26).
- **KNOWN:** confirmation is `sum(last confirm_m detections) >= confirm_n`,
  with defaults 3 of 5; it is a rolling count, not a consecutive-frame
  requirement ([`decide.py`](../../tools/obstacle_decision/decide.py), lines
  11–18, 29–35). While unconfirmed, a detected candidate is `UNCERTAIN`
  ([same](../../tools/obstacle_decision/decide.py), lines 57–57).
- **KNOWN:** Once confirmed and the plane is valid, height below the 3 cm
  `jump_min_h` threshold becomes `UNCERTAIN` when entering from `NONE` or
  `UNCERTAIN` ([`decide.py`](../../tools/obstacle_decision/decide.py), lines
  43–57). The code itself comments that `UNCERTAIN` also means “not confirmed
  yet” (line 55). With invalid plane, it instead returns `STOP_CANDIDATE`
  when estimated distance is at most 1.5 m, otherwise `UNCERTAIN` (lines
  39–42); missing finite height also yields `UNCERTAIN` (lines 46–47).
- **INFERRED:** The premise is partly right but incomplete. Low *detected*
  objects below the 3 cm jump band can be `UNCERTAIN`; however the detector
  rejects objects below its 2 cm minimum, so “box height < 3 cm” does not
  guarantee an advisory at all. Also, the unconfirmed case is 3-of-5 rather
  than consecutive frames. The ROS wrapper exports the state/code and
  measurements to JSON and the proposed wire record ([`core.py`](../../ros2/wbr_obstacle_node/wbr_obstacle_node/core.py),
  lines 94–121); topic packing accepts only codes 0–3 (lines 130–145).
- **KNOWN:** The ROS topic likewise defines codes 0–3, and its H7 receiver
  contract maps no valid message for 300 ms to `UNCERTAIN`; it says the topic
  is advisory only and the STM32 retains balance and jump authority
  ([`TERRAIN_ADVISORY_TOPIC.md`](../interfaces/TERRAIN_ADVISORY_TOPIC.md),
  lines 15–19, 30–42). The H7 change report says accepted snapshots are
  freshness-tracked and stale age reports `UNCERTAIN`, while the subscriber
  callback does not call motor/mode/timeout/RC APIs
  ([`TERRAIN_ADVISORY_CHANGES.md`](../interfaces/h7_terrain_advisory/TERRAIN_ADVISORY_CHANGES.md),
  lines 5–8, 19). **UNKNOWN:** the underlying H7 `.c/.h` sources are not in
  this checkout, so this note cannot verify the report against implementation.
- **KNOWN:** Type 4 encodes the advisory in one byte at payload offset 16;
  values 0–3 are specified, the payload is 42 bytes, and decode/encode reject
  values above 3 ([`SPEC.md`](../../tools/link_proto/SPEC.md), lines 140–148;
  [`link_proto.c`](../../tools/link_proto/link_proto.c), lines 42–45,
  72–76, 120–125). The packet uses version 1 and `COBS(header || payload ||
  CRC-32C) || 00` framing ([`SPEC.md`](../../tools/link_proto/SPEC.md),
  lines 19–38). Nucleo bench LEDs show `UNCERTAIN` as blue; unknown values
  produce no LED ([`bench.c`](../../tools/link_bench/firmware/bench.c),
  lines 106–116).
- **KNOWN:** Evaluation docs list tests for tall-box stop, empty/outside
  `NONE`, one-frame blip rejection, and codec round trip; the report describes
  synthetic-only validation and no transport/ROS integration
  ([`REPORT.md`](../../tools/obstacle_decision/REPORT.md), lines 3–12,
  66–73). Codec tests validate advisory range and malformed values
  ([`test_link_proto.c`](../../tools/link_proto/tests/test_link_proto.c),
  lines 192–208).

- **KNOWN (added in review):** the bench firmware also blinks the yellow LED at
  4 Hz for `UNCERTAIN`, for rigs without the blue LED on D9
  ([`main.c`](../../tools/link_bench/firmware/main.c), line 177). On such a rig
  `UNCERTAIN` and `JUMP_CANDIDATE` share the yellow LED (blink vs solid), so any
  new low-obstacle indication needs a pattern the operator can tell apart.
- **KNOWN (added in review):** the "below the band" boundary is hysteretic. From
  `JUMP_CANDIDATE` the state drops to `UNCERTAIN` only below
  `jump_min_h - 0.01` = 2 cm; from `STOP_CANDIDATE`, below 4 cm; from
  `NONE`/`UNCERTAIN`, below 3 cm (`decide.py`, lines 45–56). A split state
  inherits these three thresholds.
- **INFERRED (added in review):** type 4 already carries `plane_valid` and the
  EMA-filtered obstacle `height` (`SPEC.md` TerrainAdvisory offsets 17 and 26).
  A consumer can therefore already separate "plane valid, finite height below
  3 cm" from "plane invalid / no finite height" with **no wire change**. The one
  case it cannot see is "detected but not yet confirmed (fewer than 3 of 5)",
  because confirmation is not on the wire. Whether `confidence` (offset 18) could
  carry it is **UNKNOWN**; its producer semantics were not checked here.

## Options

| Option | Wire/protocol impact | STM32H7 and Nucleo impact | Tests and effort |
|---|---|---|---|
| **A. Keep one `UNCERTAIN`** | No enum, layout, framing, CRC, or version change. | H7 continues treating all uncertainty reasons alike; bench keeps blue. | No interface tests change. Lowest effort. Loses reason-level operator information. |
| **B. Add enum `LOW_OBSTACLE` / `ROLL_OVER`** | In the candidate type-4 encoding, assign code 4; keep one-byte field and 42-byte payload, so **COBS/CRC framing can remain byte-for-byte structurally unchanged**. But the current schema and codecs cap values at 3, so producers, decoders, topic range validation and enum docs must change. Version 1 is not safely forward-compatible with strict old decoders; **INFERRED: version bump or explicit negotiated compatibility is needed** for deployed peers. | H7 must recognize the code and define it as informational; the change report’s eight-value array validator/code range must be updated (source unavailable here). Bench needs a new LED mapping; unknown currently maps to off. | Add low-height classification tests, boundary/hysteresis tests, old/new codec compatibility and invalid-code tests, H7 validation/display tests, and bench LED tests. Moderate/high effort because this changes shared enum semantics. |
| **C. Keep `UNCERTAIN`; add reason/flags field** | Extending type 4 payload changes its exact length and 42-byte schema. If appended, update size/offsets/codec; framing and CRC algorithm stay the same, but packet bytes and payload length change. Requires a version bump or explicit compatibility mechanism; old exact-length parsers reject it. Alternative fixed-size reserved byte must first be established (none is specified in current 42-byte layout). | H7 tracks freshness plus reason for display/diagnostics, but retains a single state; bench may stay blue or optionally distinguish reasons. | Add reason mapping/validation, reason-preservation, stale-reason reset, topic and wire tests, plus UI tests. Moderate effort, more extensible than multiple top-level states. |

### Safety constraints and recommendation

- **ASSUMED:** `LOW_OBSTACLE` should mean “geometry estimates below the
  jumpable band,” never “safe to jump” or “safe to ignore.” The STM32 remains
  authoritative. For `JUMP_CANDIDATE`, require the existing independent
  operator/firmware gates; for `STOP_CANDIDATE`, inhibit a jump and take the
  firmware’s conservative response; for `UNCERTAIN`, unknown/stale data, or
  unrecognized codes, do not grant jump permission. A new low-obstacle state
  must be handled at least as conservatively as `UNCERTAIN` until a separately
  reviewed roll-over policy exists.
- **INFERRED recommendation:** Prefer **C**, a reason/flags field, if the goal
  is to separate “not confirmed,” “below jump band,” and “measurement/plane
  uncertainty” while preserving one conservative top-level state. It keeps
  stale/unknown handling conceptually distinct from a physical low obstacle and
  avoids teaching consumers that a new advisory enum implies a new motion
  permission. Before changing the candidate protocol, settle compatibility and
  versioning with the H7 owner. If visibility alone is not needed at the STM32,
  option A is safest and cheapest; option B is justified only if consumers need
  a distinct top-level category and all old consumers can be upgraded together.
- **Review note (Claude, 30 Oct):** for the 31 Oct demo, A plus consumer-side
  use of the existing `height`/`plane_valid` fields gives most of the
  "below jump band" visibility at zero protocol risk. C is the right
  longer-term shape once the H7 owner agrees on versioning. Nothing here should
  change before the demo.

**Abbreviations:** MCU = microcontroller unit; STM32H7 = the project’s H7-series
microcontroller; CRC = cyclic redundancy check; COBS = Consistent Overhead Byte
Stuffing; ROS = Robot Operating System; LED = light-emitting diode.
