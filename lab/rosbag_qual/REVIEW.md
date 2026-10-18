# Independent review: T4 rosbag qualification

**Verdict: APPROVE-WITH-FIXES** (software tooling only; no physical gate PASS).

Reviewed the complete change against `origin/main`, including untracked files,
using COMMON.md, T4_bag.md and R_T4.md. All edits remain in the owned directory.
The following confirmed defects were fixed directly, with regression tests in
`tests/test_review.py` and valid synthetic CDR corrections in `tests/test_qual.py`.
Locations below refer to the corrected files and indicate the relevant fix.

## Ranked findings and fixes

1. **High — recording exceeded its requested interval and could split its own
   input bag** (`record_check.py:174`). `--max-bag-duration` controls splitting,
   not session shutdown; waiting for duration plus the command timeout kept
   recording beyond the request. Removed that flag, wait only for the requested
   interval, then use bounded process-group shutdown. Early successful exit and
   inadequate receive-time capture span cannot pass (`record_check.py:74`).
   Regressions verify wait duration, argv, early exit and partial capture.
2. **High — saved replay was evaluated as an already-reduced report**
   (`replay_check.py:213`). This discarded observations. Both paths now reduce
   the same raw data, use the saved configuration, recompute criteria and require
   saved graph guards and player/QoS logs. Missing/corrupt data blocks acceptance.
   Mocked live-to-saved round trips test PASS and changed-stamp FAIL.
3. **High — incomplete evidence could pass or crash**
   (`record_check.py:119`, `bag_core.py:260`, `replay_check.py:142`). Empty cached
   recording criteria produced PASS; missing config/log files caused crashes;
   absent stamp-order measurements defaulted to zero; missing stored replay
   topics defaulted to an accepted empty recording. Saved criteria are rebuilt
   from raw command outcomes and measurements. Missing fields are BLOCKED,
   measured zero delivery fails, and known FAIL retains precedence over BLOCKED.
4. **High — replay compared the wrong rate clocks; static TF could never pass**
   (`replay_check.py:34`, `replay_check.py:169`, `bag_core.py:66`). Player scheduling
   follows bag receive timestamps, but the comparison used header-stamp rate.
   Compare interval rates with recorded receive rate scaled by playback factor,
   without cross-clock epoch subtraction. Static TF now checks all transform
   header stamps, permits zero static stamps and skips dynamic rate criteria.
5. **High — camera guard covered only the original live domain**
   (`replay_check.py:251`, `replay_check.py:79`). A camera in the replay domain
   could publish into the observer. Both domains now receive node-list checks;
   existing/unrelated configured-topic publishers block playback acceptance.
   Add discovery delay, a bag-duration-based deadline and process-group cleanup.
6. **Medium — a healthy short segment hid missing stream coverage and receive
   timing failures** (`bag_core.py:279`, `bag_core.py:306`). Receive rates were
   calculated without acceptance checks, and repeated stamps were ignored.
   Both rates are checked independently; stream boundary gaps and repeated
   dynamic stamps have explicit criteria. All chosen limits live in config with
   PROPOSED provenance. Gap counts represent events, not inferred lost samples.
7. **Medium — storage demand was mislabeled as capacity and invented limits
   were called inherited** (`config.json:92`). The saved addendum says 16.6 MB/s
   achieved versus 18.4 MB/s needed. Use a clearly PROPOSED comparison ceiling
   derived from achieved throughput, with destination-qualification limitations.
   IR2 and the period-gap multiplier are now explicitly PROPOSED; September's
   manifest did not supply them. TF provenance cites the actual manifest and
   architecture. Storage bytes exclude unrelated evidence/log files.
8. **Medium — CDR correctness and fixture validity** (`bag_core.py:29`,
   `bag_core.py:52`, `tests/test_qual.py:24`). Alignment was absolute rather than
   relative to the four-byte encapsulation, invalid ROS nanoseconds were accepted,
   and the Image fixture omitted its pixel-sequence length. Fixed these and added
   multi-transform TF, nanosecond and alignment regressions. SQLite payloads now
   stream; SQLite URI escaping supports `#`/`?` in filenames.
9. **Medium — command/error contract and portability gaps**
   (`qual_common.py:30`, `analyze_bag.py:20`, `record_check.py:199`). Argparse usage
   errors exited 2 rather than 3, an explicit missing config silently selected
   defaults, and individual topic-info output existed only inside JSON. Usage
   and invalid configuration now exit 3; missing ROS/native support is BLOCKED;
   exact command receipts and separate stdout/stderr files are saved. QoS and
   config copies travel with evidence. Reuse the existing N3 manifest validator
   instead of maintaining duplicate name-validation logic.

## Requirement audit

| Binding requirement | Review result |
| --- | --- |
| T4.1 bounded explicit-topic recording, configured SQLite/MCAP, QoS, exact command, bag info, camera parameters, topic QoS | Implemented; duration and receipts fixed; ROS execution mocked only. |
| T4.2 offline counts, header/receive rates, period gaps, reversals, stereo pairing and separate IMU rates | Implemented with stdlib SQLite and optional rosbag2_py; clock/coverage and TF fixes tested. |
| T4.3 camera stopped, bounded replay, subscribed rates versus stored rates, stamps preserved | Implemented with both-domain guards and exact stamp hashes; physical DDS compatibility remains UNKNOWN. |
| T4.4 bag size/duration versus configured storage limit | Implemented; corrected provenance and file accounting; not a storage benchmark. |
| ROS imports lazy; unavailable dependencies BLOCKED | Covered by missing-ROS and missing-native-reader tests. |
| Synthetic DB3 with handwritten Image/Imu CDR; PASS, drops, reversal | Original cases retained; serializer corrected and regressions added. |
| Real saved evidence fixture | Full external DB3 read plus a portable 3.6 KB exact-header fixture with source SHA-256. |
| Reuse existing sound logic; do not edit historical tools | Reuse `n3_metrics.read_topics`; its 11-test suite run. External converter bugs recorded in REPORT.md, not fixed. |
| Result schema, aggregate precedence, exit codes, raw logs, analyze-only for all three checks | Covered by fixture tests and round trips; no cached verdicts trusted. |
| All numeric acceptance limits in config with sources; evidence labels | Production config annotates inherited and PROPOSED values; clock labels and scope documented in outputs/README. |
| README, REPORT, REVIEW and saved tests; no commits or unrelated edits | Completed in the owned path. |

## Test evidence and remaining items

MEASURED: original five tests passed. The initial regression run reproduced
16 failures and four errors across 26 tests (including three usage-exit
subtests). Exact outputs are preserved in `tests/review-initial.log` and
`tests/review-regressions-before.log`. Both used:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s lab/rosbag_qual/tests -v
```

After fixes, all **41 qualification tests plus 11 reused N3 tests pass**.
Final exact commands and complete output are in `tests/last-run.log`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s lab/rosbag_qual/tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s experiments/2026-09-12-pi5-native-sensor-validation -p test_n3_metrics.py -v
git diff --check
```

No shell scripts were added or modified, so bash syntax checking is inapplicable.
No confirmed owned-path software defect remains open. UNKNOWN physical items
are Pi recorder/player integration, actual QoS/discovery behavior, native MCAP
plugin behavior, current camera stamp contracts, and power/thermal/USB/storage
qualification. Full payload/calibration validation and continuous camera-process
monitoring are outside this check's claims. These limitations do not turn fixture
success into an N3 PASS. See REPORT.md for the external converter defect.
