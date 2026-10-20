# Documentation change log

Append-only audit trail. Add one entry per documentation change set using the
format in README.md. Entries describe evidence and review state; they are not
approval or proof of unrun tests. Never rewrite finalized earlier entries.

### DOC-20261020-1: Simulation inventory, DM-jump audit and documentation logging rule
- Time / author: 2026-10-20 10:56 +07; Codex. This entry also records the earlier same-session edits made before the owner required a dedicated documentation log.
- Branch / base: chatgpt/20261020-simulation-control; base 6929fb4. Local working changes; no resulting commit or PR yet.
- Files:
  - AGENTS.md: added the owner's rule that every documentation change set needs an audit entry with rationale, evidence, checks and review status.
  - ops/worklog/README.md: added DOCUMENTATION_LOG.md conventions and the entry format; clarified that logging is not approval.
  - ops/worklog/CURRENT.md: changed active focus from lab-only state to simulation/control; recorded recovered source facts, current blockers, configured SSH alias and unverified Windows image-read progress while retaining card A evidence and lab blocks.
  - ops/worklog/DECISIONS.md: appended D-20261020-5 through D-20261020-9 for session scope, assumed-model authorization, source discovery, documentation logging and an append-only clarification that source implementation is not execution evidence; prior decisions remain unchanged.
  - ops/worklog/sessions/2026-10-20-simulation-control.md: created session inventory and initial teaching scope; added sim-to-real discussion and pinned source audit; then labeled the initial UNKNOWN table and four-state proposal historical and added the current six-state/two-output source-informed proposal.
  - ops/worklog/DOCUMENTATION_LOG.md: created this audit trail and first entry.
- Changes and reason: the local inventory initially had no controller source. The owner later supplied DM-jump; code inspection recovers gains, geometry constants, state/command conventions and nominal timing. Documents now distinguish those SOURCE-SUPPORTED facts from UNKNOWN physical data and CALCULATED checks. Earlier assumptions remain labeled history, rather than being mistaken for the current reproduction plan. Owner explicitly requires logs for all documents so Claude can review each change.
- Sources:
  - Owner instructions and replies in this session; decisions D-20261020-5/6/7/8/9.
  - DM-jump commit 6855ef8c6da20246251cfd473467c04112bf800f; pinned file references and source/check hashes in the session audit.
  - Existing lab session and preserved power-idle-d435-20261020-01 evidence; 731/731 checksum verification reported earlier.
  - PR #36's proposed simulation rules inspected at cdfb4c056fa6c50195391ec87ec81f3f64e566dd; not claimed as merged in this branch.
  - Primary MuJoCo/SciPy documentation and Peng/Chebotar sim-to-real papers linked in the session log; these do not supply robot physical parameters.
- Validation: independent read-only source review checked the recovered six-state/scheduled-gain interpretation and flagged stale UNKNOWN/four-state wording; those corrections were applied. Final consistency review found one execution-wording ambiguity, clarified through append-only D-20261020-9; no other material inconsistencies were reported. Earlier arithmetic evaluated gains at four lengths and checked VMC Jacobian finite differences at three poses (max absolute error 6.90e-9). `git diff --check` exited 0. Documentation assertions exited 0: all six changed Markdown files logged, zero unlogged files, pre-session decision content preserved, CURRENT.md 37 lines, current/historical scopes distinguished and pinned source revision recorded. No firmware build, MuJoCo run or RL training is claimed.
- Limitations / review: source constants are not physical measurements; actual flashed commit, masses/inertias, actuator dynamics, measured timing and original A/B/Q/R synthesis remain UNKNOWN. Proposed simulation architecture has not been implemented or approved. Changes are local and unreviewed; because AGENTS.md is also changed, this is not a worklog-only change set eligible for self-merge. No canonical gate document or hardware code changed.

### DOC-20261020-2: Record Claude approval and publish the bounded documentation change
- Time / author: 2026-10-20 11:02 +07; Codex; approval relayed directly by owner.
- Branch / base: chatgpt/20261020-simulation-control; initial base 6929fb4; fetched main 0dc029a (PR #36).
- Files: ops/worklog/{CURRENT.md,DECISIONS.md,README.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-simulation-control.md}; approved AGENTS.md logging edit retained in the same PR.
- Changes: approved reduced six-state then full five-bar MuJoCo/VMC stages; require compiled upstream C/Python parity; four-state stays archived.
- Changes: recorded mass/COM priority and owner's clarification that physical WBR assemblies are unavailable; defer weighing, request CAD/BOM, label sweeps sensitivity only.
- Changes: checked pinned MIT license and notice requirements; made new DOC entries about 15 lines; prior DOC entry preserved.
- Sources: owner's DOC-20261020-1 review and hardware clarification; D-20261020-10 through -15; pinned DM-jump 6855ef8 and license hash in the session log.
- Validation: source license read; origin/main fetched successfully. Final doc/scope checks, merge and CI receipts pending execution.
- Review: DOC-20261020-1 approved with these decisions; owner authorizes commit/push/PR and merge only after green CI and approved-scope verification.
- Limitations: no model/controller implementation or hardware measurements; actual mass/inertia and original LQR synthesis remain UNKNOWN.
- Publication: will append commit/merge/check receipts to the session log; PR history is authoritative for eventual merge status.

### DOC-20261020-3: Record upstream merge and pre-publication checks
- Time / author: 2026-10-20 11:02 +07; Codex; follows the approved publication task.
- Branch / base: chatgpt/20261020-simulation-control; origin/main 0dc029a.
- Files: ops/worklog/sessions/2026-10-20-simulation-control.md; ops/worklog/DOCUMENTATION_LOG.md.
- Changes: appended actual checkpoint/merge receipts and documentation-check results; preserved earlier pending-status entries as history.
- Sources: checkpoint 39cd6ac; clean merge f1a7fa6; fetched PR #36 rules; owner's authorization in D-20261020-14.
- Validation: merge exit 0, no conflicts; exactly six approved Markdown paths in PR delta; doc assertions and whitespace checks exit 0.
- Review: within DOC-20261020-1 plus approved review decisions/status receipts; no implementation or experimental result added.
- Limitations: push/PR/CI/remote merge not yet claimed; GitHub PR history will record subsequent publication state.

### DOC-20261020-4: Teaching contract and compiled-C parity checkpoint
- Time / author: 2026-10-20 +07; codex-f conductor.
- Branch / base: chatgpt/20261020-c-python-parity; base 0e48cff (merged PR #37).
- Files: sim/README.md; sim/parity/README.md; ops/worklog/CURRENT.md; ops/worklog/DECISIONS.md; ops/worklog/sessions/2026-10-20-c-python-parity.md; ops/worklog/DOCUMENTATION_LOG.md.
- Changes: documented learner-owned cores and approved sequence without waiting for hardware; reserved f for conductor, g/i/k preferred as user-reported Plus workers.
- Changes: new build/exercise commands, source provenance, native VMC checks, TODO status, evidence receipts, limitations and rollback; earlier source/license notices preserved unchanged.
- Sources: owner teaching/delegation instructions; D-20261020-16/17; DM-jump 6855ef8c6da20246251cfd473467c04112bf800f; MIT provenance manifest.
- Validation: original C compilation exit 0; 15/15 infrastructure tests PASS; gain checker BLOCKED exit 2; learner exercise expected FAIL exit 1.
- Validation: codex-g read-only review found guard mismatch/missing independent anchors; fixed with regression checks. Bash syntax/whitespace exit 0.
- Limits: Python gain TODO and Python VMC parity outstanding; native sanity checks do not complete milestone 1. No physics/LQR/RL or hardware result.
- Review / publication: implementation checkpoint requires Claude review before merge; commit/PR/CI and full-suite receipts appended to session log as obtained.
- Understanding check: two questions recorded, answers pending. Prior documentation approval is not approval of this code.

### DOC-20261020-5: Publish parity checkpoint and prepare Claude review
- Time / author: 2026-10-20 +07; codex-f conductor.
- Branch / base: chatgpt/20261020-c-python-parity; implementation 28fea56, base 0e48cff.
- Files: ops/worklog/reviews/2026-10-20-c-python-parity.md; ops/worklog/sessions/2026-10-20-c-python-parity.md; ops/worklog/DOCUMENTATION_LOG.md.
- Changes: prepared bounded code-review question, recorded commit/push/draft PR #38 and original-source whitespace exception.
- Sources: build/check receipts and codex-g review in session; owner teaching/account instructions; wbr-claude-review-request skill.
- Validation: push/PR creation exit 0; attached PR to chat; authored-file staged whitespace check exit 0.
- Review: Claude answer pending, PR remains draft and unmerged. Final full-suite/CI outcomes recorded in session when available.
- Limits: no learner implementation, Python VMC parity, physical/dynamics result or gate promotion implied.

### DOC-20261020-6: Record final local and CI outcomes without conflating them
- Time / author: 2026-10-20 +07; codex-f conductor.
- Branch: chatgpt/20261020-c-python-parity; reviewed CI head bfc84bf59495dfc82388f391e07cbba5d714cbe4.
- Files: ops/worklog/sessions/2026-10-20-c-python-parity.md; ops/worklog/DOCUMENTATION_LOG.md.
- Changes: recorded full local exit 1 from existing unsupported 460800-baud link-bench test; new parity suite PASS; Linux CI SUCCESS at exact head.
- Sources: /private/tmp/wbr-parity-full-tests-20261020.log; PR #38 CI job link in session.
- Validation: full runner finished, final summary inspected; exact head/CI read from GitHub. No unrelated test patched or threshold changed.
- Limits / review: local full suite is not green; learner TODO and Python VMC parity remain. PR draft, Claude review pending, no merge.

### DOC-20261020-7: Conductor dispatch and parity/main state reconciliation
- Time / author: 2026-10-20 13:38 +07; codex-f conductor.
- Branch / base: chatgpt/20261020-conducting from 5b6ab4e, integrating prior bc4aea5 parity branch.
- Files: ops/worklog/CURRENT.md; ops/worklog/DECISIONS.md; ops/worklog/sessions/2026-10-20-conducting.md; ops/worklog/DOCUMENTATION_LOG.md.
- Changes: resolved CURRENT merge conflict using latest owner hardware/role; appended D18-D20; recorded idle checks, isolated Astra Ultra workers and protection of learning exercise.
- Sources: owner conducting instruction/hardware reply; process/session-event metadata; actual SSH timeout; PR38 prior green CI.
- Validation: g/i launch headers show requested model/effort; no worker-f or occupied-k launch. Worker verification and final results pending.
- Limitations/review: camera unavailable and Pi unreachable, no live pose; no balance claim yet. Claude review only at actual milestone, not this dispatch.

### DOC-20261020-8: Persist the requested conducting rules
- Time / author: 2026-10-20 +07; codex-f conductor.
- Branch: chatgpt/20261020-conducting; parity/main integration 1fe2ae0.
- Files: AGENTS.md; ops/worklog/sessions/2026-10-20-conducting.md; ops/worklog/DOCUMENTATION_LOG.md.
- Changes: short Conducting Codex section; aligned old Claude and logging statements with owner's newest rules; scoped accounts/worktrees/briefs/verification/merge/protected learner core.
- Sources: owner's explicit role, merge, model and documentation instructions; worker launch/model receipts.
- Validation: whitespace check; account f not launched and g/i worktree isolation confirmed. CI/publication pending.
- Limitations/review: no milestone claimed; no Claude escalation required for this authorized role update. Hardware/SSH blockers remain.

### DOC-20261020-9: Integrate worker outputs and prioritize the verified simulation
- Time / author: 2026-10-20 +07; codex-f conductor.
- Branch: chatgpt/20261020-conducting integrating worker sim827c357; prior green PR38/40/41 merged.
- Files: sim/README.md; ops/worklog/{DECISIONS.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-conducting.md}; imported worker docs ops/worklog/sessions/2026-10-20-sim-lqr-push.md and earlier PR41 skill/offline-stereo.md, skill/SKILL.md, ros2/wbr_orb_node/README.md, sessions/2026-10-20-pi-orbslam-pose.md.
- Changes: running assumed-model instructions plus parityexercise boundary; documented idle dispatch, cafeSSH recovery, owner deferral of Pi, independent reruns and mergedPRreceipts.
- Sources: owner priority instruction; worker commits38399d0/827c357; conductor rawlogs and simulation folders under /private/tmp/wbr-conducting-20261020.
- Validation: parity15/15, wrapper19/19 and simulation11/11 PASS; conductor simulation CLI and independentCSV checksPASS. No learneredit. Merge resolution changes docs/package docstring only.
- Limits/review: assumptions/idealrolling only; no livecamera or source-gain parity. PR42 finalCI/merge and final milestone review file pending.

### DOC-20261020-10: Final LQR MuJoCo milestone review and live state
- Time / author: 2026-10-20 +07; codex-f conductor.
- Branch / base: chatgpt/20261020-lqr-milestone-review; base caae6ff (merged PR42).
- Files: ops/worklog/reviews/2026-10-20-lqr-mujoco.md; ops/worklog/CURRENT.md; ops/worklog/sessions/2026-10-20-conducting.md; ops/worklog/DOCUMENTATION_LOG.md.
- Changes: one final review listing mergedPR38/40/41/42 and realtests/runs/limits; currentstate marks simulationdone, Pi deferred by owner; stablearchive/hashes and questionspending recorded.
- Sources: exact PR42head be061d8, bothCIchecksSUCCESS, actualmerge caae6ff; conductor-integrated-01 rawreceipts and 34entry archive manifest.
- Validation: conductor CLI exit0, simulation11/11 testsPASS, parity15/15 and ROS-core19/19PASS; source-gainTODOdiffempty; copies checksumverified. No codechange in this final docs set.
- Limitations/review: Claude final answerpending; ASSUMED idealrolling nominalmodel only, not physical/gainparity/RL evidence. Pi/runtime milestone not claimed, no gatepromotion.

### DOC-20261020-11: Concise LQR/RL guide and approved next-milestone state
- Time / author: 2026-10-20 +07; codex-f conductor.
- Branch / base: chatgpt/20261020-delay-lag-noise; main417c1e2 (PR44 review).
- Files: docs/learning/LQR_RL_GUIDE.md; AGENTS.md; ops/worklog/{CURRENT.md,DECISIONS.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-delay-lag-noise.md}.
- Changes: short practical guide now, concise-note rule, review approval and causal delay/lag/noise→frozenK→conditional synthesis→RL sequence; logged owner learning/lab priorities and account checks.
- Sources: Claude review file/PR44; actual sim code/config; primary SciPy/MuJoCo/Gymnasium/PPO docs; owner's concise-document instruction.
- Validation: guide relative links, line count and whitespace checked; only existing nominal results referenced. New actuator checks/training not claimed complete.
- Limits / review: guide is teaching material; physical values remain assumed, gain exercise protected. Code milestone and final Claude review remain pending.

### DOC-20261020-12: Explain the mathematical model with proper Markdown equations
- Time / author: 2026-10-20 +07; codex-f conductor.
- Files: docs/learning/LQR_RL_GUIDE.md; AGENTS.md; ops/worklog/{DECISIONS.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-delay-lag-noise.md}.
- Changes: replaced unexplained code-formatted formulas with rendered mathematics and compact derivations from geometry/energy to M/h/G, linearization and LQR; added numerical example and units/assumptions. Removed rigid line limit after owner feedback.
- Sources: actual sim/planar.py, sim/lqr.py, test_planar.py Lagrange oracle; config and archived nominalK; primarydocs linked.
- Validation: local links/equation delimiters/whitespace checked; numericalinitialtorques verified against archivedgain; no new control result claimed.
- Limits/review: reducedassumedmechanics only, no contact/fivebar or hardware validation. Guide revision is teaching correction, not an algorithm change.

### DOC-20261020-13: Verify readable Markdown mathematics and derived dynamics
- Time / author: 2026-10-20 +07; codex-f conductor.
- Files: docs/learning/LQR_RL_GUIDE.md; ops/worklog/{DOCUMENTATION_LOG.md,sessions/2026-10-20-delay-lag-noise.md}.
- Changes: GitHub-compatible inline math, aligned long equations and explicit Euler-Lagrange step; no model/controller code changed.
- Validation: KaTeX rendered64expressions without errors; guide analyticalA/B matched actualMuJoCo derivatives to6.28e-10/1.99e-13 maxabsoluteerror; local links/whitespace checked.
- Limits/review: confirms mathsyntax and nominalmodel derivation only, not new actuator/RL results or physical validity.


### DOC-20261020-14: Actuator milestone verification and account priority
- Time / author: 2026-10-20 +07; codex-f conductor; worker implementations i/g.
- Files: AGENTS.md; sim/{README.md,augmented.md,augmented*.py,run_augmented.py,configs/assumed_actuator_noise.json,tests/test_augmented.py}; ops/worklog/{CURRENT.md,DECISIONS.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-actuator-noise.md,sessions/2026-10-20-delay-lag-noise.md}.
- Changes: document causal runtime/API/assumptions, frozen-first conditional design, actual complete matrix, protected exercise, quota interruptions and b priority/idle requirement. Source docstrings/comments included.
- Sources: owner/Claude sequence; worker commits aad5710/0900606; conductor complete run05 and its source/config/hash receipts; primary MuJoCo/SciPy docs linked in augmented.md.
- Validation:27/27 simulation tests PASS, full120-case execution COMPLETE,373 artifact hashes verified; all paired noise hashes equal. Frozen FAIL40/40 controlled retained; conditional PASS40/40, expected-fall controls40/40.
- Limits/review: ASSUMED plant only. No actual PPO training, hardware evidence or gate promotion; CI/merge and completed-milestone Claude review pending. b occupied by unrelated work at check, so not launched.


### DOC-20261020-15: Final actuator milestone review and evidence archive
- Time / author:2026-10-20 +07; codex-f conductor.
- Files:ops/worklog/{CURRENT.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-delay-lag-noise.md,reviews/2026-10-20-actuator-noise.md}.
- Changes: completed-milestone review with mergedPRs, exact execution and failures; archive/CI receipts; b idle-to-launch transition and pending teaching questions.
- Sources:PR47headbdac630, both CI SUCCESS, merge0c70a32; run05 source0900606 and SHA256 receipts; b lifecycle completed07:52:11Z.
- Validation:373 archived hashes rechecked;27/27 independent simulation tests and full120-case matrix already verified. Plot generated from existing rawCSV and visually inspected; not new evidence trials.
- Limits/review:conditional LQR40/40 controlled passes applies only to assumed plant; frozen failures retained. PPO training and Claude final review pending; no gate promotion.


### DOC-20261020-16: Owner message format and held-out spot check
- Time / author:2026-10-20 +07; codex-f conductor.
- Files:AGENTS.md; ops/worklog/{DECISIONS.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-delay-lag-noise.md}.
- Changes: persist owner's exact two-ending message format, confine recommendations to review files, record an additional independent held-out LQR spot check.
- Sources:owner's latest instruction; native evaluator against archived conditional5ms gain with noise1000.
- Validation:whitespace/diff check; spot-check exit0,PASS,recovery2.760s,impulse0.900Ns. No implementation or threshold change.
- Limits/review:one spot check does not establish the full held-out comparison. PPO implementation/training remains pending; publication CI pending.


### DOC-20261020-17: Frozen PPO implementation and conductor verification
- Time / author:2026-10-20 +07; codex-b implementation, codex-f integration/verification.
- Files:sim/rl/{README.md,environment.py,trace.py,training.py,evaluation.py,aggregate.py,metrics.py,provenance.py,run.py,verify.py,tests/*.py}; .github/workflows/tests.yml; ops/worklog/{CURRENT.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-ppo-training.md,sessions/2026-10-20-delay-lag-noise.md}. External brief/report/feedback/command receipts referenced in session.
- Changes: executable fixed-budget PPO pipeline, causal shared inputs, compact full-substep evidence and failure/seed accounting; explanatory math/CLI docs. Conductor corrected Gym empty-options API and CI install ordering, added actual Gym/backend checks; retained failed check/CI logs.
- Sources:read-only protocol/requirements and actuator authorization/archive; worker4288fb8/draftPR49; primary PPO/SB3/Gym docs in README. No physical parameter inference.
- Validation:worker25/25 tests,1000-step real WBR optimizer/checkpoint smoke and8full LQR parity pairs; conductor expanded27/27 tests, native-vector/reward checks and independent5000-step adapter parity PASS;12 README math expressions rendered.
- Limits/review:smoke/evaluator fall is not a full PPO result. Full5×150000-step training and800+160 held-out outcomes pending. CI initially failed on missing Gym; dependency fix pending remote check. No frozen protocol, plant, threshold or protected exercise changes; Claude final milestone review pending.


### DOC-20261020-18: Preserve worker publication and CI failure receipts
- Time / author:2026-10-20 +07; codex-f integration of codex-b a9dd86b.
- Files:ops/worklog/{DOCUMENTATION_LOG.md,sessions/2026-10-20-ppo-training.md,sessions/2026-10-20-delay-lag-noise.md}.
- Changes: import exact worker source-freeze/second-smoke/failed-CI receipts; resolve session-footer conflict under owner's D27. No runtime change.
- Sources:worker4288fb8/a9dd86b, draftPR49, failed run39392656236 and preserved log; committed smoke b02.
- Validation:conductor27/27 RL tests passed at f12414a; merge conflict markers/whitespace checked. Full training not launched yet; remote dependency fix still pending.
- Limits/review:smokes are implementation checks, not candidate policies. Training/comparison/Claude review remain pending.


### DOC-20261020-19: Durable full-run launch and parallel source audit
- Time / author:2026-10-20 +07; codex-f conductor.
- Files:ops/worklog/{CURRENT.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-delay-lag-noise.md}; external source-audit brief referenced in session.
- Changes: live state marks the existing full job RUNNING and prohibits duplicate launch; records source/command/independent smoke and b idle-to-SolHigh audit dispatch. No source-code change.
- Sources:source608222b, conductor smoke/checkpoint receipts, full-run progress files, b process/lifecycle check and CLI model header; owner parallel-estimate/priority instructions.
- Validation:conductor1000-step WBR optimizer/reload smoke exit0 and27/27 RL tests; full5seeds advancing with exact budget configured. Whitespace/diff checked; CI dependency step and generic suites passed at observation.
- Limits/review:full training/evaluation and parameter audit still running; no RL outcome, physical validity or gate approval claimed. Source remains frozen while only worklogs change.


### DOC-20261020-20: Primary parameter sources and applicability limits
- Time / author:2026-10-20 +07; codex-b source audit, codex-f independent review/integration.
- Files:docs/learning/{MODEL_PARAMETER_SOURCES.md,LQR_RL_GUIDE.md}; ops/worklog/{DOCUMENTATION_LOG.md,sessions/2026-10-20-parameter-sources.md,sessions/2026-10-20-delay-lag-noise.md}.
- Changes: compact parameter/provenance table, verified supplier/source-model references and UNKNOWN mappings; clarify aggregate definitions and link from learning guide. Record PR49 merge/full-budget training completion, without claiming completed held-out results.
- Sources:DM-jump6855ef8; pinned dmBots wheel-legged/Motor manuals; Bosch BMI088 rev1.9; exact URLs/digests in worker session and external fetch receipts. No measured owner mass/COM data.
- Validation:conductor checked manufacturer MATLAB and all3rendered supplier tables; config hashes match frozen values; links/whitespace checked. No runtime tests repeated for this documentation-only set.
- Limits/review:component specs/source constants do not identify whole-body/leg properties, actuator lag or fused sensor noise. No model/reward/threshold change; PR50 CI/merge and Claude final review pending.


### DOC-20261020-21: Retain lossless reward check across float64 reductions
- Time / author:2026-10-20 +07; codex-b conductor after owner account switch.
- Files:sim/rl/tests/test_environment.py (test comment/oracle); ops/worklog/{DOCUMENTATION_LOG.md,sessions/2026-10-20-parameter-sources.md}.
- Changes: record actual PR50 CI error; require exact saved/live reward equality and allow only float64 reduction roundoff in independent cost recomputation. No runtime or experiment threshold change.
- Sources:failedCI39396790590, maxabsolute2.78e-17/maxrelative1.84e-16; same-head companionCI passed. Log retained under /private/tmp/wbr-augmented-20261020/.
- Validation:complete RL suite27/27 PASS, zero skips, including the targeted trace case; log conductor-rl-trace-fix-tests-01.log. Remote CI pending.
- Limits/review:test portability correction does not alter archived PPO failure evidence, trained checkpoints or claimed metrics.

### DOC-20261020-22: Completed comparison, account transfer and final review
- Time / author:2026-10-20 +07; codex-b conductor (earlier training dispatched by this chat as f).
- Files:AGENTS.md; docs/learning/LQR_RL_GUIDE.md; sim/rl/{README.md,RESULTS_2026-10-20.md}; ops/worklog/{DECISIONS.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-delay-lag-noise.md,reviews/2026-10-20-rl-comparison.md}; external bounded g audit brief referenced in session.
- Changes:record owner role switch, measured negative full comparison, retained failures/conditional uncertainty, exact receipts and final Claude review; update learning links. No runtime/config/reward/protocol changes.
- Sources:source608222b, evaluation781d702, mergedPR47/48/49, run COMPLETE, archived aggregate/checkpoints/raw traces, independent audit script and host metadata. g read-only audit in progress.
- Validation:6680 archived hashes, five exact budgets and checkpoint reloads,960unique outcomes,800paired noise prefixes and four raw metric checks PASS; independent paired CI recomputed. Earlier27/27 tests and real optimizer smoke retained. Figures generated from existing data and visually checked, not new trials.
- Limits/review:LQR160/160,PPO0/800 only under this frozen assumed recipe; no causal ablation or broad RL/sim-to-real claim. Source-auditPR50 CI/test-portability fix and final Claude review pending; no gate promotion.

- DOC22 follow-through: CURRENT.md now records the completed experiment, b-conductor role, archive, protected exercise and pending publication/review; replaces stale RUNNING text. It does not label the negative result Claude-approved or change a gate.


### DOC-20261020-23: Integrate independent outcome audit and final source receipts
- Time / author:2026-10-20 +07; codex-b conductor, codex-g audit bbf4908.
- Files:ops/worklog/{CURRENT.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-delay-lag-noise.md,sessions/2026-10-20-ppo-outcome-audit.md,reviews/2026-10-20-rl-comparison.md}; sim/rl/RESULTS_2026-10-20.md.
- Changes:import scoped audit session, measured training/push exposure, PR50 green/merge receipt, complete archive/replication and strict-source-guard note. Resolve shared-log merge conflicts preserving all prior entries.
- Sources:g diagnostics/report and bbf4908; PR50head934e846, bothCI SUCCESS, merge31a5d1a; same immutable completed run and original source freeze608222b.
- Validation:conductor reran both g scripts in a new directory, both exit0 and exact diagnostic JSON matches; earlier6680hash/raw/noise/budget audit retained. Guide64/README12 math expressions rendered; links/whitespace/conflict markers checked before publication.
- Limits/review:sampled implementation audit found no actionable bug; it does not prove cause or future RL failure. No new training, runtime/reward/threshold or gate change. Final results PR/CI and Claude response pending.
- DOC23 follow-through:CURRENT now points directly to pending Claude review rather than stale training/publication work; all local document links resolve, CURRENT25lines. This final publication contains no new simulation trial or code change.
- DOC23 publication receipt:PR51 opened; archive/publication-269cc3a stores the reviewed result/guide/source-table snapshots (35supplementary hashes total). Session records the two optional learning questions, unanswered at publication. No new simulation or approval claim.

### DOC-20261020-24: Cafe, lab and cloud compute decision review
- Time / author:2026-10-20 +07; document Q&A chat, isolated cafe-compute-review worktree.
- Files:ops/worklog/{reviews/2026-10-20-cafe-compute-strategy.md,sessions/2026-10-20-cafe-compute-strategy.md,DOCUMENTATION_LOG.md}.
- Changes:compare Cho Mo owner screenshots/current cafe data, conditional promotions, Windows/backend compatibility, privacy/reset overhead and cloud/lab alternatives; prepare Claude questions. Final owner scope excludes the other branch. Proposal only, no resource purchase or architectural approval.
- Sources:6in-scope owner images/staff terms/reset-policy clarification; official Cho Mo page and vendor compatibility/pricing; completed CPU experiment and current CPU-only training source at819659c. External source receipts recorded in session.
- Validation:independent Decimal recomputation passed all6final Cho Mo economics rows,3setup-overhead rows and cloud examples; local result link resolves; screenshot/configuration conflicts retained and whitespace/scope checks passed. No runtime change or new training; publication CI pending.
- Limits/review:no cafe Windows/GPU benchmark, confirmed bonus eligibility, staff-admin access or actual room/seat billing. Claude/owner decision pending. CURRENT retained under the active conductor's ownership.
- DOC24 publication:PR53 is documentation-only and now Cho Mo-only; report formatting and6tariff/3overhead calculations checked. Final CI/merge receipt is retained with external source receipts; substantive Claude approval remains pending.


### DOC-20261020-CAFE-REVIEW: Record bounded compute approval
- Time / author:2026-10-20 +07; document Q&A chat, isolated cafe-approved-plan branch.
- Files:ops/worklog/{reviews/2026-10-20-cafe-compute-strategy.md,DECISIONS.md,DOCUMENTATION_LOG.md,sessions/2026-10-20-cafe-compute-strategy.md}.
- Changes:preserve Claude425b682 review; add a one-page current decision card, correct first-deposit x2 pricing, label all speed/setup estimates and preserve existing v2 conductor ownership. Supersede historical booking recommendations without editing the review text.
- Sources:owner-pasted review/PR54; current shared43f7f6f; original official tariffs/promotion evidence. No new vendor-price or performance claim.
- Validation:review preservation,75.8worker-hour arithmetic,pilot cost/tier,local links and documentation-only scope checked; remote CI pending.
- Limits:no pilot, dependency install, training launch, spending, new CPU-cloud quote, runtime/protocol or architecture change. CURRENT retained under active conductor ownership.

### DOC-20261020-25: PPO v2 execution
- Files: imported Claude review; sessions/2026-10-20-ppo-v2.md; related v2 implementation/session/result notes in this change set.
- Why/source: owner authorized the lean v2 direct/residual experiment; Claude review75a304d. Old v1 evidence and plant/evaluation criteria preserved.
- Validation/status: actual worker launch recorded; i usage failure retained. v2 build, optimizer smoke and full results pending; no success or Claude approval for v2 claimed.

- DOC25 follow-through: includes CURRENT/DECISIONS, both v2 sessions, new module/config/tests documentation and imported Claude review. Worker97db7f3/conductorf1b5ee7; final44/44tests,real8env optimizer/reload and full5ms zero-residual parity passed. Full3M batch RUNNING outsidegit; no full learned-policy claim.
- DOC25 continuation: durable supervisor launched09:43:55Z; heartbeat `finish-ppo-v2-comparison` every30min. Initial duplicate-free progress confirmed; source/plant/v1criteria/protected exercise unchanged. Final results and Claude v2 review pending.
- DOC25 integration:main advanced viaPR52–54 while training ran. Preserve finalized cafe DOC24; renumber only this unmerged PPO draft25. Resolve in isolated parameter-source-audit worktree, retaining both histories; no runtime or active-checkout change.
- DOC25 publication follow-through:PR56 adds only independent cafe records; preserve them alongside v2 records. Publication now uses ppo-outcome-audit worktree; parameter-source-audit is a separate viewer task. Training source unchanged.
