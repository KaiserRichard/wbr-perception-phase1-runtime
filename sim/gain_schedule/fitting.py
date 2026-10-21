"""Small NumPy-only Chebyshev least-squares fitter, independent of the plant."""

import numpy as np
from numpy.polynomial.chebyshev import chebvander

from sim.gain_schedule.model import DOMAIN_M


BASIS = "Chebyshev T_j(x), x=(2*L-L_min-L_max)/(L_max-L_min)"


def _domain(domain):
    domain = np.asarray(domain, dtype=float)
    if domain.shape != (2,) or not np.all(np.isfinite(domain)) or domain[0] >= domain[1]:
        raise ValueError("Domain must contain two finite increasing endpoints")
    return domain


def _coordinates(lengths, domain):
    values = np.asarray(lengths, dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("Lengths must be finite")
    if np.any(values < domain[0]) or np.any(values > domain[1]):
        raise ValueError("Length outside fitted domain; extrapolation is prohibited")
    return (2 * values - domain[0] - domain[1]) / (domain[1] - domain[0])


def fit_polynomial(lengths, gains, *, degree=3, domain=DOMAIN_M,
                   max_condition=1e8):
    """Fit each K entry with the same unweighted, scaled design matrix.

    Coefficients are ordered [increasing Chebyshev degree, actuator, state].
    No stability claim follows from a small coefficient fitting residual.
    """
    lengths, gains = np.asarray(lengths, float), np.asarray(gains, float)
    domain = _domain(domain)
    if lengths.ndim != 1 or len(lengths) == 0:
        raise ValueError("Expected a nonempty vector of sample lengths")
    if isinstance(degree, bool) or not isinstance(degree, (int, np.integer)) or degree < 0:
        raise ValueError("Degree must be a nonnegative integer")
    if len(lengths) <= degree or len(np.unique(lengths)) != len(lengths):
        raise ValueError("Need unique lengths and more samples than the degree")
    if gains.ndim != 3 or gains.shape[0] != len(lengths) or gains.shape[1] != 2 or gains.shape[2] < 1:
        raise ValueError("Gains must have shape [sample, 2 actuators, state]")
    if not np.all(np.isfinite(gains)):
        raise ValueError("Gains must be finite")
    if not np.isfinite(max_condition) or max_condition < 1:
        raise ValueError("max_condition must be finite and at least one")
    x = _coordinates(lengths, domain)
    if lengths.min() != domain[0] or lengths.max() != domain[1]:
        raise ValueError("Samples must include both domain endpoints")
    V = chebvander(x, degree)
    target = gains.reshape(len(lengths), -1)
    coefficients, _, rank, singular = np.linalg.lstsq(V, target, rcond=None)
    condition = float(singular[0] / singular[-1])
    if rank != degree + 1 or not np.isfinite(condition) or condition > max_condition:
        raise ValueError("Rank-deficient or ill-conditioned Chebyshev fit")
    residual = (V @ coefficients - target).reshape(gains.shape)
    raw_condition = float(np.linalg.cond(np.vander(lengths, degree + 1, increasing=True)))
    return {
        "schema_version": 1,
        "basis": BASIS,
        "domain_m": domain.tolist(),
        "degree": int(degree),
        "out_of_domain": "error",
        "coefficient_order": ["Chebyshev_degree", "actuator", "state"],
        "coefficients": coefficients.reshape(degree + 1, *gains.shape[1:]).tolist(),
        "diagnostics": {
            "sample_lengths_m": lengths.tolist(),
            "sample_count": len(lengths),
            "rank": int(rank),
            "singular_values": singular.tolist(),
            "condition_number_2": condition,
            "maximum_allowed_condition_number": float(max_condition),
            "raw_metre_power_basis_condition_number_2": raw_condition if np.isfinite(raw_condition) else None,
            "entry_max_abs_error": np.max(abs(residual), axis=0).tolist(),
            "entry_rmse": np.sqrt(np.mean(residual**2, axis=0)).tolist(),
            "max_abs_error": float(np.max(abs(residual))),
            "relative_frobenius_error": float(np.linalg.norm(residual) /
                                            max(np.linalg.norm(gains), np.finfo(float).tiny)),
        },
        "validation": "training fit only; no stability or nonlinear acceptance claim",
    }


def evaluate_polynomial(fit, lengths):
    """Return [2, state] for a scalar, or [sample, 2, state] for a vector.

    Reject nonfinite/out-of-domain inputs; never silently clamp or extrapolate.
    """
    if (fit.get("schema_version") != 1 or fit.get("basis") != BASIS or
            fit.get("out_of_domain") != "error"):
        raise ValueError("Unsupported fit format or domain policy")
    degree = fit["degree"]
    coefficients = np.asarray(fit["coefficients"], float)
    if (isinstance(degree, bool) or not isinstance(degree, int) or degree < 0 or
            coefficients.ndim != 3 or coefficients.shape[0] != degree + 1 or
            coefficients.shape[1] != 2 or coefficients.shape[2] < 1 or
            not np.all(np.isfinite(coefficients))):
        raise ValueError("Invalid polynomial coefficients")
    values = np.asarray(lengths, float)
    if values.ndim > 1:
        raise ValueError("Expected a scalar or vector of lengths")
    x = _coordinates(values, _domain(fit["domain_m"]))
    prediction = np.tensordot(chebvander(x, degree), coefficients, axes=([-1], [0]))
    return prediction[0] if values.ndim == 0 else prediction
