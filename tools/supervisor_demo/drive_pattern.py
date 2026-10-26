#!/usr/bin/env python3
"""Publish the constant bench-demo command and motor-enable state."""


def _ros_main():
    import rclpy
    from geometry_msgs.msg import Twist
    from rclpy.node import Node
    from std_msgs.msg import Bool

    class DrivePattern(Node):
        def __init__(self):
            super().__init__('drive_pattern')
            self.declare_parameter('forward_speed_mps', 0.3)
            self.command_pub = self.create_publisher(Twist, '/cmd_vel_teleop', 10)
            self.enable_pub = self.create_publisher(Bool, '/motor_enable', 10)
            self.enable = Bool()
            self.enable.data = True
            self.command = Twist()
            self.command.linear.x = float(self.get_parameter('forward_speed_mps').value)
            self.create_timer(0.05, self.publish_demo)

        def publish_demo(self):
            self.enable_pub.publish(self.enable)
            self.command_pub.publish(self.command)

        def disable(self):
            self.enable.data = False
            for _ in range(3):
                self.enable_pub.publish(self.enable)
                rclpy.spin_once(self, timeout_sec=0.02)

    rclpy.init()
    node = DrivePattern()
    try:
        node.enable_pub.publish(node.enable)
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.disable()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    _ros_main()
