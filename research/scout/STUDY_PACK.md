# Study pack (S2)

## Reading order

Estimated focused reading time: **136 minutes**. The first six follow `docs/lessons/README.md` on `main`.

1. `docs/lessons/01_can_and_robstride.md` — 12 min.
2. `docs/lessons/02_micro_ros_on_stm32.md` — 12 min.
3. `docs/lessons/03_agv_base_firmware.md` — 12 min.
4. `docs/lessons/04_wbr_balance_lqr_vmc.md` — 15 min.
5. `docs/lessons/05_wbr_jump_sequence.md` — 12 min.
6. `docs/lessons/06_test_scenarios.md` — 15 min.
7. `docs/imu_view/LESSON.md` (`claude/wbr-3d-imu-twin-90a9b7`) — 15 min.
8. `tools/imu_can_bench/README.md` (`claude2/20261029-imu-can-bench`) — 8 min.
9. `docs/pil/LESSON.md` (`claude/pil-research-0acf20`) — 15 min.
10. `lab-day-20261030/FINAL_LAB_RUNBOOK.md` (PR #158; `claude2/20261030-final-runbook`) — 20 min.

## Demos

Run each from the specified repository root; commands below are copied from the corresponding README or replay script.

### (a) 3D viewer, fake IMU

- **Worktree:** `cd /Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime/.claude/worktrees/wbr-3d-imu-twin-90a9b7` (branch `claude/wbr-3d-imu-twin-90a9b7`). Only the Python venv is in `~/Desktop/Research/wbr-lab-ops/.venv`.
- **Command:**
  ```bash
  ~/Desktop/Research/wbr-lab-ops/.venv/bin/mjpython -m tools.imu_view.view --fake
  ```
- **Expected:** the WBR visualization follows simulated pitch (±20°) and roll (±10°); accelerometer, gyro, and complementary-filter estimates are shown.
- **Hardware:** Mac only; Pi off; no MCU or IMU needed; BOOT0 out.

### (b) 3D viewer, live MPU6050

- **Worktree:** same IMU-viewer branch and repo root as (a).
- **Prerequisite:** Pi UART is free, the GY-521 MPU6050 is connected to the bench Nucleo, and `imu_can_bench` is flashed. Flash instructions are in `tools/imu_view/README.md`: BOOT0 fitted before RESET, then remove BOOT0 and RESET; keep the board still for the viewer's 2 s bias calibration.
- **Command (the explicit 8-N-1 setting is required):**
  ```bash
  ssh wbr-pi5 'stty -F /dev/ttyAMA0 115200 raw -echo cs8 -parenb -cstopb && cat /dev/ttyAMA0' | ~/Desktop/Research/wbr-lab-ops/.venv/bin/mjpython -m tools.imu_view.view --stdin --save ~/imu_view_run.csv
  ```
- **Expected:** the model tilts with the board; check flat = near zero, X-arrow end down = positive pitch, left/Y edge up = positive roll. The owner ran it on the bench on 30 Oct (a real recording was later used in PR #176).
- **Hardware:** Pi on; Nucleo powered with `imu_can_bench`; BOOT0 out after normal reset; GY-521 chip side up, X arrow forward. No micro-ROS agent or other process may own `/dev/ttyAMA0`.

### (c) MuJoCo LQR push recovery

- **Worktree:** `main`, repository root; source is `sim/README.md`.
- **One-time setup (Python 3.12), then run:**
  ```sh
  python3.12 -m venv .venv
  .venv/bin/python -m pip install -r sim/requirements.lock
  .venv/bin/mjpython -m sim.view
  ```
- **Expected:** the unscored viewer repeats a 10 s run with a 6 N push at 3 s; the delay-aware LQR attempts recovery. Default simulation assumptions include 5 ms delay, 5 ms torque lag, and body IMU noise.
- **Hardware:** Intel Mac only; Pi off; no MCU/firmware required; BOOT0 out.

### (d) Processor-in-the-loop with fake MCU

- **Worktree:** branch `claude/pil-research-0acf20`, repository root; source is `sim/pil/README.md`.
- **One-time setup and run:**
  ```sh
  python3.12 -m venv .venv
  .venv/bin/pip install -r sim/requirements.lock gymnasium==0.29.1 cloudpickle==3.1.2 \
    Farama-Notifications==0.0.6 pyserial
  .venv/bin/python -m sim.pil.run --fake --jobs 6 --out /tmp/pil-fake-01
  ```
- **Expected:** host-compiled fake MCU completes the 160-case panel; `summary.json` and `results.json` report outcomes and Python-vs-PIL differences. Exit 1 indicates a link or numerical error. This checks software/arithmetic in lockstep, not robot balance.
- **Hardware:** Intel Mac only; Pi off; no physical MCU/firmware; BOOT0 out.

### (e) End-to-end advisory replay on the Pi

- **Source/worktree:** run on `wbr-pi5`; script `~/e2e_led_replay.sh` is from `claude2/20261030-e2e-replay`. The final lab runbook is from PR #158. Bags are already recorded; no live camera is required.
- **Starting state:** Pi on; current Nucleo image is `imu_can_bench`. The LED replay requires `link_bench_f446.bin` first. The script's `led` mode backs up, verifies, flashes and starts it. When prompted, fit BOOT0 and press RESET; after GO, remove BOOT0 and press RESET before replay so the LED image boots normally.
- **Commands:**
  ```bash
  ssh wbr-pi5
  bash ~/e2e_led_replay.sh led
  bash ~/e2e_led_replay.sh replay
  ```
- **Expected:** 20 s each for B-H13, B-H05 and S1-empty; each prints sent/echo counts. A prior real-UART run measured **630/630 accepted echoes, zero loss/rejects/unmatched**; LEDs were not visually observed in that run.
- **Hardware:** Pi on; Nucleo on the Pi UART with `link_bench_f446.bin` running and BOOT0 out; `/dev/ttyAMA0` available. The script stops a running micro-ROS agent. No motor commands are involved.
- **Afterward:** the script's `bash ~/e2e_led_replay.sh restore` writes `canfix05`, not the starting `imu_can_bench` image. Reuse of the live MPU6050 demo therefore requires reflashing `imu_can_bench`.

## What each piece teaches

The CAN and RobStride lessons explain what moves over the motor bus; the micro-ROS and firmware lessons trace commands, subscriptions, watchdogs, and advisory boundaries through the MCU. The IMU viewer makes axis conventions, gyro drift, accelerometer error, and complementary filtering visible. MuJoCo demonstrates the assumed LQR response to a push, while fake-MCU PIL separates controller/software parity from physical balance. The Pi replay then exercises the recorded perception-to-advisory-to-UART path and its freshness/echo behavior; the final runbook situates bench work in a repeatable lab sequence.

## Sources used

- `origin/main`: `docs/lessons/*`, `sim/README.md`.
- `origin/claude/wbr-3d-imu-twin-90a9b7`: IMU lesson and `tools/imu_view/README.md`.
- `origin/claude/pil-research-0acf20`: PIL lesson and `sim/pil/README.md`.
- `origin/claude2/20261029-imu-can-bench`: `tools/imu_can_bench/README.md`.
- `origin/claude2/20261030-final-runbook`: final lab runbook (PR #158 per brief).
- `origin/claude2/20261030-e2e-replay`: replay script and 30 Oct result review.
