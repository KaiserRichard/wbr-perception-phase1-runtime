#!/usr/bin/env python3
"""Own one physical N3 publisher and bounded recorder; reuse existing validators.

The operator inspects the actual graph before creating record-request.json.
Only child process groups created here are stopped. No camera calibration writes.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'bundle', 'n1', 'n2', 'probe'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--camera-available', action='store_true', required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.bundle))
    from health_monitor import HealthSampler, failures
    from kernel_analysis import classify
    from n3_bag import assert_quiet, inspect_bag
    from n3_metrics import read_topics
    from sdk_capture import owners, require_n1, stop_child, validate_camera
    from validation_common import evidence_hashes, receipt, utc, write_json
    from wrapper_inspect import validate_readback
    from bounded_microsd import validate_probe, check_binding, check_bag_budget
    import yaml

    if os.geteuid() == 0:
        raise RuntimeError('Publisher and recorder must run as normal user')
    os.environ.update(ROS_DOMAIN_ID='42', ROS_LOCALHOST_ONLY='1')
    p = args.output.resolve()
    n1 = require_n1(args.n1)
    n2 = receipt(args.n2, 'N2_ACCEPT')
    if n1['camera'] != n2['camera']:
        raise RuntimeError('N1/N2 camera identity mismatch')
    owners()
    bag = p / 'bag'
    binding = validate_probe(json.loads(args.probe.read_text()), bag, 60)
    assert_quiet(42, p / 'domain-before.json', None)
    params = p / 'n3-baseline.yaml'
    shutil.copy2(params, p / 'requested-parameters.yaml')
    result = {'stage': 'N3_RECORD', 'verdict': 'FAIL', 'utc_start': utc(),
              'bag': str(bag), 'seconds': 60, 'domain': 42, 'failures': [],
              'storage_scope': 'BOUNDED_MICROSD_DIAGNOSTIC_ONLY',
              'storage_binding': binding, 'camera': n1['camera'],
              'boot_id': n1['boot_id'], 'runtime_bundle': str(args.bundle),
              'calibration_qualified': False, 'commands': {}}
    children, handles = {}, []
    sampler = HealthSampler(p)
    deadline = time.monotonic() + 900
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))

    def start(name, argv):
        result['commands'][name] = argv
        handle = (p / (name + '.log')).open('x')
        handles.append(handle)
        children[name] = subprocess.Popen(argv, stdout=handle, stderr=subprocess.STDOUT,
                                          stdin=subprocess.DEVNULL, start_new_session=True)
        return children[name]

    def capture(label, argv):
        r = subprocess.run(argv, text=True, capture_output=True, timeout=20)
        write_json(p / (label + '.json'), {'argv': argv, 'returncode': r.returncode,
                                         'stdout': r.stdout, 'stderr': r.stderr, 'utc': utc()})
        if r.returncode:
            raise RuntimeError(label + ' failed')
        return r.stdout

    try:
        capture('usb-before', ['lsusb', '-t'])
        capture('kernel-boot-before', ['journalctl', '-k', '-b', '--no-pager', '-o', 'short-iso-precise'])
        start('journal', ['journalctl', '-k', '-f', '-n', '0', '--no-pager', '-o', 'short-iso-precise'])
        time.sleep(.3)
        camera = start('camera', ['ros2', 'run', 'realsense2_camera', 'realsense2_camera_node',
                                 '--ros-args', '-r', '__ns:=/camera', '-r', '__node:=camera',
                                 '--params-file', str(params)])
        health = (p / 'health.jsonl').open('x'); handles.append(health)

        def monitor():
            if time.monotonic() > deadline or (p / 'abort.request').exists():
                raise RuntimeError('Session deadline or explicit abort')
            for name in ('camera', 'journal'):
                if children[name].poll() is not None:
                    raise RuntimeError(name + ' exited unexpectedly')
            validate_camera(n1['camera'])
            check_binding(binding); check_bag_budget(bag, binding)
            sample = sampler.sample(camera.pid)
            health.write(json.dumps(sample) + '\n'); health.flush()
            if failures(sample):
                raise RuntimeError('; '.join(failures(sample)))
            for name in ('camera', 'journal', 'recorder'):
                path = p / (name + '.log')
                if path.exists():
                    text = path.read_text(errors='replace')
                    hardware_error = 'Hardware Notification:' in text and 'Hardware Error' in text
                    if path.stat().st_size > 16 * 1024**2 or classify(text)['faults'] or hardware_error:
                        raise RuntimeError(name + ' log budget/fault; inspect preserved raw log')

        for _ in range(5):
            monitor(); time.sleep(1)
        actual_text = capture('parameter-readback', ['ros2', 'param', 'dump', '/camera/camera'])
        def flatten_parameters(value, prefix=''):
            output = {}
            for key, child in value.items():
                name = prefix + key
                if isinstance(child, dict):
                    output.update(flatten_parameters(child, name + '.'))
                else:
                    output[name] = child
            return output
        actual = flatten_parameters(yaml.safe_load(actual_text)['/camera/camera']['ros__parameters'])
        expected = yaml.safe_load(params.read_text())['/camera/camera']['ros__parameters']
        errors = validate_readback(actual, expected)
        if errors:
            raise RuntimeError('; '.join(errors))
        write_json(p / 'publisher-ready.json', {'utc': utc(), 'owner_pid': os.getpid(),
                   'publisher_pid': camera.pid, 'parameter_readback_matches': True})
        while not (p / 'record-request.json').exists():
            monitor(); time.sleep(1)
        request = json.loads((p / 'record-request.json').read_text())
        topics_file, qos_file = p / request['topics_file'], p / request['qos_file']
        specs = read_topics(topics_file)
        live = json.loads((p / 'live-gate.json').read_text())
        if live['verdict'] != 'PASS' or live['failures']:
            raise RuntimeError('Physical live observer has not passed')
        for path in (topics_file, qos_file):
            if not path.resolve().is_relative_to(p):
                raise RuntimeError('Recording configuration must be retained inside this session')
        recorder = start('recorder', ['ros2', 'bag', 'record', '--storage', 'sqlite3',
                         '--output', str(bag), '--disable-keyboard-controls',
                         '--qos-profile-overrides-path', str(qos_file),
                         '--topics', *[spec['name'] for spec in specs]])
        record_start = time.monotonic()
        observer = start('recording-observer', [sys.executable, str(args.bundle / 'n3_observer.py'),
                         '--camera-available', '--mode', 'live', '--domain', '42', '--seconds', '55',
                         '--topics-file', str(topics_file), '--output', str(p / 'recording-observer.json')])
        write_json(p / 'recording-started.json', {'utc': utc(), 'monotonic_s': record_start,
                   'recorder_pid': recorder.pid, 'duration_limit_s': 60, 'explicit_topics': [s['name'] for s in specs]})
        while time.monotonic() - record_start < 60:
            monitor()
            if recorder.poll() is not None:
                raise RuntimeError('Recorder exited before bounded interval ended')
            if observer.poll() is not None and observer.returncode:
                raise RuntimeError('Recording observer failed')
            time.sleep(min(1, max(.01, 60 - (time.monotonic() - record_start))))
        result['recorder_shutdown'] = stop_child(recorder, grace=20)
        result['recorder_returncode'] = recorder.returncode
        result['camera_shutdown'] = stop_child(camera, grace=10)
        result['camera_returncode'] = camera.returncode
        if observer.poll() is None:
            observer.wait(timeout=10)
        if observer.returncode:
            raise RuntimeError('Recording observer failed')
        if any(result[label + '_shutdown'] != 'SIGINT' or result[label + '_returncode'] not in (0, -2, 130)
               for label in ('recorder', 'camera')):
            raise RuntimeError('Recorder/publisher did not stop cleanly')
        assert_quiet(42, p / 'domain-after.json', topics_file)
        capture('bag-info', ['ros2', 'bag', 'info', str(bag)])
        result['bag_analysis'] = inspect_bag(bag, specs)
        if result['bag_analysis']['verdict'] != 'PASS':
            raise RuntimeError('Stored bag validation failed; inspect complete result')
        result['verdict'] = 'REVIEW_REQUIRED'
    except (Exception, KeyboardInterrupt) as error:
        result['failures'].append(type(error).__name__ + ': ' + str(error))
    finally:
        for name in ('recorder', 'recording-observer', 'camera', 'journal'):
            result[name + '_cleanup'] = stop_child(children.get(name))
        for handle in handles:
            handle.close()
        result['utc_end'] = utc()
        result['power_after'] = capture('power-after', ['vcgencmd', 'get_throttled']).strip()
        capture('usb-after', ['lsusb', '-t'])
        capture('kernel-boot-after', ['journalctl', '-k', '-b', '--no-pager', '-o', 'short-iso-precise'])
        result['log_analysis'] = {name: classify((p / (name + '.log')).read_text(errors='replace'))
                                  for name in ('camera', 'journal', 'recorder') if (p / (name + '.log')).exists()}
        if result['power_after'] != 'throttled=0x0' or any(v['faults'] for v in result['log_analysis'].values()):
            result['failures'].append('Final power/log check failed')
        if result['failures']:
            result['verdict'] = 'FAIL'
        result['evidence_sha256'] = evidence_hashes(p)
        write_json(p / 'result.json', result)
    print(json.dumps({k: result[k] for k in ('verdict', 'failures', 'utc_end')}), flush=True)
    return bool(result['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
