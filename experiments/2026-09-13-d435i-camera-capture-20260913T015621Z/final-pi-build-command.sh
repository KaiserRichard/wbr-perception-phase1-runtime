set -e
cd /home/richard/wbr-runtime/wbr-runtime-20260913T021130Z
sha256sum -c SHA256SUMS > /home/richard/wbr-evidence/2026-09-13-d435i-camera-capture-20260913T015621Z/final-bundle-verification.txt
python3 bundle_runtime.py verify . >> /home/richard/wbr-evidence/2026-09-13-d435i-camera-capture-20260913T015621Z/final-bundle-verification.txt
source /opt/ros/jazzy/setup.bash
for WBR_PROGRAM in camera_metadata sample_ir_checked; do
  g++ -O2 -std=c++17 -Wall -Wextra "$WBR_PROGRAM.cpp" -I/opt/ros/jazzy/include -L/opt/ros/jazzy/lib/aarch64-linux-gnu -Wl,-rpath,/opt/ros/jazzy/lib/aarch64-linux-gnu -lrealsense2 -o "$WBR_PROGRAM" > /home/richard/wbr-evidence/2026-09-13-d435i-camera-capture-20260913T015621Z/final-$WBR_PROGRAM-compile.log 2>&1
done
sha256sum camera_metadata sample_ir_checked > /home/richard/wbr-evidence/2026-09-13-d435i-camera-capture-20260913T015621Z/final-binary-hashes.txt
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s . -p 'test_*.py' -v > /home/richard/wbr-evidence/2026-09-13-d435i-camera-capture-20260913T015621Z/pi-final-tests.log 2>&1
