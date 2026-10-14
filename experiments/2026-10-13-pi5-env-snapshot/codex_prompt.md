You are inspecting the WBR Phase-1 perception runtime environment. READ-ONLY review except for writing ONE file.

Inputs (all local; do NOT ssh to the Pi, do NOT run hardware commands, do NOT install anything):
- AGENTS.md, CLAUDE.md, README.md
- docs/PROJECT_STATE.md, docs/NEXT_GATE.md, docs/ARCHITECTURE.md, docs/DECISIONS.md, docs/EVIDENCE_INDEX.md, plus other docs/*.md as needed
- experiments/ (earlier evidence)
- experiments/2026-10-13-pi5-env-snapshot/snapshot.txt  (read-only snapshot of the Pi taken 2026-10-13 by snapshot.sh in the same folder)

Context (from the user/session, treat as facts unless the snapshot contradicts them):
- The Pi (wbr-pi5, Raspberry Pi 5 4 GB, temporary stand-in for the 8 GB) boots from a 32 GB microSD. No NVMe/SSD is attached.
- The card also carried a separate OS-course project from late Sep to Oct 12; its folders were backed up and left in place (~/osbuild, ~/heterogeneous-edge-ai-os, ~/os-project-setup). Its leftovers include lttng-sessiond running, os-wifi-priority.service, /etc/sudoers.d/os-project-agent.
- The Pi clock had no NTP on the direct Ethernet link and was previously ~3 days behind.
- At snapshot time the D435i was NOT plugged in.
- The user now intends to run only the Intel D435i camera work next.

Task: write experiments/2026-10-13-pi5-env-snapshot/CODEX_INSPECTION.md containing:
1. Current state of the Pi environment vs what the repo docs claim (driver/ROS/udev/workspaces/storage/power/clock). Mark each item MEASURED (in snapshot), SOURCE-SUPPORTED (in repo docs/evidence), INFERRED, or UNKNOWN.
2. Discrepancies between docs/PROJECT_STATE.md / docs/NEXT_GATE.md and the actual Pi state.
3. Anything from the OS-course project that could contaminate D435i/N3 measurements (CPU governor, background daemons, sudoers, services, packages) and whether it matters.
4. Risks: storage headroom for rosbags on the 32 GB card, under-voltage history (get_throttled), clock/timestamp trust.
5. The first unresolved N3 condition according to the evidence, and the minimum discriminating next test (exact commands, expected output, decision rule). Do not declare any gate PASS.
6. Explicit list of what you could not verify.
Keep it under ~200 lines. Do not edit any other file.
