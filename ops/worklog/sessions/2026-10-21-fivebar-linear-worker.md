# Fivebar local linear worker — 2026-10-21

- Owner-authorized isolated worker `codex-g`; branch `chatgpt/20261021-fivebar-linearization`, worktree `/Users/quockaiser/.codex/worktrees/fivebar-linear-review/wbr-lab-ops`.
- Read root/sim AGENTS, RESEARCH_RULES, USER_PROFILE, CURRENT and Claude's PR102 review. No delegation, other-chat/account probes, Pi/SSH/hardware, owner exercise, PPO, training or rollout work.
- Implemented only new `sim/fivebar/linearize.py`, focused tests and minimal README instructions. Existing geometry, projected/reduced derivatives, config transform and `sim.lqr.synthesize` reused unchanged.
- First real CLI ran **before tests**, exit 0, 3.525 s: `run-01/` below (uncommitted implementation on base `5a41ad55e031213dcad65196767717744b087c88`). No failed dynamics/CLI attempt and no discovered model bug. Numerical rejection serialization was hardened to retain nonfinite equilibrium status as JSON null, without subtracting drift.
- Early handoff written immediately after CLI success: `/private/tmp/wbr-control-linear-review-20261021/g-linear-ready.md`, with exact interpreter/command/output/current results; no wait for independent gain study.
- Final committed-source reproduction: **`f1086c905a6c452f6659fae324155e3d6af18f14`**, clean tree, exit 0, **3.648 s**. Evidence root `/Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/fivebar`; final `run-02/{report.md,comparison.json,metrics.csv,acceleration-inputs.csv}` plus sibling `run-02.log`. Initial run remains preserved.
- No dependencies installed; existing interpreter read-only, bytecode disabled, BLAS single-threaded, nice 10. Deterministic calculations; random seeds **none**.

Exact final commands, from the worktree above (`--out` must be fresh on reproduction):

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
nice -n 10 "$PY" -m sim.fivebar.linearize \
  --lengths .12 .16 .20 .21 --projection-epsilons 1e-5 3e-6 1e-6 \
  --state-epsilons 1e-4 1e-5 1e-6 --input-epsilons 1e-4 1e-5 1e-6 \
  --out /Users/quockaiser/wbr-evidence-archive/sim-linear-review-20261021-01/fivebar/run-02
nice -n 10 "$PY" -m unittest sim.fivebar.tests.test_linearize -v
```

- All four lengths reachable/non-singular, zero state/input accepted at declared componentwise derivative tolerance `1e-7`; maximum residual `3.6964e-9`, closure below `7.8e-17 m`. No hidden bias subtraction or alternative equilibrium.
- Continuous A/B compared first at each length. Selected projection/state/input eps `1e-6` each; 3 projection values × 3 paired state/input perturbations × 4 lengths = **36** retained comparisons. Independent epsilon meanings retained explicitly. Maximum A/B entry refinement differences `0.01453` / `8.5443e-7`, maximum closed-loop rho change `2.94e-7`; no monotonic-convergence claim.
- Both continuous models use matched ZOH, dt `0.002 s`, state `[x,theta,phi,xdot,thetadot,phidot]`, inputs `[Tw,Th]`, feedback `u=-Kx`. Fresh existing reduced DARE gains use the **actual held-control MuJoCo RK4 step**, unchanged Q/R and `Qd=dt Q`, `Rd=dt R`; all synthesis matrices retained separately. Max actual-step/ZOH entry discrepancy A `7.88e-9`, B `6.40e-9`.

| L m | fivebar rho with reduced K | radial margin 1-rho | decay tau s | raw relative B norm |
|---|---:|---:|---:|---:|
| .12 | .997674099 | .002325901 | .858882 | .168317 |
| .16 | .997549295 | .002450705 | .815091 | .144941 |
| .20 | .997490806 | .002509194 | .796068 | .311595 |
| .21 | .997663634 | .002336366 | .855030 | .870170 |

- **Reduced K stabilizes all four fivebar linearizations and all refinements locally.** Every pole of reduced actual-step, reduced ZOH and fivebar ZOH is in CSV/JSON; report lists all six fivebar poles. Margin is radial distance to the unit circle, not gain/phase margin; tau is the slowest sampled decay envelope.
- Mass M and generalized input map G both contribute: `B_acc=M^-1 G`, independently agrees with finite-difference B lower rows within `1.14e-13`. JSON includes exact path-dependent decomposition `(Mf^-1-Mr^-1)Gr + Mf^-1(Gf-Gr)`. The earlier ~17% wheel reaction split was at a different pose and is not a full B percentage. At upright .16 m, wheel G is `[16.583748,-.7923375,-.2076625]` versus reduced `[16.583748,-1,0]`; wheel-to-body acceleration is `6.395338` versus `23.620010 rad/s²/(N m)`. It reverses sign at .20/.21 m. Raw matrix relative/max norms mix units and depend on scaling.
- `config_at_length`: unchanged fixed masses; reduced leg COM scales by L/L0, COM inertia by its square. Fivebar keeps four equal 0.125 kg rods, inventory 0.075/0.14 m links and 0.006 m inertial radius; it does not use the scaled equivalent-leg COM/inertia. Body/wheel parameters and costs shared, no mass matching or tuning.
- **16 focused tests passed**, initial 0.700 s; final 0.825 s in `fivebar/tests-01.log`. Known linear plant, affine/nonfinite equilibrium rejection, ZOH analytic solutions, feedback signs/shapes, unit transformation, actual mechanics/Jacobians, existing DARE compatibility, reference immutability, unreachable/straight-chain rejection and output preservation. Expected existing-directory rejection prints argparse usage; suite exits 0. `git diff --check` passed.
- Limits: assumed fixed-length projected mechanics, local standing branch; no nonlinear/hardware/contact/delay/noise/actuator/transfer validation. No model change, controller tuning, fivebar gain design, owner exercise, global logs/CURRENT edits, training or merge. Artifact attachment service unavailable; local report/CSV/JSON remain directly accessible.
