#!/usr/bin/env python3
"""N1 physical gate. Never run before the user explicitly says CAMERA AVAILABLE."""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import time

from validation_common import (ACTIVE_UNIT, EXPECTED_CAMERA, active_camera_processes, camera_guard, checked,
                               power_allowed, power_mode, power_verdict, throttled_value,
                               provenance, read, run, sha256, utc, write_json)

EXPECTED = {k: v for k, v in EXPECTED_CAMERA.items() if k != 'usb_descriptor_serial'}


def evaluate_usb(camera, direct_confirmed):
    failures = []
    if camera["idVendor"].lower() != "8086" or camera["idProduct"].lower() != "0b3a":
        failures.append("Unexpected USB VID/PID")
    if not math.isfinite(float(camera["speed_mbps"])) or float(camera["speed_mbps"]) < 5000:
        failures.append("Camera OWN USB branch below 5000M; STOP, restore direct SuperSpeed path")
    if not re.fullmatch(r"\d+-\d+", camera["sysfs_name"]) or not direct_confirmed:
        failures.append("Direct known-good cable/root-port topology not established")
    # Descriptor identity is a separate transport observation, never substituted for SDK serial.
    if camera.get("usb_descriptor_serial") not in (None, ACTIVE_UNIT['usb_descriptor_serial']):
        failures.append("Unexpected USB descriptor serial")
    return failures


def parse_enumeration(text):
    labels = {"Serial Number": "device_serial", "Asic Serial Number": "asic_serial",
              "Firmware Update Id": "firmware_update_id", "Firmware Version": "firmware",
              "Imu Type": "imu_type", "Usb Type Descriptor": "sdk_usb_type_descriptor"}
    result = {}
    for line in text.splitlines():
        match = re.match(r"^\s*([^:]+?)\s*:\s*(.*?)\s*$", line)
        if match and match[1] in labels:
            key = labels[match[1]]
            if key in result:
                raise ValueError("Multiple SDK devices/duplicate identity fields; ambiguous selection")
            result[key] = match[2]
    return result


def supported_profiles(text):
    patterns = [r"Infrared 1\s+640x480\s+Y8\s+@\s+([\d/]+) Hz",
                r"Gyro\s+MOTION_XYZ32F\s+@\s+([\d/]+) Hz",
                r"Accel\s+MOTION_XYZ32F\s+@\s+([\d/]+) Hz"]
    return all((m := re.search(pattern, text)) and str(hz) in m[1].split("/")
               for pattern, hz in zip(patterns, [15, 200, 100]))


def usb_snapshot():
    cameras = []
    for p in Path("/sys/bus/usb/devices").iterdir():
        if (p / "idVendor").is_file() and read(p / "idVendor").lower() == "8086" and read(p / "idProduct").lower() == "0b3a":
            cameras.append({"sysfs_path": str(p.resolve()), "sysfs_name": p.name,
                            "speed_mbps": float(read(p / "speed")),
                            "usb_descriptor_serial": read(p / "serial") if (p / "serial").exists() else None,
                            **{k: read(p / k) for k in ("idVendor", "idProduct", "busnum", "devnum", "product")}})
    if len(cameras) != 1:
        raise RuntimeError(f"Expected one D435i USB device; found {len(cameras)}")
    return cameras[0]


def permissions(camera):
    root = Path(camera["sysfs_path"])
    rows, groups = [], {}
    for group, cls, pattern in [("video", "video4linux", "video*"), ("hidraw", "hidraw", "hidraw*"),
                                ("iio", "iio", "iio:device*")]:
        base = Path("/sys/bus/iio/devices") if group == "iio" else Path("/sys/class") / cls
        members = [p for p in base.glob(pattern) if p.resolve().is_relative_to(root)]
        groups[group] = len(members)
        for p in members:
            node = Path("/dev") / p.name
            rows.append(access_row(node))
    helper_path = Path(__file__).with_name("wbr-d435i-iio-permissions.py")
    spec = importlib.util.spec_from_file_location("camera_permissions", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    iio = [p for p in Path("/sys/bus/iio/devices").glob("iio:device*") if p.resolve().is_relative_to(root)]
    custom = [p for p in root.rglob("HID-SENSOR-2000e1.*") if p.is_dir() and (p / "enable_sensor").exists()]
    groups["custom_hid"] = len(custom)
    for p in iio + custom:
        controls = helper.controls(p)
        if not controls:
            raise RuntimeError("Missing IIO/HID control inventory: " + str(p))
        rows.extend(access_row(c) for c in controls)
    busnode = Path(f"/dev/bus/usb/{int(camera['busnum']):03d}/{int(camera['devnum']):03d}")
    rows.append(access_row(busnode))
    return {"groups": groups, "paths": rows,
            "pass": groups["video"] >= 1 and groups["hidraw"] >= 1 and groups["iio"] == 2 and groups["custom_hid"] >= 1
                    and all(p["readable"] and p["writable"] for p in rows)}


def access_row(path):
    stat = path.stat()
    return {"path": str(path), "mode": oct(stat.st_mode & 0o777), "uid": stat.st_uid, "gid": stat.st_gid,
            "readable": os.access(path, os.R_OK, effective_ids=True),
            "writable": os.access(path, os.W_OK, effective_ids=True)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--camera-available", action="store_true")
    parser.add_argument("--diagnostic-latched-power", action="store_true",
                        help="Allow only latched bits 16-19; results remain OPEN_DIAGNOSTIC")
    parser.add_argument("--direct-cable-confirmed", action="store_true",
                        help="Physical attestation: known-good A-C SuperSpeed cable directly into blue Pi port")
    args = parser.parse_args()
    camera_guard(args.camera_available)
    args.output.mkdir(parents=True, exist_ok=False)
    result = {"stage": "N1_PRECHECK", "verdict": "FAIL", "utc_start": utc(), "failures": [],
              "power_mode": power_mode(args.diagnostic_latched_power), "throttled_raw": None}
    try:
        result.update(provenance())
        result['throttled_raw'] = checked(['vcgencmd', 'get_throttled'])
        result["n0"] = {"architecture": checked(["dpkg", "--print-architecture"]),
                        "ntp": checked(["timedatectl", "show", "-p", "NTPSynchronized", "--value"]),
                        "temperature_c": float(read("/sys/class/thermal/thermal_zone0/temp")) / 1000,
                        "throttling": result['throttled_raw'],
                        "mem_available_kib": int(re.search(r"MemAvailable:\s+(\d+)", read("/proc/meminfo"))[1])}
        n0 = result["n0"]
        result['throttled_raw'] = n0['throttling']
        result['throttled_value'] = throttled_value(n0['throttling'])
        if n0["architecture"] != "arm64" or 'VERSION_ID="24.04"' not in result["os_release"] or n0["ntp"] != "yes":
            raise RuntimeError("N0 OS/architecture/time prerequisites failed")
        if (n0["temperature_c"] >= 75 or not power_allowed(result['throttled_value'], args.diagnostic_latched_power)
                or (not args.diagnostic_latched_power and n0['throttling'] != 'throttled=0x0')
                or n0["mem_available_kib"] < 524288):
            raise RuntimeError("N0 thermal/power/memory prerequisite failed; investigate, do not clear history silently")
        if not Path("/opt/ros/jazzy/setup.bash").is_file():
            raise RuntimeError("N0 Jazzy setup missing")
        for name, cmd in {"lsusb-before.txt": ["lsusb"], "usb-tree-before.txt": ["lsusb", "-t"],
                          "kernel-baseline.txt": ["journalctl", "-k", "-b", "--no-pager", "-o", "short-iso-precise"]}.items():
            (args.output / name).write_text(checked(cmd) + "\n")
        camera = result["camera"] = usb_snapshot()
        result["active_camera_processes"] = active_camera_processes()
        # Preserve read-only node modes even on a bad transport path. Never repair it here.
        result["device_node_inventory"] = [access_row(p) for pattern in ('video*', 'hidraw*', 'iio:device*')
                                           for p in Path('/dev').glob(pattern)]
        result["failures"].extend(evaluate_usb(camera, args.direct_cable_confirmed))
        if result["failures"]:
            raise RuntimeError("N1 USB gate failed; no SDK enumeration or access repair attempted")
        result["active_camera_processes"] = active_camera_processes()
        if result["active_camera_processes"]:
            raise RuntimeError("Existing camera process; stop it explicitly before this gate")
        result["permissions"] = permissions(camera)
        if not result["permissions"]["pass"]:
            raise RuntimeError("Normal-user video/HID/IIO/control permissions failed; no broad repair")
        device_nodes = [p["path"] for p in result["permissions"]["paths"] if p["path"].startswith("/dev/")]
        result["device_owners"] = run(["fuser", *device_nodes])
        if result["device_owners"]["returncode"] != 1 or result["device_owners"]["stderr"].strip():
            raise RuntimeError("Device owner check found a user or could not establish idle state")
        enumeration = run(["/opt/ros/jazzy/bin/rs-enumerate-devices"], timeout=30)
        write_json(args.output / "sdk-enumeration.json", enumeration)
        if enumeration["returncode"]:
            raise RuntimeError("Normal-user SDK enumeration failed")
        identity = parse_enumeration(enumeration["stdout"])
        camera.update(identity)
        if any(identity.get(k) != v for k, v in EXPECTED.items()):
            raise RuntimeError("SDK identity/firmware/IMU mismatch; inspect separate fields")
        if not supported_profiles(enumeration["stdout"]):
            raise RuntimeError("Required raw profiles unavailable")
        time.sleep(3)
        result["camera_after"] = usb_snapshot()
        if any(result["camera_after"].get(k) != camera.get(k) for k in result["camera_after"]):
            raise RuntimeError("USB topology/identity/speed changed during N1")
        (args.output / "usb-tree-after.txt").write_text(checked(["lsusb", "-t"]) + "\n")
        kernel = checked(["journalctl", "-k", "-b", "--since", result["utc_start"], "--no-pager", "-o", "short-iso-precise"])
        (args.output / "kernel-interval.log").write_text(kernel + "\n")
        if re.search(r"USB disconnect|reset .*USB device|new .*USB device|xhci.*(?:error|fail)|under.?voltage|uvc.*(?:error|fail)", kernel, re.I):
            raise RuntimeError("Kernel interval contains transport/power faults; inspect raw log")
        result["verdict"] = power_verdict("PASS", args.diagnostic_latched_power)
        result["scope"] = "N1 identity/access/idle stability only; no N2 streaming or VIO verdict"
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        result["failures"].append(str(exc))
    finally:
        result["utc_end"] = utc()
        result["evidence_sha256"] = {p.name: sha256(p) for p in args.output.iterdir() if p.is_file()}
        write_json(args.output / "result.json", result)
    print(json.dumps({"verdict": result["verdict"], "failures": result["failures"], "output": str(args.output)}))
    return 0 if result["verdict"] in ("PASS", "OPEN_DIAGNOSTIC") else 1


if __name__ == "__main__":
    raise SystemExit(main())
