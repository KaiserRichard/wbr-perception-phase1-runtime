"""Robust ground-plane estimation for ROS optical-frame depth images.

Plane equation is n dot p + d = 0, with unit n oriented toward the camera.
Thus d is camera height above the plane and signed height is n dot p + d.
Pitch is positive when the optical axis points down; roll is positive for a
right-handed rotation about optical +z. Reported angles describe n relative
to the nominal level-camera normal [0, -1, 0].
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class PlaneEstimate:
    normal: np.ndarray
    offset: float
    camera_height: float
    pitch: float
    roll: float
    inlier_count: int
    valid: bool
    inlier_mask: np.ndarray


def backproject(depth, fx=386.953, fy=386.953, cx=321.034, cy=241.040, stride=1):
    """Return Nx3 camera-frame points and their (row, col) pixel indices."""
    dep = np.asarray(depth, dtype=float)
    if dep.ndim != 2 or stride < 1:
        raise ValueError("depth must be 2D and stride >= 1")
    rows, cols = np.mgrid[0:dep.shape[0]:stride, 0:dep.shape[1]:stride]
    z = dep[::stride, ::stride]
    good = np.isfinite(z) & (z > 0)
    rr, cc, zz = rows[good], cols[good], z[good]
    pts = np.column_stack(((cc-cx)*zz/fx, (rr-cy)*zz/fy, zz))
    return pts, np.column_stack((rr, cc))


def _normal_angles(n):
    # Separate roll from tilt using the projected normal. This convention is
    # exact for pure pitch and pure roll and remains well-defined near level.
    pitch = np.arctan2(-n[2], -n[1])
    roll = np.arctan2(n[0], np.hypot(n[1], n[2]))
    return float(pitch), float(roll)


def estimate_plane(depth, *, fx=386.953, fy=386.953, cx=321.034, cy=241.040,
                   stride=1, iterations=160, threshold=0.012, seed=0,
                   prior=None, max_deviation=None, min_inliers=100,
                   min_height=0.05):
    """Estimate plane with 3-point RANSAC and SVD refinement.

    prior may be ``(normal, camera_height)``. ``max_deviation`` is a tuple
    (maximum normal angular deviation in radians, maximum height deviation m).
    The prior is a hypothesis gate; final results are still fitted to data.
    """
    pts, indices = backproject(depth, fx, fy, cx, cy, stride)
    empty = PlaneEstimate(np.full(3, np.nan), np.nan, np.nan, np.nan, np.nan,
                          0, False, np.zeros(len(pts), dtype=bool))
    if len(pts) < max(3, min_inliers):
        return empty
    rng = np.random.default_rng(seed)
    best = None
    if prior is not None:
        pn = np.array(prior[0], dtype=float, copy=True); pn /= np.linalg.norm(pn)
        ph = float(prior[1])
        if max_deviation is None:
            max_deviation = (np.deg2rad(12), 0.10)
    else:
        pn = None; ph = None
    for _ in range(iterations):
        ids = rng.choice(len(pts), 3, replace=False)
        a, b, c = pts[ids]
        n = np.cross(b-a, c-a); norm = np.linalg.norm(n)
        if norm < 1e-10:
            continue
        n /= norm
        d = -float(n @ a)
        if d < 0:
            n, d = -n, -d
        # A plane through (or almost through) the camera centre has no defined
        # side; real data hit this when the view was filled by a near wall.
        if d < min_height:
            continue
        if pn is not None:
            ang = np.arccos(np.clip(n @ pn, -1, 1))
            # n faces the camera (d > 0), so a floor below the camera points
            # along the prior; surfaces above the camera (seat/desk undersides)
            # point the opposite way and are rejected.
            if ang > max_deviation[0] or abs(d-ph) > max_deviation[1]:
                continue
        residual = np.abs(pts @ n + d)
        mask = residual <= threshold
        count = int(mask.sum())
        if best is None or count > best[0]:
            best = count, mask
    if best is None or best[0] < min_inliers:
        return empty
    mask = best[1]
    cloud = pts[mask]
    center = cloud.mean(axis=0)
    _, _, vh = np.linalg.svd(cloud-center, full_matrices=False)
    n = vh[-1]
    d = -float(n @ center)
    if d < 0:
        n, d = -n, -d
    # Re-evaluate support after least-squares refinement.
    mask = np.abs(pts @ n+d) <= threshold
    if d < min_height or mask.sum() < min_inliers:
        return empty
    pitch, roll = _normal_angles(n)
    return PlaneEstimate(n, d, d, pitch, roll, int(mask.sum()), True, mask)
