set -e
mkdir -p /home/richard/wbr-package-inspect
mkdir /home/richard/wbr-package-inspect/takeover-20260912T154755Z
cd /home/richard/wbr-package-inspect/takeover-20260912T154755Z
apt download ros-jazzy-realsense2-camera=4.58.4-1noble.20260902.181721 ros-jazzy-realsense2-camera-msgs=4.58.4-1noble.20260902.134137
sha256sum *.deb
mkdir extracted
for archive in *.deb; do dpkg-deb -x "$archive" extracted; done
find extracted -name '*python*' -o -name '*typesupport*' -o -name package.xml
