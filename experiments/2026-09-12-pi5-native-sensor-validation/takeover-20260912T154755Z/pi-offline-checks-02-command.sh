set -e
cd /home/richard/wbr-runtime/wbr-runtime-20260912T160144Z
sha256sum -c SHA256SUMS
source /opt/ros/jazzy/setup.bash
WBR_RUN_ROS_SYNTHETIC=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_ros_offline -v
