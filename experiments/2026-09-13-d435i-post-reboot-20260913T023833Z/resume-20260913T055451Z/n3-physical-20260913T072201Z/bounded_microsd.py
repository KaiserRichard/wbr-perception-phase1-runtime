"""Explicit short-recording exception; never qualifies microSD as external storage."""
import json
from pathlib import Path
import shutil

from validation_common import checked


def validate_probe(probe, bag, seconds):
    if probe.get('stage') != 'BOUNDED_MICROSD_PROBE' or probe.get('verdict') != 'PASS' or probe.get('failures'):
        raise RuntimeError('No passing bounded microSD probe')
    if not 0 < seconds <= 60:
        raise RuntimeError('MicroSD bag is limited to 60 seconds')
    if (probe.get('bytes', 0) < 128 * 1024**2 or not probe.get('probe_removed') or
        probe.get('write_sha256') != probe.get('readback_sha256') or not probe.get('write_sha256') or
        min(probe.get('overall_MB_s', 0), probe.get('worst_batch_MB_s', 0)) < 9.216):
        raise RuntimeError('MicroSD write/fsync/readback evidence failed')
    if probe.get('power_before') != 'throttled=0x0' or probe.get('power_after') != 'throttled=0x0':
        raise RuntimeError('MicroSD probe power was not clean')
    mounts = json.loads(probe['mount'])['filesystems']
    if len(mounts) != 1 or not mounts[0]['source'].startswith('/dev/mmcblk') or mounts[0]['fstype'] != 'ext4':
        raise RuntimeError('Expected observed ext4 microSD filesystem')
    path = Path(bag).absolute()
    if path.exists() or not path.parent.is_dir() or any(p.is_symlink() for p in (path, *path.parents)):
        raise RuntimeError('Bag requires a new nonsymlink path and existing parent')
    binding = {'scope': 'BOUNDED_MICROSD_DIAGNOSTIC_ONLY', 'mount': mounts[0],
               'mount_st_dev': probe['device_st_dev'], 'minimum_free_bytes': 8 * 1024**3,
               'maximum_bag_bytes': 512 * 1024**2, 'bag_parent': str(path.parent),
               'probe_utc_end': probe['utc_end']}
    check_binding(binding)
    return binding


def check_binding(binding):
    path = Path(binding['bag_parent'])
    current = json.loads(checked(['findmnt', '-J', '-T', str(path)]))['filesystems']
    if current != [binding['mount']] or path.stat().st_dev != binding['mount_st_dev']:
        raise RuntimeError('MicroSD filesystem binding changed')
    if shutil.disk_usage(path).free < binding['minimum_free_bytes']:
        raise RuntimeError('MicroSD 8 GiB free-space reserve reached')


def check_bag_budget(bag, binding):
    path = Path(bag)
    if path.exists() and sum(p.stat().st_size for p in path.rglob('*') if p.is_file()) > binding['maximum_bag_bytes']:
        raise RuntimeError('Bounded microSD bag exceeded 512 MiB')
