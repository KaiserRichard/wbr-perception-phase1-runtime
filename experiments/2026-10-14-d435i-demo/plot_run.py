#!/usr/bin/env python3
"""Offline ORB-SLAM3 EuRoC trajectory plot and diagnostics; no gate verdicts."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys

# Keep Matplotlib's writable cache beside this helper, including on the Mac.
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(__file__).resolve().parent / ".cache"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize

MAX_TIME_DIFF_S = 0.02
POWER_SAMPLE = re.compile(
    r"^\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d\S*.*?\bthrottled=(0x[0-9a-fA-F]+)\b"
)


def read_trajectory(path, timestamp_divisor, allow_empty=False):
    """Read eight-column trajectories in file order; never hide clock reversals."""
    rows = []
    with path.open() as handle:
        for number, line in enumerate(handle, 1):
            fields = line.partition("#")[0].split()
            if not fields:
                continue
            try:
                if len(fields) != 8:
                    raise ValueError("expected eight columns")
                row = [float(value) for value in fields]
                if not np.isfinite(row).all():
                    raise ValueError("nonfinite value")
                if np.linalg.norm(row[4:]) == 0:
                    raise ValueError("zero quaternion")
                rows.append(row)
            except ValueError as error:
                raise ValueError(f"{path}:{number}: {error}") from error
    data = np.asarray(rows, dtype=float).reshape(-1, 8)
    if not len(data) and not allow_empty:
        raise ValueError(f"{path}: no poses")
    # Division matches the historical ns-to-TUM conversion. Multiplying by
    # 1e-9 rounds epoch timestamps differently near nearest-GT sample ties.
    data[:, 0] /= timestamp_divisor
    if np.any(np.diff(data[:, 0]) <= 0):
        raise ValueError(f"{path}: duplicate or backward trajectory timestamps")
    return data


def find_trajectories(run_dir):
    frames = sorted(run_dir.glob("f_*.txt"))
    if len(frames) != 1:
        raise ValueError(f"{run_dir}: expected exactly one f_*.txt; found {len(frames)}. "
                         "Put each trajectory pair in its own run directory.")
    keyframes = run_dir / ("kf_" + frames[0].name[2:])
    other_keyframes = set(run_dir.glob("kf_*.txt")) - {keyframes}
    if other_keyframes:
        raise ValueError(f"{run_dir}: unmatched keyframe files: {sorted(map(str, other_keyframes))}")
    return frames[0], keyframes if keyframes.exists() else None


def timing_stats(times):
    times = np.asarray(times, dtype=float)
    steps = np.diff(times)
    span = float(times[-1] - times[0]) if len(times) else 0.0
    valid = len(times) > 1 and np.all(steps > 0)
    return {"count": len(times), "duration_s": span,
            "rate_hz": float((len(times) - 1) / span) if valid else None,
            "max_gap_s": float(max(steps)) if len(steps) else None,
            "nonpositive_steps": int(np.count_nonzero(steps <= 0))}


def stream_stats(path):
    streams = {}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"stream", "index", "sdk_ms", "domain", "host_steady_ns"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: missing timestamp audit columns")
        for number, row in enumerate(reader, 2):
            try:
                key = f"{row['stream']}:{int(row['index'])}"
                sdk = float(row["sdk_ms"]) / 1000.0
                host = int(row["host_steady_ns"]) / 1e9
                if not np.isfinite([sdk, host]).all():
                    raise ValueError("nonfinite timestamp")
                values = streams.setdefault(key, {"sdk": [], "host": [], "domains": set()})
                values["sdk"].append(sdk)
                values["host"].append(host)
                values["domains"].add(row["domain"])
            except (ValueError, TypeError) as error:
                raise ValueError(f"{path}:{number}: invalid timestamp audit: {error}") from error
    result = {}
    for key, values in sorted(streams.items()):
        stats = timing_stats(values["sdk"])
        stats["clock"] = "sdk_ms / 1000"
        stats["domains"] = sorted(values["domains"])
        stats["host_steady"] = timing_stats(values["host"])
        if len(values["domains"]) != 1:
            stats["rate_hz"] = None
            stats["max_gap_s"] = None
        result[key] = stats
    return result


def power_stats(run_dir):
    """Count UTC raw samples only, excluding hex summary/historical latch bits."""
    candidates = []
    for path in sorted(set(run_dir.glob("*.log")) | set(run_dir.glob("*.txt"))):
        if path.name.startswith(("f_", "kf_")):
            continue
        flags = []
        with path.open(errors="replace") as handle:
            for line in handle:
                match = POWER_SAMPLE.search(line)
                if match:
                    flags.append(int(match.group(1), 16))
        if flags:
            candidates.append((path, flags))
    if len(candidates) > 1:
        raise ValueError("Multiple power logs contain UTC samples; keep one in RUN_DIR")
    if not candidates:
        return None
    path, flags = candidates[0]
    return {"source": path.name, "samples": len(flags),
            "live_bits_0_3_fraction": sum(bool(flag & 0xF) for flag in flags) / len(flags),
            "live_undervoltage_bit_0_fraction": sum(bool(flag & 1) for flag in flags) / len(flags),
            "per_live_bit_fraction": {str(bit): sum(bool(flag & (1 << bit)) for flag in flags)
                                      / len(flags) for bit in range(4)},
            "interpretation": "sample fraction, not time-weighted; bits 16-19 excluded"}


def associate(estimate, reference, max_diff=MAX_TIME_DIFF_S):
    """Nearest-time association from the sparser sequence, as in evo; no interpolation."""
    est_shorter = len(estimate) <= len(reference)
    short, long = (estimate, reference) if est_shorter else (reference, estimate)
    short_ids, long_ids = [], []
    for index, stamp in enumerate(short[:, 0]):
        insertion = int(np.searchsorted(long[:, 0], stamp))
        choices = [i for i in (insertion - 1, insertion) if 0 <= i < len(long)]
        nearest = min(choices, key=lambda i: (abs(long[i, 0] - stamp), i))
        if abs(long[nearest, 0] - stamp) <= max_diff:
            short_ids.append(index)
            long_ids.append(nearest)
    if len(short_ids) < 3:
        raise ValueError("ATE needs at least three timestamp matches within 0.02 s")
    pair = short[short_ids], long[long_ids]
    return pair if est_shorter else pair[::-1]


def align_se3(source, target):
    """Umeyama rigid alignment: target ~= source @ rotation.T + translation; scale=1."""
    source_mean, target_mean = source.mean(axis=0), target.mean(axis=0)
    centered_source, centered_target = source - source_mean, target - target_mean
    covariance = centered_target.T @ centered_source / len(source)
    u, singular, vt = np.linalg.svd(covariance)
    if singular[0] == 0 or singular[1] <= singular[0] * np.finfo(float).eps * 3:
        raise ValueError("SE3 alignment is underconstrained (stationary or collinear matches)")
    correction = np.eye(3)
    correction[2, 2] = -1 if np.linalg.det(u @ vt) < 0 else 1
    rotation = u @ correction @ vt
    translation = target_mean - rotation @ source_mean
    return rotation, translation


def ate_stats(estimate, reference):
    matched_est, matched_ref = associate(estimate, reference)
    rotation, translation = align_se3(matched_est[:, 1:4], matched_ref[:, 1:4])
    errors = np.linalg.norm(matched_est[:, 1:4] @ rotation.T + translation
                            - matched_ref[:, 1:4], axis=1)
    return {"alignment": "SE3 Umeyama (scale fixed at 1)",
            "association": "nearest timestamp from sparser sequence; no interpolation or offset",
            "max_time_diff_s": MAX_TIME_DIFF_S, "matched_poses": len(errors),
            "rmse_m": float(np.sqrt(np.mean(errors ** 2))),
            "mean_m": float(errors.mean()), "median_m": float(np.median(errors)),
            "max_m": float(errors.max()),
            "rotation_estimate_to_gt": rotation.tolist(),
            "translation_estimate_to_gt_m": translation.tolist()}


def quaternion_rotation(quaternion):
    x, y, z, w = quaternion / np.linalg.norm(quaternion)
    return np.array([[1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
                     [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
                     [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)]])


def keyframes_in_frame_coordinates(poses, keyframes):
    """Reconcile upstream EuRoC exports using a shared timestamp and full pose.

    System.cc:689-695/753 rebases frame poses; 1098-1101 exports keyframes in
    map coordinates. Both export body poses in the inertial mode.
    """
    if not len(keyframes):
        return keyframes, None
    shared = []
    for keyframe in keyframes:
        insertion = int(np.searchsorted(poses[:, 0], keyframe[0]))
        choices = [i for i in (insertion - 1, insertion) if 0 <= i < len(poses)]
        nearest = min(choices, key=lambda i: abs(poses[i, 0] - keyframe[0]))
        if abs(poses[nearest, 0] - keyframe[0]) <= 1e-6:
            shared.append((poses[nearest], keyframe))
    if not shared:
        raise ValueError("No shared frame/keyframe timestamp within 1 us; cannot reconcile export coordinates")
    frame, keyframe = shared[0]
    rotation = quaternion_rotation(frame[4:]) @ quaternion_rotation(keyframe[4:]).T
    translation = frame[1:4] - rotation @ keyframe[1:4]
    converted = keyframes.copy()
    converted[:, 1:4] = keyframes[:, 1:4] @ rotation.T + translation
    residuals = [np.linalg.norm(k[1:4] @ rotation.T + translation - f[1:4]) for f, k in shared]
    info = {"method": "shared-timestamp full-pose rigid transform, keyframes into frame export coordinates",
            "shared_poses": len(shared), "max_shared_position_residual_m": float(max(residuals)),
            "rotation": rotation.tolist(), "translation_m": translation.tolist()}
    # A material mismatch suggests different maps/exports, not something to fit away.
    if max(residuals) > 0.01:
        raise ValueError("Keyframe/frame export mismatch exceeds 0.01 m after coordinate reconciliation")
    return converted, info


def plot_trajectory(poses, keyframes, output, title):
    positions, elapsed = poses[:, 1:4], poses[:, 0] - poses[0, 0]
    norm = Normalize(0, max(float(elapsed[-1]), 1e-9))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), layout="constrained")
    for axis, dimensions, name in zip(axes, [(0, 1), (0, 2)], ["Top view XY", "Side view XZ"]):
        points = positions[:, dimensions]
        segments = np.stack([points[:-1], points[1:]], axis=1)
        path = LineCollection(segments, cmap="viridis", norm=norm, linewidths=1.6)
        path.set_array((elapsed[:-1] + elapsed[1:]) / 2)
        axis.add_collection(path)
        # Scatter also makes single-pose runs visible.
        axis.scatter(points[:, 0], points[:, 1], c=elapsed, cmap="viridis", norm=norm, s=3)
        if len(keyframes):
            axis.scatter(keyframes[:, 1 + dimensions[0]], keyframes[:, 1 + dimensions[1]],
                         s=18, marker="x", c="black", linewidths=0.7, label="Keyframes")
        axis.scatter(*points[0], s=90, marker="o", c="limegreen", edgecolors="black", label="Start", zorder=5)
        axis.scatter(*points[-1], s=110, marker="*", c="red", edgecolors="black", label="End", zorder=6)
        axis.autoscale()
        axis.margins(0.08)
        axis.set_aspect("equal", adjustable="box")
        axis.set(xlabel="X [m]", ylabel=f"{'Y' if dimensions[1] == 1 else 'Z'} [m]", title=name)
        axis.grid(alpha=0.25)
        axis.legend(loc="best", fontsize=8)
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap="viridis"), ax=axes, label="Elapsed trajectory time [s]")
    fig.suptitle(title + "\nExport coordinate frame; projections do not establish gravity alignment", fontsize=11)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze_run(run_dir, gt=None):
    frame_path, keyframe_path = find_trajectories(run_dir)
    poses = read_trajectory(frame_path, 1e9)
    keyframes = read_trajectory(keyframe_path, 1e9, allow_empty=True) if keyframe_path else np.empty((0, 8))
    positions = poses[:, 1:4]
    timing = timing_stats(poses[:, 0])
    stats = {"duration_s": timing["duration_s"],
             "path_length_m": float(np.linalg.norm(np.diff(positions, axis=0), axis=1).sum()),
             "extent_m": dict(zip("xyz", np.ptp(positions, axis=0).tolist())),
             "bounds_m": {"min_xyz": positions.min(axis=0).tolist(), "max_xyz": positions.max(axis=0).tolist()},
             "num_poses": len(poses), "num_keyframes": len(keyframes), "pose_rate_hz": timing["rate_hz"],
             "inputs_sha256": {frame_path.name: digest(frame_path)},
             "notes": ["Offline diagnostics only; pose rate uses exported trajectory time, not wall time.",
                       "Path length sums adjacent exported positions; tracking gaps can inflate it.",
                       "Missing optional evidence is omitted; no hardware PASS is implied."]}
    if keyframe_path:
        stats["inputs_sha256"][keyframe_path.name] = digest(keyframe_path)
    plot_keyframes, coordinate_info = keyframes_in_frame_coordinates(poses, keyframes)
    if coordinate_info is not None:
        stats["keyframe_coordinates"] = coordinate_info
    audit = run_dir / "timestamps.csv"
    if audit.exists():
        stats["streams"] = stream_stats(audit)
        stats["inputs_sha256"][audit.name] = digest(audit)
    power = power_stats(run_dir)
    if power is not None:
        stats["power"] = power
        stats["inputs_sha256"][power["source"]] = digest(run_dir / power["source"])
    title = f"{run_dir.name}: {len(poses)} poses, {len(keyframes)} keyframes"
    if gt is not None:
        stats["ate"] = ate_stats(poses, read_trajectory(gt, 1.0))
        stats["gt"] = {"path": str(gt.resolve()), "sha256": digest(gt)}
        title += f" | SE3 ATE RMSE {stats['ate']['rmse_m']:.6f} m"
    # Parse and evaluate everything before writing any result.
    plot_trajectory(poses, plot_keyframes, run_dir / "demo_plot.png", title)
    (run_dir / "demo_stats.json").write_text(json.dumps(stats, indent=2, allow_nan=False) + "\n")
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--gt", type=Path, help="Ground truth in TUM format (timestamps in seconds)")
    args = parser.parse_args()
    try:
        stats = analyze_run(args.run_dir, args.gt)
    except (OSError, ValueError, np.linalg.LinAlgError) as error:
        print(f"plot_run: {error}", file=sys.stderr)
        return 2
    print(f"Saved {args.run_dir / 'demo_plot.png'} and {args.run_dir / 'demo_stats.json'}")
    if "ate" in stats:
        print(f"SE3 ATE RMSE: {stats['ate']['rmse_m']:.9f} m ({stats['ate']['matched_poses']} matches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
