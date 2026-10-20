"""Conditional DARE on the actual delayed/lagged runtime step.

Use only AFTER an observed frozen-gain failure. No nominal Q/R retuning.
State z = [six measured coordinates, reconstructed torques, prior commands].
"""

import numpy as np
from scipy.linalg import solve_discrete_are

from sim.augmented import AugmentedRuntime, gain_hash
from sim.lqr import eigenvalues


def linearize(runtime, epsilon):
    n = runtime.state_size
    z, u = np.zeros(n), np.zeros(2)
    transition = runtime.transition_for_linearization
    A = np.column_stack([(transition(z+dz, u)-transition(z-dz, u))/(2*epsilon)
                         for dz in epsilon*np.eye(n)])
    B = np.column_stack([(transition(z, u+du)-transition(z, u-du))/(2*epsilon)
                         for du in epsilon*np.eye(2)])
    return A, B


def synthesize_augmented(base_cfg, config, frozen_gain):
    runtime = AugmentedRuntime(base_cfg, config)
    eps = base_cfg["simulation"]["finite_difference_epsilon"]
    A, B = linearize(runtime, eps)
    Q = np.zeros((runtime.state_size, runtime.state_size))
    Q[:6, :6] = runtime.dt*np.diag(base_cfg["controller"]["Q_diagonal"])
    R = runtime.dt*np.diag(base_cfg["controller"]["R_diagonal"])
    P = solve_discrete_are(A, B, Q, R)
    K = np.linalg.solve(R+B.T@P@B, B.T@P@A)
    residual = A.T@P@A-P-A.T@P@B@K+Q
    poles = np.linalg.eigvals(A-B@K)
    if max(abs(poles)) >= 1:
        raise ValueError("Augmented sampled closed-loop is unstable")
    C = np.concatenate([np.linalg.matrix_power(A, i)@B for i in range(len(A))], axis=1)
    singular = np.linalg.svd(C, compute_uv=False)
    tolerance = max(C.shape)*np.finfo(float).eps*singular[0]
    fixed = np.zeros_like(K)
    fixed[:, :6] = frozen_gain
    record = {name: value.tolist() for name, value in {
        "A_discrete_actual": A, "B_discrete_actual": B, "Q_discrete": Q,
        "R_discrete": R, "P_DARE": P, "K_used": K,
    }.items()}
    record.update(
        design="CONDITIONAL delay+lag state-augmented DARE; NOT frozen nominal gains",
        feedback="cached measured six-state + command-only reconstructed torque + clipped history",
        cost="unchanged nominal Q/R; zero added-state penalties; R penalizes issued command",
        delay_s=config.delay_s, motor_time_constant_s=list(config.motor_time_constant_s),
        dt_s=runtime.dt, integration_max_step_s=config.integration_max_step_s,
        history_steps=runtime.history_steps, state_dimension=runtime.state_size,
        state_order=[*base_cfg["controller"]["state_order"], "wheel_torque_estimate_Nm",
                     "hip_torque_estimate_Nm"] +
                    [f"previous_{i}_{a}_command_Nm" for i in range(1, runtime.history_steps+1)
                     for a in ("wheel", "hip")],
        K_sha256=gain_hash(K), epsilon=eps,
        DARE_relative_residual=float(np.linalg.norm(residual)/np.linalg.norm(Q)),
        open_loop_eigenvalues=eigenvalues(A),
        frozen_gain_augmented_plant_eigenvalues=eigenvalues(A-B@fixed),
        closed_loop_eigenvalues=eigenvalues(A-B@K),
        max_closed_loop_pole_magnitude=float(max(abs(poles))),
        controllability={"rank": int(np.sum(singular > tolerance)),
                         "singular_values": singular.tolist(), "rank_tolerance": float(tolerance),
                         "condition_number": float(singular[0]/singular[-1])},
        equilibrium_residual=float(np.max(abs(runtime.transition_for_linearization(
            np.zeros(runtime.state_size), np.zeros(2))))),
        limitation="exact known delay/T/zero initial torque; no motor uncertainty or torque sensor",
    )
    return K, record
