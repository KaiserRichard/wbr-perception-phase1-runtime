# Review request: compiled C reference and teaching harness
Requested: 2026-10-20 +07 by codex-f conductor. PR: #38 (draft).
Branch: chatgpt/20261020-c-python-parity.

## What I need from Claude
1. Approve this host-reference/teaching checkpoint for eventual merge, or identify required corrections to its source provenance, numeric contract or learner ownership?

## Context (cold-start summary, max 15 lines)
- Prior DOC-20261020-1 architecture approved and merged in PR #37; that was documentation approval only.
- Owner authorizes implementation, without waiting for a physical WBR, and reserves gain Python/A/B/LQR/reward cores for their own learning.
- `sim/parity/vendor/dm_jump/`: unchanged pinned MIT source plus checksummed provenance, commit 6855ef8c6da20246251cfd473467c04112bf800f.
- Builder compiles original VMC/gain functions; chassis task is initializer input only, never executed.
- Host contract uses float32/libm, sequential calls, fixed-pose initialized history and singularity guards; no ARM/CMSIS/transient claim.
- 15 infrastructure tests pass, including finite-difference Jacobians and independent symmetric geometry/force anchors.
- `student.py` remains TODO. Gain checker BLOCKED exit 2; learner exercise intentionally fails. Python VMC parity remains unimplemented.
- Generic CI discovers infrastructure tests, excludes learner exercises. No physics, LQR, RL, hardware or gate result.
- codex-g read-only review's guard/anchor findings addressed; f remains conductor, not a worker.
- Commands, receipt hashes and detailed limitations: `ops/worklog/sessions/2026-10-20-c-python-parity.md`.
- Check current PR CI and session publication receipts; local repository-wide validation is separate from targeted tests.

## My recommendation
MEASURED: compile and infrastructure checks support this scaffold as a teaching
checkpoint. Retain draft status until review and owner go-ahead. Do not interpret
this as milestone 1 completion: owner gain implementation and Python VMC parity
must precede reduced-model physics. Physical estimates remain parallel work.

## Claude review
Pending.
