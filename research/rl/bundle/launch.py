"""Offline stdlib bootstrap; all durable outputs go beside this file on USB."""
import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description='Frozen G1 recipe with optional runtime wall cap')
    parser.add_argument('mode', choices=['run', 'resume', 'smoke'], nargs='?', default='run')
    parser.add_argument('--jobs', type=int)
    parser.add_argument('--seed-wall-cap-min', type=float,
                        help='Cumulative per-seed minutes (default unlimited)')
    args = parser.parse_args()
    if args.jobs is not None and args.jobs < 1:
        parser.error('--jobs must be at least 1')
    import math
    if args.seed_wall_cap_min is not None and (not math.isfinite(args.seed_wall_cap_min) or args.seed_wall_cap_min <= 0):
        parser.error('--seed-wall-cap-min must be a finite positive number')
    mode = args.mode
    job_args = [] if args.jobs is None else ['--jobs', str(args.jobs)]
    if args.seed_wall_cap_min is not None:
        job_args += ['--seed-wall-cap-min', str(args.seed_wall_cap_min)]
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    receipt = ROOT / 'runs' / f'launch-{stamp}'
    receipt.mkdir(parents=True)
    with (receipt / 'console.log').open('w', buffering=1) as log:
        def run(command, required=True):
            print(subprocess.list2cmdline([str(x) for x in command]), flush=True)
            proc = subprocess.Popen([str(x) for x in command], cwd=ROOT, env=os.environ.copy(),
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    errors='replace')
            for line in proc.stdout:
                print(line, end='', flush=True)
                log.write(line)
            result = proc.wait()
            if required and result:
                raise RuntimeError(f'Exit {result}: {command}')
            return result
        started = time.monotonic()
        # Hash checks precede wheel installation.
        import hashlib
        for row in (ROOT / 'SHA256SUMS').read_text().splitlines():
            expected, name = row.split('  ', 1)
            path = ROOT / name
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
            if h.hexdigest() != expected:
                raise RuntimeError(f'Bundle hash mismatch: {name}')
        work = Path(os.environ.get('WBR_WORK', str(Path(os.environ.get('LOCALAPPDATA', str(ROOT))) / 'WBR-G1')))
        work.mkdir(parents=True, exist_ok=True)
        for name in ('TEMP', 'TMP', 'UV_CACHE_DIR'):
            os.environ[name] = str(work / 'cache')
        (work / 'cache').mkdir(exist_ok=True)
        os.environ.update(UV_PYTHON_DOWNLOADS='never', UV_OFFLINE='1', PYTHONNOUSERSITE='1')
        (receipt / 'host.json').write_text(json.dumps({'platform': platform.platform(),
            'machine': platform.machine(), 'cpu': platform.processor(), 'command': sys.argv,
            'work': str(work), 'usb': str(ROOT), 'device': 'G1 CPU PPO + CPU MuJoCo'}, indent=2))
        try:
            gpu = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            (receipt / 'nvidia-smi.txt').write_text(gpu.stdout + gpu.stderr)
        except OSError as exc:
            (receipt / 'nvidia-smi.txt').write_text(str(exc))
        # Retain a staff-readable machine receipt; failure is nonfatal.
        try:
            host = subprocess.run(['systeminfo'], capture_output=True, text=True, errors='replace')
            (receipt / 'systeminfo.txt').write_text(host.stdout+host.stderr, encoding='utf-8')
        except OSError as exc:
            (receipt / 'systeminfo.txt').write_text(str(exc))
        # Recreate after disk wipe; uv is called directly, never activate or edit PATH.
        python = work / '.venv/Scripts/python.exe'
        if not python.exists():
            run([ROOT / 'bin/uv.exe', 'venv', '--python', ROOT / 'python/python.exe', work / '.venv'])
        run([ROOT / 'bin/uv.exe', 'pip', 'install', '--python', python, '--no-index',
             '--find-links', ROOT / 'wheels', '--require-hashes', '-r', ROOT / 'locks/win-cpu.txt'])
        (receipt / 'setup.json').write_text(json.dumps({'elapsed_s': time.monotonic()-started}))
        if mode == 'resume':
            run([python, ROOT / 'portable.py', 'resume-latest', '--run', ROOT / 'runs', *job_args])
        elif mode == 'smoke':
            run([python, ROOT / 'portable.py', 'smoke', '--run', ROOT / 'runs' / f'g1-smoke-{stamp}',
                 '--smoke-seconds', str(600-(time.monotonic()-started)), *job_args])
        else:
            run([python, ROOT / 'portable.py', 'run', '--run', ROOT / 'runs' / f'g1-{stamp}', *job_args])
        (receipt / 'success.txt').write_text('USB checkpoint reload verified; see segment receipts.\n')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        error = traceback.format_exc()
        print(error, flush=True)
        with (ROOT / 'runs/launch-error.txt').open('a') as f:
            f.write(error)
        raise SystemExit(1)
