# T24 report

Completed the source/evidence investigation and delivered
`0001-initialize-localmapping-startup-state.patch` against upstream
`4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`, plus the investigation in
`docs/ORB_SLAM3_N4B_CRASH.md`, a standard-library offline verifier, source/evidence
hash manifests, real saved evidence fixture and unittest coverage.

**INFERRED, strongly source-supported:** the historical first-frame SIGSEGV
matches an uninitialized `mpCurrentKeyFrame` read through the added
`GetTimeFromIMUInit` telemetry. Recorded patch 4 targets the actual pointer.
**SOURCE-SUPPORTED additional finding:** `mFirstTs` is also uninitialized and
read before the atlas initialization check. The proposed patch initializes
both fields. The Rectified Settings print bug is a separate crash requiring
the two already-recorded Settings fixes. Their exact Pi diffs were unavailable;
the report distinguishes commit subjects, source mechanism and measured claims.

## Validation

**MEASURED offline software, 2026-10-18:**

| Check | Result | Evidence |
|---|---|---|
| Full temporary upstream copy, `git apply --verbose --check` | Exit 0; 955 files / 1,507,554,292 bytes copied, excluding `.git` / `.DS_Store`; temporary tree deleted | `validation/full-copy/receipt.json`, command and verbatim outputs |
| Exact source pin, temporary slice apply, isolated C++11 and C++17 startup regression | PASS, exit 0 | `validation/pinned-source/result.json` and `raw/` |
| Reanalysis from saved raw source and patch, independent of shared checkout | PASS, exit 0 | `validation/reanalyzed/result.json` and `raw/` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s patches/orbslam3/tests -v` | 9 tests, OK; covers PASS / FAIL / BLOCKED, changed source/pin/patch, missing source/compiler, real report fixture and usage | `tests/last-run.log` |
| All future Pi Bash snippets in investigation, concatenated and checked with `bash -n` | Exit 0 | `validation/documentation-checks.json` |

The isolated regression compiles the actual two patched member declarations
and unchanged upstream accessor bodies with a surrogate constructor and
KeyFrame/Atlas stubs. It validates nonzero-storage construction, no-keyframe
queries, and same-clock synthetic valid-keyframe timestamps before/after atlas
initialization. This is limited syntax/behavior evidence, not a full ORB build.
The existing constructor's omission of both member initializers was checked
in the pinned source. Full translation-unit compilation was not attempted
without the configured ORB/OpenCV/Eigen/Pangolin dependencies.

An initial verifier attempt exposed a check-scope error: Git discovered the
enclosing worktree and returned success while skipping temporary `include/`
paths; the compiled probe then failed its startup assertion. The checker now
sets `GIT_CEILING_DIRECTORIES` for temporary-copy commands and saves verbose
Git output. The passing test explicitly requires Git's applied-file message,
and executing the probe verifies the declarations actually changed. Original
failure evidence is retained in `validation/initial-check-scope-error/`;
subsequent final checks and full-copy applicability are separate receipts.

## Not verified and open risks

- **UNKNOWN:** raw original gdb backtrace, instruction/pointer values, core,
  exact crashing binary/library hashes and original first-crash bag identity.
  The recovered call chain is from a historical MEASURED report; a fixture
  reproducing that report is not a new observation.
- **UNKNOWN:** complete patched Pi build, actual loaded library, original
  accessor path on the Pi, successful replay, initialization/tracking quality,
  power/thermal/storage behavior, calibration and timestamp alignment. No
  hardware or gate PASS is claimed. No SSH, camera, serial device, network,
  install, GUI, commit or push was used.
- **SOURCE-SUPPORTED:** mapper accessors still lack a coherent synchronized
  snapshot; resets/keyframe lifetime and concurrent pointer/timestamp access
  remain outside this minimal startup patch.
- Existing upstream concerns were documented without modifying other tools:
  preintegration's “empty vector” diagnostic tests `size-1==0` (one sample),
  and the EuRoC IMU consumption loop lacks an end-index guard. Neither is
  established as the historical crash cause. Input coverage must be screened
  with existing `tools/n4b_offline` tooling.
- The existing Pi Settings fixes and C++17 compatibility changes must be
  preserved. The EuRoC runner avoids the reported accessor, so only running
  it would leave the original-path regression unverified. Exact rebuild,
  custom file-example compilation, replay and gdb commands are provided in
  the investigation. Missing original `.bag` means that rerun is BLOCKED.

All new files remain inside `patches/orbslam3/` and
`docs/ORB_SLAM3_N4B_CRASH.md`. Third-party source and the shared checkout were
read-only. Changes are left uncommitted for the conductor.

Proposed commit message:

```text
fix(orbslam3): initialize LocalMapping startup query state

Document the reported N4B GetCurrKFTime crash and separate Settings failure.
Provide a pinned patch for the keyframe pointer and first-IMU timestamp,
offline regression/evidence checks, and exact Pi rebuild and replay steps.
```
