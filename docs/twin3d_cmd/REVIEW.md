# T2 completed worker implementation: conductor handoff

Implemented only the allowed directories. No commit, push, PR or render attempt
was made. T1 model/control/run files and the owner-only gain schedule are
unchanged. Real WBR remains PS2 + UART; ROS is labelled throughout as
**AGV-style /cmd_vel rehearsal**. No Pi or hardware was accessed.

## Files and behavior

- `sim/twin3d_cmd/commands.py`: clamped velocity, rate limiter, receiver-clock
  watchdog, one-shot jump requests, held R1 >10-poll adapter, active jump lockout.
- `sim/twin3d_cmd/udp.py`: strict JSON protocol, per-source sequence/timestamp
  checks, nonblocking listener, one-shot or heartbeating sender CLI.
- `sim/twin3d_cmd/teleop_viewer.py`: passive viewer, keyboard/UDP arbitration,
  source/watchdog overlay, in-place reset preserving viewer MjData identity.
- `sim/twin3d_cmd/run_scripted.py`: shared T1 physics step, scripts or paced UDP,
  CSV output, built-in drive/watchdog/jump checks.
- `sim/twin3d_cmd/tests/`: commands, debounce, keyboard/reset, real T1 physics,
  UDP protocol/freshness and three real-socket tests.
- `ros2/twin_cmd_bridge/`: standalone `ament_python` package, lazy rclpy node,
  stdlib forwarder/serializer, four tests and owner-run Pi instructions.
- `docs/twin3d_cmd/`: main README, run log, this review and saved run evidence.

## Commands actually run and results

From the worktree root, using
`PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python` and
`OPENBLAS_NUM_THREADS=1` (ASSUMED CPU-use setting):

| Command | Actual result |
| --- | --- |
| `"$PYTHON" .github/run_unittest.py sim/twin3d_cmd` | Exit 0; 20 discovered, 17 passed, 3 skipped; `runs/tests-sim.txt` |
| `"$PYTHON" .github/run_unittest.py ros2/twin_cmd_bridge` | Exit 0; 4 discovered, 3 passed, 1 skipped; `runs/tests-bridge.txt` |
| `"$PYTHON" -m sim.twin3d_cmd.run_scripted --scenario drive --seconds 3 --check --out docs/twin3d_cmd/runs/drive.csv` | Exit 0; 3000 actual physics steps |
| `"$PYTHON" -m sim.twin3d_cmd.run_scripted --scenario watchdog --check --out docs/twin3d_cmd/runs/watchdog-final.csv` | Exit 0; 7000 steps, final velocity −0.002954 m/s |
| `"$PYTHON" -m sim.twin3d_cmd.run_scripted --scenario jump --check --out docs/twin3d_cmd/runs/jump.csv` | Initial default 5 s; exit 0; 5000 steps, one jump, four ignored requests, flight and landing |
| `python3 tools/lint_markdown.py docs/twin3d_cmd/README.md docs/twin3d_cmd/RUN_LOG.md docs/twin3d_cmd/REVIEW.md ros2/twin_cmd_bridge/README.md` | Exit 0; 0 issues across 4 files |

All four skipped tests encountered a real `socket.bind()` denial:
`PermissionError: [Errno 1] Operation not permitted`. They remain real-socket
tests and must execute outside this sandbox. No socket delivery has passed
here. The serializer/protocol/freshness tests and simulated physics did pass.

`runs/summary.json` contains CALCULATED checks on the saved MEASURED simulation
CSVs. The initial 5 s watchdog check failed ±0.05 m/s tracking/stopping and is
preserved in `runs/watchdog.csv`. The revised ASSUMED tracking tolerance is
±0.08 m/s (coarse, 26.7% of request) two seconds after the first request; the
stop tolerance is ±0.03 m/s over 6.5–7.0 s. The maximum tracking error is
0.0700293 m/s. These are revised criteria informed by the failed run, not
independent validation. No T1 tuning occurred. See [RUN_LOG.md](RUN_LOG.md).

## Exact conductor commands still needed

From this worktree, outside the restricted sandbox, run both suites and require
**zero skips** before claiming localhost delivery validation:

```sh
cd ~/Desktop/Research/wbr-wt-t2-command
export PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
export MJPYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/mjpython
export OPENBLAS_NUM_THREADS=1
"$PYTHON" .github/run_unittest.py sim/twin3d_cmd
"$PYTHON" .github/run_unittest.py ros2/twin_cmd_bridge
python3 tools/lint_markdown.py docs/twin3d_cmd/README.md docs/twin3d_cmd/RUN_LOG.md docs/twin3d_cmd/REVIEW.md ros2/twin_cmd_bridge/README.md
"$MJPYTHON" -m sim.twin3d_cmd.teleop_viewer --host 0.0.0.0
```

In a second terminal, while the viewer is open:

```sh
cd ~/Desktop/Research/wbr-wt-t2-command
export PYTHON=~/Desktop/Research/wbr-lab-ops/.venv/bin/python
"$PYTHON" -m sim.twin3d_cmd.udp send --v 0.3 --seconds 3
"$PYTHON" -m sim.twin3d_cmd.udp send --jump
```

Verify actual OS Up/Down/W/S input, Space jump, repeated Space lockout, R reset
and rearm, overlay, source changes, watchdog after sender loss, Esc/window
close. Reset before testing the UDP jump if Space already started a jump.
The UDP jump command without `--v` also writes velocity zero.

After closing the viewer, exercise the headless UDP CLI in terminal A:

```sh
"$PYTHON" -m sim.twin3d_cmd.run_scripted --udp --seconds 8 --out docs/twin3d_cmd/runs/conductor-udp.csv
```

Immediately send from terminal B:

```sh
"$PYTHON" -m sim.twin3d_cmd.udp send --v 0.3 --jump --seconds 2
```

Inspect accepted/rejected counts and CSV source, edge count and stale braking.
The four real-socket unit tests also cover sender-to-listener delivery, stale
and duplicate rejection, bridge protocol interoperability and paced UDP physics.

After conductor validation, record actual results in this file and stage only
the allowed paths. These commands are for the conductor, not this worker:

```sh
git add -- sim/twin3d_cmd ros2/twin_cmd_bridge docs/twin3d_cmd
git commit -m "Add T2 physics twin command interfaces and AGV-style ROS rehearsal"
git push -u origin chatgpt/20261030-t2-command
gh pr create --base main --head chatgpt/20261030-t2-command --title "T2: command interface for the physics twin" --body-file docs/twin3d_cmd/REVIEW.md
gh pr checks --watch
```

The Pi `colcon`, `ros2 run` and `teleop_twist_keyboard` commands are supplied in
the [bridge README](../../ros2/twin_cmd_bridge/README.md) for the owner to run
later. No SSH command is needed or authorized for this worker handoff.

## Limitations and review recommendation

- Rendering, OS key delivery, viewer overlay and actual network/ROS runtime are
  unverified. Physics and headless keyboard logic do not validate rendering.
- T1 `SETTLE` is latched. R/reset is deliberately the only rearm; T2 does not
  invent a contact-based transition or modify source controller behavior.
- The R1 hold adapter adds a release requirement, explicitly ASSUMED; it does
  not claim exact source retrigger parity. No UART framing/scaling was invented.
- Coarse tracking and delayed settling are visible; the first tighter check
  failed. T2 is a command rehearsal, not hardware performance/safety evidence.
- UDP has no delivery guarantee/authentication, assumes synchronized wall clocks
  for packet-age checks, and uses `src` as a sequence namespace. Runtime
  watchdog freshness is receiver-monotonic and independent of sender timestamps.
- Recommendation: run the conductor commands above and retain actual socket/
  viewer results before completing the integrated T2 milestone. Leave Pi ROS
  rehearsal for the owner's later bench session.

Claude review line after conductor validation: **Review T2 command policy,
AGV/WBR labelling, revised tolerance evidence and conductor integration results
in `docs/twin3d_cmd/REVIEW.md`; T1 controller and hardware remain unchanged.**
