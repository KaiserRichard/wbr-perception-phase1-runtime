#!/usr/bin/env python3
"""Offline independent regression against the already installed evo core API."""
import json
from pathlib import Path

import numpy as np
import plot_run
from evo.core import sync
from evo.core.trajectory import PoseTrajectory3D

ROOT = Path(__file__).resolve().parent
HISTORY = ROOT.parent / "2026-10-13-n4a-euroc-mh01"


def evo_trajectory(path, divisor):
    data = np.loadtxt(path)
    return PoseTrajectory3D(positions_xyz=data[:, 1:4],
                            orientations_quat_wxyz=data[:, [7, 4, 5, 6]],
                            timestamps=data[:, 0] / divisor)


def main():
    # Independent reading, association, and rigid alignment through evo.
    gt = evo_trajectory(HISTORY / "eval/gt_data.tum", 1)
    est = evo_trajectory(HISTORY / "run1/f_mh01_stereoi.txt", 1e9)
    gt, est = sync.associate_trajectories(gt, est, max_diff=0.02)
    est.align(gt, correct_scale=False)
    errors = np.linalg.norm(est.positions_xyz - gt.positions_xyz, axis=1)
    evo_rmse = float(np.sqrt(np.mean(errors ** 2)))
    helper = json.loads((ROOT / "example_run1/demo_stats.json").read_text())["ate"]
    if abs(evo_rmse - helper["rmse_m"]) > 1e-10:
        raise AssertionError("helper differs from installed evo")
    if abs(helper["rmse_m"] - 0.041461) > 0.5e-6:
        raise AssertionError("helper differs from the historical six-decimal evo result")
    if helper["matched_poses"] != est.num_poses:
        raise AssertionError("association count differs")
    for name in ("f_mh01_stereoi.txt", "kf_mh01_stereoi.txt"):
        if plot_run.digest(ROOT / "example_run1" / name) != plot_run.digest(HISTORY / "run1" / name):
            raise AssertionError("example input differs from historical evidence")
    print(f"helper RMSE: {helper['rmse_m']:.12f} m")
    print(f"evo RMSE:    {evo_rmse:.12f} m ({est.num_poses} associated poses)")
    print("Historical evo: 0.041461 m; copied trajectory SHA-256 values match originals.")


if __name__ == "__main__":
    main()
