#!/usr/bin/env python3
"""Replay lab-day bags under old/new advisory hysteresis and compare live packets.

Example:
  python tools/obstacle_decision/flicker_check.py \
    /Users/quockaiser/wbr-evidence-archive/lab-day-20261025 ./foxglove-out/FLICKER_REPORT.md
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
import statistics
import sys

import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.obstacle_decision.decide import Advisory, DecisionParams, update
from tools.obstacle_decision.detect import Params, process_frame
from tools.obstacle_decision.range_filter import in_range
from tools.obstacle_decision.replay_bag import _intrinsics, decode_depth
from tools.bag_tools.mcap_recovery import messages as bag_messages, readable_mcap

RUNS = ('2-books46', '3-box13', '4-approach', '4-approach-r2', '4-approach-r3')
DEPTH = '/camera/camera/aligned_depth_to_color/image_raw'
INFO = '/camera/camera/color/camera_info'
NAMES = {int(item): item.name for item in Advisory}


def _reader_path(bag_dir: Path) -> Path:
    if (bag_dir / 'metadata.yaml').is_file():
        return bag_dir
    files = sorted(bag_dir.glob('*.mcap'))
    if len(files) == 1:
        return files[0]
    raise ValueError(f'expected metadata.yaml or one MCAP file in {bag_dir}')


def _frames(reader_path: Path):
    """Yield (header stamp, depth msg, intrinsics), buffering before first CameraInfo."""
    ts = get_typestore(Stores.ROS2_JAZZY)
    with Reader(reader_path) as reader:
        topics = {conn.topic: conn for conn in reader.connections}
        if DEPTH not in topics or INFO not in topics:
            raise ValueError(f'{reader_path}: missing aligned depth or color CameraInfo')
        pending = []
        K = None
        connections = [topics[DEPTH], topics[INFO]]
        for conn, _, raw in bag_messages(reader, reader_path, connections):
            msg = ts.deserialize_cdr(raw, conn.msgtype)
            if conn.topic == INFO:
                K = _intrinsics(msg)
                for depth_msg in pending:
                    stamp = _stamp_ns(depth_msg)
                    yield stamp, depth_msg, K
                pending.clear()
            elif K is None:
                pending.append(msg)
            else:
                yield _stamp_ns(msg), msg, K
        if pending:
            raise ValueError(f'{reader_path}: no CameraInfo preceded {len(pending)} depth frames')


def _stamp_ns(msg):
    return int(msg.header.stamp.sec) * 1_000_000_000 + int(msg.header.stamp.nanosec)


def _replay(bag_dir: Path, max_forward: float, range_hysteresis: float):
    params = Params()
    old_params = DecisionParams(height_hysteresis_m=0.0)
    new_params = DecisionParams()
    detector_state = {}
    modes = {
        'old': {'params': old_params, 'range_hysteresis': 0.0, 'range_state': {}, 'decision_state': {}, 'rows': []},
        'new': {'params': new_params, 'range_hysteresis': range_hysteresis, 'range_state': {}, 'decision_state': {}, 'rows': []},
    }
    with readable_mcap(_reader_path(bag_dir)) as (reader_path, recovered_tail_bytes):
        for stamp, msg, K in _frames(reader_path):
            frame, detector_state = process_frame(decode_depth(msg), K, params, detector_state)
            for mode in modes.values():
                limited, mode['range_state'] = in_range(
                    frame, max_forward, mode['range_hysteresis'], mode['range_state'])
                decision, mode['decision_state'] = update(
                    limited, mode['decision_state'], mode['params'])
                mode['rows'].append((stamp, int(decision.advisory)))
    for mode in modes.values():
        mode['rows'].sort(key=lambda row: row[0])
    modes['recovered_tail_bytes'] = recovered_tail_bytes
    return modes


def _live_packets(path: Path):
    rows = []
    with path.open(newline='') as stream:
        for row in csv.DictReader(stream):
            rows.append((int(row['frame_stamp_ns']), int(row['advisory'])))
    return rows


def _metrics(rows):
    if not rows:
        return {'transitions': [], 'seconds': {}, 'duration_s': 0.0}
    stamps = [stamp for stamp, _ in rows]
    positive_dt = [(b - a) / 1e9 for a, b in zip(stamps, stamps[1:]) if b > a]
    tail = statistics.median(positive_dt) if positive_dt else 0.0
    elapsed = [(b - a) / 1e9 if b > a else 0.0 for a, b in zip(stamps, stamps[1:])] + [tail]
    seconds = Counter()
    for (_, code), dt in zip(rows, elapsed):
        seconds[NAMES.get(code, f'UNKNOWN_{code}')] += dt
    start = stamps[0]
    transitions = [
        ((stamp - start) / 1e9, code)
        for (stamp, code), (_, previous) in zip(rows[1:], rows[:-1])
        if code != previous
    ]
    return {'transitions': transitions, 'seconds': dict(seconds), 'duration_s': sum(elapsed)}


def _format_transitions(events):
    return ', '.join(f'{t:.3f}s {NAMES.get(code, code)}' for t, code in events) or 'none'


def _format_times(seconds):
    order = ('NONE', 'JUMP_CANDIDATE', 'STOP_CANDIDATE', 'UNCERTAIN')
    return ', '.join(f'{name} {seconds.get(name, 0.0):.2f}s' for name in order if seconds.get(name, 0.0) > 0.0005) or 'none'


def report(archive: Path, output: Path, *, max_forward=1.3, range_hysteresis=0.10):
    results = []
    for run in RUNS:
        run_dir = archive / run
        modes = _replay(run_dir / 'camera-bag', max_forward, range_hysteresis)
        live_rows = _live_packets(run_dir / 'packets.csv')
        old_rows, new_rows = modes['old']['rows'], modes['new']['rows']
        old_metrics, new_metrics, live_metrics = map(_metrics, (old_rows, new_rows, live_rows))
        old_by_stamp = dict(old_rows)
        matched = [(old_by_stamp[stamp], code) for stamp, code in live_rows if stamp in old_by_stamp]
        agreement = (sum(a == b for a, b in matched) / len(matched)) if matched else 0.0
        results.append((run, modes, live_rows, old_metrics, new_metrics, live_metrics, len(matched), agreement))

    lines = [
        '# Lab day 2026-10-25 advisory flicker report', '',
        f'Range cutoff: {max_forward:.2f} m nearest face; accepted clusters retain the live {range_hysteresis:.2f} m range hysteresis.',
        'Old replay sets both range and height hysteresis to 0; new replay uses the live range hysteresis and `DecisionParams` default height hysteresis (0.01 m).',
        'Durations use bag/header timestamps, assigning each frame state until the next frame and using the median frame period for the final sample. Transition times are relative to the first depth frame or live packet in each sequence.', '',
        '| Run | Bag frames | Old transitions | New transitions | Live packets / transitions | Old vs live at matched frame stamps |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for run, modes, live_rows, old_m, new_m, live_m, matched_n, agreement in results:
        lines.append(
            f'| {run} | {len(modes["old"]["rows"])} | {len(old_m["transitions"])} | '
            f'{len(new_m["transitions"])} | {len(live_rows)} / {len(live_m["transitions"])} | '
            f'{matched_n} matched, {agreement:.1%} agreement |'
        )
    lines.extend(['', '## Advisory time and transition times', ''])
    for run, modes, live_rows, old_m, new_m, live_m, matched_n, agreement in results:
        lines.extend([
            f'### {run}', '',
        ])
        if modes['recovered_tail_bytes']:
            lines.append(f'- Source recovery: omitted {modes["recovered_tail_bytes"]:,} incomplete trailing MCAP bytes from a temporary copy; the archived file was unchanged.')
        lines.extend([
            f'- Old time: {_format_times(old_m["seconds"])} ({old_m["duration_s"]:.2f}s total).',
            f'- Old transitions ({len(old_m["transitions"])}): {_format_transitions(old_m["transitions"])}.',
            f'- New time: {_format_times(new_m["seconds"])} ({new_m["duration_s"]:.2f}s total).',
            f'- New transitions ({len(new_m["transitions"])}): {_format_transitions(new_m["transitions"])}.',
            f'- Live time: {_format_times(live_m["seconds"])} ({live_m["duration_s"]:.2f}s observed across packet intervals).',
            f'- Live transitions ({len(live_m["transitions"])}): {_format_transitions(live_m["transitions"])}.',
        ])
        if matched_n < len(live_rows):
            lines.append(f'- Timestamp matches: {matched_n}/{len(live_rows)} live packets; unmatched packets are excluded from agreement.')
        lines.append('')
    fewer = sum(len(new['transitions']) < len(old['transitions']) for _, modes, *_ in results
                for old, new in [( _metrics(modes['old']['rows']), _metrics(modes['new']['rows']) )])
    same = sum(_metrics(modes['old']['rows'])['transitions'] == _metrics(modes['new']['rows'])['transitions']
               for _, modes, *_ in results)
    mean_agreement = statistics.mean(row[-1] for row in results)
    conclusion = [
        f'Across five runs, new defaults produced fewer transitions in {fewer}/5 runs; transition sequences were identical in {same}/5.',
        f'Old replay matched the live advisory on {mean_agreement:.1%} of exact shared frame stamps on average; live packet loss/drop means this is a sampled comparison.',
        'These results describe replayed detector output for these takes; they do not establish general flicker performance or hardware timing.',
    ]
    lines.extend(['## Conclusion', '', *conclusion, ''])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--max-forward', type=float, default=1.3)
    parser.add_argument('--range-hysteresis', type=float, default=0.10)
    args = parser.parse_args(argv)
    if args.max_forward < 0 or args.range_hysteresis < 0:
        parser.error('--max-forward and --range-hysteresis must be non-negative')
    results = report(args.archive, args.output, max_forward=args.max_forward,
                     range_hysteresis=args.range_hysteresis)
    print(f'wrote {args.output} ({len(results)} runs)')


if __name__ == '__main__':
    main()
