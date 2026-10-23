"""Evaluate recorded RGB-D bags against the mobile-demo tape-measure run sheet."""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import re
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import matplotlib.pyplot as plt
import numpy as np

from tools.obstacle_decision.replay_bag import replay_bag
from tools.obstacle_decision.decide import DecisionParams, Advisory

REQUIRED = ("run_id", "bag_path", "box_height_m", "box_front_distance_m", "box_width_m",
            "lateral_offset_m", "camera_height_m", "camera_tilt_deg", "floor_type", "notes")


def read_run_sheet(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"run sheet missing required columns: {', '.join(missing)}")
        rows = []
        seen = set()
        for line, row in enumerate(reader, 2):
            rid = (row.get("run_id") or "").strip()
            bag = (row.get("bag_path") or "").strip()
            if not rid or not bag:
                raise ValueError(f"run sheet line {line}: run_id and bag_path are required")
            if rid in seen:
                raise ValueError(f"run sheet line {line}: duplicate run_id {rid!r}")
            seen.add(rid)
            parsed = dict(row)
            parsed["run_id"], parsed["bag_path"] = rid, bag
            for col in REQUIRED[2:8]:
                try: parsed[col] = float(row[col])
                except (TypeError, ValueError): raise ValueError(f"run sheet line {line}: {col} must be numeric")
                if not math.isfinite(parsed[col]): raise ValueError(f"run sheet line {line}: {col} must be finite")
            rows.append(parsed)
    return rows


def evaluate_runs(sheet, out=".", *, stride=1, depth_topic=None, info_topic=None):
    rows = read_run_sheet(sheet)
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    base = Path(sheet).resolve().parent
    policy = DecisionParams()
    results = []
    for row in rows:
        bag = Path(row["bag_path"])
        if not bag.is_absolute(): bag = base / bag
        run_dir = out / re.sub(r"[^A-Za-z0-9_.-]+", "_", row["run_id"])
        summary = replay_bag(bag, depth_topic=depth_topic, info_topic=info_topic, stride=stride, out=run_dir)
        height = summary["obstacle_height_m"]["median"]
        distance = summary["obstacle_distance_m"]["median"]
        width = summary["obstacle_width_m"]["median"]
        camera = summary["camera_height_m"]["median"]
        estimated_advisory = max(summary["advisory_histogram"], key=summary["advisory_histogram"].get) if summary["advisory_histogram"] else "UNCERTAIN"
        measured_h = row["box_height_m"]
        expected = ("STOP_CANDIDATE" if measured_h > policy.jump_max_h else
                    "JUMP_CANDIDATE" if policy.jump_min_h <= measured_h <= policy.jump_max_h else "UNCERTAIN")
        result = {
            "run_id": row["run_id"], "bag_path": str(bag), "measured_height_m": measured_h,
            "estimated_height_m": height, "height_error_m": _err(height, measured_h),
            "measured_distance_m": row["box_front_distance_m"], "estimated_distance_m": distance,
            "distance_error_m": _err(distance, row["box_front_distance_m"]),
            "measured_width_m": row["box_width_m"], "estimated_width_m": width,
            "width_error_m": _err(width, row["box_width_m"]),
            "measured_camera_height_m": row["camera_height_m"], "estimated_camera_height_m": camera,
            "camera_height_error_m": _err(camera, row["camera_height_m"]),
            "expected_advisory": expected, "estimated_advisory": estimated_advisory,
            "advisory_correct": estimated_advisory == expected, "advisory_histogram": summary["advisory_histogram"],
            "frame_count": summary["frame_count"], "plane_valid_rate": summary["plane_valid_rate"],
            "depth_valid_fraction": summary["depth_valid_fraction"], "floor_type": row["floor_type"], "notes": row["notes"],
        }
        results.append(result)
    (out / "evaluation.json").write_text(json.dumps({"thresholds": {"jump_min_h_m": policy.jump_min_h,
        "jump_max_h_m": policy.jump_max_h, "near_m": policy.near_m}, "runs": results}, indent=2) + "\n")
    _write_markdown(out / "evaluation.md", results, policy)
    _plots(out, results)
    return results


def _err(est, measured):
    return None if est is None else float(est - measured)


def _write_markdown(path, rows, policy):
    cols = ["run_id", "height measured/estimated (m)", "height error (m)",
            "distance measured/estimated (m)", "distance error (m)", "width error (m)",
            "camera-height error (m)", "advisory expected/estimated", "correct"]
    lines = ["# RGB-D bag evaluation", "", f"Advisory thresholds: jump height {policy.jump_min_h:.3f}–{policy.jump_max_h:.3f} m; near range {policy.near_m:.2f} m.",
             "Geometry estimates are medians over all replayed frames with a finite estimate. Missing estimates are shown as `n/a`.", "",
             "| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        vals = [r["run_id"], _pair(r["measured_height_m"], r["estimated_height_m"]), _fmt(r["height_error_m"]),
                _pair(r["measured_distance_m"], r["estimated_distance_m"]), _fmt(r["distance_error_m"]),
                _fmt(r["width_error_m"]), _fmt(r["camera_height_error_m"]),
                f"{r['expected_advisory']} / {r['estimated_advisory']}", "yes" if r["advisory_correct"] else "no"]
        lines.append("| " + " | ".join(vals) + " |")
    path.write_text("\n".join(lines) + "\n")


def _plots(out, rows):
    valid = [r for r in rows if r["estimated_height_m"] is not None]
    fig, ax = plt.subplots(figsize=(6, 5))
    if valid:
        x = [r["measured_height_m"] for r in valid]; y = [r["estimated_height_m"] for r in valid]
        ax.scatter(x, y); lo=min(x+y); hi=max(x+y); ax.plot([lo,hi],[lo,hi],"k--",linewidth=1)
    ax.set(xlabel="Measured box height (m)", ylabel="Estimated box height (m)", title="Height: estimated vs measured"); ax.grid(True,alpha=.3)
    fig.tight_layout(); fig.savefig(out / "height_estimated_vs_measured.png", dpi=150); plt.close(fig)
    valid = [r for r in rows if r["distance_error_m"] is not None]
    fig, ax = plt.subplots(figsize=(6, 5))
    if valid: ax.scatter([r["measured_distance_m"] for r in valid], [r["distance_error_m"] for r in valid])
    ax.axhline(0,color="k",linewidth=1); ax.set(xlabel="Measured box front distance (m)", ylabel="Distance error, estimate − measured (m)", title="Distance error vs measured distance"); ax.grid(True,alpha=.3)
    fig.tight_layout(); fig.savefig(out / "distance_error_vs_distance.png", dpi=150); plt.close(fig)


def _fmt(v): return "n/a" if v is None else f"{v:.3f}"
def _pair(a,b): return f"{a:.3f} / {_fmt(b)}"


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("run_sheet"); p.add_argument("--out",default=".")
    p.add_argument("--stride",type=int,default=1); p.add_argument("--depth-topic"); p.add_argument("--info-topic")
    a=p.parse_args(argv)
    try: rows=evaluate_runs(a.run_sheet,a.out,stride=a.stride,depth_topic=a.depth_topic,info_topic=a.info_topic)
    except (ValueError,FileNotFoundError) as exc: p.error(str(exc))
    print(json.dumps({"run_count":len(rows),"out":str(Path(a.out))},indent=2))

if __name__ == "__main__": main()
