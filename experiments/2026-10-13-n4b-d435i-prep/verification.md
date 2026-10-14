# Mac verification receipt — OPEN

Date: 2026-10-13. Scope: offline/synthetic tooling only. All hardware gates,
SDK/OpenCV compilation/parsing, N4B execution, N4C execution and calibration
qualification remain **OPEN**. No PASS is claimed.

Before edits, inspected Git status, feature branch
`feat/d435i-camera-capture-20260913`, recent root history (HEAD `5932457`), the
requested docs, the target folder's existing `TICKET.md`/`codex_run.log`, and
upstream source/schema. The worktree already had modified/deleted/untracked
user files; they were preserved. The upstream submodule already contained
untracked `.DS_Store` files; they were preserved. This work used the existing
feature branch and did not write Git metadata.

All writes were confined to `experiments/2026-10-13-n4b-d435i-prep/`.
The generated patch was never applied to `third_party`. No camera process,
ORB executable, SSH, network, install, firmware/calibration command, persistent
network change, commit or push was executed. Existing citations were read from
local docs; no remote document was retrieved.

## Provenance

- ORB-SLAM3 source: `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`.
- Original example SHA-256:
  `b03a2c6ca6ad3d5d729a6afd22a2efad1e4f6500ed2fee7885b4e3fa607e66af`.
- New-unit factory enumeration SHA-256:
  `adbcfcdf19372c81686cfa0379d6567a1a7e441f21fd7434f1eef8254738cc73`.
- [SHA256SUMS](SHA256SUMS) identifies generated deliverables. It excludes itself,
  the pre-existing ticket/run log and locally compiled test executables. Keep
  build/runtime receipts separately; do not treat this manifest as a dataset hash.

## Completed offline checks

Commands are in [README.md](README.md). Results:

| Check | Observed result | Practical limit |
|---|---|---|
| `validate_prep.py` | Exit 0; pinned source/calibration hashes, exact Rectified key set, numeric values, both IR projections, distortion, baseline, transforms and supported rates checked | Text/schema consistency, not OpenCV FileStorage execution |
| Read-only `git apply --check` | Exit 0 against the untouched pinned example | Applicability only; SDK compilation and linking OPEN |
| `clang++ -std=c++17 -Wall -Wextra -Werror -pedantic` | Synthetic input test compiled, no diagnostics; fixture executable exit 0 | Pure helper only, no SDK/OpenCV/ORB execution |
| Input fixtures | Linear three-axis interpolation, irregular gyro times, startup trimming, trailing coverage, once-only endpoint delivery, duplicate/reversed/nonfinite samples, gaps and no extrapolation checked | Does not establish device clock accuracy or SDK callback delivery |
| Transform fixtures | Factory forward/inverse and origin/basis round trips; synthetic nonidentity SDK column-major conversion checked | Nominal IMU geometry remains uncalibrated |
| Checksums and local Markdown links | All generated artifact digests and repository-relative link targets checked | External SDK citation links not fetched |

The temporary compiled test executable and patch-generation draft were removed
after checking. Only preparation source/configuration/docs and the checksum
manifest remain, alongside the two existing user files.

## Remaining OPEN

No librealsense/OpenCV headers were found in the standard Mac include roots
checked (`/usr/local/include`, `/opt/homebrew/include`). The actual Pi SDK build,
link recipes, native libraries, recorded metadata, emitter readback, global-time
state, callback backpressure, startup/EOF/shutdown behavior and state/trajectory
logs have not been observed by this work. Real bags, exact rate/domain/count
reconciliation, initialization, map continuity, live performance, power/storage
qualification and noise/spatial/temporal calibration require the future gated
manual checks in [n4b_plan.md](n4b_plan.md).
