#!/usr/bin/env python3
"""Run controlled, profiled one-run EuRoC N4A repetitions on a Pi."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time


VERSION = "1.0.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def value(config: dict, section: str, key: str):
    return config[section][key]["value"]


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_text(command: list[str]) -> str:
    return " ".join(subprocess.list2cmdline([item]) for item in command)


def run_capture(command: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          check=check)


def parse_throttle(text: str) -> tuple[int | None, str]:
    for token in text.replace("\n", " ").split():
        if token.startswith("throttled=0x"):
            try:
                return int(token.split("=", 1)[1], 16), token
            except ValueError:
                break
    return None, text.strip()


def throttle_names(bits: int, invalid_bits: list[int]) -> list[int]:
    return [bit for bit in invalid_bits if bits & (1 << bit)]


def read_temperature(thermal_root: Path) -> tuple[float | None, str]:
    zones = sorted(thermal_root.glob("thermal_zone*/temp"))
    if not zones:
        return None, "UNKNOWN: no thermal_zone*/temp under " + str(thermal_root)
    preferred = next((path for path in zones if path.parent.name == "thermal_zone0"), zones[0])
    try:
        return int(preferred.read_text(encoding="utf-8").strip()) / 1000.0, str(preferred)
    except (OSError, ValueError):
        return None, "UNKNOWN: unreadable " + str(preferred)


def governor_snapshot(governor_root: Path) -> tuple[dict[str, str], str]:
    found: dict[str, str] = {}
    for path in sorted(governor_root.glob("cpu*/cpufreq/scaling_governor")):
        try:
            found[path.parent.parent.name] = path.read_text(encoding="utf-8").strip()
        except OSError:
            found[path.parent.parent.name] = "UNKNOWN"
    return found, ("recorded" if found else "UNKNOWN: no scaling_governor files")


def cooling_snapshot(thermal_root: Path) -> list[dict[str, str]]:
    records = []
    for path in sorted(thermal_root.glob("cooling_device*")):
        def read(name: str) -> str:
            try:
                return (path / name).read_text(encoding="utf-8").strip()
            except OSError:
                return "UNKNOWN"
        records.append({"device": path.name, "type": read("type"), "cur_state": read("cur_state")})
    return records


def write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def process_exe(pid: int) -> str | None:
    try:
        path = Path(f"/proc/{pid}/exe")
        return os.path.realpath(path) if path.exists() else None
    except OSError:
        return None


def parent_pid(pid: int) -> int | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()
        return int(fields[3])
    except (OSError, ValueError, IndexError):
        return None


def descendant_of(pid: int, ancestor: int) -> bool:
    seen: set[int] = set()
    current = pid
    while current and current not in seen and current != 1:
        if current == ancestor:
            return True
        seen.add(current)
        current = parent_pid(current) or 0
    return False


def find_orb_pid(launcher_pid: int, binary: Path) -> int | None:
    target = str(binary.resolve())
    # Test/diagnostic launchers may publish the exact child PID when the host
    # deliberately denies process-list access (for example, a macOS sandbox).
    pid_file = os.environ.get("N4A_ORB_PID_FILE") if not Path("/proc").is_dir() else None
    if pid_file:
        try:
            candidate = int(Path(pid_file).read_text(encoding="utf-8").strip())
            if candidate > 0:
                exact = process_exe(candidate)
                if exact == target or (exact is None and os.kill(candidate, 0) is None):
                    return candidate
        except (OSError, ValueError):
            pass
    proc_root = Path("/proc")
    if proc_root.is_dir():
        for entry in sorted(proc_root.glob("[0-9]*"), key=lambda p: int(p.name)):
            try:
                pid = int(entry.name)
            except ValueError:
                continue
            if pid == os.getpid() or not descendant_of(pid, launcher_pid):
                continue
            if process_exe(pid) == target:
                return pid
    # macOS has no /proc. This fallback is only for local fixture execution;
    # the Pi path above matches the executable inode directly.
    try:
        listing = subprocess.check_output(["ps", "-axo", "pid=,ppid=,command="], text=True)
    except (OSError, subprocess.SubprocessError):
        return None
    rows: dict[int, tuple[int, str]] = {}
    for line in listing.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) != 3:
            continue
        try:
            pid, ppid = int(fields[0]), int(fields[1])
        except ValueError:
            continue
        rows[pid] = (ppid, fields[2])
    for pid, (ppid, command) in rows.items():
        if pid == os.getpid():
            continue
        current = pid
        seen: set[int] = set()
        while current in rows and current not in seen and current != launcher_pid:
            seen.add(current)
            current = rows[current][0]
        if current != launcher_pid:
            continue
        first = command.split(None, 1)[0] if command.split(None, 1) else ""
        if os.path.realpath(first) == target:
            return pid
    return None


def stop_sampler(proc: subprocess.Popen, timeout_s: float) -> int | None:
    if proc.poll() is not None:
        return proc.returncode
    try:
        proc.send_signal(signal.SIGINT)
    except ProcessLookupError:
        return proc.poll()
    try:
        return proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            return proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            return proc.wait()


def try_shared_lock(path: Path) -> tuple[bool, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False, "busy: " + str(path)
        return True, "acquired: " + str(path)
    finally:
        handle.close()


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    p.add_argument("--wait-for-cooldown", action="store_true")
    p.add_argument("--allow-prior-throttle", action="store_true")
    p.add_argument("--require-performance", action="store_true")
    p.add_argument("--preflight-only", action="store_true", help="record preflight and do not launch ORB")
    p.add_argument("--accuracy-runner", type=Path)
    p.add_argument("--profile-tool", type=Path)
    p.add_argument("--thermal-root", type=Path, default=Path("/sys/class/thermal"))
    p.add_argument("--governor-root", type=Path, default=Path("/sys/devices/system/cpu"))
    p.add_argument("--vcgencmd", type=Path, default=Path("vcgencmd"))
    p.add_argument("--lock-file", type=Path)
    p.add_argument("binary", type=Path)
    p.add_argument("vocabulary", type=Path)
    p.add_argument("settings", type=Path)
    p.add_argument("dataset", type=Path)
    p.add_argument("times", type=Path)
    p.add_argument("sequence")
    p.add_argument("runs", type=int)
    p.add_argument("out", type=Path)
    return p


def preflight(args, config: dict, out: Path, lock_file: Path, runner: Path, profile_tool: Path) -> dict:
    preflight_dir = out
    start_temp_limit = float(value(config, "preflight", "start_temperature_c"))
    cooldown_timeout = float(value(config, "preflight", "cooldown_timeout_s"))
    cooldown_period = float(value(config, "preflight", "cooldown_poll_period_s"))
    invalid_bits = list(value(config, "preflight", "invalid_throttle_bits"))
    criteria: list[dict] = []
    notes: list[str] = []

    lock_ok, lock_note = try_shared_lock(lock_file)
    criteria.append({"id": "shared_orb_lock_available", "description": "Accuracy runner shared lock is available",
                     "measured": lock_note, "unit": "lock", "threshold": "available",
                     "status": "PASS" if lock_ok else "FAIL", "evidence": "lock.txt",
                     "threshold_source": "SOURCE-SUPPORTED: tools/eval_pipeline/accuracy/run_euroc.sh shared lock"})
    write_text(preflight_dir / "lock.txt", lock_note)

    temp, temp_source = read_temperature(args.thermal_root)
    wait_started = time.monotonic()
    while temp is not None and temp >= start_temp_limit and args.wait_for_cooldown:
        if time.monotonic() - wait_started >= cooldown_timeout:
            break
        time.sleep(cooldown_period)
        temp, temp_source = read_temperature(args.thermal_root)
    temp_status = ("BLOCKED" if temp is None else
                   ("PASS" if temp < start_temp_limit else "FAIL"))
    criteria.append({"id": "soc_temperature_below_start_limit", "description": "SoC temperature is below the declared start limit",
                     "measured": temp, "unit": "degC", "threshold": f"<{start_temp_limit} degC",
                     "status": temp_status, "evidence": "temperature.txt",
                     "threshold_source": config["preflight"]["start_temperature_c"]["source"]})
    write_text(preflight_dir / "temperature.txt", json.dumps({"temperature_c": temp, "source": temp_source,
                                                                  "limit_c": start_temp_limit,
                                                                  "wait_requested": args.wait_for_cooldown,
                                                                  "wait_timeout_s": cooldown_timeout}) )

    governor, governor_status = governor_snapshot(args.governor_root)
    write_text(preflight_dir / "governor.json", json.dumps(governor, indent=2, sort_keys=True))
    if not governor:
        gov_state = "BLOCKED"
    elif args.require_performance and any(item != "performance" for item in governor.values()):
        gov_state = "FAIL"
    else:
        gov_state = "PASS"
    criteria.append({"id": "cpu_governor_recorded", "description": "CPU governor is recorded and optionally performance",
                     "measured": governor if governor else governor_status, "unit": "governor",
                     "threshold": "recorded; performance when --require-performance is selected",
                     "status": gov_state, "evidence": "governor.json",
                     "threshold_source": "PROPOSED: operator-selected governor requirement; absence is not silently accepted"})

    cooling = cooling_snapshot(args.thermal_root)
    write_text(preflight_dir / "cooling_state.json", json.dumps(cooling, indent=2, sort_keys=True))
    criteria.append({"id": "cooling_state_recorded", "description": "Cooling-device state is recorded",
                     "measured": cooling if cooling else "NONE_FOUND", "unit": "cooling devices",
                     "threshold": "recorded (zero devices is recorded as NONE_FOUND)", "status": "PASS",
                     "evidence": "cooling_state.json",
                     "threshold_source": "SOURCE-SUPPORTED: Linux thermal cooling_device state files"})

    try:
        throttle_proc = run_capture([str(args.vcgencmd), "get_throttled"])
        throttle_output = throttle_proc.stdout
        throttle_rc = throttle_proc.returncode
    except OSError as exc:
        throttle_output = f"{type(exc).__name__}: {exc}"
        throttle_rc = 127
    write_text(preflight_dir / "throttled_before.txt", throttle_output)
    bits, throttle_text = parse_throttle(throttle_output)
    if throttle_rc != 0 or bits is None:
        throttle_status = "BLOCKED"
        measured = throttle_text or f"command exit {throttle_rc}"
    else:
        present = throttle_names(bits, invalid_bits)
        if present and not args.allow_prior_throttle:
            throttle_status = "FAIL"
        else:
            throttle_status = "PASS"
            if present:
                notes.append("Prior throttle bits were allowed by --allow-prior-throttle; affected runs are excluded from VALID aggregation.")
        measured = {"raw": hex(bits), "invalid_bits_set": present}
    criteria.append({"id": "no_prior_throttle_bits", "description": "vcgencmd reports no invalid current or historical bits since boot",
                     "measured": measured, "unit": "vcgencmd bits", "threshold": "no configured invalid bit unless explicitly allowed",
                     "status": throttle_status, "evidence": "throttled_before.txt",
                     "threshold_source": config["preflight"]["invalid_throttle_bits"]["source"]})

    required = [args.binary, args.vocabulary, args.settings, args.dataset, args.times]
    if not args.preflight_only and any(not path.exists() for path in required):
        notes.append("One or more launcher inputs do not exist; the accuracy runner will not be started.")
        criteria.append({"id": "launcher_inputs_present", "description": "EuRoC launcher inputs exist",
                         "measured": [str(path) for path in required if not path.exists()], "unit": "paths",
                         "threshold": "all inputs present", "status": "BLOCKED", "evidence": "provenance.json",
                         "threshold_source": "SOURCE-SUPPORTED: accuracy runner input contract"})

    status = "FAIL" if any(c["status"] == "FAIL" for c in criteria) else (
        "BLOCKED" if any(c["status"] == "BLOCKED" for c in criteria) else "PASS")
    raw_names = ["lock.txt", "temperature.txt", "governor.json", "cooling_state.json", "throttled_before.txt"]
    result = {"check": "n4a_preflight", "tool_version": VERSION, "status": status,
              "started_utc": utc_now(), "ended_utc": utc_now(),
              "host": {"system": platform.system(), "release": platform.release(),
                       "machine": platform.machine(), "python": platform.python_version()},
              "criteria": criteria, "raw_files": [{"path": name, "sha256": sha256(preflight_dir / name)}
                                                   for name in raw_names], "notes": notes,
              "prior_throttle_allowed": bool(args.allow_prior_throttle),
              "prior_throttle_bits": (measured.get("invalid_bits_set", [])
                                      if isinstance(measured, dict) else []),
              "config": {"path": str(args.config.resolve()), "sha256": sha256(args.config)},
              "commands": {"accuracy_runner": str(runner), "profile_tool": str(profile_tool),
                           "vcgencmd": command_text([str(args.vcgencmd), "get_throttled"]),
                           "lock_file": str(lock_file)}}
    write_json(preflight_dir / "preflight.json", result)
    return result


def run_experiment(args, config: dict, out: Path, runner: Path, profile_tool: Path) -> None:
    between_cooldown = float(value(config, "preflight", "between_run_cooldown_s"))
    discovery_timeout = float(value(config, "preflight", "process_discovery_timeout_s"))
    discovery_period = float(value(config, "preflight", "process_discovery_poll_period_s"))
    stop_timeout = float(value(config, "preflight", "sampler_stop_timeout_s"))
    sample_period = float(value(config, "profiling", "sample_period_s"))
    throttle_period = float(value(config, "profiling", "throttle_period_s"))
    for index in range(1, args.runs + 1):
        run_dir = out / f"run{index:02d}"
        run_dir.mkdir()
        accuracy_out = run_dir / "accuracy"
        profile_out = run_dir / "profile"
        runner_cmd = [str(runner), str(args.binary.resolve()), str(args.vocabulary.resolve()),
                      str(args.settings.resolve()), str(args.dataset.resolve()), str(args.times.resolve()),
                      args.sequence, "1", str(accuracy_out)]
        write_json(run_dir / "command.json", {"accuracy_runner": runner_cmd, "profile": [sys.executable,
                   str(profile_tool), "sampler", "--pid", "<orb-pid>", "--out", str(profile_out),
                   "--period-s", sample_period, "--throttle-period-s", throttle_period]})
        started = utc_now()
        with (run_dir / "runner.stdout.log").open("w", encoding="utf-8") as stdout, \
             (run_dir / "runner.stderr.log").open("w", encoding="utf-8") as stderr:
            runner_proc = subprocess.Popen(runner_cmd, stdout=stdout, stderr=stderr, text=True)
            orb_pid = None
            deadline = time.monotonic() + discovery_timeout
            while time.monotonic() < deadline and runner_proc.poll() is None:
                orb_pid = find_orb_pid(runner_proc.pid, args.binary)
                if orb_pid is not None:
                    break
                time.sleep(discovery_period)
            sampler_proc = None
            sampler_rc = None
            if orb_pid is not None:
                sampler_cmd = [sys.executable, str(profile_tool), "sampler", "--pid", str(orb_pid),
                               "--out", str(profile_out), "--period-s", str(sample_period),
                               "--throttle-period-s", str(throttle_period)]
                write_json(run_dir / "sampler_command.json", {"command": sampler_cmd, "orb_pid": orb_pid})
                sampler_proc = subprocess.Popen(sampler_cmd, stdout=(run_dir / "sampler.stdout.log").open("w"),
                                                stderr=(run_dir / "sampler.stderr.log").open("w"), text=True)
            runner_rc = runner_proc.wait()
            if sampler_proc is not None:
                sampler_rc = stop_sampler(sampler_proc, stop_timeout)
            else:
                write_text(run_dir / "sampler_status.txt", "BLOCKED: exact ORB executable was not discovered\n")
        write_json(run_dir / "capture.json", {"started_utc": started, "ended_utc": utc_now(),
                   "runner_exit_code": runner_rc, "sampler_exit_code": sampler_rc, "orb_pid": orb_pid,
                   "status": "CAPTURED" if orb_pid is not None and runner_rc == 0 else "INCOMPLETE"})
        if index < args.runs and between_cooldown > 0:
            time.sleep(between_cooldown)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.runs <= 0:
        print("runs must be positive", file=sys.stderr)
        return 3
    args.config = args.config.resolve()
    config = read_json(args.config)
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[2]
    runner = (args.accuracy_runner or repo_root / "tools/eval_pipeline/accuracy/run_euroc.sh").resolve()
    profile_tool = (args.profile_tool or repo_root / "tools/eval_pipeline/profile/profile.py").resolve()
    lock_file = (args.lock_file or Path(os.environ.get("TMPDIR", "/tmp")) / "wbr-stereo-inertial-euroc.lock").resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        print(f"output directory is not empty: {out}", file=sys.stderr)
        return 3
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "provenance.json", {"tool": "run_n4a_timing", "version": VERSION,
               "started_utc": utc_now(), "argv": sys.argv if argv is None else argv,
               "config": {"path": str(args.config), "sha256": sha256(args.config)},
               "host": {"system": platform.system(), "release": platform.release(),
                        "machine": platform.machine(), "python": platform.python_version()},
               "inputs": {key: str(getattr(args, key).resolve()) for key in
                          ("binary", "vocabulary", "settings", "dataset", "times")},
               "sequence": args.sequence, "runs": args.runs,
               "accuracy_runner": str(runner), "profile_tool": str(profile_tool),
               "lock_file": str(lock_file)})
    (out / "config.json").write_bytes(args.config.read_bytes())
    result = preflight(args, config, out, lock_file, runner, profile_tool)
    if result["status"] != "PASS":
        print(f"preflight={result['status']}; no ORB run started")
        return 1 if result["status"] == "FAIL" else 2
    if args.preflight_only:
        print("preflight=PASS; --preflight-only selected")
        return 0
    run_experiment(args, config, out, runner, profile_tool)
    print(f"completed {args.runs} run(s) in {out}; run analyze_n4a_timing.py next")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
