#!/usr/bin/env python3
"""Simultaneous native ROS observation; never starts a camera or changes parameters."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
import math
from pathlib import Path
import time

from n3_metrics import TopicStats, evaluate, read_topics, save_json
from validation_common import camera_guard, provenance, sha256


def utc():
    return datetime.now(timezone.utc).isoformat()


def graph_snapshot(node, specs):
    graph = {}
    for spec in specs:
        endpoints = node.get_publishers_info_by_topic(spec["name"])
        graph[spec["name"]] = [
            {"node_name": item.node_name, "node_namespace": item.node_namespace,
             "type": item.topic_type, "qos": str(item.qos_profile),
             "reliability": item.qos_profile.reliability.name,
             "durability": item.qos_profile.durability.name} for item in endpoints]
    return graph


def qos_failures(graph, specs):
    failures = []
    for spec in specs:
        for endpoint in graph.get(spec['name'], []):
            if endpoint['reliability'] not in ('RELIABLE', 'BEST_EFFORT'):
                failures.append(spec['name'] + ': unknown offered reliability')
            if spec.get('latched') and (endpoint['reliability'] != 'RELIABLE'
                                       or endpoint['durability'] != 'TRANSIENT_LOCAL'):
                failures.append(spec['name'] + ': context QoS is not reliable/transient-local')
    return failures


def forbidden_publishers(node):
    forbidden = []
    for name, _ in node.get_topic_names_and_types():
        if name.startswith("/camera/camera/") and any(
            token in name for token in ("/color/", "/depth/", "/infra2/", "/points", "/aligned_depth", "/rgbd")
        ) or name == "/camera/camera/imu":
            if node.count_publishers(name):
                forbidden.append(name)
    return sorted(forbidden)


def observe(args):
    # Deferred imports keep pure-analysis tests available on non-ROS hosts.
    import rclpy
    from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message

    specs = read_topics(args.topics_file)
    run_provenance = provenance()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.ready_file and args.ready_file.exists():
        raise FileExistsError(args.ready_file)
    if args.stop_file and args.stop_file.exists():
        raise FileExistsError(args.stop_file)
    rclpy.init(domain_id=args.domain)
    node = rclpy.create_node("wbr_n3_observer")
    stats = {spec["name"]: TopicStats(spec) for spec in specs}
    subscriptions, failures = [], []
    start_utc = utc()
    start = time.monotonic()
    graph_before, graph_after = {}, {}
    completed = False
    try:
        if args.mode in ("no-publishers", "guard"):
            deadline = start + args.seconds
            camera_nodes, extra, active = [], [], {}
            checks, next_check = 0, start
            if args.ready_file:
                save_json(args.ready_file, {"ready_utc": utc(), "domain": args.domain})
            while time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=0.1)
                if time.monotonic() >= next_check:
                    graph_after = graph_snapshot(node, specs)
                    active = {name: publishers for name, publishers in graph_after.items() if publishers}
                    camera_nodes = [namespace.rstrip("/") + "/" + name
                                    for name, namespace in node.get_node_names_and_namespaces()
                                    if "camera" in name.lower() or "realsense" in name.lower()]
                    extra = forbidden_publishers(node)
                    failures = (["required-topic publishers remain"] if active else [])
                    failures += (["camera nodes remain"] if camera_nodes else [])
                    failures += (["extra camera publishers remain"] if extra else [])
                    checks += 1
                    next_check = time.monotonic() + 0.5
                    if failures:
                        break
                if args.stop_file and args.stop_file.exists():
                    completed = True
                    break
            if args.mode == "guard" and not completed:
                failures.append("continuous live-domain guard did not finish via stop handshake")
            save_json(args.output, {"mode": args.mode, "domain": args.domain,
                                   "start_utc": start_utc, "end_utc": utc(),
                                   "graph": graph_after, "camera_nodes": camera_nodes,
                                   "checks": checks, "completed": completed,
                                   "forbidden_publishers": extra, "failures": failures,
                                   "verdict": "FAIL" if failures else "PASS"})
            return 1 if failures else 0

        for spec in specs:
            message_type = get_message(spec["type"])
            latched = spec.get("latched", False)
            qos = QoSProfile(depth=100 if latched or spec["role"] in ("image", "camera_info") else 1000,
                             reliability=ReliabilityPolicy.RELIABLE if latched else ReliabilityPolicy.BEST_EFFORT,
                             durability=DurabilityPolicy.TRANSIENT_LOCAL if latched else DurabilityPolicy.VOLATILE)

            def callback(raw, name=spec["name"], typ=message_type):
                try:
                    stats[name].add(deserialize_message(raw, typ), raw, time.monotonic())
                except Exception as error:
                    failures.append(f"{name}: deserialize/analysis error: {error}")

            subscriptions.append(node.create_subscription(message_type, spec["name"], callback, qos, raw=True))

        if args.mode == "live":
            # Exclude discovery from the measured window; retain latched context.
            deadline = time.monotonic() + args.discovery_seconds
            while time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=0.05)
                if all(stats[spec["name"]].count for spec in specs if spec.get("required", True)):
                    break
            missing = [spec["name"] for spec in specs
                       if spec.get("required", True) and not stats[spec["name"]].count]
            if missing:
                failures.append("discovery timeout: " + ", ".join(missing))
            for spec in specs:
                if not spec.get("latched", False):
                    stats[spec["name"]] = TopicStats(spec)
        graph_before = graph_snapshot(node, specs)
        start, start_utc = time.monotonic(), utc()
        if args.ready_file:
            save_json(args.ready_file, {"ready_utc": start_utc, "domain": args.domain,
                                       "subscriptions_created": len(subscriptions)})
        next_graph = start
        while time.monotonic() - start < args.seconds and not failures:
            rclpy.spin_once(node, timeout_sec=0.05)
            if time.monotonic() >= next_graph:
                graph_after = graph_snapshot(node, specs)
                failures.extend(qos_failures(graph_after, specs))
                for spec in specs:
                    publishers = graph_after[spec["name"]]
                    if any(item["type"] != spec["type"] for item in publishers):
                        failures.append(f"{spec['name']}: publisher type mismatch")
                    if len(publishers) > 1:
                        failures.append(f"{spec['name']}: multiple publishers")
                    if args.mode == "replay" and any(item["node_name"] != "rosbag2_player" for item in publishers):
                        failures.append(f"{spec['name']}: publisher other than rosbag2_player")
                extra = forbidden_publishers(node)
                if extra:
                    failures.append("forbidden extra streams: " + ", ".join(extra))
                next_graph = time.monotonic() + 0.5
            if args.stop_file and args.stop_file.exists():
                completed = True
                break
        if args.mode == "live":
            completed = time.monotonic() - start >= args.seconds
        if not completed:
            failures.append("observation did not complete its requested window/stop handshake")
    except Exception as error:
        failures.append(f"observer exception: {type(error).__name__}: {error}")
    finally:
        end = time.monotonic()
        node.destroy_node()
        rclpy.shutdown()
    reports = {name: state.report(start, end) for name, state in stats.items()}
    failures += evaluate(reports, specs, live=args.mode == "live")
    save_json(args.output, {"mode": args.mode, "domain": args.domain,
                           "provenance": run_provenance,
                           "topics_sha256": sha256(args.topics_file or Path(__file__).with_name('n3_topics.json')),
                           "start_utc": start_utc, "end_utc": utc(), "window_s": end - start,
                           "topics": reports, "graph_before": graph_before, "graph_after": graph_after,
                           "completed": completed, "failures": failures,
                           "verdict": "FAIL" if failures else "PASS",
                           "limitations": ["Transport evidence does not qualify IMU/VIO calibration.",
                                           "ROS messages do not expose native frame numbers."]})
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("live", "replay", "no-publishers", "guard"), default="live")
    parser.add_argument('--camera-available', action='store_true')
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--discovery-seconds", type=float, default=15.0)
    parser.add_argument("--domain", type=int, default=int(os.environ.get("ROS_DOMAIN_ID", "42")))
    parser.add_argument("--topics-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ready-file", type=Path)
    parser.add_argument("--stop-file", type=Path)
    args = parser.parse_args()
    os.environ['ROS_LOCALHOST_ONLY'] = '1'
    if not math.isfinite(args.seconds) or not math.isfinite(args.discovery_seconds) or args.seconds <= 0 or args.discovery_seconds <= 0 or not 0 <= args.domain <= 232:
        parser.error("positive durations and domain 0..232 required")
    if args.mode in ("replay", "guard") and (not args.ready_file or not args.stop_file):
        parser.error("replay requires ready and stop handshake paths")
    if args.mode == 'live':
        camera_guard(args.camera_available)
    return observe(args)


if __name__ == "__main__":
    raise SystemExit(main())
