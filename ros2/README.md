# Native Pi ROS 2 workspace build

build_on_pi.sh builds every direct ROS 2 package currently present under
ros2/ in a separate colcon workspace. The workspace contains symlinks back to
this checkout, so source edits remain visible without copying package files.

This is a software build check, not a Pi gate PASS. It does not prove camera
access, D435i rates, clock mapping, ORB tracking quality, power stability,
thermal headroom, or STM32 integration.

## Exact Pi command

On the Pi, with ROS 2 Jazzy and the native ORB build already available:

~~~bash
cd ~/wbr-perception-phase1-runtime
bash ros2/build_on_pi.sh \
  --workspace ~/wbr-colcon-ws \
  --outdir ~/wbr-evidence/ros2-colcon-$(date -u +%Y%m%dT%H%M%SZ) \
  --orb-root ~/orbslam3/ORB_SLAM3
~~~

The script requires /opt/ros/jazzy/setup.bash, colcon, CMake, GCC,
sha256sum, Git and Python 3. It sets MAKEFLAGS=-j2 for the Pi's measured
RAM/thermal constraints. It runs colcon test for discovered packages with a
non-empty tests/ directory.

Use --plan to print the source, symlink, build and test commands without
checking ROS or changing the workspace:

~~~bash
bash ros2/build_on_pi.sh --plan --orb-root ~/orbslam3/ORB_SLAM3
~~~

The ORB library decision is based on
<orb-root>/lib/libORB_SLAM3.so. When present, only wbr_orb_node receives
-DWITH_ORB_SLAM3=ON -DORB_SLAM3_ROOT=<orb-root>; when absent it receives
-DWITH_ORB_SLAM3=OFF and the reason is printed and recorded. Other packages
are built in a separate colcon invocation so they do not receive ORB CMake
flags.

## Evidence and criteria

The output directory contains result.json, command logs, provenance.json
and provenance.log. result.json uses the common PASS/FAIL/BLOCKED contract:

- ros_setup: Jazzy setup exists and can be sourced.
- provenance: Git commit, colcon, CMake, GCC and ORB library SHA-256 are
  recorded; an absent ORB library is recorded as null, not silently guessed.
- workspace_links: each discovered package is linked into the colcon source
  workspace.
- build: all discovered packages complete colcon build --symlink-install.
- tests: all discovered applicable package tests complete colcon test and
  colcon test-result; zero discovered tests is reported explicitly.

BLOCKED means a required ROS/tool prerequisite is absent. A successful run
only proves that the selected software built and its available tests ran on
the host where the command was executed. Fixtures and stubbed commands in
tests_build/ exercise orchestration paths; they are not hardware evidence.

