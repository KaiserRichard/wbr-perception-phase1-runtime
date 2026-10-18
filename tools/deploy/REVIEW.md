# T16 independent review

## Verdict

**APPROVE-WITH-FIXES**

## Findings (ranked)

1. **BLOCKER: smoke could not produce its required result when the manifest was missing or unreadable.** `smoke.py` called `verify_tree` before handling filesystem/JSON errors, so it exited with a traceback and no `result.json`. Fixed in `deploy.py` and `smoke.py`: verification now returns a diagnostic, and smoke emits `BLOCKED` for absent/unreadable manifest evidence or `FAIL` for a present invalid bundle, then stops before running it. Regression coverage: `tests/test_deploy.py::test_smoke_writes_blocked_result_when_manifest_is_missing_or_unreadable`.
2. **MAJOR: remote rollback always selected `$HOME/wbr-tools`, even if deployment used `--dest`.** Fixed `deploy.sh` to derive the rollback parent from the supplied destination and documented the invocation. Added a fake-host dry-run regression test.
3. **MAJOR: smoke omitted several bundled hardware-free suites, and the VIO adapter suite needs its documented build step.** Added the missing Python/C++ suites and invoke `make test` on a temporary VIO adapter copy so its ignored build artifacts do not alter the verified release. The deploy builder tests require `.git`, which is intentionally absent from an extracted archive, so they remain in the Mac test run; the link-bench simulator tests need host-only source excluded by bundle policy.

## Requirements checked

- Bundle selection uses policy roots, excludes `third_party/` by omission and excludes configured host-only paths. The temporary repository test checks included Pi files and host exclusion; the manifest test checks a real saved power/USB evidence fixture.
- Dirty checkout refusal and explicit `--allow-dirty` are covered.
- SHA-256 tamper detection, remote command dry run, local install, and local rollback are covered.
- Smoke checks include manifest integrity, Python/module inventory, help for the selected lab/evaluation CLIs, fixture analysis, and all 17 selected hardware-free suites that can run from the extracted Pi bundle.
- Custom-destination remote rollback is now covered by dry run. Actual SSH/SCP operations were not run, as required by the ticket.

## Verification after fixes

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/deploy/tests -v`: **10 tests passed**. Full output is in `tests/last-run.log`.
- `bash -n` passed for `deploy.sh`, `make_bundle.sh`, and `pi_smoke.sh`.
- Packaged offline smoke run: all 17 selected suites passed; manifest, CLI help, and fixture analysis passed. A post-run verification also confirmed the release manifest remains valid. Overall **BLOCKED** on this Mac because Python is 3.11 and the Pi minimum is 3.12. See `tests/smoke-last-run.log`; run artifacts were written under `/tmp/wbr-review-final2.YyaWMg/smoke`.
- A prior packaged run had one transient failure in the existing `lab/d435i_raw` fake SDK callback-gap test (58 ms measured against its 50 ms limit). Its isolated rerun and the final packaged rerun passed. This timing-sensitive test is outside `tools/deploy/` and remains an open risk.

## Remaining open items

- Pi Python 3.12 behavior and remote SSH/SCP/install/rollback remain **UNKNOWN** until run by the operator on the Pi.
- The fake camera callback-gap unit test can fail under host scheduling pressure, so the smoke test can correctly report `FAIL` on a transient scheduling outlier.
- No sensor, camera, serial device, or ROS graph was accessed. Fixture results do not pass a physical project gate.
