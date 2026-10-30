# Handoff: Claude 2 → Claude 1 (30 Oct 2026, ~17:30)

The owner is moving coordination to Claude 1. Claude 2's earlier answers to your 9 questions are already reflected below.
Statuses are as recorded in the source reviews. Nothing listed here as "open" is merged.

## 1. Operating rules (owner, standing)
- **Claude plans, dispatches and verifies only. Codex and agy do the work.** The Claude Pro weekly limit is the binding
  constraint: 51 % used at 01:00 on 30 Oct after one night of 4 parallel Claude sessions.
- **Codex accounts** (`codex exec`, one ticket = one worktree + branch, `--sandbox workspace-write`, add `< /dev/null` when backgrounded):
  - **codex-e, codex-k: ChatGPT Plus, default model (no `-m`).** Use them freely, including for hard tasks. Recorded on main in AGENTS.md (PR #167).
  - **codex-a/b/c/d/g/h/j: free plans, need `-m gpt-6-luna`.**
  - Avoid codex-f (the ChatGPT Work coordinator) and codex-i (quota).
  - Check that an account is idle first: `ps eww -ax | grep "CODEX_HOME=$HOME/.codex-X " | grep -v app-server`.
  - Quota error grep: `^ERROR:.*(usage limit|not supported)`. Don't grep a bare "ERROR".
  - Web research: `codex --search exec ...`. The `--search` flag goes BEFORE `exec`.
  - **Sandbox limits:** no network or pip, no `ssh wbr-pi5`, no commit/push from linked worktrees, and no MuJoCo rendering.
    The conductor commits, pushes and does anything that needs the Pi. `--sandbox danger-full-access` is refused by the auto-mode classifier.
- **agy** (`~/.local/bin/agy --model <m> -p "<prompt>"`, with `-p` last):
  - `claude-opus-4-6-thinking` is **out of quota until about 6 Nov** (161 h reset, hit on 30 Oct).
  - Use `gemini-3.8-flash-high` or `claude-sonnet-4-6`; `--effort` is rejected for Opus.
  - It fails inside the Codex sandbox (localhost bind), so run it from a normal shell.
  - It behaves like an agent: name the output file and check that file.
  - It could not read files outside its own directory, so inline the input or copy it in.
- **Per-branch ledger** (PR #180, open): every branch appends one line per finished task to
  `ops/worklog/ledger/<branch>.md`. `ops/secretary/digest.sh` (PR #181, open) aggregates the ledgers and reviews through agy.
- **Owner reads in Obsidian at `~/Desktop/Claude_reports/`** (`00 Index`, `01 Reports`, `02 Lessons`, `03 Research`,
  `04 Lab and Demos`, `attachments`). Copy every new report there with YAML frontmatter (title, date, source, tags)
  and add a link in `00 Index.md`. The owner gave full rights to edit or delete there.
- **Safety:** confirm before flashing (back up first; flashing needs the owner's BOOT0 + RESET), before any Pi reboot
  (ask every running session first), before any deletion, and before force-push. Don't drive motors.
  `gain_schedule` is owner-only. Reply in English, short, and end with exactly one `NEED FROM YOU:` or `NOTHING NEEDED:` line.

## 2. Hardware state now
- **Pi 5** (`ssh wbr-pi5`, 192.168.50.2, Ethernet, no internet; `wbr-pi5-wifi` has internet): on, with nothing running.
  The Pi Camera v2 works (imx219) but is unplugged; the D435i is lab-only.
- **Nucleo-F446RE:** runs `imu_can_bench.bin` (MPU6050 at 115200 8N1; use `stty ... cs8 -parenb -cstopb`, because flashing leaves the port at 8E1).
  BOOT0 is out. Backups: the LED image backup is in `~/wbr-evidence/e2e-replay-20261030/flash-led-065745/`, and canfix05 is verified.
  `~/e2e_led_replay.sh led|replay|restore`. Note that `restore` writes canfix05, not imu_can_bench.
- **Owner's constraints:** GPU = an internet-cafe PC (config PENDING from the owner; likely Windows, no admin rights, wiped at shutdown,
  2–4 h sessions). The owner will buy an AI accelerator themself, but only after the X1 report. The D435i requires a lab visit.

## 3. Facts that changed plans (from your answers)
- The WBR uses **DM-J4310/DM-H6215 on the DM protocol** and has **no micro-ROS** (DM-jump: PS2 + UART). RobStride and micro-ROS are on the **AGV**.
  canfix05 is a 500k bench build, not AGV-ready. Label every plan as WBR path or AGV path.
- **Single parameter source:** team-report masses 3.5/0.2/0.7 kg; five-bar 0.075/0.14/0.08; wheel 0.0603 m. Inertias are ASSUMED.
- **RL was reopened by the owner on 30 Oct** (closed since 22 Oct). The plan is in `research/rl/PLAN.md` (PR #179 branch).

## 4. Work in flight
| Item | Where | State | Next |
|---|---|---|---|
| Bench-twin program T1–T5 | 3D session `local_80657a35…` | T1 #185 PASS in sim (stand 30 s, drive 1.65 m, jump 8 cm 10/10, gate UNCERTAIN in crouch/thrust); T3 #184 combined firmware with 4 fake DM motors (built only); T4 #183 Foxglove; T5 #182 lab-day script | T2 teleop running on codex-k. Then flash T3 (owner BOOT0+RESET) and a live demo |
| RL reopen | `research/rl/PLAN.md` | Plan written by codex-e, not yet reviewed | Review it; the cafe config is needed; portable bundle |
| Capability scouting | `research/explore/x1–x4` | Written, NOT yet checked by Claude | Merge with P1 and RL into a 2–3 program roadmap for the owner (owner wants "wow", multi-axis: CV/AI, RL, SLAM+AI, autonomy) |
| YOLO P1 prototype | `research/explore/p1/` | BLOCKED: no network in the sandbox (pip, model download) or ssh to the Pi | Run it outside the sandbox: install deps, get YOLO11n ONNX, fuse with D435i bag depth, measure Mac and Pi FPS |
| Paper direction | `research/scout/SYNTHESIS.md` | The owner considers the "observation-age contract" only supplementary | Owner decision after reading |
| Course OS/CN | OS repo PRs #7, #10–#15; CN local branch `work/RTP0` | OS-T1/T2 PASS, OS-T3 FAIL (memory/cache contention), OS-T4 bridge FAIL; CN mostly PASS | Course report text later; owner said not now |

## 5. Open PRs to drive (theme batches)
- Lab first: #158 (runbook), #161 (lab fixes), #165 (E2E 630/630).
- Lab second: #157, #159, #162–#164.
- IMU/CAN: #155. Avoid #154 and #156, which overlap on `tools/agv_f446`.
- PIL: #160 (another session's branch).
- Bench twin: #182–#185.
- Research: #179. Process: #180, #181.
- Report: #153. Coordinate with ChatGPT's copy of main.tex.

## 6. Pending owner inputs
The cafe PC config · which report the supervisor last received (and when) · whether the repo is public · the paper/capability choice after the roadmap.

## 7. Key files
- Afternoon report: `ops/worklog/reviews/2026-10-30-afternoon.md`
- Request ledger: `2026-10-30-owner-request-ledger.md`
- Study pack: `research/scout/STUDY_PACK.md` (PR #179)
- All copies are in `~/Desktop/Claude_reports/`.
