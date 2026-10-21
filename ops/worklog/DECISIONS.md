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

### D-20261020-21: Defer Pi track and prioritize Mac simulation
- Decided by: owner
- Decision: prioritize other work while the only available card is slow; conductor stopped Pi worker and continues MuJoCo/LQR/push verification. No camera available; no storage change, Pi build or live-pose claim.
- Why: owner explicitly redirected effort after cafe Wi-Fi restored SSH; simulation runs independently on the Mac.
- Evidence: owner messages on 2026-10-20; conducting session records discovery and interrupted worker.
- Revisit when: owner resumes Pi work with suitable hardware/storage. Cafe SSH endpoint richard@wbr-pi5.local192.168.111.243 was measured, not guaranteed stable across networks.

### D-20261020-22: Approve nominal baseline; add causal actuator and sensor imperfections before RL
- Decided by: Claude review, relayed and authorized by owner
- Decision: nominal LQR baseline approved in PR44. Add configurable 2-5ms control delay, first-order torque lag and body IMU noise; rerun unchanged protocol/K first. Re-synthesize with delay state only if a frozen-gain case fails. Then train/evaluate RL on the identical plant/pushes across several seeds.
- Why: reviewed baseline is correct but delay is a known weak point; avoid comparing RL against an unrealistically instantaneous controller.
- Evidence: ops/worklog/reviews/2026-10-20-lqr-mujoco.md Claude section, main417c1e2; owner request.
- Revisit when: real actuator/sensor data replace assumptions. Pi waits for camera; gain_schedule remains owner-only.

### D-20261020-23: Keep this afternoon's learning material concise
- Decided by: owner
- Decision: provide one short LQR-to-RL guide with equations, code links and small exercises, not an elaborate document. Camera lab resumes when equipment is available tomorrow.
- Why: owner wants to study LQR/RL this afternoon and explicitly requested short practical notes now.
- Evidence: docs/learning/LQR_RL_GUIDE.md; AGENTS.md; owner's latest learning/document instructions.
- Revisit when: owner requests deeper material. Avoid solving protected gain exercise.

### D-20261020-24: Concise teaching must still explain the mathematics
- Decided by: owner
- Decision: replace the overly skeletal guide with rendered Markdown mathematics, coordinate/energy/force derivations, state linearization/LQR explanation and a worked numerical example. Brevity is not a fixed line limit.
- Why: owner found code-formatted equations and unexplained formulas unreadable and superficial.
- Evidence: owner feedback; revised docs/learning/LQR_RL_GUIDE.md and AGENTS.
- Revisit when: owner requests deeper details; this clarifies D23 without rewriting it.


### D-20261020-25: Prioritize codex-b while preserving shared-account availability
- Decided by: owner; conductor availability check.
- Decision: prioritize codex-b until its owner-reported expiry tomorrow, then other available approved accounts. Reserve f for conductor; use Astra Ultra for hard implementation and Sol for simpler work. Never interrupt another project to free an account.
- Why: use the owner's remaining account availability without overlapping shared work.
- Evidence: owner instruction; b lifecycle at 07:45:04Z is task_started in a different worktree, with no completion at 07:50Z. Earlier g/i/k worker runs hit usage limits; no Free fallback was launched.
- Revisit when: b is idle or the owner changes priorities. Expiry/subscription status is owner-reported.

### D-20261020-26: Freeze conditional delay-aware LQR for the PPO comparison
- Decided by: conductor, following D-20261020-22 and the predeclared protocol.
- Decision: use the unchanged-Q/R conditional delay-specific LQR gains for every RL comparison condition. Preserve nominal-gain failures; no per-episode controller selection or retuning.
- Why: original K failed settling/recovery in all 40 controlled cases; conditional gains passed all 40 across delays 2/3/4/5 ms and seeds 0..4. No controlled fall occurred.
- Evidence: complete conductor run at /private/tmp/wbr-actuator-conductor-20261020-05, source 0900606; 27/27 tests passed; 373 artifact hashes verified and paired noise hashes matched.
- Revisit when: the plant or frozen protocol changes. These are assumed-model simulation results, not hardware evidence or gate promotion.


### D-20261020-27: Make owner-facing next actions explicit
- Decided by: owner.
- Decision: every message ends with exactly one NEED FROM YOU line (one physical action or decision) or NOTHING NEEDED line (next agent action). Recommendations belong only in review files.
- Why: make required owner input immediately clear and keep routine work moving.
- Evidence: owner's communication rule on 2026-10-20; updated AGENTS.md.
- Revisit when: owner changes this format. Supersedes earlier recommendation-in-message instructions.


### D-20261020-28: Transfer conducting role to codex-b after account switch
- Decided by: owner.
- Decision: this chat now conducts as codex-b. Do not launch b as a worker; use idle owner-authorized g/i/k when useful. Preserve earlier f-conductor history as historical evidence.
- Why: owner switched accounts and explicitly asked to continue the existing project.
- Evidence: owner's latest instruction; project, five final checkpoints and running/completed evaluation remained available. AGENTS updated.
- Revisit when: owner changes account roles. Check idle status before each worker launch and never interrupt unrelated shared work.

### D-20261020-29: Retain the completed negative PPO comparison without retuning
- Decided by: conductor under the predeclared experiment and owner workflow.
- Decision: record LQR160/160 versus PPO0/800 successes after five complete150000-step policies; retain680 falls,120displacement exits and all checkpoints/raw data. No reward, acceptance or budget change, extra training or best-seed selection.
- Why: completed optimizer execution is distinct from a successful learned controller; this fixed recipe did not solve the task. The prescribed interval is conditional on these seeds and panel.
- Evidence:source608222b, full-run COMPLETE exit0; independent6680-hash/750000-step/960-slot/noise-pair audit and archived aggregate. sim/rl/RESULTS_2026-10-20.md.
- Revisit when: Claude reviews the completed milestone and a new experiment is explicitly predeclared; no sim-to-real/general-RL conclusion is drawn.


### D-20261020-CAFE: Apply the owner-relayed compute review
- Decided by: owner relaying Claude review of the Cho Mo strategy, commit425b682/PR54.
- Decision: one bounded Training Station MuJoCo pilot morning, one v2 seed, setup+export<1h; free Mac/lab training first once conductor verification completes. Initial deposit at most100–200k; no500k–1m deposit or Isaac migration. Later Isaac is learning only, conditional on staff/persistence arrangements.
- Why: current workload uses CPU physics/small policy; shutdown resets local state. CPU-cloud comparison, not GPU rental, is relevant if a measured resource need appears.
- Evidence:ops/worklog/reviews/2026-10-20-cafe-compute-strategy.md, owner review and active v2 state at43f7f6f. Cafe speed/restoration figures are estimates, not measurements.
- Limits:reported100–200k tier is x2, not x3; Training Station cash-equivalent rate12100VND/h, six hours72600, subject to staff terms. Larger deposit needs two successful pilots and known expiry plus later approval. Existing conductor retains v2 ownership; no duplicate launch.
- Revisit when: measured pilot throughput/restore time, lab access, CPU-cloud quote, or a separately approved simulation requirement changes the decision.


### D-20261020-COMPUTE-X3: Compare all available resources under the owner’s ×3 condition
- Decided by: owner’s latest clarification in the document Q&A chat.
- Decision: include Mac, brother’s laptop, lab PC, Chợ Mơ at ×3, and rented NVIDIA GPU cloud in a short use-case comparison. If ×3 is unavailable, the owner does not top up; the earlier ×2/100–200k planning scenario no longer represents the owner’s purchasing preference.
- Why: prior short report over-narrowed the question to a cafe pilot and omitted the requested resource alternatives.
- Evidence:owner clarification; refreshed official cafe/cloud rates on20October; existing hardware evidence and local Mac CPU/RAM read.
- Limits:comparison is not a payment/deposit authorization, a simulator migration or a benchmark. Preserve existing training ownership and the approved bounded MuJoCo pilot. Actual promotion eligibility/expiry and lab hardware remain unconfirmed.

### D-20261020-30: Run reviewed PPO v2 with a bounded residual arm
- Decided by: Claude review75a304d, authorized by owner; conductor supplies numeric details once before results.
- Decision: use the v2 setup recorded in sessions/2026-10-20-ppo-v2.md: reward scale.1/fall penalty1,100Hz policy,eight envs,observation VecNormalize,3M policy steps; residual cap20% with500Hz unchanged LQR. Each arm extends three to five seeds only after a strict balance PASS in the initial panel.
- Why: test the reviewed survival-reward/horizon/randomization changes and residual correction without changing physical dynamics or acceptance. Keep execution lean; no per-step training provenance.
- Evidence/status: owner request and imported Claude review. Implementation, tests and runs pending at declaration.

### D-20261020-OVERNIGHT: Keep a bounded overnight worker queue
- Owner: f conducts; g/i/k hard, b/e/default medium, d/h/j simple; check idle and quota, recheck30min and06:30, transfer partials same/lower tier. Default currently busy in this chat.
- Scope: A1–A4,B1–B3,C1–C3 approved; one branch/worktree/PR per task; conductor verifies and merges exact-head green CI. No student solution, motors, flashing or active PPO changes.
- Resource decision: Mac edits/quick tests only while PPO runs; heavy jobs wait for reachable Pi or completed training. Do not claim unrun Pi builds or simulations.
- Review: one short morning file reviews/2026-10-21-overnight.md; replaces separate overnight milestone handoffs. Earlier account assignments remain historical.

### D-20261020-OVERNIGHT-FOLLOWTHROUGH: Shared quota and model scope
- Evidence: read-only app-server metadata identifies g/k as one login with100%used in the same300min window,reset02:16local. Treat aliases as one account for idle/quota checks; preserve work and transfer to i/e. Never buy credits or consume reset credits.
- Model decision: retain A3's requested hypothetical rigid-leg domain0.12–0.30m; do not present it as the pinned five-bar's reachable domain(upper bound≈.211m). A4 has assumed rod mass distribution/bearing and demonstrated dynamics differences; keep it separate from frozen PPO/LQR.
- Scope remains implementation plus quick checks overnight; full gain sweeps, dynamics and videos wait for available compute/Pi. No physical/acceptance thresholds or research recipe changed.

### D-20261021-OBSIDIAN: Portable mathematics-first lessons
- Decided by: owner, this chat, 2026-10-21.
- Decision: English Obsidian Markdown/asset ZIPs for substantial WBR lessons;
  save learning preferences in USER_PROFILE and the portable lesson skill.
- Current scope: LQR/RL/PPO proposal for Claude review before lesson production;
  no new training or hardware action authorized by this documentation.
- Evidence: reviews/2026-10-21-obsidian-lqr-ppo-plan.md.

### D-20261021-CAMERA-DAY: Resume live camera sequence without duplicating simulation
- Decided by: owner (sequence and authority); conductor (execution split).
- Decision: conductor owns native camera work; idle g builds existing visual ROS
  wrapper in isolated worktree/private Pi source. Preserve ongoing PPO and the
  owner-only gain exercise. Existing Conducting Codex text needs no duplicate.
- Evidence: owner camera-day prompt; sessions/2026-10-21-camera-day.md; SSH and
  account receipts under /private/tmp/wbr-camera-day-20261021/.
- Revisit when: hardware arrives or an actual runtime/build failure changes work.

### D-20261021-CAMERA-REVIEW: Follow owner-relayed Claude camera changes
- Decided by: owner, relaying Claude review.
- Decision: disable native viewers; try15FPS or800features against observed drops;
  measure trackingFPS/loss events/throttling. Run stereo,RGBD,stereo-inertial using
  borrowedD435i; calibration remains read-only. Mount-preserving cart/PD-bank
  motion with marked start/end;3replays report endpointdrift and closure events.
- Evidence: owner's2026-10-21review message; camera-day session and raw Pi logs.
- Limits: no powerbank/physicalmotion verified yet; no groundtruth accuracyclaim.

### D-20261021-CAMERA-LAB-ONLY: Finish physical camera work before cafe analysis
- Decided by owner: retain4MiB receive buffers, use stereo-only MCAP/reliable
  depth50+ recording; target<1% observed gaps and equal stereo counts.
- Morning scope narrowed to drop fix, marked loop and one inertial excitation
  attempt, then stop camera/ROS processes and archive evidence on the Mac.
- Camera remains mounted. Heavy robot stays on its wheels; planar excitation is
  logged as a limitation rather than claiming all-axis excitation.

### D-20261021-REPLAY-AFTER-PPO: Preserve Mac compute isolation
- Owner explicitly chose to wait for PPO v2 completion. Three new-bag stereo
  replays are queued; no SLAM/heavy setup while training. Pi use needs a fresh
  explicit owner release. No PPO/environment/AGENTS change authorized.
- Start requires terminal supervisor and batch receipts plus no batch workers.
  Report each endpoint, map/reset context and measured trackedFPS; do not infer
  throughput from nominal15Hz. Mac replay results must be labelled as Mac.
