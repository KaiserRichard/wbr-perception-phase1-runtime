# C1-T27 simulation and compute plan — 2026-10-31

- Read `ops/worklog/CURRENT.md`, `ops/USER_PROFILE.md`, the 20 Oct café compute review, `SRC_PLAN-v2.md`, `SRC_RL_REVIEW.md`, `research/explore/ROADMAP.md`, and the current `sim/` plant/training sources.
- Inspected `research/compute/`; it did not exist, so there was no partial `SIM_COMPUTE_PLAN.md` to preserve.
- Confirmed local source facts: `sim/twin3d` is a reduced virtual-leg/contact model with optional simulated depth and `implicitfast`; current SB3 trainer selects `device='cpu'`; proposed G1 bundle is not yet the legacy v2 bundle.
- Wrote `research/compute/SIM_COMPUTE_PLAN.md` (69 lines): S0–S4 stage needs, ESTIMATE resource ranges, stage × machine fit, setup/cost estimates, ten-minute first benchmarks, timeline and buy/borrow triggers.
- Web sources checked 2026-10-31: MuJoCo/MJX, JAX platform matrix, MuJoCo Warp, Isaac Lab v3.0, RunPod rates and OEG Chợ Mơ promotions. RunPod page updated 8 Oct 2026. OEG page showed no active promotion, so ×3 café credit remains unconfirmed; station specs/rates are owner-reported in the 20 Oct review, not a fresh public quote.
- No machine benchmark, simulation, RL training or test suite was run. Estimates are planning values, not measured capability. No purchase, rental, commit or hardware action.
- `ops/worklog/CURRENT.md`, this session file, `ops/worklog/DOCUMENTATION_LOG.md` and the branch ledger were updated for continuity. Work remains local/uncommitted as requested.
