# TerrainAdvisory link bench

- Worktree/branch: `wbr-wt-c2-advisory-link`, `claude2/20261024-advisory-link`.
- Read the link bench README/firmware/Pi client, link protocol, advisory spec and
  detector modules before implementation. Initial F446 build passed (text 5976 B).
- Added types 4/5, exact 42/27-byte payloads, shared Python wire unpack, C/Python
  vectors, validation tests and the compatibility wrapper. Existing types 1–3
  vectors/layouts remain unchanged.
- Firmware applies session `WBRLINK1`, modular increasing sequence, advisory
  acceptance/rejection counts, 300 ms stale timing, immediate main-loop echoes
  and 10 Hz stale echoes. PA8 still marks decoded USART1 packets. No actuation code.
- Added synthetic/bag Pi transport, monotonic detector/send/echo timestamps,
  percentile/loss/rejection/stale summary, CSV, GPIO marker and injected faults.
  Added pseudo-terminal simulator coverage and advisory documentation.
- Final F446 rebuild: text 7264 B, data 0 B, BSS 5120 B; prebuilt binary
  matches build output. SHA-256:
  `f1982bc5f9458e48979e872a8237678ff28073db72b65be16c92510654d717cf`.
- `make -C tools/link_proto test`: PASS (C golden vectors; 5 Python tests).
- `make -C tools/link_bench test`: PASS (9 tests; QEMU test skipped because
  QEMU is unavailable). Synthetic PTY advisory fault/stale/recovery test passed.
- `make -C tools/link_bench/firmware`: PASS; rebuilt image is byte-identical to
  `prebuilt/link_bench_f446.bin`.
- `python3 -m unittest discover -s tools/obstacle_decision/tests -p
  'test_obstacle_decision.py' -v`: PASS (5 tests, including codec round trip).
- Requested pytest command was attempted, but Python has no pytest. `/tmp` venv
  install of pytest/rosbags/numpy/matplotlib/mcap-ros2-support failed because
  package host name resolution is unavailable. Full bag replay is unverified;
  import failure is retained in `/tmp/advisory-obstacle-unittest.log`.
- Initial codec wrapper unittest exposed duplicate `plane_valid` argument; fixed.
  An initial PTY health test showed an extra WIRE error; the final bench suite
  passes and keeps measured wire errors in simulator counters.
- Command logs: `/tmp/advisory-link-proto.log`, `/tmp/advisory-link-bench.log`,
  `/tmp/advisory-link-firmware.log`, `/tmp/advisory-pytest.log`,
  `/tmp/advisory-pip-install.log`, `/tmp/advisory-obstacle-codec-tests.log`.
- Real Nucleo/Pi, both physical UART paths, analyzer capture, real bags and
  measured hardware latency/loss remain UNVERIFIED. No hardware was flashed.
- Local `git add`/commit was attempted after verification but Git could not create
  `.git/worktrees/wbr-wt-c2-advisory-link/index.lock`: linked-worktree metadata
  is under the separate `wbr-perception-phase1-runtime/.git` tree, which is
  read-only in this session. No branch switch or push was attempted.
