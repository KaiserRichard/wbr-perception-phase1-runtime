#!/usr/bin/env python3
"""Run controlled, profiled one-run EuRoC N4A repetitions on a Pi."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time


VERSION = "1.1.0"


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(3, f"{self.prog}: {message}\n")


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


def blocked_replay(out: Path, reason: str) -> int:
    out.mkdir(parents=True, exist_ok=True)
    result = {"check": "n4a_preflight", "tool_version": VERSION, "status": "BLOCKED",
              "started_utc": utc_now(), "ended_utc": utc_now(),
              "host": {"system": platform.system(), "machine": platform.machine()},
              "criteria": [{"id": "saved_preflight_inputs", "description": "Saved evidence is available",
                  "measured": None, "unit": "files", "threshold": "saved config and preflight inputs present",
                  "status": "BLOCKED", "evidence": "result.json",
                  "threshold_source": "SOURCE-SUPPORTED: preflight replay input contract"}],
              "raw_files": [], "notes": ["UNKNOWN: " + reason]}
    write_json(out / "result.json", result)
    print("criterion\tstatus\tmeasured\nsaved_preflight_inputs\tBLOCKED\t" + reason)
    return 2


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
        text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        fields = text[text.rindex(")") + 1:].split()
        return int(fields[1])
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
    p = ArgumentParser(description=__doc__)
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


def preflight(args, config: dict, out: Path, lock_file: Path, runner: Path, profile_tool: Path,
              *, replay: bool = False) -> dict:
    started = utc_now()
    def save_text(path, content):
        if not replay:
            write_text(path, content)
    preflight_dir = out
    if not replay:
        (out / "config.json").write_bytes(args.config.read_bytes())
    start_temp_limit = float(value(config, "preflight", "start_temperature_c"))
    cooldown_timeout = float(value(config, "preflight", "cooldown_timeout_s"))
    cooldown_period = float(value(config, "preflight", "cooldown_poll_period_s"))
    invalid_bits = list(value(config, "preflight", "invalid_throttle_bits"))
    criteria: list[dict] = []
    notes: list[str] = []

    if replay:
        lock_note = (out / "lock.txt").read_text().strip() if (out / "lock.txt").is_file() else "UNKNOWN"
        lock_ok = lock_note.startswith("acquired:")
    else:
        lock_ok, lock_note = try_shared_lock(lock_file)
    criteria.append({"id": "shared_orb_lock_available", "description": "Accuracy runner shared lock is available",
                     "measured": lock_note, "unit": "lock", "threshold": "available",
                     "status": "PASS" if lock_ok else "FAIL" if lock_note.startswith("busy:") else "BLOCKED", "evidence": "lock.txt",
                     "threshold_source": "SOURCE-SUPPORTED: tools/eval_pipeline/accuracy/run_euroc.sh shared lock"})
    save_text(preflight_dir / "lock.txt", lock_note)

    if replay:
        saved_temp = read_json(out / "temperature.txt") if (out / "temperature.txt").is_file() else {}
        temp, temp_source = saved_temp.get("temperature_c"), saved_temp.get("source", "UNKNOWN")
    else:
        temp, temp_source = read_temperature(args.thermal_root)
    wait_started = time.monotonic()
    while temp is not None and temp >= start_temp_limit and args.wait_for_cooldown and not replay:
        if time.monotonic() - wait_started >= cooldown_timeout:
            break
        time.sleep(min(cooldown_period, max(0, cooldown_timeout - (time.monotonic() - wait_started))))
        temp, temp_source = read_temperature(args.thermal_root)
    temp_status = ("BLOCKED" if temp is None else
                   ("PASS" if temp < start_temp_limit else "FAIL"))
    criteria.append({"id": "soc_temperature_below_start_limit", "description": "SoC temperature is below the declared start limit",
                     "measured": temp, "unit": "degC", "threshold": f"<{start_temp_limit} degC",
                     "status": temp_status, "evidence": "temperature.txt",
                     "threshold_source": config["preflight"]["start_temperature_c"]["source"]})
    save_text(preflight_dir / "temperature.txt", json.dumps({"temperature_c": temp, "source": temp_source,
                                                                  "limit_c": start_temp_limit,
                                                                  "wait_requested": args.wait_for_cooldown,
                                                                  "wait_timeout_s": cooldown_timeout}) )

    if replay:
        governor = read_json(out / "governor.json") if (out / "governor.json").is_file() else {}
        governor_status = "UNKNOWN: no saved governor snapshot"
    else:
        governor, governor_status = governor_snapshot(args.governor_root)
    save_text(preflight_dir / "governor.json", json.dumps(governor, indent=2, sort_keys=True))
    if not governor or any(item in ("", "UNKNOWN") for item in governor.values()):
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

    cooling = ((read_json(out / "cooling_state.json") if (out / "cooling_state.json").is_file() else None)
               if replay else cooling_snapshot(args.thermal_root))
    save_text(preflight_dir / "cooling_state.json", json.dumps(cooling, indent=2, sort_keys=True))
    criteria.append({"id": "cooling_state_recorded", "description": "Cooling-device state is recorded",
                     "measured": cooling if cooling else "NONE_FOUND", "unit": "cooling devices",
                     "threshold": "recorded (zero devices is recorded as NONE_FOUND)",
                     "status": "BLOCKED" if cooling is None or any(
                         item.get("type") == "UNKNOWN" or item.get("cur_state") == "UNKNOWN" for item in cooling) else "PASS",
                     "evidence": "cooling_state.json",
                     "threshold_source": "SOURCE-SUPPORTED: Linux thermal cooling_device state files"})

    try:
        if replay:
            throttle_output = (out / "throttled_before.txt").read_text() if (out / "throttled_before.txt").is_file() else "UNKNOWN"
            throttle_rc = read_json(out / "preflight_inputs.json").get("throttle_exit_code", 127)
        else:
            throttle_proc = run_capture([str(args.vcgencmd), "get_throttled"])
            throttle_output = throttle_proc.stdout
            throttle_rc = throttle_proc.returncode
    except OSError as exc:
        throttle_output = f"{type(exc).__name__}: {exc}"
        throttle_rc = 127
    if not replay:
        (preflight_dir / "throttled_before.txt").write_text(throttle_output, encoding="utf-8")
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
    if replay:
        missing = read_json(out / "preflight_inputs.json").get("missing_inputs", [])
    else:
        missing = [str(path) for path in required if not path.exists()]
        missing += [str(path) for path in (runner, profile_tool) if not path.is_file()]
        if args.binary.exists() and not os.access(args.binary, os.X_OK):
            missing.append(str(args.binary) + " (not executable)")
        write_json(out / "preflight_inputs.json", {"missing_inputs": missing, "throttle_exit_code": throttle_rc,
                   "require_performance": args.require_performance, "allow_prior_throttle": args.allow_prior_throttle,
                   "preflight_only": args.preflight_only})
    if not args.preflight_only and missing:
        notes.append("One or more launcher inputs do not exist; the accuracy runner will not be started.")
        criteria.append({"id": "launcher_inputs_present", "description": "EuRoC launcher inputs exist",
                         "measured": missing, "unit": "paths",
                         "threshold": "all inputs present", "status": "BLOCKED", "evidence": "preflight_inputs.json",
                         "threshold_source": "SOURCE-SUPPORTED: accuracy runner input contract"})

    status = "FAIL" if any(c["status"] == "FAIL" for c in criteria) else (
        "BLOCKED" if any(c["status"] == "BLOCKED" for c in criteria) else "PASS")
    raw_names = ["lock.txt", "temperature.txt", "governor.json", "cooling_state.json", "throttled_before.txt", "preflight_inputs.json"]
    result = {"check": "n4a_preflight", "tool_version": VERSION, "status": status,
              "started_utc": started, "ended_utc": utc_now(),
              "host": {"system": platform.system(), "release": platform.release(),
                       "machine": platform.machine(), "python": platform.python_version()},
              "criteria": criteria, "raw_files": [{"path": name, "sha256": sha256(preflight_dir / name)}
                                                   for name in raw_names if (preflight_dir / name).is_file()], "notes": notes,
              "prior_throttle_allowed": bool(args.allow_prior_throttle),
              "prior_throttle_bits": (measured.get("invalid_bits_set", [])
                                      if isinstance(measured, dict) else []),
              "config": {"path": str(args.config.resolve()), "sha256": sha256(args.config)},
              "commands": {"accuracy_runner": str(runner), "profile_tool": str(profile_tool),
                           "vcgencmd": command_text([str(args.vcgencmd), "get_throttled"]),
                           "lock_file": str(lock_file)}}
    write_json(preflight_dir / "preflight.json", result)
    write_json(preflight_dir / "result.json", result)
    print("criterion\tstatus\tmeasured")
    for criterion in criteria:
        print(f"{criterion['id']}\t{criterion['status']}\t{criterion['measured']}")
    return result


def run_experiment(args, config: dict, out: Path, runner: Path, profile_tool: Path) -> str:
    statuses = []
    between_cooldown = float(value(config, "preflight", "between_run_cooldown_s"))
    discovery_timeout = float(value(config, "preflight", "process_discovery_timeout_s"))
    discovery_period = float(value(config, "preflight", "process_discovery_poll_period_s"))
    stop_timeout = float(value(config, "preflight", "sampler_stop_timeout_s"))
    sample_period = float(value(config, "profiling", "sample_period_s"))
    throttle_period = float(value(config, "profiling", "throttle_period_s"))
    for index in range(1, args.runs + 1):
        run_dir = out / f"run{index:02d}"
        run_dir.mkdir()
        if index > 1:
            start_dir = run_dir / "start_preflight"
            start_dir.mkdir()
            result = preflight(args, config, start_dir, Path(args.lock_file), runner, profile_tool)
            if result["status"] != "PASS":
                write_json(run_dir / "capture.json", {"status": "INCOMPLETE", "check_status": result["status"],
                           "reason": "inter_run_preflight_refused"})
                return "FAIL" if "FAIL" in statuses else result["status"]
        accuracy_out = run_dir / "accuracy"
        profile_out = run_dir / "profile"
        runner_cmd = ["bash", str(runner), str(args.binary.resolve()), str(args.vocabulary.resolve()),
                      str(args.settings.resolve()), str(args.dataset.resolve()), str(args.times.resolve()),
                      args.sequence, "1", str(accuracy_out)]
        write_json(run_dir / "command.json", {"accuracy_runner": runner_cmd, "profile": [sys.executable,
                   str(profile_tool), "sampler", "--pid", "<orb-pid>", "--out", str(profile_out),
                   "--period-s", sample_period, "--throttle-period-s", throttle_period]})
        started = utc_now()
        with ExitStack() as stack:
            stdout = stack.enter_context((run_dir / "runner.stdout.log").open("w", encoding="utf-8"))
            stderr = stack.enter_context((run_dir / "runner.stderr.log").open("w", encoding="utf-8"))
            runner_proc = subprocess.Popen(runner_cmd, stdout=stdout, stderr=stderr, text=True, start_new_session=True)
            def clean_runner():
                if runner_proc.poll() is None:
                    os.killpg(runner_proc.pid, signal.SIGTERM)
                    try:
                        runner_proc.wait(timeout=stop_timeout)
                    except subprocess.TimeoutExpired:
                        os.killpg(runner_proc.pid, signal.SIGKILL)
                        runner_proc.wait()
            stack.callback(clean_runner)
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
                sample_stdout = stack.enter_context((run_dir / "sampler.stdout.log").open("w"))
                sample_stderr = stack.enter_context((run_dir / "sampler.stderr.log").open("w"))
                sampler_proc = subprocess.Popen(sampler_cmd, stdout=sample_stdout, stderr=sample_stderr, text=True)
                stack.callback(stop_sampler, sampler_proc, stop_timeout)
            runner_rc = runner_proc.wait()
            if sampler_proc is not None:
                sampler_rc = stop_sampler(sampler_proc, stop_timeout)
            else:
                write_text(run_dir / "sampler_status.txt", "BLOCKED: exact ORB executable was not discovered\n")
        try:
            engine_rc = int((accuracy_out / "run01/exit_code.txt").read_text().strip())
        except (OSError, ValueError):
            engine_rc = None
        try:
            sampler_count = read_json(profile_out / "metadata.json").get("sample_count")
        except (OSError, ValueError, AttributeError):
            sampler_count = None
        status = ("FAIL" if engine_rc not in (0, None) else "BLOCKED" if
                  runner_rc != 0 or engine_rc is None or orb_pid is None or sampler_rc != 0 or
                  not (profile_out / "samples.csv").is_file() or
                  not isinstance(sampler_count, int) or sampler_count <= 0
                  else "PASS")
        statuses.append(status)
        write_json(run_dir / "capture.json", {"started_utc": started, "ended_utc": utc_now(),
                   "runner_exit_code": runner_rc, "sampler_exit_code": sampler_rc, "orb_pid": orb_pid,
                   "engine_exit_code": engine_rc, "check_status": status,
                   "status": "CAPTURED" if status == "PASS" else "INCOMPLETE"})
        if index < args.runs and between_cooldown > 0:
            time.sleep(between_cooldown)
    return "FAIL" if "FAIL" in statuses else "BLOCKED" if "BLOCKED" in statuses else "PASS"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if any(arg == "--analyze-only" or arg.startswith("--analyze-only=") for arg in argv):
        replay_parser = ArgumentParser(description="Re-evaluate saved preflight snapshots without hardware")
        replay_parser.add_argument("--analyze-only", type=Path, required=True)
        saved = replay_parser.parse_args(argv).analyze_only.resolve()
        if not saved.is_dir():
            return blocked_replay(saved, "saved preflight directory is absent")
        config_path = saved / "config.json"
        if not config_path.is_file() or not (saved / "preflight_inputs.json").is_file():
            return blocked_replay(saved, "saved config or preflight inputs are absent")
        flags = read_json(saved / "preflight_inputs.json")
        replay_args = argparse.Namespace(config=config_path, wait_for_cooldown=False,
            require_performance=flags.get("require_performance", False),
            allow_prior_throttle=flags.get("allow_prior_throttle", False),
            preflight_only=flags.get("preflight_only", False),
            binary=Path("UNKNOWN"), vocabulary=Path("UNKNOWN"), settings=Path("UNKNOWN"),
            dataset=Path("UNKNOWN"), times=Path("UNKNOWN"), vcgencmd=Path("vcgencmd"))
        result = preflight(replay_args, read_json(config_path), saved, Path("UNKNOWN"),
                           Path("UNKNOWN"), Path("UNKNOWN"), replay=True)
        return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[result["status"]]
    args = parser().parse_args(argv)
    if args.runs <= 0:
        print("runs must be positive", file=sys.stderr)
        return 3
    args.config = args.config.resolve()
    config = read_json(args.config)
    for section in ("preflight", "profiling"):
        for name, setting in config[section].items():
            if name.endswith("_s") or name.endswith("_c"):
                number = float(setting["value"])
                if not math.isfinite(number) or number < 0 or (number == 0 and name != "between_run_cooldown_s"):
                    raise ValueError(f"invalid {section}.{name}")
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[2]
    runner = (args.accuracy_runner or repo_root / "tools/eval_pipeline/accuracy/run_euroc.sh").resolve()
    profile_tool = (args.profile_tool or repo_root / "tools/eval_pipeline/profile/profile.py").resolve()
    lock_file = (args.lock_file or Path(os.environ.get("TMPDIR") or "/tmp") / "wbr-stereo-inertial-euroc.lock").resolve()
    if not args.preflight_only and args.accuracy_runner is None and args.lock_file is not None and lock_file != (
            Path(os.environ.get("TMPDIR") or "/tmp") / "wbr-stereo-inertial-euroc.lock").resolve():
        raise ValueError("--lock-file must match the reviewed runner's TMPDIR shared lock")
    args.lock_file = lock_file
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
    status = run_experiment(args, config, out, runner, profile_tool)
    result["check"] = "n4a_timing_capture"
    result["status"] = status
    result["ended_utc"] = utc_now()
    for receipt in sorted(out.glob("run[0-9]*/capture.json")):
        capture = read_json(receipt)
        result["criteria"].append({"id": receipt.parent.name, "description": "Engine and sampler capture completed",
            "measured": capture, "unit": "run", "threshold": "engine exit 0 and sampler capture complete",
            "status": capture["check_status"], "evidence": str(receipt.relative_to(out)),
            "threshold_source": "PROPOSED: T15 requires profiler evidence for each engine run"})
    result["raw_files"] = [{"path": str(path.relative_to(out)), "sha256": sha256(path)}
                           for path in sorted(out.rglob("*")) if path.is_file()
                           and path.name not in ("result.json", "preflight.json")]
    write_json(out / "result.json", result)
    print("run\tstatus")
    for criterion in result["criteria"]:
        print(f"{criterion['id']}\t{criterion['status']}")
    print(f"capture={status} in {out}; run analyze_n4a_timing.py next")
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[status]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, KeyboardInterrupt) as exc:
        print(f"run_n4a_timing: {exc}", file=sys.stderr)
        raise SystemExit(3)
