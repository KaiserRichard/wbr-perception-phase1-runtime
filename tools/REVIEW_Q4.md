# Q4 independent review and hardening

Reviewed 2026-10-14. **MEASURED:** all nine tool directories present were reviewed:
take_tools, calib_tools, link_proto, frames, clockmap, vio_adapter,
runtime_observer, run_harness, ros2_bridge. trajectory_eval is absent here and
excluded from review. The harness tests invoke the existing reference evaluator;
its implementation was not reviewed or changed.

Read COMMON_QUEUE.md, PROPOSAL.md, J1_components.md, J2_architecture.md and tool
READMEs. Q4 allows implementation/test edits only in take_tools, calib_tools,
link_proto, frames and clockmap; additional tools received read-only review.
Three confirmed numeric bugs were fixed with new failing-then-passing regressions.
Five findings remain OPEN outside that edit scope. No style refactoring.
Severity below is an INFERRED engineering assessment, not a hardware gate result.

## Findings, ranked by severity

### High — OPEN: Python ROS gate accepts NaN clock evidence

**MEASURED:** `ros2_bridge/mapping.py:118` checks clock revision, age and
uncertainty using comparisons without enforcing integer types. Each of
`age_upper_ns=NaN`, `uncertainty_ns=NaN`, and `revision=NaN` independently yields
`pose_published` for an otherwise valid fresh snapshot. NaN comparisons are false,
so unknown age/uncertainty bypass rejection. Python dataclass annotations do not
validate values. The C++ counterpart has integer fields and cannot represent
these inputs. JSON parsers may admit NaN, and direct callers certainly can.

Reproduced with the existing independent fixtures:

```python
from tools.ros2_bridge.tests.test_mapping import snapshot, clock, gate
s = snapshot()
for field in ('age_upper_ns', 'uncertainty_ns', 'revision'):
    print(field, gate().advance(s, clock(s, **{field: float('nan')}))[1])
# All three: pose_published
```

Missing tests: noninteger/bool/NaN/infinite clock fields, configuration budgets,
and snapshot counters. Require explicit integer/range validation before state
mutation and gate decisions. The observed bypass is in the ROS-free Python core;
actual ROS execution remains UNKNOWN. No edit authorized in this directory.

### High — OPEN: ROS skeleton does not implement its pause/forward-seek rules

**MEASURED source review:** `ros2_bridge/src/bridge_node.cpp:55` latches only
backward time changes and changes to use_sim_time. With a nonzero paused ROS
clock, a newly submitted snapshot with fresh evidence and `ros_ns <= ros_now`
can reach publication. Equal ROS time is not a suppression condition. The wall
diagnostics timer observes a pause only to force diagnostics. Forward jumps do
not invalidate the generation, evidence or gate.

DESIGN.md requires pause to stop poses and forward seek to require fresh
generation/rebind. [ROS time design, source lines 61–103](https://github.com/ros2/design/blob/gh-pages/articles/130_ros_time.md#L61-L103)
supports explicit pause and jump handling. This is a source-confirmed missing
policy, not a claimed ROS runtime failure. The executable has no connected
producer and is UNBUILT. Missing tests: paused nonzero clock with fresh ingress,
forward seek, clock-source replacement, and resume/rebind. No edit authorized.

### Medium — OPEN: harness treats a missing declared extra artifact as success

**MEASURED:** `run_harness/harness.py:395` records missing extra trajectories in
receipt.errors, but neither changes status nor sets analysis_failed. With the
success fixture and `extra_trajectories: [missing.txt]`, the receipt contains
`missing artifact: missing.txt`, while summary reports OK=1,
analysis_failures=0, input_change_runs=0. Those values satisfy main's exit-0
predicate. A requested artifact/hash can therefore disappear behind success.

```python
from tools.run_harness.tests.test_harness import HarnessTests
t = HarnessTests(); t.setUp()
try:
    t.spec['extra_trajectories'] = ['missing.txt']
    summary, receipt = t.run_harness()
    print(summary['status_counts'], summary['analysis_failures'], receipt['errors'])
finally:
    t.doCleanups()
```

Missing test: missing or escaping declared extra trajectory must cause batch
failure while preserving receipts and the original process result. No edit authorized.

### Medium — OPEN: harness can finish a trial with descendants still running

**MEASURED:** `run_harness/harness.py:290` waits for the process leader only.
Process-group cleanup runs only when that wait times out. A leader spawning a
child and exiting successfully returns exit_code=0/timed_out=False while the
child is alive. A child delaying 0.2 s wrote `child_finished` after launch returned
in the review probe; it then exited normally. This can overlap repeats or mutate
logs/artifacts after hashes are recorded. A child need not escape its process group.

[Python 3.11 subprocess documentation, extracted lines 290–299 and 400–405](https://docs.python.org/3.11/library/subprocess.html#subprocess.Popen.wait)
defines a new session and waiting for the child process, not all descendants.
Missing test: leader exit with live descendants, verifying group cleanup or
explicit rejection before artifact collection/next repeat. No edit authorized.

### Medium — FIXED: finite calibration doubles overflow/underflow ORB fields

**MEASURED:** prior ORB export accepted gyro noise 1e40 and produced outputs;
the native float cannot retain it. Noise 1e-50 becomes zero, removing the
validated nonzero density. Focal length 1e40 has the same overflow problem.
[Settings.cc, lines 184–225 and 414–423](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/src/Settings.cc#L184-L225)
reads float fields; emitted matrices declare float32 storage.

`calib_tools/calib_convert.py:266` now checks emitted real fields and transform
matrices for nonfinite float32 conversion and nonzero-to-zero underflow before
creating any output. Regression:
`test_orb_rejects_values_that_overflow_or_underflow_native_float`, failed before,
passed after. The guard checks storage representation, not physical plausibility
or all downstream ORB arithmetic. OpenVINS outputs retain their separate path.

### Medium — OPEN: optional ORB IMU boundary narrows doubles without a guard

**SOURCE-SUPPORTED:** [ImuTypes.h, lines 45–58](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/include/ImuTypes.h#L45-L58)
accepts float motion components and double seconds. Adapter append accepts any
finite double. `vio_adapter/orb_engine.cpp:26` passes those doubles to float
constructor arguments without checking representability; e.g. 1e40 is accepted
upstream but exceeds float range. Out-of-range narrowing is not a qualified
finite engine measurement. Missing test: oversized finite motion at the actual
ORB boundary, with an explicit rejection/FAULT policy. Source path inspected;
the optional binding was not compiled or executed, so runtime behavior is UNKNOWN.
No edit authorized in this directory.

### Low — FIXED: trajectory velocity overflow was marked valid

**MEASURED:** finite translations -1e308 and +1e308 at adjacent ns, or 0 and
1e308, yielded infinite backward differences with velocity_valid=true from the
library. CLI serialization rejected infinity later, but library consumers could
receive it as valid. `frames/frames.py:157` now rejects nonfinite computed velocity
before emitting the result. Regression:
`test_velocity_overflow_is_rejected_before_valid_output`, failed before,
passed after. Ordinary lever-arm, frame, epoch and velocity behavior still passes.

### Low — FIXED: IMU interpolation overflowed a finite convex result

**MEASURED:** accel endpoints -1e308 and +1e308 at 0/10 ms, with gyro at
0/5/10 ms, previously produced NaN/inf/inf through `x+(y-x)*alpha`.
The expected convex values are -1e308/0/+1e308. `take_tools/take_tools.py:403`
uses convex weights, preserving endpoints without overflowing the subtraction.
Regression: `test_finite_extreme_accel_interpolation_preserves_endpoints`, failed
before, passed after. These extreme values are parser robustness fixtures, not
physically plausible SDK observations. No raw samples or stamps are altered.

## Conventions re-derived and rejected suspicions

**SOURCE-SUPPORTED / NOT-A-BUG, calibration:**
[Kalibr yaml-formats, extracted lines 154–164 and 199–213](https://github.com/ethz-asl/kalibr/wiki/yaml-formats)
defines IMU-to-camera extrinsics, previous-to-next camera stereo extrinsics,
positive additive camera-to-IMU timeshift, and continuous noise. Inversion
requires transposed rotation and rotated negative translation. The converter
uses both inverses correctly. ORB
[Settings.cc lines 485–525](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/src/Settings.cc#L485-L525)
inverts stereo geometry for rectification and adjusts camera-to-IMU rotation.
[Tracking.cc lines 603–614](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/src/Tracking.cc#L603-L614)
scales copied densities/walks internally. No double discretization was found.
OpenVINS calibration passthrough/equal-shift restriction is consistent with
its pinned loader; actual native loading remains UNKNOWN.

**SOURCE-SUPPORTED / NOT-A-BUG, take_tools:**
[librealsense v2.58.1 ros2_writer.cpp lines 124–195, 240–270](https://github.com/realsenseai/librealsense/blob/v2.58.1/src/media/ros2/ros2_writer.cpp#L124-L270)
creates separate gyro/accel Imu vectors and metadata with original SDK
milliseconds/domain. Decoder vector slices are correct: quaternion+covariance
consume 13 doubles before gyro, and 25 before accel. Writer/header time does
not establish capture time. Metadata decimal conversion preserves the printed
value, not precision lost by upstream formatting. Strict times-file IMU bounds
avoid the inspected EuRoC loader's unbounded cursor endpoints. Diagnostic mode
still suppresses cross-domain/order-invalid derived IMU and replay times.

**SOURCE-SUPPORTED / NOT-A-BUG, frames:**
[REP-103 source lines 39–75, 95–124](https://github.com/ros-infrastructure/rep/blob/master/rep-0103.rst#L39-L124)
gives SI and optical/body axes;
[REP-105 source lines 46–76](https://github.com/ros-infrastructure/rep/blob/master/rep-0105.rst#L46-L76)
requires odom continuity. Optical basis conversion and
T_world_base=T_world_sensor*inverse(T_base_sensor) are correct. SDK column-major
rotation is explicitly reshaped. Reset/map segmentation prevents cross-epoch
differencing; domain changes are rejected even at reset. Decimal text conversion
preserves int64 ns. slam_world diagnostics make no continuous odom claim.

**SOURCE-SUPPORTED / NOT-A-BUG, link_proto:**
[RFC 3720 section 12.1, text lines 9346–9395, appendix B.4 lines 10715–10765](https://www.rfc-editor.org/rfc/rfc3720.txt)
specifies the Castagnoli generator/complement and independent vectors. Reflection
gives 0x82f63b78; init/final XOR agree. **MEASURED:** Python matched all four
32-byte RFC vectors (8a9136aa, 62a8ab43, 46dd794e, 113fdb5c), beyond the suite's
123456789 check and C/Python golden packets.
[Cheshire/Baker COBS paper, pages 3–5, table 1 and terminal-block discussion](https://www.stuartcheshire.org/papers/COBSforToN.pdf)
supports 254-byte runs without implied zero. The explicit final empty block
is a valid unoptimized encoding, not an off-by-one corruption. Packet caps are
below 254 bytes. Modular sequence/timer half-range checks, conservative ns-to-us
rounding, frozen estimate age and reference lease handling match SPEC.md.
Caller observation gaps/full missed wraps remain explicit assumptions.

**SOURCE-SUPPORTED / NOT-A-BUG, clockmap:**
[librealsense global_timestamp_reader.cpp source lines 455–472, 523–526](https://github.com/realsenseai/librealsense/blob/v2.58.4/src/global_timestamp_reader.cpp#L455-L526)
maps hardware time toward OS system time, not host steady time. The analyzer's
UTC/SDK comparison is explicitly a proxy. Integer epochs are centered before
float fitting. Re-deriving causal exchange inequalities yields
t3-rate*t4 <= offset <= t2-rate*t1, consistent with the rate bound and conditional
extrapolation uncertainty. No confirmed error found in forward/inverse mapping,
session invalidation or tick unwrap. Unknown delays/hidden steps/full missed
wraps cannot be qualified by these tests.

**SOURCE-SUPPORTED / NOT-A-BUG, vio_adapter:**
[System.cc lines 316–325](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/src/System.cc#L316-L325)
returns Tcw; binding inversion is correct.
[Tracking.cc lines 1643–1665](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/src/Tracking.cc#L1643-L1665)
retains the trailing IMU endpoint. Sending each endpoint once agrees with source
intent, although ORB's tolerance-based integration has not been run here.
Gap rejection keeping the watermark is documented deliberate recovery policy.
Stock MapChanged is not a complete map/reset history. Raw versus rectified
camera mount conventions require explicit integration validation; settings and
adapter labels alone do not qualify that alignment.

**SOURCE-SUPPORTED / NOT-A-BUG, runtime_observer:**
[Linux v6.8 proc/stat.c lines 119–128](https://github.com/torvalds/linux/blob/v6.8/fs/proc/stat.c#L119-L128)
supports counter ordering; guest counters are not counted twice. Process stat
offsets correspond to utime/stime/starttime; PID reuse and missing counters are
handled. Durations subtract integers within a host session; source ages require
identity/mapping. Ring overwrite/contention losses are counted. COMPLETE means
zero recorded observer loss, not complete lifecycle/input coverage, as documented.
No confirmed implementation bug found. Real Pi resource and overhead checks,
clock-read failure injection, and hardware timing remain unverified.

**NOT-A-BUG, run_harness and ros2_bridge:** raw world-to-sensor normalization,
matrix-to-xyzw conversion, exact ns text, observed epoch splitting and failed
trial denominators are covered. Absence of covariance, mounted body pose, odom
and TF in the bridge is intentional. ROS PoseStamped defines a header and pose
[Jazzy message source lines 1–4](https://github.com/ros2/common_interfaces/blob/jazzy/geometry_msgs/msg/PoseStamped.msg#L1-L4).
Finite covariance metadata is not a covariance qualification. Additional OPEN
issues above do not invalidate the existing synthetic convention tests.

## Validation commands and results

**MEASURED:** Python 3.11.0rc2; Apple clang 17.0.0; macOS x86_64.
Each command below was run from repository root with
`PYTHONDONTWRITEBYTECODE=1`. All exited 0, both before new regressions and after
fixes. Logs for this session: /tmp/q4-baseline-{0..8}.log and
/tmp/q4-final-{0..8}.log, ordered as the table.

| Exact command | Baseline | Final |
|---|---:|---:|
| python3 -m unittest discover -s tools/take_tools/tests -v | 19 | 20 |
| python3 -m unittest discover -s tools/calib_tools/tests -v | 15 | 16 |
| python3 -m unittest discover -s tools/frames/tests -v | 10 | 11 |
| python3 -m unittest discover -s tools/clockmap/tests -v | 37 | 37 |
| make -C tools/link_proto test | C assertions + 4 Python | same |
| make -C tools/vio_adapter test | 11 C++ fixture groups + 4 Python | same |
| make -C tools/runtime_observer test | C++ recorder checks + 20 Python | same |
| python3 -m unittest discover -s tools/run_harness/tests -v | 17 | 17 |
| make -C tools/ros2_bridge test | C++ core + 18 Python, parity enabled | same |

Final Python total: **147 passed**, zero failures/skips. C/C++ targets passed.
The three targeted new tests failed before fixes and passed afterward:

```sh
python3 -m unittest discover -s tools/calib_tools/tests -k native_float -v
python3 -m unittest discover -s tools/frames/tests -k velocity_overflow -v
python3 -m unittest discover -s tools/take_tools/tests -k extreme_accel -v
```

**MEASURED, read-only real-data checks:** called take_tools.audit on
`/Users/quockaiser/Desktop/Research/wbr-data/2026-10-14-d435i-ramtest15s/take/stereo_imu.db3`:
structural PASS, global_time only, IR1=447, IR2=447, gyro=2971, accel=1507,
447 accepted stereo pairs. Called clockmap.analyze_timestamps on adjacent
timestamps.csv: Accel=1506, Gyro=2971, IR1=445, IR2=445, one diagnostic segment
each. No raw data copied/exported into this repo; no engine execution implied.

**UNKNOWN / NOT verified:** ORB/OpenVINS native calibration loading, optional
ORB binding compilation, actual ROS package compilation/runtime, camera/Pi/MCU,
mount calibration, continuous odom, true clock/source-age bounds, hardware
overhead, controller behavior or any gate. Missing integration tests and OPEN
findings remain explicit; passing suites do not resolve them.

Process deviation: a read-only `git status --short` was invoked during initial
inventory before COMMON_QUEUE.md's no-git rule was read. No further git commands,
git mutations, installs, SSH, camera or Raspberry Pi access were performed.
