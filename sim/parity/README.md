# Milestone 1: original C reference and Python exercise

The gain schedule evaluates a cubic for each gain:
`K_i(L) = a3*L^3 + a2*L^2 + a1*L + a0`.
Compile original C before comparing the Python port so coefficient order,
row order and signs are checked against the pinned implementation.
Primary source: [DM-jump VMC and gain evaluator, pinned revision](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/VMC/VMC_calc.c).

## Scope and layout

- `vendor/dm_jump/`: unchanged source inputs, MIT notices and SHA-256 manifest.
- `build_reference.py`: verifies inputs, extracts the exact 12x4 coefficient
  initializer from `chassisR_task.c`, compiles original `VMC_calc.c` plus a host ABI.
  The chassis task is never compiled or executed.
- `c_reference/`: float32 ABI and minimal INS/CMSIS host shims (`sinf`/`cosf`).
- `reference.py`: checked ctypes interface; serializes original C static state.
- `fixtures/shared_vectors.json`: shared polynomial, schedule, valid/invalid VMC inputs.
- `student.py`: **owner's gain_schedule TODO**; output is two rows of six,
  wheel gains followed by virtual hip torque gains. No feedback sign change.
- `tests/`: infrastructure/native C checks; `exercises/`: learner acceptance test.

## Build and test on the Mac

From the repository root, with Python 3.12 and a C compiler (clang or cc):

```bash
python3 -m sim.parity.build_reference --out-dir /tmp/wbr-parity-m1-your-run
python3 .github/run_unittest.py sim/parity/tests
python3 -m sim.parity.check_student --build-dir /tmp/wbr-parity-m1-your-run --out /tmp/wbr-parity-m1-your-run/gain-result.json
WBR_PARITY_BUILD=/tmp/wbr-parity-m1-your-run python3 -m unittest sim.parity.exercises.test_gain_schedule -v
```

Use a new build directory/report filename for each attempt. No package install is
needed. Builds support macOS/Linux, not Windows. JSON build receipts contain
compiler/options, upstream commit, source/library hashes, local HEAD and dirty
status. Keep receipts and binaries outside git; record paths/hashes in worklog.

Expected today: infrastructure green, gain checker **BLOCKED (exit 2)** because
the TODO raises NotImplementedError; the exercise test deliberately fails.
After the owner implements the function, all 13 gain cases must pass. Numeric
mismatch/invalid output is FAIL (exit 1), complete gain parity PASS is exit 0.
Never change tests/tolerances merely to obtain PASS. The predeclared comparison
uses absolute 2e-5 and relative 2e-6 tolerance for C float32 versus Python double.
CI discovers `sim/*/tests`; it deliberately excludes learner exercises.

## VMC evidence and limits

Native checks cover mirrored signs, fixed-pose repeatability, geometry,
virtual-work torque mapping, independent symmetric geometry/force anchors,
finite-difference Jacobians at three poses/two perturbation sizes, and invalid
inputs. The host wrapper rejects coincident knees at BD <= 1e-6 m and other
singular/nonfinite cases; this guard is host behavior, not a firmware change.
Derivative history is initialized at a repeated fixed pose. Joint motion and
transient derivatives are outside this contract. Host libm replaces CMSIS-DSP:
no bit-exact ARM/firmware claim is made.

**Python VMC parity is not implemented.** Native C sanity checks are separate
from C/Python parity. Milestone 1 stays incomplete until the learner's gain
schedule and a separately identified Python VMC port pass the shared vectors.
No physical measurements, dynamics, balance, LQR reproduction or RL claim follows
from this harness. Next: owner completes gain_schedule; review it, then finish
VMC parity before moving to the assumed six-state model.

To roll back an experiment, choose a new output directory; sources and earlier
reports are not overwritten. To abandon implementation, retain this branch and
return to its base `0e48cff`; do not reset shared checkouts.
