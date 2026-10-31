# T2 worker run log — 2026-10-30

- Scope: only `sim/twin3d_cmd/**`, `ros2/twin_cmd_bridge/**`,
  `docs/twin3d_cmd/**`. Read CURRENT, USER_PROFILE, sim/AGENTS, T1 model/control/run,
  T1 README/tests, passive IMU viewer and lesson 05 before implementation.
- No T1 changes, renderer/viewer calls, dependency installs, SSH, serial access,
  hardware commands, git metadata writes, commits, pushes or PR operations.
- Python: `~/Desktop/Research/wbr-lab-ops/.venv/bin/python`; MuJoCo physics only.
  `OPENBLAS_NUM_THREADS=1` is an ASSUMED CPU-use setting for these runs.

## Actual physics runs

All values below are **MEASURED in simulation**, not on hardware. Commands
ran from the worktree root with the Python above and one OpenBLAS thread.

| Command suffix after `python -m sim.twin3d_cmd.run_scripted` | Actual outcome |
| --- | --- |
| `--scenario watchdog --check --out docs/twin3d_cmd/runs/watchdog.csv` | Initial 5 s run, exit 1: physics valid; ±0.05 m/s tracking/stop criteria failed |
| `--scenario jump --check --out docs/twin3d_cmd/runs/jump.csv` | Initial 5 s run, exit 0: one edge/cycle, four ignored repeats, flight and landing |
| `--scenario watchdog --check --out docs/twin3d_cmd/runs/watchdog-final.csv` | Revised default 7 s run, exit 0: coarse tracking and settled stop pass |
| `--scenario drive --seconds 3 --check --out docs/twin3d_cmd/runs/drive.csv` | 3000 physics steps, exit 0: coarse tracking passes |

- An 8 s diagnostic Python API run (`run(8, scenario_commands('watchdog'),
  out='docs/twin3d_cmd/runs/watchdog-extended.csv')`) retained the full transient.
- Velocity samples from watchdog: 2.0 s: 0.38018 m/s; 2.5 s: 0.37008;
  2.8 s: 0.35301; 4.0 s: 0.11455; 4.5 s: −0.05317; 5.0 s: −0.08261;
  6.0 s: −0.03201; 6.5 s: −0.01275; 7.0 s: −0.00295; 8.0 s: 0.00142.
- First request is at 0.5 s; last heartbeat is at 2.8 s; watchdog expiration
  is at 3.3 s; slew reaches zero reference near 3.8 s (CALCULATED from the
  ASSUMED 0.5 s timeout and 0.6 m/s² rate). Physical velocity lags and reverses.
- Final checking uses ASSUMED ±0.08 m/s tracking over 2.5–2.8 s and ±0.03 m/s
  stopping over 6.5–7.0 s, after observing the stricter initial failure.
  This is a revised coarse rehearsal criterion, not independent validation or
  a ±0.05 m/s result. Maximum tracking error in that window: 0.0700293 m/s.
- Final watchdog run: 7000 samples, final reference 0, final actual velocity
  −0.00295407 m/s, peak pitch 0.0193048 rad, no warnings/body-floor contact.
- Jump phase transitions: CROUCH at 0.501 s, THRUST at 0.536 s, RETRACT at
  0.617 s, SETTLE at 0.680 s. SETTLE remains latched as in T1. Exactly one
  request starts a jump; four repeats are ignored; both wheels contact at end.
  Tests independently repeat this on a short 3 s flat-ground run.

## Actual failures and fixes

- First unit run: 19 tests, one failure and two socket errors. Bridge: 4 tests,
  one socket error. No graphics were attempted.
- Timeout boundary: subtraction `.7-.2` rounded below `.5` and incorrectly
  accepted an expired jump. Changed deadline checks to `now >= received+timeout`
  / `now < pending+timeout`. Rerun command/physics tests passed.
- Real UDP `socket.bind(('127.0.0.1', 0))` fails in this sandbox with
  `PermissionError: [Errno 1] Operation not permitted` at `udp.py` bind.
  Real socket tests remain present and explicitly skip only this permission
  failure. No substituted socket result is claimed as real delivery.
- Reset implementation initially referenced `mujoco.mj_copyData`; read-only API
  inspection showed `hasattr(mujoco, 'mj_copyData') == False` on 3.3.7 before
  any viewer launch. Replaced it with in-place `mj_resetData`, initial qpos
  assignment and `mj_forward`, preserving the passive viewer's MjData identity.
  A physics test verifies reset and rearming without rendering.
- Pending jump requests now survive velocity-only heartbeats, and duplicate
  pending requests coalesce rather than cancel the first edge. Ignored active
  requests are never queued for a future jump.

## Final verification

Final test and Markdown lint results are recorded with exact commands in
[REVIEW.md](REVIEW.md); raw command outputs are retained under `runs/`.
Socket/graphics/ROS integration remains conductor work, not a completed result.
