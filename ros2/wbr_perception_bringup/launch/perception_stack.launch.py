"""Headless stack. Child exits propagate through the supervisor to OnProcessExit."""
import json
import os
from pathlib import Path
import sys
import uuid

from ament_index_python.packages import (get_package_prefix, get_package_share_directory,
                                         PackageNotFoundError)
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent, ExecuteProcess,
                            OpaqueFunction, RegisterEventHandler)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration

from wbr_perception_bringup.planner import Options, boolean, build_plan, load_config


def launch_stack(context):
    def value(name):
        return LaunchConfiguration(name).perform(context)
    root = str(Path(value("repo_root")).resolve())
    config_path = Path(get_package_share_directory("wbr_perception_bringup")) / "config/stack.json"
    config = load_config(config_path)
    orb = boolean(value("orb"))
    executable = ""
    if orb:
        try:
            executable = str(Path(get_package_prefix("wbr_orb_node")) / "lib/wbr_orb_node/orb_node")
        except PackageNotFoundError:
            # Let supervisor preserve a BLOCKED receipt instead of failing before
            # an evidence directory exists. No fallback executable is launched.
            executable = str(Path(root) / "install/wbr_orb_node/lib/wbr_orb_node/orb_node")
    options = Options(mode=value("mode"), bag=value("bag"), orb=orb,
        health_uart=value("health_uart"), record=value("record"), profile=boolean(value("profile")),
        repo_root=root, run_dir=value("run_dir"), session="stack-" + uuid.uuid4().hex,
        orb_executable=executable, orb_params=value("orb_params"))
    plan = build_plan(options, config)
    supervisor = ExecuteProcess(cmd=[sys.executable, "-m", "wbr_perception_bringup.supervisor",
        "--plan-json", json.dumps(plan.to_dict()), "--config", str(config_path)],
        name="perception_stack_supervisor", output="screen", cwd=root,
        sigterm_timeout=str(config["launch_shutdown_grace_s"]["value"]),
        sigkill_timeout=str(config["terminate_grace_s"]["value"]))
    # The supervisor detects EVERY required child exit (including code 0),
    # drains remaining groups in reverse order, then exits. This handler also
    # shuts down launch if the supervisor itself crashes. No orphan ORB action
    # lives independently in launch's parallel shutdown machinery.
    handler = RegisterEventHandler(OnProcessExit(target_action=supervisor,
        on_exit=[EmitEvent(event=Shutdown(reason="perception supervisor exited; inspect result.json"))]))
    return [handler, supervisor]


def generate_launch_description():
    defaults = {"mode": "live", "bag": "", "orb": "true", "health_uart": "none",
        "record": "none", "profile": "false", "repo_root": os.environ.get("WBR_ROOT", os.getcwd()),
        "run_dir": "/tmp/wbr-stack-" + uuid.uuid4().hex, "orb_params": ""}
    return LaunchDescription([DeclareLaunchArgument(key, default_value=value)
                              for key, value in defaults.items()] + [OpaqueFunction(function=launch_stack)])
