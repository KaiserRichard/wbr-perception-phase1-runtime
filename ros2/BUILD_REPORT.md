# T30 build report — dependency audit and reproducible colcon build

Date: 2026-10-18. Evidence labels are explicit because this worktree has no
Pi/ROS runtime attached.

## Built

- Added ros2/build_on_pi.sh, a Bash/Pi entry point with set -euo pipefail,
  plan mode, symlinked package workspace, ORB-present/absent selection,
  MAKEFLAGS=-j2, provenance capture and PASS/FAIL/BLOCKED result.json output.
- Added ros2/tests_build/ unittest fixtures for both ORB plans, stubbed
  provenance/build execution and missing-ROS BLOCKED behavior.
- Added ros2/README.md with exact Pi commands, criteria and limitations.

No ROS build was run here: this Mac worktree does not establish a Pi build
result. The tests use stubs and are software orchestration tests only.

## Package manifest audit

### wbr_orb_node — present in this worktree

MEASURED from package.xml, CMakeLists.txt and source includes:

| Dependency | Finding | Action/status |
|---|---|---|
| ament_cmake | Build type and find_package match. | Used. |
| rclcpp | rclcpp/rclcpp.hpp, target dependency. | Used. |
| sensor_msgs | Image and IMU messages, target dependency. | Used. |
| nav_msgs | Odometry message, target dependency. | Used. |
| yaml_cpp_vendor / yaml-cpp | Vendor package is declared and found; yaml-cpp is linked directly. | Used by current CMake; verify the Jazzy vendor export on the Pi. |
| python3 | CMake invokes scripts/generate_config.py through find_package(Python3). | Declared only as build_depend; this is sufficient for generation, but an exec_depend may be needed if the generated helper is treated as a runtime-installed tool. |
| Threads | CMake uses find_package(Threads) and links Threads::Threads. | System CMake dependency, not a ROS package manifest dependency. |
| OpenCV, Eigen3 | Used only when WITH_ORB_SLAM3=ON; CMake finds and links them. | Missing conditional/native build documentation in package.xml; the ORB-enabled Pi environment must provide them. Because this is optional and the package manifest is not edited by T30, it is reported as a defect/risk. |
| ORB-SLAM3 | System.h and orb_engine.cpp are compiled only when enabled. | No ROS package name is assumed; native root is supplied by the build script. |

No message_filters, launch_ros, geometry_msgs, tf2, tf2_ros, or
realsense2_camera import/include is present in this package. They are not
missing dependencies for the current code. The package subscribes to ROS
messages directly and does not launch the RealSense driver.

Potential manifest/CMake defect: yaml_cpp_vendor is an ament vendor package,
while the CMake target also calls find_package(yaml-cpp) and links yaml-cpp;
this coupling should be confirmed against the installed Jazzy export. It passed
only source-level audit here (UNKNOWN at runtime).

No declared ROS dependency is unused by the current source/CMake audit.
python3 is build-time only; yaml_cpp_vendor is consumed by CMake but its
separate yaml-cpp export remains an installation-time compatibility risk.

### wbr_d435i_bringup and wbr_perception_bringup

UNKNOWN / NOT PRESENT: neither package directory or package.xml exists in this
ticket worktree (git ls-files ros2/ and filesystem inspection on 2026-10-18 found
only ros2/wbr_orb_node). Therefore their imports, launch files and manifests
cannot be audited here, and this ticket does not invent dependencies for
packages that are not checked out. When they land, audit at minimum:

- wbr_d435i_bringup: ament_python, rclpy if Python nodes exist, launch,
  launch_ros, and realsense2_camera if its launch descriptions include the
  RealSense driver. sensor_msgs is needed only when Python code imports its
  message types.
- wbr_perception_bringup: ament_python, launch, launch_ros, and the actual
  package names imported by its launch/nodes; add wbr_d435i_bringup and
  wbr_orb_node only if the launch files reference those packages. Do not add
  message_filters unless code imports it.

Those are audit targets, not claims about absent source. The build script will
discover and link them automatically once their direct directories contain a
valid package.xml.

## Test results

Run from the repository root:

~~~bash
python3 -m unittest discover -s ros2/tests_build -p 'test_*.py' -v \
  > ros2/tests_build/tests/last-run.log 2>&1
bash -n ros2/build_on_pi.sh
~~~

The saved ros2/tests_build/tests/last-run.log is the authoritative local test
output. The suite covers ORB-present and ORB-absent plan output, stubbed
provenance and build/test commands, the real saved ORB Pi-build fixture excerpt,
and missing Jazzy setup returning BLOCKED with exit code 2.

Not verified: actual colcon discovery, ROS 2 Jazzy package resolution,
OpenCV/Eigen/ORB ABI compatibility, ARM64 linkability, hardware, camera,
thermal, storage, timing, or estimator correctness. The real ORB evidence
fixture is SOURCE-SUPPORTED input for assertions, not a new build result.

Proposed commit message: Add reproducible Pi ROS 2 colcon build audit

