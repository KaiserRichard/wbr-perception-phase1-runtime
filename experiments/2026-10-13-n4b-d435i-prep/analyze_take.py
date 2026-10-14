#!/usr/bin/env python3
"""Summarize a d435i_record timestamps.csv: per-stream counts, rates, gaps, ordering. Diagnostic only (OPEN)."""
import csv
import json
import sys
from collections import defaultdict

LIMITS = {"Infrared 1": 30, "Infrared 2": 30, "Gyro": 200, "Accel": 100}


def main(path):
    rows = defaultdict(list)
    domains = defaultdict(set)
    with open(path) as f:
        for r in csv.DictReader(f):
            key = r["stream"] if r["stream"] not in ("Infrared",) else f"Infrared {r['index']}"
            rows[key].append((float(r["sdk_ms"]), int(r["frame_number"]), int(r["host_steady_ns"])))
            domains[key].add(r["domain"])
    out = {}
    for k, v in sorted(rows.items()):
        t = [x[0] for x in v]
        n = [x[1] for x in v]
        dt = [b - a for a, b in zip(t, t[1:])]
        span = (t[-1] - t[0]) / 1000 if len(t) > 1 else 0
        nominal = LIMITS.get(k)
        out[k] = {
            "count": len(v),
            "span_s": round(span, 3),
            "rate_hz": round((len(v) - 1) / span, 3) if span else None,
            "nominal_hz": nominal,
            "max_gap_ms": round(max(dt), 3) if dt else None,
            "nonpositive_steps": sum(1 for d in dt if d <= 0),
            "frame_number_skips": sum(1 for a, b in zip(n, n[1:]) if b - a > 1) if k.startswith("Infrared") else None,
            "domains": sorted(domains[k]),
            "host_minus_sdk_spread_ms": round(
                (max(x[2] / 1e6 - x[0] for x in v) - min(x[2] / 1e6 - x[0] for x in v)), 3),
        }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
