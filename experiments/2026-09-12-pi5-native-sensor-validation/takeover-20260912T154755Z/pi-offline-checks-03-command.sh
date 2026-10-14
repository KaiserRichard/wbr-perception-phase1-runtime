set -e
cd /home/richard/wbr-runtime/wbr-runtime-20260912T160506Z
sha256sum -c SHA256SUMS
source /opt/ros/jazzy/setup.bash
export WBR_EXTRACTED=/home/richard/wbr-package-inspect/takeover-20260912T154755Z/extracted/opt/ros/jazzy
export PYTHONPATH="$WBR_EXTRACTED/lib/python3.12/site-packages:$PYTHONPATH"
export LD_LIBRARY_PATH="$WBR_EXTRACTED/lib:$LD_LIBRARY_PATH"
export AMENT_PREFIX_PATH="$WBR_EXTRACTED:$AMENT_PREFIX_PATH"
python3 wrapper_inspect.py --package-root "$WBR_EXTRACTED/share/realsense2_camera" --output wrapper-archive-inspection.json
WBR_RUN_ROS_SYNTHETIC=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s . -p 'test_*.py' -v
