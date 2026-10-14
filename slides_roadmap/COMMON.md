# Common rules for every roadmap worker

Goal (owner's words, translated): "A concise but detailed roadmap from where we are now to real
deployment on the WBR robot: the D435i camera running ORB-SLAM3 (and/or other algorithms around
it) integrated into the wheel-biped robot. So I can see what must be done, how, with which
software tools, and which hardware each phase needs. The hardware belongs to the lab, so using
it needs a plan. The road may not be smooth, but I do not want it roundabout: I have little time."

Project facts: read `AGENTS.md`, `CLAUDE.md`, `docs/*.md` (ARCHITECTURE, DECISIONS, PROJECT_STATE,
NEXT_GATE, NEXT_TWO_WEEKS_PERCEPTION_PLAN, D435I_VIO_CALIBRATION_READINESS, RPI5_NATIVE_PERCEPTION_BRINGUP),
`experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md`, `experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md`,
`experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md`, `slides_brief/main.tex` (current status),
`slides_course/main.tex` (gate ladder N0–N7, PASS criteria, Pi/STM32 boundary). Any other repo file may help.
Ownership boundary (fixed): Raspberry Pi 5 owns perception/SLAM/VIO/mapping (non-hard-real-time);
STM32H7 owns balance, LQR, VMC, FSM, motor and jump safety. If the Pi or SLAM fails the robot must
not lose balance. Camera IMU (D435i) and body IMU (STM32) are separate; no naive fusion.

Research: you have web search. Prefer primary sources: papers, official docs, datasheets,
maintainer repos/issues. Every external claim gets a URL. Separate what a source says from your
inference. Mark numbers you could not verify. Do not invent hardware the lab has; when unknown,
say "confirm with lab" and list it as a question for the owner.

Rules: work only in `slides_roadmap/`. No ssh, no installs, no git commands that change anything.
Do not edit other folders. English only. Be decisive: recommend one default path and name the
evidence that would make you switch, instead of listing every option equally.
