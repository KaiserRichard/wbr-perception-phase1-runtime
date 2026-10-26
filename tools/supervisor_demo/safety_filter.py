#!/usr/bin/env python3
"""Bench-demo command filter. This is not a robot safety function."""
from dataclasses import dataclass
import time


NONE = 0
JUMP_CANDIDATE = 1
STOP_CANDIDATE = 2
ADVISORY_NAMES = {
    NONE: "NONE",
    JUMP_CANDIDATE: "JUMP_CANDIDATE",
    STOP_CANDIDATE: "STOP_CANDIDATE",
    3: "UNCERTAIN",
}


@dataclass(frozen=True)
class FilterResult:
    linear_x: float
    angular_z: float
    state: str
    reason: str


def decide(linear_x, angular_z, advisory_code, distance_m, advisory_age_s,
           stop_distance_m=1.0, slow_speed=0.15, stale_after_s=0.3):
    """Apply the documented demo policy to one command and advisory sample.

    Forward speed is clamped at zero for stale data and nearby STOP_CANDIDATE;
    rotation is retained. JUMP_CANDIDATE limits positive forward speed only.
    """
    name = ADVISORY_NAMES.get(advisory_code, "UNKNOWN")
    if advisory_age_s is None or advisory_age_s > stale_after_s:
        return FilterResult(0.0 if linear_x > 0.0 else linear_x, angular_z,
                            "STALE", "advisory stale; forward motion clamped")
    if (advisory_code == STOP_CANDIDATE and distance_m is not None
            and distance_m <= stop_distance_m):
        return FilterResult(0.0 if linear_x > 0.0 else linear_x, angular_z,
                            name, "near STOP_CANDIDATE; forward motion clamped")
    if advisory_code == JUMP_CANDIDATE:
        return FilterResult(min(linear_x, slow_speed) if linear_x > 0.0 else linear_x,
                            angular_z, name, "jump candidate (would ask operator)")
    return FilterResult(linear_x, angular_z, name, "pass through")


def _ros_main():
    import rclpy
    from geometry_msgs.msg import Twist
    from rclpy.node import Node
    from std_msgs.msg import Float64MultiArray, String

    class SafetyFilter(Node):
        def __init__(self):
            super().__init__('safety_filter')
            self.declare_parameter('stop_distance_m', 1.0)
            self.declare_parameter('slow_speed', 0.15)
            self.declare_parameter('stale_after_s', 0.3)
            self.last_advisory = None
            self.last_received = None
            self.last_jump_logged = False
            self.create_subscription(Twist, '/cmd_vel_teleop', self.on_command, 10)
            self.create_subscription(Float64MultiArray, '/terrain_advisory', self.on_advisory, 10)
            self.command_pub = self.create_publisher(Twist, '/cmd_vel', 10)
            self.state_pub = self.create_publisher(String, '/safety_filter/state', 10)

        def on_advisory(self, msg):
            if len(msg.data) < 2:
                self.get_logger().warning('ignoring malformed /terrain_advisory')
                return
            code, distance = int(msg.data[0]), float(msg.data[1])
            if code not in ADVISORY_NAMES:
                self.get_logger().warning(f'ignoring unknown advisory code {code}')
                return
            self.last_advisory = (code, distance if distance >= 0.0 else None)
            self.last_received = time.monotonic()

        def on_command(self, incoming):
            now = time.monotonic()
            age = None if self.last_received is None else now - self.last_received
            code, distance = self.last_advisory if self.last_advisory is not None else (NONE, None)
            result = decide(
                incoming.linear.x, incoming.angular.z, code, distance, age,
                self.get_parameter('stop_distance_m').value,
                self.get_parameter('slow_speed').value,
                self.get_parameter('stale_after_s').value,
            )
            outgoing = Twist()
            outgoing.linear.x = result.linear_x
            outgoing.angular.z = result.angular_z
            self.command_pub.publish(outgoing)
            state = String()
            state.data = f'{result.state}: {result.reason}'
            self.state_pub.publish(state)
            is_jump = code == JUMP_CANDIDATE and age is not None and age <= self.get_parameter('stale_after_s').value
            if is_jump and not self.last_jump_logged:
                self.get_logger().warning('jump candidate (would ask operator)')
            self.last_jump_logged = is_jump

    rclpy.init()
    node = SafetyFilter()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    _ros_main()
