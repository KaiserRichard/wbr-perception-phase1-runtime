"""Pure Python startup, dependency and shutdown policy; no ROS imports."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import sys


def load_config(path=None):
    if path is None:
        path = Path(__file__).resolve().parents[1] / "config/stack.json"
        if not path.is_file():
            # Installed ament_python layout; avoid importing ament in this module.
            candidates = [Path(prefix) / "share/wbr_perception_bringup/config/stack.json"
                          for prefix in os.environ.get("AMENT_PREFIX_PATH", "").split(os.pathsep) if prefix]
            path = next((p for p in candidates if p.is_file()), path)
    config = json.loads(Path(path).read_text())
    for key, item in config.items():
        if isinstance(item, dict) and "value" in item:
            value = item["value"]
            if type(value) not in (int, float) or not 0 < value < float("inf") or not item.get("source"):
                raise ValueError(f"invalid threshold {key}")
    return config


def boolean(value):
    if type(value) is bool:
        return value
    if value in ("true", "false"):
        return value == "true"
    raise ValueError("boolean arguments must be true or false")


@dataclass(frozen=True)
class Options:
    mode: str = "live"
    bag: str = ""
    orb: bool = True
    health_uart: str = "none"
    record: str = "none"
    profile: bool = False
    repo_root: str = ""
    run_dir: str = ""
    session: str = ""
    orb_executable: str = ""
    orb_params: str = ""


@dataclass(frozen=True)
class Step:
    id: str
    kind: str
    argv: tuple[str, ...] = ()
    required: bool = True


@dataclass(frozen=True)
class Plan:
    options: Options
    steps: tuple[Step, ...]
    teardown: tuple[str, ...]

    def on_exit(self, process_id):
        step = next(step for step in self.steps if step.id == process_id)
        return "shutdown_stack" if step.kind == "process" and step.required else "continue"

    def to_dict(self):
        return asdict(self)


def build_plan(options, config=None):
    c = config if config is not None else load_config()
    o = options
    if o.mode not in ("live", "replay"):
        raise ValueError("mode must be live or replay")
    if type(o.orb) is not bool or type(o.profile) is not bool:
        raise ValueError("normalize boolean arguments before planning")
    if o.mode == "replay" and not o.bag:
        raise ValueError("replay requires bag")
    if o.mode == "live" and o.bag:
        raise ValueError("live cannot also specify bag")
    if not o.orb and (o.profile or o.health_uart != "none"):
        raise ValueError("profile or UART health requires orb=true")
    if o.health_uart != "none" and not o.health_uart.startswith("/dev/"):
        raise ValueError("health_uart must be none or an absolute /dev/ path")
    for name in ("repo_root", "run_dir", "session"):
        if not getattr(o, name):
            raise ValueError(f"{name} is required")
    for name in ("repo_root", "run_dir", "bag", "orb_params", "orb_executable"):
        value = getattr(o, name)
        if value and not Path(value).is_absolute():
            raise ValueError(f"{name} must be absolute")
    if o.record != "none" and (not o.record or not Path(o.record).is_absolute()):
        raise ValueError("record must be none or an absolute NEW bag directory")
    if o.orb and not o.orb_executable:
        raise ValueError("resolved orb executable required")
    root, run = Path(o.repo_root), Path(o.run_dir)
    py = sys.executable
    helper = lambda module: (py, "-m", f"wbr_perception_bringup.{module}")
    # Arm subscriptions before the source, especially for finite replay.
    steps = [Step("readiness", "process", helper("readiness") + ("--run-dir", str(run))),
             Step("subscriptions_armed", "wait")]
    if o.mode == "live":
        source = ("ros2", "launch", c["camera_package"], c["camera_launch"])
        source_id = "camera"
    else:
        source = ("ros2", "bag", "play", o.bag, "--clock", "--qos-profile-overrides-path",
                  str(run / "sensor_qos.yaml"))
        source_id = "bag"
    steps += [Step(source_id, "process", source), Step("first_sensor_messages", "wait")]
    if o.orb:
        args = [o.orb_executable, "--ros-args"]
        if o.orb_params:
            args += ["--params-file", o.orb_params]
        # These overrides bind this session and keep replay clock policy explicit.
        params = {"use_sim_time": o.mode == "replay",
                  "source_domain": "ros_header", "source_session": o.session,
                  "output_directory": str(run / "orb"),
                  "left_topic": c["topics"]["left"], "right_topic": c["topics"]["right"],
                  "imu_topic": c["topics"]["imu"],
                  "source_header_is_d435i_time": False, "clockmap_file": ""}
        for key, value in params.items():
            # JSON scalars are YAML-compatible; retain quotes in argv for empty
            # strings and paths containing spaces (no shell is involved).
            args += ["-p", f"{key}:={json.dumps(value)}"]
        steps.append(Step("orb", "process", tuple(args)))
        steps.append(Step("health", "process", helper("health") + (
            "--repo-root", str(root), "--run-dir", str(run), "--session", o.session,
            "--device", o.health_uart)))
    if o.record != "none":
        # Reuse the lab recorder's topic and QoS contracts, without its bounded
        # qualification runner (which would exit and stop the whole stack).
        record_config = json.loads((root / "lab/rosbag_qual/config.json").read_text())
        topics = list(dict.fromkeys([t["name"] for t in record_config["topics"]] +
                                   list(c["topics"].values())))
        steps.append(Step("record", "process", ("ros2", "bag", "record", "--storage",
            record_config["storage"]["storage_id"], "--output", o.record,
            "--qos-profile-overrides-path", str(run / "sensor_qos.yaml"),
            "--topics", *topics)))
    if o.profile:
        steps.append(Step("profile", "process", (py, str(root / "tools/eval_pipeline/profile/profile.py"),
            "sampler", "--pid", "{orb_pid}", "--out", str(run / "profile"))))
    teardown = tuple(s.id for s in reversed(steps) if s.kind == "process")
    return Plan(o, tuple(steps), teardown)
