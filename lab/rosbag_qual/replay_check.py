#!/usr/bin/env python3
"""Replay a bag in a separate ROS graph and compare delivery to offline evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from bag_core import analyze_database, storage_files
from qual_common import (base_result, criterion, file_record, finalize_result,
                         load_config, run_command, utc, write_json)


def _qos_path(config_path: Path, config: dict) -> Path:
    qos = Path(config["qos_overrides_file"])
    return qos if qos.is_absolute() else config_path.parent / qos


def _header_stamp(message) -> int | None:
    header = getattr(message, "header", None)
    if header is None or not hasattr(header, "stamp"):
        return None
    return int(header.stamp.sec) * 1_000_000_000 + int(header.stamp.nanosec)


def _observe_replay(bag: Path, config: dict, qos_path: Path, output_dir: Path, replay_domain: int) -> tuple[dict, int, str]:
    """Run rclpy subscribers and ros2 bag play; imports are intentionally lazy."""
    try:
        import rclpy
        from rclpy.executors import SingleThreadedExecutor
        from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
        from rosidl_runtime_py.utilities import get_message
    except ImportError as error:
        raise RuntimeError(f"ROS Python packages unavailable: {error}") from error

    topics = config["topics"]
    observations = {spec["name"]: {"count": 0, "stamps": [], "received_ns": [], "errors": []}
                    for spec in topics}
    rclpy.init(args=None, domain_id=replay_domain)
    node = rclpy.create_node("wbr_rosbag_qual_replay_observer")
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    subscriptions = []
    try:
        for spec in topics:
            try:
                msg_class = get_message(spec["type"])
                if spec.get("role") == "tf_static":
                    qos = QoSProfile(depth=100, reliability=ReliabilityPolicy.RELIABLE,
                                     durability=DurabilityPolicy.TRANSIENT_LOCAL)
                else:
                    qos = QoSProfile(depth=1000, reliability=ReliabilityPolicy.BEST_EFFORT,
                                     durability=DurabilityPolicy.VOLATILE)
                def callback(message, name=spec["name"]):
                    item = observations[name]
                    item["count"] += 1
                    stamp = _header_stamp(message)
                    if stamp is not None:
                        item["stamps"].append(stamp)
                    item["received_ns"].append(time.monotonic_ns())
                subscriptions.append(node.create_subscription(msg_class, spec["name"], callback, qos))
            except Exception as error:
                observations[spec["name"]]["errors"].append(f"subscription: {type(error).__name__}: {error}")
        command = ["ros2", "bag", "play", str(bag.resolve()), "--rate", "1.0",
                   "--qos-profile-overrides-path", str(qos_path)]
        log_path = output_dir / "player.log"
        with log_path.open("w") as log:
            try:
                player = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                           env=dict(os.environ, ROS_LOCALHOST_ONLY="1", ROS_DOMAIN_ID=str(replay_domain)), start_new_session=True)
            except FileNotFoundError as error:
                raise RuntimeError(f"ros2 is unavailable: {error}") from error
            timeout = float(config["record"]["duration_s"] + config["record"]["command_timeout_s"])
            deadline = time.monotonic() + timeout
            while player.poll() is None:
                executor.spin_once(timeout_sec=0.05)
                if time.monotonic() >= deadline:
                    player.kill()
                    player.wait(timeout=5)
                    raise RuntimeError("ros2 bag play exceeded bounded timeout")
            for _ in range(20):
                executor.spin_once(timeout_sec=0.05)
        observations["_command"] = command
        return observations, player.returncode, str(log_path)
    finally:
        node.destroy_node()
        rclpy.shutdown()


def _replay_report(observations: dict, config: dict) -> dict:
    report = {"topics": {}}
    for spec in config["topics"]:
        item = observations.get(spec["name"], {})
        stamps = item.get("stamps", [])
        received = item.get("received_ns", [])
        header_rate = ((len(stamps) - 1) / ((stamps[-1] - stamps[0]) / 1e9)
                       if len(stamps) > 1 and stamps[-1] > stamps[0] else None)
        receive_rate = ((len(received) - 1) / ((received[-1] - received[0]) / 1e9)
                        if len(received) > 1 and received[-1] > received[0] else None)
        import hashlib
        import struct
        digest = hashlib.sha256()
        for stamp in stamps:
            digest.update(struct.pack("<q", int(stamp)))
        report["topics"][spec["name"]] = {
            "count": item.get("count", 0), "header_count": len(stamps),
            "header_rate_hz": header_rate, "replay_receive_rate_hz": receive_rate,
            "first_header_stamp_ns": stamps[0] if stamps else None,
            "last_header_stamp_ns": stamps[-1] if stamps else None,
            "header_stamp_sha256": digest.hexdigest(), "errors": item.get("errors", [])}
    return report


def _criteria(stored: dict, replay: dict, config: dict, evidence: str) -> list[dict]:
    criteria = []
    criteria.append(criterion("replay:player", "ros2 bag play exited successfully", replay.get("player_returncode"),
                              "exit_code", "0", "PASS" if replay.get("player_returncode") == 0 else "FAIL",
                              evidence, config["record"]["threshold_source"]))
    tolerance = config["replay"]["rate_relative_tolerance"]
    fraction_limit = config["replay"]["min_count_fraction"]
    for spec in config["topics"]:
        name = spec["name"]
        expected = stored.get("topics", {}).get(name, {})
        actual = replay.get("topics", {}).get(name, {})
        expected_count = expected.get("count", 0)
        observed_count = actual.get("count", 0)
        fraction = observed_count / expected_count if expected_count else None
        count_status = "BLOCKED" if expected_count and not actual else ("PASS" if expected_count == 0 or fraction >= fraction_limit else "FAIL")
        criteria.append(criterion(f"replay:{name}:count", "Replay count fraction versus stored bag",
                                  fraction, "fraction", f">= {fraction_limit}", count_status, evidence,
                                  config["replay"]["threshold_source"]))
        if expected.get("header_count", 0):
            stamp_status = "PASS" if expected.get("header_stamp_sha256") == actual.get("header_stamp_sha256") else "FAIL"
            criteria.append(criterion(f"replay:{name}:stamps", "Replay preserves header.stamp sequence",
                                      stamp_status == "PASS", "exact", "true", stamp_status, evidence,
                                      config["replay"]["threshold_source"]))
            recorded_rate = expected.get("header_rate_hz")
            replay_rate = actual.get("replay_receive_rate_hz")
            if recorded_rate and replay_rate:
                relative_error = abs(replay_rate - recorded_rate) / recorded_rate
                rate_status = "PASS" if relative_error <= tolerance else "FAIL"
            else:
                relative_error, rate_status = None, "BLOCKED"
            criteria.append(criterion(f"replay:{name}:rate", "Replay receive rate versus recorded header rate",
                                      relative_error, "relative_error", f"<= {tolerance}", rate_status, evidence,
                                      config["replay"]["threshold_source"]))
    return criteria


def _blocked(output_dir: Path, result: dict, message: str, raw: list[Path]) -> int:
    error_path = output_dir / "error.json"
    write_json(error_path, {"error": message})
    raw.append(error_path)
    return finalize_result(result, output_dir, [criterion("replay_check", message, None, "", "ROS graph stopped and ROS Python available",
                                                         "BLOCKED", "error.json", "UNKNOWN")],
                           [file_record(item, output_dir) for item in raw if item.is_file()], [message])


def run_replay(args: argparse.Namespace) -> int:
    output_dir = Path(args.analyze_only or args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = base_result("replay_check", utc())
    config_path = Path(args.config) if args.config else Path(__file__).with_name("config.json")
    try:
        config = load_config(config_path)
    except Exception as error:
        return _blocked(output_dir, result, f"config: {type(error).__name__}: {error}", [])

    if args.analyze_only:
        stored_path, observed_path = output_dir / "stored_analysis.json", output_dir / "replay_observations.json"
        if not stored_path.is_file() or not observed_path.is_file():
            return _blocked(output_dir, result, "replay --analyze-only requires stored_analysis.json and replay_observations.json", [])
        stored = json.loads(stored_path.read_text())
        replay = json.loads(observed_path.read_text())
        criteria = _criteria(stored, replay, config, "replay_observations.json")
        return finalize_result(result, output_dir, criteria,
                               [file_record(stored_path, output_dir), file_record(observed_path, output_dir)],
                               ["ANALYZE_ONLY: re-evaluated saved replay observations; no ROS graph used."])

    if not args.bag:
        return _blocked(output_dir, result, "a bag path is required unless --analyze-only is used", [])
    qos_path = _qos_path(config_path, config)
    raw: list[Path] = [qos_path] if qos_path.is_file() else []
    if not qos_path.is_file():
        return _blocked(output_dir, result, f"configured QoS overrides file is missing: {qos_path}", raw)
    node_list = run_command(["ros2", "node", "list"], timeout=config["record"]["node_list_timeout_s"],
                             env=dict(os.environ, ROS_LOCALHOST_ONLY="1", ROS_DOMAIN_ID=str(args.live_domain)))
    write_json(output_dir / "node_list.json", node_list)
    raw.append(output_dir / "node_list.json")
    if node_list.get("missing_command"):
        return _blocked(output_dir, result, "ros2 is unavailable; replay is BLOCKED", raw)
    names = node_list.get("stdout", "").splitlines()
    forbidden = [name for name in names if "realsense" in name.lower() or name.strip() == config.get("camera_node")]
    if node_list.get("returncode") != 0:
        return _blocked(output_dir, result, "ros2 node list failed", raw)
    if forbidden:
        return _blocked(output_dir, result, "live camera/realsense node is still running: " + ", ".join(forbidden), raw)
    try:
        stored, _ = analyze_database(Path(args.bag), config)
        write_json(output_dir / "stored_analysis.json", stored)
        raw += [output_dir / "stored_analysis.json", *storage_files(Path(args.bag))]
        if any(item["status"] == "FAIL" for item in stored["criteria"]):
            return _blocked(output_dir, result, "stored bag fails offline qualification; replay not accepted", raw)
        observations, player_returncode, player_log = _observe_replay(Path(args.bag), config, qos_path, output_dir,
                                                                      args.replay_domain)
        observations["player_returncode"] = player_returncode
        observations["observed_utc"] = utc()
        write_json(output_dir / "replay_observations.json", observations)
        raw += [output_dir / "replay_observations.json", Path(player_log)]
        criteria = _criteria(stored, _replay_report(observations, config) | {"player_returncode": player_returncode}, config,
                             "replay_observations.json")
        return finalize_result(result, output_dir, criteria,
                               [file_record(item, output_dir) for item in raw if item.is_file()],
                               ["Replay evidence is separate from offline bag evidence.",
                                "No physical camera node was allowed in the replay ROS domain."])
    except Exception as error:
        return _blocked(output_dir, result, f"replay: {type(error).__name__}: {error}", raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bag", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--live-domain", type=int, default=42)
    parser.add_argument("--replay-domain", type=int, default=43)
    parser.add_argument("--analyze-only", type=Path)
    args = parser.parse_args(argv)
    if bool(args.analyze_only) == bool(args.output_dir):
        parser.error("provide exactly one of --output-dir or --analyze-only")
    return run_replay(args)


if __name__ == "__main__":
    raise SystemExit(main())

