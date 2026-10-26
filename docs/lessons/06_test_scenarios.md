# 06 — Bench test scenarios

## Purpose and limits

These scenarios form a bottom-up learning sequence for the CAN monitor and
terrain-advisory link. They are proposed bench procedures, not a claim that
they have been run or passed.

The requested `tools/agv_f446`, `tools/agv_f446_test`, and `tools/supervisor_demo`
directories are not present in this checkout. Available related material is
`tools/can_monitor`, `tools/link_bench`, `tools/microros_f446`, and the advisory
interface docs. Where a planned scenario depends on a missing binary or board
application, the setup below states the dependency instead of claiming it exists.

## General bench rules

Use a current-limited supply, verify board and transceiver voltage, and keep
motors unpowered for all new subscriber and protocol tests.
Do not connect two CAN transmitters unless the test explicitly requires them.
A silent monitor receives without ACKing; a normal node is needed for an active
transmitter to see an ACK (`tools/can_monitor/firmware/can_rx.c:45-49`).

Record the board revision, firmware hash, bus topology, bitrate, termination,
Agent endpoint, topic type, and QoS with every run. A green LED alone is not
proof that a complete message path is valid.

## Scenario 1 — Demo-board CAN loopback

**Purpose.** Verify the F446 monitor receive path and frame decoding without
connecting to the robot. The monitor reads CAN FIFO0, exposes standard versus
extended ID, DLC, and payload bytes (`tools/can_monitor/firmware/can_rx.c:66-86`).

**Setup.** Use an isolated F446 plus a CAN transceiver and a separate known-good
CAN node or a documented controller internal loopback setup. Add two 120 Ω
terminators only if the fixture has no built-in endpoint termination.
Keep the robot disconnected. Confirm the monitor is configured for the same
nominal bitrate as the peer (`can_rx.c:41-50`).

**Steps.**

1. With power removed, inspect CAN_H/CAN_L continuity and measure termination.
2. Power the isolated fixture and check transceiver standby/enable pins.
3. Send a known standard frame, then a known extended frame, each with a
   recognizable eight-byte pattern.
4. Confirm ID type, ID, DLC, and byte order in the captured output.
5. Repeat at the configured 1 Mbit/s after checking the controller clock.

**Expected result.** Both frame formats are received, DLC is eight, and payload
bytes match exactly. The current CAN monitor decoder is RobStride-oriented, so
an unrelated test frame may be received but classified as “other”; capture and
decode are separate layers (`tools/can_monitor/firmware/robstride_decode.c:24-84`).

**If it fails.** First check power and transceiver enable, then crossed RX/TX
logic pins or CAN_H/CAN_L wiring, common ground, termination, and bitrate.
If no frame reaches FIFO, inspect filter setup and RX FIFO overrun counters
(`can_rx.c:28-38, 81-89`). If raw bytes are right but values are wrong, debug
identifier format, DLC, endianness, and scaling before changing bus timing.

## Scenario 2 — Advisory LEDs on the F446 receiver

**Purpose.** Exercise a ROS message through publisher, Agent, F446 micro-ROS
subscription, validation, freshness timer, and LED mapping without motors.
The local F446 README specifies code-to-LED behavior and a 300 ms stale signal
(`tools/microros_f446/README.md:42-57`).

**Setup.** Use the Nucleo-F446RE stand-in, USB/VCP serial device, Pi-hosted Agent,
and the documented 115200 8-N-1 transport (`tools/microros_f446/README.md:3-7, 67-78`).
Wire only the documented low-current LED outputs with resistors. Leave all motors
and robot CAN harnesses disconnected.

**Steps.**

1. Start the Agent and confirm the node becomes visible.
2. Publish valid eight-element arrays with advisory codes NONE, JUMP_CANDIDATE,
   STOP_CANDIDATE, then UNCERTAIN.
3. Confirm green, yellow, red, and blue/blink patterns respectively.
4. Send a wrong-length array and then a non-finite value; confirm accepted state
   and sequence do not change.
5. Stop valid publishing for longer than 300 ms; confirm stale/red indication.
6. Restart publishing and confirm a valid message restores the corresponding LED.

**Expected result.** The receiver accepts exactly eight finite doubles, updates
sequence/receive time only on valid input, and flags stale after 300 ms
(`tools/microros_f446/README.md:44-53, 87-95`).

**If it fails.** Check device path and baud, Agent session, node/topic/type,
offered/requested QoS, then executor subscription and callback. For incorrect
LEDs, verify pin mapping and active-high wiring. For a stale indication that
never clears, inspect message validation and whether valid traffic updates the
MCU-local timestamp; do not compare Pi monotonic time to MCU ticks
(`docs/interfaces/TERRAIN_ADVISORY_TOPIC.md:26-37`).

## Scenario 3 — Safety-filter QoS compatibility

**Purpose.** Demonstrate that a ROS graph can show a publisher while a
subscriber receives nothing because offered/requested reliability is
incompatible.

**Setup.** Use the advisory publisher policy Best Effort, Keep Last depth 1
(`docs/interfaces/TERRAIN_ADVISORY_TOPIC.md:5-12`). The reported `safety_filter`
source was not found in the named checkout paths. If restored, inspect its
subscription QoS before execution. Keep a diagnostic subscriber available with
Best Effort QoS as the control case.

**Steps.**

1. Inspect topic name, type, namespace, publisher reliability, and subscriber
   reliability in graph introspection output.
2. With the reported Reliable subscriber, verify it does not match the
   Best-Effort publisher.
3. Change only the test subscriber to Best Effort, Keep Last depth 1.
4. Verify advisory samples arrive, then restore the intended application config
   and record the precise change needed.
5. Verify stale handling remains active when the publisher is stopped.

**Expected result.** The Best Effort diagnostic subscriber receives the
publisher's samples; a Reliable subscription cannot request a guarantee the
publisher does not offer. The concrete bug is reported by the task brief; it
was not independently verified because the named safety-filter source is
missing. The publisher contract is documented (`TERRAIN_ADVISORY_TOPIC.md:7-12`).

**If it fails.** Debug graph names and types first, then discovery/domain,
Agent/client session, QoS compatibility, and finally callback execution.
A successful ROS CLI echo with Best Effort but no application callback points
toward the app's subscription or callback path, not the publisher's physical
link.

## Scenario 4 — CAN monitor on the robot

**Purpose.** Passively observe real motor traffic and learn the actual frame
mix without adding commands or ACKs.
The monitor's silent-mode bit is set in its BTR write
(`tools/can_monitor/firmware/can_rx.c:45-49`).

**Setup.** First mechanically secure the robot and turn motor power off.
Confirm the monitor firmware hash and that the adapter is physically configured
for listen-only. Attach to the intended bus using short stubs; do not add a
third terminator. Review current bus termination before connecting.

**Steps.**

1. Capture with robot motor power off and record idle/error state.
2. If an owner-authorized commissioning run powers the robot, keep the monitor
   receive-only and observe only; do not issue CAN frames from the monitor.
3. Separate standard/extended identifiers, then group extended IDs by
   communication type and target ID.
4. Decode only recognized eight-byte types; keep unknown frames in the raw log.
5. Compare observed motor feedback to the actuator's local status and timestamps.

**Expected result.** The monitor can record frames without acknowledging or
altering the bus. Its parser accepts extended frames with expected lengths and
classifies known types (`tools/can_monitor/firmware/robstride_decode.c:24-84`).
A lack of ACK from the passive monitor is expected.

**If it fails.** Start at adapter power/clock, transceiver state, bus wiring,
termination, and correct receive pins. Then verify baud and silent configuration.
If raw frames arrive but decode fails, compare IDE flag, ID bitfields, DLC, and
payload layout. A decoder's rejection is not evidence that the physical bus is
broken.

## Scenario 5 — H7 advisory subscriber with motors off

**Purpose.** Validate the H7-side transport, Agent session, subscription,
message validation, and local freshness without involving actuation.
The proposed integration analysis requires motors unpowered during parser and
staleness checks (`docs/proposals/DM_JUMP_INTEGRATION_ANALYSIS.md:51-57`).

**Setup.** Use the H7 firmware only after the firmware owner provides a reviewed
subscriber build and transport configuration. The read-only reference project
`Microros_H723_USB` documents USB CDC micro-ROS transport
(`docs/topics.md:7-12`), but it is the AGV project and is not proof that the
DM-jump board has USB CDC configured. The jump integration analysis says USB
support and clock configuration were absent in that firmware snapshot
(`docs/proposals/DM_JUMP_INTEGRATION_ANALYSIS.md:61-67`).
Keep all motor power disconnected and jump-state code unchanged.

**Steps.**

1. Verify the H7 receives a valid topic and reports its accepted code, sequence,
   and MCU-local receive tick through diagnostics.
2. Send valid codes 0–3 with finite data and monotonically increasing sequence.
3. Send wrong length, NaN/Inf, invalid code, duplicate sequence, and malformed
   transport records if the chosen link protocol defines them.
4. Pause the sender for 100, 150, 300, and 400 ms and observe the declared
   freshness transition using MCU time.
5. Resume with a valid message and check recovery; confirm no actuator frame or
   state transition is caused by advisory data.

**Expected result.** Valid inputs update the advisory snapshot; rejected inputs
do not refresh freshness; after 300 ms without a valid message the state is
UNCERTAIN (`docs/interfaces/TERRAIN_ADVISORY_TOPIC.md:30-42`). No motor outputs
are involved in this test.

**If it fails.** Debug physical transport, framing, bytes, parser validation,
sequence policy, MCU timestamp, and stale-state logic in that order. Then check
ROS graph, topic type, QoS, and executor callback. Keep clocks separate. Preserve
failure logs rather than changing timeout thresholds to obtain a pass.

## Bottom-up failure map

```text
power / pins / transceiver
        ↓
physical bus or USB/UART byte stream
        ↓
frame boundaries, CRC, identifier, DLC
        ↓
message type and field scaling
        ↓
ROS Agent session and topic graph
        ↓
QoS match and executor handle
        ↓
validation, local timestamp, stale policy
        ↓
application state (motors remain disabled here)
```

Move upward only after the lower layer has evidence of correct operation.
Keep expected output and actual output distinct in the run note.

## How this applies in our project

Run these as staged, motors-off learning scenarios. First qualify isolated
physical capture and message parsing. Then verify LED semantics and QoS. For
H7, require an owner-reviewed receiver image and transport configuration; do not
borrow the AGV's USB setup as if it were the WBR board's. None of these
scenarios validates a jump or authorizes motor behavior.

<details>
<summary>Self-check questions and answers</summary>

1. **Why should the monitor not ACK a robot frame?**
   It is configured for listen-only observation and must not change bus behavior.
2. **What should a malformed advisory do to the freshness timestamp?**
   Nothing; rejected input must not make old state appear fresh.
3. **What is the control case for the QoS mismatch test?**
   A subscriber using Best Effort with the documented Best Effort publisher.
4. **Why are motors disconnected in the H7 subscriber test?**
   The goal is transport and validation evidence without actuation or state changes.
5. **What order should be used to debug a missing decoded frame?**
   Physical wiring and transceiver, bitrate, raw frame capture, then ID/DLC/payload parsing.

</details>
