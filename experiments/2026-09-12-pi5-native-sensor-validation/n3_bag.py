#!/usr/bin/env python3
"""Read finalized diagnostic bags and orchestrate complete isolated replay.

No recording or camera launch occurs in this tool. See PHASE_A_RUNBOOK.md.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from n3_metrics import TopicStats, compare_replay, evaluate, read_topics, save_json
from validation_common import evidence_hashes, provenance, sha256, verify_evidence

HERE = Path(__file__).resolve().parent


def utc():
    return datetime.now(timezone.utc).isoformat()


def inspect_bag(path, specs):
    import yaml
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message

    if not (path / "metadata.yaml").is_file():
        raise ValueError("Finalized metadata.yaml is required; do not reindex to conceal unclean recording")
    metadata = yaml.safe_load((path / "metadata.yaml").read_text())["rosbag2_bagfile_information"]
    for name in metadata.get('relative_file_paths', []):
        candidate = (path / name).resolve(strict=True)
        if not candidate.is_relative_to(path.resolve()) or candidate.stat().st_size == 0:
            raise ValueError('Missing/empty/unsafe finalized storage file')
    if not metadata.get('relative_file_paths'):
        raise ValueError('No finalized storage files in metadata')
    storage = metadata["storage_identifier"]
    if storage not in ("sqlite3", "mcap"):
        raise ValueError(f"Unreviewed storage plugin: {storage}")
    expected = {spec["name"]: spec for spec in specs}
    summary = {item["topic_metadata"]["name"]: item for item in metadata["topics_with_message_count"]}
    failures = []
    for name in summary.keys() - expected.keys():
        failures.append(f"unexpected recorded topic: {name}")
    for name, spec in expected.items():
        if name not in summary:
            if spec.get("required", True):
                failures.append(f"required topic missing from metadata: {name}")
        elif summary[name]["topic_metadata"]["type"] != spec["type"]:
            failures.append(f"metadata type mismatch: {name}")
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(path), storage_id=storage),
                rosbag2_py.ConverterOptions(input_serialization_format="cdr", output_serialization_format="cdr"))
    stats = {name: TopicStats(spec) for name, spec in expected.items()}
    classes = {name: get_message(spec["type"]) for name, spec in expected.items()}
    first_receipt = last_receipt = None
    reader_count = 0
    while reader.has_next():
        name, raw, receipt_ns = reader.read_next()
        reader_count += 1
        if first_receipt is None:
            first_receipt = receipt_ns
        if last_receipt is not None and receipt_ns < last_receipt:
            failures.append("bag receipt timestamps moved backward")
        last_receipt = receipt_ns
        if name in expected:
            stats[name].add(deserialize_message(raw, classes[name]), raw, receipt_ns / 1e9)
    duration_s = metadata["duration"]["nanoseconds"] / 1e9
    start = metadata["starting_time"]["nanoseconds_since_epoch"] / 1e9
    if duration_s <= 0:
        failures.append("nonpositive finalized bag duration")
    topics = {name: state.report(start, start + duration_s) for name, state in stats.items()}
    failures += evaluate(topics, specs)
    if reader_count != int(metadata["message_count"]):
        failures.append("reader total does not match finalized metadata")
    for name, result in topics.items():
        expected_count = int(summary.get(name, {}).get("message_count", 0))
        if result["count"] != expected_count:
            failures.append(f"{name}: decoded count differs from metadata")
        spec = expected[name]
        if "rate" in spec:
            rate = result["whole_window_hz"]
            if rate is None or not spec["rate"][0] <= rate <= spec["rate"][1]:
                failures.append(f"{name}: stored whole-window rate outside native-compatible band")
    return {"mode": "stored_bag", "inspected_utc": utc(), "bag": str(path.resolve()),
            "bag_sha256": evidence_hashes(path),
            "metadata": metadata, "storage_plugin": storage, "duration_s": duration_s,
            "reader_count": reader_count, "reader_completed": True,
            "first_receipt_ns": first_receipt, "last_receipt_ns": last_receipt,
            "topics": topics, "failures": failures, "verdict": "FAIL" if failures else "PASS"}


def stop_process(process):
    if process is not None and process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)


def local_camera_processes():
    result = subprocess.run(["ps", "-eo", "pid,args"], text=True, capture_output=True, timeout=5, check=True)
    patterns = ("realsense2_camera_node", "rs_launch.py", "rs-data-collect", "sample_ir", "rs-enumerate-devices",
                'component_container', 'realsense-viewer', 'rs-record', 'precision_capture')
    return [line.strip() for line in result.stdout.splitlines()
            if any(pattern in line for pattern in patterns)]


def assert_quiet(domain, output, topics_file):
    command = [sys.executable, str(HERE / "n3_observer.py"), "--mode", "no-publishers",
               "--seconds", "3", "--domain", str(domain), "--output", str(output)]
    if topics_file:
        command += ["--topics-file", str(topics_file)]
    result = subprocess.run(command, text=True, capture_output=True, timeout=15)
    if result.returncode:
        raise RuntimeError(f"Domain {domain} is not demonstrably quiet; inspect {output}: {result.stderr}")


def replay(args, specs):
    if args.live_domain == args.replay_domain:
        raise ValueError("Replay domain must differ from live domain")
    if not getattr(args, 'synthetic_fixture', False):
        recording = verify_evidence(args.record_result)
        if (recording.get('stage') != 'N3_RECORD' or recording.get('verdict') != 'REVIEW_REQUIRED'
                or recording.get('failures') or recording.get('camera_shutdown') != 'SIGINT'
                or recording.get('recorder_shutdown') != 'SIGINT'
                or recording.get('bag') != str(args.bag.resolve())
                or recording.get('bag_analysis', {}).get('bag_sha256') != evidence_hashes(args.bag)):
            raise ValueError('Replay requires unchanged finalized bag from clean gated recording')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    stored = inspect_bag(args.bag, specs)
    save_json(args.output_dir / "stored.json", stored)
    if stored["verdict"] != "PASS":
        raise ValueError("Stored bag validation failed; replay blocked")
    processes = local_camera_processes()
    save_json(args.output_dir / "process_check.json", {"utc": utc(), "camera_processes": processes})
    if processes:
        raise ValueError("Live camera/native capture process remains; replay blocked")
    assert_quiet(args.live_domain, args.output_dir / "live_domain_before.json", args.topics_file)
    assert_quiet(args.replay_domain, args.output_dir / "replay_domain_before.json", args.topics_file)
    duration = stored["duration_s"]
    if not 0 < duration <= 600:
        raise ValueError("This baseline tool accepts short diagnostic bags only (0 < duration <= 600 s)")
    ready, stop = args.output_dir / "observer_ready.json", args.output_dir / "observer_stop.json"
    observed_path = args.output_dir / "observed.json"
    observer_command = [sys.executable, str(HERE / "n3_observer.py"), "--mode", "replay",
                        "--domain", str(args.replay_domain), "--seconds", str(duration + 45),
                        "--ready-file", str(ready), "--stop-file", str(stop), "--output", str(observed_path)]
    if args.topics_file:
        observer_command += ["--topics-file", str(args.topics_file)]
    guard_ready = args.output_dir / "guard_ready.json"
    guard_output = args.output_dir / "live_domain_continuous.json"
    guard_command = [sys.executable, str(HERE / "n3_observer.py"), "--mode", "guard",
                     "--domain", str(args.live_domain), "--seconds", str(duration + 45),
                     "--ready-file", str(guard_ready), "--stop-file", str(stop), "--output", str(guard_output)]
    if args.topics_file:
        guard_command += ["--topics-file", str(args.topics_file)]
    player_command = ["ros2", "bag", "play", str(args.bag.resolve()), "--rate", "1.0", "--delay", "3",
                      "--qos-profile-overrides-path", str(args.qos_file)]
    environment = dict(os.environ, ROS_DOMAIN_ID=str(args.replay_domain), ROS_LOCALHOST_ONLY="1")
    save_json(args.output_dir / "commands.json", {"utc": utc(), "observer": observer_command,
                                                 "guard": guard_command, "player": player_command, "ROS_DOMAIN_ID": args.replay_domain,
                                                 "ROS_LOCALHOST_ONLY": "1"})
    observer = player = guard = None
    failures = []
    with (args.output_dir / "observer.log").open("x") as observer_log, (args.output_dir / "player.log").open("x") as player_log:
        try:
            guard = subprocess.Popen(guard_command, stdout=observer_log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            observer = subprocess.Popen(observer_command, stdout=observer_log, stderr=subprocess.STDOUT,
                                        env=environment, start_new_session=True)
            deadline = time.monotonic() + 15
            while not ready.exists() or not guard_ready.exists():
                if observer.poll() is not None or guard.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Observer readiness handshake failed; player was not started")
                time.sleep(0.1)
            # Subscriptions exist before player discovery and its explicit 3-second delay.
            player = subprocess.Popen(player_command, stdout=player_log, stderr=subprocess.STDOUT,
                                      env=environment, start_new_session=True)
            deadline = time.monotonic() + duration + 25
            next_process_check = time.monotonic()
            while player.poll() is None:
                if observer.poll() is not None:
                    raise RuntimeError("Observer exited before playback completed")
                if time.monotonic() >= deadline:
                    raise RuntimeError("Player exceeded bounded complete-playback deadline")
                if guard.poll() is not None:
                    raise RuntimeError("Continuous original live-domain guard exited during playback")
                if time.monotonic() >= next_process_check:
                    if local_camera_processes():
                        raise RuntimeError("Live camera/native capture process started during replay")
                    next_process_check = time.monotonic() + 1
                time.sleep(0.1)
            if player.returncode != 0:
                failures.append(f"player exit code {player.returncode}")
            # Drain queued deliveries before ending the observer's complete replay interval.
            time.sleep(3)
            save_json(stop, {"stop_utc": utc(), "player_exit_code": player.returncode})
            observer.wait(timeout=10)
            guard.wait(timeout=10)
            if observer.returncode:
                failures.append(f"observer exit code {observer.returncode}")
            if guard.returncode:
                failures.append(f"live-domain guard exit code {guard.returncode}")
        except Exception as error:
            failures.append(f"replay orchestration: {type(error).__name__}: {error}")
        finally:
            stop_process(player)
            stop_process(observer)
            stop_process(guard)
    if observed_path.is_file():
        observed = json.loads(observed_path.read_text())
        failures.extend(observed["failures"])
        failures.extend(compare_replay(stored, observed, specs))
    else:
        failures.append("complete observer output missing")
    if guard_output.is_file():
        failures.extend(json.loads(guard_output.read_text())["failures"])
    else:
        failures.append("continuous original-domain guard evidence missing")
    player_log_text = (args.output_dir / "player.log").read_text(errors="replace")
    if re.search(r"\b(?:error|fatal|exception|failed|corrupt(?:ed|ion)?)\b", player_log_text, re.IGNORECASE):
        failures.append("player log contains error/failure markers; review complete raw log")
    # Check the control/live domain again; a camera restart during replay invalidates acceptance.
    try:
        assert_quiet(args.live_domain, args.output_dir / "live_domain_after.json", args.topics_file)
        if local_camera_processes():
            failures.append("camera process appeared during replay")
    except Exception as error:
        failures.append(str(error))
    result = {"stage": "N3_REPLAY", "end_utc": utc(), "live_domain": args.live_domain,
              "scope": 'SYNTHETIC_TOOLING_ONLY' if getattr(args, 'synthetic_fixture', False) else 'PHYSICAL_RECORD_REPLAY',
              "provenance": provenance(), "bag_sha256": stored['bag_sha256'],
              "topics_sha256": sha256(args.topics_file or HERE / 'n3_topics.json'),
              "replay_domain": args.replay_domain, "failures": failures,
              "verdict": "FAIL" if failures else "REVIEW_REQUIRED",
              "review_required": "Review complete player.log and observer.log, including reader warnings."}
    if evidence_hashes(args.bag) != stored['bag_sha256']:
        failures.append('Bag changed during replay')
        result['verdict'] = 'FAIL'
    result['evidence_sha256'] = evidence_hashes(args.output_dir)
    save_json(args.output_dir / "replay_result.json", result)
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("bag", type=Path)
    inspect_parser.add_argument("--output", type=Path, required=True)
    inspect_parser.add_argument("--topics-file", type=Path)
    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("bag", type=Path)
    replay_parser.add_argument("--output-dir", type=Path, required=True)
    replay_parser.add_argument('--record-result', type=Path, required=True)
    replay_parser.add_argument("--live-domain", type=int, default=42)
    replay_parser.add_argument("--replay-domain", type=int, default=43)
    replay_parser.add_argument("--topics-file", type=Path)
    replay_parser.add_argument("--qos-file", type=Path, default=HERE / "n3_qos.yaml")
    args = parser.parse_args()
    specs = read_topics(args.topics_file)
    try:
        if args.command == "inspect":
            result = inspect_bag(args.bag, specs)
            save_json(args.output, result)
            return 1 if result["failures"] else 0
        return replay(args, specs)
    except Exception as error:
        print(f"BLOCKED: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
