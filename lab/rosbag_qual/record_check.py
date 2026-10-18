#!/usr/bin/env python3
"""Record a bounded explicit-topic rosbag2 session from a live ROS camera."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from bag_core import analyze_database, storage_files
from qual_common import (base_result, command_text, criterion, file_record,
                         finalize_result, load_config, run_command, utc, write_json)


def _qos_path(config_path: Path, config: dict) -> Path:
    configured = Path(config["qos_overrides_file"])
    if not configured.is_absolute():
        configured = config_path.parent / configured
    return configured


def _stop(process: subprocess.Popen[bytes], grace: float) -> str:
    if process.poll() is not None:
        return "already_exited"
    try:
        os.killpg(process.pid, signal.SIGINT)
        process.wait(timeout=grace)
        return "SIGINT"
    except ProcessLookupError:
        return "already_exited"
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return "already_exited"
        try:
            process.wait(timeout=grace)
            return "SIGTERM"
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                return "already_exited"
            process.wait(timeout=grace)
            return "SIGKILL"


def _save_command_result(output_dir: Path, name: str, data: dict) -> Path:
    path = output_dir / f"{name}.json"
    write_json(path, data)
    (output_dir / f"{name}.stdout").write_text(data.get("stdout", ""))
    (output_dir / f"{name}.stderr").write_text(data.get("stderr", ""))
    return path


def _blocked(output_dir: Path, result: dict, message: str, raw: list[Path]) -> int:
    path = output_dir / "error.json"
    write_json(path, {"error": message})
    raw.append(path)
    return finalize_result(result, output_dir, [criterion("record_check", message, None, "", "ROS available and command succeeds",
                                                         "BLOCKED", "error.json", "UNKNOWN")],
                           [file_record(item, output_dir) for item in raw], [message])


def run_record(args: argparse.Namespace) -> int:
    output_dir = Path(args.analyze_only or args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = base_result("record_check", utc())
    try:
        config_path = Path(args.config) if args.config else Path(__file__).with_name("config.json")
        config = load_config(config_path)
        qos_path = _qos_path(config_path, config)
    except Exception as error:
        return _blocked(output_dir, result, f"config: {type(error).__name__}: {error}", [])
    if args.analyze_only:
        saved = output_dir / "record_raw.json"
        if not saved.is_file():
            return _blocked(output_dir, result, "record --analyze-only requires record_raw.json", [output_dir / "config.json"])
        raw = json.loads(saved.read_text())
        criteria = raw.get("criteria", [])
        return finalize_result(result, output_dir, criteria,
                               [file_record(saved, output_dir)], ["ANALYZE_ONLY: re-evaluated saved record command outputs."])

    write_json(output_dir / "config.json", config)
    raw_paths: list[Path] = [output_dir / "config.json"]
    if qos_path.is_file():
        raw_paths.append(qos_path)
    else:
        return _blocked(output_dir, result, f"configured QoS overrides file is missing: {qos_path}", raw_paths)
    node_list = run_command(["ros2", "node", "list"], timeout=config["record"]["node_list_timeout_s"],
                             env=dict(os.environ, ROS_LOCALHOST_ONLY="1"))
    node_path = _save_command_result(output_dir, "node_list", node_list)
    raw_paths += [node_path, output_dir / "node_list.stdout", output_dir / "node_list.stderr"]
    if node_list.get("missing_command"):
        return _blocked(output_dir, result, "ros2 is unavailable; native ROS checks are BLOCKED", raw_paths)
    if node_list["returncode"] != 0:
        return _blocked(output_dir, result, "ros2 node list failed", raw_paths)
    if config.get("camera_node") not in node_list.get("stdout", "").splitlines():
        return _blocked(output_dir, result, f"configured camera node {config.get('camera_node')} is not running", raw_paths)

    duration = float(args.seconds if args.seconds is not None else config["record"]["duration_s"])
    bag = output_dir / "bag"
    if bag.exists():
        return _blocked(output_dir, result, f"refusing to overwrite existing bag {bag}", raw_paths)
    topics = [item["name"] for item in config["topics"]]
    command = ["ros2", "bag", "record", "--storage", config["storage"]["storage_id"], "--output", str(bag),
               "--max-bag-duration", str(duration), "--qos-profile-overrides-path", str(qos_path), "--topics", *topics]
    write_json(output_dir / "command.json", {"argv": command, "shell": command_text(command), "duration_s": duration,
                                               "qos_file": str(qos_path), "topics": topics})
    raw_paths.append(output_dir / "command.json")
    record_log = (output_dir / "record.log").open("x")
    process = None
    stop_reason = "not_started"
    try:
        try:
            process = subprocess.Popen(command, stdout=record_log, stderr=subprocess.STDOUT,
                                       env=dict(os.environ, ROS_LOCALHOST_ONLY="1"), start_new_session=True)
        except FileNotFoundError:
            return _blocked(output_dir, result, "ros2 is unavailable; recording is BLOCKED", raw_paths)
        try:
            process.wait(timeout=duration + config["record"]["command_timeout_s"])
            stop_reason = "self_terminated"
        except subprocess.TimeoutExpired:
            stop_reason = _stop(process, config["record"]["shutdown_grace_s"])
    finally:
        if process is not None and process.poll() is None:
            _stop(process, config["record"]["shutdown_grace_s"])
        record_log.close()
    raw_paths.append(output_dir / "record.log")
    bag_info = run_command(["ros2", "bag", "info", str(bag)], timeout=config["record"]["bag_info_timeout_s"])
    bag_info_path = _save_command_result(output_dir, "bag_info", bag_info)
    raw_paths += [bag_info_path, output_dir / "bag_info.stdout", output_dir / "bag_info.stderr"]
    params = run_command(["ros2", "param", "dump", config["camera_node"]], timeout=config["record"]["parameter_timeout_s"])
    params_path = _save_command_result(output_dir, "parameter_dump", params)
    raw_paths += [params_path, output_dir / "parameter_dump.stdout", output_dir / "parameter_dump.stderr"]
    topic_results = {}
    for index, topic in enumerate(topics):
        topic_results[topic] = run_command(["ros2", "topic", "info", "-v", topic],
                                           timeout=config["record"]["topic_info_timeout_s"])
    write_json(output_dir / "topic_info.json", topic_results)
    raw_paths.append(output_dir / "topic_info.json")
    criteria = [
        criterion("record:bounded", "Recorder stopped after the configured bounded interval",
                  stop_reason, "stop_reason", "self_terminated or SIGINT", "PASS" if stop_reason in {"self_terminated", "SIGINT"} else "FAIL",
                  "record.log", config["record"]["threshold_source"]),
        criterion("record:bag_info", "ros2 bag info completed", bag_info["returncode"], "exit_code", "0",
                  "PASS" if bag_info["returncode"] == 0 else "FAIL", "bag_info.stdout", config["record"]["threshold_source"]),
        criterion("record:parameter_dump", "Camera parameter dump completed", params["returncode"], "exit_code", "0",
                  "PASS" if params["returncode"] == 0 else "FAIL", "parameter_dump.stdout", config["record"]["threshold_source"]),
        criterion("record:topic_qos", "Every configured topic has ros2 topic info -v evidence", sum(item.get("returncode") == 0 for item in topic_results.values()),
                  "topics", f"{len(topics)}", "PASS" if all(item.get("returncode") == 0 for item in topic_results.values()) else "FAIL",
                  "topic_info.json", config["record"]["threshold_source"]),
        criterion("record:exit", "Recorder process exited successfully or by SIGINT", process.returncode if process else None,
                  "exit_code", "0, -2, or 130", "PASS" if process and process.returncode in (0, -2, 130) else "FAIL",
                  "record.log", config["record"]["threshold_source"]),
    ]
    if bag.exists():
        try:
            report, bag_criteria = analyze_database(bag, config)
            report["analyzed_utc"] = utc()
            write_json(output_dir / "analysis.json", report)
            criteria.extend(bag_criteria)
            raw_paths.append(output_dir / "analysis.json")
            raw_paths.extend(storage_files(bag))
        except Exception as error:
            criteria.append(criterion("record:offline_analysis", "Recorded bag can be analyzed offline", None, "", str(error), "BLOCKED",
                                      "record.log", "UNKNOWN"))
    else:
        criteria.append(criterion("record:bag_exists", "Bounded recording created a bag", 0, "bags", ">= 1", "FAIL",
                                  "record.log", config["record"]["threshold_source"]))
    raw = [file_record(item, output_dir) for item in raw_paths if item.is_file()]
    raw_snapshot = {"criteria": criteria, "commands": {"record": command, "bag_info": bag_info,
                                                          "parameter_dump": params, "topic_info": topic_results},
                    "stop_reason": stop_reason}
    write_json(output_dir / "record_raw.json", raw_snapshot)
    raw.append(file_record(output_dir / "record_raw.json", output_dir))
    return finalize_result(result, output_dir, criteria, raw,
                           ["Physical acceptance still requires review of bag metadata, logs and current Pi power/thermal evidence."])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--seconds", type=float)
    parser.add_argument("--analyze-only", type=Path)
    args = parser.parse_args(argv)
    if bool(args.analyze_only) == bool(args.output_dir):
        parser.error("provide exactly one of --output-dir or --analyze-only")
    return run_record(args)


if __name__ == "__main__":
    raise SystemExit(main())

