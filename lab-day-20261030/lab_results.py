#!/usr/bin/env python3
"""Read copied lab evidence on the Mac; never modify the evidence tree.

Usage: python lab-day-20261030/lab_results.py EVIDENCE_ROOT
       [--out results.md] [--json results.json]
Requires the perception venv (numpy, matplotlib, rosbags). No ROS installation.
Optional EVIDENCE_ROOT/run_sheet.csv: one row per run, columns run_id (directory
basename or relative path), outcome (PASS/FAIL), reason, tape_distance_m,
return_offset_m, box_height_m, box_width_m, box_depth_m, start_distance_m,
stop_distance_m, camera_height_m, motion_duration_s, notes. Blank measurements
stay unknown; numbers use SI units. Only this sheet supplies physical dimensions.
PASS is an owner observation, not inferred safety/accuracy. EVIDENCE means parsed
artifacts; INCOMPLETE means required evidence is absent; FAIL retains available
metrics. Log counts are message occurrences, not tracking-loss transitions or
final atlas size. Endpoint uses first/last recorded poses in the SLAM world and
may include resets/loop corrections: endpoint, not accuracy. Tracked fraction
uses recorded status messages only, never pose count divided by sensor count.
Bag duration and capture window are reported separately. Kernel counts cover the
whole saved log (root log is shared), with no inferred per-run time attribution.
LIVE delegates to summarize_live.summarize_run on temporary input copies because
that function writes a plot. Generated plots are discarded. Empty data is unknown,
not zero. P1 prefers bag suggestions, otherwise JSON objects in planner.log.
"""
import argparse
from collections import Counter
import csv
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

EXPECTED = ('M1-lab-map', 'L1-3m-line', 'A1-approach', 'P1-path-test')
LEFT = '/camera/camera/infra1/image_rect_raw'
RIGHT = '/camera/camera/infra2/image_rect_raw'
POSE = '/d435_orb/pose'
STATUS = '/d435_orb/status'
SUGGESTION = '/wbr_planner_node/suggestion'


def load(path):
    with path.open() as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f'{path.name}: expected JSON object')
    return value


def text(path):
    return path.read_text(errors='replace') if path.is_file() else ''


def finite(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('nonfinite number')
    return number


def log_metrics(run):
    content = text(run / 'slam.log')
    if not content:
        return {}
    return {
        'track_failure_messages': len(re.findall(r'Fail to track local map!', content)),
        'tracking_loss_messages': len(re.findall(r'(?i)track(?:ing)? lost|lost tracking', content)),
        'reset_messages': len(re.findall(r'(?i)(?:system|active map) reset|reset(?:ting)? (?:active )?map', content)),
        'map_creation_messages': len(re.findall(r'Creation of new map with id:', content)),
        'relocalization_messages': content.count('Relocalized!!'),
    }


def read_bags(run):
    """Stream selected messages; ignore large images except stereo header pairing."""
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore
    store = get_typestore(Stores.ROS2_JAZZY)
    counts, headers = Counter(), {LEFT: Counter(), RIGHT: Counter()}
    poses, statuses, suggestions = [], [], []
    duration = 0.0
    bags = sorted(p.parent for p in run.rglob('metadata.yaml'))
    for bag in bags:
        with Reader(bag) as reader:
            duration += reader.duration / 1e9
            for connection in reader.connections:
                counts[connection.topic] += connection.msgcount
            wanted = {POSE, STATUS, SUGGESTION}
            if run.name.startswith(('M1-', 'L1-')) and not (run / 'stereo-quality.json').exists():
                wanted.update((LEFT, RIGHT))
            connections = [c for c in reader.connections if c.topic in wanted]
            for connection, stamp, raw in reader.messages(connections=connections):
                msg = store.deserialize_cdr(raw, connection.msgtype)
                if connection.topic in headers:
                    h = msg.header.stamp
                    headers[connection.topic][h.sec * 10**9 + h.nanosec] += 1
                elif connection.topic == POSE:
                    p = msg.pose.position
                    poses.append((stamp, msg.header.frame_id, tuple(finite(v) for v in (p.x, p.y, p.z))))
                elif connection.topic == STATUS:
                    statuses.append(json.loads(msg.data))
                else:
                    suggestions.append(json.loads(msg.data))
    result = {'topic_counts': dict(counts), 'pose_count': counts.get(POSE),
              'bag_duration_s': duration if bags else None}
    if statuses:
        result['orb_status_histogram'] = dict(Counter(str(s.get('tracking_state', 'UNKNOWN')) for s in statuses))
        valid = [s for s in statuses if isinstance(s.get('pose_published'), bool)]
        result['tracked_fraction'] = sum(s['pose_published'] for s in valid) / len(valid) if valid else None
    if len(poses) >= 2:
        poses.sort()
        if len({p[1] for p in poses}) == 1:
            result['endpoint_m'] = math.dist(poses[0][2], poses[-1][2])
    if headers[LEFT] and headers[RIGHT]:
        common = headers[LEFT] & headers[RIGHT]
        result['paired_frames'] = sum(common.values())
        span = (max(common) - min(common)) / 1e9 if common else 0
        result['paired_header_rate_hz'] = (sum(common.values()) - 1) / span if span > 0 else None
    return result, suggestions


def bag_info(run):
    result, counts = {}, {}
    for path in sorted(run.rglob('*bag*info*.txt')):
        content = text(path)
        counts.update({topic: int(count) for topic, count in re.findall(r'Topic:\s*(\S+).*?Count:\s*(\d+)', content)})
        match = re.search(r'Duration:\s*([\d.]+)s', content)
        if match:
            result['bag_duration_s'] = float(match[1])
    if counts:
        result['topic_counts'] = counts
        result['pose_count'] = counts.get(POSE)
    return result


def planner_metrics(suggestions):
    actions = Counter(s['action'] for s in suggestions if isinstance(s, dict) and s.get('action'))
    times = [finite(s['timings_ms']['total']) for s in suggestions
             if isinstance(s, dict) and s.get('timings_ms', {}).get('total') is not None]
    result = {'suggestion_counts': dict(actions),
              'no_pose_fraction': actions['NO_POSE'] / sum(actions.values()) if actions else None}
    if times:
        result['planner_core_mean_ms'] = sum(times) / len(times)
        result['planner_core_max_ms'] = max(times)
    return result


def live_metrics(run):
    with tempfile.TemporaryDirectory(prefix='lab-results-live-') as scratch:
        os.environ.setdefault('MPLCONFIGDIR', scratch)
        os.environ.setdefault('XDG_CACHE_HOME', scratch)
        from tools.link_bench.pi.summarize_live import summarize_run
        copied = Path(scratch) / run.name
        copied.mkdir()
        for name in ('summary.json', 'packets.csv'):
            shutil.copyfile(run / name, copied / name)
        result = summarize_run(copied)
    result.pop('plot', None)
    return result


def kernel_metrics(run, root):
    paths = sorted(set(run.glob('*kernel*.log')) | set(run.glob('*dmesg*.log')))
    if not paths and (root / 'kernel-live.log').is_file():
        paths = [root / 'kernel-live.log']
    if not paths:
        return {'kernel_errors': None}
    pattern = re.compile(r'(?i)(?:usb.*(?:error|disconnect|reset|fail)|(?:error|fail).*usb|under.voltage|over.current|\b(?:oops|panic)\b)')
    return {'kernel_errors': sum(bool(pattern.search(line)) for p in paths for line in text(p).splitlines()),
            'kernel_scope': ', '.join(str(p.relative_to(root)) for p in paths)}


def summarize(run, root, sheet):
    kind = 'LIVE' if run.name.startswith('LIVE-chain-') or ((run / 'summary.json').exists() and (run / 'packets.csv').exists()) else run.name[:2]
    row = {'run': str(run.relative_to(root)) if run != root else run.name,
           'kind': kind, 'metrics': {}, 'physical': sheet, 'issues': []}
    metrics, issues = row['metrics'], row['issues']
    failed = []
    fatal = re.compile(r'Traceback \(most recent call last\)|process has died|Timed out waiting for|Missing setup file:|No module named|terminate called after throwing')
    for name in ('session.log', 'camera.log', 'slam.log', 'planner.log', 'record.log', 'bag.log', 'link.log'):
        for line in text(run / name).splitlines():
            if fatal.search(line):
                failed.append(f'{name}: {line.strip()}')
                break

    def attempt(label, function):
        try:
            return function()
        except Exception as error:
            failed.append(f'{label}: {type(error).__name__}: {error}')
            return None

    if kind == 'LIVE':
        value = attempt('LIVE summary', lambda: live_metrics(run))
        if value:
            metrics.update(value)
            if not value.get('frames'):
                failed.append('no packet frames')
        source = attempt('summary.json', lambda: load(run / 'summary.json'))
        if source:
            metrics.update({k: source.get(k) for k in ('sent', 'echoed', 'loss', 'dropped_frames')})
            if not source.get('echoed'):
                failed.append('no echoed packets')
            if source.get('errors'):
                failed.append(str(source['errors']))
        if sheet.get('outcome', '').upper() != 'PASS':
            issues.append('LED/physical outcome requires run sheet; UART/MCU authenticity not inferred')
    else:
        metrics.update(log_metrics(run))
        metrics.update(bag_info(run))
        suggestions = []
        value = attempt('bag read', lambda: read_bags(run))
        if value:
            data, suggestions = value
            metrics.update({k: v for k, v in data.items() if v is not None and v != {}})
        if kind in ('M1', 'L1'):
            capture = attempt('capture_summary.json', lambda: load(run / 'capture_summary.json'))
            if capture:
                metrics['capture_window_s'] = capture.get('measured_recording_window_seconds')
                failed.extend(str(e) for e in capture.get('errors', []))
                for name, code in capture.get('process_returncodes', {}).items():
                    if code != 0:
                        failed.append(f'{name} returncode={code}')
                if capture.get('bag_info_exit', 0) != 0:
                    failed.append('bag info command failed')
            if not (run / 'slam.log').is_file():
                issues.append('missing slam.log')
            if (run / 'stereo-quality.json').exists():
                quality = attempt('stereo quality', lambda: load(run / 'stereo-quality.json'))
                if quality:
                    streams = quality['streams']
                    left = streams['left']
                    if quality.get('identical_image_headers') is True:
                        metrics['paired_frames'] = left['image_count']
                        metrics['paired_header_rate_hz'] = left.get('observed_header_rate_hz')
            for key in ('paired_frames', 'tracked_fraction', 'endpoint_m'):
                if metrics.get(key) is None:
                    issues.append(f'{key} unavailable')
        if kind == 'A1':
            if not metrics.get('pose_count'):
                issues.append('no recorded pose evidence')
            if not metrics.get('orb_status_histogram'):
                issues.append('ORB status unavailable')
        if kind == 'P1':
            if not suggestions:
                decoder = json.JSONDecoder()
                for line in text(run / 'planner.log').splitlines():
                    start = line.find('{')
                    if start >= 0:
                        value = attempt('planner JSON', lambda line=line, start=start: decoder.raw_decode(line[start:])[0])
                        if value:
                            suggestions.append(value)
            value = attempt('planner metrics', lambda: planner_metrics(suggestions))
            if value:
                metrics.update(value)
            if not metrics.get('suggestion_counts'):
                issues.append('no retained suggestion messages (topic count alone is insufficient)')
        if not metrics.get('topic_counts'):
            issues.append('missing bag/topic counts')
    metrics.update(kernel_metrics(run, root))
    if sheet.get('outcome', '').upper() == 'FAIL':
        failed.append('run sheet: ' + (sheet.get('reason') or 'owner marked FAIL'))
    row['status'] = 'FAIL: ' + '; '.join(failed) if failed else ('INCOMPLETE' if issues else 'EVIDENCE')
    row['issues'] = failed + issues
    return row


def collect(root):
    sheet, sheet_error = {}, None
    if (root / 'run_sheet.csv').exists():
        try:
            with (root / 'run_sheet.csv').open(newline='') as stream:
                for item in csv.DictReader(stream):
                    sheet[item['run_id']] = {k: v for k, v in item.items() if k != 'run_id' and v}
        except Exception as error:
            sheet_error = f'run_sheet.csv: {error}'
    dirs = {p for p in root.rglob('*') if p.is_dir() and (p.name in EXPECTED or p.name.startswith('LIVE-chain-') or ((p / 'summary.json').is_file() and (p / 'packets.csv').is_file()))}
    if root.name in EXPECTED or root.name.startswith('LIVE-chain-') or ((root / 'summary.json').is_file() and (root / 'packets.csv').is_file()):
        dirs.add(root)
    rows = []
    for run in sorted(dirs):
        key = str(run.relative_to(root))
        try:
            rows.append(summarize(run, root, sheet.get(key, sheet.get(run.name, {}))))
        except Exception as error:
            rows.append({'run': key if key != '.' else run.name, 'kind': run.name[:2],
                         'status': f'FAIL: {type(error).__name__}: {error}',
                         'metrics': {}, 'physical': sheet.get(key, sheet.get(run.name, {})),
                         'issues': ['unreadable or malformed run evidence']})
    missing = [name for name in EXPECTED if not any(p.name == name for p in dirs)]
    if not any(row['kind'] == 'LIVE' for row in rows):
        missing.append('LIVE-chain-*')
    rows.extend({'run': name, 'kind': name[:2], 'status': 'MISSING', 'metrics': {}, 'physical': {}, 'issues': ['run directory not found']} for name in missing)
    if sheet_error:
        for row in rows:
            row['issues'].append(sheet_error)
            if row['status'] not in ('MISSING',) and not row['status'].startswith('FAIL'):
                row['status'] = 'INCOMPLETE'
    return rows


def fmt(value):
    if value is None:
        return 'unknown'
    if isinstance(value, float):
        return f'{value:.3f}'
    if isinstance(value, dict):
        return ', '.join(f'{k}:{fmt(v)}' for k, v in sorted(value.items())) or 'unknown'
    return str(value)


def render(rows):
    lines = ['| Run | Evidence status | Key numbers | Physical run sheet / limitations |', '|---|---|---|---|']
    labels = {'endpoint_m': 'endpoint, not accuracy (m)', 'track_failure_messages': 'track failure messages (not loss transitions)', 'map_creation_messages': 'maps created (not final atlas size)'}
    for row in rows:
        metrics = '; '.join(f'{labels.get(k, k)}={fmt(v)}' for k, v in row['metrics'].items() if k not in ('run', 'advisory_histogram_text'))
        notes = '; '.join(filter(None, (fmt(row['physical']) if row['physical'] else '', *row['issues'])))
        cells = (row['run'], row['status'], metrics or '—', notes or '—')
        lines.append('| ' + ' | '.join(c.replace('|', '\\|').replace('\n', ' ') for c in cells) + ' |')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence_root', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--json', type=Path)
    args = parser.parse_args(argv)
    root = args.evidence_root.expanduser().resolve()
    # Reports must live outside the source evidence and the archive, even via symlinks.
    for output in (args.out, args.json):
        if output:
            target = output.expanduser().resolve()
            if target.is_relative_to(root) or target.is_relative_to(Path.home() / 'wbr-evidence-archive'):
                parser.error('report output must be outside the evidence root and ~/wbr-evidence-archive')
    rows = collect(root)
    report = render(rows)
    print(report, end='')
    if args.out:
        args.out.expanduser().write_text(report)
    if args.json:
        args.json.expanduser().write_text(json.dumps({'evidence_root': str(root), 'runs': rows}, indent=2, allow_nan=False) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
