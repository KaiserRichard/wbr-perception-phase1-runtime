# Claude 1 Handoff to Next Claude Coordinator

## 1 Rules
- Claude plans and verifies. Codex and agy execute tasks.
- Account allocation: codex-e and codex-k use Plus. Other Codex workers use -m gpt-6-luna.
- Do not use codex-f (ChatGPT Work) or codex-i (quota). Check idle with ps before assigning; codex-b was busy at 17:15.
- agy Opus is out of quota until ~6 Nov.
- Safety: Ask owner before flash, Pi reboot, delete, or force-push.
- Flashing safety: Always tell owner to REMOVE BOOT0 after RESET.
- PRs: Owner permitted Claude to run gh pr merge on reviewed green PRs.

## 2 Hardware state now
- Nucleo runs T3 bench_twin v2 (sha 37cb50dd) with BOOT0 removed.
- CAN1<->CAN2 was rewired 30 Oct. imu_can_bench check is 10/10 PASS after reseat.
- T3 performance: 100 cmd/s steady, 99 sent and fed back per s, 0 lost, 0 CAN errors, ~1.2 ms latency.
- Host seq must increase across runs. Firmware rejects old seq numbers.
- Flashing uses ~/imu-can-bench/flash_safe.py via Pi /dev/ttyAMA0.
- Pi bootloader sometimes NACKs get_id on first RESET; just retry.
- Firmware backups on Pi are in ~/wbr-evidence/t3*-flash-*/flash-backup.bin and icb-restore-*.

## 3 Done today (with PR numbers)
- Merged PR #161.
- Merged PR #158 (restore = exact Step 0 readback, SHA-checked).
- Merged PR #165 (real-UART replay gated, nonzero exit on bad echoes).
- Merged PR #184 (T3 bench twin firmware v2: 460800 UART, all RX drop counters, M decimation, pi_loop.py).
- Opened PR #186 (research: RL review, 2-program roadmap, citation check 57/64 verified, P1 YOLO FPS). PR is green and contains #179 commits.
- Benchmarked P1 YOLO11n 640 ONNX CPU: Mac 22 FPS (pipeline 18.8), Pi 5 3.4 FPS (4 thr), 2.4 FPS (1 thr). Books in B-H05 never detected.
- Built portable Windows RL bundle from branch claude1/20261030-rl-review to ~/wbr-evidence/c1-20261030/WBR-RL-BUNDLE (unverified until run).

## 4 In flight and next actions in priority order
1. Merge PR #179 and PR #186
   - Owner/Worker: Next Claude coordinator.
   - Done-criteria: Spot-check PR #179, merge PR #179, then merge PR #186 into main.
2. Commit T2 teleop and run live demo
   - Owner/Worker: the 3D session owns this tree; check with it before committing (codex-k finished, output uncommitted).
   - Done-criteria: Commit uncommitted output in /Users/quockaiser/Desktop/Research/wbr-wt-t2-command, open PR, merge it, and demo T2 driving T3.
3. Test Windows RL bundle on borrowed laptop
   - Owner/Worker: Owner (run) and Next Claude coordinator (verify).
   - Done-criteria: Borrow brother's laptop (i7-11800H 8c/16t, 32 GB, RTX 3060 6 GB). Run session 1 (~2.5 h: 10 min smoke + 1 PPO v2 seed ~1.5-2 h). If faster than Mac (~450 s/process ref), run session 2 overnight (~8-10 h for 5 seeds). Return laptop.
4. Review second batch of lab PRs
   - Owner/Worker: codex-d (-m gpt-6-luna).
   - Done-criteria: Review and merge green PRs: #157, #159, #162-#164, #155 (IMU/CAN), #180, #181 (process), #153 (report), #160 (PIL).

## 5 Pending owner inputs
- Confirm if repository should be made public.
- Provide supervisor's last report.
- Choose paper versus capability direction from research/explore/ROADMAP.md.

## 6 Key paths
- Logs and evidence: ~/wbr-evidence/c1-20261030/ (logs t*.log, p1-run/, WBR-RL-BUNDLE/)
- Flash tool: ~/imu-can-bench/flash_safe.py via Pi /dev/ttyAMA0
- Firmware backups: ~/wbr-evidence/t3*-flash-*/flash-backup.bin and icb-restore-* on Pi
- T2 teleop tree: /Users/quockaiser/Desktop/Research/wbr-wt-t2-command
- Worktrees: ~/.worktrees/wbr-c1-rl-review, ~/.worktrees/wbr-c1-roadmap, ~/.worktrees/wbr-c1-prreview
- Cafe compute decision: ops/worklog/reviews/2026-10-20-cafe-compute-strategy.md (Cho Mo x3 only)
- RL bundle source: branch claude1/20261030-rl-review, research/rl/bundle (run.bat, resume.bat, CHECKLIST.md)
