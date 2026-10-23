"""Stream RGB-D messages from a ROS 2 MCAP through the offline obstacle detector."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
from collections import Counter, deque

import numpy as np
from mcap_ros2.reader import read_ros2_messages
from mcap.reader import make_reader

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.obstacle_decision.detect import Params, process_frame
from tools.obstacle_decision.decide import DecisionParams, update

DEPTH_TOPICS = (
    "/camera/camera/aligned_depth_to_color/image_raw",
    "/camera/camera/depth/image_rect_raw",
)
INFO_TOPICS = (
    "/camera/camera/color/camera_info",
    "/camera/camera/depth/camera_info",
)


def _stamp_ns(msg):
    stamp = msg.header.stamp
    return int(stamp.sec) * 1_000_000_000 + int(stamp.nanosec)


def _message_type(msg):
    return getattr(msg, "encoding", "")


def decode_depth(msg):
    """Decode a ROS Image into metres, honoring row step and common depth encodings."""
    encoding = _message_type(msg).upper()
    h, w, step = int(msg.height), int(msg.width), int(msg.step)
    raw = memoryview(msg.data)
    if encoding in ("16UC1", "MONO16"):
        dtype = np.dtype("<u2" if getattr(msg, "is_bigendian", 0) == 0 else ">u2")
        row = np.frombuffer(raw, dtype=dtype, count=(step // 2) * h).reshape(h, step // 2)[:, :w]
        return row.astype(np.float32) * 0.001
    if encoding == "32FC1":
        dtype = np.dtype("<f4" if getattr(msg, "is_bigendian", 0) == 0 else ">f4")
        row = np.frombuffer(raw, dtype=dtype, count=(step // 4) * h).reshape(h, step // 4)[:, :w]
        return row.astype(np.float32)
    raise ValueError(f"unsupported depth image encoding {encoding!r}; expected 16UC1 or 32FC1")


def _intrinsics(msg):
    k = np.asarray(msg.k, dtype=float).reshape(3, 3)
    if not np.isfinite(k).all() or k[0, 0] <= 0 or k[1, 1] <= 0:
        raise ValueError("camera_info has invalid pinhole intrinsics")
    return k


def _quantiles(vals):
    a = np.asarray(vals, dtype=float)
    a = a[np.isfinite(a)]
    if not len(a):
        return {"median": None, "iqr": None}
    q1, med, q3 = np.percentile(a, [25, 50, 75])
    return {"median": float(med), "iqr": float(q3 - q1)}


def _resolve_topics(path, depth_topic=None, info_topic=None):
    found = {}
    with Path(path).open("rb") as stream:
        summary = make_reader(stream).get_summary()
    if summary is not None:
        schemas = summary.schemas
        for channel in summary.channels.values():
            schema = schemas.get(channel.schema_id)
            if schema is not None:
                found[channel.topic] = schema.name
    depths = [t for t in DEPTH_TOPICS if t in found]
    infos = [t for t in INFO_TOPICS if t in found]
    dt = depth_topic or (depths[0] if depths else None)
    it = info_topic or ("/camera/camera/color/camera_info" if dt and "aligned_depth_to_color" in dt and "/camera/camera/color/camera_info" in found else None)
    if not it:
        it = infos[0] if infos else None
    if not dt or not it or dt not in found or it not in found:
        available = ", ".join(f"{t} ({ty})" for t, ty in sorted(found.items())) or "none"
        missing = "depth topic" if not dt or dt not in found else "camera_info topic"
        raise ValueError(f"missing {missing} in {path}; available topics: {available}")
    if not found[dt].endswith("/Image") or not found[it].endswith("/CameraInfo"):
        raise ValueError(f"topic type mismatch: {dt} is {found[dt]}, {it} is {found[it]}")
    return dt, it


def replay_bag(bag, *, depth_topic=None, info_topic=None, stride=1, out="."):
    bag = Path(bag)
    if not bag.is_file():
        raise FileNotFoundError(f"bag file not found: {bag}")
    if stride < 1:
        raise ValueError("stride must be >= 1")
    dt, it = _resolve_topics(bag, depth_topic, info_topic)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    stem = bag.stem
    csv_path, json_path = out / f"{stem}_frames.csv", out / f"{stem}_summary.json"
    params = Params()
    decision_params = DecisionParams()
    plane_state, decision_state = {}, {}
    counts, depths_valid = Counter(), []
    plane_h, obs_d, obs_h, obs_w = [], [], [], []
    pending = deque()
    latest_k = None
    written = 0
    depth_seen = 0

    fields = ["stamp", "plane_valid", "plane_height_m", "plane_pitch_deg", "plane_roll_deg",
              "nearest_obstacle_distance_m", "nearest_obstacle_height_m", "nearest_obstacle_width_m",
              "advisory", "ms", "depth_valid_fraction"]

    def process_depth(item, k, writer):
        nonlocal written, plane_state, decision_state
        msg = item.ros_msg
        depth = decode_depth(msg)
        valid = np.isfinite(depth) & (depth > 0)
        frac = float(valid.mean()) if depth.size else 0.0
        depths_valid.append(frac)
        fr, plane_state = process_frame(depth, k, params, plane_state)
        decision, decision_state = update(fr, decision_state, decision_params)
        counts[decision.advisory.name] += 1
        if fr.plane_valid:
            plane_h.append(fr.plane_height_m)
        if fr.nearest is not None:
            obs_d.append(fr.nearest.distance_m); obs_h.append(fr.nearest.height_m); obs_w.append(fr.nearest.width_m)
        writer.writerow({
            "stamp": f"{_stamp_ns(msg) / 1e9:.9f}", "plane_valid": int(fr.plane_valid),
            "plane_height_m": _finite(fr.plane_height_m), "plane_pitch_deg": _finite(np.rad2deg(fr.plane_pitch_rad)),
            "plane_roll_deg": _finite(np.rad2deg(fr.plane_roll_rad)),
            "nearest_obstacle_distance_m": _finite(fr.nearest.distance_m if fr.nearest else math.nan),
            "nearest_obstacle_height_m": _finite(fr.nearest.height_m if fr.nearest else math.nan),
            "nearest_obstacle_width_m": _finite(fr.nearest.width_m if fr.nearest else math.nan),
            "advisory": decision.advisory.name, "ms": f"{fr.timing_ms:.6f}", "depth_valid_fraction": f"{frac:.8f}",
        })
        written += 1

    with csv_path.open("w", newline="") as fcsv:
        writer = csv.DictWriter(fcsv, fieldnames=fields); writer.writeheader()
        for item in read_ros2_messages(bag, topics=[dt, it]):
            if item.channel.topic == it:
                latest_k = _intrinsics(item.ros_msg)
                # CameraInfo is often emitted once before image messages. Flush frames
                # now that calibration is available; latest calibration is static/valid.
                while pending:
                    process_depth(pending.popleft(), latest_k, writer)
            elif item.channel.topic == dt:
                depth_seen += 1
                if (depth_seen - 1) % stride:
                    continue
                if latest_k is None:
                    pending.append(item)
                else:
                    process_depth(item, latest_k, writer)
    if pending:
        raise ValueError(f"no {it} message available to decode {len(pending)} depth frame(s)")
    summary = {
        "bag_path": str(bag), "depth_topic": dt, "info_topic": it,
        "frame_count": written, "plane_valid_rate": float(len(plane_h) / written) if written else 0.0,
        "static_segment": "all replayed frames (no motion/static metadata in bag)",
        "camera_height_m": _quantiles(plane_h), "obstacle_distance_m": _quantiles(obs_d),
        "obstacle_height_m": _quantiles(obs_h), "obstacle_width_m": _quantiles(obs_w),
        "advisory_histogram": dict(sorted(counts.items())),
        "depth_valid_fraction": float(np.mean(depths_valid)) if depths_valid else 0.0,
        "frames_csv": str(csv_path),
    }
    json_path.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def _finite(x):
    return float(x) if math.isfinite(float(x)) else ""


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bag"); p.add_argument("--depth-topic"); p.add_argument("--info-topic")
    p.add_argument("--stride", type=int, default=1); p.add_argument("--out", default=".")
    a = p.parse_args(argv)
    try:
        result = replay_bag(a.bag, depth_topic=a.depth_topic, info_topic=a.info_topic, stride=a.stride, out=a.out)
    except (ValueError, FileNotFoundError) as exc:
        p.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
