#!/usr/bin/env python3
"""Bounded N2 SDK capture after explicit camera availability and fresh N1 PASS.

Writes metadata/IMU CSV and small logs only; no image stream dataset or ROS bag.
Optional 12-second image-content sampling is separate from the SDK interval.
Only this runner's child process groups are signaled. All evidence is additive.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import signal
import socket
import subprocess
import time

from health_monitor import HealthSampler, failures as health_failures
from image_content import analyze as analyze_images
from kernel_analysis import classify
from sdk_analysis import analyze as analyze_csv
from validation_common import evidence_hashes, provenance, verify_evidence

DEVICE_SERIAL = "243322073847"
PROFILE = ("# Stream,width,height,fps,format,index; raw baseline only.\n"
           "INFRARED,640,480,15,Y8,1\nGYRO,1,1,200,MOTION_XYZ32F,0\n"
           "ACCEL,1,1,100,MOTION_XYZ32F,0\n")


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    with Path(path).open("x") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def command(argv, cwd=None):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=15, cwd=cwd)
    return {"argv": argv, "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def require_n1(path, now=None):
    result = json.loads(Path(path).read_text())
    now = now or datetime.now(timezone.utc)
    age = (now - datetime.fromisoformat(result["utc_end"])).total_seconds()
    if result.get("stage") != "N1_PRECHECK" or result.get("verdict") != "PASS" or result.get("failures"):
        raise ValueError("N1 is not PASS")
    verify_evidence(path)
    if not 0 <= age <= 7200:
        raise ValueError("N1 must be current (no older than two hours, no future time)")
    if result.get("hostname") != socket.gethostname():
        raise ValueError("N1 belongs to a different host")
    if result.get("boot_id") != Path("/proc/sys/kernel/random/boot_id").read_text().strip():
        raise ValueError("N1 belongs to a different boot")
    camera = result["camera"]
    if (camera.get("device_serial") != DEVICE_SERIAL or camera.get("asic_serial") != "251843061466"
            or camera.get("firmware_update_id") != "251843061466"
            or camera.get("firmware") != "5.17.3.10" or camera.get("imu_type") != "BMI085"
            or float(camera["speed_mbps"]) < 5000):
        raise ValueError("N1 camera identity/profile context does not match baseline")
    validate_camera(camera)
    return result


def validate_camera(camera):
    path = Path(camera["sysfs_path"]).resolve(strict=True)
    if not path.is_relative_to(Path("/sys/devices")) or path.name != camera["sysfs_name"]:
        raise ValueError("N1 sysfs path is not an expected physical USB device")
    if ((path / "idVendor").read_text().strip() != "8086"
            or (path / "idProduct").read_text().strip() != "0b3a"):
        raise ValueError("Camera USB device identity changed")
    if float((path / "speed").read_text()) < 5000:
        raise ValueError("Camera branch dropped below 5000 Mb/s")
    if any((path / key).read_text().strip() != str(camera[key]) for key in ('busnum', 'devnum')):
        raise ValueError('Camera re-enumerated since N1')
    serial_path = path / "serial"
    serial = serial_path.read_text().strip() if serial_path.exists() else None
    if serial != camera.get("usb_descriptor_serial"):
        raise ValueError("USB descriptor serial observation changed since N1")


def stop_child(process, grace=8):
    """Return cleanup escalation; never target unrelated processes."""
    if process is None or process.poll() is not None:
        return "already_exited"
    for sig, timeout in ((signal.SIGINT, grace), (signal.SIGTERM, 3), (signal.SIGKILL, 3)):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            process.wait()
            return "already_exited"
        try:
            process.wait(timeout=timeout)
            return sig.name
        except subprocess.TimeoutExpired:
            pass
    raise RuntimeError("Owned process did not terminate")


def snapshot(output):
    commands = {"lsusb": ["lsusb"], "usb_tree": ["lsusb", "-t"],
                "storage": ["findmnt", "-J", "-T", str(output)],
                "user": ["id"], "kernel": ["uname", "-a"],
                "packages": ["dpkg-query", "-W", "-f=${Package}\t${Version}\n",
                             "ros-jazzy-librealsense2", "ros-jazzy-rosbag2", "ros-jazzy-realsense2-camera"]}
    return {key: command(argv) for key, argv in commands.items()}


def owners():
    nodes = [str(p) for pattern in ("video*", "hidraw*", "iio:device*") for p in Path("/dev").glob(pattern)]
    if not nodes:
        raise ValueError("No video/HID/IIO nodes exist after N1")
    result = command(["fuser", *nodes])
    if result["returncode"] != 1 or result["stdout"].strip() or result["stderr"].strip():
        raise ValueError("Sensor ownership check failed or sensor already owned: " + json.dumps(result))


def run_capture(args):
    n1 = require_n1(args.n1_result)
    owners()
    if not args.sdk_binary.is_file() or not os.access(args.sdk_binary, os.X_OK):
        raise ValueError("SDK binary missing/not executable")
    if args.image_sampler and (not args.image_sampler.is_file() or not os.access(args.image_sampler, os.X_OK)):
        raise ValueError("Image sampler missing/not executable; compile before hardware session")
    target = args.output.resolve()
    if target.exists():
        raise ValueError("Output directory exists; historical evidence cannot be overwritten")
    target.mkdir(parents=True, exist_ok=False)
    (target / "profile.csv").write_text(PROFILE)
    shutil.copy2(args.n1_result, target / "n1-result.json")
    argv = [str(args.sdk_binary), "--no-eth", "-s", DEVICE_SERIAL,
            "-c", str(target / "profile.csv"), "-t", str(args.seconds), "-f", str(target / "frames.csv")]
    result = {"stage": {20: "N2_SMOKE", 105: "N2_REPRODUCTION", 300: "N2_SOAK"}[args.seconds],
              "verdict": "FAIL", "automatic_checks_pass": False, "utc_start": utc(),
              "duration_requested_seconds": args.seconds, "argv": argv, "shell_command": shlex.join(argv),
              "hostname": socket.gethostname(), "platform": platform.platform(),
              "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
              "n1_sha256": hashlib.sha256(args.n1_result.read_bytes()).hexdigest(), "camera": n1["camera"],
              "failures": [], "review_required": ["Read unfiltered kernel and SDK logs", "Review representative IR images"],
              "N2": "NOT DECIDED: complete 300-second soak and human evidence review required",
              "goal": 'Measure native raw IR1/gyro/accel delivery and shutdown without ROS',
              "hypothesis": 'Direct SuperSpeed transport and scoped access sustain the exact baseline profile',
              "input_source": 'Physical D435i selected by SDK serial; not synthetic',
              "monitor_interval_seconds": 1, "raw_image_dataset_recorded": False}
    write_json(target / "command.json", result)
    collector = follower = None
    log_handles = []
    start = time.monotonic()
    sample_count = 0
    sample_times = []
    sampler = HealthSampler(target)
    offsets = {"kernel-live.log": 0, "sdk.log": 0}
    original_sigterm = signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt("SIGTERM")))
    try:
        result["before"] = snapshot(target)
        result['provenance'] = provenance()
        result['sdk_binary_sha256'] = hashlib.sha256(args.sdk_binary.read_bytes()).hexdigest()
        result['image_sampler_sha256'] = hashlib.sha256(args.image_sampler.read_bytes()).hexdigest() if args.image_sampler else None
        if any(result["before"][name]["returncode"] for name in ("lsusb", "usb_tree", "storage")):
            raise RuntimeError("Before USB/storage snapshot failed")
        result["git_revision"] = command(["git", "rev-parse", "HEAD"], Path(__file__).parent)
        result["git_status"] = command(["git", "status", "--short"], Path(__file__).parent)
        result["os_release"] = Path("/etc/os-release").read_text()
        baseline = command(["journalctl", "-k", "-n", "30", "--no-pager", "-o", "short-iso-precise"])
        write_json(target / "kernel-baseline.json", baseline)
        if baseline["returncode"] or not baseline["stdout"].strip() or baseline["stderr"].strip():
            raise RuntimeError("Cannot establish normal-user kernel journal access")
        kernel = (target / "kernel-live.log").open("x")
        sdk = (target / "sdk.log").open("x")
        health = (target / "health.jsonl").open("x")
        log_handles.extend([kernel, sdk, health])
        follower = subprocess.Popen(["journalctl", "-k", "-f", "-n", "0", "--no-pager", "-o", "short-iso-precise"],
                                    stdout=kernel, stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(.3)

        def monitor(pid=None):
            nonlocal sample_count
            if follower.poll() is not None:
                raise RuntimeError("Continuous kernel monitor exited early")
            validate_camera(n1["camera"])
            sample = sampler.sample(pid)
            sample["capture_elapsed_seconds"] = time.monotonic() - start
            health.write(json.dumps(sample, allow_nan=False) + "\n")
            health.flush()
            sample_count += 1
            sample_times.append(sample["monotonic_seconds"])
            errors = health_failures(sample)
            if errors:
                raise RuntimeError("; ".join(errors))
            for name in offsets:
                path = target / name
                if path.stat().st_size > 64 * 1024**2:
                    raise RuntimeError("Log exceeded 64 MiB bounded-evidence guard")
                with path.open(errors="replace") as handle:
                    handle.seek(offsets[name])
                    findings = classify(handle.read())
                    offsets[name] = handle.tell()
                if findings["faults"]:
                    raise RuntimeError(f"{name}: " + "; ".join(f["text"] for f in findings["faults"]))

        monitor()
        result["sdk_utc_start"] = utc()
        sdk_start = time.monotonic()
        collector = subprocess.Popen(argv, stdout=sdk, stderr=subprocess.STDOUT, start_new_session=True)
        while collector.poll() is None:
            if time.monotonic() - sdk_start > args.seconds + 30:
                raise RuntimeError("SDK exceeded requested duration plus 30-second startup/finalization bound")
            monitor(collector.pid)
            time.sleep(1)
        result["sdk_returncode"] = collector.wait()
        result["sdk_elapsed_seconds"] = time.monotonic() - sdk_start
        result["sdk_utc_end"] = utc()
        monitor()
        if result["sdk_returncode"] != 0:
            raise RuntimeError(f"SDK exited {result['sdk_returncode']}")
        if "Task completed" not in (target / "sdk.log").read_text(errors="replace"):
            raise RuntimeError("SDK log lacks successful orderly completion")
        timing = analyze_csv(target / "frames.csv", args.seconds)
        write_json(target / "timing-analysis.json", timing)
        if not timing["automatic_checks_pass"]:
            raise RuntimeError("Full SDK timing/profile checks failed; inspect timing-analysis.json")
        if timing["setup_boundary_review_required"]:
            result["review_required"].append("Review SDK pre-open timer/start-boundary offsets; no automatic loss exemption")
        if args.image_sampler:
            owners()
            image_argv = [str(args.image_sampler), "--camera-available", DEVICE_SERIAL, str(target / "image-content")]
            image_command = {"argv": image_argv, "utc_start": utc(), "duration_requested_seconds": 12}
            image_log = (target / "image-content.log").open("x")
            log_handles.append(image_log)
            offsets["image-content.log"] = 0
            image_start = time.monotonic()
            collector = subprocess.Popen(image_argv, stdout=image_log, stderr=subprocess.STDOUT, start_new_session=True)
            while collector.poll() is None:
                if time.monotonic() - image_start > 30:
                    raise RuntimeError("Image sampler exceeded 30-second bound")
                monitor(collector.pid)
                time.sleep(1)
            image_command.update(utc_end=utc(), returncode=collector.wait())
            write_json(target / "image-command.json", image_command)
            if image_command["returncode"] != 0:
                raise RuntimeError("Image sampler failed")
            images = analyze_images(target / "image-content")
            write_json(target / "image-analysis.json", images)
            if not images["automatic_checks_pass"]:
                raise RuntimeError("Image metadata/content checks failed")
        else:
            result["review_required"].append("Image sampler omitted; image-content evidence is still missing")
        time.sleep(1)
        monitor()
        result["sdk_orderly_shutdown"] = True
    except (Exception, KeyboardInterrupt) as error:
        result["failures"].append(f"{type(error).__name__}: {error}")
    finally:
        for label, process in (("collector_cleanup", collector), ("kernel_monitor_cleanup", follower)):
            try:
                result[label] = stop_child(process)
            except Exception as error:
                result["failures"].append(f"{label}: {error}")
        for handle in log_handles:
            handle.close()
        signal.signal(signal.SIGTERM, original_sigterm)
        result["utc_end"] = utc()
        result["elapsed_seconds"] = time.monotonic() - start
        result["health_sample_count"] = sample_count
        try:
            result["after"] = snapshot(target)
            validate_camera(n1["camera"])
            if any(result["after"][name]["returncode"] for name in ("lsusb", "usb_tree", "storage")):
                raise RuntimeError("After USB/storage snapshot failed")
        except Exception as error:
            result["failures"].append(f"After snapshot/USB verification: {error}")
        result["log_analysis"] = {name: classify((target / name).read_text(errors="replace"))
                                  for name in offsets if (target / name).exists()}
        if any(report["faults"] for report in result["log_analysis"].values()):
            result["failures"].append("Kernel/SDK/image log classifier found faults; read complete raw logs")
        result["health_coverage_seconds"] = sample_times[-1] - sample_times[0] if len(sample_times) >= 2 else 0
        result["health_max_sampling_gap_seconds"] = max((b - a for a, b in zip(sample_times, sample_times[1:])), default=None)
        if result["health_coverage_seconds"] < args.seconds or (result["health_max_sampling_gap_seconds"] or float("inf")) > 3:
            result["failures"].append("Health monitoring coverage incomplete or sample interval exceeded 3 seconds")
        result["automatic_checks_pass"] = bool(result.get("sdk_orderly_shutdown") and not result["failures"])
        result["verdict"] = "REVIEW_REQUIRED" if result["automatic_checks_pass"] else "FAIL"
        (target / "SUMMARY.md").write_text(f"# {result['stage']}\n\nAutomatic verdict: **{result['verdict']}**.\n\n"
                                            f"Requested raw SDK interval: {args.seconds} seconds. N2 is not decided.\n\n"
                                            "See capture-result.json, timing-analysis.json, health.jsonl and unfiltered logs.\n")
        result['evidence_sha256'] = evidence_hashes(target)
        write_json(target / "capture-result.json", result)
    print(json.dumps({"output": str(target), "verdict": result["verdict"], "failures": result["failures"]}, indent=2))
    return 0 if result["automatic_checks_pass"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera-available", action="store_true")
    parser.add_argument("--n1-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, choices=(20, 105, 300), required=True)
    parser.add_argument("--sdk-binary", type=Path, default=Path("/opt/ros/jazzy/bin/rs-data-collect"))
    parser.add_argument("--image-sampler", type=Path)
    args = parser.parse_args()
    if not args.camera_available:
        parser.error("STOP: requires explicit CAMERA AVAILABLE and --camera-available")
    if platform.system() != "Linux" or os.geteuid() == 0:
        parser.error("Run on the Pi as normal camera user, never as root")
    try:
        return run_capture(args)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        parser.exit(1, f"N2 preflight failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
