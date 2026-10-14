#!/usr/bin/env python3
"""Read-only, camera-free Pi inventory. Safe to run via `ssh ... python3 -`."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess


def command(argv):
    try:
        p = subprocess.run(argv, text=True, capture_output=True, timeout=30)
        return {"argv": argv, "returncode": p.returncode,
                "stdout": p.stdout, "stderr": p.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": argv, "returncode": None, "error": str(exc)}


def inventory():
    packages = ["ros-jazzy-librealsense2", "ros-jazzy-realsense2-camera",
                "ros-jazzy-realsense2-description", "ros-jazzy-rosbag2",
                "ros-jazzy-rosbag2-storage-mcap", "ros-jazzy-rosbag2-storage-sqlite3",
                "ros-jazzy-ros2bag", "ros-jazzy-rclpy"]
    commands = {
        "utc": ["date", "-u", "--iso-8601=seconds"], "hostname": ["hostname"],
        "identity": ["id"], "os": ["cat", "/etc/os-release"],
        "model": ["cat", "/proc/device-tree/model"], "kernel": ["uname", "-a"],
        "architecture": ["dpkg", "--print-architecture"],
        "links": ["ip", "-brief", "link"], "addresses": ["ip", "-brief", "address"],
        "routes": ["ip", "route"], "routes_ipv6": ["ip", "-6", "route"],
        "time": ["timedatectl", "show", "-p", "NTPSynchronized", "-p", "Timezone"],
        "memory": ["free", "-b"], "root_free": ["df", "-B1", "/"],
        "thermal": ["cat", "/sys/class/thermal/thermal_zone0/temp"],
        "vcgencmd_temperature": ["vcgencmd", "measure_temp"],
        "throttling": ["vcgencmd", "get_throttled"],
        "ssh_service": ["systemctl", "is-active", "ssh"],
        "packages": ["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${db:Status-Status}\n", *packages],
        "candidates": ["apt-cache", "policy", *packages],
        "block_devices": ["lsblk", "-J", "-o", "NAME,TYPE,SIZE,MODEL,SERIAL,TRAN,FSTYPE,UUID,MOUNTPOINTS"],
        "old_mount_resolution": ["findmnt", "-J", "-T", "/mnt/wbr-data"],
        "journal_read_access": ["journalctl", "-k", "-b", "-n", "0", "--no-pager"],
    }
    repo = str(Path.home() / "wbr-perception-phase1-runtime")
    for key, args in {"git_status": ["status", "--short"], "git_branch": ["branch", "--show-current"],
                      "git_head": ["rev-parse", "HEAD"], "git_recent": ["log", "--oneline", "-5"],
                      "git_submodules": ["submodule", "status"],
                      "git_head_patch": ["show", "--format=fuller", "HEAD"]}.items():
        commands[key] = ["git", "-C", repo, *args]
    result = {"scope": "PHASE_A_CAMERA_FREE_INVENTORY", "camera_state": "NOT_ASSESSED",
              "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "ssh_connection": os.environ.get("SSH_CONNECTION"),
              "ros_jazzy_setup_present": Path("/opt/ros/jazzy/setup.bash").is_file(),
              "commands": {key: command(argv) for key, argv in commands.items()}}
    result["permission_file_sha256"] = {}
    for p in [Path("/etc/udev/rules.d/99-wbr-d435i.rules"),
              Path("/usr/local/libexec/wbr-d435i-iio-permissions")]:
        result["permission_file_sha256"][str(p)] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    return result


if __name__ == "__main__":
    print(json.dumps(inventory(), indent=2))
