# Final milestone review: assumed WBR LQR balancing in MuJoCo

Requested: 2026-10-20 +07 by codex-f conductor, after implementation/verification/merge.
Milestone: nominal reduced six-state SIMULATION balance plus declared push recovery.

## Decision requested
1. Approve this scoped nominal baseline as the starting point for later control comparison, or name required corrections to mechanics, synthesis or interpretation before proceeding?

## Context (cold-start summary)
- Owner made Codex the conductor: idle Plus workers, isolated worktrees, conductor reruns and green-CI merge; Claude only final milestone review.
- Worker codex-i, gpt-6-astra ultra, implemented the approved reduced planar six-state model and NEW matched LQR. Full five-bar/VMC and RL are not implemented here.
- State: x, absolute leg pitch, absolute body pitch and their rates; aggregate wheel-pair and hip-pair torque inputs.
- MuJoCo integrates nonlinear gravity dynamics; wheel/hip reactions checked against independent Lagrange equations. No springs, servos, gravity compensation or angular constraint holds it upright.
- Ideal no-slip planar rolling is an explicit reduction: axle height fixed, wheel inertia retained as I/r² armature. No contact/slip, heave, yaw/roll or leg-length dynamics.
- Mass/COM/inertia, torque caps and leg length are ASSUMED in one replaceable config. Wheel radius is a source code constant, not a physical measurement.
- Continuous A/B and actual RK4-step discrete A/B are finite-differenced; new CARE/DARE gains, residuals, controllability and sampled poles are recorded. Default is saturated DARE at 2 ms.
- Owner gain_schedule TODO remains unchanged; neither gain parity nor Python VMC parity is claimed complete. No real-robot or sim-to-real validation.
- Pi track: native executable/data and ROS exist, cafe Wi-Fi SSH works; owner then prioritized other work due slow card/no camera. No SLAM/ROS-pose milestone completed, no STM32/motor actions.

## Merged PRs

| PR | Merged change | Merge revision |
| --- | --- | --- |
| [#38](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/38) | Compiled source reference and protected learner exercise | ba36fc357b34ba9196452773a4abca8bd2029931 |
| [#40](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/40) | Requested Conducting Codex rules and dispatch logs | 268d9bd38e6487396c4d52d58e14c7af88d41a5f |
| [#41](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/41) | Camera-free Pi preparation; wrapper gaps documented, no pose claim | 5c6225bce4ac2e8cf10a539e34f54a243c21d5b2 |
| [#42](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/42) | ASSUMED MuJoCo model, new LQR, protocol/tests and CI | caae6ff6141957a0dcef06ce2e2baaa65710b8b5 |

GitHub PR history is authoritative. PR42 exact verified head was
`be061d8df3121e66a46ea67a5eae6e2f8c862093`; original worker commit
`827c357546abeef99553938584ca6e4167564471`. Conductor resolved documentation/
package-docstring conflicts only. Both PR42 checks SUCCESS at that integrated
head; [actual CI run](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/actions/runs/39382644952).

## What was actually run

Conductor executed these from the repository root (using the worker's pinned
isolated Python environment; exact command/source hashes are in result.json):

```sh
/Users/quockaiser/.codex/worktrees/sim-lqr-push/wbr-lab-ops/.venv/bin/python -m sim.run_planar --config sim/configs/assumed_planar.json --out /private/tmp/wbr-conducting-20261020/conductor-integrated-01
```

Exit 0 at commit be061d8. Tracked sources were clean; provenance honestly records
unrelated pre-existing untracked host-test binaries. The same protocol was
independently run earlier as conductor-sim-01 and conductor-sim-02. The second
repeat checks the final runner metric addition; the third verifies integration.
These deterministic repeats are reproducibility checks, not independent samples.

| Scenario | Declared experiment and measured result |
| --- | --- |
| Balance | 10 s, leg +8°, body -6°, zero initial rates; recovery 1.732 s, peak translation 0.0391 m |
| Push | Same initial condition, 6 N body-COM pulse [3.00,3.15) s = 0.9 N s; recovery 2.714 s after pulse end; post-push peak tilt 6.095°, peak translation 0.1596 m |
| Open loop | Same model/initial condition, exactly zero torques; 45.164° at 0.182 s (required fall negative control) |

Both controlled runs satisfy all six final-window error tolerances, 2/4 N m
actuator caps and zero numerical warnings; no saturation. Thresholds/protocol
were declared before first run and not relaxed. Overall peak 8° includes the
initial tilt and must not be reported as the push response alone.

Conductor also ran:
- `.venv/bin/python .github/run_unittest.py sim/tests`: 11/11 PASS, no skips. Tests include independent nonlinear mechanics and COM-force mapping, actuator reaction/clipping, passive energy, Riccati/discretization and deliberately zeroed LQR failing balance.
- Independent raw CSV checks: all entries finite, 5,001 samples in each controlled case, push integral 0.9 N s, open-loop torques exactly zero.
- `/usr/local/bin/python3.12 .github/run_unittest.py sim/parity/tests`: 15/15 PASS (infrastructure only; learner TODO still BLOCKED).
- `make -C ros2/wbr_orb_node test`: 19/19 host-core PASS (fake engine; not a ROS/SLAM pose).
- `git diff bc4aea5 -- sim/parity/student.py`: empty.

## Stable evidence and reproduction

Mac archive: `/Users/quockaiser/wbr-evidence-archive/sim-lqr-20261020-01`.
Includes `conductor/` raw CSV/JSON/MJCF/plot, `worker/` clean-worker run,
`source/` integration source snapshot, test logs and `SHA256.json` (34 entries).
Manifest SHA-256: `5ac9344be387c0fd57e702bcaf2c0358fc2136337eb4f414c95b60756a50c1c1`.
Conductor result SHA-256: `9ffecf467e5dff5e1c0fc64abb6e224b68b8f7ecec6c125d6e09562580e53970`.
Config SHA-256: `f6310f9d7ac2c4f44186e43a632d2d75e9a0eecd0766464c28fdee0ab6ad6a99`.
Pinned packages: MuJoCo3.3.7, NumPy1.26.4, SciPy1.15.3, Matplotlib3.10.3.
Reproduce via `sim/README.md` and `sim/requirements.lock` with a new output folder.

## Recommendation and limits

Approve only the nominal ASSUMED-model baseline if the mechanics/synthesis are
acceptable. Next declare perturbation/initial-condition coverage and retain this
same model/actuator/control-rate baseline for any later RL comparison. Real
mass properties, motor response/contact data and full five-bar VMC remain
separate work. No RL win, robustness envelope, hardware gate or deployed control
claim follows from one deterministic test condition. No gate promoted.

Two learning questions were sent; answers pending: why separate leg/body angles,
and what the open-loop fall does/does not prove.

## Claude review
Pending final review.
