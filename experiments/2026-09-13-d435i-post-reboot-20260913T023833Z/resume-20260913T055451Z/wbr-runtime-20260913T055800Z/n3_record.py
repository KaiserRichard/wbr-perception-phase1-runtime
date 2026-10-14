#!/usr/bin/env python3
"""Gated short native ROS session: live observer, explicit bag, clean stop, metadata.

The main thread owns its camera, observer, journal and recorder process groups.
Replay is a separate command after this process has stopped its live camera.
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

from health_monitor import HealthSampler, failures as health_failures
from kernel_analysis import classify
from n3_bag import assert_quiet, inspect_bag
from n3_metrics import read_topics
from sdk_capture import stop_child, validate_camera, owners
from storage_qualify import validate_mount, _check_pinned_mount
from validation_common import (camera_guard, checked, evidence_hashes, provenance,
                               receipt, run, sha256, utc, write_json)
from wrapper_inspect import inspect as inspect_wrapper, validate_readback

HERE = Path(__file__).resolve().parent


def recorder_argv(bag, specs):
    return ['ros2', 'bag', 'record', '--storage', 'sqlite3', '--output', str(bag),
            '--disable-keyboard-controls', '--qos-profile-overrides-path', str(HERE / 'n3_qos.yaml'),
            '--topics', *[spec['name'] for spec in specs]]


def run_session(args):
    import yaml
    camera_guard(args.camera_available)
    os.environ.update(ROS_DOMAIN_ID='42', ROS_LOCALHOST_ONLY='1')
    n2 = receipt(args.n2_result, 'N2_ACCEPT')
    storage = receipt(args.storage_result, 'STORAGE_QUALIFY')
    n1 = receipt(args.n1_result, 'N1_PRECHECK')
    if n1['camera'] != n2['camera']:
        raise RuntimeError('N1 and N2 camera identity/topology differ; repeat N2 after transport change')
    if n1['utc_start'] <= storage['utc_end']:
        raise RuntimeError('N1 must follow storage qualification with both USB devices attached')
    validate_camera(n1['camera'])
    owners()
    binding = validate_mount(storage['mount'], storage['uuid'], storage['device'])
    if binding['binding'] != storage['mount_binding']['binding'] or binding['blockdevices'] != storage['mount_binding']['blockdevices']:
        raise RuntimeError('Storage identity changed since qualification')
    static = inspect_wrapper(Path('/opt/ros/jazzy/share/realsense2_camera'), HERE / 'n3_baseline.yaml')
    if not static['automatic_checks_pass']:
        raise RuntimeError('Installed wrapper version/parameter-name check failed')
    bag = args.bag.absolute()
    if not bag.parent.is_dir() or bag.exists() or any(p.is_symlink() for p in [bag, *bag.parents]):
        raise RuntimeError('Bag requires a new nonsymlink path in an existing external directory')
    if not bag.parent.resolve().is_relative_to(Path(storage['mount'])) or bag.parent.stat().st_dev != binding['mount_st_dev']:
        raise RuntimeError('Bag path is outside the qualified external filesystem')
    args.output.mkdir(parents=True, exist_ok=False)
    for name, src in [('n2-result.json', args.n2_result), ('n1-result.json', args.n1_result), ('storage-result.json', args.storage_result)]:
        shutil.copy2(src, args.output / name)
    specs = read_topics()
    result = {'stage': 'N3_RECORD', 'verdict': 'FAIL', 'utc_start': utc(), 'failures': [],
              'goal': 'Validate native raw ROS delivery and a short finalized explicit-topic bag',
              'hypothesis': 'Qualified storage sustains baseline delivery without sensor loss during recording',
              'provenance': provenance(), 'storage_binding': binding, 'bag': str(bag),
              'seconds': args.seconds, 'domain': 42, 'wrapper_static': static}
    env = dict(os.environ, ROS_DOMAIN_ID='42', ROS_LOCALHOST_ONLY='1')
    commands = {'camera': ['ros2', 'run', 'realsense2_camera', 'realsense2_camera_node', '--ros-args',
                          '-r', '__ns:=/camera', '-r', '__node:=camera', '--params-file', str(HERE / 'n3_baseline.yaml')],
                'recorder': recorder_argv(bag, specs),
                'journal': ['journalctl', '-k', '-f', '-n', '0', '--no-pager', '-o', 'short-iso-precise']}
    result['commands'] = commands
    write_json(args.output / 'command.json', result)
    camera = recorder = journal = observer = None
    handles = []
    sampler = HealthSampler(args.output)
    recorder_sampler = HealthSampler(args.output)
    original_sigterm = signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))
    try:
        write_json(args.output / 'before.json', {'usb_tree': checked(['lsusb', '-t']), 'lsusb': checked(['lsusb'])})
        baseline = run(['journalctl', '-k', '-n', '30', '--no-pager'])
        write_json(args.output / 'kernel-baseline.json', baseline)
        if baseline['returncode'] or baseline['stderr'].strip() or not baseline['stdout'].strip():
            raise RuntimeError('Normal-user kernel journal access is unavailable')
        assert_quiet(42, args.output / 'domain-before.json', None)
        health = (args.output / 'health.jsonl').open('x'); handles.append(health)
        def start(label):
            handle = (args.output / (label + '.log')).open('x'); handles.append(handle)
            return subprocess.Popen(commands[label], stdout=handle, stderr=subprocess.STDOUT,
                                    env=env, start_new_session=True)
        journal = start('journal')
        time.sleep(.3)
        camera = start('camera')
        def monitor():
            if journal.poll() is not None or camera.poll() is not None:
                raise RuntimeError('Camera or continuous journal process exited early')
            validate_camera(n1['camera'])
            _check_pinned_mount(storage['mount'], binding)
            sample = sampler.sample(camera.pid)
            if recorder and recorder.poll() is None:
                sample['recorder'] = recorder_sampler.sample(recorder.pid)
            health.write(json.dumps(sample, allow_nan=False) + '\n'); health.flush()
            if health_failures(sample):
                raise RuntimeError('; '.join(health_failures(sample)))
            for name in ('camera', 'recorder', 'journal'):
                path = args.output / (name + '.log')
                if path.exists():
                    if path.stat().st_size > 16 * 1024**2:
                        raise RuntimeError('Bounded log budget exceeded')
                    if classify(path.read_text(errors='replace'))['faults']:
                        raise RuntimeError(name + ' log contains faults; inspect raw evidence')
        for _ in range(5):
            monitor(); time.sleep(1)
        parameters = run(['ros2', 'param', 'dump', '/camera/camera'], timeout=20)
        write_json(args.output / 'parameter-readback.json', parameters)
        if parameters['returncode']:
            raise RuntimeError('Live parameter readback failed')
        actual = yaml.safe_load(parameters['stdout'])['/camera/camera']['ros__parameters']
        expected = yaml.safe_load((HERE / 'n3_baseline.yaml').read_text())['/camera/camera']['ros__parameters']
        errors = validate_readback(actual, expected)
        if errors:
            raise RuntimeError('; '.join(errors))
        def observe(name, seconds):
            nonlocal observer
            commands[name] = [sys.executable, str(HERE / 'n3_observer.py'), '--camera-available',
                              '--mode', 'live', '--seconds', str(seconds), '--domain', '42',
                              '--output', str(args.output / (name + '.json'))]
            observer = start(name)
            deadline = time.monotonic() + seconds + 25
            while observer.poll() is None:
                monitor()
                if time.monotonic() > deadline:
                    raise RuntimeError('Observer deadline exceeded')
                if recorder and recorder.poll() is not None:
                    raise RuntimeError('Recorder exited before requested interval')
                time.sleep(1)
            if observer.returncode:
                raise RuntimeError(name + ' observer failed')
        observe('live-gate', 60)
        # Recheck the mount immediately before creating the bag. The 60-second
        # observer proved live delivery before any recorder was started.
        validate_mount(storage['mount'], storage['uuid'], storage['device'])
        recorder = start('recorder')
        observe('recording-observer', args.seconds)
        result['recorder_shutdown'] = stop_child(recorder, grace=20)
        result['recorder_returncode'] = recorder.returncode
        if result['recorder_shutdown'] != 'SIGINT' or recorder.returncode not in (0, -2, 130):
            raise RuntimeError('Recorder did not stop cleanly via SIGINT')
        result['bag_analysis'] = inspect_bag(bag, specs)
        if result['bag_analysis']['verdict'] != 'PASS':
            raise RuntimeError('Finalized bag failed content/count/metadata validation')
        result['camera_shutdown'] = stop_child(camera)
        result['camera_returncode'] = camera.returncode
        if result['camera_shutdown'] != 'SIGINT' or camera.returncode not in (0, -2, 130):
            raise RuntimeError('Live camera did not stop cleanly')
        assert_quiet(42, args.output / 'domain-after.json', None)
        result['verdict'] = 'REVIEW_REQUIRED'
    except (Exception, KeyboardInterrupt) as error:
        result['failures'].append(f'{type(error).__name__}: {error}')
    finally:
        for label, process in [('recorder', recorder), ('observer', observer), ('camera', camera), ('journal', journal)]:
            result[label + '_cleanup'] = stop_child(process)
        for handle in handles:
            handle.close()
        signal.signal(signal.SIGTERM, original_sigterm)
        result['utc_end'] = utc()
        result['commands'] = commands
        result['after_usb'] = run(['lsusb', '-t'])
        if result['after_usb']['returncode']:
            result['failures'].append('After USB snapshot failed')
        try:
            validate_camera(n1['camera'])
        except Exception as error:
            result['failures'].append('After camera USB verification: ' + str(error))
        result['log_analysis'] = {p.name: classify(p.read_text(errors='replace')) for p in args.output.glob('*.log')}
        if any(d['faults'] for d in result['log_analysis'].values()):
            result['failures'].append('Raw logs contain faults')
        if result['failures']:
            result['verdict'] = 'FAIL'
        result['evidence_sha256'] = evidence_hashes(args.output)
        write_json(args.output / 'result.json', result)
    print(json.dumps({'verdict': result['verdict'], 'failures': result['failures'], 'output': str(args.output)}))
    return 1 if result['failures'] else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera-available', action='store_true')
    for name in ('n1-result', 'n2-result', 'storage-result', 'bag', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--seconds', type=int, choices=(20, 60), default=20)
    args = parser.parse_args()
    try:
        camera_guard(args.camera_available)
        return run_session(args)
    except Exception as error:
        print(f'STOP: {type(error).__name__}: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
