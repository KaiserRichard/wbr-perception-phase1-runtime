# Handoff prompt: Claude 1 → Claude 2 (31 Oct 2026, ~18:45)

You are taking over coordination of the owner's WBR + OS-course work from Claude 1. Read this fully, then continue. Reply in English and keep messages short. End every message with exactly one `NEED FROM YOU:` or `NOTHING NEEDED:` line.

## Rules (owner, standing)
- Claude plans, dispatches and verifies; Codex and agy do the work. codex-e and codex-k are Plus (no `-m`; codex-e's weekly quota resets 1 Nov 08:53, so spend it). Free accounts need `-m gpt-6-luna`: c, a, j and b are freshest; d, g and h are 74–85 % used. Avoid codex-f and codex-i. Check an account is idle first: `ps eww -ax | grep "CODEX_HOME=$HOME/.codex-X "`. agy has Gemini only (`gemini-3.8-flash-high`); its Claude models come back around 6 Nov. agy writes logs and reports.
- When watching for a job with `pgrep -f`, use a bracket pattern (`'Ticket X[Y]'`) so the watcher doesn't match itself. Two watchers got stuck on 31 Oct because of this.
- No jobs left running overnight: the owner closes the Mac. `caffeinate -d -i -s -t <sec>` while the owner is awake.
- Ask before flashing, rebooting the Pi, deleting anything or force-pushing. Merging reviewed, green PRs is allowed.
- **Report review mode:** while the owner comments on a PDF, only COLLECT the comments in `review_next/OWNER_COMMENTS_v*.md`, and apply them in one batch when the owner says "xong".

## 1. WBR supervisor report (Vietnamese is the priority)
Folder: `~/Desktop/30:10 video /WBR_Phase1_Report/` (note the colon and the trailing space). Versions: `report_vi_v3/` (current, 11 pages), `report_vi_v2/`, `report_vi/`, `report/` (English, older).
- Title: "Wheel-Biped Autonomy: Visual-Inertial SLAM with ORB-SLAM3". Audience: the supervisor and a senior teammate. Purpose: show what was built and learned, and the potential of the direction, in a concise, modest tone. No self-promotion, no skills section, no timeline, no "minh chứng" lines (only "Video demo: <name>" linked to the Drive folder https://drive.google.com/drive/folders/1g8vi4wmHtbJAhe8nm_MJynogYDxjnhWM), no meeting proposals, no internal file names. Acronyms expanded once in English (MCU (Microcontroller Unit)); product names are not explained. Diagrams are black and white with orthogonal lines only.
- **Pending batch:** `review_next/OWNER_COMMENTS_v3.md`, items 1–10 so far. The owner has NOT said "xong" for v3 yet. Earlier rules are in `OWNER_COMMENTS.md` and `OWNER_COMMENTS_v2.md`.
- Images: `review_next/owner_images/fig_4_1_signal_chain_chatgpt.png` is APPROVED (section 3.1). The 3-panel "same obstacle signal, different meaning" image is waiting for the owner's corrected version (the robot must be about 35–40 cm, knee height of a person). An EuRoC sample image is also waiting on the owner. `review_next/CHATGPT_IMAGE_PROMPTS.md` holds the prompts.
- Open question to the owner: RAM of the bench Pi (8 GB in the docs, 4 GB mentioned for the EuRoC run).
- After the Vietnamese version is final, mirror it to English.

## 2. OS course midterm report
Worktree `~/.worktrees/OS-wt-report`, branch `docs/os-midterm-20261031`, PR KaiserRichard/heterogeneous-edge-ai-os#16. File `report_vi/BaoCao_HDH_Nhom3Stars_GiuaKy.docx` (built from `content.md` by `build_docx.py`).
- Measured results are in `report_vi/pi_results/`. OS-T1 PASS (30 fps on 30 Oct + 10 fps rerun on 31 Oct). OS-T2 PASS (31 Oct rerun with the performance governor; 2 threads, P99/P50 = 1.27). OS-T3 and OS-T4 FAIL. One failed T2 attempt on 31 Oct was deleted by mistake; this is disclosed.
- Running: **OS-WIRING** on codex-a (log `~/wbr-evidence/c1-20261031/OS-WIRING.log`) draws the bench wiring/pinout (Pi 5 + Pi Camera v2 on CAM/DISP 0 + Nucleo UART + LEDs + MPU6050) with Claude 2's `make_breadboard.py` method, inserts it into `content.md`, and leaves 2 placeholders for the owner's photos (full setup, camera close-up). Verify its pins and any UNVERIFIED items, then commit to the PR.

## 3. RL G1 experiment
Branch `claude1/20261031-rl-g1` (pushed, no PR yet). Code in `sim/rl/g1/`; 15 tests pass with `source /private/tmp/wbr-g1-env.sh` (the dependencies live in `/private/tmp`, which is fragile; reinstall into a proper venv if it's gone). Mac: 338.8 steps/s single, 416.6 aggregate with 5 jobs (about 4.7 h for the full run).
- Package for the owner: `sim/rl/g1/cloud/` (`g1_code.zip`, `kaggle_g1.ipynb` for seeds 0,1,2; `colab_g1.ipynb` for seeds 3,4; `CLOUD_README.md`). The owner has a Kaggle account and is about to run it. When the outputs come back, run `python -m sim.rl.g1.merge_runs --parts ... --out ...`, then the final evaluation, and report against the preregistered PLAN-v2 thresholds (`research/rl/PLAN-v2.md`).

## 4. Hardware state
The Pi 5 is on (Ethernet, `ssh wbr-pi5`) with the camera on CAM/DISP 0, governor `ondemand`. The Nucleo runs T3 bench_twin v2 (sha 37cb50dd). The CAN wiring was reseated on 30 Oct; imu_can_bench passed 10/10 after that.

## 5. Other open items
Owner to close PR #155 (redundant). #153 (27 Oct report) is superseded by the new report. #160 (PIL) belongs to another session. Branches without PRs: `claude1/20261030-coord` (ops notes, ticket queue). Ticket plan: `ops/tickets/2026-10-31/README.md` on that branch.
