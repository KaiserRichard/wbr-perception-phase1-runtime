set -e
cd /home/richard/wbr-runtime/wbr-runtime-20260912T160003Z
source /opt/ros/jazzy/setup.bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s . -p 'test_*.py' -v
g++ -O2 -std=c++17 -Wall -Wextra sample_ir_checked.cpp -I/opt/ros/jazzy/include -L/opt/ros/jazzy/lib/aarch64-linux-gnu -Wl,-rpath,/opt/ros/jazzy/lib/aarch64-linux-gnu -lrealsense2 -o sample_ir_checked
sha256sum sample_ir_checked
WBR_RUN_ROS_SYNTHETIC=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_ros_offline -v
