"""Small shared helpers for the explicit hardware-validation stages."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(path):
    return Path(path).read_text().strip()


def run(argv, timeout=30):
    p = subprocess.run([str(x) for x in argv], capture_output=True, text=True, timeout=timeout)
    return {"argv": [str(x) for x in argv], "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def checked(argv, timeout=30):
    r = run(argv, timeout)
    if r["returncode"]:
        raise RuntimeError(f"Command failed: {r}")
    return r["stdout"].strip()


def write_json(path, data):
    with Path(path).open("x") as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.write("\n")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def evidence_hashes(directory):
    root = Path(directory)
    return {str(p.relative_to(root)): sha256(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not p.is_symlink()}


def verify_evidence(path):
    result = json.loads(Path(path).read_text())
    hashes = result.get('evidence_sha256')
    if not hashes:
        raise RuntimeError('Missing sealed evidence hashes')
    for name, digest in hashes.items():
        evidence = (Path(path).parent / name).resolve(strict=True)
        if not evidence.is_relative_to(Path(path).parent.resolve()) or sha256(evidence) != digest:
            raise RuntimeError('Evidence escaped directory or changed: ' + name)
    return result


def provenance():
    here = Path(__file__).resolve().parent
    bundle = here / "bundle-manifest.json"
    if bundle.exists():
        for name, expected in json.loads(bundle.read_text())['source_sha256'].items():
            if Path(name).name != name or sha256(here / name) != expected:
                raise RuntimeError('Canonical runtime bundle changed: ' + name)
    sources = {p.name: sha256(p) for p in here.iterdir()
               if p.is_file() and p.suffix in (".py", ".cpp", ".yaml", ".csv", ".rules", ".sh")}
    sources['n3_topics.json'] = sha256(here / 'n3_topics.json')
    return {"utc": utc(), "hostname": socket.gethostname(),
            "boot_id": read("/proc/sys/kernel/random/boot_id"),
            "kernel": checked(["uname", "-a"]), "os_release": read("/etc/os-release"),
            "user": checked(["id"]), "source_sha256": sources,
            "canonical_bundle": json.loads(bundle.read_text()) if bundle.exists() else None,
            "runtime_git": run(["git", "-C", here, "rev-parse", "HEAD"]),
            "package_versions": run(["dpkg-query", "-W", "ros-jazzy-librealsense2", "ros-jazzy-realsense2-camera", "ros-jazzy-rosbag2*"])}


def receipt(path, stage, max_age=7200):
    result = json.loads(Path(path).read_text())
    if result.get("stage") != stage or result.get("verdict") != "PASS" or result.get('failures'):
        raise RuntimeError(f"Prerequisite {stage} has no PASS receipt")
    if result.get("hostname") != socket.gethostname() or result.get("boot_id") != read("/proc/sys/kernel/random/boot_id"):
        raise RuntimeError("Prerequisite is from another host or boot")
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(result["utc_end"])).total_seconds()
    if not 0 <= age <= max_age:
        raise RuntimeError("Prerequisite expired or clock moved backward; rerun it")
    verify_evidence(path)
    return result


def camera_guard(available):
    if not available:
        raise RuntimeError("STOP: requires explicit user CAMERA AVAILABLE, then --camera-available")
    if os.geteuid() == 0:
        raise RuntimeError("Run as the normal camera user, never root")


def active_camera_processes():
    names = {"rs-data-collect", "rs-enumerate-devices", "sample_ir", "sample_ir_checked", "camera_metadata",
             "realsense-viewer", "rs-infrared", "rs-motion", "realsense2_camera_node",
             "component_container", "component_container_mt", "rs-record"}
    found = []
    for p in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            args = p.read_bytes().split(b"\0")
            if args and Path(os.fsdecode(args[0])).name in names:
                found.append({"pid": int(p.parent.name), "argv": [os.fsdecode(x) for x in args if x]})
        except (OSError, ValueError):
            continue
    return found
