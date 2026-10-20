# Decision log

Append-only. Format in `README.md`. Earlier decisions live in `docs/PROJECT_STATE.md`,
`docs/NEXT_GATE.md` and merged PR descriptions.

### D-20261019-1: Single acquisition profile n3_640x480_30
- Decided by: owner
- Decision: IR1+IR2 Y8 640x480 at 30 Hz, gyro 200 Hz, accel 100 Hz, emitter OFF for N2, N3 and calibration.
- Why: resolves the profile conflict between raw, bag and calibration configs (audit, High severity).
- Evidence: PR #32; `lab/d435i_raw/profiles/n3_640x480_30.yaml`, `lab/rosbag_qual/profiles/n3_640x480_30.json`.
- Revisit when: storage qualification or a camera change says otherwise.

### D-20261019-2: 128 GB migration clones the whole 32 GB card
- Decided by: Claude (owner did not object)
- Decision: clone on the Mac with dd + cmp verification; keep the 32 GB card untouched as backup.
- Why: the Pi 5 has one microSD slot; cloning keeps a full rollback.
- Evidence: `ops/lab-assistant/skills/wbr-storage-migrate/SKILL.md` (PR #33).
- Revisit when: never, unless an NVMe/SSD is added.

### D-20261020-1: Lab assistant decides routine lab steps itself
- Decided by: owner
- Decision: ChatGPT Work/Codex decides next steps, retries, one-variable fixes and identity-only session configs; escalates only threshold/code, plan changes, unlocalized failures and gate interpretation.
- Why: avoid round-trips through Claude for routine work.
- Evidence: PR #34, `ops/lab-assistant/INSTRUCTIONS.md` "Decision authority".
- Revisit when: a routine decision causes lost evidence.

### D-20261020-2: Use the D435 for platform checks while the D435i is away
- Decided by: owner (swap); Claude review (card A override)
- Decision: run card A with a session-only thresholds file changing only usb_identity to 8086:0b07. Results count as Pi power/USB evidence with a D435, never as D435i evidence.
- Why: the D435i is in use elsewhere; platform evidence is still useful.
- Evidence: `ops/worklog/sessions/2026-10-20-lab-d435.md`.
- Revisit when: the D435i returns.

### D-20261020-3: Card B stays blocked; no in-session pyrealsense2 install
- Decided by: owner, Claude review
- Decision: do not install the binding or use the C++ RAM recorder as a card B substitute during the lab.
- Why: binding version must match the installed librealsense; the RAM recorder's output does not feed the card B checker.
- Evidence: handoff 2026-10-20 08:29.
- Revisit when: a reviewed binding-install plan exists.

### D-20261020-4: ChatGPT Work is the main agent; Claude reviews
- Decided by: owner
- Decision: ChatGPT Work does most WBR work and records state, decisions and sessions in `ops/worklog/`; Claude is used for reviews via `ops/worklog/reviews/`.
- Why: Claude quota is limited; ChatGPT quota is not.
- Evidence: `AGENTS.md`, `ops/CHATGPT_WORK_SETUP.md`.
- Revisit when: review quality or continuity suffers.
