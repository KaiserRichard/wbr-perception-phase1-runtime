"""Pure configuration transforms; importing this module does not run physics."""

from copy import deepcopy
import math


DOMAIN_M = (0.12, 0.20)
FAMILY = "assumed-planar-fixed-mass-scaled-leg-v1"
STUDY = "reachable-posture-rays-0.12-0.20-v1"
DEFAULT_LENGTHS = tuple(round(0.12 + i * 0.01, 2) for i in range(9))
EVALUATION_LENGTHS = (0.12, 0.135, 0.16, 0.185, 0.20)
DEFAULT_DELAYS = (0.002, 0.003, 0.004, 0.005)


def check_length(length):
    """Restricted study policy, separate from the general parameter transform."""
    length = float(length)
    if not math.isfinite(length) or not DOMAIN_M[0] <= length <= DOMAIN_M[1]:
        raise ValueError(f"Leg length must be finite and within {DOMAIN_M} m")
    return length


def training_midpoints(lengths):
    """Use actual training intervals, with no extrapolation or rounded queries."""
    lengths = sorted(check_length(length) for length in lengths)
    if (len(lengths) < 2 or len(set(lengths)) != len(lengths) or
            (lengths[0], lengths[-1]) != DOMAIN_M):
        raise ValueError("Training lengths must be unique and span the restricted domain")
    return [(left + right) / 2 for left, right in zip(lengths, lengths[1:])]


def config_at_length(reference, length):
    """Pure positive-length transform, NOT a geometric feasibility assertion.

    Keep masses fixed; scale leg COM by L/L0 and COM inertia by (L/L0)^2.
    Other offline model comparisons may request hypothetical lengths; their
    geometry must reject infeasible poses itself. Study entry points separately
    call check_length. Never clamp a requested length into the study domain.
    """
    length = float(length)
    if not math.isfinite(length) or length <= 0:
        raise ValueError("Leg length must be positive and finite")
    cfg = deepcopy(reference)
    p = cfg["physics"]
    original_length = float(p["leg_length"]["value"])
    if not math.isfinite(original_length) or original_length <= 0:
        raise ValueError("Reference leg length must be positive and finite")
    ratio = length / original_length
    values = {
        "leg_length": length,
        "leg_com": p["leg_com"]["value"] * ratio,
        "leg_inertia": p["leg_inertia"]["value"] * ratio**2,
    }
    for name, value in values.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"Invalid scaled {name}")
        p[name].update(value=value, evidence="ASSUMED",
                       source=f"{FAMILY}; see sim/gain_schedule/README.md")
    cfg["label"] = f"ASSUMED leg-length study: L={length:g} m"
    return cfg
