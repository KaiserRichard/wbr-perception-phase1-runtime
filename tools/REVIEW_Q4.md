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
Q6 subsequently authorized fixes for all five remaining findings under tools/.
All five are now FIXED with failing-then-passing regressions, including shared
ROS-free/ORB-free boundary logic. ROS/ORB integration remains UNBUILT/UNKNOWN.
No hardware gate is promoted.
Severity below is an INFERRED engineering assessment, not a hardware gate result.

## Findings, ranked by severity

The original reproduction paragraphs describe Q4 behavior before fixes. Q6 fix
paragraphs describe the current implementation and its measured limits.

### High — FIXED: Python ROS gate accepts NaN clock evidence

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

**MEASURED, Q6 fix:** `ros2_bridge/mapping.py` now validates exact Python int
values (excluding bool), nonnegative native uint64 counters/generation/revision,
uint32 reason bits, int64 source/age/uncertainty/budgets and the ROS stamp range
before mutating watermarks or boundaries. Invalid configuration withholds poses.
`test_numeric_inputs_are_typed_and_bounded_before_mutation` failed with 87
subtest failures before the fix, then passed. It covers each clock numeric
field, snapshot counters and configuration with bool, noninteger, NaN, infinity,
negative and oversized values, then verifies valid input can still publish.
`test_native_integer_range_edges` additionally verifies signed overflow rejection
and accepted native maxima. Actual ROS execution remains UNKNOWN.

### High — FIXED: ROS skeleton does not implement its pause/forward-seek rules

**MEASURED source review:** `ros2_bridge/src/bridge_node.cpp:55` latches only
backward time changes and changes to use_sim_time. With a nonzero paused ROS
clock, a newly submitted snapshot with fresh evidence and `ros_ns <= ros_now`
can reach publication. Equal ROS time is not a suppression condition. The wall
diagnostics timer observes a pause only to force diagnostics. Forward jumps do
not invalidate the generation, evidence or gate.

DESIGN.md requires pause to stop poses and forward seek to require fresh
generation/rebind. [ROS time design, source lines 61–103](https://github.com/ros2/design/blob/gh-pages/articles/130_ros_time.md#L61-L103)
supports explicit pause and jump handling.

**MEASURED, Q6 fix:** extracted the old polling behavior into shared ROS-free
`src/clock_policy.hpp`; `clock_policy_checks` in `tests/core_probe.cpp` failed
on a nonzero pause before the fix. The node now uses that policy: equal replay
time suppresses poses even with fresh ingress; Gate still consumes paused
snapshots/reset events, so resume needs a later fresh estimate. Backward jumps,
mode changes, excessive forward increments and explicit discontinuity events
latch restart/rebind. A fault clears pending snapshots and clock evidence.
Tests pass for zero/nonzero pause, resume, forward jump, small notified seek,
equal-time source replacement, mode change, backward jump, unconfigured policy
and restart with fresh estimate/evidence in a new generation (old evidence fails).

**SOURCE-SUPPORTED, Q6 source review:** the UNBUILT node registers a retained
jump handler using [Jazzy rclcpp clock.hpp, lines 212–238](https://github.com/ros2/rclcpp/blob/jazzy/rclcpp/include/rclcpp/clock.hpp#L212-L238)
and [rcl time.h, lines 100–111](https://github.com/ros2/rcl/blob/jazzy/rcl/include/rcl/time.h#L100-L111).
This latches notified jumps even between polls after clock startup. The new
`max_forward_step_ns` parameter defaults to -1 (replay poses withheld until
configured); no physical budget is invented. It bounds an ordinary replay
increment, so slow polls/fast playback can conservatively fault. The trusted
replay owner must call `notify_clock_discontinuity()` **before every seek or
publisher replacement**, including small/equal-time changes which clock samples
cannot distinguish from ordinary progression. That integration seam, the ROS
callback, mailbox clearing and actual publication remain UNBUILT/UNKNOWN; no
producer/supervisor is connected. This Q6 policy supersedes DESIGN.md's earlier
backward-only implementation note; it is not complete autonomous seek detection.

### Medium — FIXED: harness treats a missing declared extra artifact as success

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

**MEASURED, Q6 fix:** the artifact-collection error path now sets
`receipt.analysis_failed` for missing or escaping declared artifacts, retaining
process exit/status, trajectory validity, errors, partial hashes and receipts.
`test_missing_or_escaping_extra_artifact_fails_batch` failed in both missing
and escaping-symlink cases before the fix. Both now pass: the successful engine
remains exit_code=0/status=OK, analysis_failures=1, and the CLI returns 1.

### Medium — FIXED: harness can finish a trial with descendants still running

**MEASURED:** `run_harness/harness.py:290` waits for the process leader only.
Process-group cleanup runs only when that wait times out. A leader spawning a
child and exiting successfully returns exit_code=0/timed_out=False while the
child is alive. A child delaying 0.2 s wrote `child_finished` after launch returned
in the review probe; it then exited normally. This can overlap repeats or mutate
logs/artifacts after hashes are recorded. A child need not escape its process group.

[Python 3.11 subprocess documentation, extracted lines 290–299 and 400–405](https://docs.python.org/3.11/library/subprocess.html#subprocess.Popen.wait)
defines a new session and waiting for the child process, not all descendants.
**MEASURED, Q6 fix:** `launch()` now kills the trial's POSIX process group
in a finally block after every leader wait, including successful exit, before
logs close or artifact collection/another repeat starts. Timeout still records
timed_out and the reaped leader return code. A vanished process group is harmless.
`test_leader_exit_cleans_descendants_before_return` failed before the fix: a
child wrote its delayed marker after launch returned. It now passes: the marker
remains absent beyond the child's intended write time, with the original
exit_code=0/timed_out=False retained. Existing timeout-with-child fixtures pass.
**UNKNOWN / limitation:** this owns descendants that remain in the launched
process group; deliberately detached sessions/other process groups are outside
this POSIX cleanup contract. Kernel I/O completion and zombie reaping are not
measured by the delayed-writer test.

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

### Medium — FIXED: optional ORB IMU boundary narrows doubles without a guard

**SOURCE-SUPPORTED:** [ImuTypes.h, lines 45–58](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4/include/ImuTypes.h#L45-L58)
accepts float motion components and double seconds. Adapter append accepts any
finite double. `vio_adapter/orb_engine.cpp:26` passes those doubles to float
constructor arguments without checking representability; e.g. 1e40 is accepted
upstream but exceeds float range. Out-of-range narrowing is not a qualified
finite engine measurement. Missing test: oversized finite motion at the actual
ORB boundary, with an explicit rejection/FAULT policy. Source path inspected;
the optional binding was not compiled or executed, so runtime behavior is UNKNOWN.
**MEASURED, Q6 fix:** `vio_adapter/orb_engine.cpp` now calls shared
ORB-free `orb_imu.hpp::orb_motion()` immediately before constructing each
`IMU::Point`. The helper rejects nonfinite/out-of-float-range values before
casting, and nonzero-to-zero underflow after casting. It throws range_error;
the existing Adapter exception path emits invalid FAULT/ENGINE_FAULT and counts
engine rejection, without calling TrackStereo for that batch. Double seconds
remain unchanged. Ordinary float rounding is allowed; this is storage
representability, not physical plausibility qualification.

The new C++ fixture group in `tests/test_adapter.cpp` failed its rejection
assertion with the extracted unchecked narrowing, then passed with the guard.
It exercises both signs of overflow/underflow plus NaN/infinity in all six
components; zero, normal, float-max and subnormal edges; and a boundary-checking
fake Engine proving the Adapter FAULT path and no accepted batch. The optional
ORB binding itself remains UNBUILT/UNKNOWN; the exact helper it calls is compiled
and executed without ORB. The adapter now has 12 C++ fixture groups.


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
Finite covariance metadata is not a covariance qualification. The Q6 fixes above preserve the existing synthetic convention tests.

## Validation commands and results

**MEASURED:** Python 3.11.0rc2; Apple clang 17.0.0; macOS x86_64.
Each command below was run from repository root with
`PYTHONDONTWRITEBYTECODE=1`. Q4 baseline/final counts are retained as history;
all nine Q6 final commands exited 0. Q6 logs: `/tmp/q6-final-{0..8}.log`, ordered
as the table. Q6 did not rerun the old baseline; targeted new regressions were
run before each fix. Logs: `/tmp/q6-red-{numeric,artifact,descendants,clock,orb}.log`
(C++ build logs also use the `q6-red-*-build.log` names).

| Exact command | Q4 baseline | Q4 final | Q6 final |
|---|---:|---:|---:|
| python3 -m unittest discover -s tools/take_tools/tests -v | 19 | 20 | 20 |
| python3 -m unittest discover -s tools/calib_tools/tests -v | 15 | 16 | 16 |
| python3 -m unittest discover -s tools/frames/tests -v | 10 | 11 | 11 |
| python3 -m unittest discover -s tools/clockmap/tests -v | 37 | 37 | 37 |
| make -C tools/link_proto test | C assertions + 4 Python | same | same |
| make -C tools/vio_adapter test | 11 C++ fixture groups + 4 Python | same | 12 C++ fixture groups + 4 Python |
| make -C tools/runtime_observer test | C++ recorder checks + 20 Python | same | same |
| python3 -m unittest discover -s tools/run_harness/tests -v | 17 | 17 | 19 |
| make -C tools/ros2_bridge test | C++ core + 18 Python, parity enabled | same | C++ core + clock policy + 20 Python, parity enabled |

Q6 final Python total: **151 passed**, zero failures/skips. C/C++ targets passed.
Q4 final Python total was 147. All five Q6 targeted regressions failed before
their fixes and passed afterward; the additional integer range-edge test passes.
Q6 edited only under tools/ and created no REPORT file.

Exact Q6 regression commands (each with `PYTHONDONTWRITEBYTECODE=1`):

```sh
python3 -m unittest discover -s tools/ros2_bridge/tests -k numeric -v
python3 -m unittest discover -s tools/run_harness/tests -k extra_artifact -v
python3 -m unittest discover -s tools/run_harness/tests -k leader_exit -v
make -C tools/ros2_bridge build/core_probe
tools/ros2_bridge/build/core_probe < /dev/null
make -C tools/vio_adapter build/test_adapter
tools/vio_adapter/build/test_adapter
```

Before fixes: numeric regression failed (87 subtests); extra-artifact regression
failed (2 subtests); descendant regression failed (1 assertion). Both C++
executables built, then aborted on the new pause/narrowing assertion (exit 134).
After fixes: all pass, including the two C++ assertion executables as part of
the final make targets. The C++ red runs used extracted old boundary logic;
the node/binding now call the same fixed helpers tested by those executables.


The three Q4 targeted tests failed before their Q4 fixes and passed afterward:

```sh
python3 -m unittest discover -s tools/calib_tools/tests -k native_float -v
python3 -m unittest discover -s tools/frames/tests -k velocity_overflow -v
python3 -m unittest discover -s tools/take_tools/tests -k extreme_accel -v
```

**MEASURED, Q4 read-only real-data checks (not rerun in Q6):** called take_tools.audit on
`/Users/quockaiser/Desktop/Research/wbr-data/2026-10-14-d435i-ramtest15s/take/stereo_imu.db3`:
structural PASS, global_time only, IR1=447, IR2=447, gyro=2971, accel=1507,
447 accepted stereo pairs. Called clockmap.analyze_timestamps on adjacent
timestamps.csv: Accel=1506, Gyro=2971, IR1=445, IR2=445, one diagnostic segment
each. No raw data copied/exported into this repo; no engine execution implied.

**UNKNOWN / NOT verified:** ORB/OpenVINS native calibration loading, optional
ORB binding compilation, actual ROS package compilation/runtime, camera/Pi/MCU,
mount calibration, continuous odom, true clock/source-age bounds, hardware
overhead, controller behavior or any gate. Missing integration tests remain explicit; passing ROS-free/ORB-free suites
does not establish actual ROS/ORB build/runtime or hardware behavior.

Q4 process deviation: a read-only `git status --short` was invoked during initial
inventory before COMMON_QUEUE.md's no-git rule was read. No further git commands,
git mutations, installs, SSH, camera or Raspberry Pi access were performed.

Q6 process: no git commands, installs, SSH, camera/Pi/MCU access or real-data
mutation. Q4's read-only real-data results above are retained history and were
not rerun in Q6. No new report was written; Q6 evidence is recorded here only.
