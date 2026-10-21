#!/usr/bin/env python3
"""Bounded camera-free integration check. Run on Pi with ROS Jazzy sourced."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('node', 'bag', 'settings', 'vocabulary', 'output'):
        parser.add_argument('--' + arg, required=True, type=Path)
    parser.add_argument('--domain', type=int, default=187)
    args = parser.parse_args()
    for name in ('node', 'bag', 'settings', 'vocabulary', 'output'):
        setattr(args, name, getattr(args, name).resolve())
    if not 1 <= args.domain <= 232:
        parser.error('use a private nonzero ROS domain (1..232)')
    args.output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.update(ROS_DOMAIN_ID=str(args.domain), ROS_LOCALHOST_ONLY='1',
               ROS_LOG_DIR=str(args.output / 'ros-logs'), OPENBLAS_NUM_THREADS='1',
               OMP_NUM_THREADS='1', LD_BIND_NOW='1')
    started = time.monotonic()
    # Work stops at 145s; three owned process groups have <=10s cleanup each.
    deadline = started + 145
    children, handles = {}, []
    receipt = {'commands': {}, 'pids': {}, 'exits': {}, 'signals': [],
               'domain': args.domain, 'bag_seconds': 20, 'rate': 0.3, 'child_deadline_s': 180}

    def save():
        receipt['elapsed_s'] = time.monotonic() - started
        (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')

    def launch(name, command):
        log = (args.output / (name + '.log')).open('x')
        handles.append(log)
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                 cwd=args.output, env=env, start_new_session=True)
        children[name] = child
        receipt['commands'][name], receipt['pids'][name] = command, child.pid
        save()
        return child

    def ready(name, needles, seconds):
        until = min(deadline, time.monotonic() + seconds)
        while time.monotonic() < until:
            if children[name].poll() is not None:
                raise RuntimeError(f'{name} exited {children[name].returncode}')
            log = (args.output / (name + '.log')).read_text(errors='replace')
            if all(needle in log for needle in needles):
                return
            time.sleep(0.2)
        raise TimeoutError(f'{name} readiness timeout')

    def stop(name):
        child = children[name]
        for sig, seconds in ((signal.SIGINT, 7), (signal.SIGTERM, 2), (signal.SIGKILL, 1)):
            # Address only our own session/process group, including descendants.
            try:
                os.killpg(child.pid, sig)
            except ProcessLookupError:
                break
            receipt['signals'].append([name, sig.name])
            try:
                child.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                continue
            try:
                os.killpg(child.pid, 0)
            except ProcessLookupError:
                break
        receipt['exits'][name] = child.poll()

    def terminate(signum, _frame):
        raise RuntimeError(f'supervisor received signal {signum}')

    signal.signal(signal.SIGTERM, terminate)
    try:
        launch('record', ['ros2', 'bag', 'record', '--storage', 'mcap', '--use-sim-time',
                         '--output', str(args.output / 'map-bag'), '--topics',
                         '/d435_orb/pose', '/d435_orb/status',
                         '/d435_orb/map_points', '/d435_orb/map_points_info'])
        launch('slam', [str(args.node), '--ros-args', '-p', 'mode:=stereo', '-p', 'use_sim_time:=true',
                        '-p', 'orb_vocabulary:=' + str(args.vocabulary),
                        '-p', 'orb_settings:=' + str(args.settings),
                        '-p', 'image_topic:=/wbr_map_test/left',
                        '-p', 'second_topic:=/wbr_map_test/right'])
        ready('slam', ['viewer disabled'], 55)
        # With simulated time the recorder cannot subscribe until player /clock exists.
        ready('record', ['Listening for topics'], 10)
        player = launch('play', ['ros2', 'bag', 'play', str(args.bag), '--rate', '0.3',
                                '--clock', '40', '--playback-duration', '20',
                                '--read-ahead-queue-size', '20', '--disable-keyboard-controls',
                                '--topics', '/camera/camera/infra1/image_rect_raw',
                                '/camera/camera/infra2/image_rect_raw', '--remap',
                                '/camera/camera/infra1/image_rect_raw:=/wbr_map_test/left',
                                '/camera/camera/infra2/image_rect_raw:=/wbr_map_test/right'])
        while player.poll() is None:
            if time.monotonic() >= deadline:
                raise TimeoutError('145s work deadline reached')
            if children['slam'].poll() is not None or children['record'].poll() is not None:
                raise RuntimeError('SLAM or recorder exited during replay')
            time.sleep(0.2)
        if player.returncode:
            raise RuntimeError(f'player exited {player.returncode}')
        time.sleep(min(3, max(0, deadline - time.monotonic())))
    except BaseException as error:
        receipt['error'] = repr(error)
    finally:
        for name in ('play', 'slam', 'record'):
            if name in children:
                stop(name)
        remaining = []
        for name, child in children.items():
            try:
                os.killpg(child.pid, 0)
                remaining.append(name)
            except ProcessLookupError:
                pass
        abnormal = {name: code for name, code in receipt['exits'].items() if code != 0}
        if abnormal:
            receipt.setdefault('error', f'abnormal child exits: {abnormal}')
        receipt['remaining_process_groups'] = remaining
        receipt['all_owned_children_exited'] = all(p.poll() is not None for p in children.values())
        save()
        for handle in handles:
            handle.close()
    if receipt.get('error') or remaining or not receipt['all_owned_children_exited']:
        print(json.dumps(receipt, indent=2))
        return 1
    # Writers have stopped: prove the independently retained MCAP is readable.
    checker = Path(__file__).resolve().parents[1] / 'scripts' / 'check_map_points_bag.py'
    remaining_budget = started + 180 - time.monotonic()
    if remaining_budget <= 0:
        receipt['error'] = '180s deadline reached before persisted validation'
        save()
        return 1
    with (args.output / 'validation.json').open('x') as output, (args.output / 'validation.log').open('x') as errors:
        try:
            check = subprocess.run([sys.executable, str(checker), str(args.output / 'map-bag'),
                                    '--source-bag', str(args.bag)], stdout=output, stderr=errors,
                                   timeout=min(30, remaining_budget))
            receipt['validation_exit'] = check.returncode
        except subprocess.TimeoutExpired:
            receipt['error'] = 'persisted validation exceeded remaining deadline'
            receipt['validation_exit'] = 124
    save()
    print(json.dumps(receipt, indent=2))
    return receipt['validation_exit']


if __name__ == '__main__':
    raise SystemExit(main())
