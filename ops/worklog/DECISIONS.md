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

### D-20261020-5: Start simulation/control exploration with a model and LQR inventory
- Decided by: owner (goal); Codex (first diagnostic step)
- Decision: locate a MuJoCo WBR model and existing LQR baseline before implementing the simulation or training RL. Keep all work in simulation; report unavailable physical parameters and gains as UNKNOWN.
- Why: the inspected perception repository contains no WBR mechanical model or numerical LQR gains; assumed teaching-model results must not be presented as reproduction of the robot baseline.
- Evidence: ops/worklog/sessions/2026-10-20-simulation-control.md; owner request on 2026-10-20; proposed simulation protocol in open PR #36.
- Revisit when: the owner supplies a mechanical/controller source, or explicitly approves a simplified assumed model.

### D-20261020-6: Authorize an ASSUMED teaching model while real controller/model data are requested
- Decided by: owner
- Decision: scope a wheel-legged inverted-pendulum teaching model, derive a new LQR baseline for it, and keep replaceable physical parameters in one config file. Every assumed parameter must have an evidence label, units and an honest source. Existing hardware K, state ordering, sample period, CAD/inertias and motor limits remain UNKNOWN; the owner is requesting them from the lab.
- Why: permit simulation learning without representing invented values or derived gains as the real WBR baseline.
- Evidence: owner's reply on 2026-10-20; proposed architecture and parameter inventory in ops/worklog/sessions/2026-10-20-simulation-control.md.
- Revisit when: real parameters arrive; confirm that they fit the teaching model topology before replacing values. Detailed package/experiment architecture approval is pending before adding sim/.

### D-20261020-7: Audit DM-jump as a source-informed controller reference
- Decided by: owner (source supplied); Codex (audit scope)
- Decision: pin https://github.com/nguyenbinh-shark/DM-jump at 6855ef8c6da20246251cfd473467c04112bf800f and use its executed six-state, two-output, gain-scheduled LQR/VMC equations as the controller reference for planning. The proposed four-state wheel-only model remains a teaching exercise and is not a reproduction of this controller.
- Why: source reveals geometry, runtime gains, state/sign conventions, PID and actuator clamps that were not present in the perception repository. These are SOURCE-SUPPORTED code facts, not measured physical parameters or proof of the lab's flashed firmware.
- Evidence: controller audit in ops/worklog/sessions/2026-10-20-simulation-control.md; source snapshot and arithmetic receipts referenced there.
- Revisit when: lab confirms its deployed commit, parameter provenance, dynamics and gain-synthesis files. Supersedes the unavailable-controller portions of D-20261020-5/6; their physical-data uncertainty and simulation-only boundary remain.

### D-20261020-8: Log every documentation change for Claude review
- Decided by: owner
- Decision: whenever any document is created or revised, record its changed files, rationale, sources, validation, uncertainty and review status in ops/worklog/DOCUMENTATION_LOG.md, linked from the session log. This includes worklog and agent-instruction updates; related edits may share one change-set entry.
- Why: Claude must be able to review how a document changed without reconstructing the conversation.
- Evidence: owner's instruction on 2026-10-20; AGENTS.md; ops/worklog/README.md; DOC-20261020-1.
- Revisit when: the owner changes the documentation-review workflow.

### D-20261020-9: Clarify that the controller audit establishes implementation, not execution
- Decided by: Codex, following independent source-review feedback
- Decision: read D-20261020-7's phrase "executed six-state" as "source-implemented six-state". No controller execution, firmware build, MuJoCo rollout or hardware test was performed in this audit.
- Why: source call-path analysis must not be mistaken for measured runtime evidence. This append-only correction preserves the original entry for audit.
- Evidence: independent documentation consistency review; source-audit limitations in ops/worklog/sessions/2026-10-20-simulation-control.md; DOC-20261020-1.
- Revisit when: actual execution evidence is collected. Supersedes only the execution wording of D-20261020-7, not its source reference or proposed model scope.

### D-20261020-10: Approve a two-stage source-informed simulation architecture
- Decided by: Claude review, relayed and authorized by owner
- Decision: stage 1 is a reduced planar six-state model for source gain parity and explicitly new LQR synthesis; stage 2 is a full planar five-bar MuJoCo model with VMC. The four-state model stays archived.
- Why: preserve the source controller's independent leg/body states and wheel/hip actions before adding closed-chain implementation detail.
- Evidence: owner's review of DOC-20261020-1 on 2026-10-20; current scope in sessions/2026-10-20-simulation-control.md.
- Revisit when: parity or physical-model evidence requires a reviewed architecture change. Supersedes the pending-architecture status in D-20261020-6/7 for these two stages; no implementation or hardware deployment is implied.

### D-20261020-11: Require compiled upstream C versus Python parity
- Decided by: Claude review, relayed by owner
- Decision: locally compile the pinned DM-jump gain-schedule and VMC C functions in an isolated host harness, then compare the Python port on shared test vectors. Repeating formulas in two new implementations is insufficient.
- Why: detect state/sign, numeric, coefficient-order and function-porting errors before physics validation.
- Evidence: DOC-20261020-1 review; source commit 6855ef8c6da20246251cfd473467c04112bf800f.
- Revisit when: upstream functions or the source revision change; preserve source notices and record compiler/options/tolerances and fixtures. This milestone has not run yet.

### D-20261020-12: Prioritize body/leg mass and center-of-mass evidence
- Decided by: Claude review, relayed by owner
- Decision: prioritize body and leg mass/COM data and eventually weighing plus supported balance tests. Until physical data exist, mass sweeps are sensitivity studies only, not parameter identification or sim-to-real validation.
- Why: control response depends on mass distribution; a nominal assumed model cannot establish physical correspondence.
- Evidence: DOC-20261020-1 review and owner measurement request in this session; hardware-availability clarification in D-20261020-15.
- Revisit when: CAD/BOM estimates or physical assemblies become available; label the provenance and uncertainty of each separately.

### D-20261020-13: Check and preserve upstream licensing before code reuse
- Decided by: Claude review (requirement); Codex (source check)
- Decision: the pinned DM-jump root LICENSE states MIT terms. Before copying gain/VMC code, preserve the applicable copyright/permission notices and audit file/upstream provenance; otherwise use a reference to the pinned commit without copying implementation.
- Why: the source audit does not itself authorize stripping notices or imply all third-party files share the root license.
- Evidence: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/LICENSE; SHA-256 e530433beec8b250e0b5cc9668b378875fb58ce904b90268e0ea4df86edcf524.
- Revisit when: copying specific source functions, including code with upstream dmBots provenance. No controller implementation was copied into this repository in the documentation task.

### D-20261020-14: Approve documentation logging and bounded publication
- Decided by: Claude review, relayed and authorized by owner
- Decision: documentation logging is approved; keep new DOC entries about 15 lines with details in session logs. Owner authorizes merging origin/main into this branch, committing/pushing and opening a PR; pre-approves merging it after CI is green only if its diff matches DOC-20261020-1 plus these review decisions.
- Why: make review inexpensive while keeping the publication scope explicit.
- Evidence: owner's DOC-20261020-1 review message; DOC-20261020-2.
- Revisit when: the diff expands beyond the reviewed documentation/decision scope or CI fails. This is not blanket approval for simulation code or hardware deployment.

### D-20261020-15: Physical WBR measurements cannot be requested before assemblies exist
- Decided by: owner (availability clarification); Codex (corrected next step)
- Decision: the owner's physical WBR hardware is not yet available to weigh or balance-test. Record physical body/leg mass and COM validation as unavailable; request CAD/mass properties, BOM and component specifications if obtainable, and label estimates explicitly. Defer physical tests until assemblies exist.
- Why: the earlier weighing request was premature; unavailable measurements must not block source parity or be replaced by invented measured values.
- Evidence: owner's reply on 2026-10-20 to the mass/COM request; D-20261020-12.
- Revisit when: physical assemblies become available. This clarifies the applicability/timing of D-20261020-12 without changing its evidence priority.

### D-20261020-16: Proceed without robot hardware using learner-owned control cores
- Decided by: owner
- Decision: proceed C/Python parity -> assumed six-state model -> matched LQR -> RL; obtain better physical estimates in parallel. Owner writes gain-schedule Python, A/B matrices, LQR solver call and reward. Agents provide TODOs/tests, review and boilerplate, without completing those cores unless asked.
- Why: learn by doing without confusing assumed simulation with physical validation or waiting for unavailable assemblies.
- Evidence: owner's teaching-mode instruction; sim/README.md; sessions/2026-10-20-c-python-parity.md.
- Revisit when: owner changes teaching ownership or new physical/source evidence requires reviewed model changes. Explain each milestone under ten lines with a primary source, then ask two questions and log the checkpoint.

### D-20261020-17: Reserve codex-f for the conductor
- Decided by: owner
- Decision: this session is codex-f; never launch it as a worker. Prefer user-reported Plus aliases codex-g, codex-i and codex-k for explicitly delegated work; check availability first. Do not inspect credentials or change account configuration.
- Why: avoid assigning a worker to the conductor's own account and preserve ownership of learner exercises.
- Evidence: owner's account-label clarification and correction; codex-g read-only review receipt in the parity session.
- Revisit when: owner changes account assignments. Subscription labels are USER-REPORTED, not independently verified.

### D-20261020-18: Conductor owns delegation, independent verification and green-CI merge
- Decided by: owner
- Decision: reserve f as conductor; use idle user-reported Plus g/i/k workers, one task per branch/worktree, Astra ultra for hard work and Sol for simpler work. Workers build/fix/install routine dependencies and submit PRs; conductor reproduces results and merges green CI. Claude only reviews completed milestones.
- Why: run perception and simulation in parallel with explicit ownership and final review rather than intermediate approval round trips.
- Evidence: owner conductor instruction on 2026-10-20; conducting session; AGENTS.md section requested.
- Revisit when: owner changes delegation policy. Supersedes intermediate Claude code-merge review in earlier decisions for this authorized workflow; safety and evidence rules remain.

### D-20261020-19: Afternoon hardware availability limits Pi track
- Decided by: owner (availability); conductor (bounded preparation)
- Decision: no camera this afternoon; available board has 4 GB RAM and a slow 32 GB card. Current SSH target timed out. Prepare existing stereo/ROS offline path while awaiting connectivity; do not claim live camera output. Leave STM32 alone.
- Why: unavailable hardware cannot be replaced by fake poses or historical Pi5 evidence.
- Evidence: owner reply; direct SSH timeout; sessions/2026-10-20-conducting.md.
- Revisit when: Pi SSH reachable and/or camera returns.

### D-20261020-20: Implement running simulation baseline while preserving gain exercise
- Decided by: owner
- Decision: worker implements ASSUMED reduced six-state MuJoCo, new matched LQR and push test now. Protect sim/parity/student.py gain_schedule as learner-only; keep gain/VMC parity explicitly pending rather than treating simulation as source-gain reproduction.
- Why: newest instruction asks for an operational baseline in parallel; unavailable robot and incomplete learning exercise need not prevent assumed-model runs.
- Evidence: owner two-track instruction and named exception; sim worker brief.
- Revisit when: physical data or learner gain port arrives. Supersedes the prior sequencing/ownership restriction only where necessary for this explicit simulation task; no RL or deployment authorized here.
