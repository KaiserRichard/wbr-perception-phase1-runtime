"""Geometric evidence for two fixed posture rays, not a robot motion envelope."""

from copy import deepcopy
import math

import numpy as np

from sim.fivebar.geometry import Geometry
from sim.gain_schedule.model import DOMAIN_M, check_length


def geometry_evidence(reference, lengths):
    """Bound the entire interval analytically, then exercise existing IK/Jacobians.

    For symmetric proximal/distal lengths a,b and half pin spacing h, the
    distances to the two pins satisfy r²=L²+h²±2hL*cos(beta). They increase
    over this interval. Strict |b-a|<r<a+b excludes serial singularities.
    On the outward assembly, distal angles are alpha_A-gamma_A and
    alpha_E+gamma_E, with 0<gamma<=asin(a/b). Bounding their separation
    strictly inside (0,pi) excludes a parallel-distal closure singularity.
    See README for the derivation and scope of this sufficient certificate.
    """
    geometry = Geometry.from_inventory(reference)
    a, b, h = geometry.l1, geometry.l2, geometry.l5 / 2
    lo, hi = DOMAIN_M
    if not (b > a and a + b > h):
        raise ValueError("Interval certificate requires the pinned b>a geometry")
    values = sorted({lo, hi, *(check_length(value) for value in lengths)})
    initial = reference["protocol"]["initial_state"]
    postures = []
    for name, theta, phi in (("upright", 0., 0.),
                             ("balance_start", initial[1], initial[2])):
        beta = math.pi / 2 + theta - phi
        endpoints = [np.array([h + L * math.cos(beta), L * math.sin(beta)])
                     for L in (lo, hi)]
        pin_vectors = [[point - np.array([pin, 0.]) for point in endpoints]
                       for pin in (0., 2*h)]
        radii = [[float(np.linalg.norm(v)) for v in vectors] for vectors in pin_vectors]
        alphas = [[math.atan2(v[1], v[0]) for v in vectors] for vectors in pin_vectors]
        gamma_max = math.asin(a / b)
        ray_limit = (math.sqrt((a+b)**2 - (h*math.sin(beta))**2)
                     - h*abs(math.cos(beta)))
        separation = [min(alphas[1]) - max(alphas[0]),
                      max(alphas[1]) - min(alphas[0]) + 2 * gamma_max]
        # These conditions justify endpoint bounds and the fixed outward branch.
        if not (0 < beta < math.pi and lo > abs(h * math.cos(beta)) and
                all(b-a < r[0] <= r[1] < a+b for r in radii) and
                0 < separation[0] <= separation[1] < math.pi):
            raise ValueError(f"Reachability/nonsingularity certificate failed: {name}")
        samples = []
        for length in values:
            q = geometry.inverse(length, beta, elbows=(1, -1), branch=1)
            cartesian, virtual = geometry.jacobians(q, branch=1)
            samples.append({
                "length_m": length, "motor_angles_rad": q.tolist(),
                "reconstructed_length_beta": geometry.virtual(q).tolist(),
                "cartesian_jacobian": cartesian.tolist(),
                "virtual_jacobian": virtual.tolist(),
                "cartesian_determinant": float(np.linalg.det(cartesian)),
                "virtual_determinant": float(np.linalg.det(virtual)),
                "cartesian_singular_values": np.linalg.svd(cartesian, compute_uv=False).tolist(),
                "virtual_singular_values": np.linalg.svd(virtual, compute_uv=False).tolist(),
            })
        postures.append({
            "name": name, "theta_rad": theta, "body_phi_rad": phi, "beta_rad": beta,
            "serial_radius_bounds_m": radii,
            "strict_serial_radius_limits_m": [b-a, b+a],
            "serial_extension_ray_limit_m": ray_limit,
            "length_margin_to_extension_m": ray_limit - hi,
            "minimum_radius_margin_to_fold_m": min(r[0] - (b-a) for r in radii),
            "minimum_radius_margin_to_extension_m": min(a+b - r[1] for r in radii),
            "distal_angle_separation_bounds_rad": separation,
            "interval_reachable_and_nonsingular": True, "samples": samples,
        })
    return {
        "domain_m": list(DOMAIN_M),
        "source_geometry": deepcopy(reference["source_geometry_inventory_unused"]),
        "max_upright_reach_m": math.sqrt((a+b)**2 - h**2),
        "max_upright_reach_formula": "sqrt((l1+l2)^2-(l5/2)^2); singular boundary",
        "serial_extension_ray_limit_formula": "sqrt((a+b)^2-h^2*sin(beta)^2)-h*abs(cos(beta))",
        "assembly": {"elbows": [1, -1], "branch": 1},
        "postures": postures,
        "limitation": "Source-supported dimensions, not a measured robot range. Hardware "
                      "joint limits UNKNOWN; full motion envelope unvalidated. Certificate "
                      "covers only upright and declared balance-start posture rays.",
    }
