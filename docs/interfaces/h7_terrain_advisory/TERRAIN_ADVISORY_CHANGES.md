# Terrain advisory receive path

## Changes

- `Core/Src/freertos.c:99-122, 335-394` adds the `/terrain_advisory` subscriber storage and a 10 Hz `/terrain_advisory_ack` publisher. The subscriber uses a static eight-double buffer and Best Effort QoS. Its callback at lines 978-989 only passes the received array to the advisory snapshot module; it does not call any motor, mode, timeout, or RC API.
- `Core/Src/freertos.c:623-721, 795-809` creates and destroys the new ROS entities, adds the subscription to the executor, and raises executor capacity from four to five handles.
- `User/APP/terrain_advisory.c:14-79` and `User/APP/terrain_advisory.h:1-36` validate the eight-value array, keep accepted/rejected counters and the last accepted sequence, copy snapshots inside a short FreeRTOS critical section, and report UNCERTAIN once the local receive age reaches 300 ms. Invalid messages increment `rejected` without changing the accepted snapshot or its freshness tick.
- `User/APP/lcd_task.c:178-184, 455-489` uses the existing 20 Hz LCD refresh to show `ADV:STALE` or the current code, distance, and height on the System Stats page.
- `Makefile:42` includes the module in `C_SOURCES`.
- `docs/topics.md:26, 218-248` documents the topic fields, QoS, rate, and CLI examples.

The interface contract implemented here is the one supplied in the task because `docs/interfaces/TERRAIN_ADVISORY_TOPIC.md` is absent from this checkout.

## Resource impact

- Static subscription data storage adds 8 doubles (64 bytes). The module's snapshot and bookkeeping add approximately another 64 bytes of static storage, plus the small ROS message/entity structs. No heap allocation is performed in the callback.
- The executor handle capacity increases by one, from 4 to 5. The static library is configured for 5 subscriptions, so that pool is now full.
- The firmware has 4 publishers before this change and the static library allows 10. Adding the ack publisher uses 5 of 10 slots, so `micro_ros_stm32cubemx_utils/microros_static_library/library_generation/colcon.meta` does not need an update or library rebuild for publisher capacity.
- Motor command behavior, modes, watchdogs, and RC logic were not changed. The advisory is currently informational only.

## Bench check (motors disabled)

1. Keep the wheels lifted or otherwise mechanically safe, and disable motor outputs with `/motor_enable` before connecting the ROS 2 publisher. Check the device's `RC` state and do not publish any motor command topic.
2. Start the agent and verify discovery:

   ```bash
   ros2 node info /stm32h7_node
   ros2 topic echo /terrain_advisory_ack
   ```

   The ack publishes at about 10 Hz and remains zero until a valid advisory is received.

3. Publish a valid STOP_CANDIDATE sample (code 2, 0.99 m distance, 13 cm height, 40 cm width, 0.95 confidence, valid plane, sequence 42, source age 20 ms):

   ```bash
   ros2 topic pub -r 10 /terrain_advisory std_msgs/msg/Float64MultiArray \
     "{data: [2.0, 0.99, 0.13, 0.40, 0.95, 1.0, 42.0, 0.02]}"
   ```

   The System Stats LCD page should show `ADV:STOP 0.99m 13cm`; `/terrain_advisory_ack` should report 42.

4. Stop the publisher. Within 300 ms the LCD should change to `ADV:STALE`; the ack should retain 42. Restart with another valid sequence and confirm that both update.
5. With motors still disabled, test validation using a short array or invalid field. For example, confidence `1.1` must not update the LCD snapshot's freshness or ack sequence:

   ```bash
   ros2 topic pub -1 /terrain_advisory std_msgs/msg/Float64MultiArray \
     "{data: [2.0, 0.99, 0.13, 0.40, 1.1, 1.0, 43.0, 0.02]}"
   ```

6. For the unplug check, first publish a valid sample, then disconnect the terrain-advisory source or stop its host publisher while leaving the LCD powered. The display should become `ADV:STALE` after 300 ms and the ack should keep its last accepted sequence. If disconnecting the USB transport itself, the firmware's existing agent reconnect behavior also applies; verify freshness after the link is restored.

## Unverified

- No build, test, script, or Make target was run, as requested. Compiler/linker compatibility and the rebuilt firmware image therefore remain unverified.
- No board or micro-ROS Agent was available, so topic discovery, reliable ack behavior, real receive timing, LCD formatting, and the unplug procedure remain unverified on hardware.
- With the required eight-double static buffer, a serialized message longer than the buffer may be rejected by micro-ROS during deserialization before the callback runs. Short wrong-length messages are counted by the module; over-capacity messages may not increment its rejected counter. Confirm this behavior with the exact generated micro-ROS library during bench commissioning.

## Build check (Claude 2, 26 Oct)

Built on macOS with Arm GNU Toolchain 14.2.Rel1 and the senior's prebuilt libmicroros v1.0.0
(SHA-256 3c7bb1a2...4ab6b verified; fetched with `gh release download`, because the fetch script's
`${VAR,,}` needs bash 4 and macOS ships bash 3). One fix to Codex's code: `terrain_advisory.c` must
include `FreeRTOS.h` before `task.h`. Result: text 207184, data 14880, bss 273864 B; `prebuilt/microros_H7_terrain_advisory.bin`.
Only pre-existing warnings (LCD font tables). Not run on hardware.
