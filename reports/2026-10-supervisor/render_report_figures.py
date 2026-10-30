#!/usr/bin/env python3
"""Render report figures from saved measurements without rerunning perception."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vi(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".rstrip("0").rstrip(".").replace(".", ",")


def distance_figure(evaluation: Path, output: Path) -> list[dict]:
    data = json.loads(evaluation.read_text())
    rows = [r for r in data["runs"] if r["run_type"] == "box"
            and r.get("distance_error_m") is not None]
    labels = []
    for row in rows:
        rid = row["run_id"]
        kind = "Hộp" if rid in {"B-H26", "B-H13"} else "Sách"
        height = vi(row["measured_height_m"] * 100)
        distance = vi(row["measured_distance_m"], 3)
        extra = " (lặp)" if rid.endswith("-rep") else ""
        if rid == "B-H05-D1p3":
            extra = " + chân đèn"
        labels.append(f"{kind} {height} cm{extra} / {distance} m")
    errors = np.array([r["distance_error_m"] * 100 for r in rows])
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(9, 7), dpi=170)
    fig.subplots_adjust(left=0.43, right=0.95, bottom=0.19, top=0.83)
    fig.suptitle("Sai số khoảng cách theo từng lượt thử", y=0.95, fontsize=16)
    ax.set_title("Vật thử (chiều cao) / khoảng cách đo bằng thước", loc="left",
                 fontsize=11, pad=18)
    ax.axvline(0, color="#404040", linewidth=1.1)
    for i, (row, error) in enumerate(zip(rows, errors)):
        failure = row["run_id"] == "B-H05-D1p3"
        color = "#A43E36" if failure else "#293D50"
        ax.hlines(i, min(0, error), max(0, error), color=color, alpha=0.5, linewidth=1.8)
        ax.scatter(error, i, marker="x" if failure else "o", color=color,
                   s=85 if failure else 45, linewidths=2 if failure else 0, zorder=3)
        text = f"{error:+.1f}".replace(".", ",").replace("-", "−")
        ax.annotate(text, (error, i), xytext=(9 if error >= 0 else -9, 0),
                    textcoords="offset points", va="center",
                    ha="left" if error >= 0 else "right", fontsize=12, color=color)
    ax.set_yticks(y, labels, fontsize=12)
    ax.tick_params(axis="y", length=0, pad=12)
    ax.invert_yaxis()
    ax.set_xlim(-2.3, 2.8)
    ax.set_xticks([-2, -1, 0, 1, 2])
    ax.set_xlabel("Sai số = ước lượng − thước (cm)", labelpad=10, fontsize=12)
    ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    ax.set_axisbelow(True)
    for edge in ["top", "left", "right"]:
        ax.spines[edge].set_visible(False)
    fig.text(0.43, 0.075, "Âm: ước lượng gần hơn     |     Dương: ước lượng xa hơn", fontsize=10)
    fig.text(0.43, 0.025, "×  Lượt gộp sách với chân đèn; không phải vật thể riêng", fontsize=10,
             color="#A43E36")
    fig.savefig(output, facecolor="white")
    plt.close(fig)
    return [{"run_id": r["run_id"], "measured_distance_m": r["measured_distance_m"],
             "estimated_distance_m": r["estimated_distance_m"],
             "distance_error_m": r["distance_error_m"], "plotted_error_cm": float(e),
             "label": label} for r, e, label in zip(rows, errors, labels)]


def dense_figure(ply: Path, output: Path) -> int:
    with ply.open() as stream:
        if stream.readline().strip() != "ply":
            raise ValueError("Expected a PLY file")
        if stream.readline().strip() != "format ascii 1.0":
            raise ValueError("Expected the archived ASCII PLY")
        count = None
        while True:
            line = stream.readline()
            if not line:
                raise ValueError("Missing PLY end_header")
            if line.startswith("element vertex "):
                count = int(line.split()[-1])
            if line.strip() == "end_header":
                break
        cloud = np.loadtxt(stream, dtype=np.float32)
    if count != len(cloud) or cloud.shape[1] != 4:
        raise ValueError("PLY dimensions do not match its header")
    fig, ax = plt.subplots(figsize=(9, 7), dpi=160)
    sc = ax.scatter(cloud[:, 0], cloud[:, 1], c=cloud[:, 2], s=0.25,
                    cmap="viridis", linewidths=0, rasterized=True)
    fig.colorbar(sc, ax=ax, label="map z (m)")
    ax.set_xlabel("map x (forward, m)")
    ax.set_ylabel("map y (left, m)")
    ax.set_title("D435i stereo dense map, top-down")
    ax.axis("equal")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return len(cloud)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--dense-ply", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "figures")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = {"evaluation_sha256": digest(args.evaluation), "dense_ply_sha256": digest(args.dense_ply)}
    rows = distance_figure(args.evaluation, args.out / "distance-error-vs-distance.png")
    count = dense_figure(args.dense_ply, args.out / "dense-map-topdown.png")
    if original != {"evaluation_sha256": digest(args.evaluation), "dense_ply_sha256": digest(args.dense_ply)}:
        raise RuntimeError("An input changed during rendering")
    receipt = {**original, "distance_rows": rows, "dense_point_count": count,
               "distance_unit": "cm", "dense_title": "D435i stereo dense map, top-down",
               "scope": "Visualization of saved data; no new measurement or perception execution"}
    (args.out / "render-receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(f"Rendered {len(rows)} saved distance trials and {count} archived dense points; inputs unchanged.")


if __name__ == "__main__":
    main()
