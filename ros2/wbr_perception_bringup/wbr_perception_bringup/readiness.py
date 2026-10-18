"""Runtime-only ROS subscriber. Sensor arrival readiness is not qualification."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time


def save(path, value):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads((args.run_dir / "config.json").read_text())
    # Keep the planner and host tests entirely independent of ROS imports.
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image, Imu
    rclpy.init(args=[])
    node = rclpy.create_node("wbr_stack_readiness")
    qos_profile_sensor_data.depth = config["readiness_qos_depth"]["value"]
    seen, counts = {}, {key: 0 for key in config["topics"]}
    required = config["readiness_messages"]["value"]

    def callback(role, msg):
        counts[role] += 1
        if role not in seen:
            seen[role] = {
                "ros_header_stamp_ns": msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec,
                "receipt_clock_monotonic_ns": time.monotonic_ns(),
                "source_clock": "ROS header.stamp; D435i hardware/global identity UNKNOWN",
                "topic": config["topics"][role]}
        if all(count >= required for count in counts.values()) and not (args.run_dir / "ready.json").exists():
            save(args.run_dir / "ready.json", {"first_messages": seen,
                "evidence": "MEASURED arrival only; no clock mapping or stream qualification"})

    subscriptions = [node.create_subscription(Imu if role == "imu" else Image, topic,
        lambda msg, role=role: callback(role, msg), qos_profile_sensor_data)
        for role, topic in config["topics"].items()]
    save(args.run_dir / "armed.json", {"topics": config["topics"],
        "clock_monotonic_ns": time.monotonic_ns(), "evidence": "MEASURED subscriptions created; DDS discovery not proven"})
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
