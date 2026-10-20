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
