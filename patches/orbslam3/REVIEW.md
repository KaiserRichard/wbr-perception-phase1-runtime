# Independent review: T24 N4B startup crash

## Verdict

**APPROVE.** No confirmed defect was found in the patch, investigation, or
offline verifier. No code changes were needed during review.

## Ranked findings

None.

## Independent crash-site reconstruction

The saved MEASURED report in the session addendum names
`main → System::GetTimeFromIMUInit → LocalMapping::GetCurrKFTime` on the first
frame. I independently followed this path in the pinned upstream source before
relying on the investigation's conclusion:

- `System::GetTimeFromIMUInit` first calls `GetCurrKFTime` and reads
  `mFirstTs` before testing the atlas IMU-initialized flag (`src/System.cc:1339–1345`).
- `GetCurrKFTime` tests `mpCurrentKeyFrame` and dereferences it on the true
  branch (`src/LocalMapping.cc:1506–1515`). Its declaration is uninitialized
  upstream (`include/LocalMapping.h:166`), and the constructor does not assign
  it. This supports the reported invalid read/dereference mechanism.
- The D435i runner patch calls the initialization query after `TrackStereo`
  (`stereo_inertial_d435i_file.patch:249–256`). The upstream EuRoC runner calls
  `TrackStereo` but does not call this accessor. The reviewed patch only adds
  default member initializers, so it does not change the EuRoC execution path.

The inspected evidence contains no raw gdb backtrace, instruction address,
registers, pointer value, core, or exact first-crash binary hashes. The
call-chain and first-frame SIGSEGV therefore remain a MEASURED historical
report; identification of this uninitialized pointer as the fault is
INFERRED, strongly supported by source. The investigation labels this limit
correctly.

## Requirement review

- **Patch and diagnosis:** the git-format patch is against pinned commit
  `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`. It initializes the implicated
  pointer and the separately uninitialized `mFirstTs`, which is read on the
  same path before the atlas check. The latter is a source-supported additional
  issue, not presented as a separately measured crash.
- **Patch ordering/applicability:** verified `git apply --check` and apply on a
  temporary slice from the pinned source. Also applied the saved D435i runner
  patch first, then the reviewed patch; both applied cleanly and the resulting
  runner contains the accessor call. The Pi Settings and C++17 commit subjects
  are recorded, but their exact diffs are absent from the saved evidence, so
  their complete Pi-tree application order could not be independently
  reconstructed. They touch separate files from this patch according to the
  recorded subjects.
- **EuRoC regression:** no call to the affected accessor exists in the official
  EuRoC runner; the two declaration initializers do not alter that path.
- **Input conditions and clock domains:** the report correctly distinguishes
  D435i IMU and camera timestamps, notes that input can prolong pre-keyframe
  startup without being required to trigger the defect, and does not infer a
  unit or empty-vector cause from the missing raw trace.
- **Docs, evidence labels, and gate status:** source, measured report, inference,
  unknowns, hardware limits, exact future Pi rebuild/rerun steps, and the
  no-gate-PASS caveat are stated. The local upstream issue/changelog search is
  bounded to available source-tree text; no unsupported issue citation is
  made.
- **Verifier and fixtures:** tests exercise PASS, FAIL, BLOCKED, usage, source
  identity, patch failure, and a real saved historical report. Analyze-only
  uses saved source/patch evidence. Its PASS is limited to offline patch/probe
  behavior and cannot establish a Pi build or N4B gate PASS.

## Fixes and test results

No confirmed defects were found, so no fixes or additional regression tests
were needed. Re-ran the complete added test suite after review:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s patches/orbslam3/tests -v
Ran 9 tests in 5.684s
OK
```

Exact per-test output is saved in `tests/last-run.log`.

Ordered temporary application check:

```text
git apply --check -p1 <saved D435i runner patch>    exit 0
git apply -p1 <saved D435i runner patch>            exit 0
git apply --check <reviewed ORB startup patch>      exit 0
git apply <reviewed ORB startup patch>              exit 0
Temporary source slice removed on exit.
```

The verifier's saved C++11 and C++17 isolated probes also pass through the
unittest suite. This is not a full ORB translation-unit build.

## Remaining open items

- **UNKNOWN:** patched Pi rebuild, actual loaded library, and D435i replay were
  not verified. The saved queue outcome stopped during build verification.
- **UNKNOWN:** exact Pi-local Settings and C++17 patch diffs are not preserved,
  preventing exact recreation of that complete modified tree.
- The patch does not make mapper state reads thread-safe and does not establish
  keyframe lifetime/reset safety; these are documented follow-up risks.

The verdict approves the source patch and evidence package only. N4B remains
OPEN.
