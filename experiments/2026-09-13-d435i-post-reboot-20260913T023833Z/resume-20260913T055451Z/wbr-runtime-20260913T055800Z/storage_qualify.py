#!/usr/bin/env python3
"""Qualify an explicitly selected external USB filesystem; never mount or format it.

The destructive scope is limited to this process's exclusive-created probe file.
No benchmark runs without --qualify-external-storage. Phase A uses unit tests only.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import stat
import sys
import time
import uuid as uuid_module

from validation_common import checked, provenance, read, run, sha256, utc, write_json


GIB = 1024 ** 3
CHUNK_BYTES = 64 * 1024 ** 2
MINIMUM_FREE_BYTES = 10 * GIB
MINIMUM_MBPS = 9.216  # Twice the 4.608 MB/s IR1 pixel payload; engineering margin.


def _flatten_devices(devices):
    for device in devices:
        yield device
        yield from _flatten_devices(device.get("children", []))


def evaluate_mount_snapshot(snapshot, mount, uuid, device):
    """Evaluate captured mount facts; pure function used by synthetic safety tests."""
    if snapshot["euid"] == 0:
        raise RuntimeError("Storage qualification must run as the normal user")
    if snapshot["symlink_component"]:
        raise RuntimeError("Refusing a mount path with a symlink component")
    if mount == "/" or snapshot["mount_st_dev"] == snapshot["root_st_dev"]:
        raise RuntimeError("Refusing root filesystem or an unmounted fallback directory")
    if not snapshot["device_is_block"]:
        raise RuntimeError("Expected an existing block device")
    entries = snapshot["findmnt"].get("filesystems", [])
    if len(entries) != 1:
        raise RuntimeError("Expected exactly one exact mountpoint")
    binding = entries[0]
    if binding.get("target") != mount or binding.get("source") != device:
        raise RuntimeError("Mount source or exact mountpoint does not match")
    if not uuid or binding.get("uuid") != uuid:
        raise RuntimeError("Filesystem UUID does not match")
    if not binding.get("fstype") or "rw" not in binding.get("options", "").split(","):
        raise RuntimeError("Filesystem type unavailable or mount is read-only")
    if binding.get("maj:min") != snapshot["device_major_minor"]:
        raise RuntimeError("findmnt block identity does not match the selected device")
    if snapshot["mount_major_minor"] != snapshot["device_major_minor"]:
        raise RuntimeError("Mounted filesystem is not backed by the selected device")
    devices = list(_flatten_devices(snapshot["lsblk"].get("blockdevices", [])))
    if not devices or any(str(x.get("path", "")).startswith("/dev/mmcblk") for x in devices):
        raise RuntimeError("Refusing microSD or an unknown block-device chain")
    disks = [x for x in devices if x.get("type") == "disk"]
    if len(disks) != 1 or disks[0].get("tran") != "usb":
        raise RuntimeError("Expected one external USB disk ancestor")
    if any(x.get("ro") not in (False, 0, "0") for x in devices):
        raise RuntimeError("Block device is read-only or its state is unknown")
    if not disks[0].get("model") or not disks[0].get("serial"):
        raise RuntimeError("External block-device model/serial identity is incomplete")
    if not snapshot["writable"]:
        raise RuntimeError("Mount is not writable/searchable by the normal user")
    if snapshot["free_bytes"] < MINIMUM_FREE_BYTES:
        raise RuntimeError("Less than 10 GiB free space; do not benchmark or record")
    return {"mount": mount, "uuid": uuid, "device": device,
            "binding": binding, "blockdevices": devices,
            "free_bytes": snapshot["free_bytes"],
            "mount_st_dev": snapshot["mount_st_dev"],
            "mount_inode": snapshot["mount_inode"]}


def validate_mount(mount, uuid, device):
    """Return verified identity binding or raise before any dataset/probe write.

    Reuse immediately before bag recording. Receipt freshness is a separate check.
    Paths must identify an already mounted external USB filesystem, never root/SD.
    """
    requested = Path(mount).expanduser()
    if not requested.is_absolute():
        raise RuntimeError("Mount path must be absolute")
    if ".." in requested.parts:
        raise RuntimeError("Mount path must not contain '..'")
    components = [requested, *requested.parents]
    symlink = any(p.is_symlink() for p in components)
    mount_path = str(requested)
    device_path = str(Path(device).resolve(strict=True))
    mount_stat = requested.stat()
    device_stat = os.stat(device_path)
    free = os.statvfs(requested)
    snapshot = {
        "euid": os.geteuid(), "symlink_component": symlink,
        "device_is_block": stat.S_ISBLK(device_stat.st_mode),
        "mount_st_dev": mount_stat.st_dev, "mount_inode": mount_stat.st_ino,
        "root_st_dev": os.stat("/").st_dev,
        "mount_major_minor": f"{os.major(mount_stat.st_dev)}:{os.minor(mount_stat.st_dev)}",
        "device_major_minor": f"{os.major(device_stat.st_rdev)}:{os.minor(device_stat.st_rdev)}",
        "writable": os.access(requested, os.W_OK | os.X_OK),
        "free_bytes": free.f_bavail * free.f_frsize,
        "findmnt": json.loads(checked([
            "findmnt", "--json", "--mountpoint", mount_path,
            "--output", "TARGET,SOURCE,FSTYPE,UUID,OPTIONS,MAJ:MIN"])),
        "lsblk": json.loads(checked([
            "lsblk", "--json", "--paths", "--bytes", "--inverse",
            "--output", "NAME,PATH,TYPE,TRAN,MODEL,SERIAL,SIZE,FSTYPE,UUID,MOUNTPOINTS,PKNAME,RM,RO",
            device_path])),
    }
    return evaluate_mount_snapshot(snapshot, mount_path, uuid, device_path)


def assess_benchmark(samples, bytes_written, elapsed, checksum_matches,
                     minimum_bytes=GIB, minimum_seconds=60.0):
    """Return pass/fail reasons from measured write+fsync cycles, without hardware."""
    failures = []
    if not math.isfinite(elapsed) or any(not math.isfinite(x[k]) for x in samples
                                       for k in ('decimal_MB_per_second', 'fsync_seconds')):
        raise ValueError('Nonfinite benchmark measurements')
    if bytes_written < minimum_bytes:
        failures.append("Minimum write volume was not reached")
    if elapsed < minimum_seconds:
        failures.append("Sustained write duration was not reached before the write budget cap")
    if not checksum_matches:
        failures.append("Readback checksum mismatch")
    if not samples or elapsed <= 0:
        failures.append("Missing benchmark timing samples")
    overall = bytes_written / elapsed / 1_000_000 if elapsed > 0 else 0.0
    worst = min((x["decimal_MB_per_second"] for x in samples), default=0.0)
    if overall < MINIMUM_MBPS or worst < MINIMUM_MBPS:
        failures.append("Overall or worst 64 MiB write+fsync throughput is below 9.216 MB/s")
    return {"failures": failures, "overall_decimal_MB_per_second": overall,
            "worst_batch_decimal_MB_per_second": worst,
            "max_fsync_seconds": max((x["fsync_seconds"] for x in samples), default=0.0)}


def _check_pinned_mount(mount, binding):
    path = Path(mount)
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise RuntimeError("Mount path became a symlink")
    current = path.stat()
    if (current.st_dev, current.st_ino) != (binding["mount_st_dev"], binding["mount_inode"]):
        raise RuntimeError("Mount disappeared or its identity changed during the probe")
    free = os.statvfs(path)
    if free.f_bavail * free.f_frsize < MINIMUM_FREE_BYTES:
        raise RuntimeError("Probe stopped to preserve 10 GiB free-space headroom")


def benchmark(mount, binding, minimum_bytes=GIB, seconds=60.0, maximum_bytes=8 * GIB,
              progress=None):
    """Write one owned sequential file with per-64MiB fsync, then checksum readback.

    Holding the directory fd anchors file creation/cleanup to the verified mount.
    The probe is unlinked only after verifying the same owned inode. The current
    pathname/device binding is also checked before each write batch.
    """
    _check_pinned_mount(mount, binding)
    if binding["free_bytes"] < maximum_bytes + MINIMUM_FREE_BYTES:
        raise RuntimeError("Free space must cover the complete probe budget plus 10 GiB")
    directory_fd = os.open(mount, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    filename = f".wbr-storage-probe-{uuid_module.uuid4().hex}"
    probe_fd = None
    owned_inode = None
    result = {"samples": [], "bytes_written": 0, "probe_file_removed": False}
    try:
        directory_stat = os.fstat(directory_fd)
        if (directory_stat.st_dev, directory_stat.st_ino) != (binding["mount_st_dev"], binding["mount_inode"]):
            raise RuntimeError("Mount identity changed before exclusive probe creation")
        probe_fd = os.open(filename, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                           0o600, dir_fd=directory_fd)
        owned_inode = os.fstat(probe_fd).st_ino
        # Generate outside the timed interval. Every batch uses a random 1 MiB
        # block; its repetitions are disclosed and checksum covers exact writes.
        block = os.urandom(1024 ** 2)
        expected = hashlib.sha256()
        begin = time.monotonic()
        while result["bytes_written"] < maximum_bytes:
            _check_pinned_mount(mount, binding)
            batch_size = min(CHUNK_BYTES, maximum_bytes - result["bytes_written"])
            batch_start = time.monotonic()
            remaining = batch_size
            while remaining:
                payload = memoryview(block)[:min(len(block), remaining)]
                expected.update(payload)
                while payload:
                    count = os.write(probe_fd, payload)
                    if count <= 0:
                        raise RuntimeError("Probe write made no progress")
                    payload = payload[count:]
                remaining -= min(len(block), remaining)
            before_fsync = time.monotonic()
            os.fsync(probe_fd)
            end = time.monotonic()
            result["bytes_written"] += batch_size
            sample = {"bytes": batch_size, "write_and_fsync_seconds": end - batch_start,
                      "fsync_seconds": end - before_fsync,
                      "decimal_MB_per_second": batch_size / (end - batch_start) / 1_000_000,
                      "elapsed_seconds": end - begin}
            result["samples"].append(sample)
            if progress:
                progress(sample)
            if sample["decimal_MB_per_second"] < MINIMUM_MBPS:
                break  # The required margin already failed; avoid needless writes.
            if result["bytes_written"] >= minimum_bytes and end - begin >= seconds:
                break
        result["write_and_fsync_seconds"] = time.monotonic() - begin
        result["expected_sha256"] = expected.hexdigest()
        # This is buffered readback, potentially from cache; no durability claim
        # across power loss or forced cache dropping follows.
        os.lseek(probe_fd, 0, os.SEEK_SET)
        actual = hashlib.sha256()
        read_begin = time.monotonic()
        read_bytes = 0
        while True:
            chunk = os.read(probe_fd, 1024 ** 2)
            if not chunk:
                break
            actual.update(chunk)
            read_bytes += len(chunk)
        result["readback_seconds"] = time.monotonic() - read_begin
        result["readback_bytes"] = read_bytes
        result["readback_sha256"] = actual.hexdigest()
        result["checksum_matches"] = (read_bytes == result["bytes_written"] and
                                       actual.hexdigest() == expected.hexdigest())
        _check_pinned_mount(mount, binding)
    finally:
        if probe_fd is not None:
            os.close(probe_fd)
        try:
            if owned_inode is not None:
                current = os.stat(filename, dir_fd=directory_fd, follow_symlinks=False)
                if stat.S_ISREG(current.st_mode) and current.st_ino == owned_inode:
                    os.unlink(filename, dir_fd=directory_fd)
                    before_sync = time.monotonic()
                    os.fsync(directory_fd)
                    result["cleanup_directory_fsync_seconds"] = time.monotonic() - before_sync
                    result["probe_file_removed"] = True
                else:
                    raise RuntimeError("Probe pathname changed; refusing to remove an unowned file")
        finally:
            os.close(directory_fd)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mount", required=True, type=Path)
    parser.add_argument("--uuid", required=True)
    parser.add_argument("--device", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New directory for small evidence")
    parser.add_argument("--qualify-external-storage", action="store_true")
    parser.add_argument("--bytes", type=int, default=GIB, help="Minimum bytes; default 1 GiB")
    parser.add_argument("--seconds", type=float, default=60.0, help="Minimum write duration; >=60")
    parser.add_argument("--max-bytes", type=int, default=8 * GIB,
                        help="Explicit write budget, default 8 GiB; review cost before increasing")
    args = parser.parse_args()
    if not args.qualify_external_storage:
        parser.error("No benchmark authorization: requires --qualify-external-storage")
    if args.bytes < GIB or not math.isfinite(args.seconds) or args.seconds < 60 or args.max_bytes < args.bytes:
        parser.error("Require minimum 1 GiB, at least 60 seconds, and max-bytes >= bytes")
    if args.max_bytes % CHUNK_BYTES:
        parser.error("max-bytes must be a multiple of 64 MiB")
    args.output.mkdir(exist_ok=False)
    result = {"stage": "STORAGE_QUALIFY", "verdict": "FAIL", "utc_start": utc(),
              'goal': 'Measure external filesystem write/fsync/readback as a prerequisite to short bags',
              'hypothesis': 'Selected external USB storage sustains at least twice the raw IR payload',
              "hostname": socket.gethostname(), "boot_id": read("/proc/sys/kernel/random/boot_id"),
              "argv": sys.argv, "mount": str(args.mount), "uuid": args.uuid,
              "device": str(args.device), "failures": [],
              "criteria": {"minimum_bytes": args.bytes, "minimum_seconds": args.seconds,
                           "maximum_write_bytes": args.max_bytes, "per_batch_bytes": CHUNK_BYTES,
                           "minimum_decimal_MB_per_second": MINIMUM_MBPS},
              "method": "Buffered sequential write; random 1 MiB block repeated; fsync every 64 MiB; SHA-256 readback may use cache",
              "requires_n1_after_storage_qualification": True,
              "limitations": ["Necessary storage prerequisite; live recording must still prove no sensor loss",
                              "No direct-I/O, cache-eviction, power-loss durability or enclosure reliability claim"]}
    try:
        result["provenance"] = provenance()
        before = validate_mount(args.mount, args.uuid, args.device)
        result["mount_binding"] = before
        result["device"] = before["device"]
        result['blkid'] = run(['blkid', before['device']])
        if result['blkid']['returncode'] or f'UUID="{args.uuid}"' not in result['blkid']['stdout']:
            raise RuntimeError('Normal-user blkid UUID cross-check failed')
        for name, argv in [("lsusb.txt", ["lsusb"]), ("usb-tree.txt", ["lsusb", "-t"])]:
            captured = run(argv)
            write_json(args.output / (name + ".command.json"), captured)
            if captured["returncode"]:
                raise RuntimeError("USB topology capture failed")
            (args.output / name).write_text(captured["stdout"])
        result["topology_sha256"] = sha256(args.output / "usb-tree.txt")
        result["camera_usb_vendor_product_present"] = bool(re.search(
            r"\b8086:0b3a\b", (args.output / "lsusb.txt").read_text(), re.IGNORECASE))
        with (args.output / "write-samples.jsonl").open("x") as progress_file:
            def progress(sample):
                progress_file.write(json.dumps(sample, allow_nan=False) + "\n")
                progress_file.flush()
            result["benchmark"] = benchmark(args.mount, before, args.bytes, args.seconds,
                                            args.max_bytes, progress=progress)
        after = validate_mount(args.mount, args.uuid, args.device)
        result["mount_after"] = after
        if before["binding"] != after["binding"] or before["blockdevices"] != after["blockdevices"]:
            raise RuntimeError("Mount or block-device identity changed across the probe")
        data = result["benchmark"]
        result["assessment"] = assess_benchmark(data["samples"], data["bytes_written"],
            data["write_and_fsync_seconds"], data["checksum_matches"], args.bytes, args.seconds)
        result["failures"].extend(result["assessment"]["failures"])
        if not data["probe_file_removed"]:
            result["failures"].append("Probe cleanup did not finalize")
        result["verdict"] = "PASS" if not result["failures"] else "FAIL"
    except (Exception, KeyboardInterrupt) as exc:
        result["failures"].append(f"{type(exc).__name__}: {exc}")
    result["utc_end"] = utc()
    result["evidence_sha256"] = {p.name: sha256(p) for p in args.output.iterdir() if p.is_file()}
    write_json(args.output / "result.json", result)
    print(json.dumps({"stage": result["stage"], "verdict": result["verdict"],
                      "failures": result["failures"], "result": str(args.output / "result.json")}))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
