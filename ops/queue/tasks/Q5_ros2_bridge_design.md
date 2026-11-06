# Q5 — ROS 2 output bridge design + skeleton, dir: tools/ros2_bridge/
Read queue/tasks/COMMON_QUEUE.md first. ROS 2 is NOT installed here. Write DESIGN.md: node that consumes EstimateSnapshot
(tools/vio_adapter if present, else the documented struct) and publishes nav_msgs/Odometry-free outputs first:
geometry_msgs/PoseStamped in slam_world, diagnostic_msgs via diagnostic_updater, TF policy per R1 (who owns map->odom,
odom->base_link; bridge must not publish odom until a continuous local source exists), QoS per topic, replay /clock rules,
covariance policy (no invented covariance), how a stale/reset snapshot is handled, and what it must never do (restamp stale
poses, affect MCU authority). Cite REP-103/105, Jazzy QoS docs, diagnostic_updater, nav_msgs definitions. Add a rclcpp
skeleton (package.xml, CMakeLists.txt, src) that is plausible for Jazzy but clearly marked UNBUILT; a pure-python test that
checks the snapshot->message field mapping logic (separated into a ROS-free module).
