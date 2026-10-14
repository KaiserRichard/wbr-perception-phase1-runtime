#!/usr/bin/env python3
"""One-Hz Pi health sampler; no camera API and no background worker threads."""
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from validation_common import power_allowed


def command(argv):
    result = subprocess.run(argv, text=True, capture_output=True, timeout=5)
    if result.returncode:
        raise RuntimeError(f"{argv[0]} failed ({result.returncode}): {result.stderr.strip()}")
    return result.stdout.strip()


class HealthSampler:
    """The capture owner calls sample once per second and owns serialization."""

    def __init__(self, output):
        self.output = Path(output)
        self.previous_cpu = None
        self.previous_process = None
        self.tick_hz = os.sysconf("SC_CLK_TCK")
        self.page_bytes = os.sysconf("SC_PAGE_SIZE")

    def sample(self, pid=None):
        now = time.monotonic()
        values = [int(v) for v in Path("/proc/stat").read_text().splitlines()[0].split()[1:9]]
        cpu = (sum(values), values[3] + values[4])
        busy = None
        if self.previous_cpu and cpu[0] > self.previous_cpu[0]:
            busy = 100 * (1 - (cpu[1] - self.previous_cpu[1]) / (cpu[0] - self.previous_cpu[0]))
        self.previous_cpu = cpu
        memory = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
        throttle_text = command(["vcgencmd", "get_throttled"])
        match = re.fullmatch(r"throttled=(0x[0-9a-fA-F]+)", throttle_text)
        if not match:
            raise RuntimeError(f"Cannot interpret throttling flags: {throttle_text}")
        measure_temp = command(["vcgencmd", "measure_temp"])
        temp_match = re.fullmatch(r"temp=([0-9.]+)'C", measure_temp)
        if not temp_match:
            raise RuntimeError(f"Cannot interpret measure_temp: {measure_temp}")
        result = {"utc": datetime.now(timezone.utc).isoformat(), "monotonic_seconds": now,
                  "temperature_c": float(Path("/sys/class/thermal/thermal_zone0/temp").read_text()) / 1000,
                  "vcgencmd_temperature_c": float(temp_match[1]),
                  "throttled_raw": throttle_text, "throttled": match[1], "throttled_value": int(match[1], 16),
                  "memory_available_kib": int(memory["MemAvailable"].split()[0]),
                  "system_cpu_busy_percent": busy, "process_pid": pid,
                  "process_cpu_percent": None, "process_rss_bytes": None,
                  "storage_free_bytes": shutil.disk_usage(self.output).free}
        if pid is not None:
            try:
                # comm can contain spaces and ')'; the last ')' ends the comm field.
                fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
                ticks = int(fields[11]) + int(fields[12])
                result["process_rss_bytes"] = int(fields[21]) * self.page_bytes
                if self.previous_process and self.previous_process[0] == pid:
                    result["process_cpu_percent"] = 100 * (ticks - self.previous_process[1]) / self.tick_hz / (now - self.previous_process[2])
                self.previous_process = (pid, ticks, now)
            except FileNotFoundError:
                result["process_exited_before_sample"] = True
        return result


def failures(sample, diagnostic_latched_power=False):
    errors = []
    if not power_allowed(sample["throttled_value"], diagnostic_latched_power):
        errors.append("Nonzero current or historical Pi power/thermal flags")
    if sample["temperature_c"] >= 80 or sample["vcgencmd_temperature_c"] >= 80:
        errors.append("Pi temperature is at or above conservative 80 C stop threshold")
    if sample["memory_available_kib"] < 256 * 1024:
        errors.append("MemAvailable below 256 MiB guard")
    if sample["storage_free_bytes"] < 256 * 1024**2:
        errors.append("Less than 256 MiB free for metadata/log finalization")
    return errors
