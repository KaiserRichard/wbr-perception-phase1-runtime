# TerrainAdvisory link bench milestone review

- Merged PRs: none. Changes remain uncommitted because the sandbox denies writes
  to this linked worktree's Git metadata in `wbr-perception-phase1-runtime/.git`.
- Scope: shared type 4/type 5 codec and vectors, advisory-only F446 receiver and
  echo, Pi synthetic/bag sender, pseudo-terminal simulator, docs and prebuilt.
- `make -C tools/link_proto test`: PASS; C vectors and 5 Python tests.
- `make -C tools/link_bench test`: PASS; 9 tests, QEMU firmware test skipped
  because `qemu-system-arm` is unavailable. Includes synthetic advisory and
  CRC/old-sequence/session/non-finite/400 ms silence/recovery exercise.
- `make -C tools/link_bench/firmware`: PASS; text 7264 B, data 0 B, BSS 5120 B.
  Built image equals packaged prebuilt. SHA-256:
  `f1982bc5f9458e48979e872a8237678ff28073db72b65be16c92510654d717cf`.
- Five `test_obstacle_decision.py` unittest cases pass, including shared codec
  compatibility. Requested pytest command could not run (`pytest` is absent);
  temporary dependency installation failed at DNS resolution. Bag replay import
  test therefore remains unverified.
- Limitations: real Nucleo/Pi UART, physical USART2, analyzer capture, actual
  rosbag/MCAP replay, measured hardware loss/latency and all physical behavior
  are UNVERIFIED. No hardware was flashed. No controller/actuation behavior was
  added.
- Logs: `/tmp/advisory-link-proto.log`, `/tmp/advisory-link-bench.log`,
  `/tmp/advisory-link-firmware.log`, `/tmp/advisory-pytest.log`,
  `/tmp/advisory-pip-install.log`, `/tmp/advisory-obstacle-unittest.log`, and
  `/tmp/advisory-obstacle-codec-tests.log`.

Claude review request: inspect the local TerrainAdvisory milestone and confirm
the 42-byte/27-byte wire layouts, rejection reasons, stale timing, and bench-only
safety boundary against the implemented vectors and firmware logic.
