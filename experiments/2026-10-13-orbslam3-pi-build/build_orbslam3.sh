#!/bin/bash
# Build Pangolin + ORB-SLAM3 on wbr-pi5 (Pi 5, 4 GB, Ubuntu 24.04, ROS 2 Jazzy binary).
# Runs detached on the Pi; all output under $EV. Does not touch the repo checkout, camera, udev or boot config.
set -euo pipefail
EV=$HOME/wbr-evidence/2026-10-13-orbslam3-build
mkdir -p "$EV"
exec > >(tee -a "$EV/build.log") 2>&1
echo "START $(date -u +%FT%TZ)"

# 1. power/thermal/memory logger (every 5 s) for the whole build
cat > "$EV/wbr-power-logger.sh" <<'LOG'
#!/bin/bash
while true; do
  echo "$(date -u +%FT%TZ) up=$(cut -d' ' -f1 /proc/uptime) $(vcgencmd get_throttled) $(vcgencmd measure_temp) $(vcgencmd measure_clock arm) memavail_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo) swapfree_kb=$(awk '/SwapFree/{print $2}' /proc/meminfo)"
  sleep 5
done
LOG
chmod +x "$EV/wbr-power-logger.sh"
pgrep -f wbr-power-logger.sh >/dev/null || nohup "$EV/wbr-power-logger.sh" >> "$EV/power.log" 2>&1 < /dev/null &

# 2. dependencies
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libboost-serialization-dev libglew-dev libepoxy-dev \
  libgl1-mesa-dev libwayland-dev libxkbcommon-dev wayland-protocols git
dpkg -l libboost-serialization-dev libglew-dev libepoxy-dev | awk '/^ii/{print $2,$3}' > "$EV/apt-versions.txt"

# 3. temporary swap (not in fstab)
if ! swapon --show | grep -q swapfile-orbslam3; then
  sudo fallocate -l 4G /swapfile-orbslam3 && sudo chmod 600 /swapfile-orbslam3
  sudo mkswap /swapfile-orbslam3 >/dev/null && sudo swapon /swapfile-orbslam3
fi
swapon --show

# 4. Pangolin (pinned)
mkdir -p ~/orbslam3 && cd ~/orbslam3
[ -d Pangolin ] || git clone --depth 1 --branch v0.9.1 https://github.com/stevenlovegrove/Pangolin.git
cd Pangolin && git rev-parse HEAD > "$EV/pangolin-commit.txt"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_PANGOLIN_PYTHON=OFF -DBUILD_EXAMPLES=OFF -DBUILD_TOOLS=OFF \
  -DBUILD_TESTS=OFF -DCMAKE_INSTALL_PREFIX=/usr/local
T0=$(date +%s); cmake --build build -j2; echo "pangolin_build_s=$(( $(date +%s)-T0 ))"
sudo cmake --install build && sudo ldconfig

# 5. ORB-SLAM3 copy (repo checkout left untouched)
cd ~/orbslam3
SRC=$HOME/wbr-perception-phase1-runtime/third_party/ORB_SLAM3
if [ ! -d ORB_SLAM3 ]; then
  cp -a "$SRC" ORB_SLAM3
  (cd "$SRC" && git rev-parse HEAD) > "$EV/orbslam3-source-commit.txt"
  rm -f ORB_SLAM3/.git   # submodule gitlink file; the copy is not a repo
  cd ORB_SLAM3 && git init -q && git add -A && git -c user.email=b@l -c user.name=build commit -qm "pristine 4452a3c copy"
  # minimal patch: C++17 (Pangolin 0.9 requires it), drop the C++11/14 check
  sed -i 's/-std=c++11/-std=c++17/g; s/-std=c++14/-std=c++17/g' CMakeLists.txt Thirdparty/*/CMakeLists.txt
  sed -i 's/CHECK_CXX_COMPILER_FLAG("-std=c++1[14]" COMPILER_SUPPORTS_CXX1[14])/set(COMPILER_SUPPORTS_CXX11 ON)/' CMakeLists.txt
  sed -i 's/-march=native//g' CMakeLists.txt Thirdparty/*/CMakeLists.txt
  git diff > "$EV/orbslam3-cxx17.patch"; git commit -qam "c++17 patch"
fi
cd ~/orbslam3/ORB_SLAM3
for d in DBoW2 g2o Sophus; do
  extra=""; [ "$d" = Sophus ] && extra="-DBUILD_TESTS=OFF -DBUILD_EXAMPLES=OFF"  # Sophus tests fail -Werror=array-bounds on GCC 13 aarch64; ORB-SLAM3 uses headers only
  cmake -S Thirdparty/$d -B Thirdparty/$d/build -DCMAKE_BUILD_TYPE=Release $extra
  cmake --build Thirdparty/$d/build -j2
done
[ -f Vocabulary/ORBvoc.txt ] || tar -xf Vocabulary/ORBvoc.txt.tar.gz -C Vocabulary
T0=$(date +%s)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/opt/ros/jazzy
cmake --build build -j2 || { echo "j2 failed, retry j1"; cmake --build build -j1; }
echo "orbslam3_build_s=$(( $(date +%s)-T0 ))"
ls -la lib Examples/Stereo-Inertial/ Examples/Monocular-Inertial/ | tee "$EV/artifacts.txt"
echo "DONE $(date -u +%FT%TZ)"
