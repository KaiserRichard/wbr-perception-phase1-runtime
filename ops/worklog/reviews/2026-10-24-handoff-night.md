# Handoff — 2026-10-24 night (Claude 2, before the owner switches account)

Read this first in the next session. Owner assigns Claude 2 directly; reviews go to
`ops/worklog/reviews/` on pushed branches.

## State
- Merged to main today: PR #132 (detector), #133 (Pi→Nucleo UART link, hardware tested),
  #135 (live chain), #136 (CI deps), #137 (Monday checklist: A1 15 Hz + ORB, journalctl),
  #138 (local map from a real bag), #139 (ORB checks for L1/M1). CI runs stay pending
  (GitHub Actions billing).
- Open: PR #134 (Foxglove demo converter; the owner's screenshot shows the layout renders —
  ready to merge), PR #140 (`claude2/20261025-led-planner`).
- PR #140: Nucleo LEDs (D4 PB5 green NONE, D5 PB4 yellow JUMP, D6 PB10 red STOP, D9 PC7
  blue UNCERTAIN; stale/no link blinks red 2 Hz; prebuilt SHA-256 07f0af8d…; NOT flashed)
  + `ros2/wbr_planner_node` (live lateral-shift planner from ORB pose + local map) +
  `lab-day-20261025/path_live.sh` + `LED_WIRING.md`. codex-e reviewed (2 blockers, 5 major,
  2 minor in planner/script; firmware clean); codex-d fixed all with regression tests
  (11 pass, commit d876580). Live run on the Pi not done yet.
- 24 Oct lab data: on the Pi `~/wbr-evidence/mobile-demo-20261024-01/`; copy to
  `~/wbr-evidence-archive/mobile-demo-20261024-01/` with SHA-256 check was started at
  19:00 over Ethernet (`ssh wbr-pi5`, 192.168.50.2; the Pi has no internet on that link).
  Verify the checksums before relying on the copy.
- Pi deploy started: code rsynced to `~/wbr-demo-20261025` (revision in GIT_REVISION),
  workspace `~/wbr-demo-ws-20261025` (planner + obstacle node). Check the colcon build and
  a 10 s planner start (`/tmp/planner-start.log`) before the lab.

## Next lab session (camera borrowed, owner can go any day)
Order: M1 lab map 180 s (stereo, handheld) → L1 3.00 m line → A1 RGB-D + ORB approach →
LIVE camera→Pi→Nucleo with LEDs → P1 path test (floor, 3 m course, box in the middle,
`path_live.sh`, Foxglove on the Mac). Checklists: `lab-day-20261026/CHECKLIST.md`,
`lab-day-20261025/LED_WIRING.md`. RGB-D always 15 Hz (microSD sustained 56.3 MB/s).
Bench firmware baud 460800. LIVE does not record a camera bag: run `record.sh rgbd` in parallel.
Flash the LED firmware only after the owner says go (backup of the OS-project firmware:
`~/wbr-evidence-archive/nucleo-backup-20261024/`).

## Open decisions for the owner / Claude 1
- STM32H7 firmware owner must review TerrainAdvisory (fields, 300 ms stale, response policy).
- `tools/perception_health/SPEC.md` tracking enum is off by one vs ORB_SLAM3 Tracking.h.
- UNCERTAIN mixes "not confirmed yet" and "below the jump band"; split into LOW later?
- Planner on the Pi next to ORB-SLAM3: CPU load unmeasured (path_live.sh logs cpu.log).
