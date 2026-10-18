# ORB-SLAM3 N4B startup crash patch

This directory contains an unapplied git-format diff against official upstream
`4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`. It initializes
`LocalMapping::mpCurrentKeyFrame` and `mFirstTs`, both read by the custom D435i
runner before initialization. The [investigation](../../docs/ORB_SLAM3_N4B_CRASH.md)
explains the reported crash, the distinct Settings defect, and exact future Pi
rebuild and replay commands. Third-party source is preserved.

From the repository root, with Python 3.11+ and an existing C++ compiler:

```bash
python3 patches/orbslam3/verify_patch.py \
  --source /Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime/third_party/ORB_SLAM3 \
  --outdir /tmp/n4b-patch-verification
python3 patches/orbslam3/verify_patch.py \
  --analyze-only patches/orbslam3/validation/pinned-source \
  --outdir /tmp/n4b-patch-reanalysis
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s patches/orbslam3/tests -v
```

Output directories must be new. `--compiler /path/to/c++` overrides compiler
discovery. The same check runs on the Pi against a **pristine pinned source**:

```bash
python3 patches/orbslam3/verify_patch.py \
  --source "$HOME/wbr-perception-phase1-runtime/third_party/ORB_SLAM3" \
  --outdir "$HOME/wbr-evidence/n4b-patch-check-$(date -u +%Y%m%dT%H%M%SZ)"
```

The historical Pi build copy has local patches and its own commit IDs; it is
not an appropriate `--source` identity fixture. See the investigation for how
to rebuild that existing modified stack and rerun the original accessor path.

| Criterion | Meaning | Limit |
|---|---|---|
| `source_pin` | Exact upstream revision and SHA-256 of the three relevant source files | Does not identify an installed binary |
| `patch_applies` | `git apply --check` and apply succeed on a temporary source slice | Does not build the full library |
| `startup_probe` | Actual patched member declarations and unchanged accessor bodies compile and run assertions in C++11 and C++17 | Constructor, KeyFrame and Atlas are isolated substitutes; no threads or SDK |

The probe default-constructs in nonzero storage, checks the no-keyframe return,
then exercises uninitialized/initialized atlas states and same-clock timestamp
subtraction with a valid synthetic keyframe. It does not execute the original
undefined behavior. Initializers and exact expected values are semantic
invariants, not numeric acceptance thresholds. `source_manifest.json` is the
single configuration for exact source identity; no numeric screening limits
are introduced.

Each check emits `result.json`, a short table, verbatim command stdout/stderr,
command/exit receipts, source snapshots and SHA-256 provenance. Missing source,
Git or compiler means BLOCKED; identity mismatch, failed apply, failed compile
or assertion means FAIL. FAIL takes precedence over BLOCKED. Exit codes are
0 PASS, 1 FAIL, 2 BLOCKED, 3 usage/internal error. Analyze-only rechecks saved
raw source, revision and patch, and recompiles; it needs no shared checkout.
Temporary mutations stay under this directory's `tmp/`, removed afterwards.

`validation/full-copy/` separately records the ticket-required apply check on
a complete temporary copy of the shared upstream tree (omitting `.git` and
`.DS_Store`), subsequently deleted. `validation/pinned-source/` and
`validation/reanalyzed/` record the passing final checks. The first verifier
attempt and its failure are retained under `validation/initial-check-scope-error/`;
see [REPORT.md](REPORT.md).

Tests include PASS, FAIL and BLOCKED paths, saved real upstream source and
`tests/fixtures/real_saved_crash.json`, a verbatim historical report with its
source hash. **Fixture/check PASS is not N4B or any hardware gate PASS.** These
checks cannot establish Pi compilation, loaded library identity, source input
quality, IMU initialization, tracking, reset lifetime or thread safety. Source
snapshots retain upstream GPL notices. No hardware, network or installs are
needed.
