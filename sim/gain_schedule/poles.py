"""Local fitted-feedback pole calculation; no synthesis or rollout here."""

import numpy as np

from sim.gain_schedule.fitting import evaluate_polynomial
from sim.gain_schedule.model import check_length


def check_fitted_poles(regime, length, exact, design, cfg):
    length = check_length(length)
    fitted = evaluate_polynomial(regime["fit"], length)
    exact = np.asarray(exact, float)
    if (fitted.shape != exact.shape or
            regime["state_order"] != design["state_order"] or
            regime["input_order"] != cfg["controller"]["input_order"] or
            fitted.shape != (len(regime["input_order"]), len(regime["state_order"]))):
        raise ValueError("Schedule incompatible with runtime state/input order")
    A = np.asarray(design["A_discrete_actual"], float)
    B = np.asarray(design["B_discrete_actual"], float)
    n = fitted.shape[1]
    dt = float(design["dt_s"])
    if (A.shape != (n, n) or B.shape != (n, 2) or
            not all(np.all(np.isfinite(v)) for v in (A, B, exact)) or
            not np.isfinite(dt) or dt <= 0 or dt != cfg["simulation"]["dt_s"]):
        raise ValueError("Invalid actual runtime linearization or control period")
    poles, vectors = np.linalg.eig(A - B @ fitted)
    if not all(np.all(np.isfinite(v)) for v in (poles, vectors)):
        raise ValueError("Nonfinite closed-loop poles")
    radius = float(np.max(np.abs(poles)))
    return {
        "length_m": length, "delay_s": regime["runtime"]["delay_s"], "dt_s": dt,
        "state_order": regime["state_order"], "input_order": regime["input_order"],
        "feedback": "u=-Kfit*z; poles=eig(Ad_actual-Bd_actual@Kfit)",
        "exact_pole_radius": design["max_closed_loop_pole_magnitude"],
        "Kfit": fitted.tolist(),
        "polynomial_closed_loop_eigenvalues": [[float(p.real), float(p.imag)] for p in poles],
        "right_eigenvectors_by_mode_real_imag": [
            [[float(v.real), float(v.imag)] for v in vector] for vector in vectors.T],
        "eigenpair_note": "Eigenvalue i pairs with vector i in state_order; mixed-unit "
                          "vector entries do not establish a physical mode identity.",
        "polynomial_pole_radius": radius, "margin_to_one": 1 - radius,
        "slowest_time_constant_s": float(-dt / np.log(radius)) if 0 < radius < 1 else None,
        "polynomial_local_status": "PASS" if radius < 1 else "FAIL",
        "max_abs_gain_error": float(np.max(abs(fitted - exact))),
        "relative_frobenius_gain_error": float(np.linalg.norm(fitted - exact) /
                                               max(np.linalg.norm(exact), np.finfo(float).tiny)),
        "gain_error_note": "Diagnostic only: entries combine different state/input units.",
    }
