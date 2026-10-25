# Terrain Advisory ROS 2 Topic

## Interface

| Property | Value |
|---|---|
| Topic | `/terrain_advisory` (configurable with `advisory_topic`) |
| Direction | Pi obstacle node publisher → STM32 subscriber |
| Type | `std_msgs/msg/Float64MultiArray` |
| Reliability / history | Best Effort, Keep Last depth 1 |
| Rate | One message per processed depth frame; target about 8–15 Hz |

`data` contains exactly eight values, in this fixed order. `layout` is unused.

| Index | Field | Meaning |
|---:|---|---|
| 0 | `advisory_code` | Integer-valued code: 0 NONE, 1 JUMP_CANDIDATE, 2 STOP_CANDIDATE, 3 UNCERTAIN |
| 1 | `distance_m` | Obstacle front-face distance in the ground frame; 0 if none |
| 2 | `height_m` | Obstacle height in metres; 0 if unavailable |
| 3 | `width_m` | Obstacle width in metres; 0 if unavailable |
| 4 | `confidence` | Confidence in `[0, 1]` |
| 5 | `plane_valid` | `1` when the ground plane is valid, otherwise `0` |
| 6 | `sequence` | Monotonically increasing Pi processed-frame counter |
| 7 | `detection_age_s` | Pi monotonic time from depth-frame receipt to publish; seconds |

Unavailable measurements are encoded as zero. All eight transmitted values must
be finite. `detection_age_s` is diagnostic only: it uses the Pi monotonic clock
and must never be compared with an STM32 tick or ROS epoch timestamp.

## STM32 receiver rules

- Accept only `data.size == 8`, finite values at every index, and an integer
  advisory code in the defined range 0–3. Reject malformed messages without
  refreshing the receive time.
- Record the STM32 tick when each valid message arrives. If no valid message has
  arrived for 300 ms, report `UNCERTAIN` regardless of the last received code.
  Compute elapsed time with the STM32 tick and its wrap-safe subtraction.
- This topic is advisory only. It never commands motion; the STM32 retains all
  balance and jump authority.
- A possible future jump gate is: operator request **and** a fresh
  `JUMP_CANDIDATE` **and** distance inside an owner-chosen window. No distance
  window is defined by this interface.

The example receiver is in [`terrain_advisory_microros_example.c`](terrain_advisory_microros_example.c).
