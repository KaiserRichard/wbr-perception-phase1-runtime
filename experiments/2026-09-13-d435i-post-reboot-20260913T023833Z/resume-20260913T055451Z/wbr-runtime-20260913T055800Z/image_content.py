#!/usr/bin/env python3
"""Validate saved IR1 PGM samples and metadata without a camera or image SDK."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def read_pgm(path):
    data = Path(path).read_bytes()
    position = 0
    tokens = []
    for _ in range(4):
        while position < len(data):
            if data[position:position + 1].isspace():
                position += 1
            elif data[position:position + 1] == b"#":
                end = data.find(b"\n", position)
                if end < 0:
                    raise ValueError("Unterminated PGM comment")
                position = end + 1
            else:
                break
        start = position
        while position < len(data) and not data[position:position + 1].isspace():
            position += 1
        tokens.append(data[start:position])
    if tokens != [b"P5", b"640", b"480", b"255"]:
        raise ValueError(f"Expected binary 640x480 grayscale PGM, got {tokens!r}")
    if position >= len(data) or not data[position:position + 1].isspace():
        raise ValueError("Missing PGM payload separator")
    # Only consume the required separator, never pixel bytes that equal whitespace.
    position += 2 if data[position:position + 2] == b"\r\n" else 1
    pixels = data[position:]
    if len(pixels) != 640 * 480:
        raise ValueError(f"Expected 307200 pixel bytes, got {len(pixels)}")
    return pixels


def analyze(directory):
    directory = Path(directory)
    with (directory / "frames.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 150:
        raise ValueError("Fewer than 150 image-content metadata samples")
    previous_stamp = previous_frame = None
    gaps = []
    images = []
    domains = set()
    filenames = set()
    for row in rows:
        stamp = float(row["stamp_ms"])
        frame = int(row["frame_number"])
        stride = int(row["stride"])
        if (int(row["width"]) != 640 or int(row["height"]) != 480 or stride < 640
                or int(row["bytes"]) != stride * 480 or not math.isfinite(stamp)):
            raise ValueError("Malformed image metadata")
        if previous_stamp is not None:
            if stamp <= previous_stamp or frame != previous_frame + 1:
                raise ValueError("Image timestamps/frame numbers do not increase continuously")
            gaps.append((stamp - previous_stamp) / 1000)
        previous_stamp, previous_frame = stamp, frame
        domains.add(row["domain"])
        name = row["saved_file"]
        if name:
            if Path(name).name != name or not name.endswith(".pgm") or name in filenames:
                raise ValueError("Unsafe or duplicated saved image filename")
            filenames.add(name)
            pixels = read_pgm(directory / name)
            mean = sum(pixels) / len(pixels)
            variance = sum((value - mean) ** 2 for value in pixels) / len(pixels)
            images.append({"file": name, "width": 640, "height": 480, "format": "Y8/mono8",
                           "pixel_bytes": len(pixels), "minimum": min(pixels), "maximum": max(pixels),
                           "mean": mean, "stdev": math.sqrt(variance),
                           "sha256": hashlib.sha256(pixels).hexdigest(),
                           "statistically_nontrivial": variance > 1.0 and max(pixels) - min(pixels) > 2})
    if len(images) != 3 or len(domains) != 1 or not next(iter(domains), ""):
        raise ValueError("Require exactly three saved samples and one known timestamp domain")
    passed = (all(image["statistically_nontrivial"] for image in images)
              and len({image["sha256"] for image in images}) == 3 and max(gaps) <= .20)
    return {"source": str(directory), "frame_count": len(rows), "images": images,
            "timestamp_domains": sorted(domains), "max_stamp_gap_seconds": max(gaps),
            "nonpositive_stamp_steps": 0, "all_distinct_images": len({image["sha256"] for image in images}) == 3,
            "automatic_checks_pass": passed, "verdict": "REVIEW_REQUIRED" if passed else "FAIL",
            "visual_review_required": "Open all three saved PGMs; verify coherent grayscale scene, no garbled rows/blocks and expected response. Record reviewer, UTC and observations separately.",
            "scene_motion_tested": False, "N2": "NOT DECIDED: statistical variation alone does not establish responsive non-garbled imagery"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = analyze(args.directory)
    except (ValueError, OSError, KeyError) as error:
        result = {"automatic_checks_pass": False, "verdict": "FAIL", "failures": [str(error)]}
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    return 0 if result["automatic_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
