#!/usr/bin/env python3
"""Automated home acceptance test for the F446 micro-ROS AGV base.

The ROS-free calculations live here too, so the acceptance rules can be tested
with the Python standard library on a machine without ROS installed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence


# Geometry matches User/Config/robot_config.h in the read-only H723 source tree:
# WHEEL_RADIUS=0.060 m, WHEEL_BASE=0.345 m. The feedback signs are +1/+1 because
# docs/topics.md defines /motor_fb in wheel frame (positive = forward on both
# wheels); the firmware already multiplies by MOTOR_LEFT_SIGN=-1 /
# MOTOR_RIGHT_SIGN=+1 before publishing. Pass --left-sign -1 to check a raw
# motor-frame publisher instead.
DEFAULT_WHEEL_RADIUS = 0.060
DEFAULT_WHEEL_BASE = 0.345
DEFAULT_LEFT_SIGN = 1.0
DEFAULT_RIGHT_SIGN = 1.0
MAX_WHEEL_SPEED = 20.0
TIMEOUT_STATUS_BIT = 0x20
MOTORS_ENABLED_STATUS_BIT = 0x10

REQUIRED_TOPICS = ("/cmd_vel", "/motor_enable", "/motor_fb", "/motor_status")


def expected_wheel_speeds(
    linear_x: float,
    angular_z: float,
    wheel_radius: float = DEFAULT_WHEEL_RADIUS,
    wheel_base: float = DEFAULT_WHEEL_BASE,
    left_sign: float = DEFAULT_LEFT_SIGN,
    right_sign: float = DEFAULT_RIGHT_SIGN,
    max_wheel_speed: float = MAX_WHEEL_SPEED,
) -> tuple[float, float]:
    """Differential-drive targets in motor-feedback wheel frame, with common saturation."""
    if wheel_radius <= 0 or wheel_base <= 0 or max_wheel_speed <= 0:
        raise ValueError("wheel dimensions and speed limit must be positive")
    left = (linear_x - wheel_base * angular_z / 2.0) / wheel_radius * left_sign
    right = (linear_x + wheel_base * angular_z / 2.0) / wheel_radius * right_sign
    peak = max(abs(left), abs(right))
    if peak > max_wheel_speed:
        scale = max_wheel_speed / peak
        left *= scale
        right *= scale
    return left, right


def check_close_pair(
    actual: Sequence[float], expected: Sequence[float], tolerance: float
) -> tuple[bool, str]:
    if len(actual) != 2 or len(expected) != 2:
        return False, "expected exactly two wheel values"
    errors = [abs(float(a) - float(e)) for a, e in zip(actual, expected)]
    ok = all(math.isfinite(float(a)) and err <= tolerance for a, err in zip(actual, errors))
    return ok, f"actual={list(actual)!r}, expected={list(expected)!r}, abs_error={errors!r}, tol={tolerance:g}"


def check_zero_pair(actual: Sequence[float], tolerance: float) -> tuple[bool, str]:
    return check_close_pair(actual, (0.0, 0.0), tolerance)


def check_common_scale(
    actual: Sequence[float], unsaturated: Sequence[float], tolerance: float
) -> tuple[bool, str]:
    """Check that saturation preserves the two-wheel vector's common ratio."""
    if len(actual) != 2 or len(unsaturated) != 2:
        return False, "expected exactly two wheel values"
    ratios = []
    for a, u in zip(actual, unsaturated):
        if abs(u) <= 1e-12:
            if abs(a) > tolerance:
                return False, f"zero unsaturated wheel became {a:g}"
        else:
            ratios.append(float(a) / float(u))
    if not ratios:
        return False, "no nonzero wheel target to compare"
    spread = max(ratios) - min(ratios) if len(ratios) > 1 else 0.0
    common = sum(ratios) / len(ratios)
    good = spread <= tolerance and common > 0.0 and abs(common * max(abs(x) for x in unsaturated) - MAX_WHEEL_SPEED) <= max(tolerance, 0.05)
    return good, f"wheel scale factors={ratios!r}, spread={spread:.6g}, mean={common:.6g}"


def check_timeout(status_values: Iterable[int], velocities: Sequence[float], zero_tolerance: float) -> tuple[bool, str]:
    statuses = [int(v) for v in status_values]
    has_bit = any(value & TIMEOUT_STATUS_BIT for value in statuses)
    wheels_ok, wheel_detail = check_zero_pair(velocities, zero_tolerance)
    return has_bit and wheels_ok, f"timeout_bit_seen={has_bit}, {wheel_detail}"


def check_disabled(status_values: Iterable[int], velocities: Sequence[float], zero_tolerance: float) -> tuple[bool, str]:
    statuses = [int(v) for v in status_values]
    status_clear = bool(statuses) and not (statuses[-1] & MOTORS_ENABLED_STATUS_BIT)
    wheels_ok, wheel_detail = check_zero_pair(velocities, zero_tolerance)
    return status_clear and wheels_ok, f"latest_status={statuses[-1] if statuses else None}, motors_enabled_bit_clear={status_clear}, {wheel_detail}"


def check_timeout_timing(
    last_command_elapsed_s: float,
    status_samples: Iterable[tuple[float, int]],
    feedback_rows: Iterable[dict[str, Any]],
    zero_tolerance: float,
    max_wait_s: float,
) -> tuple[bool, str]:
    timeout_times = [t for t, value in status_samples
                     if t >= last_command_elapsed_s and int(value) & TIMEOUT_STATUS_BIT]
    zero_times = [float(row["elapsed_s"]) for row in feedback_rows
                  if float(row["elapsed_s"]) >= last_command_elapsed_s
                  and abs(float(row["left_velocity_rad_s"])) <= zero_tolerance
                  and abs(float(row["right_velocity_rad_s"])) <= zero_tolerance]
    timeout_delay = min(timeout_times) - last_command_elapsed_s if timeout_times else None
    zero_delay = min(zero_times) - last_command_elapsed_s if zero_times else None
    good = timeout_delay is not None and zero_delay is not None and timeout_delay <= max_wait_s and zero_delay <= max_wait_s
    return good, f"timeout_bit_delay_s={timeout_delay}, first_zero_feedback_delay_s={zero_delay}, limit_s={max_wait_s:g}"


def check_nan_ignored(before: Sequence[float], after: Sequence[float], tolerance: float) -> tuple[bool, str]:
    return check_close_pair(after, before, tolerance)


@dataclass
class StepResult:
    name: str
    passed: bool
    detail: str


class FeedbackRecorder:
    """ROS callbacks append normalized feedback rows; no ROS import at module load."""

    def __init__(self) -> None:
        self.feedback: list[dict[str, Any]] = []
        self.status: list[tuple[float, int]] = []
        self.started = time.monotonic()

    def feedback_callback(self, msg: Any) -> None:
        pos = list(msg.position)
        vel = list(msg.velocity)
        eff = list(msg.effort)
        if len(vel) < 2:
            return
        stamp = msg.header.stamp
        stamp_s = float(stamp.sec) + float(stamp.nanosec) * 1e-9
        self.feedback.append({
            "elapsed_s": time.monotonic() - self.started,
            "ros_stamp_s": stamp_s,
            "frame_id": msg.header.frame_id,
            "left_position_rad": pos[0] if len(pos) > 0 else "",
            "right_position_rad": pos[1] if len(pos) > 1 else "",
            "left_velocity_rad_s": vel[0],
            "right_velocity_rad_s": vel[1],
            "left_effort_nm": eff[0] if len(eff) > 0 else "",
            "right_effort_nm": eff[1] if len(eff) > 1 else "",
        })

    def status_callback(self, msg: Any) -> None:
        self.status.append((time.monotonic() - self.started, int(msg.data)))


def _write_outputs(out_dir: str, recorder: FeedbackRecorder, summary: dict[str, Any]) -> None:
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "motor_fb.csv")
    fields = ["elapsed_s", "ros_stamp_s", "frame_id", "left_position_rad", "right_position_rad",
              "left_velocity_rad_s", "right_velocity_rad_s", "left_effort_nm", "right_effort_nm"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(recorder.feedback)
    summary["artifacts"] = {"motor_fb_csv": csv_path, "summary_json": os.path.join(out_dir, "summary.json")}
    with open(summary["artifacts"]["summary_json"], "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, allow_nan=False)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="agv_home_test_output", help="directory for motor_fb.csv and summary.json")
    p.add_argument("--node-name", default="/stm32_agv_node")
    p.add_argument("--cmd-vel", default="/cmd_vel")
    p.add_argument("--motor-enable", default="/motor_enable")
    p.add_argument("--motor-fb", default="/motor_fb")
    p.add_argument("--motor-status", default="/motor_status")
    p.add_argument("--wheel-radius", type=float, default=DEFAULT_WHEEL_RADIUS, help="meters")
    p.add_argument("--wheel-base", type=float, default=DEFAULT_WHEEL_BASE, help="meters")
    p.add_argument("--left-sign", type=float, default=DEFAULT_LEFT_SIGN)
    p.add_argument("--right-sign", type=float, default=DEFAULT_RIGHT_SIGN)
    p.add_argument("--velocity-tolerance", type=float, default=1.5, help="rad/s absolute feedback tolerance")
    p.add_argument("--zero-tolerance", type=float, default=0.5, help="rad/s zero feedback tolerance")
    p.add_argument("--saturation-tolerance", type=float, default=0.6, help="rad/s saturation tolerance")
    p.add_argument("--settle-seconds", type=float, default=0.5)
    p.add_argument("--drive-seconds", type=float, default=3.0)
    p.add_argument("--timeout-margin", type=float, default=0.4, help="extra wait after 500 ms watchdog")
    p.add_argument("--discovery-seconds", type=float, default=8.0)
    return p.parse_args()


def run() -> int:
    args = _parse_args()
    # Defer ROS imports to allow standard-library unit tests on non-ROS hosts.
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
        from geometry_msgs.msg import Twist
        from std_msgs.msg import Bool, UInt8
        from sensor_msgs.msg import JointState
    except ImportError as exc:
        print(f"FAIL ROS dependencies: {exc}")
        return 2

    class HomeTestNode(Node):
        def __init__(self) -> None:
            super().__init__("agv_f446_home_test")
            best_effort = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            reliable = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10, reliability=ReliabilityPolicy.RELIABLE)
            self.cmd_pub = self.create_publisher(Twist, args.cmd_vel, best_effort)
            self.enable_pub = self.create_publisher(Bool, args.motor_enable, reliable)
            self.recorder = FeedbackRecorder()
            self.last_cmd_publish_elapsed_s: float | None = None
            self.fb_sub = self.create_subscription(JointState, args.motor_fb, self.recorder.feedback_callback, best_effort)
            self.status_sub = self.create_subscription(UInt8, args.motor_status, self.recorder.status_callback, reliable)

    rclpy.init()
    node = HomeTestNode()
    results: list[StepResult] = []

    def spin_for(seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=min(0.05, max(0.0, deadline - time.monotonic())))

    def report(name: str, passed: bool, detail: str) -> None:
        results.append(StepResult(name, passed, detail))
        print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")

    def publish_enable(enabled: bool) -> None:
        msg = Bool(); msg.data = enabled
        node.enable_pub.publish(msg)

    def publish_twist(vx: float, wz: float) -> None:
        msg = Twist(); msg.linear.x = float(vx); msg.angular.z = float(wz)
        node.cmd_pub.publish(msg)
        node.last_cmd_publish_elapsed_s = time.monotonic() - node.recorder.started

    def drive(vx: float, wz: float, duration: float, hz: float = 20.0) -> None:
        deadline = time.monotonic() + duration
        period = 1.0 / hz
        while rclpy.ok() and time.monotonic() < deadline:
            publish_twist(vx, wz)
            rclpy.spin_once(node, timeout_sec=min(period, max(0.0, deadline - time.monotonic())))

    def latest_velocity() -> tuple[float, float] | None:
        if not node.recorder.feedback:
            return None
        row = node.recorder.feedback[-1]
        return float(row["left_velocity_rad_s"]), float(row["right_velocity_rad_s"])

    def stable_velocity() -> tuple[float, float] | None:
        recent = node.recorder.feedback[-10:]
        if not recent:
            return None
        return (sum(float(x["left_velocity_rad_s"]) for x in recent) / len(recent),
                sum(float(x["right_velocity_rad_s"]) for x in recent) / len(recent))

    try:
        deadline = time.monotonic() + args.discovery_seconds
        discovered = False
        node_seen = False
        topics_seen: set[str] = set()
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            graph_nodes = {f"/{ns.strip('/')}/{name}".replace("//", "/") if ns else f"/{name}" for name, ns in node.get_node_names_and_namespaces()}
            # normalize root node names
            node_seen = args.node_name in graph_nodes or args.node_name.lstrip("/") in {n.lstrip("/") for n in graph_nodes}
            graph_topics = {name for name, _ in node.get_topic_names_and_types()}
            topics_seen = graph_topics.intersection({args.cmd_vel, args.motor_enable, args.motor_fb, args.motor_status})
            if node_seen and len(topics_seen) == 4:
                discovered = True
                break
        report("node and four required topics discovered", discovered,
               f"node={args.node_name} seen={node_seen}; topics={sorted(topics_seen)}")

        # Disabled output check: command remains active while disabled.
        publish_enable(False)
        spin_for(0.3)
        drive(0.3, 0.0, 0.8)
        spin_for(args.settle_seconds)
        observed = stable_velocity()
        ok, detail = check_zero_pair(observed or (float("nan"), float("nan")), args.zero_tolerance)
        report("disabled motors hold zero under nonzero cmd_vel", ok, detail)

        publish_enable(True)
        spin_for(0.4)
        drive(0.3, 0.0, args.drive_seconds)
        spin_for(args.settle_seconds)
        expected = expected_wheel_speeds(0.3, 0.0, args.wheel_radius, args.wheel_base, args.left_sign, args.right_sign)
        observed = stable_velocity()
        ok, detail = check_close_pair(observed or (float("nan"), float("nan")), expected, args.velocity_tolerance)
        report("forward command wheel velocity and signs", ok, f"{detail}; expected signs=({args.left_sign:+g},{args.right_sign:+g})")

        drive(0.2, 0.5, args.drive_seconds)
        spin_for(args.settle_seconds)
        expected = expected_wheel_speeds(0.2, 0.5, args.wheel_radius, args.wheel_base, args.left_sign, args.right_sign)
        observed = stable_velocity()
        ok, detail = check_close_pair(observed or (float("nan"), float("nan")), expected, args.velocity_tolerance)
        report("turning command differential wheel speeds", ok, detail)

        drive(2.0, 0.0, args.drive_seconds)
        spin_for(args.settle_seconds)
        unsat = (2.0 / args.wheel_radius * args.left_sign, 2.0 / args.wheel_radius * args.right_sign)
        expected = expected_wheel_speeds(2.0, 0.0, args.wheel_radius, args.wheel_base, args.left_sign, args.right_sign)
        observed = stable_velocity()
        values = observed or (float("nan"), float("nan"))
        wheel_ok, wheel_detail = check_close_pair(values, expected, args.saturation_tolerance)
        scale_ok, scale_detail = check_common_scale(values, unsat, args.saturation_tolerance / MAX_WHEEL_SPEED)
        report("20 rad/s common-ratio saturation", wheel_ok and scale_ok,
               f"{wheel_detail}; expected={expected!r}; {scale_detail}")

        # Silence the command stream; wait for the 500 ms firmware watchdog and margin.
        spin_for(0.5 + args.timeout_margin)
        observed = stable_velocity()
        last_cmd = node.last_cmd_publish_elapsed_s
        if last_cmd is None:
            ok, detail = False, "no command publication timestamp recorded"
        else:
            bit_ok, bit_detail = check_timeout((value for _, value in node.recorder.status),
                                               observed or (float("nan"), float("nan")), args.zero_tolerance)
            timing_ok, timing_detail = check_timeout_timing(
                last_cmd, node.recorder.status, node.recorder.feedback,
                args.zero_tolerance, 0.5 + args.timeout_margin)
            ok, detail = bit_ok and timing_ok, f"{bit_detail}; {timing_detail}"
        report("command timeout stops wheels and sets status bit 0x20", ok, detail)

        # Re-establish a valid nonzero command, then send NaN; ignored means feedback stays at baseline.
        drive(0.2, 0.0, 0.45)
        spin_for(0.05)
        baseline = stable_velocity()
        nan_start = len(node.recorder.feedback)
        # Keep the whole probe under the 500 ms watchdog from the last valid
        # command, otherwise a correct timeout could look like NaN acceptance.
        drive(float("nan"), 0.0, 0.2)
        spin_for(0.05)
        after_rows = node.recorder.feedback[nan_start:]
        if after_rows:
            after = (sum(float(x["left_velocity_rad_s"]) for x in after_rows) / len(after_rows),
                     sum(float(x["right_velocity_rad_s"]) for x in after_rows) / len(after_rows))
        else:
            after = (float("nan"), float("nan"))
        ok, detail = check_nan_ignored(baseline or (float("nan"), float("nan")), after, args.velocity_tolerance)
        report("NaN cmd_vel is ignored", ok, f"baseline={baseline}, after_nan={after}; {detail}")

        publish_enable(False)
        spin_for(0.5)
        observed = stable_velocity()
        ok, detail = check_disabled((value for _, value in node.recorder.status),
                                    observed or (float("nan"), float("nan")), args.zero_tolerance)
        report("motors disabled at test end", ok, detail)
    except Exception as exc:
        report("test execution", False, f"{type(exc).__name__}: {exc}")
    finally:
        # Leave output disabled even on a test exception.
        try:
            publish_enable(False)
            spin_for(0.1)
        except Exception:
            pass
        summary = {
            "node": args.node_name,
            "topics": {"cmd_vel": args.cmd_vel, "motor_enable": args.motor_enable, "motor_fb": args.motor_fb, "motor_status": args.motor_status},
            "geometry": {"wheel_radius_m": args.wheel_radius, "wheel_base_m": args.wheel_base, "left_sign": args.left_sign, "right_sign": args.right_sign},
            "tolerances_rad_s": {"velocity": args.velocity_tolerance, "zero": args.zero_tolerance, "saturation": args.saturation_tolerance},
            "steps": [asdict(item) for item in results],
            "passed": bool(results) and all(item.passed for item in results),
            "feedback_samples": len(node.recorder.feedback),
            "status_samples": len(node.recorder.status),
            "status_values": [value for _, value in node.recorder.status],
        }
        _write_outputs(args.out, node.recorder, summary)
        print(f"SUMMARY {'PASS' if summary['passed'] else 'FAIL'}: {sum(r.passed for r in results)}/{len(results)} steps; output={args.out}")
        node.destroy_node()
        rclpy.shutdown()
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
