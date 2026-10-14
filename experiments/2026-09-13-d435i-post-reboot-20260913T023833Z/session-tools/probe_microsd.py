#!/usr/bin/env python3
"""128 MiB bounded microSD write/fsync/readback probe, not external qualification."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(exist_ok=False)
    def command(argv): return subprocess.check_output(argv, text=True).strip()
    def utc(): return datetime.now(timezone.utc).isoformat()
    result = {'stage': 'BOUNDED_MICROSD_PROBE', 'scope': 'Short bounded captures only; no external-storage PASS',
              'utc_start': utc(), 'hostname': socket.gethostname(), 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
              'verdict': 'FAIL', 'failures': [], 'batches': [], 'mount': command(['findmnt','-J','-T',str(a.output)]),
              'lsblk': command(['lsblk','-J','-o','NAME,MODEL,SERIAL,TRAN,SIZE,FSTYPE,UUID,MOUNTPOINTS']),
              'device_st_dev': a.output.stat().st_dev, 'free_before': shutil.disk_usage(a.output).free,
              'power_before': command(['vcgencmd','get_throttled']), 'usb_before': command(['lsusb','-t'])}
    probe = a.output/'owned-probe.bin'
    try:
        if result['power_before'] != 'throttled=0x0' or result['free_before'] < 10*1024**3:
            raise RuntimeError('Power/free-space prerequisite failed')
        digest = hashlib.sha256()
        start = time.monotonic()
        with probe.open('xb') as handle:
            for i in range(16):
                block = os.urandom(8*1024**2)
                begin = time.monotonic(); handle.write(block); handle.flush(); os.fsync(handle.fileno())
                elapsed = time.monotonic()-begin
                digest.update(block)
                power = command(['vcgencmd','get_throttled'])
                result['batches'].append({'index':i,'bytes':len(block),'write_fsync_s':elapsed,'MB_s':len(block)/elapsed/1e6,'power':power})
                if power != 'throttled=0x0': raise RuntimeError('Power changed during bounded write')
        result['elapsed_s'] = time.monotonic()-start
        result['bytes'] = probe.stat().st_size
        result['overall_MB_s'] = result['bytes']/result['elapsed_s']/1e6
        result['worst_batch_MB_s'] = min(b['MB_s'] for b in result['batches'])
        result['write_sha256'] = digest.hexdigest()
        readback = hashlib.sha256()
        with probe.open('rb') as handle:
            for block in iter(lambda: handle.read(8*1024**2), b''): readback.update(block)
        result['readback_sha256'] = readback.hexdigest()
        result['power_after'] = command(['vcgencmd','get_throttled'])
        result['usb_after'] = command(['lsusb','-t'])
        if result['write_sha256'] != result['readback_sha256']: raise RuntimeError('Checksum mismatch')
        if result['power_after'] != 'throttled=0x0' or result['usb_after'] != result['usb_before']: raise RuntimeError('Power/USB changed')
        if min(result['overall_MB_s'], result['worst_batch_MB_s']) < 9.216: raise RuntimeError('Below 2x IR payload margin for short image/bag capture')
        result['verdict'] = 'PASS'
    except Exception as e: result['failures'].append(str(e))
    finally:
        if probe.exists(): probe.unlink()
        result['probe_removed'] = not probe.exists()
        result['utc_end'] = utc()
        (a.output/'probe-details.json').write_text(json.dumps(result,indent=2)+'\n')
        result['evidence_sha256'] = {'probe-details.json':hashlib.sha256((a.output/'probe-details.json').read_bytes()).hexdigest()}
        (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('verdict','failures','batches') if k != 'batches'}))
    return bool(result['failures'])


if __name__ == '__main__': raise SystemExit(main())
