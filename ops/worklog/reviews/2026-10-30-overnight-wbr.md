# Overnight WBR perception — 30 Oct 2026 (Claude conductor, Codex a/b/c on gpt-6-luna)

1. **24 Oct data integrity: DONE (MEASURED).** SHA-256 of Mac `~/wbr-evidence-archive/mobile-demo-20261024-01` vs Pi `~/wbr-evidence/…`: 180/180 common files identical, 0 differ, 0 Pi-only. 9 Mac-only files are Mac-side derivatives (6 Foxglove-demo MCAPs + layout, LIVE.mcap, T1-rgbd-smoke.mcap; written 12:33–17:46 after the Pi runs). Pi hashed with `nice -n 19 ionice -c3`; read-only both sides. Hash lists: `~/wbr-evidence-archive/overnight-20261030-01/`.
2. **PR #140 LED planner: DONE, with one OPEN finding.**
   - PR already merged 25 Oct (2df00b3), so no rebase was needed.
   - Tests on main: planner 11/11 OK; `make -C tools/link_bench test` PASS.
   - Pi: `~/wbr-demo-20261025` planner/obstacle source identical to main (26 files). colcon build (into /tmp, existing install untouched) PASS in 5.9 s.
   - Planner 10 s on replayed B-H13 / S1-empty depth with a fake fixed pose: alive; 23 / 19 suggestions; core mean 60 / 64 ms, max 94 ms.
   - **OPEN:** the empty scene (S1-empty) is also `BLOCKED`, with obstacle cells about 0.75 m ahead and 0.4 m right. Cause UNKNOWN (fake pose or scene); recheck in P1 with real ORB pose. A SIGINT shutdown logs a harmless publish error.
3. **(a) tracking-state enum: DONE, PR #157.** Wire values now equal ORB-SLAM3 `Tracking.h:121-129` @4452a3c (OK=2, OK_KLT=5, SYSTEM_NOT_READY=255). Unit tests 29 OK; MCU C test + parity PASS. 4 integration failures and 1 flaky PTY error are pre-existing on main.
4. **(b) UNCERTAIN split design note: DONE, PR #159.** Recommends no wire change before the demo. Type 4 already carries `height`/`plane_valid`; only "not yet confirmed" is invisible on the wire.
5. **Final-lab runbook: DONE, PR #158** (`lab-day-20261030/FINAL_LAB_RUNBOOK.md`, 124 lines; all paths checked on the Pi). Two blockers fixed:
   - LED image SHA must be `bf5721b4…03ed`; the `07f0af8d…` in LED_REPORT is stale since d29beae.
   - `path_live.sh` default `PLANNER_SETUP` (ws-20261024) has **no planner**; the runbook overrides it to ws-20261025.
   - Also: the LED image is not on the Pi yet (scp step added).

Limits: no camera or Nucleo used; no flashing, motors or reboot; PRs open, not merged. The runbook's canfix01 banner is UNVERIFIED.

## Wave 2 (00:40–01:10; Codex e/d/g/h, all checked by Claude)
6. **Planner "empty" BLOCKED: DONE, PR #162, not a bug (INFERRED from MEASURED replay).** S1 was a strip ending at a lamp pole (~1.42 m) and wall (~1.60 m), both inside the 3 m goal. Ablation: obstacles kept only before 1.3 m → GO_STRAIGHT. Floor fit 0.293 m / 9.6°. **P1 needs ~3 m of clear floor** (added to the runbook).
7. **Lab fixes: DONE, PR #161.**
   - `path_live.sh` now defaults to ws-20261025; LED_REPORT hash corrected; quiet Ctrl-C in both nodes.
   - Review caught a worker bug, `from rclpy.exceptions import RCLError` (absent on Jazzy), which **crashed the node on the Pi**; fixed.
   - Pi runs: planner 24 suggestions / 0 errors; obstacle node 53 advisories, STOP_CANDIDATE at 0.130 m height.
8. **perception_health integration: DONE, PR #163 (stacked on #157).** 24/24 + 29/29 + MCU PASS. PTY test fixed with a monotonic deadline; e2e fixtures use a test-only age override (cause INFERRED: subprocess startup counted against the 100 ms hold).
9. **Preflight: DONE, in PR #158** (commit 8d38256). Read-only `preflight.sh` run on the Pi: **PASS, exit 0** (WARN: D435i absent). LED image staged on the Pi, SHA verified.
