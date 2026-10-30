# Brief 2 (2026-10-30): synthesis and study pack. The owner starts reading at ~14:00

The rules from BRIEF.md still apply: English, no invented citations, keep evidence statuses, don't commit, edit only your own file.

**S1, codex-e** writes `research/scout/SYNTHESIS.md` (max ~120 lines).
- Read t1–t4.
- Open and check at least the 8 most important citations, and mark each as checked.
- Rank 3 paper directions. For each give:
  - the research question (one sentence);
  - the claimed contribution;
  - the closest prior work and the real difference from it;
  - the experiments needed, marked before-robot or after-robot;
  - the reusable evidence already in the repo;
  - the best venue and its deadline;
  - effort in weeks and the main risk.
- Give an honest recommendation for the first paper, and say why the other two are not first.
- Add a reading list of at most 10 papers in reading order, one line each on why.

**S2, codex-h** writes `research/scout/STUDY_PACK.md` (max ~100 lines). Use `git fetch` and `git show origin/<branch>:<path>`; never check out.
1. Reading order for the in-repo lessons. Use only existing files: `docs/pil/LESSON.md` (branch `claude/pil-research-0acf20`), `docs/imu_view/LESSON.md` (`claude/wbr-3d-imu-twin-90a9b7`), `docs/lessons/` on main, the IMU/CAN README, `lab-day-20261030/FINAL_LAB_RUNBOOK.md` (PR #158). Give the time per item.
2. Demos and simulations the owner can run alone on an Intel Mac and the bench, each with:
   - its exact commands, copied from the README files;
   - the branch or worktree to run it from;
   - the expected result;
   - the hardware state needed (BOOT0 out, which firmware is flashed, Pi on or off).

   The demos:
   - (a) 3D WBR viewer in fake mode;
   - (b) 3D WBR viewer with the live MPU6050 (stty `cs8 -parenb -cstopb`);
   - (c) MuJoCo LQR push recovery from `sim/`;
   - (d) processor-in-the-loop with the fake MCU (`sim/pil`);
   - (e) the end-to-end advisory replay on the Pi (`~/e2e_led_replay.sh`). The LED image must be reflashed first, because the Nucleo currently runs `imu_can_bench`.
3. A one-paragraph "what each piece teaches you".
