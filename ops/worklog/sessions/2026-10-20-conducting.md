# Conducting Codex: parallel Pi and simulation

Started: 2026-10-20 13:29 +07; conductor codex-f. Branch chatgpt/20261020-conducting, initial origin/main 5b6ab4e.

## Plan and boundaries
- Architecture: existing Pi stereo/ROS wrapper; ASSUMED reduced planar six-state MuJoCo/new LQR on Mac. Full five-bar remains later, no RL now.
- Files: AGENTS conducting rules, shared worklogs, workers limited to scoped module files/session logs.
- Risks: absent camera/Pi SSH, guessed physical properties, worker overlap. Separate branches/worktrees, bounded runs, one physical owner; no deletion or STM32/motors.
- Rollback: leave feature branches/worktrees intact, revert reviewed commits via new PR if necessary; no resets/history rewrite or shared-checkout branch changes.
- Existing dirty files were generated host-test binaries/dSYM/.build from prior full suite; preserved and excluded from commits.

## Dispatch
- Before launch, g/i last session task_complete at 2026-10-20T01:39Z; no active task children. Persistent app-server daemons alone were not counted as active work. k has interactive CLI PID30573 in Desktop/CN; skipped. f conductor reserved.
- g/i are USER-REPORTED Plus; no auth files inspected. Local models cache confirms gpt-6-astra supports ultra; launch headers confirm selected model/effort.
- Managed worktree g: /Users/quockaiser/.codex/worktrees/pi-orbslam-pose/wbr-lab-ops, chatgpt/20261020-pi-orbslam-pose.
- Managed worktree i: /Users/quockaiser/.codex/worktrees/sim-lqr-push/wbr-lab-ops, chatgpt/20261020-sim-lqr-push.
- Both launched gpt-6-astra ultra, one CLI/task; no extra account workers or subdelegation.
- Briefs/logs: /private/tmp/wbr-conducting-20261020/{pi,sim}-brief.txt and {pi,sim}-events.log. Briefs contain goal, allowed paths, exact success requirements and prohibitions.

## Actual results so far
- Owner: no camera this afternoon, only 4GB Pi, slow32GB microSD and STM32. Live camera milestone deferred. Requested powered/Ethernet/SSH address while preparation continues.
- Conductor SSH wbr-pi5 ConnectTimeout8: exit255, timeout192.168.50.2:22. No Pi mutations.
- Main now 5b6ab4e includes requested bringup skill; read it fully. Main changed documentation policy, but owner's latest pasted instructions still require decisions/documentation log; continue logging.
- Integrated prior parity branch locally; CURRENT conflict resolved to latest hardware and new conducting scope, preserving prior evidence references. Original commits retained; no learner implementation.
- Further checks, publication, CI and independent worker verification pending.

## Documentation changes
- CURRENT reconciles latest hardware and parallel work; DECISIONS appends D18-D20; this session and DOC7 record role/source/limits.
- AGENTS requested Conducting Codex section will be logged with publication; no milestone review until a real run completes.

- Implemented owner's requested Conducting Codex section in AGENTS; aligned older Claude/logging text so it no longer contradicts this role. Worker briefs already carry these instructions.
- Conductor reruns parity scaffold tests before merge; no Python learner code edited.
