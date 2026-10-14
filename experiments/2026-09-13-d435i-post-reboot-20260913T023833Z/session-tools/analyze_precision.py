#!/usr/bin/env python3
"""Offline analysis of full-precision frame evidence; never infers synchronization."""
import argparse
from collections import defaultdict, Counter
import json
import math
from pathlib import Path


def analyze(path):
    streams = defaultdict(list)
    for line in Path(path).read_text().splitlines():
        row = json.loads(line)
        if not math.isfinite(row['sdk_timestamp_ms']):
            raise ValueError('Nonfinite SDK timestamp')
        streams[row['stream']].append(row)
    result = {'streams': {}, 'limitations': ['Matching timestamp domains do not prove physical synchronization.',
        'Host UTC and steady clocks are sampled successively at callback entry.',
        'SDK float IMU values are preserved; factory calibration fallback still applies.']}
    required = {'Infrared 1': (14.25, 15.75, .2), 'Gyro': (190, 210, .05), 'Accel': (95, 105, .05)}
    for name, rows in streams.items():
        stamps = [r['sdk_timestamp_ms'] / 1000 for r in rows]
        arrivals = [r['host_steady_ns'] / 1e9 for r in rows]
        gaps = [b-a for a,b in zip(stamps, stamps[1:])]
        arrival_gaps = [b-a for a,b in zip(arrivals, arrivals[1:])]
        numbers = [r['frame_number'] for r in rows]
        number_gaps = [b-a for a,b in zip(numbers,numbers[1:])]
        hz = (len(rows)-1)/(arrivals[-1]-arrivals[0]) if len(rows) > 1 else 0
        bands = required.get(name, (float('inf'), 0, 0))
        summary = {'count': len(rows), 'callback_span_s': arrivals[-1]-arrivals[0], 'arrival_rate_hz': hz,
            'domains': dict(Counter(r['timestamp_domain'] for r in rows)), 'first_sdk_s': stamps[0], 'last_sdk_s': stamps[-1],
            'first_host_steady_ns': rows[0]['host_steady_ns'], 'last_host_steady_ns': rows[-1]['host_steady_ns'],
            'repeated_timestamps': sum(g == 0 for g in gaps), 'backward_timestamps': sum(g < 0 for g in gaps),
            'max_timestamp_gap_s': max(gaps, default=0), 'max_arrival_gap_s': max(arrival_gaps, default=0),
            'nonpositive_arrival_steps': sum(g <= 0 for g in arrival_gaps),
            'missing_frame_numbers': sum(max(0,g-1) for g in number_gaps),
            'nonpositive_frame_steps': sum(g <= 0 for g in number_gaps),
            'metadata_keys': sorted({k for r in rows for k in r['metadata']}),
            'image_count': sum('image' in r for r in rows),
            'automatic_timing_pass': bands[0] <= hz <= bands[1] and bool(gaps) and min(gaps) > 0
                and max(gaps) <= bands[2] and min(arrival_gaps) > 0 and max(arrival_gaps) <= bands[2]
                and all(g == 1 for g in number_gaps)}
        if 'xyz' in rows[0]:
            vectors = [r['xyz'] for r in rows]
            if not all(math.isfinite(x) for v in vectors for x in v): raise ValueError('Nonfinite IMU')
            summary['xyz_mean'] = [sum(v[i] for v in vectors)/len(vectors) for i in range(3)]
            summary['xyz_min'] = [min(v[i] for v in vectors) for i in range(3)]
            summary['xyz_max'] = [max(v[i] for v in vectors) for i in range(3)]
            summary['xyz_stddev'] = [(sum((v[i]-summary['xyz_mean'][i])**2 for v in vectors)/len(vectors))**.5 for i in range(3)]
        result['streams'][name] = summary
    values = list(result['streams'].values())
    result['cross_stream_host_overlap_s'] = max(0,(min(r['last_host_steady_ns'] for r in values)-max(r['first_host_steady_ns'] for r in values))/1e9) if values else 0
    result['automatic_timing_pass'] = set(streams) == set(required) and all(s['automatic_timing_pass'] for s in values)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    with a.output.open('x') as handle: json.dump(analyze(a.input), handle, indent=2, allow_nan=False); handle.write('\n')
