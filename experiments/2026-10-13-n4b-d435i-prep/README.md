# D435i stereo-inertial preparation — OPEN

SDK serial **317422076650**, firmware **5.17.3.10**, BMI085. Mac-only preparation;
all gates remain **OPEN**. No camera/ORB execution, SSH, network, installation,
commit or push. Existing evidence and upstream checkout are preserved.

- [Candidate YAML](D435i_317422076650_stereo_inertial.yaml): rectified stereo
  640×480/30, gyro-grid IMU/200; assumed unit noise.
- [Calibration review](calibration_notes.md): exact schema, transform direction
  and math, upstream comparison, nominal IMU geometry and unknown calibration.
- [N4B/N4C plan](n4b_plan.md): gates, isolated Pi build/run commands, recording,
  hand motion, success observations, storage and timestamp provenance.
- [Unapplied patch](stereo_inertial_d435i_file.patch) and [recorder](d435i_record.cpp),
  with [input association](d435i_input.h) and [shared SDK helpers](d435i_rs.h).
- [Verification](verification.md), [artifact checks](validate_prep.py),
  [synthetic fixtures](test_d435i_input.cpp), and [checksums](SHA256SUMS).

Reproduce camera-free checks from the repository root; compilation output stays
in this experiment folder. No dependency installation is required:

```bash
python3 experiments/2026-10-13-n4b-d435i-prep/validate_prep.py
clang++ -std=c++17 -Wall -Wextra -Werror -pedantic \
  experiments/2026-10-13-n4b-d435i-prep/test_d435i_input.cpp \
  -o experiments/2026-10-13-n4b-d435i-prep/test_d435i_input
experiments/2026-10-13-n4b-d435i-prep/test_d435i_input
cd experiments/2026-10-13-n4b-d435i-prep
shasum -a 256 -c SHA256SUMS
```

These prove tooling only. SDK/OpenCV parsing and compilation, actual bags,
initialization, live timing and N4 qualification remain OPEN. Future camera and
ORB execution requires explicit **CAMERA AVAILABLE** and the documented gates.
The pre-existing `TICKET.md` and `codex_run.log` are retained as received.
