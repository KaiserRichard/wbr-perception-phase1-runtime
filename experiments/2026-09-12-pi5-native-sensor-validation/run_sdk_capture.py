#!/usr/bin/env python3
"""Bounded SDK metadata/IMU capture with continuous kernel monitoring.

No image payload or ROS bag is recorded by rs-data-collect. Only the child
processes started here are stopped. Any abnormal termination fails the run.
"""
import argparse
import glob
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone

USB_SERIAL = '251843061466'
DEVICE_SERIAL = '243322073847'
USB_ROOT = Path('/mnt/wbr-data')
FAULT = re.compile(r'USB disconnect|reset .*USB device|new .*USB device|'
                   r'under.?voltage|throttl|over.?current|segfault|Frame Corrupted|'
                   r'Incomplete video frame|Permission denied|'
                   r'xhci.*(?:error|fail|dead|timeout|not responding)|'
                   r'uvcvideo.*(?:fail|error)|(?:hid|iio).*?(?:fail|error)', re.I)


def command(argv):
    return subprocess.check_output(argv, text=True).strip()


def stop_child(process, grace=10):
    if process is None or process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New directory on the verified USB mount')
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--seconds', type=int, required=True)
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run as the normal camera user')
    if not 1 <= args.seconds <= 600:
        parser.error('Choose a bounded 1–600 second probe')
    target = args.output.resolve()
    if not target.is_relative_to(USB_ROOT / 'wbr-perception-phase1/2026-09-12'):
        parser.error('Output must be in the dated USB experiment root')
    if command(['findmnt', '-rn', '-T', str(USB_ROOT), '-o', 'UUID']) != '1017-F615':
        parser.error('Expected experiment USB filesystem is not mounted')
    if shutil.disk_usage(USB_ROOT).free < 2 * 1024**3:
        parser.error('Less than 2 GiB free on the experiment drive')
    cameras = [p for p in Path('/sys/bus/usb/devices').glob('*')
               if (p/'serial').is_file() and (p/'serial').read_text().strip() == USB_SERIAL]
    if len(cameras) != 1:
        parser.error('Expected exactly one camera with the session serial')
    camera = cameras[0]
    if (camera/'speed').read_text().strip() != '5000':
        parser.error('Camera is not at the validated 5000 Mb/s speed')
    owners = subprocess.run(['fuser', *glob.glob('/dev/video*'), *glob.glob('/dev/iio:*')],
                            capture_output=True, text=True)
    if owners.returncode == 0:
        parser.error('An existing process owns a sensor device: ' + owners.stdout)
    target.mkdir(parents=True, exist_ok=False)
    shutil.copy2(args.config, target/'profile.csv')
    # SDK selection uses Device Serial Number; sysfs/udev uses ASIC/USB serial.
    argv = ['/opt/ros/jazzy/bin/rs-data-collect', '-s', DEVICE_SERIAL,
            '-c', str(target/'profile.csv'), '-t', str(args.seconds), '-f', str(target/'frames.csv')]
    result = {'started_utc': datetime.now(timezone.utc).isoformat(), 'argv': argv,
              'duration_requested_seconds': args.seconds, 'user': command(['id']),
              'device_serial': DEVICE_SERIAL, 'asic_usb_serial': USB_SERIAL,
              'usb_before': command(['lsusb', '-t']), 'lsusb_before': command(['lsusb']),
              'failures': [], 'resource_samples': []}
    (target/'command.json').write_text(json.dumps(result, indent=2)+'\n')
    follower = collector = None
    start = time.monotonic()
    cpu_previous = None
    try:
        with (target/'kernel-live.log').open('x') as kernel, (target/'sdk.log').open('x') as sdk:
            # Start following before the SDK opens the device; keep until it closes.
            follower = subprocess.Popen(['journalctl', '-k', '-f', '-n', '0', '-o', 'short-iso-precise'],
                                        stdout=kernel, stderr=subprocess.STDOUT)
            time.sleep(1)
            if follower.poll() is not None:
                raise RuntimeError('Kernel follower failed to start')
            collector = subprocess.Popen(argv, stdout=sdk, stderr=subprocess.STDOUT)
            while collector.poll() is None:
                if time.monotonic() - start > args.seconds + 30:
                    result['failures'].append('SDK exceeded bounded run time')
                    break
                logs = (target/'kernel-live.log').read_text() + (target/'sdk.log').read_text()
                faults = [line for line in logs.splitlines() if FAULT.search(line)]
                if faults:
                    result['failures'].extend(faults)
                    break
                if follower.poll() is not None:
                    result['failures'].append('Continuous kernel follower exited early')
                    break
                try:
                    if (camera/'serial').read_text().strip() != USB_SERIAL or (camera/'speed').read_text().strip() != '5000':
                        raise RuntimeError('Camera identity or speed changed')
                    cpu = [int(v) for v in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
                    cpu_now = (sum(cpu), cpu[3] + cpu[4])
                    cpu_busy = None
                    if cpu_previous and cpu_now[0] > cpu_previous[0]:
                        cpu_busy = 100 * (1 - (cpu_now[1]-cpu_previous[1])/(cpu_now[0]-cpu_previous[0]))
                    cpu_previous = cpu_now
                    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
                    result['resource_samples'].append({
                        'elapsed_seconds': time.monotonic()-start,
                        'temperature_c': int(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000,
                        'throttled': command(['vcgencmd', 'get_throttled']),
                        'process': command(['ps', '-p', str(collector.pid), '-o', 'pid=,%cpu=,rss=,etimes=']),
                        'cpu_system_busy_percent': cpu_busy,
                        'memory_available_kib': int(memory['MemAvailable'].split()[0]),
                        'storage_free_bytes': shutil.disk_usage(USB_ROOT).free,
                    })
                    if result['resource_samples'][-1]['throttled'] != 'throttled=0x0':
                        result['failures'].append('Power/thermal flag is nonzero')
                        break
                except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
                    # Process may exit normally between poll and ps; other errors fail.
                    if collector.poll() is None:
                        result['failures'].append(str(error))
                    break
                time.sleep(1)
            if result['failures']:
                stop_child(collector)
            result['sdk_returncode'] = collector.wait()
            time.sleep(1)
            stop_child(follower)
    except BaseException as error:
        result['failures'].append(f'{type(error).__name__}: {error}')
        raise
    finally:
        stop_child(collector)
        stop_child(follower)
        result['finished_utc'] = datetime.now(timezone.utc).isoformat()
        result['elapsed_seconds'] = time.monotonic()-start
        result['usb_after'] = command(['lsusb', '-t'])
        result['lsusb_after'] = command(['lsusb'])
        result['sdk_returncode'] = collector.returncode if collector else None
        for name in ('kernel-live.log', 'sdk.log'):
            if (target/name).exists():
                result['failures'].extend(line for line in (target/name).read_text().splitlines()
                                          if FAULT.search(line) and line not in result['failures'])
        result['capture_completed_without_detected_fault'] = result['sdk_returncode'] == 0 and not result['failures']
        result['N2'] = 'NOT DECIDED: analyze all three streams, image samples and kernel/health evidence'
        (target/'capture-result.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k != 'resource_samples'}, indent=2))
    return 0 if result['capture_completed_without_detected_fault'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
