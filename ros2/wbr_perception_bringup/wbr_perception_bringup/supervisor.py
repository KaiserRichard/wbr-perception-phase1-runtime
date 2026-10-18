"""Own required child process groups, readiness barriers and ordered teardown."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time

from . import __version__
from .planner import Options, Plan, Step, load_config


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def analyze(outdir):
    raw_path = outdir / "run_raw.json"
    raw = json.loads(raw_path.read_text())
    config = json.loads((outdir / "config.json").read_text())
    expected = [s["id"] for s in raw["plan"]["steps"]]
    criteria = []

    def criterion(key, description, measured, threshold, status, source):
        criteria.append(dict(id=key, description=description, measured=measured, unit="policy",
            threshold=threshold, status=status, evidence="run_raw.json", threshold_source=source))

    blocked = raw.get("blocked_reason")
    completed = [e["step"] for e in raw["events"] if e["event"] == "step_complete"]
    criterion("startup", "All ordered startup steps completed", completed, expected,
        "BLOCKED" if blocked else "PASS" if completed == expected else "FAIL",
        "SOURCE-SUPPORTED T27 ordered start and first-message barrier; " + config["readiness_timeout_s"]["source"])
    failures = [e for e in raw["events"] if e["event"] in ("unexpected_exit", "runtime_error")]
    criterion("required_processes", "No required child exited before shutdown", failures, "no unexpected exits/errors",
        "FAIL" if failures else "BLOCKED" if blocked else "PASS", "SOURCE-SUPPORTED T27 fail-closed required-process exit policy")
    started = [e["step"] for e in raw["events"] if e["event"] == "process_start"]
    stopped = [e["step"] for e in raw["events"] if e["event"] == "process_stopped"]
    forced = [e for e in raw["events"] if e["event"] == "kill_required"]
    criterion("teardown", "Started groups stopped in reverse order without SIGKILL", stopped,
        list(reversed(started)), "FAIL" if stopped != list(reversed(started)) or forced else "PASS",
        "SOURCE-SUPPORTED T27 reverse teardown; " + config["shutdown_grace_s"]["source"] + "; " + config["terminate_grace_s"]["source"])
    missing = []
    inventory = raw.get("saved_raw_files", [])
    needed = {"config.json"} | {name + ".log" for name in started}
    if not blocked:
        needed.add("sensor_qos.yaml")
    if "subscriptions_armed" in completed:
        needed.add("armed.json")
    if "first_sensor_messages" in completed:
        needed.add("ready.json")
    if not needed.issubset({item["path"] for item in inventory}):
        missing.append("incomplete saved raw-file inventory")
    for item in inventory:
        path = outdir / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            missing.append(item["path"])
    if not raw.get("ended_utc"):
        missing.append("unfinished run receipt")
    criterion("saved_evidence", "Saved raw files exist and match their final receipt hashes", missing,
        "complete unchanged saved evidence", "BLOCKED" if missing else "PASS",
        "SOURCE-SUPPORTED COMMON.md raw outputs and SHA-256 evidence contract")
    status = "FAIL" if any(c["status"] == "FAIL" for c in criteria) else (
        "BLOCKED" if any(c["status"] == "BLOCKED" for c in criteria) else "PASS")
    files = [raw_path] + [outdir / item["path"] for item in inventory if (outdir / item["path"]).is_file()]
    result = dict(check="perception_stack_orchestration", tool_version=__version__, status=status,
        started_utc=raw["started_utc"], ended_utc=raw["ended_utc"], host=raw["host"], criteria=criteria,
        raw_files=[{"path": str(p.relative_to(outdir)), "sha256": sha256(p)} for p in files],
        notes=["MEASURED process orchestration only. Fixture PASS is not a Pi or perception gate PASS.",
               "Sensor clocks remain ROS header.stamp; readiness host receipts are CLOCK_MONOTONIC, never subtracted.",
               "Run profile validity and lab/rosbag_qual separately; no sensor/recording/performance acceptance is implied."] +
              (["BLOCKED: " + blocked] if blocked else []))
    write_json(outdir / "result.json", result)
    print("criterion                 status")
    for item in criteria:
        print(f"{item['id']:25} {item['status']}")
    print(f"overall                   {status}")
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[status]


def preflight(plan):
    """Read-only checks before starting any publishers or opening a UART."""
    o = plan.options
    root = Path(o.repo_root)
    required = [root / "lab/rosbag_qual/qos_overrides.yaml"]
    if o.orb:
        required += [root / "tools/perception_health/py/sender.py",
                     root / "tools/perception_health/integration/vio_to_pose_events.py"]
    if o.profile:
        required += [root / "tools/eval_pipeline/profile/profile.py"]
    if o.orb_params:
        required.append(Path(o.orb_params))
    for path in required:
        if not path.is_file():
            return f"required file absent: {path}"
    if o.mode == "replay" and not Path(o.bag).is_dir():
        return "bag directory absent"
    if o.health_uart != "none" and not Path(o.health_uart).exists():
        return f"health UART device absent: {o.health_uart}"
    if o.record != "none":
        record = Path(o.record)
        if record.exists() or not record.parent.is_dir():
            return "record needs a NEW directory with an existing parent"
        if record == Path(o.run_dir) or record in Path(o.run_dir).parents or Path(o.run_dir) in record.parents:
            return "record and run_dir must be disjoint"
    if importlib.util.find_spec("rclpy") is None:
        return "rclpy unavailable; source the provisioned ROS 2 Jazzy environment"
    if importlib.util.find_spec("sensor_msgs") is None:
        return "sensor_msgs unavailable; source the provisioned ROS 2 Jazzy environment"
    for step in plan.steps:
        if step.kind == "process" and shutil.which(step.argv[0]) is None:
            return f"required executable absent: {step.argv[0]}"
    if o.mode == "live":
        try:
            from ament_index_python.packages import get_package_share_directory
            c = json.loads((Path(o.run_dir) / "config.json").read_text())
            launch = Path(get_package_share_directory(c["camera_package"])) / "launch" / c["camera_launch"]
            if not launch.is_file():
                return f"camera launch absent: {launch}"
        except (ImportError, LookupError) as exc:
            return f"camera package unavailable: {exc}"
    return None


class Supervisor:
    def __init__(self, plan, config, *, check=preflight):
        self.plan, self.config, self.check = plan, config, check
        self.out = Path(plan.options.run_dir)
        self.children = {}
        self.logs = []
        self.stop_requested = False
        self.raw = dict(started_utc=utc(), ended_utc=None, plan=plan.to_dict(), events=[],
            host={"system": platform.system(), "release": platform.release(),
                  "machine": platform.machine(), "python": platform.python_version()})

    def event(self, event, **fields):
        self.raw["events"].append(dict(event=event, clock_monotonic_ns=time.monotonic_ns(), **fields))
        write_json(self.out / "run_raw.json", self.raw)

    def request_stop(self, signum=None, frame=None):
        self.stop_requested = True

    def check_children(self):
        for name, process in self.children.items():
            code = process.poll()
            if code is not None and self.plan.on_exit(name) == "shutdown_stack":
                self.event("unexpected_exit", step=name, returncode=code)
                raise RuntimeError(f"required process {name} exited ({code})")

    def wait_for(self, filename):
        deadline = time.monotonic() + self.config["readiness_timeout_s"]["value"]
        while not self.stop_requested:
            self.check_children()
            if (self.out / filename).is_file():
                data = json.loads((self.out / filename).read_text())
                if filename == "ready.json" and set(data["first_messages"]) != set(self.config["topics"]):
                    raise ValueError("incomplete readiness receipt")
                return True
            if time.monotonic() >= deadline:
                raise RuntimeError(f"readiness timeout waiting for {filename}")
            time.sleep(self.config["poll_s"]["value"])
        return False

    def start(self, step):
        argv = [str(self.children["orb"].pid) if word == "{orb_pid}" else word for word in step.argv]
        log = (self.out / f"{step.id}.log").open("xb")
        self.logs.append(log)
        child = subprocess.Popen(argv, cwd=self.plan.options.repo_root, stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        self.children[step.id] = child
        self.event("process_start", step=step.id, pid=child.pid, argv=argv)

    @staticmethod
    def group_alive(process):
        process.poll()  # reap the group leader before checking descendants
        try:
            os.killpg(process.pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # A disappearing group can briefly yield EPERM under host sandbox
            # policy. It does not prove that the group is gone. Retry through
            # the normal deadlines, and report failure if absence stays unknown.
            return True

    def stop_children(self):
        for name in self.plan.teardown:
            process = self.children.get(name)
            if process is None:
                continue
            for sig, grace in ((signal.SIGINT, self.config["shutdown_grace_s"]["value"]),
                               (signal.SIGTERM, self.config["terminate_grace_s"]["value"]),
                               (signal.SIGKILL, self.config["terminate_grace_s"]["value"])):
                if not self.group_alive(process):
                    break
                if sig == signal.SIGKILL:
                    self.event("kill_required", step=name)
                self.event("stop_signal", step=name, signal=sig.name)
                try:
                    os.killpg(process.pid, sig)
                except ProcessLookupError:
                    pass
                except PermissionError as exc:
                    self.event("signal_unavailable", step=name, signal=sig.name, message=str(exc))
                deadline = time.monotonic() + grace
                while self.group_alive(process) and time.monotonic() < deadline:
                    time.sleep(self.config["poll_s"]["value"])
            if self.group_alive(process):
                self.event("runtime_error", message=f"process group {name} survived SIGKILL")
            else:
                self.event("process_stopped", step=name, returncode=process.poll())

    def run(self):
        self.out.mkdir(parents=True, exist_ok=False)
        write_json(self.out / "config.json", self.config)
        self.event("begin")
        previous = {sig: signal.signal(sig, self.request_stop) for sig in (signal.SIGINT, signal.SIGTERM)}
        try:
            blocked = self.check(self.plan)
            if blocked:
                self.raw["blocked_reason"] = blocked
            else:
                qos = (Path(self.plan.options.repo_root) / "lab/rosbag_qual/qos_overrides.yaml").read_text()
                topic = self.config["topics"]["imu"]
                if topic + ":" not in qos.splitlines():
                    qos += (f"\n{topic}:\n  reliability: best_effort\n  durability: volatile\n"
                            f"  history: keep_last\n  depth: {self.config['combined_imu_bag_qos_depth']['value']}\n")
                (self.out / "sensor_qos.yaml").write_text(qos)
                for step in self.plan.steps:
                    if self.stop_requested:
                        break
                    self.check_children()
                    if step.kind == "process":
                        self.start(step)
                    elif not self.wait_for("armed.json" if step.id == "subscriptions_armed" else "ready.json"):
                        break
                    self.event("step_complete", step=step.id)
                while not self.stop_requested:
                    self.check_children()
                    time.sleep(self.config["poll_s"]["value"])
                self.event("requested_shutdown")
        except (OSError, ValueError, RuntimeError, KeyError) as exc:
            self.event("runtime_error", message=str(exc))
        finally:
            self.stop_children()
            for log in self.logs:
                log.close()
            self.raw["ended_utc"] = utc()
            # Hash streams rather than loading potentially long runtime logs
            # or ORB traces into memory. The separate bag is qualified elsewhere.
            paths = sorted(p for p in self.out.rglob("*") if p.is_file()
                           and p not in (self.out / "run_raw.json", self.out / "result.json"))
            self.raw["saved_raw_files"] = [{"path": str(p.relative_to(self.out)),
                "sha256": sha256(p)} for p in paths]
            write_json(self.out / "run_raw.json", self.raw)
            for sig, handler in previous.items():
                signal.signal(sig, handler)
        return analyze(self.out)


def plan_from_dict(data):
    return Plan(Options(**data["options"]), tuple(Step(**{**s, "argv": tuple(s["argv"])}) for s in data["steps"]),
                tuple(data["teardown"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan-json")
    group.add_argument("--analyze-only", type=Path)
    parser.add_argument("--config", type=Path)
    try:
        args = parser.parse_args()
        if args.analyze_only:
            return analyze(args.analyze_only)
        return Supervisor(plan_from_dict(json.loads(args.plan_json)), load_config(args.config)).run()
    except SystemExit as exc:
        return 0 if exc.code == 0 else 3
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"perception stack: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
