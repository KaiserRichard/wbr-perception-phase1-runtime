# Supervisor demo

- Added `tools/supervisor_demo/` with ROS 2 safety-filter adapter, pure decision
  function, six unit tests, 20 Hz command pattern, launch script, Foxglove layout,
  and supervisor walkthrough.
- Policy implements the requested bench-demo rules; stale age uses monotonic
  receipt time. The docs identify the F446, CAN fake motor, and recorded camera
  as stand-ins and list unproven claims.
- Test: `python3 -m unittest discover -s tools/supervisor_demo/tests -v` —
  6 passed.
- No ROS launch, bag replay, serial connection, firmware operation, Foxglove
  GUI, or physical hardware behavior was run or verified.
- Changes remain uncommitted on `claude2/20261026-supervisor-demo`.
