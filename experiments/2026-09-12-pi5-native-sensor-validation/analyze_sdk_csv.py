#!/usr/bin/env python3
"""Summarize declared full windows in rs-data-collect 2.58.4 CSV output.

CSV retains frame timestamps, tool-relative arrivals and quantized IMU vectors,
but does not serialize timestamp domain or image pixels. A timing PASS here
does not by itself pass N2: image, SDK logs, kernel and health checks are separate.
"""
import argparse
import csv
import json
import math
import statistics
from pathlib import Path

EXPECTED = {'Infrared': (1, 14.25, 15.75, 0.20),
            'Gyro': (0, 190.0, 210.0, 0.05),
            'Accel': (0, 95.0, 105.0, 0.05)}


def read_samples(path):
    if path.stat().st_size == 0:
        raise ValueError('CSV was not finalized; sample rates are unavailable, not zero')
    data = {name: [] for name in EXPECTED}
    in_samples = False
    with path.open(newline='') as handle:
        for row in csv.reader(handle):
            if row and row[0] == 'Stream Type' and len(row) > 2 and row[2] == 'F#':
                in_samples = True
                continue
            if not in_samples or not row or row[0] not in data:
                continue
            name = row[0]
            if int(row[1]) != EXPECTED[name][0]:
                raise ValueError(f'Unexpected {name} stream index: {row[1]}')
            sample = {'frame': int(row[2]), 'stamp': float(row[3]) / 1000,
                      'arrival': float(row[4]) / 1000,
                      'vector': [float(v) for v in row[5:8]]}
            data[name].append(sample)
    return data


def summarize(samples, start, duration, limits):
    rows = [s for s in samples if start <= s['arrival'] < start + duration]
    _, low, high, gap = limits
    result = {'count': len(rows), 'whole_window_hz': len(rows) / duration}
    if len(rows) < 2:
        return result | {'timing_pass': False, 'reason': 'Fewer than two samples'}
    arrivals = [s['arrival'] for s in rows]
    stamps = [s['stamp'] for s in rows]
    stamp_steps = [b - a for a, b in zip(stamps, stamps[1:])]
    arrival_steps = [b - a for a, b in zip(arrivals, arrivals[1:])]
    frame_steps = [b['frame'] - a['frame'] for a, b in zip(rows, rows[1:])]
    edges = [arrivals[0] - start, start + duration - arrivals[-1]]
    finite = all(math.isfinite(v) for s in rows
                 for v in [s['stamp'], s['arrival'], *s['vector']])
    result.update(first_arrival_offset_seconds=edges[0], last_arrival_silence_seconds=edges[1],
                  max_arrival_gap_seconds=max(arrival_steps),
                  max_arrival_gap_with_boundaries_seconds=max(*edges, *arrival_steps),
                  max_stamp_gap_seconds=max(stamp_steps),
                  nonpositive_stamp_steps=sum(v <= 0 for v in stamp_steps),
                  nonpositive_arrival_steps=sum(v <= 0 for v in arrival_steps),
                  nonpositive_frame_steps=sum(v <= 0 for v in frame_steps),
                  missing_frame_numbers=sum(max(0, v - 1) for v in frame_steps),
                  finite_values=finite)
    if rows[0]['vector']:
        result['mean_xyz'] = [statistics.mean(axis) for axis in zip(*(s['vector'] for s in rows))]
        result['mean_vector_norm'] = statistics.mean(math.sqrt(sum(v*v for v in s['vector'])) for s in rows)
    result['timing_pass'] = (finite and low <= result['whole_window_hz'] <= high
                             and max(*edges, *arrival_steps) <= gap
                             and max(stamp_steps) <= gap
                             and result['nonpositive_stamp_steps'] == 0
                             and result['nonpositive_arrival_steps'] == 0
                             and result['nonpositive_frame_steps'] == 0)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--start', type=float, required=True)
    parser.add_argument('--duration', type=float, required=True)
    parser.add_argument('--windows', type=int, default=1)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.start < 0 or args.duration <= 0 or args.windows < 1:
        parser.error('Invalid measurement window')
    data = read_samples(args.input)
    out = {'source': str(args.input), 'method': 'tool-relative whole windows, half-open [start,end)',
           'timestamp_domain': 'Not serialized by rs-data-collect; no synchronization claim',
           'imu_precision': 'Vendor CSV rounds vectors to 0.001; retain original CSV',
           'windows': []}
    out['all_received_samples'] = {}
    for name, rows in data.items():
        steps = [b['stamp'] - a['stamp'] for a, b in zip(rows, rows[1:])]
        frame_steps = [b['frame'] - a['frame'] for a, b in zip(rows, rows[1:])]
        out['all_received_samples'][name] = {
            'count': len(rows),
            'first_arrival_seconds': rows[0]['arrival'] if rows else None,
            'last_arrival_seconds': rows[-1]['arrival'] if rows else None,
            'first_stamp_seconds': rows[0]['stamp'] if rows else None,
            'last_stamp_seconds': rows[-1]['stamp'] if rows else None,
            'nonpositive_stamp_steps': sum(v <= 0 for v in steps),
            'nonpositive_frame_steps': sum(v <= 0 for v in frame_steps),
            'missing_frame_numbers': sum(max(0, v-1) for v in frame_steps),
            'max_stamp_gap_seconds': max(steps) if steps else None,
        }
    for i in range(args.windows):
        start = args.start + i * args.duration
        out['windows'].append({'start_seconds': start, 'duration_seconds': args.duration,
                               'streams': {name: summarize(data[name], start, args.duration, limits)
                                           for name, limits in EXPECTED.items()}})
    out['all_timing_windows_pass'] = all(s['timing_pass'] for w in out['windows'] for s in w['streams'].values())
    out['N2'] = 'NOT DECIDED: requires image, device/kernel logs, calibration context and health evidence'
    args.output.write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    print(json.dumps(out, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
