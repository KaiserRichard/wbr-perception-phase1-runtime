from dataclasses import replace
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from types import ModuleType, SimpleNamespace
from contextlib import redirect_stdout
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
ROOT = PACKAGE.parents[1]
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(ROOT))

from wbr_perception_bringup.planner import Options, boolean, build_plan, load_config
from wbr_perception_bringup.supervisor import Supervisor, analyze, preflight, write_json
from wbr_perception_bringup.health import convert_event, follow
from tools.perception_health.integration.vio_to_pose_events import Converter
from tools.perception_health.py.perception_health import (
    StreamParser, TYPE_PERCEPTION_HEALTH, decode_health_payload, U32_MAX)


def test_config():
    return {**load_config(), **json.loads((HERE / "config.json").read_text())}


def options(**kw):
    return replace(Options(repo_root=str(ROOT), run_dir="/tmp/unused-test-stack", session="fixture-session",
                           orb_executable="/fixture/orb_node"), **kw)


class PlannerTests(unittest.TestCase):
    def test_live_order_and_reverse(self):
        plan = build_plan(options(profile=True, record="/tmp/new-record"))
        self.assertEqual([s.id for s in plan.steps], ["readiness", "subscriptions_armed", "camera",
            "first_sensor_messages", "orb", "health", "record", "profile"])
        self.assertEqual(plan.teardown, ("profile", "record", "health", "orb", "camera", "readiness"))

    def test_replay_excludes_camera_and_clock_policy(self):
        plan = build_plan(options(mode="replay", bag="/bags/accepted"))
        ids = [s.id for s in plan.steps]
        self.assertNotIn("camera", ids)
        self.assertIn("bag", ids)
        self.assertIn("--clock", next(s.argv for s in plan.steps if s.id == "bag"))
        self.assertIn("use_sim_time:=true", next(s.argv for s in plan.steps if s.id == "orb"))
        self.assertIn("use_sim_time:=false", next(s.argv for s in build_plan(options()).steps if s.id == "orb"))

    def test_health_none_and_device(self):
        for device in ("none", "/dev/ttyAMA0"):
            step = next(s for s in build_plan(options(health_uart=device)).steps if s.id == "health")
            self.assertEqual(step.argv[-2:], ("--device", device))

    def test_profile_direct_orb_pid(self):
        plan = build_plan(options(profile=True))
        self.assertEqual(next(s for s in plan.steps if s.id == "orb").argv[0], "/fixture/orb_node")
        self.assertIn("{orb_pid}", next(s for s in plan.steps if s.id == "profile").argv)

    def test_all_required_process_exits_shutdown(self):
        plan = build_plan(options(profile=True, record="/tmp/new-record"))
        for step in plan.steps:
            self.assertEqual(plan.on_exit(step.id), "shutdown_stack" if step.kind == "process" else "continue")

    def test_sensor_only(self):
        plan = build_plan(options(orb=False))
        self.assertEqual(plan.teardown, ("camera", "readiness"))

    def test_invalid_options_and_bool(self):
        for changes in ({"mode": "bad"}, {"mode": "replay"}, {"bag": "/bags/both"},
                        {"orb": False, "profile": True}, {"orb": False, "health_uart": "/dev/a"},
                        {"health_uart": "ttyAMA0"}, {"record": "relative"}, {"orb": "true"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                build_plan(options(**changes))
        self.assertTrue(boolean("true"))
        self.assertFalse(boolean("false"))
        with self.assertRaises(ValueError):
            boolean("yes")

    def test_record_reuses_lab_topics_and_includes_combined_imu(self):
        plan = build_plan(options(record="/tmp/new-record"))
        command = next(s.argv for s in plan.steps if s.id == "record")
        lab = json.loads((ROOT / "lab/rosbag_qual/config.json").read_text())
        for topic in lab["topics"]:
            self.assertIn(topic["name"], command)
        self.assertIn(load_config()["topics"]["imu"], command)


class SupervisorTests(unittest.TestCase):
    def exercise(self, *, exiting=None, mode="live", code=7, blocked=None, no_ready=False, ignore_int=None, send_signal=False):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            out = parent / "run"
            write_json(parent / "behavior.json", {"exit": exiting, "exit_code": code, "no_ready": no_ready, "ignore_int": ignore_int})
            plan = build_plan(options(run_dir=str(out), mode=mode, bag="/fixture/bag" if mode == "replay" else "",
                                      profile=True, record=str(parent / "bag")))
            steps = tuple(replace(s, argv=(sys.executable, str(HERE / "fake_process.py"), str(out), s.id) +
                                 (("{orb_pid}",) if s.id == "profile" else ()))
                          if s.kind == "process" else s for s in plan.steps)
            plan = replace(plan, steps=steps)
            supervisor = Supervisor(plan, test_config(), check=lambda _: blocked)
            errors = []

            def controller():
                deadline = time.monotonic() + test_config()["fixture_timeout_s"]["value"]
                while time.monotonic() < deadline:
                    path = out / "run_raw.json"
                    if path.exists():
                        try:
                            raw = json.loads(path.read_text())
                            if raw.get("ended_utc"):
                                return
                            complete = [e["step"] for e in raw["events"] if e["event"] == "step_complete"]
                            # Wait for the profiler to check its target PID too.
                            if complete == [s.id for s in plan.steps] and (out / "profile_target_pid.txt").exists():
                                if exiting:
                                    (out / "release").touch()
                                elif send_signal:
                                    os.kill(os.getpid(), signal.SIGTERM)
                                else:
                                    supervisor.request_stop()
                                return
                        except (json.JSONDecodeError, OSError):
                            pass
                    time.sleep(test_config()["poll_s"]["value"])
                errors.append("fixture deadline exceeded")
                supervisor.request_stop()

            thread = threading.Thread(target=controller)
            thread.start()
            try:
                with redirect_stdout(io.StringIO()):
                    result_code = supervisor.run()
                    # A forged old verdict must have no effect on analyze-only.
                    (out / "result.json").write_text('{"status":"PASS"}')
                    self.assertEqual(analyze(out), result_code)
                result = json.loads((out / "result.json").read_text())
                raw = json.loads((out / "run_raw.json").read_text())
                if not blocked and not no_ready:
                    orb_pid = next(e["pid"] for e in raw["events"] if e["event"] == "process_start" and e["step"] == "orb")
                    self.assertEqual(int((out / "profile_target_pid.txt").read_text()), orb_pid)
                for item in result["raw_files"]:
                    self.assertEqual(hashlib.sha256((out / item["path"]).read_bytes()).hexdigest(), item["sha256"])
                self.assertEqual(next(c for c in result["criteria"] if c["id"] == "teardown")["status"], "PASS")
                if not blocked:
                    (out / "profile.log").unlink(missing_ok=True)
                    if not no_ready:
                        with redirect_stdout(io.StringIO()):
                            self.assertEqual(analyze(out), 1 if exiting else 2)
                return result_code, result, raw
            finally:
                thread.join(test_config()["fixture_timeout_s"]["value"])
                self.assertFalse(thread.is_alive())
                self.assertFalse(errors)

    def test_pass_and_analyze_roundtrip(self):
        code, result, raw = self.exercise()
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "PASS")
        starts = [e["step"] for e in raw["events"] if e["event"] == "process_start"]
        stops = [e["step"] for e in raw["events"] if e["event"] == "process_stopped"]
        self.assertEqual(stops, starts[::-1])

    def test_each_required_exit_fails_and_tears_down(self):
        for role in ("camera", "readiness", "orb", "health", "record", "profile"):
            with self.subTest(role=role):
                code, result, raw = self.exercise(exiting=role)
                self.assertEqual((code, result["status"]), (1, "FAIL"))
                self.assertTrue(any(e["event"] == "unexpected_exit" and e["step"] == role for e in raw["events"]))

    def test_normal_bag_eof_is_stack_shutdown_not_stale_orb(self):
        code, result, raw = self.exercise(exiting="bag", mode="replay", code=0)
        self.assertEqual(code, 1)
        self.assertNotIn("camera", [e.get("step") for e in raw["events"]])
        self.assertTrue(any(e["event"] == "unexpected_exit" and e["returncode"] == 0 for e in raw["events"]))

    def test_blocked_no_processes(self):
        code, result, raw = self.exercise(blocked="fixture missing ROS dependency")
        self.assertEqual((code, result["status"]), (2, "BLOCKED"))
        self.assertFalse(any(e["event"] == "process_start" for e in raw["events"]))

    def test_readiness_timeout_never_starts_orb(self):
        code, result, raw = self.exercise(no_ready=True)
        self.assertEqual(code, 1)
        self.assertNotIn("orb", [e.get("step") for e in raw["events"] if e["event"] == "process_start"])

    def test_real_preflight_missing_ros(self):
        with patch("wbr_perception_bringup.supervisor.importlib.util.find_spec", return_value=None):
            self.assertIn("rclpy unavailable", preflight(build_plan(options())))

    def test_absent_uart_is_blocked_before_start_or_open(self):
        plan = build_plan(options(health_uart="/dev/wbr-t27-deliberately-absent"))
        self.assertIn("health UART device absent", preflight(plan))

    def test_sigterm_to_supervisor_and_sigint_escalation(self):
        code, result, raw = self.exercise(ignore_int="profile", send_signal=True)
        self.assertEqual(code, 0)
        sent = [e["signal"] for e in raw["events"] if e["event"] == "stop_signal" and e["step"] == "profile"]
        self.assertEqual(sent, ["SIGINT", "SIGTERM"])

    def test_permission_error_does_not_claim_group_gone(self):
        process = SimpleNamespace(pid=1234, poll=lambda: 0)
        with patch("wbr_perception_bringup.supervisor.os.killpg", side_effect=PermissionError):
            self.assertTrue(Supervisor.group_alive(process))
        with patch("wbr_perception_bringup.supervisor.os.killpg", side_effect=ProcessLookupError):
            self.assertFalse(Supervisor.group_alive(process))


class LaunchWiringTests(unittest.TestCase):
    def test_real_launch_file_uses_planner_and_exit_handler(self):
        # Minimal ROS launch API doubles exercise our wiring, not ROS itself.
        class Action:
            def __init__(self, *args, **kwargs):
                self.args, self.kwargs = args, kwargs
        class Configuration:
            def __init__(self, name):
                self.name = name
            def perform(self, context):
                return context[self.name]
        modules = {}
        for name in ("ament_index_python", "ament_index_python.packages", "launch", "launch.actions",
                     "launch.event_handlers", "launch.events", "launch.substitutions"):
            modules[name] = ModuleType(name)
        packages = modules["ament_index_python.packages"]
        packages.get_package_prefix = lambda _: "/installed"
        packages.get_package_share_directory = lambda _: str(PACKAGE)
        packages.PackageNotFoundError = LookupError
        modules["launch"].LaunchDescription = Action
        for name in ("DeclareLaunchArgument", "EmitEvent", "ExecuteProcess", "OpaqueFunction", "RegisterEventHandler"):
            setattr(modules["launch.actions"], name, type(name, (Action,), {}))
        modules["launch.event_handlers"].OnProcessExit = type("OnProcessExit", (Action,), {})
        modules["launch.events"].Shutdown = type("Shutdown", (Action,), {})
        modules["launch.substitutions"].LaunchConfiguration = Configuration
        context = dict(mode="replay", bag="/bags/accepted", orb="true", health_uart="none", record="none",
                       profile="true", repo_root=str(ROOT), run_dir="/tmp/launch-test-stack", orb_params="")
        spec = importlib.util.spec_from_file_location("stack_launch_under_test", PACKAGE / "launch/perception_stack.launch.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(module)
            handler, process = module.launch_stack(context)
            self.assertEqual(type(handler).__name__, "RegisterEventHandler")
            exit_handler = handler.args[0]
            self.assertIs(exit_handler.kwargs["target_action"], process)
            self.assertEqual(type(exit_handler.kwargs["on_exit"][0].kwargs["event"]).__name__, "Shutdown")
            argv = process.kwargs["cmd"]
            plan = json.loads(argv[argv.index("--plan-json") + 1])
            self.assertNotIn("camera", [s["id"] for s in plan["steps"]])
            self.assertEqual(plan["options"]["orb_executable"], "/installed/lib/wbr_orb_node/orb_node")
            self.assertGreater(float(process.kwargs["sigterm_timeout"]),
                               len(plan["teardown"]) * (load_config()["shutdown_grace_s"]["value"] +
                                                        2 * load_config()["terminate_grace_s"]["value"]))


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.events = [json.loads(line) for line in (HERE / "fixtures/real_epoch_pose_events.jsonl").read_text().splitlines()]

    def test_real_saved_epochs_converter_preserves_unknowns(self):
        converter = Converter("fixture-session")
        source_epochs = []
        for event in self.events:
            value = convert_event(event, converter)
            source_epochs.append(value["pose_source_d435i_ns"])
            self.assertFalse(value["mapping"]["valid"])
            self.assertTrue(value["degraded"])
            self.assertFalse(value["imu_initialized"])
            if event["adapter_tracking_state"] == "TRACKING":
                self.assertFalse(value["integration"]["tracking_exact"])
        provenance = json.loads((HERE / "fixtures/provenance.json").read_text())
        self.assertEqual(source_epochs, provenance["source_epochs_ns"])

    def test_regression_session_change_and_malformed_event(self):
        converter = Converter("fixture-session")
        convert_event(self.events[1], converter)
        with self.assertRaises(ValueError):
            convert_event(self.events[0], converter)
        with self.assertRaises(ValueError):
            convert_event({**self.events[2], "source_session": "changed"}, converter)
        with self.assertRaises(KeyError):
            convert_event({}, converter)

    def test_partial_line_follow_and_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            path.write_bytes(b'{"integer":')
            def finish():
                with path.open("ab") as stream:
                    stream.write(b'1791950284553748047}\n')
            thread = threading.Timer(test_config()["poll_s"]["value"], finish)
            thread.start()
            stream = follow(path, test_config()["poll_s"]["value"], load_config()["max_event_bytes"]["value"])
            try:
                self.assertEqual(next(stream), {"integer": 1791950284553748047})
                path.write_bytes(b"")
                with self.assertRaises(ValueError):
                    next(stream)
            finally:
                stream.close()
                thread.join()

    def test_file_mode_emits_real_sender_frames_without_uart(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "orb").mkdir()
            write_json(out / "config.json", test_config())
            (out / "orb/pose_events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in self.events))
            env = dict(os.environ, PYTHONPATH=str(PACKAGE), PYTHONDONTWRITEBYTECODE="1")
            with (out / "health.log").open("wb") as log:
                child = subprocess.Popen([sys.executable, "-m", "wbr_perception_bringup.health", "--repo-root", str(ROOT),
                    "--run-dir", str(out), "--session", "fixture-session", "--device", "none"], env=env,
                    stdout=log, stderr=subprocess.STDOUT)
                try:
                    deadline = time.monotonic() + test_config()["fixture_timeout_s"]["value"]
                    frames = []
                    while time.monotonic() < deadline:
                        path = out / "health_frames.bin"
                        if path.exists():
                            frames = StreamParser().feed(path.read_bytes())
                            if sum(typ == TYPE_PERCEPTION_HEALTH for typ, _, _ in frames) == len(self.events):
                                break
                        if child.poll() is not None:
                            self.fail((out / "health.log").read_text())
                        time.sleep(test_config()["poll_s"]["value"])
                    health = [decode_health_payload(payload) for typ, _, payload in frames if typ == TYPE_PERCEPTION_HEALTH]
                    self.assertEqual(len(health), len(self.events))
                    self.assertTrue(all(h.pose_age_us == U32_MAX and not h.imu_initialized for h in health))
                    child.send_signal(signal.SIGINT)
                    self.assertEqual(child.wait(timeout=test_config()["fixture_timeout_s"]["value"]), 0)
                finally:
                    if child.poll() is None:
                        child.kill()
                        child.wait()


if __name__ == "__main__":
    unittest.main()
