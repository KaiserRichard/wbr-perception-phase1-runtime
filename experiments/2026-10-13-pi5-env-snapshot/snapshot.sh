#!/bin/bash
# Read-only environment snapshot of wbr-pi5. Makes no changes to system state.
sec(){ echo; echo "########## $1"; }
sec "identity/time"; hostname; date -u; timedatectl 2>&1; uptime
sec "os/kernel"; cat /etc/os-release; uname -a; cat /proc/cmdline
sec "hardware"; cat /proc/device-tree/model; echo; free -h; nproc; vcgencmd get_throttled; vcgencmd measure_temp; vcgencmd measure_clock arm; cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
sec "storage"; lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINT,MODEL,TRAN; df -h; findmnt /
sec "boot config"; sudo rpi-eeprom-config; grep -vE '^\s*(#|$)' /boot/firmware/config.txt
sec "usb"; lsusb; lsusb -t
sec "video devices"; ls -l /dev/video* 2>&1; cat /etc/udev/rules.d/99-wbr-d435i.rules
sec "dmesg realsense/usb tail"; sudo dmesg | grep -iE 'realsense|8086|uvc|usb .*(new|disconnect)|xhci' | tail -40
sec "librealsense"; which rs-enumerate-devices realsense-viewer 2>&1; dpkg -l | grep -iE 'realsense|librealsense' ; rs-enumerate-devices -s 2>&1 | head -30
sec "ros"; ls /opt/ros; dpkg -l | grep -E '^ii\s+ros-jazzy-(realsense|ros-base|desktop|rosbag2|image|cv-bridge|tf2|imu|rmw)' | awk '{print $2, $3}'
sec "ros env"; bash -lc 'source /opt/ros/jazzy/setup.bash && printenv | grep -E "^(ROS|RMW|AMENT)" ; ros2 pkg list 2>/dev/null | grep -iE "realsense|rosbag2_storage|imu" '
sec "workspaces"; ls -la ~/ros2_ws ~/ros2_ws/* 2>&1 | head -30
sec "orb-slam3"; find / -xdev -maxdepth 5 -iname '*orb*slam*' 2>/dev/null | head -20
sec "wbr dirs"; for d in ~/wbr-*; do echo "--- $d"; (cd $d && find . -maxdepth 3 | head -60); done
sec "wbr git"; for d in ~/wbr-*; do [ -d $d/.git ] && (cd $d && echo "--- $d" && git status -sb | head -10 && git log --oneline -5); done
sec "n3 evidence"; find ~ -xdev -iname '*n3*' 2>/dev/null | head -50; find ~ -xdev \( -name 'metadata.yaml' -o -name '*.db3' -o -name '*.mcap' \) 2>/dev/null | head -30
sec "python"; python3 --version; python3 -c 'import pyrealsense2 as rs; print("pyrealsense2", rs.__version__)' 2>&1
sec "running services"; systemctl list-units --type=service --state=running --no-legend | awk '{print $1}'
sec "custom units/sudoers"; ls /etc/systemd/system/*.service; ls /etc/sudoers.d
sec "bash history (tail)"; tail -80 ~/.bash_history
