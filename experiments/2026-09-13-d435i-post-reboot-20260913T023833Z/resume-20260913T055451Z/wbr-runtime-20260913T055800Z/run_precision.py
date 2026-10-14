#!/usr/bin/env python3
"""Bounded post-N2 physical dataset with existing power/USB/process guards."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

from health_monitor import HealthSampler, failures
from analyze_precision import analyze
from kernel_analysis import classify
from sdk_capture import owners, require_n1, stop_child, validate_camera
from validation_common import evidence_hashes, receipt, sha256, utc, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--camera-available', action='store_true', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--n1-result', type=Path, required=True)
    p.add_argument('--n2-result', type=Path, required=True)
    p.add_argument('--notes', type=Path, required=True)
    p.add_argument('--seconds', type=int, required=True)
    p.add_argument('--image-every', type=int, default=0)
    p.add_argument('--emitter-off', action='store_true')
    args = p.parse_args()
    if not 1 <= args.seconds <= 1800 or args.image_every < 0 or os.geteuid() == 0:
        p.error('Invalid bounds/user')
    n1 = require_n1(args.n1_result)
    n2 = receipt(args.n2_result, 'N2_ACCEPT')
    if n1['camera'] != n2['camera']:
        p.error('N1/N2 topology or identity mismatch')
    owners()
    estimated = args.seconds * (315 * 2200 + (4608000 / args.image_every if args.image_every else 0))
    if estimated > 3 * 1024**3 or shutil.disk_usage(args.output.parent).free < estimated + 8 * 1024**3:
        p.error('Dataset budget exceeds 3 GiB or 8 GiB free-space reserve')
    notes = json.loads(args.notes.read_text())
    args.output.mkdir(exist_ok=False)
    binary = Path(__file__).with_name('precision_capture')
    result = {'stage': 'PHYSICAL_FULL_PRECISION', 'verdict': 'FAIL', 'utc_start': utc(),
              'seconds': args.seconds, 'image_every': args.image_every, 'emitter_off': args.emitter_off,
              'estimated_max_bytes': estimated, 'notes': notes, 'camera': n1['camera'],
              'runtime_bundle': str(binary.parent), 'binary_sha256': sha256(binary),
              'n1_sha256': sha256(args.n1_result), 'n2_sha256': sha256(args.n2_result),
              'boot_id': n1['boot_id'], 'failures': [], 'storage': 'bounded microSD; not external-storage qualification'}
    argv = [str(binary), '--camera-available', str(args.output / 'data'), str(args.seconds),
            str(args.image_every), '1' if args.emitter_off else '0']
    result['argv'] = argv
    write_json(args.output / 'command.json', result)
    children, handles = {}, []
    sampler = HealthSampler(args.output)
    old_signal = signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))
    try:
        for name, command in [('journal', ['journalctl', '-k', '-f', '-n', '0', '--no-pager', '-o', 'short-iso-precise'])]:
            h = (args.output / (name + '.log')).open('x'); handles.append(h)
            children[name] = subprocess.Popen(command, stdout=h, stderr=subprocess.STDOUT, start_new_session=True)
        health = (args.output / 'health.jsonl').open('x'); handles.append(health)
        def monitor():
            if children['journal'].poll() is not None:
                raise RuntimeError('Kernel follower exited')
            validate_camera(n1['camera'])
            sample = sampler.sample(children['collector'].pid if 'collector' in children else None)
            health.write(json.dumps(sample) + '\n'); health.flush()
            if failures(sample):
                raise RuntimeError('; '.join(failures(sample)))
            if sample['storage_free_bytes'] < 8 * 1024**3:
                raise RuntimeError('8 GiB reserve reached')
            for name in ('journal.log', 'collector.log', 'data/sdk.log'):
                path = args.output / name
                if path.exists():
                    if path.stat().st_size > 32 * 1024**2:
                        raise RuntimeError('Log budget exceeded')
                    log_text = path.read_text(errors='replace')
                    if 'out of frame resources' in log_text.lower():
                        raise RuntimeError(name + ': SDK frame resource exhaustion')
                    found = classify(log_text)['faults']
                    if found:
                        raise RuntimeError(name + ': ' + json.dumps(found))
        time.sleep(.3); monitor()
        h = (args.output / 'collector.log').open('x'); handles.append(h)
        children['collector'] = subprocess.Popen(argv, stdout=h, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + args.seconds + 30
        while children['collector'].poll() is None:
            monitor()
            if time.monotonic() > deadline:
                raise RuntimeError('Collector deadline exceeded')
            time.sleep(1)
        monitor()
        result['returncode'] = children['collector'].returncode
        result['collector'] = json.loads((args.output / 'data/collector-result.json').read_text())
        if result['returncode'] or result['collector']['queue_overflow'] or not result['collector']['clean_stop']:
            raise RuntimeError('Collector failed, overflowed, or did not stop cleanly')
        timing = analyze(args.output / 'data/frames.jsonl')
        write_json(args.output / 'timing-analysis.json', timing)
        if not timing['automatic_timing_pass']:
            raise RuntimeError('Full-precision timing/frame continuity failed; inspect timing-analysis.json')
        result['verdict'] = 'CAPTURED_REVIEW_REQUIRED'
    except (Exception, KeyboardInterrupt) as error:
        result['failures'].append(str(error))
    finally:
        for name in ('collector', 'journal'):
            if name in children:
                result[name + '_cleanup'] = stop_child(children[name], grace=10)
        for h in handles: h.close()
        signal.signal(signal.SIGTERM, old_signal)
        result['utc_end'] = utc()
        result['power_after'] = subprocess.check_output(['vcgencmd', 'get_throttled'], text=True).strip()
        result['usb_after'] = subprocess.check_output(['lsusb', '-t'], text=True)
        if result['power_after'] != 'throttled=0x0':
            result['failures'].append('Nonzero final power flags'); result['verdict'] = 'FAIL'
        result['evidence_sha256'] = evidence_hashes(args.output)
        write_json(args.output / 'result.json', result)
    print(json.dumps({k: result[k] for k in ('verdict', 'failures', 'utc_end')}))
    return bool(result['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
